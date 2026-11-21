"""A calibração do revisor de outra família (ADR-0083, parte 3 do M25; plano do M25, §2).

    uv run --env-file .env python -m campsverso_tools.revisor calibrar [--model M] [--teto 1.0]
    uv run python -m campsverso_tools.revisor relatorio

Os casos ficam em `tests/fixtures/revisor/casos.yaml`: três entregas do escritório com um defeito
plantado e o gêmeo limpo de uma delas. Cada modelo lê cada caso uma vez, com o mesmo pedido que o
publicador faria (as regras do `CLAUDE.md` e a constituição), pela porta de modelo e numa fita
(`data/revisor/calibracao.jsonl`): rodar de novo responde de graça. As respostas vão para
`tests/fixtures/revisor/calibracao.json`, que os testes do revisor leem sem chamar nada, e
`relatorio` escreve `docs/arena/revisor-calibracao.md` a partir delas.

**A conta:** um achado grave ou médio que cita um dos arquivos do defeito acha o defeito; um
grave ou médio que não cita nenhum é um achado a mais, que quem lê o relatório confere à mão (pode
ser um defeito de verdade que o gabarito não previu). No caso limpo, todo achado grave ou médio é
a mais. Fica o modelo que acha os defeitos sem inventar outros (o plano, §2).
"""

import argparse
import asyncio
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_adapters import RecordingModel, SystemWallClock, load_env, model_port
from campsverso_adapters.workshop_review import CONSTITUTION
from campsverso_codehost.reviewer import Reviewer, ReviewInput, findings_of, guide_from

REPO = Path(__file__).resolve().parents[4]
CASES = REPO / "tests" / "fixtures" / "revisor" / "casos.yaml"
RESULTS = REPO / "tests" / "fixtures" / "revisor" / "calibracao.json"
TAPE = REPO / "data" / "revisor" / "calibracao.jsonl"
REPORT = REPO / "docs" / "arena" / "revisor-calibracao.md"
ENV = REPO / "config" / "env" / "local.yaml"
MODELS = ("google/gemini-4-neon", "openai/gpt-6.2-astra")
SERIOUS = ("grave", "média")
GUESS_USD = 0.15  # a estimativa de uma chamada antes da primeira resposta, para o teto


@dataclass(frozen=True)
class Case:
    name: str
    number: int
    title: str
    description: str
    acceptance: str
    diff: str
    files: tuple[str, ...]  # os arquivos do defeito; vazio no caso limpo
    what: str

    def item(self) -> ReviewInput:
        head = hashlib.sha1(self.diff.encode()).hexdigest()
        return ReviewInput(
            self.number, self.title, self.description, self.acceptance, self.diff, head
        )


def load_notes(path: Path = CASES) -> list[str]:
    """A leitura à mão dos achados a mais, que o relatório copia."""
    raw = cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))
    return [str(n).strip() for n in cast(list[Any], raw.get("notes") or [])]


def load_cases(path: Path = CASES) -> list[Case]:
    raw = cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))
    found: list[Case] = []
    for entry in cast(list[Mapping[str, Any]], raw["cases"]):
        defect = cast(Mapping[str, Any] | None, entry.get("defect"))
        found.append(
            Case(
                name=str(entry["name"]),
                number=int(entry["number"]),
                title=str(entry["title"]),
                description=str(entry.get("description") or ""),
                acceptance=str(entry.get("acceptance") or ""),
                diff=(path.parent / str(entry["diff"])).read_text(encoding="utf-8"),
                files=tuple(str(f) for f in cast(list[Any], (defect or {}).get("files") or [])),
                what=str((defect or {}).get("what") or ""),
            )
        )
    return found


def _cites(line: str, files: Sequence[str]) -> bool:
    return any(f in line or Path(f).name in line for f in files)


def score(case: Case, body: str) -> tuple[bool | None, int]:
    """Achou o defeito (None no caso limpo) e quantos achados graves ou médios são a mais."""
    serious = [line for severity, line in findings_of(body) if severity in SERIOUS]
    hit = any(_cites(line, case.files) for line in serious) if case.files else None
    extra = sum(1 for line in serious if not case.files or not _cites(line, case.files))
    return hit, extra


def guide() -> str:
    return guide_from((REPO / "CLAUDE.md").read_text(encoding="utf-8"))


async def calibrate(models: Sequence[str], cases: Sequence[Case], ceiling: float) -> float:
    """Roda os casos em cada modelo, na fita; para antes de passar do teto. Devolve o gasto."""
    env, clock = load_env(ENV), SystemWallClock()
    rules = guide()
    saved = _load()
    done = {(r["model"], r["case"]) for r in saved["results"] if "raw" in r}
    spent, guess = 0.0, GUESS_USD
    for model in models:
        inner = model_port(model, routes=env.routes, clock=clock)
        port = RecordingModel(inner, TAPE, "record", clock=clock)
        reviewer = Reviewer({model: port}.__getitem__, [model], rules, CONSTITUTION)
        try:
            for case in cases:
                if (model, case.name) in done:
                    continue
                if spent + guess > ceiling:
                    print(f"teto de US$ {ceiling:.2f}: parei antes de {model} em {case.name}")
                    return spent
                review = await reviewer.review(case.item())
                entry: dict[str, Any] = {"case": case.name, "model": model}
                if review is None:
                    entry["error"] = "sem resposta"
                else:
                    hit, extra = score(case, review.text)
                    cost = review.cost_usd or 0.0
                    spent += 0.0 if review.replayed else cost
                    guess = max(guess, cost)
                    entry |= {
                        "verdict": review.verdict,
                        "raw": review.raw,
                        "findings": review.findings,
                        "severities": [s for s, _ in findings_of(review.text)],
                        "hit": hit,
                        "extra": extra,
                        "cost_usd": cost,
                        "replayed": review.replayed,
                        "served_by": review.served_by,
                        "prompt_sha256": review.prompt_sha256,
                    }
                saved["results"] = [
                    r for r in saved["results"] if (r["model"], r["case"]) != (model, case.name)
                ] + [entry]
                saved["date"] = datetime.now(UTC).isoformat(timespec="seconds")
                saved["guide_sha256"] = hashlib.sha256(rules.encode()).hexdigest()
                _store(saved)
                print(
                    f"{model} · {case.name}: {entry.get('verdict')} · "
                    f"achou={entry.get('hit')} · a mais={entry.get('extra')} · "
                    f"US$ {entry.get('cost_usd', 0):.4f}"
                )
        finally:
            await inner.aclose()
    return spent


def _load() -> dict[str, Any]:
    if RESULTS.is_file():
        return cast(dict[str, Any], json.loads(RESULTS.read_text(encoding="utf-8")))
    return {"results": []}


def _store(saved: Mapping[str, Any]) -> None:
    order = {name: i for i, name in enumerate(c.name for c in load_cases())}
    results = sorted(
        cast(list[dict[str, Any]], saved["results"]),
        key=lambda r: (str(r["model"]), order.get(str(r["case"]), 99)),
    )
    RESULTS.write_text(
        json.dumps({**saved, "results": results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _mark(value: bool | None) -> str:
    return "—" if value is None else ("sim" if value else "**não**")


def render(saved: Mapping[str, Any], cases: Sequence[Case], notes: Sequence[str] = ()) -> str:
    """O relatório da calibração: a tabela por modelo e as revisões inteiras."""
    results = cast(list[Mapping[str, Any]], saved.get("results") or [])
    by_case = {c.name: c for c in cases}
    models = sorted({str(r["model"]) for r in results}, key=lambda m: (m not in MODELS, m))
    lines = [
        "# A calibração do revisor de outra família",
        "",
        "Gerado por `make revisor-calibrar` (ADR-0083, parte 3 do M25) a partir de "
        "`tests/fixtures/revisor/calibracao.json`; os casos estão em "
        "`tests/fixtures/revisor/casos.yaml`.",
        "",
        f"Rodada de {str(saved.get('date', ''))[:10]}. Cada modelo leu cada entrega uma vez, com "
        "o pedido que o publicador faz: as regras do `CLAUDE.md`, a constituição e o diff, sem "
        "ferramentas, com esforço médio.",
        "",
        "Um achado grave ou médio que cita um arquivo do defeito *acha* o defeito; um grave ou "
        "médio que não cita nenhum fica *a mais* e é conferido à mão abaixo. No caso limpo, todo "
        "achado grave ou médio é a mais.",
        "",
        "| caso | gabarito | " + " | ".join(f"`{m}`" for m in models) + " |",
        "|---|---|" + "---|" * len(models),
    ]
    for case in cases:
        cells: list[str] = []
        for model in models:
            found = next(
                (r for r in results if r["model"] == model and r["case"] == case.name), None
            )
            if found is None:
                cells.append("não rodou")
            elif "error" in found:
                cells.append(str(found["error"]))
            else:
                cells.append(
                    f"{found['verdict'] or 'sem veredito'} · achou {_mark(found['hit'])} · "
                    f"a mais {found['extra']}"
                )
        expected = "devolver" if case.files else "mesclar"
        lines.append(f"| {case.name} | {expected} | " + " | ".join(cells) + " |")
    lines += ["", "| modelo | achou | a mais | vereditos certos | custo |", "|---|---|---|---|---|"]
    for model in models:
        mine = [r for r in results if r["model"] == model and "raw" in r]
        planted = [r for r in mine if by_case[str(r["case"])].files]
        hits = sum(1 for r in planted if r["hit"])
        extra = sum(int(r["extra"]) for r in mine)
        right = sum(
            1
            for r in mine
            if r["verdict"] == ("devolver" if by_case[str(r["case"])].files else "mesclar")
        )
        cost = sum(float(r.get("cost_usd") or 0) for r in mine)
        lines.append(
            f"| `{model}` | {hits} de {len(planted)} | {extra} | {right} de {len(mine)} | "
            f"US$ {cost:.3f} |"
        )
    if notes:
        lines += ["", "## A leitura à mão", ""]
        lines += [f"- {note}" for note in notes]
    lines += ["", "## O gabarito", ""]
    for case in cases:
        lines.append(f"- **{case.name}:** {case.what or 'nenhum defeito: o gêmeo limpo.'}")
    lines += ["", "## As revisões", ""]
    for case in cases:
        for model in models:
            found = next(
                (r for r in results if r["model"] == model and r["case"] == case.name), None
            )
            if found is None or "raw" not in found:
                continue
            lines += [
                "<details>",
                f"<summary>{case.name} · {model} · {found['verdict']}</summary>",
                "",
                str(found["raw"]).strip(),
                "",
                "</details>",
                "",
            ]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.revisor")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("calibrar", help="roda os casos nos modelos (chama a API)")
    run.add_argument("--model", action="append", help="um modelo; sem ele, os dois do plano")
    run.add_argument("--case", action="append", help="um caso; sem ele, todos")
    run.add_argument("--teto", type=float, default=1.0, help="o teto da rodada, em dólares")
    sub.add_parser("relatorio", help="escreve o relatório a partir das respostas gravadas")
    args = parser.parse_args(argv)
    cases = load_cases()
    if args.command == "calibrar":
        chosen = [c for c in cases if not args.case or c.name in args.case]
        TAPE.parent.mkdir(parents=True, exist_ok=True)
        spent = asyncio.run(calibrate(args.model or MODELS, chosen, args.teto))
        print(f"gasto nesta rodada: US$ {spent:.4f}")
    REPORT.write_text(render(_load(), cases, load_notes()), encoding="utf-8")
    print(f"relatório em {REPORT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
