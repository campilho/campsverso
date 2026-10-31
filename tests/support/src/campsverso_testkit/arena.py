"""A arena (ADR-0061): as corridas de 30 dias em processo, uma por controlador, lado a lado.

    uv run --env-file .env python -m campsverso_testkit.arena --days 30 [--rodada boavista|morada]
        [--only NOME] [--out PASTA]

Sobre o `make corrida` do M11: o pipeline em memória (kernel, percepção, mente, medidor e guarda),
com o mundo esperando cada resposta por construção. As corridas rodam em sequência, cada uma na
sua pasta. A rodada `camps` (M12) é a fazenda 1: o script da bíblia §11, o Haiku 5.5 sem memória
(M10), o Haiku 5.5 com memória (M11) em quatro seeds e o Haiku 5.5 com memória sem a regra R-001,
como controle. A rodada `boavista` (M14, ADR-0063) é a Fazenda Boa Vista: o fazendeiro-script 2,
o Haiku com memória em quatro seeds e sem a regra, o Sonnet e o Opus, cada corrida com os seus
dias e o seu teto de orçamento. A rodada `morada` (M19, ADR-0070) é a verificação na Morada do
Sol: o script 2, o script 3 e o oráculo nos mapas a, b e c, o script 3 sem a água e a fadiga e o
Haiku com memória, um ano cada. A rodada `playbook` (ADR-0071) é o agricultor treinado: o Haiku
com o playbook no mapa a, sem e com no mapa b, e o Sonnet sem e com, 14 dias, se o Haiku mudar.
Uma pasta com `summary.json` é uma corrida feita, e uma pasta que existe é uma corrida tomada:
rodar de novo só completa as que faltam, e dois processos em paralelo dividem a rodada sozinhos.
Depois, `make arena-report` escreve o relatório. O CI nunca roda isto.
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

from campsverso_adapters import (
    AnthropicModel,
    OpenRouterModel,
    RecordingModel,
    SqliteMemory,
    SystemWallClock,
    key_variable,
    load_env,
    model_port,
)
from campsverso_budget.ledger import BudgetLimits
from campsverso_mind import PLAYBOOK_VERSION
from campsverso_ports import MemoryPort, ModelPort
from campsverso_testkit.fita import LIMITS, summary
from campsverso_testkit.nats_server import REPO
from campsverso_testkit.pipeline import ENV, MODEL, DeadlockError, Pipeline
from campsverso_testkit.prova import exam_of, examine, script_model
from campsverso_tools.arena import east_signals
from campsverso_tools.ficha import run_card
from campsverso_tools.metrics import compute, table

SEED = 20261010  # o mesmo dos testes e do mundo oficial
SEED_BOAVISTA = 20261019  # o do mundo farm-boavista-01
BOAVISTA = "farm_boavista"
SEED_MORADA = 20261022  # o do mundo farm-morada-do-sol-01
MORADA = "farm_morada_do_sol"
YEAR = 28  # o ano acelerado da Morada do Sol
SONNET = "claude-sonnet-5-5"
OPUS = "claude-opus-5-5"


@dataclass(frozen=True)
class Spec:
    """Uma corrida: quem controla o Camps, com que memória, com ou sem a regra, em que seed."""

    name: str
    controller: Literal["script", "llm"]
    memory: bool = False
    river_bonus: bool = True
    seed: int = SEED
    cartridge: str = "farm_camps"  # a Fazenda do Camps; farm_boavista é a fazenda 2 (M14)
    model: str = MODEL
    days: int | None = None  # os dias da corrida (a rodada da Boa Vista); sem isto, os de --days
    limits: BudgetLimits | None = None  # o teto da corrida; sem isto, o do Haiku (LIMITS)
    script: str | None = None  # o fazendeiro-script; sem isto, o do cartucho (ADR-0070)
    map: str | None = None  # a variante do mapa (ADR-0070); sem isto, o mapa de hoje
    playbook: int = 0  # a versão do playbook no prompt da mente (ADR-0071); 0 é sem playbook
    hire: str | None = None  # a contratação forçada do script 3, "ficha:dias" (ADR-0073)
    hire_from: int = 8  # o primeiro dia em que contrata (o do arquivo do script 3)
    compare: bool = False  # a ferramenta de comparação na reflexão, o braço do Haiku (ADR-0074)
    advisor: str | None = None  # o conselheiro na reflexão, o outro braço (ADR-0074)


SPECS: tuple[Spec, ...] = (
    Spec("script", "script"),
    Spec("haiku", "llm"),
    Spec("haiku-memoria", "llm", memory=True),
    Spec("haiku-memoria-s2", "llm", memory=True, seed=SEED + 1),
    Spec("haiku-memoria-s3", "llm", memory=True, seed=SEED + 2),
    Spec("haiku-memoria-s4", "llm", memory=True, seed=SEED + 3),
    Spec("haiku-memoria-sem-regra", "llm", memory=True, river_bonus=False),
)


def _boavista(name: str, **overrides: Any) -> Spec:
    """Uma corrida da mente com memória na Boa Vista, por 30 dias, na seed do mundo."""
    base: dict[str, Any] = {
        "controller": "llm",
        "memory": True,
        "seed": SEED_BOAVISTA,
        "cartridge": BOAVISTA,
        "days": 30,
    }
    return Spec(name, **(base | overrides))


# A segunda rodada (M14, ADR-0063): Sonnet e Opus por 30 dias, com tetos que dizem até onde
# cabem (uns US$ 0,60 e 0,95 por dia pela conta do plano); ARENA_DIAS limita todos.
SPECS_BOAVISTA: tuple[Spec, ...] = (
    Spec("script2", "script", seed=SEED_BOAVISTA, cartridge=BOAVISTA, days=30),
    _boavista("haiku-memoria"),
    _boavista("haiku-memoria-s2", seed=SEED_BOAVISTA + 1),
    _boavista("haiku-memoria-s3", seed=SEED_BOAVISTA + 2),
    _boavista("haiku-memoria-s4", seed=SEED_BOAVISTA + 3),
    _boavista("haiku-memoria-sem-regra", river_bonus=False),
    _boavista("sonnet-memoria", model=SONNET, limits=BudgetLimits(1.50, 25.0)),
    _boavista("opus-memoria", model=OPUS, limits=BudgetLimits(2.50, 35.0)),
)


def _morada(name: str, controller: Literal["script", "llm"], **overrides: Any) -> Spec:
    """Uma corrida da Morada do Sol: um ano (28 dias), na seed do mundo."""
    base: dict[str, Any] = {"seed": SEED_MORADA, "cartridge": MORADA, "days": YEAR}
    return Spec(name, controller, **(base | overrides))


# A rodada de verificação do M19 (ADR-0070, decisão 14): as três réguas nos três mapas, de graça,
# o script 3 com a água e a fadiga desligadas (o controle: não pode descobrir o que não existe) e
# uma corrida do Haiku com memória, caderno de campo e experimento no mapa a.
SPECS_MORADA: tuple[Spec, ...] = (
    *(
        _morada(
            f"{name}-{variant}", "script", script=script, map=None if variant == "a" else variant
        )
        for name, script in (("script2", "farmer2"), ("script3", "farmer3"), ("oraculo", "oracle"))
        for variant in ("a", "b", "c")
    ),
    _morada("script3-sem-regras", "script", script="farmer3", river_bonus=False),
    _morada("haiku-memoria", "llm", memory=True),
)
# O agricultor treinado (ADR-0071): o Haiku com o playbook 1 no mapa a (a corrida sem ele é a da
# rodada morada) e sem e com no mapa b; o playbook 2 duas vezes em cada mapa; o Sonnet sem e com,
# 14 dias no mapa a, só se o Haiku mudar.
SONNET_TETO = BudgetLimits(usd_per_sim_day=1.50, usd_total=15.0)
SPECS_PLAYBOOK: tuple[Spec, ...] = (
    _morada("haiku-playbook", "llm", memory=True, playbook=1),
    _morada("haiku-memoria-b", "llm", memory=True, map="b"),
    _morada("haiku-playbook-b", "llm", memory=True, map="b", playbook=1),
    # O playbook 2 (ADR-0071, a revisão): duas corridas iguais por mapa, porque o modelo sorteia;
    # o mundo é o mesmo (a seed), e a diferença entre elas é a do próprio modelo.
    *(
        _morada(f"haiku-playbook2{suffix}{rep}", "llm", memory=True, map=variant, playbook=2)
        for variant, suffix in ((None, ""), ("b", "-b"))
        for rep in ("", "-r2")
    ),
    _morada("sonnet-memoria-14d", "llm", memory=True, model=SONNET, days=14, limits=SONNET_TETO),
    _morada(
        "sonnet-playbook-14d",
        "llm",
        memory=True,
        model=SONNET,
        days=14,
        limits=SONNET_TETO,
        playbook=2,
    ),
)
# A verificação dos ajudantes (ADR-0072, decisão 12; ADR-0073): o script 3 e o oráculo nos mapas a
# e b, sem ajudante e com a contratação forçada a partir do dia 8, de graça. O Tião por 1 e por 7
# dias (o mais barato), a Nina por 3 e a Dita por 1 (a plantadeira).
HIRES = ("tiao:1", "tiao:7", "nina:3", "dita:1")
SPECS_AJUDANTES: tuple[Spec, ...] = tuple(
    _morada(
        f"{name}-{variant}" + (f"-{hire.replace(':', '')}" if hire else ""),
        "script",
        script=script,
        map=None if variant == "a" else variant,
        hire=hire,
    )
    for name, script in (("script3", "farmer3"), ("oraculo", "oracle"))
    for variant in ("a", "b")
    for hire in (None, *HIRES)
)
# A terceira arena (ADR-0074): as quatro réguas nos quatro mapas, de graça, com o script 3 fixo (a
# régua do meio, decisão 4); o d é o mapa do M21. As corridas dos modelos entram aqui uma por vez,
# no mapa d, com o ok do usuário (decisão 17).
RULERS = (
    ("script2", "farmer2"),
    ("script3", "farmer3"),
    ("script3-fixo", "farmer3-fixo"),
    ("oraculo", "oracle"),
)
SPECS_TERCEIRA: tuple[Spec, ...] = (
    *(
        _morada(
            f"{name}-{variant}", "script", script=script, map=None if variant == "a" else variant
        )
        for name, script in RULERS
        for variant in ("a", "b", "c", "d")
    ),
    # O Haiku três vezes (30/out), com memória, o caderno de campo e o experimento da noite, no
    # teto de sempre (US$ 0,60 por dia, 10 no total); os números ficam lacrados até o humano jogar.
    *(_morada(f"haiku{rep}", "llm", memory=True, map="d") for rep in ("", "-r2", "-r3")),
)
ROUNDS: dict[str, tuple[Spec, ...]] = {
    "camps": SPECS,
    "boavista": SPECS_BOAVISTA,
    "morada": SPECS_MORADA,
    "playbook": SPECS_PLAYBOOK,
    "ajudantes": SPECS_AJUDANTES,
    "terceira": SPECS_TERCEIRA,
}


def _hiring(spec: Spec) -> dict[str, Any] | None:
    """A contratação forçada (ADR-0073): a ficha e os dias, sempre que o caixa paga."""
    if spec.hire is None:
        return None
    helper, days = spec.hire.split(":")
    force = {"helper": helper, "days": int(days)}
    return {"helpers": {"force": force, "from_day": spec.hire_from}}


def _say(line: str, log: Path) -> None:
    print(line, flush=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


async def run_spec(
    spec: Spec, days: int, out: Path, *, port: ModelPort | None = None
) -> dict[str, Any]:
    """Roda uma corrida e grava a pasta dela: `summary.json` (o resumo, o `spec`, os totais da
    bíblia e os sinais do leste ou do rio), `metrics.txt`, `archive.jsonl` e, com modelo,
    `llm.jsonl` (a fita inteira) e `memory.sqlite`; no mundo com prova (ADR-0070), `prova.json`,
    com a prova da mente antes e depois, ou a do script 3 no fim; com o script 3 ou o oráculo,
    `modelo.json`, o que ele aprendeu (ou sabe). Devolve o resumo. Se a mente desistir (três
    falhas seguidas), a corrida para no dia em que isso aconteceu, marcado em `aborted_day`; se
    bater no teto de orçamento, idem, em `budget_day`. `port` troca a API por uma porta falsa
    (só os testes). O `archive.jsonl` cresce a cada dia simulado, e o `estado.json` diz o dia e
    se a corrida terminou: é o que o modo de assistir lê ao vivo (ADR-0068)."""
    if spec.playbook and spec.playbook != PLAYBOOK_VERSION:
        raise ValueError(
            f"{spec.name}: o playbook {spec.playbook} não está mais no código "
            f"(a versão de agora é a {PLAYBOOK_VERSION}; as antigas ficam no git)"
        )
    out.mkdir(parents=True, exist_ok=True)
    log = out / "progresso.txt"
    archive = out / "archive.jsonl"
    archive.write_text("", encoding="utf-8")
    written = 0

    def flush(day: int, *, done: bool = False) -> None:
        nonlocal written
        fresh = pipeline.envelopes[written:]
        with archive.open("a", encoding="utf-8") as handle:
            handle.writelines(json.dumps(e, ensure_ascii=False) + "\n" for e in fresh)
        written += len(fresh)
        state = {"name": spec.name, "day": day, "done": done, "events": written}
        (out / "estado.json").write_text(json.dumps(state), encoding="utf-8")

    clock = SystemWallClock()
    api: AnthropicModel | OpenRouterModel | None = None
    notebook: MemoryPort | bool = False
    if spec.controller == "llm":
        # A API da Anthropic, ou a OpenRouter quando o modelo tem rota na tabela (ADR-0074).
        routes = load_env(ENV).routes
        inner: ModelPort = (
            port if port is not None else model_port(spec.model, routes=routes, clock=clock)
        )
        api = inner if isinstance(inner, AnthropicModel | OpenRouterModel) else None
        port = RecordingModel(inner, out / "llm.jsonl", "record", clock=clock)
        notebook = SqliteMemory(out / "memory.sqlite") if spec.memory else False
    else:
        port = None
    pipeline = Pipeline(
        spec.seed,
        controller=spec.controller,
        river_bonus=spec.river_bonus,
        port=port,
        budget=(spec.limits or LIMITS) if port is not None else None,
        memory=notebook,
        cartridge=spec.cartridge,
        model=spec.model,
        map_variant=spec.map,
        script=spec.script,
        playbook=spec.playbook > 0,
        script_config=_hiring(spec),
        compare=spec.compare,
        advisor=spec.advisor,
    )
    exam = exam_of(spec.cartridge)
    prova: dict[str, Any] = {}  # a prova do mundo (ADR-0070): antes, com a memória vazia
    if exam is not None and (taken := await examine(pipeline, exam, port)) is not None:
        prova["before"] = taken
    started = datetime.now(UTC)
    _say(
        f"{spec.name}: {days} dia(s), {spec.controller}, memória "
        f"{'ligada' if spec.memory else 'desligada'}, regra "
        f"{'ligada' if spec.river_bonus else 'desligada'}, seed {spec.seed}"
        f"{f', mapa {spec.map}' if spec.map else ''}"
        f"{f', com o playbook {spec.playbook}' if spec.playbook else ''}"
        f"{', com a comparação' if spec.compare else ''}"
        f"{f', com o conselheiro {spec.advisor}' if spec.advisor else ''}"
        f"{f', contratando {spec.hire} desde o dia {spec.hire_from}' if spec.hire else ''}, "
        f"em {out}",
        log,
    )
    await pipeline.start()
    aborted: int | None = None
    budget_day: int | None = None
    for day in range(1, days + 1):
        try:
            await pipeline.run_days(1)
        except DeadlockError:
            partial = summary(pipeline)
            if not partial["budget_exceeded"]:
                raise
            budget_day = day  # a guarda pausou o mundo no teto (ADR-0058): o dia fica pela metade
            _say(
                f"{spec.name}: bateu no teto de orçamento no dia {day} "
                f"(US$ {partial['cost_usd']:.2f}); a corrida para aqui",
                log,
            )
            break
        flush(day)
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
        if partial["budget_exceeded"]:  # o teto chegou no fim do dia, sem travar o relógio
            budget_day = day
            _say(f"{spec.name}: bateu no teto de orçamento no dia {day}; a corrida para aqui", log)
            break
    if exam is not None and (taken := await examine(pipeline, exam, port, end=True)) is not None:
        prova["after"] = taken  # e no fim, com o bloco de abertura e o caderno
    model = script_model(pipeline.script) if pipeline.script is not None else None
    if model is not None:  # o que o script 3 aprendeu, ou a verdade do oráculo (ADR-0070)
        (out / "modelo.json").write_text(
            json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if api is not None:
        await api.aclose()  # antes de o laço desta corrida fechar
    report = compute(pipeline.envelopes)
    result: dict[str, Any] = {
        "spec": asdict(spec),
        **summary(pipeline),
        "aborted_day": aborted,
        "budget_day": budget_day,
        "real_seconds": round((datetime.now(UTC) - started).total_seconds(), 1),
        "totals": report.totals(),
        "east": east_signals(pipeline.envelopes),
    }
    mind = pipeline.mind  # a ficha da corrida (ADR-0074): o modelo, a rota, o esforço, o harness
    result["card"] = run_card(
        started=started.isoformat(),
        spec=result["spec"],
        envelopes=pipeline.envelopes,
        tape=out / "llm.jsonl",
        root=REPO,
        mind=None
        if mind is None
        else {"name": mind.mind.name, "system": mind.system, "tools": mind.tool_specs},
    )
    if exam is not None and prova:  # a nota no resumo; o gabarito e as respostas em prova.json
        result["prova"] = {
            when: {k: v for k, v in taken.items() if k != "answers"}
            for when, taken in prova.items()
        }
        key = {q.id: q.answer for q in exam.questions}
        (out / "prova.json").write_text(
            json.dumps({"key": key, **prova}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    (out / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / "metrics.txt").write_text(table(report) + "\n", encoding="utf-8")
    flush(budget_day or aborted or days, done=True)  # o resto do dia que parou, se parou
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.arena")
    parser.add_argument("--days", type=int, default=30, help="o teto de dias de cada corrida")
    parser.add_argument(
        "--rodada",
        choices=sorted(ROUNDS),
        default="camps",
        help="a lista de corridas: camps (a fazenda 1, M12), boavista (a fazenda 2, M14), "
        "morada (a verificação do M19), playbook (o agricultor treinado, ADR-0071) ou ajudantes "
        "(a contratação forçada, ADR-0073)",
    )
    parser.add_argument(
        "--only",
        action="append",
        help="só esta corrida (repetível); sem isto, todas, em sequência",
    )
    parser.add_argument(
        "--out", type=Path, help="a pasta da arena (padrão: data/arena/<data-hora>)"
    )
    args = parser.parse_args(argv)
    only: list[str] = list(args.only or [])
    names = [s.name for s in ROUNDS[args.rodada]]
    if unknown := sorted(set(only) - set(names)):
        parser.error(f"corrida(s) fora da rodada {args.rodada}: {', '.join(unknown)}")
    specs = [s for s in ROUNDS[args.rodada] if not only or s.name in only]
    routes = load_env(ENV).routes
    keys = sorted({key_variable(s.model, routes) for s in specs if s.controller == "llm"})
    if missing := [k for k in keys if not os.environ.get(k)]:
        print(f"{', '.join(missing)} ausente: rode com --env-file .env (ADR-0058)", file=sys.stderr)
        return 2
    out: Path = args.out or REPO / "data" / "arena" / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    for spec in specs:
        folder = out / spec.name
        if (folder / "summary.json").exists():
            print(f"{spec.name}: feita, pulando ({folder})", flush=True)
            continue
        try:
            folder.mkdir(parents=True, exist_ok=False)  # a reserva: a pasta é de quem a criou
        except FileExistsError:
            print(
                f"{spec.name}: tomada por outro processo, pulando "
                f"(se foi abandonada, apague {folder} para refazer)",
                flush=True,
            )
            continue
        days = min(spec.days, args.days) if spec.days else args.days
        result = asyncio.run(run_spec(spec, days, folder))
        totals = result["totals"]
        print(
            f"{spec.name}: {totals['days']} dias, moedas {totals['coins_end']}, "
            f"colheitas {totals['harvests']}, desmaios {totals['faints']}, "
            f"custo US$ {totals.get('llm', {}).get('cost_usd', 0):.2f}, "
            f"{result['east']['river']} "
            f"{'descoberto' if result['east']['discovered'] else 'não descoberto'}",
            flush=True,
        )
    print(f"relatório: make arena-report PASTA={out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
