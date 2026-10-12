"""Calendário simulado: converte ticks em data, hora e dia (tempo §2, §3; ADR-0038)."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from campsverso_cartridge_api import ClockDef

MINUTES_PER_DAY = 1440


def parse_hhmm(value: str) -> int:
    hours, minutes = value.split(":")
    minute = int(hours) * 60 + int(minutes)
    if not 0 <= minute < MINUTES_PER_DAY:
        raise ValueError(f"horário inválido: {value}")
    return minute


def format_hhmm(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


@dataclass(frozen=True, slots=True)
class Calendar:
    start: datetime  # com fuso; tick 0
    tick_seconds: int
    day_starts_at: int  # minuto do dia em que o dia vira

    @classmethod
    def create(cls, start: datetime, clock: ClockDef) -> Calendar:
        if start.tzinfo is None:
            raise ValueError("a data-base do calendário precisa de fuso horário")
        if clock.tick_seconds <= 0 or 60 % clock.tick_seconds != 0:
            raise ValueError("o tick precisa dividir um minuto (horários HH:MM exatos)")
        return cls(start, clock.tick_seconds, parse_hhmm(clock.day_starts_at))

    @property
    def ticks_per_minute(self) -> int:
        return 60 // self.tick_seconds

    def simtime(self, tick: int) -> datetime:
        return self.start + timedelta(seconds=tick * self.tick_seconds)

    def simtime_iso(self, tick: int) -> str:
        return self.simtime(tick).isoformat(timespec="seconds")

    def _absolute_minute(self, tick: int) -> int:
        start_minute = self.start.hour * 60 + self.start.minute
        return start_minute + (tick * self.tick_seconds) // 60

    def minute_of_day(self, tick: int) -> int:
        return self._absolute_minute(tick) % MINUTES_PER_DAY

    def is_minute_start(self, tick: int) -> bool:
        return (self.start.second + tick * self.tick_seconds) % 60 == 0

    def day(self, tick: int) -> int:
        """Dia 1 é o dia que contém o tick 0; o dia vira em `day_starts_at`."""

        def index(t: int) -> int:
            return (self._absolute_minute(t) - self.day_starts_at) // MINUTES_PER_DAY

        return 1 + index(tick) - index(0)

    def ticks_until(self, tick: int, minute: int) -> int:
        """Ticks até a próxima vez em que o relógio marca `minute` (de 1 até um dia inteiro)."""
        delta = (minute - self.minute_of_day(tick)) % MINUTES_PER_DAY or MINUTES_PER_DAY
        return delta * self.ticks_per_minute
