"""A partida de um humano no sandbox como mais uma corrida da arena (ADR-0066).

    make arena-humano SANDBOX=data/sandbox/<pasta> [PASTA=data/arena/<rodada>] [NOME=humano]

Junta os arquivos de dia do mundo do sandbox (`<sandbox>/archive/<mundo>/`) num `archive.jsonl` e
escreve o `summary.json` que o relatório lê, numa pasta nova da rodada. Depois,
`make arena-report PASTA=<rodada>` põe o humano ao lado das corridas. A pasta do humano nunca é
sobrescrita: uma segunda partida entra com outro `NOME`.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from campsverso_tools.arena import latest_arena
from campsverso_tools.metrics import compute, read_archive

POSSESSED = "campsverso.avatar.possessed.v1"


def _seconds(envelopes: Sequence[dict[str, Any]]) -> float:
    """O tempo de relógio entre o primeiro e o último evento: a partida inteira, com as pausas."""
    times = [datetime.fromisoformat(str(e["time"])) for e in envelopes if e.get("time")]
    return (max(times) - min(times)).total_seconds() if times else 0.0


def _human_from(envelopes: Sequence[dict[str, Any]]) -> int | None:
    """O tick em que um humano assumiu o avatar pela primeira vez; antes dele, jogou o script."""
    for e in envelopes:
        if e.get("type") == POSSESSED and e["data"].get("controller", {}).get("type") == "human":
            return int(e.get("tick", 0))
    return None


def import_sandbox(sandbox: Path, arena: Path, name: str = "humano") -> Path:
    """Copia a partida do sandbox para `<arena>/<name>`, com o arquivo e o resumo da corrida."""
    world: dict[str, Any] = yaml.safe_load((sandbox / "world.yaml").read_text(encoding="utf-8"))
    folder = sandbox / "archive" / str(world["worldid"])
    envelopes = list(read_archive(folder))
    if not envelopes:
        raise ValueError(f"nenhum evento em {folder}")
    out = arena / name
    out.mkdir(parents=True)  # já existir é erro: a partida de outra noite não se apaga
    report = compute(envelopes)
    summary = {
        "spec": {
            "name": name,
            "controller": "human",
            "memory": False,
            "river_bonus": world.get("rules_file") is None,
            "seed": world.get("seed"),
            "cartridge": world.get("cartridge"),
            "days": len(report.complete_days),
            "limits": None,
        },
        "days": len(report.complete_days),
        "calls": 0,
        "cost_usd": 0,
        "real_seconds": _seconds(envelopes),
        "gave_up": False,
        "aborted_day": None,
        "budget_day": None,
        "human_from_tick": _human_from(envelopes),
        "sandbox": str(sandbox),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "archive.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in envelopes), encoding="utf-8"
    )
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.arena_humano")
    parser.add_argument("sandbox", type=Path, help="a pasta do sandbox em que o humano jogou")
    parser.add_argument("--arena", type=Path, help="a rodada (padrão: a arena mais recente)")
    parser.add_argument("--name", default="humano", help="o nome da corrida na rodada")
    args = parser.parse_args(argv)
    arena = args.arena or latest_arena()
    if arena is None:
        print("nenhuma arena em data/arena; passe PASTA=", file=sys.stderr)
        return 2
    try:
        out = import_sandbox(args.sandbox, arena, args.name)
    except (FileNotFoundError, FileExistsError, ValueError) as error:
        print(f"não importado: {error}", file=sys.stderr)
        return 2
    print(f"a partida está em {out}; o relatório: make arena-report PASTA={arena}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
