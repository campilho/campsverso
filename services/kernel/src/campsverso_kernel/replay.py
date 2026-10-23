"""Replay de um dia (A5; ADR-0047, decisão 4): reexecutar e comparar com o arquivo de eventos.

Parte do snapshot mais recente que não passa do começo do dia (no pior caso, o inicial, que nunca
é apagado), reexecuta o diário de entradas até o começo do dia seguinte e compara os fatos do dia
com os que o arquivo JSONL guardou. Iguais, provam que o dia gravado se reproduz.
"""

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from campsverso_kernel.calendar import Calendar
from campsverso_kernel.core import WorldConfig
from campsverso_kernel.definition import WorldDefinition
from campsverso_kernel.recovery import RecoveryError, reexecute
from campsverso_kernel.version import RunVersion
from campsverso_kernel.world import plain
from campsverso_ports import BlobStore, EnvelopeValidator, WorldStore

type FactKey = tuple[int, int, str, str]


@dataclass(frozen=True)
class DayReplay:
    day: int
    start: int
    end: int
    from_snapshot: str
    regenerated: list[FactKey]
    recorded: list[FactKey]

    @property
    def equal(self) -> bool:
        return self.regenerated == self.recorded

    @staticmethod
    def digest(facts: Sequence[FactKey]) -> str:
        return hashlib.sha256("\n".join(map(repr, facts)).encode()).hexdigest()

    def first_difference(self) -> tuple[FactKey | None, FactKey | None] | None:
        for regenerated, recorded in zip(self.regenerated, self.recorded, strict=False):
            if regenerated != recorded:
                return regenerated, recorded
        if len(self.regenerated) == len(self.recorded):
            return None
        shorter = min(len(self.regenerated), len(self.recorded))
        extra = self.regenerated[shorter:] or [None]
        missing = self.recorded[shorter:] or [None]
        return extra[0], missing[0]


def day_range(calendar: Calendar, day: int) -> tuple[int, int]:
    """[primeiro tick do dia, primeiro tick do dia seguinte); o dia 1 contém o tick 0."""
    if day < 1:
        raise ValueError("os dias começam em 1")
    start = 0
    for _ in range(day - 1):
        start += calendar.ticks_until(start, calendar.day_starts_at)
    return start, start + calendar.ticks_until(start, calendar.day_starts_at)


def _key(seq: int, tick: int, kind: str, data: Any) -> FactKey:
    return (seq, tick, kind, json.dumps(plain(data), sort_keys=True, ensure_ascii=False))


def replay_day(
    definition: WorldDefinition,
    config: WorldConfig,
    version: RunVersion,
    store: WorldStore,
    blobs: BlobStore,
    archive: Iterable[Mapping[str, Any]],
    day: int,
    validator: EnvelopeValidator | None = None,
) -> DayReplay:
    calendar = Calendar.create(config.start, definition.clock, definition.year)
    start, end = day_range(calendar, day)
    usable = [s for s in store.snapshots() if s.tick <= start]
    if not usable:
        raise RecoveryError(f"nenhum snapshot no começo do dia {day} ou antes dele")
    snapshot = usable[-1]
    facts = reexecute(definition, config, version, store, blobs, snapshot, end, validator)

    def wanted(seq: int, tick: int) -> bool:  # o que veio antes do snapshot não se regenera
        return start <= tick < end and seq >= snapshot.next_seq

    source = f"/kernel/{config.worldid}"
    recorded = sorted(
        _key(int(e["seq"]), int(e["tick"]), str(e["type"]), e["data"])
        for e in archive
        if e.get("source") == source and wanted(int(e["seq"]), int(e["tick"]))
    )
    regenerated = [_key(f.seq, f.tick, f.type, f.data) for f in facts if wanted(f.seq, f.tick)]
    return DayReplay(day, start, end, snapshot.ref, regenerated, recorded)
