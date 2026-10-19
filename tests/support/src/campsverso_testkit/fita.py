"""Grava a fita de teste do controlador LLM (ADR-0059).

    uv run --env-file .env python -m campsverso_testkit.fita --days 1

O pipeline em memória (kernel, percepção, mente e guarda de orçamento), com a mente sobre a API de
verdade em modo `record`, por N dias simulados: o mesmo mundo, a mesma seed e os mesmos ids dos
testes, então a fita gravada reproduz o dia exatamente, em `replay`, sem rede. Ao fim, a fita
magra (o hash do pedido e a resposta, sem o corpo do pedido) vai para `--out`, e o próprio comando
a reproduz uma vez, para conferir. Custa uns centavos no Haiku 5.5; o CI nunca roda isto.
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
from campsverso_ports import ModelPort
from campsverso_testkit.nats_server import REPO
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
    assert pipeline.mind is not None
    return {
        "days": pipeline.core.tick // 1440,
        "calls": len(completed),
        "failed": len(failed),
        "charged": len(charged),
        "replayed": len(completed) - len(charged),
        "cost_usd": round(sum(float(c["cost_usd"]) for c in charged), 4),
        "tokens": dict(usage),
        "latency_ms_median": int(statistics.median(latencies)) if latencies else 0,
        "no_tool": pipeline.mind.no_tool,
        "reflections": pipeline.mind.reflections,
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
        "budget_notices": len(pipeline.of_type("ops.budget.threshold_reached.v1")),
        "budget_exceeded": len(pipeline.of_type("ops.budget.exceeded.v1")),
    }


async def run_days(days: int, port: ModelPort) -> dict[str, Any]:
    pipeline = Pipeline(controller="llm", port=port, budget=LIMITS)
    await pipeline.start()
    await pipeline.run_days(days)
    return summary(pipeline)


async def record(days: int, out: Path) -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY ausente: rode com --env-file .env (ADR-0058)", file=sys.stderr)
        return 2
    scratch = Path(tempfile.mkdtemp(prefix="campsverso-fita-")) / "gravacao.jsonl"
    clock = SystemWallClock()
    recorder = RecordingModel(AnthropicModel(clock=clock), scratch, "record", clock=clock)
    print(f"gravando {days} dia(s) com a API... (uma chamada por decisão)", flush=True)
    recorded = await run_days(days, recorder)
    print(json.dumps({"gravacao": recorded}, ensure_ascii=False, indent=2), flush=True)
    entries = slim(scratch, out)
    print(f"fita magra: {out} ({entries} chamadas)", flush=True)
    replayed = await run_days(days, RecordingModel(None, out, "replay"))
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
        "--out", type=Path, help="a fita magra (padrão: tests/fixtures/llm/camps-dia-N.jsonl)"
    )
    args = parser.parse_args(argv)
    out = args.out or FIXTURES / f"camps-dia-{args.days}.jsonl"
    return asyncio.run(record(args.days, out))


if __name__ == "__main__":
    sys.exit(main())
