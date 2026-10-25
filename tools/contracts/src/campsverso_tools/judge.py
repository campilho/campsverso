"""O juiz das crenças (ADR-0070, decisão 13).

    uv run --env-file .env python -m campsverso_tools.judge PASTA [--only NOME]
    uv run python -m campsverso_tools.judge PASTA --conferir docs/arena/juiz-gabarito.yaml

Lê as crenças do fim de cada corrida com memória (com as evidências, a trajetória e as que foram
retiradas) e dá, para cada regra oculta do mundo, um veredito: **a causa** (a crença diz o
mecanismo, e serviria num mapa novo: "perto da água cresce mais rápido"), **só o lugar** (um
lugar é melhor, sem o porquê: "o leste cresce mais rápido") ou **não descobriu**. O juiz é o
Opus 5.5, uma chamada por corrida, pela porta de modelo e numa fita (`juiz.jsonl`); o veredito
vai para `juiz.json`, que o relatório da arena lê sem chamar de novo. O juiz não sabe de quem são
as crenças: o dossiê não tem nome de corrida, de modelo nem de seed. A rubrica de cada mundo fica
no cartucho (`cartridges/<cartucho>/eval/juiz.yaml`), com a verdade das regras.

O juiz classifica o que as crenças afirmam, como se a regra valesse: numa corrida com a regra
desligada, "a causa" é uma descoberta falsa, e quem lê o relatório sabe disso pelo `spec`.

`--conferir` compara os vereditos gravados com o gabarito feito à mão e imprime a concordância e
as discordâncias, sem chamar nada.
"""

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_adapters import (
    AnthropicModel,
    ModelPrices,
    RecordingModel,
    SystemWallClock,
    cost_usd,
    load_env,
)
from campsverso_ports import ModelCallError, ModelPort, ModelRequest, ModelResponse

REPO = Path(__file__).resolve().parents[4]
ENV = REPO / "config" / "env" / "local.yaml"
MODEL = "claude-opus-5-5"
VERDICT = "verdicts"
CAUSE, PLACE, NONE = "causa", "lugar", "nao"
MIN_CONFIDENCE = 0.5
FORMED = "campsverso.memory.belief.formed.v1"
UPDATED = "campsverso.memory.belief.updated.v1"
RETRACTED = "campsverso.memory.belief.retracted.v1"
TICKS_PER_DAY = 1440


def _day(envelope: Mapping[str, Any]) -> int:
    return int(envelope.get("tick") or 0) // TICKS_PER_DAY + 1


def _confidence(value: Any) -> float:
    if isinstance(value, Mapping):
        return float(cast(Mapping[str, Any], value)["after"])
    return float(value)


def _pct(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


@dataclass
class Belief:
    """Uma crença, da formação ao fim: o enunciado de agora, as evidências e cada passo."""

    belief_id: str
    statement: str
    first_statement: str
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list[str])
    steps: list[str] = field(default_factory=list[str])
    retracted: tuple[int, str] | None = None  # o dia e o porquê


def beliefs_of(
    envelopes: Iterable[Mapping[str, Any]], until_day: int | None = None
) -> dict[str, Belief]:
    """As crenças da corrida, lidas dos eventos da memória na ordem do arquivo; com `until_day`,
    como estavam no fim daquele dia."""
    found: dict[str, Belief] = {}
    for envelope in envelopes:
        kind = str(envelope.get("type", ""))
        if kind not in (FORMED, UPDATED, RETRACTED):
            continue
        if until_day is not None and _day(envelope) > until_day:
            break
        data = cast(Mapping[str, Any], envelope.get("data") or {})
        belief_id, statement = str(data["belief_id"]), str(data["statement"])
        belief = found.setdefault(belief_id, Belief(belief_id, statement, statement))
        belief.statement = statement
        day = _day(envelope)
        if kind == RETRACTED:
            belief.retracted = (day, str(data.get("reason") or ""))
            belief.steps.append(f"dia {day} retirada")
            continue
        belief.retracted = None
        belief.confidence = _confidence(data["confidence"])
        belief.evidence = [str(e) for e in cast(Sequence[Any], data.get("evidence") or ())]
        step = "formada" if kind == FORMED else "revisada"
        belief.steps.append(f"dia {day} {step} {_pct(belief.confidence)}")
    return found


def dossier(envelopes: Iterable[Mapping[str, Any]], until_day: int | None = None) -> str:
    """O que o juiz lê: as crenças ativas (enunciado, confiança, evidências e trajetória) e as
    retiradas, sem nada que diga de quem são; com `until_day`, as daquele dia."""
    beliefs = sorted(beliefs_of(envelopes, until_day).values(), key=lambda b: b.belief_id)
    active = [b for b in beliefs if b.retracted is None]
    gone = [b for b in beliefs if b.retracted is not None]
    lines = [f"## As crenças ativas no fim ({len(active)})", ""]
    for b in active:
        lines.append(f"### {b.belief_id} (confiança {_pct(b.confidence)})")
        lines.append(f"Enunciado: {b.statement}")
        if b.first_statement != b.statement:
            lines.append(f"Como foi formada: {b.first_statement}")
        lines.extend(f"- evidência: {e}" for e in b.evidence)
        lines.append("Trajetória: " + "; ".join(b.steps))
        lines.append("")
    lines += [f"## As crenças retiradas ({len(gone)})", ""]
    for b in gone:
        day, reason = b.retracted or (0, "")
        why = f" Por quê: {reason}" if reason else ""
        lines.append(f"- {b.belief_id}, retirada no dia {day}: {b.statement}{why}")
    return "\n".join(lines).rstrip() + "\n"


def read_envelopes(text: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


# ----------------------------------------------------------------------------- a rubrica


@dataclass(frozen=True)
class Rule:
    """Uma regra oculta: a verdade, o que conta como a causa e, se houver, como só o lugar."""

    id: str
    rule: str
    cause: str
    place: str | None = None

    @property
    def verdicts(self) -> list[str]:
        return [CAUSE, PLACE, NONE] if self.place else [CAUSE, NONE]


@dataclass(frozen=True)
class Rubric:
    world: str
    rules: tuple[Rule, ...]


def _flat(text: Any) -> str:
    return " ".join(str(text).split())


def load_rubric(cartridge: str, root: Path = REPO) -> Rubric | None:
    """A rubrica do mundo, em `cartridges/<cartucho>/eval/juiz.yaml`; `None` sem rubrica."""
    path = root / "cartridges" / cartridge / "eval" / "juiz.yaml"
    if not path.is_file():
        return None
    doc = cast(Mapping[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))
    rules = tuple(
        Rule(
            str(r["id"]),
            _flat(r["rule"]),
            _flat(r["cause"]),
            _flat(r["place"]) if r.get("place") else None,
        )
        for r in cast(Sequence[Mapping[str, Any]], doc["rules"])
    )
    return Rubric(_flat(doc["world"]), rules)


INSTRUCTIONS = f"""\
Você é o juiz de um experimento com agentes que vivem numa fazenda simulada. O agente não sabia \
as regras ocultas do mundo: anotou crenças sobre como o mundo funciona, a partir do que viu. Você \
recebe a descrição do mundo, as regras ocultas (a verdade) e as crenças do agente no fim da \
corrida, e diz, para cada regra, o que as crenças mostram que ele descobriu.

Os vereditos:
- `{CAUSE}`: uma crença afirma o mecanismo da regra, no sentido certo, de um jeito que serviria \
para agir num mapa novo (o que conta como a causa vem descrito em cada regra);
- `{PLACE}`: uma crença diz que um lugar é melhor ou pior pelo efeito da regra, sem dizer o \
porquê; só existe nas regras que descrevem o que conta como só o lugar;
- `{NONE}`: nenhuma crença mostra a regra.

Como julgar:
1. Só contam as crenças ativas com confiança de {MIN_CONFIDENCE:.1f} ou mais. As retiradas e as \
de confiança menor aparecem só para contexto.
2. Julgue pelo enunciado. As evidências e a forma como a crença foi formada ajudam a entender o \
que o enunciado quer dizer, mas não acrescentam uma descoberta que o enunciado não faz.
3. A crença tem de afirmar o efeito no sentido certo. Uma crença que contradiz a regra, que é \
vaga demais para guiar uma decisão, ou que só repete o que o manual já diz, vale `{NONE}`.
4. Se mais de uma crença serve, fique com o veredito mais alto ({CAUSE}, depois {PLACE}) e, \
entre as crenças que o sustentam, com a de maior confiança.
5. Cite o id da crença que sustenta o veredito; em `{NONE}`, deixe o id vazio.
6. Explique cada veredito numa frase curta.

Responda com a ferramenta `{VERDICT}`, e só com ela."""


def verdict_tool(rubric: Rubric) -> dict[str, Any]:
    """A ferramenta estrita dos vereditos: um objeto por regra."""
    return {
        "name": VERDICT,
        "description": "Entregue o veredito de cada regra oculta.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                r.id: {
                    "type": "object",
                    "properties": {
                        "verdict": {"type": "string", "enum": r.verdicts},
                        "belief_id": {"type": "string"},
                        "why": {"type": "string"},
                    },
                    "required": ["verdict", "belief_id", "why"],
                    "additionalProperties": False,
                }
                for r in rubric.rules
            },
            "required": [r.id for r in rubric.rules],
            "additionalProperties": False,
        },
    }


def judge_request(rubric: Rubric, text: str, *, model: str = MODEL) -> ModelRequest:
    """O pedido: a rubrica (o mundo e as regras) e o dossiê da corrida, sem saber de quem é."""
    lines = ["# O mundo", "", rubric.world, "", "# As regras ocultas", ""]
    for r in rubric.rules:
        lines.append(f"## `{r.id}`")
        lines.append(f"A verdade: {r.rule}")
        lines.append(f"Conta como a causa quando {r.cause}")
        if r.place:
            lines.append(f"Conta como só o lugar quando {r.place}")
        lines.append("")
    lines += ["# As crenças do agente", "", text]
    return ModelRequest(
        model=model,
        messages=[{"role": "user", "content": [{"type": "text", "text": "\n".join(lines)}]}],
        system=INSTRUCTIONS,
        tools=[verdict_tool(rubric)],
        max_tokens=16_000,
        effort="high",
        purpose="judge",
    )


def read_verdicts(rubric: Rubric, response: ModelResponse) -> dict[str, dict[str, str]]:
    """Os vereditos da ferramenta; o que falta ou não é opção vira `nao`, sem crença."""
    chosen = next((t for t in response.tool_uses() if t.get("name") == VERDICT), None)
    given = cast(Mapping[str, Any], (chosen or {}).get("input") or {})
    found: dict[str, dict[str, str]] = {}
    for r in rubric.rules:
        item = cast(Mapping[str, Any], given.get(r.id) or {})
        verdict = str(item.get("verdict", NONE))
        if verdict not in r.verdicts:
            verdict = NONE
        belief = str(item.get("belief_id") or "") if verdict != NONE else ""
        found[r.id] = {"verdict": verdict, "belief_id": belief, "why": str(item.get("why", ""))}
    return found


async def judge(
    port: ModelPort,
    rubric: Rubric,
    text: str,
    *,
    model: str = MODEL,
    prices: ModelPrices | None = None,
) -> dict[str, Any]:
    """Uma chamada: os vereditos, o uso e o custo; uma chamada que falha não tem veredito."""
    try:
        response = await port.complete(judge_request(rubric, text, model=model))
    except ModelCallError as error:
        return {"model": model, "error": error.kind, "message": error.message, "rules": {}}
    return {
        "model": model,
        "rules": read_verdicts(rubric, response),
        "usage": response.usage.as_dict(),
        "cost_usd": cost_usd(response.usage, prices) if prices is not None else 0.0,
        "replayed": response.replayed,
    }


# ----------------------------------------------------------------------------- a arena


def _spec(folder: Path) -> Mapping[str, Any]:
    summary = cast(Mapping[str, Any], json.loads((folder / "summary.json").read_text("utf-8")))
    return cast(Mapping[str, Any], summary.get("spec") or {})


def judged_runs(arena: Path, only: Sequence[str] = ()) -> list[Path]:
    """As corridas com memória de uma arena, que são as que têm crenças para julgar."""
    found = [
        sub
        for sub in sorted(arena.iterdir())
        if (sub / "summary.json").is_file() and _spec(sub).get("memory")
    ]
    return [f for f in found if not only or f.name in only]


async def judge_run(folder: Path, port: ModelPort, *, model: str = MODEL) -> dict[str, Any] | None:
    """Julga uma corrida: a fita em `juiz.jsonl` e o veredito em `juiz.json`. Uma fita que já
    tem o pedido responde de graça."""
    rubric = load_rubric(str(_spec(folder).get("cartridge") or "farm_camps"))
    if rubric is None:
        return None
    text = dossier(read_envelopes((folder / "archive.jsonl").read_text(encoding="utf-8")))
    clock = SystemWallClock()
    taped = RecordingModel(port, folder / "juiz.jsonl", "record", clock=clock)
    result = await judge(taped, rubric, text, model=model, prices=load_env(ENV).models.get(model))
    (folder / "juiz.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


async def judge_arena(arena: Path, only: Sequence[str] = (), *, model: str = MODEL) -> float:
    api = AnthropicModel(clock=SystemWallClock())
    spent = 0.0
    try:
        for folder in judged_runs(arena, only):
            result = await judge_run(folder, api, model=model)
            if result is None:
                print(f"{folder.name}: o mundo não tem rubrica", flush=True)
                continue
            spent += float(result.get("cost_usd", 0.0)) if not result.get("replayed") else 0.0
            verdicts = cast(Mapping[str, Mapping[str, str]], result["rules"])
            told = ", ".join(f"{k} {v['verdict']}" for k, v in verdicts.items())
            print(f"{folder.name}: {told or result.get('error')}", flush=True)
    finally:
        await api.aclose()
    return spent


# ----------------------------------------------------------------------------- a conferência


def _marked(mark: Any) -> str:
    """Uma marcação do gabarito: o veredito só, ou `{verdict, belief}`."""
    if isinstance(mark, Mapping):
        return str(cast(Mapping[str, Any], mark)["verdict"])
    return str(mark)


def agreement(key: Path, root: Path) -> tuple[int, int, list[str]]:
    """O gabarito feito à mão contra os vereditos gravados: concordâncias, total e cada
    discordância numa linha. `root` é a pasta das arenas."""
    doc = cast(Mapping[str, Any], yaml.safe_load(key.read_text(encoding="utf-8")))
    agreed = total = 0
    differ: list[str] = []
    for run, expected in cast(Mapping[str, Mapping[str, Any]], doc["runs"]).items():
        path = root / run / "juiz.json"
        given: Mapping[str, Mapping[str, str]] = {}
        if path.is_file():
            given = cast(Mapping[str, Any], json.loads(path.read_text(encoding="utf-8")))["rules"]
        for rule, mark in expected.items():
            want = _marked(mark)
            got = str(given.get(rule, {}).get("verdict", "sem veredito"))
            total += 1
            if got == want:
                agreed += 1
            else:
                why = given.get(rule, {}).get("why", "")
                differ.append(f"{run} {rule}: à mão {want}, o juiz {got}. {why}".rstrip())
    return agreed, total, differ


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_tools.judge")
    parser.add_argument("arena", type=Path, help="a pasta da arena (data/arena/<rodada>)")
    parser.add_argument("--only", action="append", help="só esta corrida (repetível)")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument(
        "--conferir", type=Path, help="o gabarito feito à mão: confere, sem chamar nada"
    )
    args = parser.parse_args(argv)
    if args.conferir is not None:
        agreed, total, differ = agreement(args.conferir, args.arena)
        print(f"concordância: {agreed} de {total} ({agreed / max(total, 1):.0%})")
        for line in differ:
            print(f"- {line}")
        return 0
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY ausente: rode com --env-file .env (ADR-0058)", file=sys.stderr)
        return 2
    spent = asyncio.run(judge_arena(args.arena, list(args.only or []), model=args.model))
    print(f"custo do juiz: US$ {spent:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
