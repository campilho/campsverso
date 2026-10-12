"""Serviço de percepção: uma foto do mundo visível a cada pedido de decisão (ADR-0028, ADR-0047).

Lê `world` e `agent` com consumidores duráveis. A projeção vai para um arquivo, com o último seq
aplicado de cada stream, antes de cada confirmação: se o processo cair, volta do arquivo e o
JetStream entrega o resto. Antes de montar a foto de um pedido, alcança o stream `world`, para que
tudo o que o kernel publicou antes do pedido já esteja na projeção.
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any

from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_perception.projection import Projection
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
DECISION = "campsverso.avatar.decision_requested.v1"


class PerceptionService:
    def __init__(
        self,
        worldid: str,
        bus: EventBus,
        blobs: BlobStore,
        clock: WallClock,
        ids: IdGenerator,
        telemetry: Telemetry,
    ) -> None:
        self._worldid = worldid
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

    def _load(self) -> Projection:
        try:
            return Projection(json.loads(self._blobs.get(self._key)))
        except FileNotFoundError, KeyError:
            return Projection()

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
                if envelope["type"] == DELIVERED or self.projection.seen("agent", envelope):
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
        avatar_id = str(decision["data"]["avatar_id"])
        projection = self.projection
        projection.out_seq += 1
        info = CONTRACT_TYPES[DELIVERED]
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            # Mesmo pedido, mesma foto: reenviada depois de uma queda, o JetStream deduplica.
            "id": self._ids.derive(str(decision["id"]), "perception"),
            "source": f"/perception/{self._worldid}",
            "type": DELIVERED,
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
            "data": {
                "avatar_id": avatar_id,
                "kind": "snapshot",
                "as_of_tick": projection.tick,
                # O pedido que a foto responde: o controlador age só com este evento (ADR-0048).
                "decision": {
                    "reason": decision["data"]["reason"],
                    "controller": dict(decision["data"]["controller"]),
                },
                "view": projection.view(avatar_id),
            },
        }
        if decision.get("correlationid"):
            envelope["correlationid"] = decision["correlationid"]
        await self._bus.publish(subject(DELIVERED, self._worldid, avatar_id), envelope)
        self.delivered += 1
