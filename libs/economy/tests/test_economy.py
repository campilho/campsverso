"""A economia sozinha, sem fazenda (ADR-0069): o mercado que cai e recupera, o que sobe na compra e
volta, a referência pela estação, a oscilação limitada, as encomendas e a reputação, a agenda."""

from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from campsverso_economy import (
    MarketRules,
    Order,
    OrderRules,
    Recurring,
    ReputationRules,
    after_delivery,
    after_expiry,
    buy,
    draw,
    drift,
    effect,
    expired,
    recover,
    reference,
    refuse_delivery,
    refuse_take,
    sell,
    take,
)

SELL = MarketRules(step=0.02, floor=0.4, recovery=1 / 3)
BUY = MarketRules(step=0.03, ceiling=2.0, recovery=1.0)
ORDERS = OrderRules(
    max_open=4, max_taken=2, new_per_day=2, chance=0.5, qty=(2, 6), days=(3, 7), premium=0.5
)


class Lcg:
    """Um gerador congruencial pequeno: o bastante para sortear igual em toda execução."""

    def __init__(self, seed: int) -> None:
        self.state = seed

    def random(self) -> float:
        self.state = (self.state * 6364136223846793005 + 1442695040888963407) % 2**64
        return (self.state >> 11) / 2**53

    def randint(self, low: int, high: int) -> int:
        return low + int(self.random() * (high - low + 1))


def test_vender_derruba_o_preco_unidade_por_unidade_ate_o_piso() -> None:
    trade = sell(25.0, 1.0, 3, SELL)
    assert trade.total == 25 + 25 + 24  # 25; 24,5 arredonda para cima; 24
    assert trade.factor == pytest.approx(0.94)
    assert trade.next_price == 24
    flooded = sell(25.0, 1.0, 100, SELL)
    assert flooded.factor == pytest.approx(0.4)
    assert flooded.next_price == 10


def test_o_preco_derrubado_recupera_um_terco_por_dia() -> None:
    factor = sell(25.0, 1.0, 30, SELL).factor  # 30 rabanetes: o fator vai a 0,4
    days = [factor := recover(factor, SELL) for _ in range(4)]
    assert days[0] == pytest.approx(0.6)
    assert days[1] == pytest.approx(0.733333, abs=1e-5)
    assert days[3] < 1.0  # o que se despejou ainda pesa quatro dias depois


def test_comprar_sobe_o_preco_e_ele_volta_inteiro_de_manha() -> None:
    trade = buy(10.0, 1.0, 5, BUY)
    assert trade.total == 10 + 10 + 11 + 11 + 11  # 10; 10,3; 10,6; 10,9; 11,2
    assert trade.next_price == 12  # 11,5 arredonda para cima
    assert recover(trade.factor, BUY) == 1.0


def test_a_referencia_pela_estacao_pela_oscilacao_e_pelo_choque() -> None:
    assert reference(40) == 40
    assert reference(40, season=1.25) == 50
    assert reference(40, season=1.6, drift=0.05, shock=0.15) == pytest.approx(
        40 * 1.6 * 1.05 * 1.15
    )


def test_a_oscilacao_anda_pouco_por_dia_e_nao_passa_do_limite() -> None:
    rng = Lcg(7)
    value = 0.0
    for _ in range(200):
        moved = drift(value, rng, 0.04, 0.15)
        assert abs(moved - value) <= 0.04 + 1e-9
        assert -0.15 <= moved <= 0.15
        value = moved


@given(st.floats(0.0, 3.0), st.integers(0, 60))
def test_o_fator_fica_entre_o_piso_e_o_teto(factor: float, qty: int) -> None:
    assert sell(30.0, max(factor, SELL.floor), qty, SELL).factor >= SELL.floor
    assert buy(30.0, min(factor, BUY.ceiling), qty, BUY).factor <= BUY.ceiling


@given(st.floats(0.0, 3.0))
def test_a_recuperacao_aproxima_da_referencia_sem_passar(factor: float) -> None:
    after = recover(factor, SELL)
    assert abs(after - 1.0) <= abs(factor - 1.0) + 1e-9
    assert (after - 1.0) * (factor - 1.0) >= -1e-12


def _ids() -> Callable[[], str]:
    counter = iter(range(1, 1000))
    return lambda: f"order-{next(counter):03d}"


def test_os_pedidos_do_dia_sao_os_mesmos_pela_seed() -> None:
    candidates = [("milho", 45.0), ("rabanete", 25.0)]
    clients = ["Dona Cida", "Seu Juca", "a padaria"]
    rep = ReputationRules()

    def day_orders(seed: int) -> list[Order]:
        rng = Lcg(seed)
        return draw(rng, 3, 0, candidates, clients, ORDERS, 0.5, rep, _ids())

    first = draw(Lcg(11), 3, 0, candidates, clients, ORDERS, 0.5, rep, _ids())
    assert first == day_orders(11)
    for order in first:
        assert 2 <= order.qty <= 6
        assert 6 <= order.due_day <= 10
        base = dict(candidates)[order.item]
        assert order.reward == int(order.qty * base * 1.5 + 0.5)
    assert draw(Lcg(11), 3, 4, candidates, clients, ORDERS, 0.5, rep, _ids()) == []


def test_a_reputacao_mexe_na_chance_e_no_premio() -> None:
    rep = ReputationRules()
    assert effect(0.5, rep) == 1.0
    assert effect(1.0, rep) == 1.5
    assert effect(0.0, rep) == 0.5
    always = OrderRules(4, 2, 4, 1.0, (3, 3), (5, 5), 0.5)
    good = draw(Lcg(3), 1, 0, [("milho", 40.0)], ["Dona Cida"], always, 1.0, rep, _ids())
    bad = draw(Lcg(3), 1, 0, [("milho", 40.0)], ["Dona Cida"], always, 0.0, rep, _ids())
    assert good[0].reward == 3 * 40 * (1 + 0.5 * 1.5)  # 210
    assert bad[0].reward == 3 * 40 * (1 + 0.5 * 0.5)  # 150
    counts = [
        sum(
            len(draw(Lcg(s), 1, 0, [("milho", 40.0)], ["x"], ORDERS, r, rep, _ids()))
            for s in range(200)
        )
        for r in (0.0, 0.5, 1.0)
    ]
    assert (
        counts[0] < counts[1] < counts[2]
    )  # o quadro esvazia para quem falha e enche para quem cumpre
    assert after_delivery(0.95, rep) == 1.0
    assert after_expiry(0.1, rep) == 0.0


def test_aceitar_entregar_e_vencer() -> None:
    order = draw(
        Lcg(1),
        1,
        0,
        [("milho", 40.0)],
        ["Dona Cida"],
        OrderRules(4, 2, 1, 1.0, (2, 2), (3, 3), 0.5),
        0.5,
        ReputationRules(),
        _ids(),
    )[0]
    assert refuse_take(order, "camps", 2, ORDERS) == "too_many_orders"
    taken = take(order, "camps")
    assert refuse_take(taken, "ana", 0, ORDERS) == "order_taken"
    assert refuse_delivery(order, "camps", 2) == "not_your_order"
    assert refuse_delivery(taken, "ana", 2) == "not_your_order"
    assert refuse_delivery(taken, "camps", 4) is None  # o último dia ainda vale
    assert expired(taken, 5)
    assert refuse_delivery(taken, "camps", 5) == "order_expired"


def test_a_feira_a_cada_sete_dias() -> None:
    fair = Recurring(every=7, first=7)
    assert [d for d in range(1, 30) if fair.happens(d)] == [7, 14, 21, 28]
    assert fair.next_on(1) == 7
    assert fair.next_on(8) == 14
    assert fair.next_on(14) == 14
