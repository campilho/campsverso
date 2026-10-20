"""Métricas da bíblia §13 a partir de envelopes do arquivo."""

from typing import Any

from campsverso_tools.metrics import compute, table


def ev(seq: int, tick: int, kind: str, /, **data: Any) -> dict[str, Any]:
    return {
        "source": "/kernel/w",
        "seq": seq,
        "tick": tick,
        "type": f"campsverso.{kind}",
        "time": f"2026-10-12T01:00:{seq:02d}Z",
        "data": data,
    }


def test_metricas_por_dia() -> None:
    envelopes: list[dict[str, Any]] = [
        ev(0, 0, "world.session.started.v1", tick_seconds=60),
        ev(1, 0, "world.item.created.v1", item="moeda", qty=100, container_id="camps"),
        ev(2, 10, "world.item.consumed.v1", item="moeda", qty=30, container_id="camps"),
        ev(3, 1500, "farm.crop.matured.v1", plot_id="plot-e-01", days=2),
        ev(4, 1500, "farm.crop.matured.v1", plot_id="plot-w-01", days=3),
        ev(5, 1510, "action.completed.v1", action="harvest", params={"target": "plot-e-01"}),
        ev(6, 1520, "action.rejected.v1", reason="not_adjacent"),
        ev(9, 1525, "action.completed.v1", action="plant", params={"target": "plot-w-02"}),
        ev(7, 1530, "avatar.decision_requested.v1", needs={"fome": 72.5}),
        ev(8, 2880, "world.clock.phase_changed.v1"),  # o dia 3 começa: o dia 2 fica completo
        {"source": "/perception/w", "seq": 0, "tick": 1600, "type": "x", "time": "", "data": {}},
    ]
    report = compute(envelopes)
    day1, day2, day3 = report.days
    assert (day2.complete, day3.complete) == (True, False)
    assert (day1.day, day1.coins_end) == (1, 70)
    assert day2.harvests == {"leste": 1}
    assert day2.plantings == {"oeste": 1}  # ADR-0061: os plantios por grupo, para o sinal do leste
    assert report.totals()["plantings"] == {"oeste": 1}
    assert report.totals()["mean_days_to_mature"] == {"leste": 2.0, "oeste": 3.0}
    assert day2.rejections == {"not_adjacent": 1}
    assert day2.hunger_peak == 72.5
    text = table(report)
    assert "colheitas(o/l)" in text
    assert "cavados" not in text  # a fazenda 1 não tem o bloco da Boa Vista


def test_dia_incompleto_fica_fora_dos_totais() -> None:
    envelopes: list[dict[str, Any]] = [
        ev(0, 0, "world.session.started.v1", tick_seconds=60),
        ev(1, 0, "world.item.created.v1", item="moeda", qty=100, container_id="camps"),
        ev(2, 1440, "world.item.consumed.v1", item="moeda", qty=30, container_id="camps"),
        ev(3, 1450, "avatar.fainted.v1"),
    ]
    report = compute(envelopes)
    assert [d.complete for d in report.days] == [True, False]
    totals = report.totals()
    assert (totals["days"], totals["partial_day"]) == (1, 2)
    assert (totals["coins_end"], totals["faints"]) == (100, 0)


def call(seq: int, tick: int, cost: float, *, charged: bool = True) -> dict[str, Any]:
    return {
        "source": "/controller-runner/llm/camps",
        "seq": seq,
        "tick": tick,
        "type": "campsverso.llm.call.completed.v1",
        "time": f"2026-10-12T02:00:{seq:02d}Z",
        "data": {
            "latency_ms": 1000 + seq,
            "cost_usd": cost,
            "charged": charged,
            "usage": {"input_tokens": 100, "output_tokens": 10, "cache_read_input_tokens": 900},
        },
    }


def test_metricas_do_modelo_por_dia() -> None:
    """ADR-0059: chamadas, custo cobrado, tokens e latência por dia, a partir dos llm.call.*."""
    envelopes: list[dict[str, Any]] = [
        ev(0, 0, "world.session.started.v1", tick_seconds=60),
        ev(1, 2880, "world.clock.phase_changed.v1"),
        call(0, 10, 0.001),
        call(1, 20, 0.002, charged=False),  # da fita: entra nos tokens, não no custo
        call(2, 1500, 0.004),
        {
            "source": "/controller-runner/llm/camps",
            "seq": 3,
            "tick": 1510,
            "type": "campsverso.llm.call.failed.v1",
            "time": "2026-10-12T02:00:03Z",
            "data": {"error": "timeout"},
        },
    ]
    report = compute(envelopes)
    day1, day2 = report.days[:2]
    assert (day1.calls, day1.cost_usd, day1.calls_failed) == (2, 0.001, 0)
    assert day1.tokens == {
        "input_tokens": 200,
        "output_tokens": 20,
        "cache_read_input_tokens": 1800,
    }
    assert (day2.calls, day2.calls_failed, day2.cost_usd) == (1, 1, 0.004)
    llm = report.totals()["llm"]
    assert llm["calls"] == 3
    assert llm["calls_failed"] == 1
    assert llm["cost_usd"] == 0.005
    assert llm["cost_usd_per_day"] == 0.0025
    assert llm["latency_ms_median"] == 1001
    assert "llm" not in compute(envelopes[:2]).totals()  # o script não tem modelo


def test_o_grupo_do_canteiro_cavado_vem_do_atributo() -> None:
    """ADR-0062: na Boa Vista os canteiros nascem em tempo de execução com `group` no atributo."""
    envelopes: list[dict[str, Any]] = [
        ev(0, 0, "world.session.started.v1", tick_seconds=60),
        ev(
            1,
            10,
            "world.entity.spawned.v1",
            entity_id="plot-01",
            kind="plot",
            attributes={"group": "leste"},
        ),
        ev(2, 20, "action.completed.v1", action="plant", params={"target": "plot-01"}),
        ev(3, 30, "action.completed.v1", action="harvest", params={"target": "plot-01"}),
        ev(4, 40, "action.completed.v1", action="harvest", params={"target": "plot-x-09"}),
    ]
    day = compute(envelopes).days[0]
    assert day.plantings == {"leste": 1}
    assert day.harvests == {"leste": 1, "outro": 1}


def test_a_boa_vista_mede_o_que_a_biblia_2_pede() -> None:
    """ADR-0062, decisão 13: a faixa do rio pela posição (o canteiro nasce sem grupo), o dia da
    ferramenta, a mistura por semana, os pratos, os estragos, as murchas da madura e as vendas
    abaixo de 80% do preço."""
    terrain = {
        "rows": ["GGGGGGRR", "GGGGGGRR"],
        "legend": {
            "G": {"kind": "grass", "properties": {"water": False}},
            "R": {"kind": "river", "properties": {"water": True}},
        },
    }

    def spawn(seq: int, tick: int, eid: str, kind: str, **data: Any) -> dict[str, Any]:
        return ev(seq, tick, "world.entity.spawned.v1", entity_id=eid, kind=kind, **data)

    def sell(seq: int, tick: int, qty: int) -> dict[str, Any]:
        return ev(seq, tick, "world.item.transferred.v1", item="rabanete", qty=qty,
                  from_container="camps", to_container="sell-box", reason="sell")  # fmt: skip

    def done(seq: int, tick: int, action: str, **params: Any) -> dict[str, Any]:
        return ev(seq, tick, "action.completed.v1", action=action, params=params)

    def price(seq: int, tick: int, value: int, cause: str) -> dict[str, Any]:
        return ev(seq, tick, "world.entity.state_changed.v1", entity_id="sell-box",
                  changes={"preco_rabanete": value}, cause=cause)  # fmt: skip

    envelopes: list[dict[str, Any]] = [
        ev(0, 0, "world.session.started.v1", tick_seconds=60, map=terrain),
        price(1, 0, 25, "market_reset"),
        # A 4 tiles da água (x 6) é faixa do rio; a 5, fora. Os dois nascem de uma ação.
        spawn(2, 5, "plot-01", "plot", position={"x": 2, "y": 0}, action_id="act-1"),
        spawn(3, 6, "plot-02", "plot", position={"x": 1, "y": 1}, action_id="act-2"),
        spawn(4, 7, "plow-1", "plow", container_id="camps", action_id="act-3"),
        done(5, 8, "plant", target="plot-01", crop="tomate"),
        done(6, 9, "plant", target="plot-02", crop="rabanete"),
        done(7, 10, "cook", target="stove", recipe="sopa_de_batata"),
        ev(8, 11, "world.item.consumed.v1", item="rabanete", qty=2, container_id="chest",
           reason="spoiled"),
        ev(9, 12, "farm.crop.withered.v1", plot_id="plot-01", crop="tomate", day=1, dry_days=0),
        ev(10, 13, "farm.crop.withered.v1", plot_id="plot-02", crop="rabanete", day=1, dry_days=2),
        sell(11, 14, 5),  # a 25, o preço que a caixa mostrava
        price(12, 14, 19, "sell"),  # caiu abaixo de 80% de 25 (20)
        sell(13, 15, 3),
        done(14, 20, "harvest", target="plot-01"),
        ev(15, 1440 * 8, "world.clock.phase_changed.v1"),  # o dia 9 é a semana 2
        done(16, 1440 * 8 + 1, "plant", target="plot-02", crop="alho"),
        ev(17, 1440 * 9, "world.clock.phase_changed.v1"),
    ]  # fmt: skip
    report = compute(envelopes)
    day1 = report.days[0]
    assert day1.plots_dug == {"rio": 1, "fora": 1}
    assert day1.tools_bought == {"plow": 1}
    assert day1.plantings == {"rio": 1, "fora": 1}
    assert day1.plantings_by_crop == {"tomate": 1, "rabanete": 1}
    assert day1.harvests == {"rio": 1}
    assert day1.cooked == {"sopa_de_batata": 1}
    assert day1.spoiled == {"rabanete": 2}
    assert (day1.withered, day1.withered_ripe) == (2, 1)
    assert (day1.sales, day1.sales_below_floor) == (8, 3)
    totals = report.totals()
    assert totals["plots_dug"] == {"fora": 1, "rio": 1}
    assert totals["tools_bought"] == {"plow": 1}  # o dia da primeira compra
    assert totals["plantings_by_week"] == {"1": {"rabanete": 1, "tomate": 1}, "2": {"alho": 1}}
    assert (totals["withered_ripe"], totals["sales"], totals["sales_below_floor"]) == (1, 8, 3)
    assert report.groups == ("rio", "fora")
    text = table(report)
    assert "colheitas(rio/fora)" in text
    assert "cavados(rio/fora)" in text
    assert "plow" in text
