"""As encomendas da Morada do Sol (ADR-0069), no mundo real: o quadro ao lado do quiosque, os
pedidos que aparecem de manhã, aceitar, entregar e receber na hora, as recusas, o prazo que vence
e a reputação de quem aceita (R-004, oculta)."""

import pytest

from campsverso_cartridge_api import EntityView, Scalar
from campsverso_testkit.farm import Farmer, make_core, of_type

DAY = 1440
BOARD = "order-board"


def _farmer() -> Farmer:
    core = make_core(cartridge="farm_morada_do_sol")
    core.start()
    farmer = Farmer(core)
    farmer.run(1)
    return farmer


def _morning(farmer: Farmer) -> None:
    farmer.advance(DAY - farmer.core.tick % DAY + 1)


def _orders(farmer: Farmer) -> list[EntityView]:
    found = [e for e in farmer.core.world.entities("order") if e.container_id == BOARD]
    return sorted(found, key=lambda e: e.entity_id)


def _int(value: Scalar) -> int:
    assert isinstance(value, int)
    return value


def _give(farmer: Farmer, item: str, qty: int) -> None:
    farmer.core.world.create_item(item, qty, "camps", "test")
    farmer.core.drain()


def _reputation(farmer: Farmer) -> Scalar:
    return farmer.core.world.entity(BOARD).hidden.get("reputation_camps")


def test_os_pedidos_aparecem_no_quadro_de_manha() -> None:
    farmer = _farmer()
    orders = _orders(farmer)
    assert orders  # a seed do mundo já traz um pedido no dia 1
    first = orders[0]
    attributes = first.attributes
    assert set(attributes) >= {"cliente", "item", "quantidade", "pagamento", "prazo", "aceita_por"}
    assert attributes["aceita_por"] is None
    assert 3 <= _int(attributes["prazo"]) - 1 <= 7
    assert first.display_name is not None
    assert "até o dia" in first.display_name
    board = farmer.core.world.entity(BOARD)
    assert board.attributes.get("capacity") == 100
    for _ in range(4):
        _morning(farmer)
    assert len(_orders(farmer)) <= 4  # o quadro não passa de quatro


def test_aceitar_entregar_e_receber_na_hora() -> None:
    farmer = _farmer()
    world = farmer.core.world
    order = _orders(farmer)[0]
    item, qty = str(order.attributes["item"]), _int(order.attributes["quantidade"])
    reward = _int(order.attributes["pagamento"])
    farmer.walk(35, 35)  # ao lado do quadro (36, 36) e do quiosque (34, 36)
    (missing,) = of_type(
        farmer.do("deliver_order", target=BOARD, order=order.entity_id), "action.rejected"
    )
    assert missing["reason"] == "not_your_order"  # entregar exige ter aceitado
    facts = farmer.do("accept_order", target=BOARD, order=order.entity_id)
    (accepted,) = of_type(facts, "economy.order.accepted")
    assert accepted == {"order_id": order.entity_id, "taker": "camps", "day": 1}
    assert world.entity(order.entity_id).attributes["aceita_por"] == "camps"
    (short,) = of_type(
        farmer.do("deliver_order", target=BOARD, order=order.entity_id), "action.rejected"
    )
    assert short["reason"] == "missing_item"
    _give(farmer, item, qty)
    coins = dict(world.items("camps"))["moeda"]
    facts = farmer.do("deliver_order", target=BOARD, order=order.entity_id)
    (delivered,) = of_type(facts, "economy.order.delivered")
    assert delivered["reward"] == reward
    assert dict(world.items("camps"))["moeda"] == coins + reward  # pago na hora
    assert dict(world.items("camps")).get(item, 0) == 0
    assert order.entity_id not in {e.entity_id for e in world.entities()}
    assert _reputation(farmer) == pytest.approx(0.6)


def test_dois_aceitos_por_vez_e_um_pedido_so_tem_um_dono() -> None:
    farmer = _farmer()
    while len(_orders(farmer)) < 3:
        _morning(farmer)
    farmer.walk(35, 35)
    farmer.until("08:00")
    first, second, third = _orders(farmer)[:3]
    assert of_type(
        farmer.do("accept_order", target=BOARD, order=first.entity_id), "action.completed"
    )
    (taken,) = of_type(
        farmer.do("accept_order", target=BOARD, order=first.entity_id), "action.rejected"
    )
    assert taken["reason"] == "order_taken"
    assert of_type(
        farmer.do("accept_order", target=BOARD, order=second.entity_id), "action.completed"
    )
    (many,) = of_type(
        farmer.do("accept_order", target=BOARD, order=third.entity_id), "action.rejected"
    )
    assert many["reason"] == "too_many_orders"
    (unknown,) = of_type(
        farmer.do("accept_order", target=BOARD, order="order-999"), "action.rejected"
    )
    assert unknown["reason"] == "no_order"


def test_o_pedido_aceito_que_vence_baixa_a_reputacao() -> None:
    farmer = _farmer()
    order = _orders(farmer)[0]
    due = _int(order.attributes["prazo"])
    farmer.walk(35, 35)
    farmer.do("accept_order", target=BOARD, order=order.entity_id)
    while farmer.core.world.day <= due:
        _morning(farmer)
    expired = of_type(farmer.facts, "economy.order.expired")
    (gone,) = [e for e in expired if e["order_id"] == order.entity_id]
    assert gone["taker"] == "camps"
    assert gone["day"] == due + 1
    assert _reputation(farmer) == pytest.approx(0.3)
