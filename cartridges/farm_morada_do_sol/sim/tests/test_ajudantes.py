"""Os ajudantes da Morada do Sol (ADR-0072), no mundo real: o quadro, o contrato pago adiantado, a
chegada na manhã seguinte, a ordem dada ao lado, a saída no fim do turno com o que carrega indo
para o baú, o fim do contrato, a dispensa, a venda que paga ao patrão e a semente do Tião."""

from campsverso_farm_sim import helpers
from campsverso_testkit.farm import Farmer, make_core, of_type

DAY = 1440
BOARD = "helper-board"
CREW = ("dita", "nina", "seu-bento", "tiao", "ze-graudo")


def _farmer() -> Farmer:
    core = make_core(cartridge="farm_morada_do_sol")
    core.start()
    farmer = Farmer(core)
    farmer.run(1)
    return farmer


def _give(farmer: Farmer, item: str, qty: int, to: str = "camps") -> None:
    farmer.core.world.create_item(item, qty, to, "test")
    farmer.core.drain()


def _at_board(farmer: Farmer) -> None:
    farmer.walk(35, 38)


def _until_day(farmer: Farmer, day: int, hhmm: str) -> None:
    """Até a hora pedida do dia pedido (o dia vira às 06:00)."""
    while farmer.core.world.day < day:
        farmer.advance(DAY - farmer.core.tick % DAY + 1)
    if farmer.core.world.minute_of_day < int(hhmm[:2]) * 60 + int(hhmm[3:]):
        farmer.until(hhmm)


def test_os_ajudantes_comecam_fora_com_as_ferramentas_e_o_quadro_os_mostra() -> None:
    farmer = _farmer()
    world = farmer.core.world
    assert world.avatars() == ["camps"]
    assert sorted(a for a in world.avatar_map if a != "camps") == sorted(CREW)
    assert world.entity(BOARD).attributes["dita"] == "livre"
    dita = world.entity("dita")
    assert (dita.attributes["nome"], dita.attributes["diaria"], dita.position) == ("Dita", 40, None)
    assert {e.entity_id for e in world.entities() if e.container_id == "dita"} == {
        "dita-regador",
        "dita-pa",
    }
    assert world.capacity("ze-graudo") == 40
    assert world.entity("nina").attributes["night_vision"] is True
    assert world.entity("seu-bento").attributes["horario"] == "08:00-16:00"


def test_contratar_paga_adiantado_e_o_ajudante_chega_na_manha_seguinte() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _at_board(farmer)
    (refused,) = of_type(
        farmer.do("hire_helper", target=BOARD, helper="dita", days=3), "action.rejected"
    )
    assert refused["reason"] == "insufficient_funds"  # 120 contra as 100 do começo
    (wrong,) = of_type(
        farmer.do("hire_helper", target=BOARD, helper="dita", days=2), "action.rejected"
    )
    assert wrong["reason"] == "invalid_params"
    _give(farmer, "moeda", 100)
    before = world.items("camps")["moeda"]
    facts = farmer.do("hire_helper", target=BOARD, helper="dita", days=3)
    (hired,) = of_type(facts, "economy.labor.hired")
    day = world.day
    assert hired == {
        "helper": "dita",
        "employer": "camps",
        "days": 3,
        "wage": 40,
        "total": 120,
        "first_day": day + 1,
        "day": day,
    }
    assert world.items("camps")["moeda"] == before - 120
    assert world.entity(BOARD).attributes["dita"] == f"com camps até o dia {day + 3}"
    assert (world.entity("dita").attributes["ordem"], helpers.payee(world, "dita")) == (
        "cuidar",
        "camps",
    )
    (busy,) = of_type(
        farmer.do("hire_helper", target=BOARD, helper="dita", days=1), "action.rejected"
    )
    assert busy["reason"] == "helper_busy"
    _until_day(farmer, day + 1, "06:01")
    (entered,) = of_type(farmer.facts, "avatar.entered")
    assert entered == {"avatar_id": "dita", "position": {"x": 33, "y": 38}, "reason": "work_day"}
    assert world.need("dita", "fome") < 1


def test_a_ordem_e_dada_ao_lado_e_o_dia_termina_com_o_baú_e_o_contrato() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "moeda", 100)
    _at_board(farmer)
    farmer.do("hire_helper", target=BOARD, helper="dita", days=1)
    first = world.day + 1
    _until_day(farmer, first, "06:30")
    (far,) = of_type(farmer.do("order_helper", target="dita", task="regar"), "action.rejected")
    assert far["reason"] == "not_adjacent"
    farmer.walk(33, 37)
    farmer.do("order_helper", target="dita", task="plantar", crop="rabanete")
    assert world.entity("dita").attributes["ordem"] == "plantar"
    assert world.entity("dita").attributes["ordem_cultura"] == "rabanete"
    (other,) = of_type(
        farmer.do("order_helper", target="dita", task="regar", avatar="dita"), "action.rejected"
    )
    assert other["reason"] == "not_employer"
    _give(farmer, "rabanete", 2, to="dita")
    chest = world.items("chest").get("rabanete", 0)
    farmer.until("18:01")
    (left,) = of_type(farmer.facts, "avatar.left")
    assert (left["avatar_id"], left["reason"]) == ("dita", "end_of_day")
    assert world.items("chest").get("rabanete", 0) == chest + 2  # o que carregava ficou no baú
    (ended,) = of_type(farmer.facts, "economy.labor.ended")
    assert ended == {"helper": "dita", "employer": "camps", "day": first}
    assert world.entity("dita").attributes["patrao"] is None
    assert world.entity(BOARD).attributes["dita"] == "livre"


def test_dispensar_no_quadro_e_os_dias_pagos_nao_voltam() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "moeda", 200)
    _at_board(farmer)
    farmer.do("hire_helper", target=BOARD, helper="tiao", days=7)
    coins = world.items("camps")["moeda"]
    facts = farmer.do("dismiss_helper", target=BOARD, helper="tiao")
    (dismissed,) = of_type(facts, "economy.labor.dismissed")
    assert (dismissed["days_left"], world.items("camps")["moeda"]) == (7, coins)
    assert world.entity(BOARD).attributes["tiao"] == "livre"


def test_o_tiao_perde_semente_e_a_nina_nao_pega_ferramenta_pesada() -> None:
    farmer = _farmer()
    world = farmer.core.world
    _give(farmer, "moeda", 100)
    _at_board(farmer)
    farmer.do("hire_helper", target=BOARD, helper="tiao", days=1)
    _until_day(farmer, world.day + 1, "06:01")
    world.set_attributes("tiao", hidden={"perde_semente": 1.0})  # a chance toda, para o teste
    _give(farmer, "semente_rabanete", 3, to="tiao")
    farmer.do("dig", target={"x": 34, "y": 38}, avatar="tiao")
    plot = max(e.entity_id for e in world.entities("plot"))
    facts = farmer.do("plant", target=plot, crop="rabanete", avatar="tiao")
    reasons = [c["reason"] for c in of_type(facts, "world.item.consumed")]
    assert reasons == ["plant", "seed_lost"]
    assert world.items("tiao").get("semente_rabanete", 0) == 1
    nina = world.entity("nina")
    assert nina.hidden["peso_max_ferramenta"] == 4.0
