"""Guarda de orçamento (ADR-0058): soma o custo das chamadas de modelo e pausa o mundo no teto.

Consome `llm.call.completed` do stream `observer` com um consumidor durável e conta só as chamadas
cobradas (`charged`), por dia simulado (pelo tick do envelope) e no total do mundo. Publica
`ops.budget.threshold_reached` em 50, 80 e 100% de cada teto e, ao chegar a 100%,
`ops.budget.exceeded` e `cmd.clock.pause` com `reason: budget`. O livro-caixa vai para um arquivo
antes de cada confirmação; depois de uma queda, a guarda retoma dele e o JetStream entrega o
resto. Só o operador retoma o mundo; se o teto continuar estourado, a próxima chamada cobrada
pausa de novo.
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any

from campsverso_budget.ledger import BudgetLedger, BudgetLimits, Notice
from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_ports import (
    BlobStore,
    Consumer,
    Envelope,
    EventBus,
    IdGenerator,
    Telemetry,
    WallClock,
)

COMPLETED = "campsverso.llm.call.completed.v1"
SESSION_STARTED = "campsverso.world.session.started.v1"
THRESHOLD = "campsverso.ops.budget.threshold_reached.v1"
EXCEEDED = "campsverso.ops.budget.exceeded.v1"
PAUSE = "campsverso.cmd.clock.pause.v1"
DEFAULT_TICK_SECONDS = 60


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
    ) -> None:
        self._worldid = worldid
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
        self._seq = 0
        self.paused_times = 0
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

    async def stop(self) -> None:
        for consumer in (self._observer, self._world):
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
                day = self._day(int(envelope["tick"]))
                notices = self.ledger.record(
                    str(envelope["id"]), day, float(envelope["data"]["cost_usd"])
                )
                for notice in notices:
                    await self._announce(notice, envelope)
            self._save()
        except Exception as error:
            self.failure = error
            raise

    async def _announce(self, notice: Notice, cause: Mapping[str, Any]) -> None:
        data: dict[str, Any] = {
            "scope": notice.scope,
            "spent_usd": notice.spent_usd,
            "limit_usd": notice.limit_usd,
        }
        if notice.day is not None:
            data["day"] = notice.day
        await self._publish(
            THRESHOLD, {**data, "threshold_pct": notice.threshold_pct}, cause, "system/budget"
        )
        if notice.exceeded:
            await self._publish(PAUSE, {"reason": "budget"}, cause, "system/budget")
            await self._publish(EXCEEDED, {**data, "paused": True}, cause, "system/budget")
            self.paused_times += 1
            self._telemetry.warning(
                "budget.exceeded",
                scope=notice.scope,
                day=notice.day,
                spent_usd=notice.spent_usd,
                limit_usd=notice.limit_usd,
            )

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
