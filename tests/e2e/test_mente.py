"""A mente no ciclo inteiro em memória (ADR-0059): kernel, percepção, runner, mente, medidor e
guarda, com uma porta falsa (a tubulação) e com a fita gravada pela API (um dia do Camps)."""

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from campsverso_adapters import RecordingModel, SqliteMemory
from campsverso_budget.ledger import BudgetLimits
from campsverso_mind import Clock, Memory, MemorySettings
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


# ------------------------------------------------------- dois dias do Camps, pela fita

FIXTURE = REPO / "tests" / "fixtures" / "llm" / "camps-dia-2.jsonl"
HOUR = re.compile(r"\b([01]\d|2[0-3]):[0-5]\d\b")


def _recorded() -> int:
    return sum(1 for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line)


def _hours_of_day(pipeline: Pipeline, day: int) -> set[str]:
    """As horas (HH:MM) em que o kernel publicou algo num dia: o que o agente pôde ver."""
    hours: set[str] = set()
    for envelope in pipeline.kernel_events():
        tick = int(envelope.get("tick") or 0)
        if tick // 1440 + 1 == day and envelope.get("simtime"):
            hours.add(str(envelope["simtime"])[11:16])
    return hours


async def test_dois_dias_do_camps_pela_fita() -> None:
    """A fita gravada com a API (make fita DIAS=2) reproduz dois dias do Camps sem rede: as mesmas
    chamadas, nada cobrado, nenhum desmaio, a guarda quieta; à noite do dia 1 a reflexão formou
    crenças com evidências do que ele viu, e a janela seguinte abriu com o resumo (ADR-0060).
    Mudou o cartão, as notas, o catálogo ou a memória, muda o hash do pedido: grava de novo."""
    pipeline = Pipeline(
        controller="llm", port=RecordingModel(None, FIXTURE, "replay"), budget=LIMITS
    )
    await pipeline.start()
    await pipeline.run_days(2)
    calls = pipeline.of_type("llm.call.completed.v1")
    assert pipeline.of_type("llm.call.failed.v1") == []  # nenhum cassette_miss
    assert len(calls) == _recorded()
    assert _by(calls, "charged") == {False}
    assert {c["purpose"] for c in calls} == {"decision", "reflection"}
    assert pipeline.mind is not None
    assert pipeline.mind.no_tool == 0
    assert pipeline.mind.reflections >= 1
    assert pipeline.of_type("avatar.fainted.v1") == []
    assert pipeline.of_type("ops.budget.exceeded.v1") == []
    done = Counter(str(a["action"]) for a in pipeline.of_type("action.completed.v1"))
    assert done["plant"] >= 8
    assert done["sleep"] >= 1
    assert pipeline.core.world.needs_points("camps")["fome"] < 100
    reflected = pipeline.of_type("memory.reflected.v1")
    assert reflected[0]["day"] == 1
    assert reflected[0]["summary"]
    formed = pipeline.of_type("memory.belief.formed.v1")
    assert formed, "a primeira noite forma pelo menos uma crença"
    evidence = [line for b in formed for line in b["evidence"]]
    assert evidence, "toda crença nova cita o que o agente viu"
    cited = {m.group(0) for line in evidence for m in HOUR.finditer(line)}
    seen = _hours_of_day(pipeline, 1) | _hours_of_day(pipeline, 2)
    assert cited & seen, f"nenhuma hora citada existe no arquivo: {sorted(cited)[:5]}"
    opening = str(pipeline.mind.window.messages[0]["content"][0]["text"])
    assert opening.startswith("## O que você lembra")
    assert "ao dormir:" in opening  # a janela abriu com o resumo da última noite


async def test_a_memoria_sobrevive_a_um_reinicio_da_mente(tmp_path: Path) -> None:
    """O arquivo da memória, fechado e reaberto por uma mente nova, abre a janela com o que o
    Camps aprendeu ontem (ADR-0060)."""
    path = tmp_path / "camps.sqlite"
    pipeline = Pipeline(
        controller="llm",
        port=RecordingModel(None, FIXTURE, "replay"),
        memory=SqliteMemory(path),
    )
    await pipeline.start()
    await pipeline.run_days(1)
    assert pipeline.mind is not None
    assert pipeline.mind.memory is not None
    pipeline.mind.memory.port.close()

    reopened = SqliteMemory(path)
    beliefs = reopened.beliefs()
    assert beliefs
    last = reopened.last_reflection()
    assert last is not None
    assert last.day == 1
    block = Memory(reopened, "camps", MemorySettings()).block(
        Clock(1440, 2, "2026-10-11T06:00:00-03:00")
    )
    assert f"Dia 1, ao dormir: {last.summary}" in block
    assert beliefs[0].statement in block
