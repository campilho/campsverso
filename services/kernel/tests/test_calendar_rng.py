from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from campsverso_cartridge_api import ClockDef
from campsverso_kernel.calendar import Calendar, parse_hhmm
from campsverso_kernel.rng import RngStreams, SplitMix64

BRT = timezone(timedelta(hours=-3))
CLOCK = ClockDef(tick_seconds=60, day_starts_at="06:00", phases=())
CAL = Calendar.create(datetime(2026, 10, 10, 6, 0, tzinfo=BRT), CLOCK)


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


def test_calendario_exige_fuso_e_tick_que_divide_o_minuto() -> None:
    with pytest.raises(ValueError, match="fuso"):
        Calendar.create(datetime(2026, 10, 10, 6, 0), CLOCK)
    with pytest.raises(ValueError, match="minuto"):
        Calendar.create(CAL.start, ClockDef(tick_seconds=90, day_starts_at="06:00", phases=()))


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
