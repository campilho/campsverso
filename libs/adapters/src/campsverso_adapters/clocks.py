"""Adaptadores da porta WallClock."""

import time
from datetime import UTC, datetime, timedelta


class SystemWallClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()


class FakeWallClock:
    """Relógio controlado pelo teste."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start or datetime(2026, 10, 10, 9, 0, tzinfo=UTC)
        self._monotonic = 0.0

    def now(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._monotonic

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)
        self._monotonic += seconds
