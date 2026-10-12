"""Critério de pronto do M1: 1 dia simulado em teste, pelo serviço e pelo barramento validador."""

import time
from collections import Counter

from campsverso_testkit.hashing import canonical_hash
from campsverso_testkit.service import ServiceFarmer

DAY = 1440


async def _scripted_day(seed: int = 20261010) -> ServiceFarmer:
    """Um dia de fazendeiro: planta e rega nos dois lados, come, compra, vende e dorme na cama."""
    farm = ServiceFarmer(seed)
    await farm.start()
    await farm.run(1)
    await farm.do("move", target={"x": 23, "y": 9})
    for plot in ("plot-e-01", "plot-e-05"):
        await farm.do("plant", target=plot, crop="rabanete")
        await farm.do("water", target=plot)
    await farm.do("move", target={"x": 12, "y": 9})
    for plot in ("plot-w-04", "plot-w-08"):
        await farm.do("plant", target=plot, crop="rabanete")
        await farm.do("water", target=plot)
    await farm.do("move", target={"x": 7, "y": 3})
    await farm.do("withdraw", item="rabanete", qty=3)
    await farm.do("eat", item="rabanete")
    await farm.until("08:00")
    await farm.do("move", target={"x": 17, "y": 15})
    await farm.do("buy", item="semente_rabanete", qty=4)
    await farm.do("move", target={"x": 8, "y": 5})
    await farm.do("sell", item="rabanete", qty=2)
    await farm.until("20:30")
    await farm.do("move", target={"x": 4, "y": 3})
    await farm.do("sleep", target="bed")
    await farm.until("06:00")
    await farm.run(1)
    return farm


async def test_um_dia_sem_controlador_passa_inteiro_pelo_contrato() -> None:
    farm = ServiceFarmer()
    await farm.start()
    await farm.run(DAY)
    kinds = Counter(e["type"].removeprefix("campsverso.") for e in farm.events)
    assert kinds["world.clock.phase_changed.v1"] == 5
    assert kinds["world.weather.changed.v1"] == 2  # dia 1 na abertura e dia 2 às 05:00
    assert kinds["avatar.fainted.v1"] == 1  # ninguém foi dormir: desmaio às 02:00


async def test_um_dia_roteirizado_de_fazendeiro() -> None:
    farm = await _scripted_day()
    assert farm.of_type("action.rejected") == []
    assert len(farm.of_type("action.completed")) == 19
    (paid,) = farm.of_type("farm.buyer.paid")
    assert paid["total"] == 50
    assert farm.of_type("avatar.fainted") == []
    (ended,) = farm.of_type("avatar.sleep.ended.v2")
    assert (ended["cause"], ended["bed_id"]) == ("voluntary", "bed")
    stages = {p: farm.core.world.entity(p).attributes["stage"] for p in ("plot-e-01", "plot-w-04")}
    weather = farm.core.world.weather(1)
    if weather != "rain":  # sem chuva no dia 1, só a rega conta, e a R-001 aparece já no dia 2
        assert stages == {"plot-e-01": "crescendo", "plot-w-04": "broto"}
    hidden = [
        e
        for e in farm.events
        if e["visibility"] == "internal" and e["type"].endswith("effect_applied.v1")
    ]
    assert {e["data"]["entity_id"] for e in hidden} == {"plot-e-01", "plot-e-05"}


async def test_mesma_seed_e_mesmos_comandos_dao_o_mesmo_hash() -> None:
    """Prévia do A4: o hash canônico (ADR-0021) é idêntico em duas execuções."""
    first, second = await _scripted_day(), await _scripted_day()
    assert canonical_hash(first.events) == canonical_hash(second.events)
    other = await _scripted_day(seed=7)
    assert len(other.events) > 0


def test_desempenho_de_um_dia_em_modo_maximo() -> None:
    """Números para o diário: tempo real de 1 dia tick a tick e com salto de tempo."""
    from campsverso_testkit.farm import make_core

    timings: dict[str, float] = {}
    for jump in (False, True):
        core = make_core()
        core.start()
        start = time.perf_counter()
        core.advance(DAY, jump=jump)
        timings["salto" if jump else "tick a tick"] = time.perf_counter() - start
        core.drain()
    print(f"\n1 dia simulado: {timings}")
    assert timings["tick a tick"] < 2.0
