"""Serviço do kernel: envolve o núcleo com IO, carimba envelopes e usa o barramento (ADR-0038)."""

from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_kernel.core import KernelCore
from campsverso_kernel.facts import Fact
from campsverso_ports import Envelope, EventBus, IdGenerator, Subscription, WallClock

_RECENT_IDS = 10_000  # seq -> id, para resolver causationid entre fatos próximos


class KernelService:
    def __init__(self, core: KernelCore, bus: EventBus, clock: WallClock, ids: IdGenerator) -> None:
        self.core = core
        self._bus = bus
        self._clock = clock
        self._ids = ids
        self._worldid = core.config.worldid
        self._source = f"/kernel/{self._worldid}"
        self._ids_by_seq: OrderedDict[int, str] = OrderedDict()
        self._subscription: Subscription | None = None

    async def start(self) -> None:
        self._subscription = await self._bus.subscribe(
            f"campsverso.{self._worldid}.cmd.>", self._on_command
        )
        self.core.start()
        await self.flush()

    async def stop(self) -> None:
        if self._subscription is not None:
            await self._subscription.unsubscribe()

    async def _on_command(self, _: str, envelope: Envelope) -> None:
        self.core.submit(envelope)
        await self.flush()

    async def run_ticks(self, ticks: int) -> None:
        for _ in range(ticks):
            self.core.step()
            await self.flush()

    async def flush(self) -> None:
        for fact in self.core.drain():
            envelope = self._envelope(fact)
            avatar_id = fact.data.get("avatar_id")
            await self._bus.publish(subject(fact.type, self._worldid, avatar_id), envelope)

    def _envelope(self, fact: Fact) -> dict[str, Any]:
        info = CONTRACT_TYPES[fact.type]
        event_id = self._ids.new_id()
        self._ids_by_seq[fact.seq] = event_id
        if len(self._ids_by_seq) > _RECENT_IDS:
            self._ids_by_seq.popitem(last=False)
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            "id": event_id,
            "source": self._source,
            "type": fact.type,
            "time": self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "datacontenttype": "application/json",
            "dataschema": info.dataschema,
            "worldid": self._worldid,
            "cartridge": self.core.definition.top.id,
            "tick": fact.tick,
            "simtime": self.core.calendar.simtime_iso(fact.tick),
            "seq": fact.seq,
            "actor": "system/kernel",
            "provenance": "simulated",
            "visibility": info.visibility,
            "data": _plain(fact.data),
        }
        avatar_id = fact.data.get("avatar_id")
        if avatar_id is not None:
            envelope["subject"] = f"avatar/{avatar_id}"
        causation = (
            self._ids_by_seq.get(fact.caused_by)
            if isinstance(fact.caused_by, int)
            else fact.caused_by
        )
        if causation:
            envelope["causationid"] = causation
        correlation = self._ids.new_id() if fact.opens_correlation else fact.correlation
        if correlation:
            envelope["correlationid"] = correlation
        return envelope


def _plain(value: Any) -> Any:
    """Cópia em tipos JSON simples (MappingProxyType e tuplas viram dict e list)."""
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]  # pyright: ignore[reportUnknownVariableType]
    return value
