"""A guarda no pipeline em memória (ADR-0058): chamadas cobradas estouram o teto e o kernel para."""

from typing import Any

from campsverso_adapters import MemoryBlobStore
from campsverso_budget.ledger import BudgetLimits
from campsverso_budget.service import COMPLETED, EXCEEDED, PAUSE, THRESHOLD, BudgetService
from campsverso_contracts import subject
from campsverso_testkit.farm import WORLD
from campsverso_testkit.pipeline import Pipeline

LIMITS = BudgetLimits(usd_per_sim_day=0.6, usd_total=10.0)


def _call(
    pipeline: Pipeline, seq: int, tick: int, cost: float, *, charged: bool = True
) -> dict[str, Any]:
    return {
        "specversion": "1.0",
        "id": pipeline.ids.new_id(),
        "source": "/controller-runner/llm/haiku",
        "type": COMPLETED,
        "time": "2026-10-18T03:00:00Z",
        "datacontenttype": "application/json",
        "dataschema": "contracts://events/llm/call.completed.v1",
        "worldid": WORLD,
        "cartridge": "farm_camps",
        "tick": tick,
        "simtime": "2026-10-10T06:10:00-03:00",
        "seq": seq,
        "provenance": "simulated",
        "visibility": "observer",
        "actor": "system/controller-runner",
        "data": {
            "controller": {"type": "llm", "id": "llm/haiku"},
            "purpose": "decision",
            "provider": "anthropic",
            "model": "claude-haiku-5-5",
            "prompt_sha256": "ab" * 32,
            "latency_ms": 900,
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "cost_usd": cost,
            "charged": charged,
            "stop_reason": "tool_use",
        },
    }


async def test_estourar_o_teto_do_dia_pausa_o_mundo_e_o_gasto_sobrevive_a_uma_queda() -> None:
    pipeline = Pipeline(controller="none")
    blobs = MemoryBlobStore()
    guard = BudgetService(
        WORLD, LIMITS, pipeline.bus, blobs, pipeline.clock, pipeline.ids, pipeline.telemetry
    )
    await guard.start()
    await pipeline.start()
    assert pipeline.core.paused is False

    async def call(seq: int, tick: int, cost: float, **kw: Any) -> None:
        await pipeline.bus.publish(
            subject(COMPLETED, WORLD), _call(pipeline, seq, tick, cost, **kw)
        )

    await call(0, 10, 0.25)
    await call(1, 20, 0.40, charged=False)  # reproduzida da fita: não conta
    await call(2, 30, 0.25)
    assert pipeline.core.paused is False
    assert [n["threshold_pct"] for n in pipeline.of_type("ops.budget.threshold_reached.v1")] == [
        50,
        80,
    ]
    await call(3, 40, 0.25)
    assert pipeline.core.paused is True  # o kernel recebeu cmd.clock.pause pelo barramento
    pauses = pipeline.of_type("cmd.clock.pause.v1")
    assert pauses == [{"reason": "budget"}]
    (exceeded,) = pipeline.of_type("ops.budget.exceeded.v1")
    assert exceeded == {
        "scope": "day",
        "day": 1,
        "spent_usd": 0.75,
        "limit_usd": 0.6,
        "paused": True,
    }
    assert guard.paused_times == 1
    assert [
        e["type"] for _, e in pipeline.inner.published if e["type"] in (THRESHOLD, PAUSE, EXCEEDED)
    ] == [THRESHOLD, THRESHOLD, THRESHOLD, PAUSE, EXCEEDED]

    # A guarda caiu e voltou: o livro-caixa veio do arquivo, e uma chamada repetida não conta.
    again = BudgetService(
        WORLD, LIMITS, pipeline.bus, blobs, pipeline.clock, pipeline.ids, pipeline.telemetry
    )
    assert again.ledger.total == 0.75
    assert again.ledger.record(pipeline.inner.published[-5][1]["id"], 1, 0.25) == []
    await guard.stop()
