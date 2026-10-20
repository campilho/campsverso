"""A Fazenda Boa Vista (bíblia 2; ADR-0062): as mecânicas novas do gênero farm ligadas pelo
cenário, exercitadas no mundo real. A fazenda 1 continua coberta pelos testes de farm_camps."""

import pytest

from campsverso_cartridge_api import Position
from campsverso_testkit.farm import Farmer, make_core, of_type

DAY = 1440


def _farmer(*, river_bonus: bool = True) -> Farmer:
    core = make_core(cartridge="farm_boavista", river_bonus=river_bonus)
    core.start()
    farmer = Farmer(core)
    farmer.run(1)
    return farmer


def _give(farmer: Farmer, item: str, qty: int) -> None:
    """Põe itens no inventário por fora das ações, e recolhe os fatos para não confundir."""
    farmer.core.world.create_item(item, qty, "camps", "test")
    farmer.core.drain()


def _morning(farmer: Farmer, days: int = 1) -> None:
    """Passa por `days` viradas das 06:00."""
    for _ in range(days):
        farmer.advance(DAY - farmer.core.tick % DAY + 1)


def test_estado_inicial_da_boa_vista() -> None:
    world = _farmer().core.world
    assert dict(world.items("camps")) == {"moeda": 100, "semente_rabanete": 10}
    assert dict(world.items("chest")) == {"rabanete": 5}
    assert list(world.entities("plot")) == []
    assert world.entity("spade").container_id == "camps"
    assert world.entity("watering-can").attributes["charges"] == 10
    camps = world.entity("camps").attributes
    assert (camps["capacity"], camps["weight"]) == (20, 8.0)  # pá 3, regador 4, 10 sementes 1
    assert world.entity("chest").attributes["capacity"] == 100
    assert world.entity("stove").position == Position(3, 4)
    kiosk = world.entity("kiosk").attributes
    assert (
        kiosk["estoque_hoje"]
        == "semente_abobora, semente_batata, semente_cenoura, semente_rabanete, adubo"
    )
    assert world.entity("sell-box").attributes["preco_rabanete"] == 25


def test_cavar_so_na_grama_com_a_pa_e_so_ate_o_teto() -> None:
    farmer = _farmer()
    farmer.walk(4, 8)  # o caminho
    (rejected,) = of_type(farmer.do("dig"), "action.rejected")
    assert rejected["reason"] == "not_grass"
    farmer.walk(5, 8)
    facts = farmer.do("dig")
    (spawned,) = of_type(facts, "world.entity.spawned")
    assert (spawned["entity_id"], spawned["kind"], spawned["position"]) == (
        "plot-01",
        "plot",
        {"x": 5, "y": 8},
    )
    assert spawned["attributes"] == {
        "crop": None,
        "stage": None,
        "watered_today": False,
        "group": "oeste",
    }
    (rejected,) = of_type(farmer.do("dig"), "action.rejected")
    assert rejected["reason"] == "occupied"
    farmer.walk(20, 9)
    (spawned,) = of_type(farmer.do("dig"), "world.entity.spawned")
    assert (spawned["entity_id"], spawned["attributes"]["group"]) == ("plot-02", "leste")
    world = farmer.core.world
    assert [e.entity_id for e in world.entities("plot")] == ["plot-01", "plot-02"]
    # Sem a pá, não se cava.
    world.move_entity("spade", "chest")
    farmer.walk(21, 9)
    (rejected,) = of_type(farmer.do("dig"), "action.rejected")
    assert rejected["reason"] == "missing_item"


def test_adubo_vale_para_o_proximo_plantio() -> None:
    farmer = _farmer()
    _give(farmer, "adubo", 1)
    farmer.walk(5, 8)
    farmer.do("dig")
    facts = farmer.do("fertilize", target="plot-01")
    assert of_type(facts, "action.completed")
    world = farmer.core.world
    assert world.entity("plot-01").attributes["adubado"] is True
    (rejected,) = of_type(farmer.do("fertilize", target="plot-01"), "action.rejected")
    assert rejected["reason"] == "already_fertilized"
    farmer.do("plant", target="plot-01", crop="rabanete")
    assert world.entity("plot-01").attributes["adubado"] is False
    farmer.do("water", target="plot-01")
    _morning(farmer)
    assert world.entity("plot-01").hidden["growth_points"] == pytest.approx(1.5)  # 1 + 0,5
    farmer.do("water", target="plot-01")
    _morning(farmer)
    assert world.entity("plot-01").hidden["growth_points"] == pytest.approx(3.0)
    assert world.entity("plot-01").attributes["stage"] == "madura"


def test_o_alho_cresce_sem_rega_e_o_tomate_murcha_com_um_dia_seco() -> None:
    farmer = _farmer()
    _give(farmer, "semente_alho", 1)
    _give(farmer, "semente_tomate", 1)
    farmer.walk(5, 8)
    farmer.do("dig")
    farmer.do("plant", target="plot-01", crop="alho")
    farmer.walk(6, 8)
    farmer.do("dig")
    farmer.do("plant", target="plot-02", crop="tomate")
    _morning(farmer)
    world = farmer.core.world
    assert world.entity("plot-01").hidden["growth_points"] == pytest.approx(1.0)  # sem rega
    assert world.entity("plot-02").attributes["stage"] == "murcha"  # um dia seco bastou
    assert "needs_water" not in world.entity("plot-01").attributes  # nada disso é visível


def test_a_madura_murcha_depois_de_tres_dias_sem_colher() -> None:
    farmer = _farmer()
    farmer.walk(5, 8)
    farmer.do("dig")
    farmer.do("plant", target="plot-01", crop="rabanete")
    world = farmer.core.world
    for _ in range(3):
        farmer.do("water", target="plot-01")
        _morning(farmer)
    assert world.entity("plot-01").attributes["stage"] == "madura"
    _morning(farmer, 2)
    assert world.entity("plot-01").attributes["stage"] == "madura"
    _morning(farmer)
    assert world.entity("plot-01").attributes["stage"] == "murcha"


def test_a_colheita_tem_validade() -> None:
    farmer = _farmer()
    farmer.walk(5, 8)
    farmer.do("dig")
    farmer.do("plant", target="plot-01", crop="rabanete")
    for _ in range(3):
        farmer.do("water", target="plot-01")
        _morning(farmer)
    facts = farmer.do("harvest", target="plot-01")
    (created,) = of_type(facts, "world.item.created")
    assert (created["item"], created["expires_day"]) == ("rabanete", farmer.core.world.day + 4)


def test_ferramentas_pesam_se_excluem_e_vao_para_o_bau() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "moeda", 400)
    farmer.walk(16, 14)  # ao lado do quiosque (16,15)
    farmer.until("08:00")
    facts = farmer.do("buy", item="plow", qty=1)
    (spawned,) = of_type(facts, "world.entity.spawned")
    assert (spawned["entity_id"], spawned["container_id"]) == ("plow-1", "camps")
    assert world.weight("camps") == 20.0  # pá 3, regador 4, sementes 1, arado 12: no limite
    (rejected,) = of_type(farmer.do("buy", item="watering_can_large", qty=1), "action.rejected")
    assert rejected["reason"] == "too_heavy"
    farmer.walk(7, 5)  # ao lado do baú (7,4)
    facts = farmer.do("deposit", target="chest", item="plow-1")
    (stored,) = of_type(facts, "world.entity.stored")
    assert (stored["from_container"], stored["to_container"]) == ("camps", "chest")
    assert world.weight("camps") == 8.0
    farmer.walk(16, 14)
    facts = farmer.do("buy", item="watering_can_large", qty=1)
    assert of_type(facts, "world.entity.spawned")[0]["entity_id"] == "watering-can-large-1"
    assert world.entity("watering-can-large-1").attributes["charges"] == 25
    assert world.weight("camps") == 17.0
    assert dict(world.items("camps"))["moeda"] == 500 - 300 - 150
    # Arado e regador grande não cabem juntos (21 > 20): para pegar um, guarda-se o outro.
    farmer.walk(7, 5)
    (rejected,) = of_type(farmer.do("withdraw", target="chest", item="plow-1"), "action.rejected")
    assert rejected["reason"] == "too_heavy"
    farmer.do("deposit", target="chest", item="watering-can-large-1")
    assert of_type(farmer.do("withdraw", target="chest", item="plow-1"), "world.entity.stored")
    assert world.weight("camps") == 20.0
    assert world.entity("watering-can-large-1").container_id == "chest"


def test_o_arado_acelera_plantar_e_cavar() -> None:
    farmer = _farmer()
    world = farmer.core.world
    world.spawn(
        __import__("campsverso_cartridge_api").SpawnDef("plow-1", "plow", container_id="camps")
    )
    farmer.walk(5, 8)
    facts = farmer.do("dig")
    (accepted,) = of_type(facts, "action.accepted")
    assert accepted["duration_ticks"] == 5
    facts = farmer.do("plant", target="plot-01", crop="rabanete")
    (accepted,) = of_type(facts, "action.accepted")
    assert accepted["duration_ticks"] == 1


def test_o_mercado_satura_e_o_comprador_paga_o_valor_do_dia() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "rabanete", 12)
    farmer.walk(8, 7)  # ao lado da caixa (8,6)
    farmer.do("sell", target="sell-box", item="rabanete", qty=6)
    box = world.entity("sell-box")
    assert box.attributes["preco_rabanete"] == 23  # a sexta unidade já saiu a 23; a sétima também
    assert box.hidden["sold_rabanete"] == 6
    assert box.hidden["value_rabanete"] == pytest.approx(5 * 25 + 23)
    coins = dict(world.items("camps"))["moeda"]
    farmer.until("22:00")
    farmer.run(1)
    box = world.entity("sell-box")  # a visão é uma foto: pegar de novo
    assert box.hidden["due_rabanete"] == pytest.approx(148.0)
    _morning(farmer)
    assert dict(world.items("camps"))["moeda"] == coins + 148
    assert world.entity("sell-box").attributes["preco_rabanete"] == 25  # o dia novo zera


def test_o_quiosque_tem_estoque_por_dia() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "moeda", 100)
    farmer.walk(16, 14)
    farmer.until("08:00")
    (rejected,) = of_type(farmer.do("buy", item="semente_alho", qty=1), "action.rejected")
    assert rejected["reason"] == "out_of_stock"
    assert of_type(farmer.do("buy", item="semente_batata", qty=1), "action.completed")
    assert of_type(farmer.do("buy", item="adubo", qty=2), "action.completed")
    _morning(farmer)
    assert "semente_alho" in str(world.entity("kiosk").attributes["estoque_hoje"])
    assert "semente_batata" not in str(world.entity("kiosk").attributes["estoque_hoje"])


def test_cozinhar_e_o_ensopado_segura_a_fome() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "batata", 3)
    _give(farmer, "cenoura", 1)
    _give(farmer, "alho", 1)
    facts = farmer.do("cook", target="stove", recipe="sopa_de_batata")  # o Camps nasce ao lado
    (created,) = of_type(facts, "world.item.created")
    assert (created["item"], created["expires_day"]) == ("sopa_de_batata", world.day + 2)
    assert dict(world.items("camps"))["batata"] == 1
    (rejected,) = of_type(
        farmer.do("cook", target="stove", recipe="sopa_de_batata"), "action.rejected"
    )
    assert rejected["reason"] == "missing_ingredients"
    farmer.do("cook", target="stove", recipe="ensopado")
    full_rate = world.rate("camps", "fome")
    hunger = world.need("camps", "fome")
    farmer.do("eat", item="ensopado")
    assert world.need("camps", "fome") == pytest.approx(max(0.0, hunger - 110), abs=0.6)
    assert world.rate("camps", "fome") == full_rate / 2
    assert isinstance(world.entity("camps").attributes["satisfeito_ate"], str)


def test_andar_gasta_energia() -> None:
    farmer = _farmer()
    world = farmer.core.world
    before, start = world.need("camps", "energia"), farmer.core.tick
    farmer.walk(4, 14)  # pela porta e pelo caminho: 10 tiles
    awake = (farmer.core.tick - start) / 60  # 1 por hora acordado (ADR-0056)
    assert world.need("camps", "energia") == pytest.approx(before - 10 * 0.05 - awake, abs=0.001)
