"""Calendário simulado: converte ticks em data, hora e dia (tempo §2, §3; ADR-0038)."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from campsverso_cartridge_api import ClockDef, YearDef

MINUTES_PER_DAY = 1440
MS_PER_DAY = 86_400_000
DAYS_PER_YEAR = 365  # o ano do calendário; o bissexto não muda as estações


def month_day(value: str) -> tuple[int, int]:
    """ "MM-DD" -> (mês, dia), conferido num ano bissexto (29/02 vale)."""
    month, day = (int(part) for part in value.split("-"))
    date(2024, month, day)  # ValueError fora do calendário
    return month, day


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
    tick_ms: (
        int  # o passo em milissegundos inteiros (ADR-0081): 60.000 na fazenda, 250 no escritório
    )
    day_starts_at: int  # minuto do dia em que o dia vira
    year: YearDef | None = None  # o ano acelerado com estações (ADR-0067)

    @classmethod
    def create(cls, start: datetime, clock: ClockDef, year: YearDef | None = None) -> Calendar:
        if start.tzinfo is None:
            raise ValueError("a data-base do calendário precisa de fuso horário")
        tick_ms = round(clock.tick_seconds * 1000)
        if tick_ms <= 0 or tick_ms != clock.tick_seconds * 1000 or 60_000 % tick_ms != 0:
            raise ValueError(
                "o tick precisa ser de milissegundos inteiros que dividem um minuto"
                " (horários HH:MM exatos)"
            )
        return cls(start, tick_ms, parse_hhmm(clock.day_starts_at), year)

    @property
    def tick_seconds(self) -> float:
        """O passo em segundos, para as contas de tempo real (a escala, o passo de tela)."""
        return self.tick_ms / 1000

    @property
    def whole_seconds(self) -> int | None:
        """O passo em segundos inteiros, quando ele cabe neles; None num tick menor que o segundo
        ou quebrado (o `session.started` vai então na v2, com `tick_ms`)."""
        return self.tick_ms // 1000 if self.tick_ms % 1000 == 0 else None

    @property
    def ticks_per_day(self) -> int:
        return MS_PER_DAY // self.tick_ms

    def date_of(self, day: int) -> date | None:
        """A data do calendário no dia `day` (ADR-0067): o ano do mundo começa em `year.start` e
        cabe em `year.days` dias simulados. Sem ano declarado, None. Não toca no `simtime`."""
        if self.year is None:
            return None
        month, first = month_day(self.year.start)
        return date(self.start.year, month, first) + timedelta(
            days=((day - 1) * DAYS_PER_YEAR) // self.year.days
        )

    def season(self, day: int) -> str | None:
        """A estação que vale na data do dia: a do último começo até ela, voltando à do fim do
        ano antes do primeiro começo (o verão de dezembro segue em janeiro)."""
        when = self.date_of(day)
        if when is None or self.year is None:
            return None
        starts = sorted((month_day(start), name) for name, start in self.year.seasons)
        current = starts[-1][1]
        for start, name in starts:
            if start <= (when.month, when.day):
                current = name
        return current

    @property
    def ticks_per_minute(self) -> int:
        return 60_000 // self.tick_ms

    def simtime(self, tick: int) -> datetime:
        return self.start + timedelta(milliseconds=tick * self.tick_ms)

    def simtime_iso(self, tick: int) -> str:
        return self.simtime(tick).isoformat(timespec="seconds")

    def _absolute_minute(self, tick: int) -> int:
        start_minute = self.start.hour * 60 + self.start.minute
        return start_minute + (tick * self.tick_ms) // 60_000

    def minute_of_day(self, tick: int) -> int:
        return self._absolute_minute(tick) % MINUTES_PER_DAY

    def is_minute_start(self, tick: int) -> bool:
        return self._ms_into_minute(tick) == 0

    def _ms_into_minute(self, tick: int) -> int:
        return (self.start.second * 1000 + tick * self.tick_ms) % 60_000

    def day(self, tick: int) -> int:
        """Dia 1 é o dia que contém o tick 0; o dia vira em `day_starts_at`."""

        def index(t: int) -> int:
            return (self._absolute_minute(t) - self.day_starts_at) // MINUTES_PER_DAY

        return 1 + index(tick) - index(0)

    def ticks_until(self, tick: int, minute: int) -> int:
        """Ticks até a próxima vez em que o relógio marca `minute` (de 1 até um dia inteiro).

        Num tick menor que um minuto (o escritório, ADR-0078), o tick de agora pode cair no meio
        de um minuto: os segundos já passados nele saem da conta, e o salto cai no minuto exato."""
        delta = (minute - self.minute_of_day(tick)) % MINUTES_PER_DAY or MINUTES_PER_DAY
        return (delta * 60_000 - self._ms_into_minute(tick)) // self.tick_ms
