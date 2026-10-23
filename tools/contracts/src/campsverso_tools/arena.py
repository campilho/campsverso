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

from campsverso_tools.metrics import Report, compute, group_of, plot_groups

REPO = Path(__file__).resolve().parents[4]
ARENAS = REPO / "data" / "arena"
REPORTS = REPO / "docs" / "arena"
TICKS_PER_DAY = 1440
DAY_STARTS_AT = 6 * 60  # o dia simulado começa às 06:00
FROM_DAY = 4  # a partir de quando o comportamento conta como "depois de ter visto" (ADR-0061)
EAST = re.compile(r"\bleste\b|\bplot-e-\d+\b", re.IGNORECASE)
# Na Boa Vista não há "leste" nos ids: a descoberta é falar do rio, da beira dele ou do lado leste.
# "Margem" sozinha não conta: na arena do M14 era a margem de lucro do tomate.
RIVER = re.compile(r"\brio\b|margem do rio|beira do rio|perto da [áa]gua|\bleste\b", re.IGNORECASE)
# As outras regras ocultas da Boa Vista (bíblia 2 §10): o assunto e o efeito, no mesmo trecho. Os
# efeitos são estreitos de propósito: "regado todo dia, o tomate amadurece em 4" não é a murcha,
# e "guardar comida no baú" não é o baú que conserva (arena do M14).
RULES: dict[str, tuple[re.Pattern[str], re.Pattern[str]]] = {
    "tomate": (
        re.compile(r"\btomate", re.IGNORECASE),
        re.compile(r"murch|\bsec[oa]s?\b|sem (água|rega)|um dia sem", re.IGNORECASE),
    ),
    "alho": (
        re.compile(r"\balho", re.IGNORECASE),
        re.compile(
            r"sem (rega|água)|n[ãa]o precisa|dispensa|n[ãa]o regar|cresce(u)? sem|sozinho",
            re.IGNORECASE,
        ),
    ),
    "bau": (
        re.compile(r"\bba[úu]\b", re.IGNORECASE),
        re.compile(
            r"conserva|dura(m)? mais|estraga(m)? menos|demora(m)? (mais )?a estragar"
            r"|n[ãa]o estraga|vence(m)? (mais tarde|depois)",
            re.IGNORECASE,
        ),
    ),
    "ensopado": (
        re.compile(r"\bensopado", re.IGNORECASE),
        re.compile(
            r"sacia|segura a fome|fome (sobe|cresce) (mais )?devagar|dura mais|mais tempo",
            re.IGNORECASE,
        ),
    ),
    "adubo": (
        re.compile(r"\badub", re.IGNORECASE),
        re.compile(
            r"cresce(m|u)? (mais|melhor)|mais r[áa]pid|b[ôo]nus|acelera|rende(m)? mais",
            re.IGNORECASE,
        ),
    ),
}
WORLDS = {
    "farm_camps": "farm-camps-01",
    "farm_boavista": "farm-boavista-01",
    "farm_morada_do_sol": "farm-morada-do-sol-01",
}
MODEL_NAMES = {
    "claude-haiku-5-5": "Haiku 5.5",
    "claude-sonnet-5-5": "Sonnet 5.5",
    "claude-opus-5-5": "Opus 5.5",
}
# O que faz de uma crença (ou anotação) sobre o leste uma descoberta, e não só uma menção: um
# comparativo de tempo ou de vantagem, ou o rio. "Madura em 3 dias" não conta: é o manual. É uma
# heurística; a trajetória inteira vai para o relatório, para quem quiser discordar.
DISCOVERY = re.compile(
    r"\b(2|dois) dias?\b|r[áa]pid|mais cedo|mais depressa|menos dias|antes (do|que o) oeste"
    r"|melhor|\brio\b|cresce(m)? mais|rende(m)? mais",
    re.IGNORECASE,
)
ORDER = (
    "script",
    "script2",
    "humano",
    "haiku",
    "haiku-memoria",
    "haiku-memoria-s2",
    "haiku-memoria-s3",
    "haiku-memoria-s4",
    "haiku-memoria-sem-regra",
    "sonnet-memoria",
    "opus-memoria",
)
SPAWNED = "campsverso.world.entity.spawned.v1"
WITHERED = "campsverso.farm.crop.withered.v1"
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


SEGMENTS = re.compile(r"[.;:!?\n]")


def notes_east_advantage(text: str, mention: re.Pattern[str] = EAST) -> bool:
    """Verdadeiro quando o trecho que fala do lugar (entre pontos, dois-pontos ou ponto e
    vírgula) também fala de tempo, de vantagem ou do rio. "Abóbora no leste; rabanete para
    comida rápida" não conta: a rapidez é do rabanete. `mention` é o que conta como falar do
    lugar: o leste na fazenda 1, o rio na Boa Vista."""
    return any(mention.search(part) and DISCOVERY.search(part) for part in SEGMENTS.split(text))


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
    first_statement: str = ""  # como a crença foi escrita quando falou do leste pela primeira vez
    steps: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    confidence: float = 0.0
    retracted_day: int | None = None


def _buckets(
    counters: Mapping[str, Counter[str]], groups: tuple[str, str], river: str
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for bucket, name in (("early", f"days_1_{FROM_DAY - 1}"), ("late", f"from_day_{FROM_DAY}")):
        counter = counters[bucket]
        total = sum(counter.values())
        out[name] = {
            groups[0]: counter[groups[0]],
            groups[1]: counter[groups[1]],
            "east_fraction": round(counter[river] / total, 2) if total else None,
        }
    return out


def mentions_rule(text: str, subject: re.Pattern[str], effect: re.Pattern[str]) -> bool:
    """O assunto e o efeito de uma regra oculta no mesmo trecho (bíblia 2 §10)."""
    return any(subject.search(part) and effect.search(part) for part in SEGMENTS.split(text))


def east_signals(envelopes: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Os sinais do leste (fazenda 1) ou do rio (Boa Vista) de uma corrida, lidos do arquivo
    dela na ordem em que foi escrito (ADR-0061, decisão 5): a primeira anotação e a primeira
    crença que falam do lugar, a trajetória de cada crença sobre ele, e os plantios, colheitas e
    canteiros cavados por grupo, antes e a partir do dia 4. `discovered` é a heurística: uma
    crença ativa, confiante (0,7 ou mais) e que fala de tempo, de vantagem ou do rio. Na Boa
    Vista entram também as outras regras ocultas (`rules`: a primeira anotação e a primeira
    crença sobre cada uma) e o comportamento que as confirma ou desmente (`behaviour`)."""
    everything = list(envelopes)
    plot_group = plot_groups(everything)
    river = "rio" if "rio" in plot_group.values() or "fora" in plot_group.values() else "leste"
    groups = ("rio", "fora") if river == "rio" else ("oeste", "leste")
    mention = RIVER if river == "rio" else EAST
    first_note: dict[str, Any] | None = None
    first_discovery_note: dict[str, Any] | None = None  # a primeira que nota a vantagem
    first_belief: dict[str, Any] | None = None
    first_band_dig: dict[str, Any] | None = None
    tracks: dict[str, BeliefTrack] = {}
    plantings = {"early": Counter[str](), "late": Counter[str]()}
    harvests = {"early": Counter[str](), "late": Counter[str]()}
    digs = {"early": Counter[str](), "late": Counter[str]()}
    rules: dict[str, dict[str, Any]] = {
        name: {"first_note": None, "first_belief": None} for name in RULES
    }
    behaviour = Counter[str]()
    crops: dict[str, str] = {}  # o que está plantado em cada canteiro, para ver a rega do alho
    for envelope in everything:
        kind = str(envelope.get("type", ""))
        data: Mapping[str, Any] = envelope.get("data", {})
        day = _day(envelope)
        if kind == NOTED:
            text = str(data["text"])
            if mention.search(text):
                note = {"day": day, "hour": _hour(envelope), "text": text}
                if first_note is None:
                    first_note = note
                if first_discovery_note is None and notes_east_advantage(text, mention):
                    first_discovery_note = note
            for name, (subject, effect) in RULES.items():
                if rules[name]["first_note"] is None and mentions_rule(text, subject, effect):
                    rules[name]["first_note"] = {"day": day, "hour": _hour(envelope), "text": text}
        elif kind in (FORMED, UPDATED):
            belief_id, statement = str(data["belief_id"]), str(data["statement"])
            confidence = _confidence(data)
            for name, (subject, effect) in RULES.items():
                if rules[name]["first_belief"] is None and mentions_rule(
                    statement, subject, effect
                ):
                    rules[name]["first_belief"] = {
                        "day": day,
                        "belief_id": belief_id,
                        "statement": statement,
                        "confidence": confidence,
                    }
            track = tracks.get(belief_id)
            if track is None:
                if not mention.search(statement):
                    continue
                track = tracks[belief_id] = BeliefTrack(belief_id, statement, day, statement)
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
        elif kind == COMPLETED:
            action = str(data.get("action"))
            params: Mapping[str, Any] = data.get("params") or {}
            target = str(params.get("target"))
            bucket = "late" if day >= FROM_DAY else "early"
            if action in ("plant", "harvest"):
                group = group_of(target, plot_group)
                (plantings if action == "plant" else harvests)[bucket][group] += 1
                if action == "plant":
                    crop = str(params.get("crop"))
                    crops[target] = crop
                    if crop in ("tomate", "alho"):
                        behaviour[f"{crop}_planted"] += 1
                else:
                    crops.pop(target, None)
            elif action == "water" and crops.get(target) == "alho":
                behaviour["alho_waterings"] += 1
            elif action == "clear":
                crops.pop(target, None)
            elif action == "deposit":
                behaviour["deposits"] += 1
            elif action == "cook":
                behaviour["ensopados" if params.get("recipe") == "ensopado" else "pratos"] += 1
            elif action == "fertilize":
                behaviour["fertilized"] += 1
        elif kind == SPAWNED and data.get("kind") == "plot" and data.get("action_id"):
            group = group_of(str(data["entity_id"]), plot_group)
            digs["late" if day >= FROM_DAY else "early"][group] += 1
            if group == river and first_band_dig is None:
                first_band_dig = {"day": day, "hour": _hour(envelope), "plot": data["entity_id"]}
        elif kind == WITHERED and data.get("crop") == "tomate":
            behaviour["tomate_withered"] += 1
    active = [t for t in tracks.values() if t.retracted_day is None]
    discovery = [
        t for t in active if t.confidence >= 0.7 and notes_east_advantage(t.statement, mention)
    ]
    best = max(discovery, key=lambda t: t.confidence, default=None)
    return {
        "river": river,
        "groups": list(groups),
        "first_note": first_note,
        "first_discovery_note": first_discovery_note,
        "first_belief": first_belief,
        "beliefs": [asdict(t) for t in tracks.values()],
        "plantings": _buckets(plantings, groups, river),
        "harvests": _buckets(harvests, groups, river),
        "digs": _buckets(digs, groups, river),
        "first_band_dig": first_band_dig,
        "rules": rules,
        "behaviour": dict(sorted(behaviour.items())),
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

    @property
    def river(self) -> str:
        """O grupo que a regra favorece: `leste` na fazenda 1, `rio` na Boa Vista."""
        return str(self.east.get("river", "leste"))

    @property
    def groups(self) -> tuple[str, str]:
        return self.report.groups


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


def _frac(bucket: Mapping[str, Any], groups: tuple[str, str], river: str) -> str:
    total = int(bucket[groups[0]]) + int(bucket[groups[1]])
    if not total:
        return EMPTY
    return f"{round(float(bucket['east_fraction']) * 100)}% ({bucket[river]} de {total})"


def _table(header: Sequence[str], rows: Iterable[Sequence[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def _spark(values: Sequence[int], top: int) -> str:
    if top <= 0:
        return BARS[0] * len(values)
    return "".join(BARS[min(7, round(v / top * 7))] for v in values)


def _pair(
    mapping: Mapping[str, Any], decimals: int = 0, groups: tuple[str, str] = ("oeste", "leste")
) -> str:
    return f"{_n(mapping.get(groups[0], 0), decimals)} / {_n(mapping.get(groups[1], 0), decimals)}"


def _counts(mapping: Mapping[str, Any]) -> str:
    """`rabanete 148, tomate 6`, do maior para o menor; `-` quando não há nada."""
    items = sorted(mapping.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))
    return ", ".join(f"{name} {count}" for name, count in items) or EMPTY


def _tools(mapping: Mapping[str, Any]) -> str:
    """O dia da primeira compra de cada ferramenta: `regador grande dia 25, arado -`."""
    names = {"watering_can_large": "regador grande", "plow": "arado"}
    return ", ".join(
        f"{label} {'dia ' + str(mapping[kind]) if kind in mapping else EMPTY}"
        for kind, label in names.items()
    )


def _bible_rows(runs: Sequence[Run]) -> list[list[str]]:
    rows: list[tuple[str, list[str]]] = []

    def row(label: str, cell: Callable[[Run], str]) -> None:
        rows.append((label, [cell(r) for r in runs]))

    def llm(r: Run, key: str, decimals: int = 0) -> str:
        return _n(r.report.totals()["llm"][key], decimals) if r.has_model else EMPTY

    def totals(r: Run) -> dict[str, Any]:
        return r.report.totals()

    groups = runs[0].groups if runs else ("oeste", "leste")
    label = f"{groups[0]} / {groups[1]}"
    extras = any(r.report.has_extras for r in runs)  # a Boa Vista (bíblia 2 §13)
    row("Dias completos", lambda r: str(totals(r)["days"]))
    row("Moedas ao fim", lambda r: str(totals(r)["coins_end"]))
    row(f"Colheitas ({label})", lambda r: _pair(totals(r)["harvests"], groups=groups))
    row(f"Plantios ({label})", lambda r: _pair(totals(r)["plantings"], groups=groups))
    row(
        f"Dias até amadurecer ({label})",
        lambda r: " / ".join(_n(totals(r)["mean_days_to_mature"].get(g), 1) for g in groups),
    )
    if extras:
        row(f"Canteiros cavados ({label})", lambda r: _pair(totals(r)["plots_dug"], groups=groups))
        row("Ferramentas (dia da compra)", lambda r: _tools(totals(r)["tools_bought"]))
        row("Plantios por cultura", lambda r: _counts(totals(r)["plantings_by_crop"]))
        row("Refeições (por receita)", lambda r: _counts(totals(r)["cooked"]))
        row("Estragos (unidades, por item)", lambda r: _counts(totals(r)["spoiled"]))
        row("Murchas da madura", lambda r: str(totals(r)["withered_ripe"]))
        row(
            "Vendas (unidades; abaixo de 80% do preço)",
            lambda r: f"{totals(r)['sales']} ({totals(r)['sales_below_floor']})",
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
    row(
        "Parou no teto de orçamento",
        lambda r: (
            f"sim, no dia {r.summary['budget_day']}" if r.summary.get("budget_day") else "não"
        ),
    )
    row("Tempo real", lambda r: _duration(float(r.summary.get("real_seconds", 0))))
    return [[label, *cells] for label, cells in rows]


def _rule_cell(r: Run, name: str) -> str:
    """O que a corrida escreveu e fez sobre uma regra oculta da Boa Vista."""
    rule = cast(Mapping[str, Any], r.east.get("rules", {}).get(name, {}))
    done = cast(Mapping[str, Any], r.east.get("behaviour", {}))
    did = {
        "tomate": (
            f"plantou {done.get('tomate_planted', 0)}, murcharam {done.get('tomate_withered', 0)}"
        ),
        "alho": (
            f"plantou {done.get('alho_planted', 0)}, regou {done.get('alho_waterings', 0)} vez(es)"
        ),
        "bau": f"guardou {done.get('deposits', 0)} vez(es)",
        "ensopado": f"cozinhou {done.get('ensopados', 0)} ensopado(s)",
        "adubo": f"adubou {done.get('fertilized', 0)} vez(es)",
    }[name]
    if not r.has_memory:
        return f"sem memória; {did}"
    note, belief = rule.get("first_note"), rule.get("first_belief")
    wrote = f"anotação dia {note['day']}" if note else "nenhuma anotação"
    held = (
        f"crença dia {belief['day']} ({_n(belief['confidence'], 2)})"
        if belief
        else "nenhuma crença"
    )
    return f"{wrote}; {held}; {did}"


def _east_rows(runs: Sequence[Run]) -> list[list[str]]:
    river = runs[0].river if runs else "leste"
    groups = runs[0].groups if runs else ("oeste", "leste")
    place = "o leste" if river == "leste" else "o rio"
    where = "no leste" if river == "leste" else "na faixa do rio"

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

    def first_dig(r: Run) -> str:
        dig = r.east.get("first_band_dig")
        return f"dia {dig['day']}, {dig['hour']} ({dig['plot']})" if dig else "nunca"

    def frac(r: Run, what: str, bucket: str) -> str:
        return _frac(r.east[what][bucket], groups, river)

    def verdict(r: Run) -> str:
        control = " (controle: sem a regra)" if not r.spec.get("river_bonus", True) else ""
        if not r.has_memory:
            return "só pelo comportamento" + control
        if r.east["discovered"]:
            return f"descobriu ({r.east['discovered_by']})" + control
        return "não" + control

    early, late = f"days_1_{FROM_DAY - 1}", f"from_day_{FROM_DAY}"
    rows: list[list[str]] = [
        [f"Primeira anotação que cita {place}", *[first_note(r) for r in runs]],
        [f"Primeira anotação que nota a vantagem d{place}", *[discovery_note(r) for r in runs]],
        [f"Primeira crença sobre {place}", *[first_belief(r) for r in runs]],
        [f"Crenças sobre {place} ao fim", *[at_end(r) for r in runs]],
    ]
    if river == "rio":
        rows += [
            [
                f"Canteiros cavados {where}, dias 1 a {FROM_DAY - 1}",
                *[frac(r, "digs", early) for r in runs],
            ],
            [
                f"Canteiros cavados {where}, do dia {FROM_DAY}",
                *[frac(r, "digs", late) for r in runs],
            ],
            [f"Primeiro canteiro {where}", *[first_dig(r) for r in runs]],
        ]
    rows += [
        [
            f"Plantios {where}, dias 1 a {FROM_DAY - 1}",
            *[frac(r, "plantings", early) for r in runs],
        ],
        [f"Plantios {where}, do dia {FROM_DAY}", *[frac(r, "plantings", late) for r in runs]],
        [f"Colheitas {where}, do dia {FROM_DAY}", *[frac(r, "harvests", late) for r in runs]],
    ]
    if river == "rio":
        labels = {
            "tomate": "Regra oculta: o tomate murcha com um dia seco",
            "alho": "Regra oculta: o alho não precisa de rega",
            "bau": "Regra oculta: o baú conserva",
            "ensopado": "Regra oculta: o ensopado sacia por mais tempo",
            "adubo": "Regra oculta: o adubo e o seu tamanho",
        }
        rows += [[label, *[_rule_cell(r, name) for r in runs]] for name, label in labels.items()]
    rows.append(["Veredito", *[verdict(r) for r in runs]])
    return rows


def _trajectory(track: Mapping[str, Any], last_day: int) -> str:
    steps = " → ".join(
        f"dia {s['day']} {s['kind']} {_n(s['confidence'], 2)}" for s in track["steps"]
    )
    if track["retracted_day"] is not None:
        span = f"dia {track['first_day']} a {track['retracted_day']}, retirada"
    else:
        span = f"dia {track['first_day']} a {last_day}, confiança {_n(track['confidence'], 2)}"
    first = str(track.get("first_statement") or track["statement"])
    before = f' Antes: "{first}".' if first != track["statement"] else ""
    return f'- **{track["belief_id"]}** ({span}): "{track["statement"]}".{before} {steps}.'


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


def _controller_name(spec: Mapping[str, Any]) -> str:
    if spec.get("controller") == "human":
        return "humano"
    if spec.get("controller") != "llm":
        return str(spec.get("controller"))
    model = str(spec.get("model", "claude-haiku-5-5"))
    return MODEL_NAMES.get(model, model)


def _limits(spec: Mapping[str, Any]) -> str:
    limits = spec.get("limits")
    if not isinstance(limits, Mapping):
        return EMPTY
    limits = cast(Mapping[str, Any], limits)
    return f"{_n(limits.get('usd_per_sim_day'), 2)} · {_n(limits.get('usd_total'), 0)}"


def render(runs: Sequence[Run], *, source: str, date: str) -> str:
    """O relatório em Markdown, com as corridas lado a lado."""
    names = [r.name for r in runs]
    days = max((int(r.report.totals()["days"]) for r in runs), default=0)
    cartridge = str(runs[0].spec.get("cartridge", "farm_camps")) if runs else "farm_camps"
    world = WORLDS.get(cartridge, cartridge)
    river = runs[0].river if runs else "leste"
    place = "o leste" if river == "leste" else "o rio"
    behaviour = (
        f"plantios e colheitas no leste a partir do dia {FROM_DAY}"
        if river == "leste"
        else (
            "canteiros cavados na faixa do rio, e plantios e colheitas nela a partir do dia "
            f"{FROM_DAY}"
        )
    )
    lines = [
        f"# Arena de {date}",
        "",
        f"{len(runs)} corrida(s) de até {days} dias em processo, no mesmo mundo (`{world}`), "
        "com o mundo esperando o modelo por construção (ADR-0061). Gerado por `make arena-report` "
        f"a partir de `{source}` (fora do git). A tabela da bíblia §13 é o total dos dias "
        f'completos de cada corrida; "descobriu {place}" é lido do dado da memória de quem a '
        f"tem (a primeira anotação e a primeira crença que falam d{place}, e a trajetória de "
        f"cada crença) e do comportamento de todos ({behaviour}). A corrida sem a regra R-001 é "
        "o controle.",
        "",
        "## As corridas",
        "",
        _table(
            [
                "Corrida",
                "Controlador",
                "Memória",
                "Regra R-001",
                "Seed",
                "Dias",
                "Teto US$ (dia · total)",
                "Tempo real",
            ],
            [
                [
                    r.name,
                    _controller_name(r.spec),
                    "sim" if r.has_memory else "não",
                    "ligada" if r.spec.get("river_bonus", True) else "desligada",
                    str(r.spec.get("seed", "?")),
                    str(r.report.totals()["days"]),
                    _limits(r.spec),
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
    lines += ["", f"## Quem descobriu {place}", "", _table(["Sinal", *names], _east_rows(runs)), ""]
    for r in runs:
        if not r.has_memory:
            continue
        last_day = int(r.report.totals()["days"])
        lines += [f"### {r.name}: as crenças sobre {place}", ""]
        tracks = list(r.east["beliefs"])
        lines += [_trajectory(t, last_day) for t in tracks] or [f"Nenhuma crença falou d{place}."]
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
