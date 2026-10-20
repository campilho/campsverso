"""A arena (ADR-0061): as corridas de 30 dias em processo, uma por controlador, lado a lado.

    uv run --env-file .env python -m campsverso_testkit.arena --days 30 [--only NOME] [--out PASTA]

Sobre o `make corrida` do M11: o pipeline em memória (kernel, percepção, mente, medidor e guarda),
com o mundo esperando cada resposta por construção. As corridas rodam em sequência, cada uma na
sua pasta: o script da bíblia §11, o Haiku 5.5 sem memória (M10), o Haiku 5.5 com memória (M11)
em quatro seeds e o Haiku 5.5 com memória sem a regra R-001, como controle. Uma pasta com
`summary.json` é uma corrida feita: rodar de novo só completa as que faltam. Depois,
`make arena-report` escreve o relatório. O CI nunca roda isto.
"""

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from campsverso_adapters import AnthropicModel, RecordingModel, SqliteMemory, SystemWallClock
from campsverso_ports import MemoryPort, ModelPort
from campsverso_testkit.fita import LIMITS, summary
from campsverso_testkit.nats_server import REPO
from campsverso_testkit.pipeline import Pipeline
from campsverso_tools.arena import east_signals
from campsverso_tools.metrics import compute, table

SEED = 20261010  # o mesmo dos testes e do mundo oficial


@dataclass(frozen=True)
class Spec:
    """Uma corrida: quem controla o Camps, com que memória, com ou sem a regra, em que seed."""

    name: str
    controller: Literal["script", "llm"]
    memory: bool = False
    river_bonus: bool = True
    seed: int = SEED


SPECS: tuple[Spec, ...] = (
    Spec("script", "script"),
    Spec("haiku", "llm"),
    Spec("haiku-memoria", "llm", memory=True),
    Spec("haiku-memoria-s2", "llm", memory=True, seed=SEED + 1),
    Spec("haiku-memoria-s3", "llm", memory=True, seed=SEED + 2),
    Spec("haiku-memoria-s4", "llm", memory=True, seed=SEED + 3),
    Spec("haiku-memoria-sem-regra", "llm", memory=True, river_bonus=False),
)


def _say(line: str, log: Path) -> None:
    print(line, flush=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


async def run_spec(spec: Spec, days: int, out: Path) -> dict[str, Any]:
    """Roda uma corrida e grava a pasta dela: `summary.json` (o resumo, o `spec`, os totais da
    bíblia e os sinais do leste), `metrics.txt`, `archive.jsonl` e, com modelo, `llm.jsonl` (a
    fita inteira) e `memory.sqlite`. Devolve o resumo. Se a mente desistir (três falhas seguidas),
    a corrida para no dia em que isso aconteceu, marcado em `aborted_day`."""
    out.mkdir(parents=True, exist_ok=True)
    log = out / "progresso.txt"
    clock = SystemWallClock()
    port: ModelPort | None = None
    api: AnthropicModel | None = None
    notebook: MemoryPort | bool = False
    if spec.controller == "llm":
        api = AnthropicModel(clock=clock)
        port = RecordingModel(api, out / "llm.jsonl", "record", clock=clock)
        notebook = SqliteMemory(out / "memory.sqlite") if spec.memory else False
    pipeline = Pipeline(
        spec.seed,
        controller=spec.controller,
        river_bonus=spec.river_bonus,
        port=port,
        budget=LIMITS if port is not None else None,
        memory=notebook,
    )
    started = datetime.now(UTC)
    _say(
        f"{spec.name}: {days} dia(s), {spec.controller}, memória "
        f"{'ligada' if spec.memory else 'desligada'}, regra "
        f"{'ligada' if spec.river_bonus else 'desligada'}, seed {spec.seed}, em {out}",
        log,
    )
    await pipeline.start()
    aborted: int | None = None
    for day in range(1, days + 1):
        await pipeline.run_days(1)
        partial = summary(pipeline)
        elapsed = (datetime.now(UTC) - started).total_seconds()
        _say(
            f"{spec.name} dia {day}: {partial['calls']} chamadas, US$ {partial['cost_usd']:.4f}, "
            f"recusas {sum(partial['rejected'].values())}, desmaios {partial['faints']}, "
            f"fome {partial['needs'].get('fome', 0):.0f}, {elapsed:.0f} s",
            log,
        )
        if partial["gave_up"]:
            aborted = day
            _say(f"{spec.name}: a mente desistiu no dia {day}; a corrida para aqui", log)
            break
    if api is not None:
        await api.aclose()  # antes de o laço desta corrida fechar
    report = compute(pipeline.envelopes)
    result: dict[str, Any] = {
        "spec": asdict(spec),
        **summary(pipeline),
        "aborted_day": aborted,
        "real_seconds": round((datetime.now(UTC) - started).total_seconds(), 1),
        "totals": report.totals(),
        "east": east_signals(pipeline.envelopes),
    }
    (out / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "metrics.txt").write_text(table(report) + "\n", encoding="utf-8")
    (out / "archive.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False) + "\n" for e in pipeline.envelopes),
        encoding="utf-8",
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.arena")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument(
        "--only",
        action="append",
        choices=[s.name for s in SPECS],
        help="só esta corrida (repetível); sem isto, todas, em sequência",
    )
    parser.add_argument(
        "--out", type=Path, help="a pasta da arena (padrão: data/arena/<data-hora>)"
    )
    args = parser.parse_args(argv)
    only: list[str] = list(args.only or [])
    specs = [s for s in SPECS if not only or s.name in only]
    if any(s.controller == "llm" for s in specs) and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY ausente: rode com --env-file .env (ADR-0058)", file=sys.stderr)
        return 2
    out: Path = args.out or REPO / "data" / "arena" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    for spec in specs:
        folder = out / spec.name
        if (folder / "summary.json").exists():
            print(f"{spec.name}: feita, pulando ({folder})", flush=True)
            continue
        result = asyncio.run(run_spec(spec, args.days, folder))
        totals = result["totals"]
        print(
            f"{spec.name}: {totals['days']} dias, moedas {totals['coins_end']}, "
            f"colheitas {totals['harvests']}, desmaios {totals['faints']}, "
            f"custo US$ {totals.get('llm', {}).get('cost_usd', 0):.2f}, "
            f"leste {'descoberto' if result['east']['discovered'] else 'não descoberto'}",
            flush=True,
        )
    print(f"relatório: make arena-report PASTA={out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
