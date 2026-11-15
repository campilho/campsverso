"""O livro-caixa da guarda (ADR-0058): cada limiar avisa uma vez, por dia e no total; o teto
estourado avisa de novo a cada chamada cobrada; reentrega não conta."""

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
    (again,) = ledger.record("d", 1, 0.25)  # o teto do dia segue estourado: avisa de novo
    assert (again.scope, again.threshold_pct, again.repeated, again.spent_usd) == (
        "day",
        100,
        True,
        1.0,
    )
    assert exceeded.repeated is False
    assert ledger.record("d", 1, 0.25) == []  # a reentrega da mesma chamada continua sem contar
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
    # O teto do mundo não vira com o dia, e o que já estourou sobrevive à ida e volta em JSON.
    later = BudgetLedger(copy.limits, json.loads(json.dumps(copy.export())))
    (repeat,) = later.record("z", 9, 0.01)
    assert (repeat.scope, repeat.day, repeat.repeated) == ("total", None, True)
    assert repeat.exceeded


def test_o_pedido_tem_teto_proprio_e_sem_teto_so_soma() -> None:
    """O teto por pedido do escritório (ADR-0080): cada pedido conta à parte, ao lado do dia e do
    total. Sem `usd_per_ticket`, o gasto do pedido só é somado."""
    ledger = BudgetLedger(BudgetLimits(usd_per_sim_day=10.0, usd_total=100.0, usd_per_ticket=1.0))
    notices = ledger.record("a", 1, 0.85, "pedido-1")
    assert [(n.scope, n.ticket_id, n.threshold_pct) for n in notices] == [
        ("ticket", "pedido-1", 50),
        ("ticket", "pedido-1", 80),
    ]
    assert ledger.record("b", 1, 0.40, "pedido-2") == []  # outro pedido, outra conta
    (done,) = ledger.record("c", 1, 0.20, "pedido-1")
    assert (done.scope, done.exceeded, done.day, done.spent_usd) == ("ticket", True, None, 1.05)
    (again,) = ledger.record("d", 1, 0.01, "pedido-1")
    assert (again.ticket_id, again.repeated) == ("pedido-1", True)
    assert ledger.record("e", 1, 0.01) == []  # sem pedido: só o dia e o total
    assert ledger.by_ticket == {"pedido-1": 1.06, "pedido-2": 0.4}
    assert ledger.exceeded_now() == ["pedido-1"]

    free = BudgetLedger(BudgetLimits(usd_per_sim_day=10.0, usd_total=100.0))
    notices = free.record("a", 1, 5.0, "pedido-1")
    assert [n.scope for n in notices] == ["day"]  # 50% do dia; nenhum aviso de pedido
    assert free.by_ticket == {"pedido-1": 5.0}


def test_os_tetos_novos_desfazem_o_estouro_e_voltam_depois_de_uma_queda() -> None:
    """O `cmd.ops.budget.set` (ADR-0080): subir o teto acima do gasto desfaz o estouro e rearma os
    avisos acima do gasto; os tetos do comando valem no lugar dos do arquivo, inclusive depois de
    uma queda. Baixar o teto avisa na chamada seguinte."""
    file_limits = BudgetLimits(usd_per_sim_day=0.6, usd_total=10.0)
    ledger = BudgetLedger(file_limits)
    ledger.record("a", 1, 0.7)  # 50, 80 e 100% do dia
    assert ledger.exceeded_now() == ["day"]
    ledger.set_limits(ledger.limits.changed({"usd_per_sim_day": 1.0, "reason": "mais um pouco"}))
    assert ledger.limits == BudgetLimits(usd_per_sim_day=1.0, usd_total=10.0)
    assert ledger.exceeded_now() == []
    assert ledger.reached["day:1"] == [50]  # 70% de 1,00: o 80 e o 100 voltam a valer
    (eighty,) = ledger.record("b", 1, 0.15)
    assert (eighty.threshold_pct, eighty.repeated) == (80, False)

    back = BudgetLedger(file_limits, json.loads(json.dumps(ledger.export())))
    assert back.limits.usd_per_sim_day == 1.0  # o do comando, e não o do arquivo
    back.set_limits(back.limits.changed({"usd_per_ticket": 0.5, "usd_total": 0.8}))
    assert back.limits == BudgetLimits(usd_per_sim_day=1.0, usd_total=0.8, usd_per_ticket=0.5)
    notices = back.record("c", 1, 0.01)  # o total baixou para menos que o gasto
    assert [(n.scope, n.threshold_pct) for n in notices] == [
        ("total", 50),
        ("total", 80),
        ("total", 100),
    ]
    assert back.exceeded_now() == ["total"]
    untouched = BudgetLedger(
        file_limits, json.loads(json.dumps(BudgetLedger(file_limits).export()))
    )
    assert "limits" not in untouched.export()  # sem comando, vale o arquivo
