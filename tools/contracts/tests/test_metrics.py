"""Métricas da bíblia §13 a partir de envelopes do arquivo."""

from typing import Any

from campsverso_tools.metrics import compute


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
        ev(7, 1530, "avatar.decision_requested.v1", needs={"fome": 72.5}),
        ev(8, 2880, "world.clock.phase_changed.v1"),  # o dia 3 começa: o dia 2 fica completo
        {"source": "/perception/w", "seq": 0, "tick": 1600, "type": "x", "time": "", "data": {}},
    ]
    report = compute(envelopes)
    day1, day2, day3 = report.days
    assert (day2.complete, day3.complete) == (True, False)
    assert (day1.day, day1.coins_end) == (1, 70)
    assert day2.harvests == {"leste": 1}
    assert report.totals()["mean_days_to_mature"] == {"leste": 2.0, "oeste": 3.0}
    assert day2.rejections == {"not_adjacent": 1}
    assert day2.hunger_peak == 72.5


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
