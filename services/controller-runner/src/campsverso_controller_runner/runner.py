"""Controller-runner: responde a cada foto da percepção com uma proposta de ação (escopo §5).

O ciclo: o kernel pede uma decisão, a percepção manda a foto (com o motivo do pedido e o
controlador da vez) e o controlador com a posse responde com `cmd.action.propose`, levando o mesmo
correlationid. Basta a foto: o runner não depende da ordem entre dois eventos (ADR-0048).
O id do comando é derivado do id da foto: se o runner cair depois de publicar e antes de
confirmar, a proposta repetida é descartada pelo kernel (ADR-0046).
"""

from collections.abc import Mapping, Sequence
from importlib.metadata import entry_points
from typing import Any, Protocol, cast

from campsverso_ports import Consumer, Envelope, EventBus, IdGenerator, Telemetry, WallClock

DECISION = "campsverso.avatar.decision_requested.v1"
DELIVERED = "campsverso.perception.delivered.v1"
PROPOSE = "campsverso.cmd.action.propose.v1"
ENTRY_POINT_GROUP = "campsverso.controllers"


class Controller(Protocol):
    """O que um controlador implementa. O script do cartucho segue esta forma sem importá-la."""

    @property
    def controller_type(self) -> str: ...

    @property
    def controller_id(self) -> str: ...

    def decide(self, view: Mapping[str, Any]) -> Mapping[str, Any]:
        """A `view` de `perception.delivered.v1` vira {action, params, intent?}."""
        ...


def load_controller(name: str) -> Controller:
    """Controladores instalados, registrados no grupo `campsverso.controllers` (ADR-0011)."""
    found = {ep.name: ep for ep in entry_points(group=ENTRY_POINT_GROUP)}
    if name not in found:
        raise LookupError(f"controlador {name!r} não encontrado ({sorted(found)})")
    return cast(Controller, found[name].load())


def command_envelope(
    worldid: str,
    cartridge: str,
    controller_type: str,
    controller_id: str,
    command_id: str,
    seq: int,
    time: str,
    data: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "specversion": "1.0",
        "id": command_id,
        "source": f"/controller-runner/{controller_id}",
        "type": PROPOSE,
        "time": time,
        "datacontenttype": "application/json",
        "dataschema": "contracts://commands/action/propose.v1",
        "worldid": worldid,
        "cartridge": cartridge,
        "seq": seq,
        "controller": controller_type,
        "controllerid": controller_id,
        "provenance": "simulated",
        "visibility": "observer",
        "data": dict(data),
    }


class ControllerRunner:
    def __init__(
        self,
        worldid: str,
        avatar_id: str,
        controller: Controller,
        bus: EventBus,
        ids: IdGenerator,
        clock: WallClock,
        telemetry: Telemetry,
    ) -> None:
        self._worldid = worldid
        self._avatar = avatar_id
        self.controller = controller
        self._bus = bus
        self._ids = ids
        self._clock = clock
        self._telemetry = telemetry
        self._last: Mapping[str, Any] | None = None
        self._consumer: Consumer | None = None
        self.answered = 0
        self.failure: BaseException | None = None

    async def start(self) -> None:
        w, a = self._worldid, self._avatar
        durable = f"controller-{w}-{a}-{self.controller.controller_type}"
        self._consumer = await self._bus.consume(
            f"campsverso.{w}.agent.{a}.perception.delivered.v1", durable, self._on_batch
        )

    async def stop(self) -> None:
        if self._consumer is not None:
            await self._consumer.unsubscribe()

    async def _on_batch(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        try:
            for _, envelope in batch:
                if envelope["type"] == DELIVERED:
                    await self._answer(envelope)
        except Exception as error:
            self.failure = error
            raise

    async def _answer(self, perception: Envelope) -> None:
        decision = perception["data"].get("decision")
        if decision is None or decision["controller"]["id"] != self.controller.controller_id:
            return  # a vez é de outro controlador
        proposal = dict(self.controller.decide(perception["data"]["view"]))
        if (
            decision is not None
            and decision["reason"] == "action_rejected"
            and proposal == self._last
        ):
            # A mesma proposta acabou de ser recusada: repetir só repetiria a recusa.
            proposal = {"action": "wait", "params": {"ticks": 15}, "intent": "esperar (recusado)"}
        self._last = proposal
        data: dict[str, Any] = {"avatar_id": self._avatar, **proposal}
        envelope = command_envelope(
            self._worldid,
            str(perception["cartridge"]),
            self.controller.controller_type,
            self.controller.controller_id,
            self._ids.derive(str(perception["id"]), "command"),
            int(perception["seq"]),
            self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            data,
        )
        envelope["causationid"] = perception["id"]
        if perception.get("correlationid"):
            envelope["correlationid"] = perception["correlationid"]
        for key in ("tick", "simtime"):
            if perception.get(key) is not None:
                envelope[key] = perception[key]
        await self._bus.publish(f"campsverso.{self._worldid}.cmd.action.propose.v1", envelope)
        self.answered += 1
