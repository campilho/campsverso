"""A prova do mundo na arena (ADR-0070, decisão 12).

Com a mente, a prova vai duas vezes pela fita da corrida, fora do medidor do mundo (não conta nas
chamadas nem no teto da corrida; o custo fica em `prova.json`): antes de o mundo começar, com a
memória vazia (o que o modelo supõe), e no fim, com o bloco de abertura e o caderno. A mente
nunca vê a prova enquanto joga.

O script 3 e o oráculo não respondem: o avaliador lê a crença deles (o efeito de cada atributo,
com o intervalo corrigido pelas comparações múltiplas, e a perda medida por faixa de distância) e
escolhe a opção que a crença sustenta, pela regra que cada pergunta declara em `script`; sem como
ler, ou sem dado bastante, "não sei". O oráculo passa pela mesma leitura com a verdade no lugar da
crença, e tirar o gabarito nessas perguntas confere que o gabarito bate com as regras do cartucho.
O script 2 não tem modelo e fica sem prova.

A leitura mudou no M21 (ADR-0074, decisão 13): o intervalo de 90% virou o corrigido, e a pergunta
dos corvos passou de 30 para 40 tiles. `reread` relê as rodadas antigas pelo `modelo.json`, sem
regravar nada:

    uv run python -m campsverso_testkit.prova data/arena/<rodada> [...]
"""

import argparse
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_adapters import cost_usd, load_env
from campsverso_mind import Clock, Exam, LlmController, Question, exam_request, grade, load_exam
from campsverso_mind import read_answers as read_given
from campsverso_ports import ModelCallError, ModelPort
from campsverso_testkit.nats_server import REPO
from campsverso_testkit.pipeline import ENV, Pipeline
from campsverso_tools.arena import corrected

type Effects = Mapping[str, tuple[float, float]]  # o atributo e o intervalo corrigido, em vezes
type Loss = Callable[[int, int | None], tuple[float, int]]  # (porta, espantalho) -> (perda, vezes)

EXAM = "eval/prova.yaml"  # a prova de um cartucho, fora do pacote da mente
FAR, NEAR = 40, 5  # as distâncias da porta nas perguntas dos corvos (40: além da última faixa)
GUARD_AT = (1, 6)  # a distância ao espantalho de cada faixa da pergunta do espantalho
MIN_SEEN = 3  # plantios maduros medidos para uma perda contar
HIGH, LOW = 0.25, 0.1  # perda alta e perda baixa
SURE = 1_000_000  # as "medidas" da verdade, no oráculo
FARMER3 = REPO / "cartridges/farm/script/src/campsverso_farm_script/data/farmer3.yaml"


def exam_of(cartridge: str) -> Exam | None:
    path = REPO / "cartridges" / cartridge / EXAM
    return load_exam(path) if path.is_file() else None


# ----------------------------------------------------------------------------- a mente


async def take_exam(
    port: ModelPort, exam: Exam, mind: LlmController, memory: str, *, model: str
) -> dict[str, Any]:
    """Uma prova: a nota, as respostas e o custo; uma chamada que falha responde "não sei"."""
    request = exam_request(
        exam, system=mind.identity, memory=memory, model=model, avatar_id="camps"
    )
    try:
        response = await port.complete(request)
    except ModelCallError as error:
        result = grade(exam, {q.id: exam.unknown for q in exam.questions}).as_dict()
        return {**result, "cost_usd": 0.0, "error": error.kind}
    prices = load_env(ENV).models.get(model)
    cost = cost_usd(response.usage, prices) if prices is not None else 0.0
    return {**grade(exam, read_given(exam, response)).as_dict(), "cost_usd": cost}


async def examine(
    pipeline: Pipeline, exam: Exam, port: ModelPort | None, *, end: bool = False
) -> dict[str, Any] | None:
    """A prova de uma corrida, antes de começar ou no fim (`end`): a mente com memória responde
    pela porta, com o que lembra; o script, só no fim, pelo modelo dele; `None` sem prova."""
    mind = pipeline.mind
    if mind is not None and mind.memory is not None and port is not None:
        memory = mind.memory
        block = memory.block(memory.clock or Clock(0, 1, ""))  # antes: "o caderno está vazio"
        return await take_exam(port, exam, mind, block, model=mind.model)
    if end and pipeline.script is not None:
        return script_exam(exam, pipeline.script)
    return None


# ----------------------------------------------------------------------------- o script


def _corrected(effects: Sequence[tuple[str, float, float]]) -> Effects:
    """O intervalo de 90% de cada atributo, corrigido pelos atributos do modelo (sem a base)."""
    attributes = sum(1 for name, _, _ in effects if name != "base")
    return {name: corrected(low, high, attributes) for name, low, high in effects}


def knowledge_of(script: object) -> tuple[Effects, Loss] | None:
    """A crença do script 3 (ou a verdade do oráculo), lida do caderno dele; `None` sem modelo."""
    knows: Any = getattr(getattr(script, "book", None), "beliefs", None)
    if knows is None:
        return None
    effects = _corrected([(str(e.name), float(e.low), float(e.high)) for e in knows.effects()])
    truth = getattr(knows, "loss", None)  # o oráculo sabe a chance, sem medir
    if callable(truth):
        known = cast(Callable[[int, int | None], float], truth)
        return effects, lambda door, guard: (known(door, guard), SURE)
    rates = cast(Mapping[tuple[int, int], tuple[float, int]], knows.loss_rates())
    cell = cast(Callable[[int, int | None], tuple[int, int]], knows.loss_cell)
    return effects, lambda door, guard: rates.get(cell(door, guard), (0.0, 0))


def _effect(q: Question, effects: Effects, unknown: str) -> str:
    rule = q.script
    measured = [effects[n] for n in cast(Sequence[str], rule["effect"]) if n in effects]
    if any(low > 1.0 for low, _ in measured):
        return str(rule["above"])
    if any(high < 1.0 for _, high in measured):
        return str(rule["below"])
    return unknown


def _reach(q: Question, effects: Effects, unknown: str) -> str:
    """A faixa mais longe da água que ainda ajuda, com certeza."""
    bands = cast(Mapping[str, str], q.script["reach"])
    helping = [n for n in bands if n in effects and effects[n][0] > 1.0]
    return bands[helping[-1]] if helping else unknown


def _loss(q: Question, loss: Loss, unknown: str) -> str:
    rule = q.script
    kind, means = str(rule["loss"]), str(rule.get("means", unknown))
    far, seen_far = loss(FAR, None)
    if kind == "far":
        return means if seen_far >= MIN_SEEN and far >= HIGH else unknown
    if kind == "near":
        near, seen = loss(NEAR, None)
        return means if seen >= MIN_SEEN and near <= LOW else unknown
    if seen_far < MIN_SEEN or far < HIGH:
        return unknown  # sem perda longe, não há do que proteger
    bands = cast(Mapping[int, str], rule["bands"])
    protected = [
        band
        for band, distance in enumerate(GUARD_AT)
        if (rate := loss(FAR, distance))[1] >= MIN_SEEN and rate[0] <= LOW
    ]
    return bands.get(protected[-1], unknown) if protected else unknown


def script_answers(exam: Exam, effects: Effects, loss: Loss) -> dict[str, str]:
    """A resposta que a crença sustenta em cada pergunta; "não sei" onde não há como ler."""
    answers: dict[str, str] = {}
    for q in exam.questions:
        if "effect" in q.script:
            answers[q.id] = _effect(q, effects, exam.unknown)
        elif "reach" in q.script:
            answers[q.id] = _reach(q, effects, exam.unknown)
        elif "loss" in q.script:
            answers[q.id] = _loss(q, loss, exam.unknown)
        else:
            answers[q.id] = exam.unknown
    return answers


def script_model(script: object) -> dict[str, Any] | None:
    """O modelo do script 3 no fim (ou a verdade do oráculo): o efeito de cada atributo, com o
    intervalo de 90% e os plantios que o mediram, e a perda medida por faixa (`modelo.json`)."""
    knows: Any = getattr(getattr(script, "book", None), "beliefs", None)
    if knows is None:
        return None
    effects = [
        {"name": e.name, "mean": e.mean, "low": e.low, "high": e.high, "measured": e.measured}
        for e in knows.effects()
    ]
    rates = cast(Mapping[tuple[int, int], tuple[float, int]], knows.loss_rates())
    loss = [
        {"door": door, "guard": guard, "rate": rate, "measured": seen}
        for (door, guard), (rate, seen) in rates.items()
    ]
    config = cast(Mapping[str, Any], getattr(getattr(knows, "beliefs", knows), "config", {}))
    bins = {name: [int(b) for b in config.get(name, ())] for name in ("loss_door", "loss_guard")}
    return {"effects": effects, "loss": loss, "bins": bins}


def script_exam(exam: Exam, script: object) -> dict[str, Any] | None:
    """A prova do fim de um script, lida no modelo dele; `None` sem modelo (o script 2)."""
    known = knowledge_of(script)
    if known is None:
        return None
    return grade(exam, script_answers(exam, *known)).as_dict()


# ----------------------------------------------------------------------------- a releitura


def _bins(model: Mapping[str, Any]) -> tuple[list[int], list[int]]:
    """As faixas da perda: as do `modelo.json`, ou, nas rodadas de antes do M21, as do arquivo."""
    bins = cast(Mapping[str, Sequence[int]] | None, model.get("bins"))
    if bins is None:
        config = cast(Mapping[str, Any], yaml.safe_load(FARMER3.read_text(encoding="utf-8")))
        bins = cast(Mapping[str, Sequence[int]], config["model"])
    return [int(b) for b in bins["loss_door"]], [int(b) for b in bins["loss_guard"]]


def model_knowledge(model: Mapping[str, Any]) -> tuple[Effects, Loss]:
    """A crença gravada de um script 3 (`modelo.json`), na leitura de hoje."""
    found = cast(Sequence[Mapping[str, Any]], model["effects"])
    effects = _corrected([(str(e["name"]), float(e["low"]), float(e["high"])) for e in found])
    doors, guards = _bins(model)
    rates = {
        (int(e["door"]), int(e["guard"])): (float(e["rate"]), int(e["measured"]))
        for e in cast(Sequence[Mapping[str, Any]], model["loss"])
    }

    def loss(door: int, guard: int | None) -> tuple[float, int]:
        d = next((i for i, b in enumerate(doors) if door <= b), len(doors))
        g = (
            len(guards)
            if guard is None
            else next((i for i, b in enumerate(guards) if guard <= b), len(guards))
        )
        return rates.get((d, g), (0.0, 0))

    return effects, loss


def reread(arena: Path, exam: Exam) -> list[dict[str, Any]]:
    """A prova do fim de cada script 3 de uma rodada, gravada e relida (ADR-0074, decisão 13): o
    nome, a nota de antes e a de agora, e as perguntas cuja resposta mudou. Não regrava nada."""
    rows: list[dict[str, Any]] = []
    for folder in sorted(p for p in arena.iterdir() if (p / "modelo.json").is_file()):
        summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
        if summary["spec"].get("script") != "farmer3" or not (folder / "prova.json").is_file():
            continue
        given = json.loads((folder / "prova.json").read_text(encoding="utf-8"))["after"]
        model = json.loads((folder / "modelo.json").read_text(encoding="utf-8"))
        now = grade(exam, script_answers(exam, *model_knowledge(model))).as_dict()
        before = cast(Mapping[str, str], given["answers"])
        changed = {
            q: (before.get(q, exam.unknown), a)
            for q, a in now["answers"].items()
            if before.get(q, exam.unknown) != a
        }
        rows.append({"name": folder.name, "before": given, "now": now, "changed": changed})
    return rows


def _score(taken: Mapping[str, Any]) -> str:
    return f"{taken['right']} certas, {taken['wrong']} erradas, {taken['unknown']} não sei"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="a prova dos scripts 3, relida (ADR-0074)")
    parser.add_argument("arenas", nargs="+", type=Path)
    parser.add_argument("--cartucho", default="farm_morada_do_sol")
    args = parser.parse_args(argv)
    exam = exam_of(args.cartucho)
    if exam is None:
        print(f"{args.cartucho}: sem prova", file=sys.stderr)
        return 1
    print("| Rodada | Corrida | Gravada | Relida | O que mudou |")
    print("|---|---|---|---|---|")
    for arena in args.arenas:
        for row in reread(arena, exam):
            changed = "; ".join(f"{q}: {a} → {b}" for q, (a, b) in row["changed"].items())
            cells = (arena.name, row["name"], _score(row["before"]), _score(row["now"]))
            print(f"| {' | '.join(cells)} | {changed or 'nada'} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
