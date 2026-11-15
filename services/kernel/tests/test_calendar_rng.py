from datetime import date, datetime, timedelta, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from campsverso_cartridge_api import ClockDef, YearDef
from campsverso_kernel.calendar import Calendar, parse_hhmm
from campsverso_kernel.rng import RngStreams, SplitMix64

BRT = timezone(timedelta(hours=-3))
CLOCK = ClockDef(tick_seconds=60, day_starts_at="06:00", phases=())
CAL = Calendar.create(datetime(2026, 10, 10, 6, 0, tzinfo=BRT), CLOCK)
# O ano da Morada do Sol (ADR-0067): 28 dias simulados, começando na primavera do hemisfério sul.
YEAR = YearDef(
    28,
    "09-22",
    (("primavera", "09-22"), ("verao", "12-21"), ("outono", "03-20"), ("inverno", "06-21")),
)
SOL = Calendar.create(datetime(2026, 10, 10, 6, 0, tzinfo=BRT), CLOCK, YEAR)


def test_tick_zero_e_o_inicio_do_projeto() -> None:
    assert CAL.simtime_iso(0) == "2026-10-10T06:00:00-03:00"
    assert CAL.day(0) == 1
    assert CAL.minute_of_day(0) == parse_hhmm("06:00")


@pytest.mark.parametrize(
    ("tick", "day", "hhmm"),
    [(1439, 1, "05:59"), (1440, 2, "06:00"), (1380, 1, "05:00"), (2879, 2, "05:59")],
)
def test_o_dia_vira_as_seis(tick: int, day: int, hhmm: str) -> None:
    assert CAL.day(tick) == day
    assert CAL.minute_of_day(tick) == parse_hhmm(hhmm)


def test_ticks_ate_o_proximo_horario() -> None:
    assert CAL.ticks_until(0, parse_hhmm("06:00")) == 1440
    assert CAL.ticks_until(0, parse_hhmm("08:00")) == 120
    assert CAL.ticks_until(1380, parse_hhmm("06:00")) == 60


def test_ticks_ate_o_horario_num_tick_menor_que_o_minuto() -> None:
    """ADR-0078: com o tick de 2 s, o tick de agora cai no meio do minuto, e o salto precisa
    cair no minuto exato; antes, chegava às 01:00:02 e o sistema das 09:00 nunca disparava."""
    office = Calendar.create(datetime(2026, 11, 16, 0, 0, tzinfo=BRT), ClockDef(2, "00:00", ()))
    assert office.ticks_until(0, parse_hhmm("01:00")) == 1800
    assert office.ticks_until(1, parse_hhmm("01:00")) == 1799  # das 00:00:02
    tick = 1 + office.ticks_until(1, parse_hhmm("09:00"))
    assert office.simtime_iso(tick) == "2026-11-16T09:00:00-03:00"
    assert office.is_minute_start(tick)
    assert office.ticks_until(16215, parse_hhmm("09:00")) == 43185  # das 09:00:30: amanhã


def test_o_tick_de_250_ms() -> None:
    """ADR-0081: o escritório anda em quartos de segundo. O calendário conta em milissegundos, e
    o salto até um horário cai no minuto exato também no meio de um segundo."""
    office = Calendar.create(datetime(2026, 11, 16, 0, 0, tzinfo=BRT), ClockDef(0.25, "00:00", ()))
    assert (office.tick_ms, office.tick_seconds, office.whole_seconds) == (250, 0.25, None)
    assert (office.ticks_per_minute, office.ticks_per_day) == (240, 345_600)
    assert office.simtime_iso(4) == "2026-11-16T00:00:01-03:00"
    assert office.simtime(1) == datetime(2026, 11, 16, 0, 0, 0, 250_000, tzinfo=BRT)
    assert office.ticks_until(0, parse_hhmm("01:00")) == 14_400
    assert office.ticks_until(3, parse_hhmm("01:00")) == 14_397  # das 00:00:00,75
    tick = 3 + office.ticks_until(3, parse_hhmm("09:00"))
    assert office.simtime_iso(tick) == "2026-11-16T09:00:00-03:00"
    assert office.is_minute_start(tick)
    assert not office.is_minute_start(tick + 1)
    assert office.minute_of_day(tick + 239) == 540
    assert office.minute_of_day(tick + 240) == 541
    assert office.day(345_599) == 1
    assert office.day(345_600) == 2
    assert CAL.whole_seconds == 60  # a fazenda segue em segundos inteiros, no session.started v1


def test_calendario_exige_fuso_e_tick_que_divide_o_minuto() -> None:
    with pytest.raises(ValueError, match="fuso"):
        Calendar.create(datetime(2026, 10, 10, 6, 0), CLOCK)
    with pytest.raises(ValueError, match="minuto"):
        Calendar.create(CAL.start, ClockDef(tick_seconds=90, day_starts_at="06:00", phases=()))
    with pytest.raises(ValueError, match="milissegundos"):  # 700 ms não divide o minuto
        Calendar.create(CAL.start, ClockDef(tick_seconds=0.7, day_starts_at="06:00", phases=()))
    with pytest.raises(ValueError, match="milissegundos"):  # meio milissegundo
        Calendar.create(CAL.start, ClockDef(tick_seconds=0.0005, day_starts_at="06:00", phases=()))


def test_splitmix64_reproduz_o_vetor_de_referencia() -> None:
    assert SplitMix64(0).next_u64() == 0xE220A8397B1DCDAF


@given(st.integers(min_value=0, max_value=2**63), st.text(min_size=1, max_size=12))
def test_fluxos_nomeados_sao_reprodutiveis(seed: int, name: str) -> None:
    first = [RngStreams(seed).get(name).random() for _ in range(1)]
    again = [RngStreams(seed).get(name).random() for _ in range(1)]
    assert first == again
    assert all(0.0 <= v < 1.0 for v in first)


@given(st.integers(min_value=0, max_value=2**32), st.integers(-50, 50), st.integers(0, 50))
def test_randint_fica_no_intervalo(seed: int, low: int, width: int) -> None:
    rng = SplitMix64(seed)
    assert all(low <= rng.randint(low, low + width) <= low + width for _ in range(20))


def test_fluxos_diferentes_sao_independentes() -> None:
    streams = RngStreams(42)
    assert streams.get("weather").random() != streams.get("market").random()


def test_sem_ano_nao_ha_data_nem_estacao() -> None:
    assert CAL.date_of(1) is None
    assert CAL.season(5) is None


def test_o_ano_de_28_dias_tem_sete_dias_por_estacao() -> None:
    seasons = [SOL.season(day) for day in range(1, 29)]
    assert seasons == ["primavera"] * 7 + ["verao"] * 7 + ["outono"] * 7 + ["inverno"] * 7
    assert SOL.season(29) == "primavera"  # o ano seguinte


@pytest.mark.parametrize(
    ("day", "when"),
    [
        (1, date(2026, 9, 22)),
        (7, date(2026, 12, 9)),
        (8, date(2026, 12, 22)),
        (15, date(2027, 3, 23)),
        (22, date(2027, 6, 22)),
        (29, date(2027, 9, 22)),
    ],
)
def test_a_data_anda_uns_13_dias_por_dia_simulado(day: int, when: date) -> None:
    assert SOL.date_of(day) == when


def test_janeiro_ainda_e_verao() -> None:
    """Antes do primeiro começo do ano (20/03), vale a estação do fim do ano: o verão."""
    days = [day for day in range(1, 29) if (SOL.date_of(day) or date.min).month == 1]
    assert days
    assert {SOL.season(day) for day in days} == {"verao"}
