"""O orçamento da percepção (ADR-0056, decisão 8): fotos contadas, deltas estimados entre elas."""

from typing import Any

from campsverso_tools.perception_budget import CHARS_PER_TOKEN, compute


def _view(stage: str, coins: int) -> dict[str, Any]:
    return {
        "clock": {"tick": 0, "sim_time": "2026-10-10T06:00:00-03:00", "day": 1, "phase": "x"},
        "weather": {"condition": "sun", "day": 1},
        "self": {"entity_id": "camps", "position": {"x": 1, "y": 1}, "needs": {}, "asleep": False},
        "containers": [{"container_id": "camps", "items": [{"item": "moeda", "qty": coins}]}],
        "entities": [
            {
                "entity_id": f"plot-{i}",
                "kind": "plot",
                "attributes": {"stage": stage if i == 0 else "x"},
            }
            for i in range(20)
        ],
    }


def _snapshot(seq: int, tick: int, view: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "campsverso.perception.delivered.v1",
        "source": "/perception/lab",
        "seq": seq,
        "tick": tick,
        "visibility": "agent",
        "data": {"avatar_id": "camps", "kind": "snapshot", "as_of_tick": tick, "view": view},
    }


def _event(tick: int, kind: str, visibility: str = "world", **data: Any) -> dict[str, Any]:
    return {
        "type": f"campsverso.{kind}",
        "source": "/kernel/lab",
        "tick": tick,
        "visibility": visibility,
        "data": data,
    }


def test_fotos_contadas_e_deltas_estimados_entre_elas() -> None:
    archive = [
        _event(0, "world.session.started.v1", tick_seconds=60),
        _snapshot(0, 10, _view("semente", 100)),
        _event(12, "world.entity.state_changed.v1", entity_id="plot-0", changes={"stage": "broto"}),
        _event(12, "avatar.decision_requested.v1", "agent", avatar_id="camps", reason="x"),
        _snapshot(1, 14, _view("broto", 100)),
        _snapshot(2, 1500, _view("broto", 90)),  # dia 2
    ]
    report = compute(archive, every=20)
    assert [d.day for d in report.days] == [1, 2]
    first, second = report.days[0].deliveries
    assert first.delta is None  # a primeira entrega é sempre uma foto
    assert second.delta is not None
    assert second.delta < second.snapshot / 3  # mudou um canteiro em vinte: o delta é bem menor
    totals = report.totals()
    assert totals["deliveries"] == 3
    assert totals["tokens_per_day_snapshots_only"] > totals["tokens_per_day_with_deltas"] > 0
    assert totals["chars_per_token"] == CHARS_PER_TOKEN
    assert report.days[0].snapshots_only() == first.snapshot + second.snapshot
    # O pedido de decisão não entra no "o que aconteceu"; a mudança do canteiro, sim.
    delta_third = report.days[1].deliveries[0].delta
    assert delta_third is not None


def test_sem_deltas_a_politica_de_fotos_e_igual_a_so_fotos() -> None:
    archive = [_snapshot(i, i * 10, _view("semente", 100)) for i in range(3)]
    report = compute(archive, every=0)  # a cada 0 deltas: toda entrega é foto
    totals = report.totals()
    assert totals["tokens_per_day_snapshots_only"] == totals["tokens_per_day_with_deltas"]
