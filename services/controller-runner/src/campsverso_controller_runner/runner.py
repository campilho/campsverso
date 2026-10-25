"""Controller-runner: responde a cada entrega da percepção com uma proposta de ação (escopo §5).

O ciclo: o kernel pede uma decisão, a percepção manda a foto (ou, para a mente, o delta; ADR-0056)
com o motivo do pedido e o controlador da vez, e o controlador com a posse responde com
`cmd.action.propose`, levando o mesmo correlationid. Basta a entrega: o runner não depende da
ordem entre dois eventos (ADR-0048). O id do comando é derivado do id da entrega: se o runner cair
depois de publicar e antes de confirmar, a proposta repetida é descartada pelo kernel (ADR-0046).

A mente (ADR-0059) é assíncrona, porque a chamada ao modelo leva segundos. Ela pode assumir o
avatar ao subir e devolvê-lo ao descer, e desiste depois de falhas seguidas: o runner então devolve
o avatar ao controlador padrão do cartucho. Uma entrega publicada antes de a última proposta sair
é um pedido superado: entra na janela da mente sem chamada ao modelo, porque o kernel pede de novo
quando a ação acaba, e os eventos dela são a única cópia do que aconteceu no meio-tempo.
"""

from collections.abc import Mapping, Sequence
from datetime import datetime
from importlib.metadata import entry_points
from typing import Any, Protocol, cast, runtime_checkable

from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_mind import Mind
from campsverso_ports import Consumer, Envelope, EventBus, IdGenerator, Telemetry, WallClock

DECISION = "campsverso.avatar.decision_requested.v1"
DELIVERED = "campsverso.perception.delivered.v1"
UPDATED = "campsverso.perception.updated.v1"
PROPOSE = "campsverso.cmd.action.propose.v1"
POSSESS = "campsverso.cmd.avatar.possess.v1"
RELEASE = "campsverso.cmd.avatar.release.v1"
ENTRY_POINT_GROUP = "campsverso.controllers"
MINDS_GROUP = "campsverso.minds"
WAIT_AFTER_REJECTION: Mapping[str, Any] = {
    "action": "wait",
    "params": {"ticks": 15},
    "intent": "esperar (recusado)",
}


class Controller(Protocol):
    """O que um controlador implementa. O script do cartucho segue esta forma sem importá-la."""

    @property
    def controller_type(self) -> str: ...

    @property
    def controller_id(self) -> str: ...

    def decide(self, view: Mapping[str, Any]) -> Mapping[str, Any]:
        """A `view` de `perception.delivered.v1` vira {action, params, intent?}."""
        ...


@runtime_checkable
class AsyncController(Protocol):
    """A mente (ADR-0059): decide sobre a entrega inteira, foto ou delta, de forma assíncrona."""

    @property
    def controller_type(self) -> str: ...

    @property
    def controller_id(self) -> str: ...

    @property
    def gave_up(self) -> bool: ...

    def observe(self, delivery: Mapping[str, Any]) -> None:
        """Uma entrega superada: entra na janela sem pedir decisão ao modelo."""
        ...

    async def decide(self, delivery: Mapping[str, Any]) -> Mapping[str, Any] | None:
        """Os dados de `perception.delivered.v1` ou `perception.updated.v1` viram uma proposta;
        `None` quando a mente desistiu."""
        ...

    async def after_proposal(self) -> None:
        """Depois de a proposta sair: a reflexão da noite, se for a hora (ADR-0060)."""
        ...

    def drain_events(self) -> Sequence[Mapping[str, Any]]:
        """Eventos `observer` que a mente produziu (`{type, data}`), para o runner publicar."""
        ...


class SimTime:
    """O relógio simulado visto pelo runner (a última entrega), para o medidor de chamadas."""

    def __init__(self) -> None:
        self.tick = 0
        self.simtime = ""

    def __call__(self) -> tuple[int, str]:
        return self.tick, self.simtime


def load_controller(name: str) -> Controller:
    """Controladores instalados, registrados no grupo `campsverso.controllers` (ADR-0011)."""
    found = {ep.name: ep for ep in entry_points(group=ENTRY_POINT_GROUP)}
    if name not in found:
        raise LookupError(f"controlador {name!r} não encontrado ({sorted(found)})")
    return cast(Controller, found[name].load())


def load_mind(name: str) -> Mind:
    """Mentes instaladas, registradas no grupo `campsverso.minds` (ADR-0059)."""
    found = {ep.name: ep for ep in entry_points(group=MINDS_GROUP)}
    if name not in found:
        raise LookupError(f"mente {name!r} não encontrada ({sorted(found)})")
    return cast(Mind, found[name].load())


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


def _iso(moment: datetime) -> str:
    return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _parse(time: object) -> datetime | None:
    if not isinstance(time, str):
        return None
    try:
        return datetime.fromisoformat(time.replace("Z", "+00:00"))
    except ValueError:
        return None


class ControllerRunner:
    def __init__(
        self,
        worldid: str,
        avatar_id: str,
        controller: Controller | AsyncController,
        bus: EventBus,
        ids: IdGenerator,
        clock: WallClock,
        telemetry: Telemetry,
        *,
        cartridge: str | None = None,
        possess: bool = False,
        sim_time: SimTime | None = None,
    ) -> None:
        if possess and cartridge is None:
            raise ValueError("assumir o avatar exige o cartucho do mundo (vai no envelope)")
        self._worldid = worldid
        self._avatar = avatar_id
        self.controller = controller
        self._mind: AsyncController | None = (
            controller if isinstance(controller, AsyncController) else None
        )
        self._bus = bus
        self._ids = ids
        self._clock = clock
        self._telemetry = telemetry
        self._cartridge = cartridge
        self._possess = possess
        self.sim_time = sim_time or SimTime()
        self._last: Mapping[str, Any] | None = None
        self._last_proposal_at: datetime | None = None
        self._consumer: Consumer | None = None
        self._out_seq = 0
        self.answered = 0
        self.superseded = 0
        self.memory_events = 0
        self.possessing = False
        self.released = 0
        self.failure: BaseException | None = None

    @property
    def is_mind(self) -> bool:
        return self._mind is not None

    async def start(self) -> None:
        w, a = self._worldid, self._avatar
        durable = f"controller-{w}-{a}-{self.controller.controller_type}"
        # A mente recebe fotos e deltas; script e replay continuam só com a foto (e o consumidor
        # durável que já existe no JetStream mantém o filtro de sempre).
        kind = "perception.>" if self.is_mind else "perception.delivered.v1"
        self._consumer = await self._bus.consume(
            f"campsverso.{w}.agent.{a}.{kind}", durable, self._on_batch
        )
        if self._possess:
            ref = {"type": self.controller.controller_type, "id": self.controller.controller_id}
            await self._control(POSSESS, {"avatar_id": a, "controller": ref})
            self.possessing = True
            self._telemetry.info("controller.possessed", avatar=a, controller=ref["id"])

    async def stop(self) -> None:
        if self.possessing:
            await self.release("stopped")
        if self._consumer is not None:
            await self._consumer.unsubscribe()

    async def release(self, reason: str) -> None:
        """Devolve o avatar ao controlador padrão do cartucho (o kernel sabe qual é)."""
        await self._control(RELEASE, {"avatar_id": self._avatar})
        self.possessing = False
        self.released += 1
        self._telemetry.warning("controller.released", avatar=self._avatar, reason=reason)

    async def _control(self, command_type: str, data: Mapping[str, Any]) -> None:
        info = CONTRACT_TYPES[command_type]
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            "id": self._ids.new_id(),
            "source": f"/controller-runner/{self.controller.controller_id}",
            "type": command_type,
            "time": _iso(self._clock.now()),
            "datacontenttype": "application/json",
            "dataschema": info.dataschema,
            "worldid": self._worldid,
            "cartridge": self._cartridge,
            "seq": self._out_seq,
            "actor": self.controller.controller_id,
            "provenance": "simulated",
            "visibility": info.visibility,
            "data": dict(data),
        }
        self._out_seq += 1
        await self._bus.publish(subject(command_type, self._worldid), envelope)

    async def _on_batch(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        try:
            for _, envelope in batch:
                if envelope["type"] in (DELIVERED, UPDATED):
                    await self._answer(envelope)
        except Exception as error:
            self.failure = error
            raise

    async def _answer(self, perception: Envelope) -> None:
        data = cast(Mapping[str, Any], perception["data"])
        decision = cast(Mapping[str, Any] | None, data.get("decision"))
        if decision is None or decision["controller"]["id"] != self.controller.controller_id:
            return  # a vez é de outro controlador
        if perception.get("tick") is not None:
            self.sim_time.tick = int(perception["tick"])
            self.sim_time.simtime = str(perception.get("simtime") or "")
        proposal = await self._decide(perception, data, decision)
        if proposal is None:
            return
        if decision["reason"] == "action_rejected" and proposal == self._last:
            # A mesma proposta acabou de ser recusada: repetir só repetiria a recusa.
            proposal = dict(WAIT_AFTER_REJECTION)
        self._last = proposal
        payload: dict[str, Any] = {"avatar_id": self._avatar, **proposal}
        envelope = command_envelope(
            self._worldid,
            str(perception["cartridge"]),
            self.controller.controller_type,
            self.controller.controller_id,
            self._ids.derive(str(perception["id"]), "command"),
            int(perception["seq"]),
            _iso(self._clock.now()),
            payload,
        )
        envelope["causationid"] = perception["id"]
        if perception.get("correlationid"):
            envelope["correlationid"] = perception["correlationid"]
        for key in ("tick", "simtime"):
            if perception.get(key) is not None:
                envelope[key] = perception[key]
        await self._bus.publish(f"campsverso.{self._worldid}.cmd.action.propose.v1", envelope)
        self._last_proposal_at = self._clock.now()
        self.answered += 1
        if self._mind is not None:
            await self._mind.after_proposal()
            await self._publish_memory(str(perception["cartridge"]))

    async def _publish_memory(self, cartridge: str) -> None:
        """O que a mente anotou, refletiu e passou a acreditar vai para o operador e o arquivo."""
        assert self._mind is not None
        for event in self._mind.drain_events():
            event_type = str(event["type"])
            info = CONTRACT_TYPES[event_type]
            tick, simtime = self.sim_time()
            envelope: dict[str, Any] = {
                "specversion": "1.0",
                "id": self._ids.new_id(),
                "source": f"/controller-runner/{self.controller.controller_id}",
                "type": event_type,
                "time": _iso(self._clock.now()),
                "datacontenttype": "application/json",
                "dataschema": info.dataschema,
                "worldid": self._worldid,
                "cartridge": cartridge,
                "tick": tick,
                "seq": self._out_seq,
                "actor": self.controller.controller_id,
                "provenance": "simulated",
                "visibility": info.visibility,
                "data": dict(cast(Mapping[str, Any], event["data"])),
            }
            if simtime:
                envelope["simtime"] = simtime
            self._out_seq += 1
            await self._bus.publish(subject(event_type, self._worldid), envelope)
            self.memory_events += 1

    async def _decide(
        self, perception: Envelope, data: Mapping[str, Any], decision: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        if self._mind is None:
            if perception["type"] != DELIVERED:
                return None  # script e replay só entendem a foto
            script = cast(Controller, self.controller)
            # A foto e o motivo do pedido (uma recusa, um despertar): o script 2 não repete uma
            # proposta recusada, e o 3 anota o que a última ação fez (ADR-0070).
            view = {**cast(Mapping[str, Any], data["view"]), "decision": decision}
            return dict(script.decide(view))
        published = _parse(perception.get("time"))
        if (
            self._last_proposal_at is not None
            and published is not None
            and published < self._last_proposal_at
        ):
            # Pedido superado: chegou antes de a última proposta sair; o kernel vai pedir de novo.
            self._mind.observe(data)
            self.superseded += 1
            self._telemetry.info("controller.superseded", reason=decision["reason"])
            return None
        proposal = await self._mind.decide(data)
        if self._mind.gave_up:
            self._telemetry.error("controller.gave_up", avatar=self._avatar)
            if self.possessing:
                await self.release("model_failures")
            return None
        return None if proposal is None else dict(proposal)
