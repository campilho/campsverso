"""Uma rodada sintética da arena para o teste da página da arena no navegador (ADR-0068).

    uv run python -m campsverso_testkit.assistir --out data/sandbox/e2e-arena --port 8797

Grava duas corridas de um dia da fazenda 1 com o fazendeiro-script, em processo (sem NATS): uma
terminada (`gravada`) e uma pela metade (`ao vivo`, o arquivo ainda sem o fim). Depois vira o
gateway no modo de assistir sobre a pasta, na porta pedida, até receber o SIGTERM.
"""

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from campsverso_testkit.pipeline import Pipeline


async def _day() -> list[dict[str, Any]]:
    pipeline = Pipeline()
    await pipeline.start()
    await pipeline.run_days(1)
    return [dict(e) for e in pipeline.envelopes]


def _write(folder: Path, envelopes: Sequence[dict[str, Any]], *, done: bool) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "archive.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in envelopes), encoding="utf-8"
    )
    state = {"name": folder.name, "day": 1, "done": done, "events": len(envelopes)}
    (folder / "estado.json").write_text(json.dumps(state), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="pasta da rodada sintética")
    parser.add_argument("--port", type=int, required=True, help="porta do gateway")
    args = parser.parse_args(argv)
    envelopes = asyncio.run(_day())
    _write(args.out / "script-gravada", envelopes, done=True)
    _write(args.out / "script-ao-vivo", envelopes[: len(envelopes) // 2], done=False)
    command = [sys.executable, "-m", "campsverso_gateway.main", "--watch", str(args.out)]
    os.execv(sys.executable, [*command, "--port", str(args.port)])


if __name__ == "__main__":
    sys.exit(main())
