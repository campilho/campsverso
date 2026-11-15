"""Guarda de orçamento (ADR-0058, ADR-0080): soma o custo das chamadas de modelo e age no teto.

Consome `llm.call.completed` do stream `observer` com um consumidor durável e conta só as chamadas
cobradas (`charged`), por dia simulado (pelo tick do envelope), por pedido do escritório (o
`ticket_id` da chamada) e no total do mundo. Publica `ops.budget.threshold_reached.v2` em 50, 80 e
100% de cada teto e, ao chegar a 100%, `ops.budget.exceeded.v2`. O que acontece no teto do dia e
no total é do mundo (`budget.on_exceeded`):
- `pause` (as fazendas): a guarda pede `cmd.clock.pause` com `reason: budget`. Só o operador
  retoma; se o teto continuar estourado, a próxima chamada cobrada pausa de novo, sem repetir o
  limiar;
- `mind_off` (o escritório): o mundo segue, e a mente, ao ler o aviso, desliga e deixa a rotina
  conduzir o dev.
No teto de um pedido, o mundo nunca pausa: a mente larga aquele pedido.

O operador muda os tetos com o mundo vivo (`cmd.ops.budget.set`); a guarda responde com
`ops.budget.limits_changed`. A cada `pulse_seconds`, ela dá sinal de vida em
`campsverso.<mundo>.live.budget` (os tetos, o gasto e o que está estourado), num assunto que nenhum
stream guarda; sem o sinal, a mente do escritório desliga. O livro-caixa vai para um arquivo antes
de cada confirmação; depois de uma queda, a guarda retoma dele e o JetStream entrega o resto.
"""

import contextlib
import json
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from campsverso_budget.ledger import BudgetLedger, BudgetLimits, Notice
from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_ports import (
    BlobStore,
    BusUnavailableError,
    Consumer,
    Envelope,
    EventBus,
    IdGenerator,
    Telemetry,
    WallClock,
)

COMPLETED = "campsverso.llm.call.completed.v1"
SESSION_STARTED = "campsverso.world.session.started.v1"
THRESHOLD = "campsverso.ops.budget.threshold_reached.v2"
EXCEEDED = "campsverso.ops.budget.exceeded.v2"
LIMITS_CHANGED = "campsverso.ops.budget.limits_changed.v1"
SET = "campsverso.cmd.ops.budget.set.v1"
PAUSE = "campsverso.cmd.clock.pause.v1"
PULSE = "campsverso.live.budget.v1"
DEFAULT_TICK_SECONDS = 60
type OnExceeded = Literal["pause", "mind_off"]


class BudgetService:
    def __init__(
        self,
        worldid: str,
        limits: BudgetLimits,
        bus: EventBus,
        blobs: BlobStore,
        clock: WallClock,
        ids: IdGenerator,
        telemetry: Telemetry,
        on_exceeded: OnExceeded = "pause",
    ) -> None:
        self._worldid = worldid
        self._on_exceeded: OnExceeded = on_exceeded
        self._bus = bus
        self._blobs = blobs
        self._clock = clock
        self._ids = ids
        self._telemetry = telemetry
        self._key = f"{worldid}/ledger.json"
        self.ledger = self._load(limits)
        self._tick_seconds = DEFAULT_TICK_SECONDS
        self._world: Consumer | None = None
        self._observer: Consumer | None = None
        self._commands: Consumer | None = None
        self._seq = 0
        self.paused_times = 0
        self._pulse_seconds: float | None = None
        self.failure: BaseException | None = None

    def _load(self, limits: BudgetLimits) -> BudgetLedger:
        try:
            return BudgetLedger(limits, json.loads(self._blobs.get(self._key)))
        except FileNotFoundError, KeyError:
            return BudgetLedger(limits)

    def _save(self) -> None:
        self._blobs.put(self._key, json.dumps(self.ledger.export(), ensure_ascii=False).encode())

    async def start(self) -> None:
        w = self._worldid
        self._world = await self._bus.consume(
            f"campsverso.{w}.world.session.started.v1", f"budget-{w}-world", self._on_world
        )
        self._observer = await self._bus.consume(
            f"campsverso.{w}.observer.llm.>", f"budget-{w}-llm", self._on_llm
        )
        self._commands = await self._bus.consume(subject(SET, w), f"budget-{w}-set", self._on_set)

    async def stop(self) -> None:
        for consumer in (self._commands, self._observer, self._world):
            if consumer is not None:
                await consumer.unsubscribe()

    async def _on_world(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        for _, envelope in batch:
            if envelope["type"] == SESSION_STARTED:
                self._tick_seconds = int(envelope["data"]["tick_seconds"])

    def _day(self, tick: int) -> int:
        return tick // (86_400 // self._tick_seconds) + 1

    async def _on_llm(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        try:
            for _, envelope in batch:
                if envelope["type"] != COMPLETED or not envelope["data"].get("charged"):
                    continue
                data = envelope["data"]
                day = self._day(int(envelope["tick"]))
                ticket = data.get("ticket_id")
                notices = self.ledger.record(
                    str(envelope["id"]),
                    day,
                    float(data["cost_usd"]),
                    None if ticket is None else str(ticket),
                )
                # Um só cmd.clock.pause por chamada, mesmo com os dois tetos; o do pedido nunca
                # pausa.
                pause = self._on_exceeded == "pause"
                for notice in notices:
                    stops = pause and notice.scope != "ticket"
                    await self._announce(notice, envelope, pause=stops)
                    pause = pause and not (stops and notice.exceeded)
            self._save()
        except Exception as error:
            self.failure = error
            raise

    async def _announce(self, notice: Notice, cause: Mapping[str, Any], *, pause: bool) -> None:
        data: dict[str, Any] = {
            "scope": notice.scope,
            "spent_usd": notice.spent_usd,
            "limit_usd": notice.limit_usd,
        }
        if notice.day is not None:
            data["day"] = notice.day
        if notice.ticket_id is not None:
            data["ticket_id"] = notice.ticket_id
        if not notice.repeated:  # o limiar avisa uma vez; a pausa se repete
            await self._publish(
                THRESHOLD, {**data, "threshold_pct": notice.threshold_pct}, cause, "system/budget"
            )
        if notice.exceeded:
            if pause:
                await self._publish(PAUSE, {"reason": "budget"}, cause, "system/budget")
                self.paused_times += 1
            # No mundo que pausa, o dia e o total pausam, mesmo quando o pedido de pausa já saiu
            # pelo outro teto da mesma chamada.
            paused = self._on_exceeded == "pause" and notice.scope != "ticket"
            await self._publish(EXCEEDED, {**data, "paused": paused}, cause, "system/budget")
            self._telemetry.warning(
                "budget.exceeded",
                scope=notice.scope,
                day=notice.day,
                ticket_id=notice.ticket_id,
                spent_usd=notice.spent_usd,
                limit_usd=notice.limit_usd,
            )

    async def _on_set(self, batch: Sequence[tuple[str, Envelope]]) -> None:
        """Os tetos novos do operador (ADR-0080). O contrato já foi conferido no gateway; aqui, o
        livro-caixa muda, vai para o arquivo e o fato sai, com um sinal de vida logo atrás."""
        try:
            changed = False
            for _, envelope in batch:
                if envelope["type"] != SET:
                    continue
                data = envelope["data"]
                self.ledger.set_limits(self.ledger.limits.changed(data))
                self._save()
                await self._publish(
                    LIMITS_CHANGED,
                    {**self.ledger.limits.export(), "reason": str(data["reason"])},
                    envelope,
                    "system/budget",
                )
                self._telemetry.info("budget.limits_changed", **self.ledger.limits.export())
                changed = True
            if changed and self._pulse_seconds is not None:
                await self.announce_pulse(self._pulse_seconds)
        except Exception as error:
            self.failure = error
            raise

    async def announce_pulse(self, pulse_seconds: float) -> None:
        """O sinal de vida (ADR-0080), como o pulso do kernel (ADR-0051): num assunto que nenhum
        stream guarda. Não é fato, e perdê-lo não perde nada: o próximo tenta de novo."""
        self._pulse_seconds = pulse_seconds
        ledger = self.ledger
        message: dict[str, Any] = {
            "type": PULSE,
            "worldid": self._worldid,
            "limits": ledger.limits.export(),
            "spent_total_usd": ledger.total,
            "exceeded": ledger.exceeded_now(),
            "pulse_seconds": pulse_seconds,
            "sent_at": self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        }
        if ledger.last_day is not None:
            message["day"] = ledger.last_day
            message["spent_day_usd"] = ledger.by_day.get(str(ledger.last_day), 0.0)
        with contextlib.suppress(BusUnavailableError):
            await self._bus.announce(f"campsverso.{self._worldid}.live.budget", message)

    async def _publish(
        self, event_type: str, data: Mapping[str, Any], cause: Mapping[str, Any], actor: str
    ) -> None:
        info = CONTRACT_TYPES[event_type]
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            "id": self._ids.new_id(),
            "source": f"/budget/{self._worldid}",
            "type": event_type,
            "time": self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "datacontenttype": "application/json",
            "dataschema": info.dataschema,
            "worldid": self._worldid,
            "cartridge": cause["cartridge"],
            "tick": cause["tick"],
            "simtime": cause["simtime"],
            "seq": self._seq,
            "actor": actor,
            "provenance": "simulated",
            "visibility": info.visibility,
            "causationid": cause["id"],
            "data": dict(data),
        }
        self._seq += 1
        await self._bus.publish(subject(event_type, self._worldid), envelope)
