"""A feira da Morada do Sol (ADR-0069), no mundo real: a barraca na entrada da fazenda abre a cada 7
dias, das 06:00 às 14:00, compra acima da referência com pressão própria e paga na hora."""

from campsverso_cartridge_api import Scalar
from campsverso_testkit.farm import Farmer, make_core, of_type

DAY = 1440
STALL = "feira"


def _farmer() -> Farmer:
    core = make_core(cartridge="farm_morada_do_sol")
    core.start()
    farmer = Farmer(core)
    farmer.run(1)
    return farmer


def _to_day(farmer: Farmer, day: int) -> None:
    while farmer.core.world.day < day:
        farmer.advance(DAY - farmer.core.tick % DAY + 1)


def _give(farmer: Farmer, item: str, qty: int) -> None:
    farmer.core.world.create_item(item, qty, "camps", "test")
    farmer.core.drain()


def _int(value: Scalar) -> int:
    assert isinstance(value, int)
    return value


def test_a_barraca_abre_a_cada_sete_dias_das_seis_as_duas() -> None:
    farmer = _farmer()
    stall = farmer.core.world.entity(STALL)
    assert stall.attributes["open"] is False
    assert stall.attributes["proxima_feira"] == 7
    _give(farmer, "milho", 2)
    farmer.walk(32, 37)  # ao lado da barraca (31, 37)
    (closed,) = of_type(farmer.do("sell", target=STALL, item="milho", qty=1), "action.rejected")
    assert closed["reason"] == "closed"
    _to_day(farmer, 7)
    assert farmer.core.world.entity(STALL).attributes["open"] is True
    farmer.until("14:00")
    farmer.run(1)
    stall = farmer.core.world.entity(STALL)
    assert stall.attributes["open"] is False
    assert stall.attributes["proxima_feira"] == 14


def test_a_feira_paga_mais_e_na_hora_e_cada_unidade_baixa_o_preco() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _to_day(farmer, 7)
    box_price = _int(world.entity("sell-box").attributes["preco_milho"])
    fair_price = _int(world.entity(STALL).attributes["preco_milho"])
    assert fair_price > box_price  # 30% acima da referência do mercado
    _give(farmer, "milho", 10)
    farmer.walk(32, 37)
    coins = dict(world.items("camps"))["moeda"]
    facts = farmer.do("sell", target=STALL, item="milho", qty=10)
    assert of_type(facts, "action.completed")
    paid = dict(world.items("camps"))["moeda"] - coins
    assert paid > 9 * box_price  # pago na hora, acima do que a caixa daria
    assert _int(world.entity(STALL).attributes["preco_milho"]) < fair_price
    assert dict(world.items("camps")).get("milho", 0) == 0
    (wrong,) = of_type(
        farmer.do("sell", target=STALL, item="semente_rabanete", qty=1), "action.rejected"
    )
    assert wrong["reason"] == "invalid_params"
    _to_day(farmer, 14)
    assert _int(world.entity(STALL).attributes["preco_milho"]) >= fair_price * 0.8  # zerou
