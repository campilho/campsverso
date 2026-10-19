"""O relatório da arena (ADR-0061).

    uv run python -m campsverso_tools.arena [data/arena/<data-hora>] [--out docs/arena/DATA.md]

Lê as corridas de uma arena (uma pasta por controlador, com `summary.json` e `archive.jsonl`,
gravadas por `campsverso_testkit.arena`) e escreve o relatório em Markdown: a tabela da bíblia §13
lado a lado, quem descobriu o leste pelo dado da memória (a primeira anotação, a primeira crença e
a trajetória da confiança a cada reflexão) e pelo comportamento (plantios e colheitas no leste a
partir do dia 4), as moedas por dia em texto e os caminhos das fitas. Sem a pasta, usa a arena
mais recente de `data/arena/`.
"""

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, cast

from campsverso_tools.metrics import Report, compute

REPO = Path(__file__).resolve().parents[4]
ARENAS = REPO / "data" / "arena"
REPORTS = REPO / "docs" / "arena"
TICKS_PER_DAY = 1440
DAY_STARTS_AT = 6 * 60  # o dia simulado começa às 06:00
FROM_DAY = 4  # a partir de quando o comportamento conta como "depois de ter visto" (ADR-0061)
EAST = re.compile(r"\bleste\b|\bplot-e-\d+\b", re.IGNORECASE)
# O que faz de uma crença sobre o leste uma descoberta, e não só uma menção: fala de tempo, de
# vantagem ou do rio. É uma heurística; a trajetória inteira vai para o relatório, para quem ler.
DISCOVERY = re.compile(
    r"\b(2|dois) dias?\b|r[áa]pid|mais cedo|\bantes\b|melhor|\brio\b|madur|menos dias",
    re.IGNORECASE,
)
ORDER = (
    "script",
    "haiku",
    "haiku-memoria",
    "haiku-memoria-s2",
    "haiku-memoria-s3",
    "haiku-memoria-s4",
    "haiku-memoria-sem-regra",
)
BARS = "▁▂▃▄▅▆▇█"
EMPTY = "-"  # a célula de quem não tem a medida (o script não tem modelo)
FORMED = "campsverso.memory.belief.formed.v1"
UPDATED = "campsverso.memory.belief.updated.v1"
RETRACTED = "campsverso.memory.belief.retracted.v1"
NOTED = "campsverso.memory.noted.v1"
COMPLETED = "campsverso.action.completed.v1"


def _day(envelope: Mapping[str, Any]) -> int:
    return int(envelope.get("tick") or 0) // TICKS_PER_DAY + 1


def _hour(envelope: Mapping[str, Any]) -> str:
    simtime = str(envelope.get("simtime") or "")
    if "T" in simtime:
        return simtime.split("T")[1][:5]
    minutes = (DAY_STARTS_AT + int(envelope.get("tick") or 0)) % TICKS_PER_DAY
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _confidence(data: Mapping[str, Any]) -> float:
    value = data["confidence"]
    if isinstance(value, Mapping):
        return float(cast(Mapping[str, Any], value)["after"])
    return float(value)


@dataclass
class BeliefTrack:
    """Uma crença que fala do leste, da formação ao fim: cada reflexão que mexeu nela."""

    belief_id: str
    statement: str
    first_day: int
    steps: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    confidence: float = 0.0
    retracted_day: int | None = None


def _buckets(counters: Mapping[str, Counter[str]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for bucket, name in (("early", f"days_1_{FROM_DAY - 1}"), ("late", f"from_day_{FROM_DAY}")):
        counter = counters[bucket]
        total = sum(counter.values())
        out[name] = {
            "oeste": counter["oeste"],
            "leste": counter["leste"],
            "east_fraction": round(counter["leste"] / total, 2) if total else None,
        }
    return out


def east_signals(envelopes: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Os sinais do leste de uma corrida, lidos do arquivo dela na ordem em que foi escrito
    (ADR-0061, decisão 5): a primeira anotação e a primeira crença que falam do leste, a
    trajetória de cada crença sobre o leste, e os plantios e colheitas por grupo, antes e a
    partir do dia 4. `discovered` é a heurística: uma crença ativa, confiante (0,7 ou mais) e
    que fala de tempo, de vantagem ou do rio."""
    first_note: dict[str, Any] | None = None
    first_discovery_note: dict[str, Any] | None = None  # a primeira que nota a vantagem
    first_belief: dict[str, Any] | None = None
    tracks: dict[str, BeliefTrack] = {}
    plantings = {"early": Counter[str](), "late": Counter[str]()}
    harvests = {"early": Counter[str](), "late": Counter[str]()}
    for envelope in envelopes:
        kind = str(envelope.get("type", ""))
        data: Mapping[str, Any] = envelope.get("data", {})
        day = _day(envelope)
        if kind == NOTED:
            text = str(data["text"])
            if EAST.search(text):
                note = {"day": day, "hour": _hour(envelope), "text": text}
                if first_note is None:
                    first_note = note
                if first_discovery_note is None and DISCOVERY.search(text):
                    first_discovery_note = note
        elif kind in (FORMED, UPDATED):
            belief_id, statement = str(data["belief_id"]), str(data["statement"])
            track = tracks.get(belief_id)
            if track is None:
                if not EAST.search(statement):
                    continue
                track = tracks[belief_id] = BeliefTrack(belief_id, statement, day)
            confidence = _confidence(data)
            track.statement, track.confidence = statement, confidence
            track.steps.append(
                {
                    "day": day,
                    "kind": "formada" if kind == FORMED else "revisada",
                    "confidence": confidence,
                }
            )
            if first_belief is None:
                first_belief = {
                    "day": day,
                    "hour": _hour(envelope),
                    "belief_id": belief_id,
                    "statement": statement,
                    "confidence": confidence,
                }
        elif kind == RETRACTED:
            track = tracks.get(str(data["belief_id"]))
            if track is not None:
                track.confidence, track.retracted_day = 0.0, day
                track.steps.append({"day": day, "kind": "retirada", "confidence": 0.0})
        elif kind == COMPLETED and data.get("action") in ("plant", "harvest"):
            group = "leste" if str(data["params"]["target"]).startswith("plot-e-") else "oeste"
            bucket = "late" if day >= FROM_DAY else "early"
            (plantings if data["action"] == "plant" else harvests)[bucket][group] += 1
    active = [t for t in tracks.values() if t.retracted_day is None]
    discovery = [t for t in active if t.confidence >= 0.7 and DISCOVERY.search(t.statement)]
    best = max(discovery, key=lambda t: t.confidence, default=None)
    return {
        "first_note": first_note,
        "first_discovery_note": first_discovery_note,
        "first_belief": first_belief,
        "beliefs": [asdict(t) for t in tracks.values()],
        "plantings": _buckets(plantings),
        "harvests": _buckets(harvests),
        "discovered": best is not None,
        "discovered_by": best.belief_id if best is not None else None,
    }


def beliefs_at_end(envelopes: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """As crenças ativas ao fim da corrida, da mais confiante à menos, lidas dos eventos."""
    beliefs: dict[str, dict[str, Any]] = {}
    for envelope in envelopes:
        kind = str(envelope.get("type", ""))
        data: Mapping[str, Any] = envelope.get("data", {})
        if kind in (FORMED, UPDATED):
            beliefs[str(data["belief_id"])] = {
                "belief_id": str(data["belief_id"]),
                "statement": str(data["statement"]),
                "confidence": _confidence(data),
                "day": _day(envelope),
            }
        elif kind == RETRACTED:
            beliefs.pop(str(data["belief_id"]), None)
    return sorted(beliefs.values(), key=lambda b: (-float(b["confidence"]), str(b["belief_id"])))


@dataclass
class Run:
    """Uma corrida lida da pasta dela."""

    name: str
    folder: Path
    summary: dict[str, Any]
    report: Report
    east: dict[str, Any]
    beliefs: list[dict[str, Any]]

    @property
    def spec(self) -> dict[str, Any]:
        return dict(self.summary.get("spec", {}))

    @property
    def has_memory(self) -> bool:
        return bool(self.spec.get("memory"))

    @property
    def has_model(self) -> bool:
        return "llm" in self.report.totals()


def read_envelopes(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_run(folder: Path) -> Run:
    summary: dict[str, Any] = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    envelopes = read_envelopes(folder / "archive.jsonl")
    return Run(
        folder.name,
        folder,
        summary,
        compute(envelopes),
        east_signals(envelopes),
        beliefs_at_end(envelopes),
    )


def load_runs(folder: Path) -> list[Run]:
    runs = [load_run(sub) for sub in folder.iterdir() if (sub / "summary.json").exists()]
    return sorted(
        runs, key=lambda r: (ORDER.index(r.name) if r.name in ORDER else len(ORDER), r.name)
    )


def latest_arena(root: Path = ARENAS) -> Path | None:
    """A arena mais recente que já tem alguma corrida feita."""
    if not root.is_dir():
        return None
    arenas = [
        p
        for p in sorted(root.iterdir())
        if p.is_dir() and any((s / "summary.json").exists() for s in p.iterdir() if s.is_dir())
    ]
    return arenas[-1] if arenas else None


# ----------------------------------------------------------------------------- o relatório


def _n(value: Any, decimals: int = 0) -> str:
    if value is None:
        return EMPTY
    return f"{float(value):.{decimals}f}".replace(".", ",")


def _duration(seconds: float) -> str:
    whole = int(seconds)
    if whole >= 3600:
        return f"{whole // 3600} h {whole % 3600 // 60:02d} min"
    if whole >= 60:
        return f"{whole // 60} min {whole % 60:02d} s"
    return f"{whole} s"


def _frac(bucket: Mapping[str, Any]) -> str:
    total = int(bucket["oeste"]) + int(bucket["leste"])
    if total == 0:
        return EMPTY
    return f"{round(float(bucket['east_fraction']) * 100)}% ({bucket['leste']} de {total})"


def _table(header: Sequence[str], rows: Iterable[Sequence[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def _spark(values: Sequence[int], top: int) -> str:
    if top <= 0:
        return BARS[0] * len(values)
    return "".join(BARS[min(7, round(v / top * 7))] for v in values)


def _pair(mapping: Mapping[str, Any], decimals: int = 0) -> str:
    return f"{_n(mapping.get('oeste', 0), decimals)} / {_n(mapping.get('leste', 0), decimals)}"


def _bible_rows(runs: Sequence[Run]) -> list[list[str]]:
    rows: list[tuple[str, list[str]]] = []

    def row(label: str, cell: Callable[[Run], str]) -> None:
        rows.append((label, [cell(r) for r in runs]))

    def llm(r: Run, key: str, decimals: int = 0) -> str:
        return _n(r.report.totals()["llm"][key], decimals) if r.has_model else EMPTY

    def totals(r: Run) -> dict[str, Any]:
        return r.report.totals()

    row("Dias completos", lambda r: str(totals(r)["days"]))
    row("Moedas ao fim", lambda r: str(totals(r)["coins_end"]))
    row("Colheitas (oeste / leste)", lambda r: _pair(totals(r)["harvests"]))
    row("Plantios (oeste / leste)", lambda r: _pair(totals(r)["plantings"]))
    row(
        "Dias até amadurecer (oeste / leste)",
        lambda r: " / ".join(
            _n(totals(r)["mean_days_to_mature"].get(g), 1) for g in ("oeste", "leste")
        ),
    )
    row("Recusas", lambda r: str(sum(totals(r)["rejections"].values())))
    row("Murchas", lambda r: str(totals(r)["withered"]))
    row("Pico de fome", lambda r: _n(totals(r)["hunger_peak"]))
    row("Desmaios", lambda r: str(totals(r)["faints"]))
    row("Chamadas", lambda r: llm(r, "calls"))
    row(
        "Chamadas por dia",
        lambda r: (
            _n(totals(r)["llm"]["calls"] / max(1, totals(r)["days"]), 1) if r.has_model else EMPTY
        ),
    )
    row("Chamadas que falharam", lambda r: llm(r, "calls_failed"))
    row("Custo (US$)", lambda r: llm(r, "cost_usd", 2))
    row("Custo por dia (US$)", lambda r: llm(r, "cost_usd_per_day", 3))
    row("Latência mediana (ms)", lambda r: llm(r, "latency_ms_median"))
    row("Reflexões", lambda r: str(r.summary.get("reflections", 0)) if r.has_memory else EMPTY)
    row("Anotações", lambda r: str(r.summary.get("notes", 0)) if r.has_memory else EMPTY)
    row(
        "Crenças ao fim (formadas / revisadas / retiradas)",
        lambda r: (
            (
                f"{len(r.beliefs)} ({r.summary['beliefs']['formed']} / "
                f"{r.summary['beliefs']['updated']} / {r.summary['beliefs']['retracted']})"
            )
            if r.has_memory and "beliefs" in r.summary
            else EMPTY
        ),
    )
    row(
        "Desistiu (três falhas seguidas)",
        lambda r: (
            f"sim, no dia {r.summary['aborted_day']}" if r.summary.get("aborted_day") else "não"
        ),
    )
    row("Tempo real", lambda r: _duration(float(r.summary.get("real_seconds", 0))))
    return [[label, *cells] for label, cells in rows]


def _east_rows(runs: Sequence[Run]) -> list[list[str]]:
    def first_note(r: Run) -> str:
        note = r.east["first_note"]
        if not r.has_memory:
            return "sem memória"
        return f"dia {note['day']}, {note['hour']}" if note else "nunca"

    def discovery_note(r: Run) -> str:
        note = r.east.get("first_discovery_note")
        if not r.has_memory:
            return "sem memória"
        return f"dia {note['day']}, {note['hour']}" if note else "nunca"

    def first_belief(r: Run) -> str:
        belief = r.east["first_belief"]
        if not r.has_memory:
            return "sem memória"
        if not belief:
            return "nunca"
        return f"dia {belief['day']} ({belief['belief_id']}, {_n(belief['confidence'], 2)})"

    def at_end(r: Run) -> str:
        if not r.has_memory:
            return "sem memória"
        active = [b for b in r.east["beliefs"] if b["retracted_day"] is None]
        if not active:
            return "nenhuma"
        top = max(float(b["confidence"]) for b in active)
        return f"{len(active)}, a mais confiante a {_n(top, 2)}"

    def verdict(r: Run) -> str:
        control = " (controle: sem a regra)" if not r.spec.get("river_bonus", True) else ""
        if not r.has_memory:
            return "só pelo comportamento" + control
        if r.east["discovered"]:
            return f"descobriu ({r.east['discovered_by']})" + control
        return "não" + control

    rows: list[list[str]] = [
        ["Primeira anotação que cita o leste", *[first_note(r) for r in runs]],
        ["Primeira anotação que nota a vantagem do leste", *[discovery_note(r) for r in runs]],
        ["Primeira crença sobre o leste", *[first_belief(r) for r in runs]],
        ["Crenças sobre o leste ao fim", *[at_end(r) for r in runs]],
        [
            f"Plantios no leste, dias 1 a {FROM_DAY - 1}",
            *[_frac(r.east["plantings"][f"days_1_{FROM_DAY - 1}"]) for r in runs],
        ],
        [
            f"Plantios no leste, do dia {FROM_DAY}",
            *[_frac(r.east["plantings"][f"from_day_{FROM_DAY}"]) for r in runs],
        ],
        [
            f"Colheitas no leste, do dia {FROM_DAY}",
            *[_frac(r.east["harvests"][f"from_day_{FROM_DAY}"]) for r in runs],
        ],
        ["Veredito", *[verdict(r) for r in runs]],
    ]
    return rows


def _trajectory(track: Mapping[str, Any], last_day: int) -> str:
    steps = " → ".join(
        f"dia {s['day']} {s['kind']} {_n(s['confidence'], 2)}" for s in track["steps"]
    )
    if track["retracted_day"] is not None:
        span = f"dia {track['first_day']} a {track['retracted_day']}, retirada"
    else:
        span = f"dia {track['first_day']} a {last_day}, confiança {_n(track['confidence'], 2)}"
    return f'- **{track["belief_id"]}** ({span}): "{track["statement"]}". {steps}.'


def _by_day(run: Run) -> dict[int, Any]:
    return {d.day: d for d in run.report.complete_days}


def _series(runs: Sequence[Run], value: Callable[[Any], int]) -> tuple[dict[str, list[int]], int]:
    """Uma série por corrida, do dia 1 ao último dia completo de todas, com 0 nos dias sem
    fato (só acontece em testes); e o maior valor, para a escala das barras."""
    longest = max((d.day for r in runs for d in r.report.complete_days), default=0)
    series = {
        r.name: [
            value(_by_day(r)[day]) if day in _by_day(r) else 0 for day in range(1, longest + 1)
        ]
        for r in runs
    }
    top = max((max(v) for v in series.values() if v), default=0)
    return series, top


def _chart(series: Mapping[str, Sequence[int]], top: int) -> list[str]:
    width = max((len(name) for name in series), default=0)
    return [
        "```",
        *[f"{name:<{width}}  {_spark(values, top)}" for name, values in series.items()],
        "```",
    ]


def _harvests_section(runs: Sequence[Run]) -> list[str]:
    series, top = _series(runs, lambda d: int(d.harvests.get("leste", 0)))
    longest = max((len(v) for v in series.values()), default=0)
    lines = ["## Colheitas por dia", ""]
    lines.append(f"As colheitas no leste, de 0 a {top} por dia, um caractere por dia:")
    lines.append("")
    lines += _chart(series, top)
    lines += ["", "Oeste / leste, por dia:", ""]
    rows = [
        [
            str(day),
            *[_pair(_by_day(r)[day].harvests) if day in _by_day(r) else EMPTY for r in runs],
        ]
        for day in range(1, longest + 1)
    ]
    lines.append(_table(["Dia", *series.keys()], rows))
    lines.append("")
    return lines


def _coins_section(runs: Sequence[Run]) -> list[str]:
    series, top = _series(runs, lambda d: int(d.coins_end))
    longest = max((len(v) for v in series.values()), default=0)
    lines = ["## Moedas por dia", ""]
    lines.append(f"A barra vai de 0 a {top} moedas, um caractere por dia.")
    lines.append("")
    lines += _chart(series, top)
    lines.append("")
    rows = [
        [
            str(day),
            *[str(_by_day(r)[day].coins_end) if day in _by_day(r) else EMPTY for r in runs],
        ]
        for day in range(1, longest + 1)
    ]
    lines.append(_table(["Dia", *series.keys()], rows))
    lines.append("")
    return lines


def render(runs: Sequence[Run], *, source: str, date: str) -> str:
    """O relatório em Markdown, com as corridas lado a lado."""
    names = [r.name for r in runs]
    days = max((int(r.report.totals()["days"]) for r in runs), default=0)
    lines = [
        f"# Arena de {date}",
        "",
        f"{len(runs)} corrida(s) de até {days} dias em processo, no mesmo mundo (`farm-camps-01`), "
        "com o mundo esperando o modelo por construção (ADR-0061). Gerado por `make arena-report` "
        f"a partir de `{source}` (fora do git). A tabela da bíblia §13 é o total dos dias "
        'completos de cada corrida; "descobriu o leste" é lido do dado da memória de quem a '
        "tem (a primeira anotação e a primeira crença que falam do leste, e a trajetória de cada "
        "crença) e do comportamento de todos (plantios e colheitas no leste a partir do dia "
        f"{FROM_DAY}). A corrida sem a regra R-001 é o controle.",
        "",
        "## As corridas",
        "",
        _table(
            ["Corrida", "Controlador", "Memória", "Regra R-001", "Seed", "Dias", "Tempo real"],
            [
                [
                    r.name,
                    "Haiku 5.5"
                    if r.spec.get("controller") == "llm"
                    else str(r.spec.get("controller")),
                    "sim" if r.has_memory else "não",
                    "ligada" if r.spec.get("river_bonus", True) else "desligada",
                    str(r.spec.get("seed", "?")),
                    str(r.report.totals()["days"]),
                    _duration(float(r.summary.get("real_seconds", 0))),
                ]
                for r in runs
            ],
        ),
        "",
        "## A tabela da bíblia §13, lado a lado",
        "",
        _table(["Métrica", *names], _bible_rows(runs)),
        "",
        "### Recusas por motivo",
        "",
    ]
    reasons = sorted({k for r in runs for k in r.report.totals()["rejections"]})
    lines.append(
        _table(
            ["Motivo", *names],
            [
                [reason, *[str(r.report.totals()["rejections"].get(reason, 0)) for r in runs]]
                for reason in reasons
            ],
        )
    )
    lines += ["", "## Quem descobriu o leste", "", _table(["Sinal", *names], _east_rows(runs)), ""]
    for r in runs:
        if not r.has_memory:
            continue
        last_day = int(r.report.totals()["days"])
        lines += [f"### {r.name}: as crenças sobre o leste", ""]
        tracks = list(r.east["beliefs"])
        lines += [_trajectory(t, last_day) for t in tracks] or ["Nenhuma crença falou do leste."]
        lines += ["", f"As crenças mais confiantes ao fim ({len(r.beliefs)} ativas):", ""]
        lines += [
            f'- {_n(b["confidence"], 2)} **{b["belief_id"]}** (dia {b["day"]}): "{b["statement"]}"'
            for b in r.beliefs[:3]
        ] or ["- nenhuma"]
        lines.append("")
    lines += _coins_section(runs)
    lines += _harvests_section(runs)
    lines += ["## Os arquivos", ""]
    for r in runs:
        files = ", ".join(f"`{p.name}`" for p in sorted(r.folder.iterdir()) if p.is_file())
        lines.append(f"- **{r.name}**: `{source}/{r.name}/` com {files}")
    return "\n".join(lines) + "\n"


def _date_of(folder: Path) -> str:
    match = re.match(r"(\d{4})(\d{2})(\d{2})", folder.name)
    return f"{match[1]}-{match[2]}-{match[3]}" if match else folder.name


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.arena")
    parser.add_argument(
        "folder",
        nargs="?",
        type=Path,
        help="a arena, em data/arena/<data-hora> (padrão: a mais recente com corridas feitas)",
    )
    parser.add_argument(
        "--out", type=Path, help="o relatório (padrão: docs/arena/DATA.md, pela data da arena)"
    )
    args = parser.parse_args(argv)
    folder: Path | None = args.folder or latest_arena()
    if folder is None or not folder.is_dir():
        print("nenhuma arena em data/arena/: rode make arena", file=sys.stderr)
        return 2
    runs = load_runs(folder)
    if not runs:
        print(f"nenhuma corrida feita em {folder}", file=sys.stderr)
        return 2
    date = _date_of(folder)
    out: Path = args.out or REPORTS / f"{date}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        source = str(folder.resolve().relative_to(REPO))
    except ValueError:
        source = str(folder)
    out.write_text(render(runs, source=source, date=date), encoding="utf-8")
    print(f"{out}: {len(runs)} corrida(s) de {folder}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
