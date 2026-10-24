"""O processamento da Morada do Sol (ADR-0069), no mundo real: o tacho comprado e fincado, que faz
geleia, molho e farinha sozinho, e a composteira ao lado da casa, que faz adubo do que ia se
perder. O produto espera na máquina, sai pelo `withdraw` e vende na caixa."""

from campsverso_cartridge_api import Position, SpawnDef
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


def test_o_tacho_trabalha_sozinho_e_o_produto_espera_nele() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "tacho", 1)
    _give(farmer, "morango", 4)
    farmer.walk(10, 23)
    assert of_type(farmer.do("place", item="tacho", target={"x": 11, "y": 23}), "action.completed")
    (tacho,) = world.entities("tacho")
    assert tacho.entity_id == "tacho-01"
    facts = farmer.do("process", target="tacho-01", recipe="geleia")
    assert of_type(facts, "action.completed")
    tacho = world.entity("tacho-01")
    assert tacho.attributes["fazendo"] == "geleia"
    assert tacho.attributes["faltam_horas"] == 12
    assert dict(world.items("camps")).get("morango") == 1
    (busy,) = of_type(farmer.do("process", target="tacho-01", recipe="geleia"), "action.rejected")
    assert busy["reason"] == "machine_busy"
    farmer.advance(6 * 60)
    assert world.entity("tacho-01").attributes["faltam_horas"] in (6, 7)
    farmer.advance(7 * 60)  # o avatar fez outra coisa; o tacho terminou sozinho
    tacho = world.entity("tacho-01")
    assert tacho.attributes["fazendo"] is None
    assert dict(world.items("tacho-01")) == {"geleia": 1}
    assert of_type(
        farmer.do("withdraw", target="tacho-01", item="geleia", qty=1), "action.completed"
    )
    assert dict(world.items("camps"))["geleia"] == 1


def test_faltando_ingrediente_ou_receita_de_outra_maquina() -> None:
    farmer = _farmer()
    world = farmer.core.world
    world.spawn(SpawnDef("tacho-09", "tacho", position=Position(11, 23)))
    farmer.core.drain()
    farmer.walk(10, 23)
    (short,) = of_type(farmer.do("process", target="tacho-09", recipe="farinha"), "action.rejected")
    assert short["reason"] == "missing_ingredients"
    (other,) = of_type(farmer.do("process", target="tacho-09", recipe="adubo"), "action.rejected")
    assert other["reason"] == "invalid_params"


def test_a_composteira_faz_adubo_do_que_ia_se_perder() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "rabanete", 3)
    farmer.walk(3, 18)  # ao lado da composteira (2, 17)
    (wrong,) = of_type(
        farmer.do("process", target="composteira", recipe="adubo", item="semente_rabanete"),
        "action.rejected",
    )
    assert wrong["reason"] == "invalid_params"
    facts = farmer.do("process", target="composteira", recipe="adubo", item="rabanete")
    assert of_type(facts, "action.completed")
    farmer.advance(3 * DAY + 60)
    assert dict(world.items("composteira")) == {"adubo": 1}


def test_limpar_a_planta_murcha_deixa_os_restos_e_a_caixa_compra_o_produto() -> None:
    farmer = _farmer()
    world = farmer.core.world
    world.spawn(SpawnDef("plot-901", "plot", position=Position(10, 21)))
    world.set_attributes("plot-901", visible={"crop": "milho", "stage": "murcha"})
    farmer.core.drain()
    farmer.walk(9, 21)
    assert of_type(farmer.do("clear", target="plot-901"), "action.completed")
    assert dict(world.items("camps"))["resto"] == 1
    _give(farmer, "farinha", 1)
    price = world.entity("sell-box").attributes["preco_farinha"]
    assert isinstance(price, int)
    assert price > 400
    assert of_type(farmer.do("sell", target="sell-box", item="farinha", qty=1), "action.completed")
