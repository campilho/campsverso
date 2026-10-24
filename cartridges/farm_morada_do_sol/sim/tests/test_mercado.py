"""O mercado da Morada do Sol (ADR-0069), no mundo real: a caixa que lembra o que se vendeu, o
quiosque cuja semente sobe com a compra, e a referência pela estação. A Boa Vista continua com o
mercado do dia (test_boavista.py)."""

import pytest

from campsverso_cartridge_api import Scalar
from campsverso_testkit.farm import Farmer, make_core, of_type

DAY = 1440


def _farmer() -> Farmer:
    core = make_core(cartridge="farm_morada_do_sol")
    core.start()
    farmer = Farmer(core)
    farmer.run(1)
    return farmer


def _give(farmer: Farmer, item: str, qty: int) -> None:
    farmer.core.world.create_item(item, qty, "camps", "test")
    farmer.core.drain()


def _morning(farmer: Farmer) -> None:
    farmer.advance(DAY - farmer.core.tick % DAY + 1)


def _num(value: Scalar) -> float:
    assert isinstance(value, int | float)
    return float(value)


def _reference(farmer: Farmer, item: str, base: float, season: float = 1.0) -> float:
    drift = _num(farmer.core.world.entity("sell-box").hidden[f"drift_{item}"])
    return base * season * (1 + drift)


def test_vender_muito_derruba_o_preco_que_so_recupera_aos_poucos() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "rabanete", 20)
    farmer.walk(9, 21)  # ao lado da caixa (9, 20)
    reference = _reference(farmer, "rabanete", 25)
    assert world.entity("sell-box").attributes["preco_rabanete"] == int(reference + 0.5)
    farmer.do("sell", target="sell-box", item="rabanete", qty=20)
    box = world.entity("sell-box")
    assert box.hidden["factor_rabanete"] == pytest.approx(0.6)
    assert box.attributes["preco_rabanete"] == int(reference * 0.6 + 0.5)
    expected = sum(int(reference * (1 - 0.02 * n) + 0.5) for n in range(20))
    assert box.hidden["value_rabanete"] == pytest.approx(expected)
    _morning(farmer)
    box = world.entity("sell-box")
    assert box.hidden["factor_rabanete"] == pytest.approx(0.6 + 0.4 * 0.3333, abs=1e-4)
    reference = _reference(farmer, "rabanete", 25)
    assert _num(box.attributes["preco_rabanete"]) < reference  # um dia depois, ainda abaixo
    _morning(farmer)
    _morning(farmer)
    assert _num(world.entity("sell-box").hidden["factor_rabanete"]) < 0.95  # três dias depois


def test_despejar_para_no_piso() -> None:
    farmer = _farmer()
    _give(farmer, "milho", 24)
    farmer.walk(9, 21)
    farmer.do("sell", target="sell-box", item="milho", qty=24)
    assert farmer.core.world.entity("sell-box").hidden["factor_milho"] == pytest.approx(0.52)
    _give(farmer, "milho", 10)
    farmer.do("sell", target="sell-box", item="milho", qty=10)
    assert farmer.core.world.entity("sell-box").hidden["factor_milho"] == pytest.approx(0.4)


def test_comprar_muita_semente_sobe_o_preco_no_dia_e_ele_volta_de_manha() -> None:
    farmer = _farmer()
    world = farmer.core.world
    farmer.walk(34, 35)  # ao lado do quiosque (34, 36)
    farmer.until("08:00")
    assert world.entity("kiosk").attributes["preco_semente_rabanete"] == 10
    assert of_type(farmer.do("buy", item="semente_rabanete", qty=5), "action.completed")
    assert dict(world.items("camps"))["moeda"] == 100 - (10 + 10 + 11 + 11 + 11)
    assert world.entity("kiosk").attributes["preco_semente_rabanete"] == 12
    (rejected,) = of_type(farmer.do("buy", item="semente_rabanete", qty=10), "action.rejected")
    assert rejected["reason"] == "insufficient_funds"  # dez a 10 cabiam; a 12 subindo, não
    _morning(farmer)
    assert world.entity("kiosk").attributes["preco_semente_rabanete"] == 10


def test_fora_da_estacao_a_colheita_vale_mais() -> None:
    farmer = _farmer()
    box = farmer.core.world.entity("sell-box")
    # Na primavera: o alho está parado (1,6), a batata fraca (1,25), o milho bom (1,0).
    assert box.attributes["preco_alho"] == int(_reference(farmer, "alho", 40, 1.6) + 0.5)
    assert box.attributes["preco_batata"] == int(_reference(farmer, "batata", 50, 1.25) + 0.5)
    assert box.attributes["preco_milho"] == int(_reference(farmer, "milho", 45) + 0.5)
    drift = {k: v for k, v in box.hidden.items() if str(k).startswith("drift_")}
    assert all(abs(_num(v)) <= 0.04 for v in drift.values())  # um dia de oscilação
