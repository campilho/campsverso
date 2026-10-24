"""O clima da Morada do Sol (ADR-0069), no mundo real: o tempo de amanhã sorteado na véspera pela
libs/climate, a tempestade que rega e derruba plantas maduras, a seca que pede rega até o meio-dia
e gasta mais o regador, e o mercado que sobe depois de uma delas."""

import pytest

from campsverso_cartridge_api import Position, SpawnDef
from campsverso_testkit.farm import Farmer, make_core, of_type

DAY = 1440


def _farmer() -> Farmer:
    core = make_core(cartridge="farm_morada_do_sol")
    core.start()
    farmer = Farmer(core)
    farmer.run(1)
    return farmer


def _morning(farmer: Farmer) -> None:
    farmer.advance(DAY - farmer.core.tick % DAY + 1)


def _plot(farmer: Farmer, plot_id: str, x: int, y: int, stage: str, crop: str = "milho") -> None:
    world = farmer.core.world
    world.spawn(SpawnDef(plot_id, "plot", position=Position(x, y)))
    world.set_attributes(plot_id, visible={"crop": crop, "stage": stage})
    farmer.core.drain()


def _tomorrow(farmer: Farmer, condition: str) -> None:
    """Troca o tempo de amanhã, como se a previsão das 18:00 tivesse saído assim."""
    farmer.until("18:00")
    farmer.run(1)
    farmer.core.world.set_weather(condition, farmer.core.world.day + 1)
    farmer.core.drain()


def test_o_tempo_de_amanha_sai_as_seis_da_tarde() -> None:
    farmer = _farmer()
    world = farmer.core.world
    assert world.weather(1) is not None  # o dia 1, sorteado no começo
    assert world.weather(2) is None
    farmer.until("18:00")
    farmer.run(1)
    (forecast,) = [
        e for e in of_type(farmer.facts, "world.weather.changed") if e.get("forecast") is True
    ]
    assert forecast["day"] == 2
    assert world.weather(2) == forecast["condition"]


def test_a_tempestade_rega_e_derruba_parte_das_maduras() -> None:
    farmer = _farmer()
    for n in range(20):
        _plot(farmer, f"plot-9{n:02d}", 10 + n, 23, "madura")
    _plot(farmer, "plot-990", 10, 24, "crescendo")
    _tomorrow(farmer, "storm")
    _morning(farmer)
    world = farmer.core.world
    fallen = of_type(farmer.facts, "farm.crop.knocked_down")
    assert 1 <= len(fallen) <= 14  # 30% de 20, pelo RNG da tempestade
    assert {f["plot_id"] for f in fallen} <= {f"plot-9{n:02d}" for n in range(20)}
    for f in fallen:
        assert world.entity(str(f["plot_id"])).attributes["crop"] is None
    assert world.entity("plot-990").attributes["watered_today"] is True  # a tempestade regou


def test_na_seca_quem_nao_regou_ate_o_meio_dia_nao_cresce_e_o_regador_gasta_dois() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _plot(farmer, "plot-901", 10, 23, "semente")
    _plot(farmer, "plot-902", 11, 23, "semente")
    _tomorrow(farmer, "drought")
    _morning(farmer)
    farmer.walk(10, 24)
    charges = world.entity("watering-can").attributes["charges"]
    assert of_type(farmer.do("water", target="plot-901"), "action.completed")
    assert world.entity("watering-can").attributes["charges"] == int(str(charges)) - 2
    farmer.until("12:00")
    farmer.run(1)
    assert of_type(farmer.do("water", target="plot-902"), "action.completed")  # tarde demais
    _morning(farmer)
    assert float(str(world.entity("plot-901").hidden["growth_points"])) > 0
    assert float(str(world.entity("plot-902").hidden.get("growth_points") or 0)) == 0


def test_depois_da_tempestade_o_mercado_sobe_por_tres_dias() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _tomorrow(farmer, "storm")
    _morning(farmer)
    box = world.entity("sell-box")
    assert box.hidden["shock"] == pytest.approx(0.15)
    assert box.hidden["shock_until"] == world.day + 2
    drift = float(str(box.hidden["drift_milho"]))
    assert box.attributes["preco_milho"] == int(45 * (1 + drift) * 1.15 + 0.5)
