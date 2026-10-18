"""Serviço de percepção: uma foto ou um delta do mundo visível a cada pedido de decisão (ADR-0028,
ADR-0047, ADR-0056).

Lê `world` e `agent` com consumidores duráveis. A projeção vai para um arquivo, com o último seq
aplicado de cada stream, antes de cada confirmação: se o processo cair, volta do arquivo e o
JetStream entrega o resto. Antes de montar a foto de um pedido, alcança o stream `world`, para que
tudo o que o kernel publicou antes do pedido já esteja na projeção.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_perception.view import PerceptionState
from campsverso_ports import (
    BlobStore,
    Consumer,
    Envelope,
    EventBus,
    IdGenerator,
    Telemetry,
    WallClock,
)

DELIVERED = "campsverso.perception.delivered.v1"
UPDATED = "campsverso.perception.updated.v1"
DECISION = "campsverso.avatar.decision_requested.v1"


@dataclass(frozen=True, slots=True)
class PerceptionPolicy:
    """Quem recebe foto ou delta (ADR-0056). Script e replay recebem sempre a foto: a linha de
    base e o replay das sessões antigas não mudam. Quem pede deltas recebe a foto na primeira
    decisão, ao assumir a posse e a cada `snapshot_every` deltas."""

    deltas_for: frozenset[str] = frozenset({"llm"})
    snapshot_every: int = 20


class PerceptionService:
    def __init__(
        self,
        worldid: str,
        bus: EventBus,
        blobs: BlobStore,
        clock: WallClock,
        ids: IdGenerator,
        telemetry: Telemetry,
        policy: PerceptionPolicy | None = None,
    ) -> None:
        self._worldid = worldid
        self._policy = policy or PerceptionPolicy()
        self._ids = ids
        self._bus = bus
        self._blobs = blobs
        self._clock = clock
        self._telemetry = telemetry
        self._key = f"{worldid}/projection.json"
        self.projection = self._load()
        self._world: Consumer | None = None
        self._agent: Consumer | None = None
        self.delivered = 0
        self.failure: BaseException | None = None

    def _load(self) -> PerceptionState:
        try:
            return PerceptionState(json.loads(self._blobs.get(self._key)))
        except FileNotFoundError, KeyError:
            return PerceptionState()

    def _save(self) -> None:
        data = json.dumps(self.projection.export(), ensure_ascii=False, separators=(",", ":"))
        self._blobs.put(self._key, data.encode())

    async def start(self) -> None:
        w = self._worldid
        self._world = await self._bus.consume(
            f"campsverso.{w}.world.>", f"perception-{w}-world", self._on_world
        )
        self._agent = await self._bus.consume(
            f"campsverso.{w}.agent.>", f"perception-{w}-agent", self._on_agent
        )

    async def stop(self) -> None:
        for consumer in (self._agent, self._world):
            if consumer is not None:
                await consumer.unsubscribe()

    async def _on_world(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        try:
            for _, envelope in batch:
                if not self.projection.seen("world", envelope):
                    self.projection.apply("world", envelope)
            self._save()
        except Exception as error:
            self.failure = error
            raise

    async def _on_agent(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        try:
            for _, envelope in batch:
                if envelope["type"] in (DELIVERED, UPDATED) or self.projection.seen(
                    "agent", envelope
                ):
                    continue
                if envelope["type"] == DECISION:
                    assert self._world is not None
                    await self._world.caught_up()  # tudo o que veio antes do pedido
                self.projection.apply("agent", envelope)
                if envelope["type"] == DECISION:
                    await self._deliver(envelope)
            self._save()
        except Exception as error:
            self.failure = error
            raise

    async def _deliver(self, decision: Mapping[str, Any]) -> None:
        data = decision["data"]
        avatar_id, reason = str(data["avatar_id"]), str(data["reason"])
        controller = dict(data["controller"])
        projection = self.projection
        policy = self._policy
        snapshot = str(controller["type"]) not in policy.deltas_for or projection.wants_snapshot(
            avatar_id, str(controller["id"]), reason, policy.snapshot_every
        )
        event_type = DELIVERED if snapshot else UPDATED
        payload: dict[str, Any]
        if snapshot:
            payload = {
                "avatar_id": avatar_id,
                "kind": "snapshot",
                "as_of_tick": projection.tick,
                "view": projection.view(avatar_id),
            }
        else:
            payload = projection.delta(avatar_id)
        # O pedido que a entrega responde: o controlador age só com este evento (ADR-0048).
        payload["decision"] = {"reason": reason, "controller": controller}
        projection.out_seq += 1
        info = CONTRACT_TYPES[event_type]
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            # Mesmo pedido, mesma entrega: reenviada depois de uma queda, o JetStream deduplica.
            "id": self._ids.derive(str(decision["id"]), "perception"),
            "source": f"/perception/{self._worldid}",
            "type": event_type,
            "time": self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "datacontenttype": "application/json",
            "dataschema": info.dataschema,
            "worldid": self._worldid,
            "cartridge": decision["cartridge"],
            "tick": projection.tick,
            "simtime": projection.simtime,
            "seq": projection.out_seq - 1,
            "actor": "system/perception",
            "provenance": "simulated",
            "visibility": info.visibility,
            "subject": f"avatar/{avatar_id}",
            "causationid": decision["id"],
            "data": payload,
        }
        if decision.get("correlationid"):
            envelope["correlationid"] = decision["correlationid"]
        await self._bus.publish(subject(event_type, self._worldid, avatar_id), envelope)
        projection.deliver(avatar_id, str(controller["id"]), snapshot=snapshot)
        self.delivered += 1
