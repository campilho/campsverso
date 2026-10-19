"""A mente no ciclo inteiro em memória (ADR-0059): kernel, percepção, runner, mente, medidor e
guarda, com uma porta falsa (a tubulação) e com a fita gravada pela API (um dia do Camps)."""

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from campsverso_adapters import RecordingModel
from campsverso_budget.ledger import BudgetLimits
from campsverso_ports import (
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
)
from campsverso_testkit.nats_server import REPO
from campsverso_testkit.pipeline import LLM_ID, Pipeline

LIMITS = BudgetLimits(usd_per_sim_day=0.60, usd_total=10.0)


class WaitingPort:
    """Uma porta que só sabe esperar: o bastante para ver a tubulação inteira funcionar."""

    provider = "fake"

    def __init__(self) -> None:
        self.lengths: list[int] = []  # mensagens por pedido: a janela cresce e zera na foto

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 1

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.lengths.append(len(request.messages))
        return ModelResponse(
            content=[
                {"type": "thinking", "thinking": "", "signature": "x"},
                {
                    "type": "tool_use",
                    "id": f"toolu_{len(self.lengths)}",
                    "name": "wait",
                    "input": {"ticks": 15, "intent": "esperar e observar"},
                },
            ],
            stop_reason="tool_use",
            usage=ModelUsage(1200, 40, 0, 0),
            model=request.model,
            latency_ms=1,
        )


def _by(events: Sequence[Mapping[str, Any]], key: str) -> set[Any]:
    return {e[key] for e in events}


async def test_a_tubulacao_da_mente_com_uma_porta_falsa() -> None:
    port = WaitingPort()
    pipeline = Pipeline(controller="llm", port=port, budget=LIMITS)
    await pipeline.start()
    await pipeline.run_days(1)
    proposals = pipeline.of_type("cmd.action.propose.v1")
    calls = pipeline.of_type("llm.call.completed.v1")
    assert len(proposals) == len(calls) == len(port.lengths) > 30
    assert _by(proposals, "action") == {"wait"}
    assert _by(proposals, "intent") == {"esperar e observar"}
    assert pipeline.of_type("llm.call.failed.v1") == []
    assert _by(calls, "charged") == {True}
    assert {c["controller"]["id"] for c in calls} == {LLM_ID}
    assert {c["purpose"] for c in calls} == {"decision"}
    stamped = [e for e in pipeline.envelopes if e["type"] == "campsverso.llm.call.completed.v1"]
    assert all(int(e["tick"]) > 0 for e in stamped[1:])  # o relógio simulado vem das entregas
    snapshots = pipeline.of_type("perception.delivered.v1")
    deltas = pipeline.of_type("perception.updated.v1")
    assert len(snapshots) >= 2  # a primeira decisão e a foto a cada 20 deltas (ADR-0056)
    assert len(deltas) > 20
    assert port.lengths[0] == 1  # a foto abre a janela
    assert max(port.lengths) > 20  # a janela cresce: cada delta é um turno
    assert port.lengths.count(1) == len(snapshots)  # e cada foto zera a janela
    assert pipeline.of_type("ops.budget.exceeded.v1") == []
    assert pipeline.core.world.avatar_map["camps"].controller.id == LLM_ID


# ----------------------------------------------------------------- um dia do Camps, pela fita

FIXTURE = REPO / "tests" / "fixtures" / "llm" / "camps-dia-1.jsonl"


async def test_um_dia_do_camps_pela_fita() -> None:
    """A fita gravada com a API (make fita DIAS=1) reproduz o dia 1 do Camps sem rede: as mesmas
    chamadas, nada cobrado, nenhum desmaio, a guarda quieta. Mudou o cartão, as notas ou o
    catálogo, muda o hash do pedido: grava de novo (ADR-0059)."""
    recorded = sum(1 for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line)
    pipeline = Pipeline(
        controller="llm", port=RecordingModel(None, FIXTURE, "replay"), budget=LIMITS
    )
    await pipeline.start()
    await pipeline.run_days(1)
    calls = pipeline.of_type("llm.call.completed.v1")
    assert (
        pipeline.of_type("llm.call.failed.v1") == []
    )  # nenhum cassette_miss: o prompt é o gravado
    assert len(calls) == recorded == 41
    assert _by(calls, "charged") == {False}
    assert pipeline.mind is not None
    assert pipeline.mind.no_tool == 0
    assert pipeline.of_type("avatar.fainted.v1") == []
    assert pipeline.of_type("ops.budget.exceeded.v1") == []
    done = Counter(str(a["action"]) for a in pipeline.of_type("action.completed.v1"))
    assert done["plant"] == 8  # o dia 1 do Camps: os oito canteiros do oeste plantados e regados
    assert done["water"] == 8
    assert done["eat"] >= 1
    assert done["sleep"] == 1
    assert pipeline.of_type("action.rejected.v1") == []
    needs = pipeline.core.world.needs_points("camps")
    assert needs["fome"] < 100
    intents = [str(a["intent"]) for a in pipeline.of_type("action.accepted.v1") if a.get("intent")]
    assert len(intents) == len(
        pipeline.of_type("action.accepted.v1")
    )  # toda ação aceita tem a intenção
    assert all(intents)
