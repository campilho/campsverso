"""Controlador replay: reenvia as propostas gravadas, no tick em que valeram (escopo §5).

As propostas e os ticks saem do arquivo de eventos: cada comando gravado tem um fato do kernel
causado por ele (`action.accepted` traz `applied_tick`; `action.rejected`, o próprio tick).
No primeiro pedido de decisão endereçado a ele, o replay manda todas, cada uma com `at_tick`;
o kernel as guarda e aplica cada uma no seu tick (ADR-0047). Isso reproduz até uma sessão humana
do modo contínuo, em que os comandos não chegavam em resposta a pedidos.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from campsverso_controller_runner.runner import DECISION, PROPOSE, command_envelope
from campsverso_ports import Consumer, Envelope, EventBus, IdGenerator, Telemetry, WallClock

ACCEPTED = "campsverso.action.accepted.v1"
REJECTED = "campsverso.action.rejected.v1"


@dataclass(frozen=True)
class Recorded:
    tick: int
    data: Mapping[str, Any]  # avatar_id, action, params, intent?


def recorded_proposals(envelopes: Iterable[Mapping[str, Any]], avatar_id: str) -> list[Recorded]:
    """Propostas do avatar que o kernel processou, em ordem de aplicação."""
    commands: dict[str, Mapping[str, Any]] = {}
    applied: dict[str, tuple[int, int]] = {}  # id do comando -> (tick, seq do fato)
    for envelope in envelopes:
        kind = envelope.get("type")
        if kind == PROPOSE and envelope["data"].get("avatar_id") == avatar_id:
            commands[str(envelope["id"])] = envelope["data"]
        elif kind in (ACCEPTED, REJECTED) and envelope.get("causationid"):
            data = envelope["data"]
            tick = int(data["applied_tick"]) if kind == ACCEPTED else int(envelope["tick"])
            applied.setdefault(str(envelope["causationid"]), (tick, int(envelope["seq"])))
    ordered = sorted((applied[cid], cid) for cid in commands if cid in applied)
    recorded: list[Recorded] = []
    for (tick, _), cid in ordered:
        data = {k: v for k, v in commands[cid].items() if k != "at_tick"}
        recorded.append(Recorded(tick, data))
    return recorded


class ReplayRunner:
    controller_type = "replay"

    def __init__(
        self,
        worldid: str,
        avatar_id: str,
        controller_id: str,
        recording: Sequence[Recorded],
        bus: EventBus,
        ids: IdGenerator,
        clock: WallClock,
        telemetry: Telemetry,
    ) -> None:
        self._worldid = worldid
        self._avatar = avatar_id
        self.controller_id = controller_id
        self._recording = recording
        self._bus = bus
        self._ids = ids
        self._clock = clock
        self._telemetry = telemetry
        self._consumer: Consumer | None = None
        self.sent = 0
        self.failure: BaseException | None = None

    async def start(self) -> None:
        w, a = self._worldid, self._avatar
        self._consumer = await self._bus.consume(
            f"campsverso.{w}.agent.{a}.avatar.decision_requested.v1",
            f"controller-{w}-{a}-replay",
            self._on_batch,
        )

    async def stop(self) -> None:
        if self._consumer is not None:
            await self._consumer.unsubscribe()

    async def _on_batch(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        for _, envelope in batch:
            mine = envelope["data"]["controller"]["id"] == self.controller_id
            if envelope["type"] == DECISION and mine and self.sent == 0:
                await self._send_all(envelope)

    async def _send_all(self, decision: Envelope) -> None:
        now = self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z")
        for seq, entry in enumerate(self._recording):
            envelope = command_envelope(
                self._worldid,
                str(decision["cartridge"]),
                self.controller_type,
                self.controller_id,
                self._ids.derive(str(decision["id"]), f"replay-{seq}"),
                seq,
                now,
                {**entry.data, "at_tick": entry.tick},
            )
            await self._bus.publish(f"campsverso.{self._worldid}.cmd.action.propose.v1", envelope)
            self.sent += 1
        self._telemetry.info("replay.sent", commands=self.sent)
