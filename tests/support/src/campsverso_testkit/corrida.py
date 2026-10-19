"""Uma corrida de N dias em processo (ADR-0060; a unidade da arena do M12, ADR-0061).

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

from campsverso_testkit.arena import Spec, run_spec
from campsverso_testkit.nats_server import REPO


async def run(days: int, out: Path, *, memory: bool) -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY ausente: rode com --env-file .env (ADR-0058)", file=sys.stderr)
        return 2
    result = await run_spec(Spec("corrida", "llm", memory=memory), days, out)
    print((out / "metrics.txt").read_text(encoding="utf-8"), flush=True)
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
