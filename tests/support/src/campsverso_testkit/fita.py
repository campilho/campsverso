"""Grava a fita de teste do controlador LLM (ADR-0059).

    uv run --env-file .env python -m campsverso_testkit.fita --days 1

O pipeline em memória (kernel, percepção, mente e guarda de orçamento), com a mente sobre a API de
verdade em modo `record`, por N dias simulados: o mesmo mundo, a mesma seed e os mesmos ids dos
testes, então a fita gravada reproduz o dia exatamente, em `replay`, sem rede. Ao fim, a fita
magra (o hash do pedido e a resposta, sem o corpo do pedido) vai para `--out`, e o próprio comando
a reproduz uma vez, para conferir. Custa uns centavos no Haiku 5.5; o CI nunca roda isto.

**O escritório** (`--cartridge office_campsverso`; o plano do M24, §8): a manhã do primeiro dia do
mundo de teste, até as 12:00, com a mente com rotina do dev e a oficina no repositório de exemplo
(`tests/fixtures/oficina`): o bom-dia do gerente e os pedidos das 9:30 e das 10:30. O mundo espera
cada sessão (`background=False`), e a gravação para se o gasto passar de `OFFICE_CAP_USD`.
"""

import argparse
import asyncio
import json
import os
import statistics
import sys
import tempfile
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from campsverso_adapters import AnthropicModel, RecordingModel, SystemWallClock
from campsverso_budget.ledger import BudgetLimits
from campsverso_ports import (
    ModelCallError,
    ModelCapabilities,
    ModelPort,
    ModelRequest,
    ModelResponse,
)
from campsverso_testkit.nats_server import REPO
from campsverso_testkit.oficina import example_office_repo
from campsverso_testkit.pipeline import Pipeline

LIMITS = BudgetLimits(usd_per_sim_day=0.60, usd_total=10.0)
FIXTURES = REPO / "tests" / "fixtures" / "llm"


def slim(source: Path, out: Path) -> int:
    """A fita magra: tudo menos o corpo do pedido (a reprodução só precisa do hash)."""
    entries = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(
                json.dumps({k: v for k, v in entry.items() if k != "request"}, ensure_ascii=False)
                + "\n"
            )
    return len(entries)


def summary(pipeline: Pipeline) -> dict[str, Any]:
    """O que o Camps fez e quanto custou, lido dos eventos do próprio pipeline."""
    completed = pipeline.of_type("llm.call.completed.v1")
    failed = pipeline.of_type("llm.call.failed.v1")
    done = pipeline.of_type("action.completed.v1")
    # Só o que foi cobrado conta: em `record`, um pedido repetido volta da fita de graça, com o
    # `usage` e a latência da gravação, e somá-los inflaria o custo (o laço da reflexão do M11).
    charged = [c for c in completed if c["charged"]]
    usage = Counter[str]()
    for call in charged:
        for key, value in call["usage"].items():
            usage[str(key)] += int(value)
    latencies = [int(c["latency_ms"]) for c in charged]
    mind = pipeline.mind  # o script não tem mente: os contadores dela ficam em zero (ADR-0061)
    return {
        "days": pipeline.core.tick // 1440,
        "calls": len(completed),
        "failed": len(failed),
        "charged": len(charged),
        "replayed": len(completed) - len(charged),
        "cost_usd": round(sum(float(c["cost_usd"]) for c in charged), 4),
        "tokens": dict(usage),
        "latency_ms_median": int(statistics.median(latencies)) if latencies else 0,
        "no_tool": mind.no_tool if mind is not None else 0,
        "reflections": mind.reflections if mind is not None else 0,
        "comparisons": mind.memory.comparisons if mind is not None and mind.memory else 0,
        "advised": mind.memory.advised if mind is not None and mind.memory else 0,
        "gave_up": mind.gave_up if mind is not None else False,
        "notes": len(pipeline.of_type("memory.noted.v1")),
        "beliefs": {
            "formed": len(pipeline.of_type("memory.belief.formed.v1")),
            "updated": len(pipeline.of_type("memory.belief.updated.v1")),
            "retracted": len(pipeline.of_type("memory.belief.retracted.v1")),
        },
        "snapshots": len(pipeline.of_type("perception.delivered.v1")),
        "deltas": len(pipeline.of_type("perception.updated.v1")),
        "actions": dict(sorted(Counter(str(a["action"]) for a in done).items())),
        "rejected": dict(
            sorted(
                Counter(str(r["reason"]) for r in pipeline.of_type("action.rejected.v1")).items()
            )
        ),
        "faints": len(pipeline.of_type("avatar.fainted.v1")),
        "needs": pipeline.core.world.needs_points("camps"),
        "budget_notices": len(pipeline.of_type("ops.budget.threshold_reached.v2")),
        "budget_exceeded": len(pipeline.of_type("ops.budget.exceeded.v2")),
    }


OFFICE = "office_campsverso"
OFFICE_MODEL = "claude-sonnet-5-5"  # o dos mundos do escritório, com o esforço médio deles
OFFICE_HOURS = 12  # a manhã do primeiro dia: o bom-dia e os pedidos das 9:30 e das 10:30
OFFICE_CAP_USD = 1.00  # a gravação para se passar disto (a conta prevista é bem menor)

SLUGS = {
    "farm_camps": "camps",
    "farm_boavista": "boavista",
    "farm_morada_do_sol": "morada",
    OFFICE: "escritorio",
}


class Capped:
    """Uma porta com teto de gasto: antes de cada chamada, soma o que já foi cobrado (os eventos do
    medidor do próprio pipeline) e recusa passar do teto."""

    def __init__(self, inner: ModelPort, cap_usd: float) -> None:
        self._inner = inner
        self._cap = cap_usd
        self.pipeline: Pipeline | None = None

    @property
    def provider(self) -> str:
        return self._inner.provider

    def capabilities(self) -> ModelCapabilities:
        return self._inner.capabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return await self._inner.count_tokens(request)

    def spent(self) -> float:
        if self.pipeline is None:
            return 0.0
        calls = self.pipeline.of_type("llm.call.completed.v1")
        return sum(float(c["cost_usd"]) for c in calls if c["charged"])

    async def complete(self, request: ModelRequest) -> ModelResponse:
        if self.spent() >= self._cap:
            raise ModelCallError("bad_request", f"o teto da gravação: US$ {self._cap:.2f}")
        return await self._inner.complete(request)


def office_summary(pipeline: Pipeline) -> dict[str, Any]:
    """O que o dev fez na manhã do escritório e quanto custou."""
    completed = pipeline.of_type("llm.call.completed.v1")
    charged = [c for c in completed if c["charged"]]
    usage = Counter[str]()
    for call in charged:
        for key, value in call["usage"].items():
            usage[str(key)] += int(value)
    mind = pipeline.office_mind
    assert mind is not None
    return {
        "calls": len(completed),
        "failed": len(pipeline.of_type("llm.call.failed.v1")),
        "charged": len(charged),
        "replayed": len(completed) - len(charged),
        "cost_usd": round(sum(float(c["cost_usd"]) for c in charged), 4),
        "tokens": dict(usage),
        "sessions": mind.sessions,
        "replies": mind.replies,
        "unfinished": sorted(mind.failed),
        "delivered": [str(d["ticket_id"]) for d in pipeline.of_type("office.ticket.delivered.v1")],
        "patches": len([k for k in pipeline.deliveries.blobs if k.endswith(".patch")]),
        "steps": dict(
            sorted(Counter(str(s["tool"]) for s in pipeline.of_type("workshop.step.v2")).items())
        ),
        "robots": len(pipeline.of_type("workshop.robot_called.v1")),
    }


async def run_office(port: ModelPort, model: str = OFFICE_MODEL) -> dict[str, Any]:
    """A manhã do escritório, com a oficina numa cópia nova do repositório de exemplo."""
    with tempfile.TemporaryDirectory(prefix="campsverso-escritorio-") as folder:
        repo = example_office_repo(Path(folder))
        pipeline = Pipeline(
            controller="llm", port=port, cartridge=OFFICE, workshop_repo=repo, model=model
        )
        if isinstance(port, Capped):
            port.pipeline = pipeline
        await pipeline.start()
        await pipeline.run_until(pipeline.day * OFFICE_HOURS // 24)
        return office_summary(pipeline)


async def run_days(days: int, port: ModelPort, cartridge: str = "farm_camps") -> dict[str, Any]:
    pipeline = Pipeline(controller="llm", port=port, budget=LIMITS, cartridge=cartridge)
    await pipeline.start()
    await pipeline.run_days(days)
    return summary(pipeline)


async def record(days: int, out: Path, cartridge: str = "farm_camps") -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY ausente: rode com --env-file .env (ADR-0058)", file=sys.stderr)
        return 2
    scratch = Path(tempfile.mkdtemp(prefix="campsverso-fita-")) / "gravacao.jsonl"
    clock = SystemWallClock()
    office = cartridge == OFFICE
    api: ModelPort = AnthropicModel(clock=clock)
    if office:
        api = Capped(api, OFFICE_CAP_USD)
    recorder = RecordingModel(api, scratch, "record", clock=clock)
    if office:
        print(f"gravando a manhã do escritório com {OFFICE_MODEL}...", flush=True)
        recorded = await run_office(recorder)
    else:
        print(f"gravando {days} dia(s) com a API... (uma chamada por decisão)", flush=True)
        recorded = await run_days(days, recorder, cartridge)
    print(json.dumps({"gravacao": recorded}, ensure_ascii=False, indent=2), flush=True)
    entries = slim(scratch, out)
    print(f"fita magra: {out} ({entries} chamadas)", flush=True)
    tape = RecordingModel(None, out, "replay")
    replayed = await (run_office(tape) if office else run_days(days, tape, cartridge))
    print(json.dumps({"reproducao": replayed}, ensure_ascii=False, indent=2), flush=True)
    if replayed["failed"] or replayed["calls"] != recorded["calls"] or replayed["charged"]:
        print("a reprodução não bateu com a gravação: a fita não serve de teste", file=sys.stderr)
        return 1
    print("reprodução ok: mesmas chamadas, nenhuma falha, nada cobrado", flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.fita")
    parser.add_argument("--days", type=int, default=1, help="dias simulados a gravar")
    parser.add_argument(
        "--out", type=Path, help="a fita magra (padrão: tests/fixtures/llm/<cartucho>-dia-N.jsonl)"
    )
    parser.add_argument(
        "--cartridge", choices=sorted(SLUGS), default="farm_camps", help="o mundo (ADR-0062)"
    )
    args = parser.parse_args(argv)
    slug = SLUGS[args.cartridge]
    office = args.cartridge == OFFICE
    out = args.out or FIXTURES / (
        f"{slug}-manha.jsonl" if office else f"{slug}-dia-{args.days}.jsonl"
    )
    return asyncio.run(record(args.days, out, args.cartridge))


if __name__ == "__main__":
    sys.exit(main())
