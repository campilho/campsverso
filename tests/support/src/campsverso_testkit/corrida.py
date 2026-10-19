"""Uma corrida de N dias em processo (ADR-0060; base da arena do M12).

    uv run --env-file .env python -m campsverso_testkit.corrida --days 7 [--sem-memoria]

O pipeline em memória (kernel, percepção, mente, medidor e guarda), com a mente sobre a API de
verdade: o mundo espera cada resposta, então um dia leva o tempo das chamadas (uns 90 s), não os
20 minutos de 72x. Ao fim, na pasta: `summary.json` (o que o Camps fez e quanto custou), a fita
inteira (`llm.jsonl`, com os pedidos), a memória (`memory.sqlite`) e `metrics.txt` (a tabela da
bíblia §13 com as colunas do modelo). Mesmo mundo e mesma seed dos testes. O CI nunca roda isto.
"""

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from campsverso_adapters import AnthropicModel, RecordingModel, SqliteMemory, SystemWallClock
from campsverso_testkit.fita import LIMITS, summary
from campsverso_testkit.nats_server import REPO
from campsverso_testkit.pipeline import Pipeline
from campsverso_tools.metrics import compute, table


async def run(days: int, out: Path, *, memory: bool) -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY ausente: rode com --env-file .env (ADR-0058)", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    clock = SystemWallClock()
    port = RecordingModel(AnthropicModel(clock=clock), out / "llm.jsonl", "record", clock=clock)
    notebook = SqliteMemory(out / "memory.sqlite") if memory else False
    pipeline = Pipeline(controller="llm", port=port, budget=LIMITS, memory=notebook)
    started = datetime.now(UTC)
    print(
        f"corrida de {days} dia(s), memória {'ligada' if memory else 'desligada'}, em {out}",
        flush=True,
    )
    await pipeline.start()
    for day in range(1, days + 1):
        await pipeline.run_days(1)
        partial = summary(pipeline)
        print(
            f"dia {day}: {partial['calls']} chamadas, US$ {partial['cost_usd']:.4f}, "
            f"recusas {sum(partial['rejected'].values())}, desmaios {partial['faints']}, "
            f"fome {partial['needs'].get('fome', 0):.0f}",
            flush=True,
        )
    report = compute(pipeline.envelopes)
    result = {
        **summary(pipeline),
        "memory": memory,
        "real_seconds": round((datetime.now(UTC) - started).total_seconds(), 1),
        "totals": report.totals(),
    }
    (out / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "metrics.txt").write_text(table(report) + "\n", encoding="utf-8")
    (out / "archive.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in pipeline.envelopes),
        encoding="utf-8",
    )
    print(table(report), flush=True)
    print(json.dumps(result["totals"], ensure_ascii=False), flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.corrida")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--sem-memoria", action="store_true", help="a mente do M10, sem caderno")
    parser.add_argument(
        "--out", type=Path, help="pasta da corrida (padrão: data/corridas/<data-hora>)"
    )
    args = parser.parse_args(argv)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out = (
        args.out
        or REPO / "data" / "corridas" / f"{stamp}-{'sem' if args.sem_memoria else 'com'}-memoria"
    )
    return asyncio.run(run(args.days, out, memory=not args.sem_memoria))


if __name__ == "__main__":
    sys.exit(main())
