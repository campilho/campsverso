"""O livro-caixa da guarda (ADR-0058): cada limiar avisa uma vez, por dia e no total; reentrega
não conta."""

import json

from campsverso_budget.ledger import BudgetLedger, BudgetLimits


def test_avisos_saem_uma_vez_por_limiar_e_a_reentrega_nao_conta() -> None:
    ledger = BudgetLedger(BudgetLimits(usd_per_sim_day=0.6, usd_total=10.0))
    assert ledger.record("a", 1, 0.25) == []  # 41% do dia
    notices = ledger.record("b", 1, 0.25)  # 83%: os dois limiares de uma vez, em ordem
    assert [(n.scope, n.day, n.threshold_pct) for n in notices] == [("day", 1, 50), ("day", 1, 80)]
    assert ledger.record("b", 1, 0.25) == []  # o mesmo id de novo: nada
    assert ledger.by_day == {"1": 0.5}
    (exceeded,) = ledger.record("c", 1, 0.25)
    assert (exceeded.threshold_pct, exceeded.exceeded, exceeded.spent_usd) == (100, True, 0.75)
    assert ledger.record("d", 1, 0.25) == []  # já avisado: nada até virar o dia
    (fresh,) = ledger.record("e", 2, 0.30)  # dia novo: 50% de novo
    assert (fresh.day, fresh.threshold_pct) == (2, 50)
    assert ledger.total == 1.3


def test_teto_total_e_ida_e_volta_em_json() -> None:
    ledger = BudgetLedger(BudgetLimits(usd_per_sim_day=100.0, usd_total=1.0))
    notices = ledger.record("x", 1, 0.9)
    assert [(n.scope, n.threshold_pct) for n in notices] == [("total", 50), ("total", 80)]
    copy = BudgetLedger(ledger.limits, json.loads(json.dumps(ledger.export())))
    assert (copy.total, copy.by_day, copy.reached) == (
        0.9,
        {"1": 0.9},
        {"day:1": [], "total": [50, 80]},
    )
    (exceeded,) = copy.record("y", 1, 0.2)
    assert (exceeded.scope, exceeded.exceeded) == ("total", True)
    assert copy.record("x", 1, 0.9) == []  # os ids vistos também voltam
