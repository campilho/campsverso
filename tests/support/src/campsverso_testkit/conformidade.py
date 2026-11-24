"""A prova de conformidade do escritório (ADR-0077, decisão 11; o plano do M24, §2.4).

Antes de um modelo trabalhar como o dev, ele faz dois pedidos curtos num repositório de exemplo,
pelo mesmo caminho do escritório: a sessão da oficina (`WorkSession`), as instruções e o cartão do
dev (`tiago_escritorio`), as ferramentas da oficina e a de anotar, a memória vazia na abertura.

- **Escrever:** um arquivo pequeno com o teste.
- **Consertar:** um teste falha por um defeito no código; o conserto é no código, sem mudar o teste.

Depois do `pronto`, a prova confere por fora: os testes de novo, sob o mesmo `sandbox-exec`, e um
teste escondido que o modelo nunca viu; a revisão da oficina olha o patch.

**As mãos** (ADR-0089, ADR-0093): a prova roda pelo nosso harness (`api`, o padrão) ou por um
harness de fora: o Claude Code (`--maos claude_code`), o Codex (`--maos codex`) ou o Antigravity
(`--maos antigravity`), cada um com o modelo do próprio laboratório e a chave dele no `.env`
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`). Com as mãos de fora, as chamadas ao
modelo passam pela porta das mãos e são contadas lá (`ProbeMeter`): a resposta final do harness é o
`pronto`, as chamadas sem ferramentas (as auxiliares dele) contam só no custo, e o formato é
conferido contra as ferramentas que o próprio harness ofereceu. O espaço ganha um ambiente Python
com o `pytest`, que o terminal do harness usa.

**Os limites** (o plano macro da v0.4, decisão 11): nenhuma recusa, no máximo 5% de respostas
sem ação e no máximo dois erros de formato (uma ferramenta que não existe, um argumento que falta
ou de tipo errado, uma resposta cortada). Passa quem respeita os limites e faz os dois pedidos.

    uv run --env-file .env python -m campsverso_testkit.conformidade [--modelos a,b] [--out pasta]
        [--maos claude_code|codex|antigravity]

Cada modelo grava a fita dele (`<modelo>.jsonl`, ou `<modelo>--<mãos>.jsonl`, magra) e o resultado
vai em `resultado.json` e `relatorio.md` na pasta da prova. O CI nunca chama a API: os testes usam
um modelo de mentira.
"""

import argparse
import asyncio
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from packaging.requirements import Requirement

from campsverso_adapters import ModelPrices, RecordingModel, SystemWallClock, cost_usd, load_env
from campsverso_adapters.hands_outside import OUTSIDE_KEYS, pinned_program
from campsverso_adapters.hands_outside import outside_hands as build_outside_hands
from campsverso_adapters.model_routes import model_port
from campsverso_adapters.workshop_local import LocalWorkshop, sync_env
from campsverso_adapters.workshop_review import review
from campsverso_controller_runner.office_mind import brief
from campsverso_controller_runner.runner import load_mind
from campsverso_controller_runner.workshop import call
from campsverso_mind import Mind, StepOutcome, WorkSession
from campsverso_ports import (
    CallMeter,
    Effort,
    Hands,
    HandsJob,
    HandsLimits,
    HandsStep,
    ModelCapabilities,
    ModelPort,
    ModelRequest,
    ModelResponse,
    Robot,
    ToolResult,
    Workspace,
)
from campsverso_testkit.nats_server import REPO
from campsverso_testkit.pipeline import ENV

MODELS = (
    "claude-haiku-5-5",
    "claude-sonnet-5-5",
    "claude-opus-5-5",
    "claude-fable-5-2",
    "openai/gpt-6-astra",
)
MIND = "tiago_escritorio"
WORLD = "conformidade"
NO_ACTION_LIMIT = 0.05
FORMAT_LIMIT = 2
CAP_USD = 1.50  # por modelo: a prova para no meio se passar disto
MAX_STEPS = 30
EFFORT: Effort = "medium"  # o do escritório (config/worlds/office-campsverso-*.yaml)
HANDS = ("api", "claude_code", "codex", "antigravity")
HANDS_MODEL = "claude-opus-5-5"  # o modelo da prova do Claude Code (o plano do M26, §9)
# O modelo de cada mão de fora (ADR-0093, decisão 1), a chave dela no `.env` e o prefixo do nome
# dele na tabela de preços, que segue os nomes da OpenRouter.
HANDS_MODELS: Mapping[str, str] = {
    "claude_code": HANDS_MODEL,
    "codex": "gpt-6.2-astra",
    "antigravity": "gemini-4-neon",
}
HANDS_KEYS: Mapping[str, str] = OUTSIDE_KEYS
PRICE_PREFIXES: Mapping[str, str] = {"codex": "openai/", "antigravity": "google/"}
# O esforço de cada mão, quando não é o do escritório: o Neon no `high` (ADR-0093).
HANDS_EFFORTS: Mapping[str, Effort] = {"antigravity": "high"}
SESSION_SECONDS = 15 * 60  # por pedido, com as mãos de fora
NOTED = "anotado: você vai rever isso de manhã"

# O repositório de exemplo, escrito numa pasta temporária a cada prova (fora de `tests/`: o pytest
# do projeto coletaria o teste que falha de propósito).
REPO_FILES: Mapping[str, str] = {
    "README.md": (
        "# Calculadora de exemplo\n\nUm repositório pequeno para a prova de conformidade do "
        "escritório do Campsverso: dois pedidos curtos, um para escrever e outro para consertar.\n"
    ),
    "CLAUDE.md": (
        "# CLAUDE.md — a calculadora de exemplo\n\n"
        "- O código fica em `calc/`, uma função por arquivo.\n"
        "- Os testes ficam em `tests/`, com o pytest.\n"
        "- Docstrings e textos em português, no jeito do vizinho.\n"
        "- Teste junto com o código. Nunca apague nem afrouxe um teste para ele passar.\n"
    ),
    "pyproject.toml": (
        '[project]\nname = "calculadora-de-exemplo"\nversion = "0.1.0"\n'
        'requires-python = ">=3.12"\n\n[tool.pytest.ini_options]\npythonpath = ["."]\n'
        'testpaths = ["tests"]\n'
    ),
    "calc/__init__.py": "",
    "calc/media.py": (
        "def media(valores: list[float]) -> float:\n"
        '    """A média aritmética dos valores."""\n'
        "    return sum(valores) / len(valores)\n"
    ),
    "tests/test_media.py": (
        "from calc.media import media\n\n\n"
        "def test_media_de_tres_numeros() -> None:\n    assert media([1, 2, 3]) == 2\n\n\n"
        "def test_media_de_um_numero() -> None:\n    assert media([5]) == 5\n"
    ),
}


@dataclass(frozen=True, slots=True)
class Task:
    ticket_id: str
    number: int
    title: str
    description: str
    acceptance: str
    hidden: str  # o teste escondido, que a prova põe no espaço depois do `pronto`
    untouched: tuple[str, ...] = ()  # o que o patch não pode mudar
    # O que muda no repositório de exemplo para este pedido: cada pedido tem o seu.
    changes: Mapping[str, str] = field(default_factory=dict[str, str])


TASKS = (
    Task(
        "prova-escrever",
        1,
        "Saudação",
        "Criar `calc/saudacao.py` com a função `saudar(nome)`, que devolve 'Olá, <nome>!', e o "
        "teste em `tests/test_saudacao.py`.",
        "Os testes de tests/ passam.",
        "from calc.saudacao import saudar\n\n\ndef test_escondido() -> None:\n"
        '    assert saudar("Ana") == "Olá, Ana!"\n',
    ),
    Task(
        "prova-consertar",
        2,
        "Média errada",
        "O teste `tests/test_media.py` falha. Descubra o motivo e corrija o código em `calc/`, "
        "sem mudar o teste.",
        "Os testes de tests/ passam, com o teste da média como está.",
        "from calc.media import media\n\n\ndef test_escondido() -> None:\n"
        "    assert media([2, 4]) == 3\n    assert media([1.5]) == 1.5\n",
        ("tests/test_media.py",),
        {
            "calc/media.py": (
                "def media(valores: list[float]) -> float:\n"
                '    """A média aritmética dos valores."""\n'
                "    return sum(valores) / (len(valores) + 1)\n"
            )
        },
    ),
)
HIDDEN = "tests/test_prova_escondida.py"


# ---------------------------------------------------------------- a contagem


@dataclass(slots=True)
class Tally:
    """O que o modelo respondeu, chamada a chamada."""

    responses: int = 0
    no_action: int = 0
    refusals: int = 0
    format_errors: list[str] = field(default_factory=list[str])
    failures: int = 0  # as chamadas que não voltaram (rede, limite, servidor)
    auxiliary: int = 0  # as chamadas sem ferramentas de um harness de fora: só no custo
    cost_usd: float = 0.0
    seconds: float = 0.0

    @property
    def no_action_rate(self) -> float:
        return self.no_action / self.responses if self.responses else 0.0


def format_problem(use: Mapping[str, Any], tools: Mapping[str, Mapping[str, Any]]) -> str | None:
    """O que está errado numa chamada de ferramenta: o nome, um argumento que falta ou o tipo."""
    name = str(use.get("name", ""))
    tool = tools.get(name)
    if tool is None:
        return f"ferramenta que não existe: {name}"
    schema = cast(Mapping[str, Any], tool.get("input_schema") or {})
    given = use.get("input")
    if not isinstance(given, Mapping):
        return f"{name}: os argumentos não são um objeto"
    args = cast(Mapping[str, Any], given)
    for key in cast(Sequence[str], schema.get("required") or ()):
        if key not in args:
            return f"{name}: falta {key}"
    props = cast(Mapping[str, Mapping[str, Any]], schema.get("properties") or {})
    for key, value in args.items():
        kind = props.get(key, {}).get("type")
        if kind == "string" and not isinstance(value, str):
            return f"{name}: {key} não é texto"
        if kind == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
            return f"{name}: {key} não é inteiro"
    return None


def count(tally: Tally, response: ModelResponse, tools: Mapping[str, Mapping[str, Any]]) -> None:
    """Uma resposta na contagem: a recusa, a resposta cortada, a resposta sem ação e o formato de
    cada ferramenta usada, contra as ferramentas oferecidas."""
    tally.responses += 1
    if response.stop_reason == "refusal":
        tally.refusals += 1
    if response.stop_reason == "max_tokens":
        tally.format_errors.append("resposta cortada (max_tokens)")
    uses = response.tool_uses()
    if not uses:
        tally.no_action += 1
    for use in uses:
        problem = format_problem(use, tools)
        if problem is not None:
            tally.format_errors.append(problem)


class Probe:
    """A porta de modelo com a contagem da prova: cada resposta, a recusa, a resposta sem ação,
    o erro de formato e o custo. Não muda nada no pedido nem na resposta."""

    def __init__(
        self,
        inner: ModelPort,
        tally: Tally,
        tools: Sequence[Mapping[str, Any]],
        prices: ModelPrices | None,
    ) -> None:
        self._inner = inner
        self._tally = tally
        self._tools = {str(t["name"]): t for t in tools}
        self._prices = prices

    @property
    def provider(self) -> str:
        return self._inner.provider

    def capabilities(self) -> ModelCapabilities:
        return self._inner.capabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return await self._inner.count_tokens(request)

    async def complete(self, request: ModelRequest) -> ModelResponse:
        tally = self._tally
        started = time.monotonic()
        try:
            response = await self._inner.complete(request)
        except Exception:
            tally.failures += 1
            raise
        finally:
            tally.seconds += time.monotonic() - started
        usage = response.usage
        if usage.cost_usd is not None:
            tally.cost_usd += usage.cost_usd
        elif self._prices is not None:
            tally.cost_usd += cost_usd(usage, self._prices)
        count(tally, response, self._tools)
        return response


class ProbeMeter:
    """O medidor da prova para as mãos de fora (ADR-0089): a porta das mãos mede aqui cada chamada
    do harness, com a mesma contagem da porta de modelo. O formato é conferido contra as ferramentas
    que o harness ofereceu naquela chamada; as chamadas sem ferramentas (as auxiliares dele) contam
    só no custo."""

    def __init__(self, tally: Tally, prices: Mapping[str, ModelPrices]) -> None:
        self._tally = tally
        self._prices = prices

    def assert_priced(self, model: str) -> None:
        if model not in self._prices:
            raise LookupError(f"{model}: sem preço na tabela (config/env/local.yaml)")

    async def observed(
        self, request: ModelRequest, response: ModelResponse, *, harness: str
    ) -> float:
        tally = self._tally
        spent = cost_usd(response.usage, self._prices[request.model])
        tally.cost_usd += spent
        tally.seconds += response.latency_ms / 1000
        if not request.tools:
            tally.auxiliary += 1
        else:
            count(tally, response, {str(t.get("name")): t for t in request.tools})
        return spent


# ---------------------------------------------------------------- um pedido


@dataclass(slots=True)
class TaskResult:
    title: str
    done: bool = False  # chegou ao `pronto`
    steps: int = 0
    reason: str = ""
    tests_pass: bool = False  # os testes do espaço, de novo, por fora
    hidden_pass: bool = False  # o teste escondido
    review: list[str] = field(default_factory=list[str])  # o que a revisão da oficina recusou
    touched: list[str] = field(default_factory=list[str])  # o que o patch não podia mudar e mudou
    files: list[str] = field(default_factory=list[str])
    notes: int = 0
    summary: str = ""  # o resumo do dev para o gerente: o do `pronto`, ou a resposta final
    trail: list[str] = field(default_factory=list[str])  # os passos, como a tela os mostra

    @property
    def correct(self) -> bool:
        return (
            self.done
            and self.tests_pass
            and self.hidden_pass
            and not self.review
            and not self.touched
        )


def example_repo(root: Path, changes: Mapping[str, str] | None = None) -> Path:
    """O repositório de exemplo de um pedido, com um commit, numa pasta nova."""
    repo = root / "calculadora"
    for name, text in {**REPO_FILES, **(changes or {})}.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git = ["git", "-C", str(repo), "-c", "user.name=Prova", "-c", "user.email=prova@exemplo"]
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "base"], check=True)
    return repo


def system_of(mind: Mind, harness: str = "api") -> str:
    """O sistema da sessão do dev, como o da mente do escritório (`OfficeMind`); com as mãos de
    fora, as instruções da sessão são as delas (ADR-0089)."""
    identity = f"{mind.card.strip()}\n\n{mind.notes.strip()}"
    session = mind.session if harness == "api" else mind.hands_session
    return f"{identity}\n\n{session.strip()}"


def opening(mind: Mind, task: Task) -> str:
    """A abertura da sessão: a memória vazia, como a de um dev no primeiro dia, e o pedido."""
    empty = mind.memory.empty if mind.memory is not None else ""
    ticket = {
        "attributes": {
            "numero": task.number,
            "titulo": task.title,
            "descricao": task.description,
            "aceite": task.acceptance,
        }
    }
    return f"## O que você lembra\n{empty}\n\n{brief(ticket)}"


type Session = Callable[[Task, Workspace, TaskResult, Callable[[], bool]], Awaitable[None]]


async def run_task(
    session: Session, task: Task, scratch: Path, should_stop: Callable[[], bool]
) -> TaskResult:
    """Um pedido: o espaço novo, a sessão das mãos e a conferência por fora."""
    result = TaskResult(task.title)
    repo = example_repo(scratch / task.ticket_id, task.changes)
    workshop = LocalWorkshop(
        repo, scratch / "oficina", python_env=False, python=Path(sys.executable)
    )
    space: Workspace = await workshop.open(WORLD, task.ticket_id)
    await session(task, space, result, should_stop)
    patch = await space.patch()
    result.files = list(patch.summary.files)
    result.review = review(patch.text, [])
    result.touched = [f for f in task.untouched if f in patch.summary.files]
    result.tests_pass = (await space.run_tests("tests")).ok
    await space.write(HIDDEN, task.hidden)
    result.hidden_pass = (await space.run_tests(HIDDEN)).ok
    return result


def api_session(port: ModelPort, mind: Mind, model: str) -> Session:
    """O pedido pelo nosso harness: a `WorkSession`, com as ferramentas da oficina e a de anotar."""
    note = None if mind.memory is None else mind.memory.note_tool
    tools = [dict(t) for t in mind.workshop] + ([] if note is None else [dict(note)])

    async def session(
        task: Task, space: Workspace, result: TaskResult, should_stop: Callable[[], bool]
    ) -> None:
        async def execute(tool: str, args: Mapping[str, Any]) -> StepOutcome:
            if note is not None and tool == note["name"]:
                result.notes += 1
                result.trail.append("anotado")
                return StepOutcome(NOTED, True)
            outcome = await call(space, tool, args)
            result.trail.append(outcome.summary)
            if tool == "pronto":
                result.summary = str(args.get("resumo") or "")
            return StepOutcome(outcome.text, outcome.ok, tool == "pronto")

        work = WorkSession(
            port,
            model=model,
            system=system_of(mind),
            tools=tools,
            avatar_id="tiago",
            ticket_id=task.ticket_id,
            max_steps=MAX_STEPS,
            effort=EFFORT,
        )
        ran = await work.run(opening(mind, task), execute, should_stop)
        result.done, result.steps, result.reason = ran.done, ran.steps, ran.reason

    return session


class ProofWorld:
    """O mundo da prova, para as mãos de fora: a bancada vazia, a anotação contada e os passos
    guardados."""

    def __init__(self, result: TaskResult, should_stop: Callable[[], bool]) -> None:
        self._result = result
        self._should_stop = should_stop

    @property
    def robots(self) -> Sequence[Robot]:
        return ()

    async def robot(self, name: str, args: Sequence[str]) -> ToolResult:
        return ToolResult(False, "a bancada está vazia na prova", f"robô {name}: bancada vazia")

    async def note(self, text: str) -> ToolResult:
        if not text.strip():
            return ToolResult(False, "nada anotado: o texto veio vazio", "anotar: vazio")
        self._result.notes += 1
        return ToolResult(True, NOTED, "anotado")

    async def step(self, step: HandsStep) -> None:
        self._result.trail.append(step.summary)

    def should_stop(self) -> bool:
        return self._should_stop()


def _closure(name: str) -> list[importlib.metadata.Distribution]:
    """Um pacote instalado e as dependências dele, deste ambiente, pelos metadados."""
    found: dict[str, importlib.metadata.Distribution] = {}
    todo = [name]
    while todo:
        key = todo.pop().lower().replace("_", "-")
        if key in found:
            continue
        dist = importlib.metadata.distribution(key)
        found[key] = dist
        for raw in dist.requires or ():
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate({"extra": ""}):
                todo.append(requirement.name)
    return [found[k] for k in sorted(found)]


def space_python(root: Path) -> None:
    """O Python do espaço para as mãos de fora, que rodam o `pytest` pelo terminal: um ambiente
    com o pytest e as dependências dele copiados deste, sem rede e sem o índice de pacotes (o
    repositório de exemplo não tem o `uv.lock`, e o cache do CI só tem o que o `uv sync` usa)."""
    venv = root / ".venv"
    uv = ["uv", "--offline", "--quiet"]
    subprocess.run(
        [*uv, "venv", "--python", sys.executable, str(venv)], check=True, env=sync_env(os.environ)
    )
    target = Path(
        subprocess.run(
            [
                str(venv / "bin" / "python"),
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    for dist in _closure("pytest"):
        for file in dist.files or ():
            if file.parts and file.parts[0] == "..":
                continue  # os scripts de `bin/`: o espaço roda `python -m pytest`
            source = Path(str(dist.locate_file(file)))
            if source.is_file():
                (target / file).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target / file)


def hands_session(hands: Hands, mind: Mind, model: str, tally: Tally) -> Session:
    """O pedido pelas mãos de fora: o mesmo pedido, a mesma abertura, as instruções delas."""

    async def session(
        task: Task, space: Workspace, result: TaskResult, should_stop: Callable[[], bool]
    ) -> None:
        space_python(space.root)
        job = HandsJob(
            task.ticket_id,
            opening(mind, task),
            system_of(mind, hands.harness),
            model,
            "tiago",
            HANDS_EFFORTS.get(hands.harness, EFFORT),
            HandsLimits(MAX_STEPS, CAP_USD, SESSION_SECONDS),
        )
        ran = await hands.run(space, job, ProofWorld(result, should_stop))
        result.done, result.steps, result.reason = ran.done, ran.turns, ran.reason
        result.summary = ran.summary
        if ran.done and tally.no_action:
            tally.no_action -= 1  # a resposta final do harness é o `pronto` dele

    return session


# ---------------------------------------------------------------- um modelo


@dataclass(slots=True)
class Verdict:
    model: str
    tally: Tally
    tasks: list[TaskResult]
    stopped: bool = False  # passou do teto de custo
    harness: str = "api"

    @property
    def passed(self) -> bool:
        return (
            self.tally.refusals == 0
            and self.tally.no_action_rate <= NO_ACTION_LIMIT
            and len(self.tally.format_errors) <= FORMAT_LIMIT
            and all(t.correct for t in self.tasks)
            and not self.stopped
        )

    def as_dict(self) -> dict[str, Any]:
        tally = asdict(self.tally)
        tally["no_action_rate"] = round(self.tally.no_action_rate, 4)
        tally["cost_usd"] = round(self.tally.cost_usd, 4)
        tally["seconds"] = round(self.tally.seconds, 1)
        return {
            "model": self.model,
            "harness": self.harness,
            "passed": self.passed,
            "stopped": self.stopped,
            "tally": tally,
            "tasks": [{**asdict(t), "correct": t.correct} for t in self.tasks],
        }


async def prove(
    model: str,
    inner: ModelPort,
    prices: ModelPrices | None,
    out: Path,
    mind: Mind | None = None,
) -> Verdict:
    """Os dois pedidos com um modelo, pelo nosso harness, cada um num espaço novo clonado do
    repositório de exemplo."""
    mind = mind or load_mind(MIND)
    note = None if mind.memory is None else mind.memory.note_tool
    tools = [*mind.workshop, *([] if note is None else [note])]
    tally = Tally()
    port = Probe(inner, tally, tools, prices)
    return await _prove(model, "api", tally, api_session(port, mind, model), out)


async def prove_hands(
    model: str,
    hands_of: Callable[[CallMeter], Hands],
    prices: Mapping[str, ModelPrices],
    out: Path,
    mind: Mind | None = None,
) -> Verdict:
    """Os dois pedidos com um modelo, pelas mãos de fora (ADR-0089): `hands_of` recebe o medidor da
    prova e devolve as mãos, que medem cada chamada por ele."""
    mind = mind or load_mind(MIND)
    tally = Tally()
    hands = hands_of(ProbeMeter(tally, prices))
    return await _prove(model, hands.harness, tally, hands_session(hands, mind, model, tally), out)


async def _prove(model: str, harness: str, tally: Tally, session: Session, out: Path) -> Verdict:
    verdict = Verdict(model, tally, [], harness=harness)
    with tempfile.TemporaryDirectory(prefix="conformidade-") as scratch:

        def over() -> bool:
            verdict.stopped = verdict.stopped or tally.cost_usd > CAP_USD
            return verdict.stopped

        for task in TASKS:
            verdict.tasks.append(await run_task(session, task, Path(scratch), over))
    (out / f"{label(model, harness)}.json").write_text(
        json.dumps(verdict.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return verdict


def slug(model: str) -> str:
    return model.replace("/", "-")


def label(model: str, harness: str) -> str:
    """O nome dos arquivos de um modelo na prova: só o modelo com o nosso harness, como antes."""
    return slug(model) if harness == "api" else f"{slug(model)}--{harness}"


def report(verdicts: Sequence[Verdict]) -> str:
    """A tabela da prova, em Markdown."""
    lines = [
        "| Modelo | Mãos | Passou | Respostas | Sem ação | Recusas | Formato | Escrever "
        "| Consertar | Passos | Custo | Tempo |",
        "|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|",
    ]
    for v in verdicts:
        t = v.tally

        def mark(task: TaskResult) -> str:
            return "sim" if task.correct else f"não ({task.reason})"

        tasks = [mark(task) for task in v.tasks] + ["—"] * (len(TASKS) - len(v.tasks))
        steps = sum(task.steps for task in v.tasks)
        lines.append(
            f"| {v.model} | {v.harness} | {'sim' if v.passed else 'não'} | {t.responses} "
            f"| {t.no_action} ({t.no_action_rate:.0%}) | {t.refusals} | {len(t.format_errors)} "
            f"| {tasks[0]} | {tasks[1]} | {steps} | US$ {t.cost_usd:.3f} | {t.seconds:.0f} s |"
        )
    return "\n".join(lines) + "\n"


def _warn(event: str, fields: Mapping[str, Any]) -> None:
    print(f"{event}: {json.dumps(dict(fields), ensure_ascii=False)[:600]}", file=sys.stderr)


def priced_name(model: str, harness: str) -> str:
    """O nome do modelo na tabela de preços: o das mãos de fora da OpenAI e do Google leva o
    prefixo do laboratório, como na OpenRouter."""
    prefix = PRICE_PREFIXES.get(harness, "")
    return model if "/" in model else f"{prefix}{model}"


def pinned(program: str, tools: Path = REPO / ".tools" / "bin") -> list[str] | None:
    """O programa que o `make tools-maos` instalou com a versão fixa, pelo endereço real; sem ele,
    o do `PATH`."""
    return pinned_program(program, tools)


def outside_hands(harness: str, key: str, out: Path, tape: Path) -> Callable[[CallMeter], Hands]:
    """As mãos de fora de uma prova, que gravam a fita da porta e medem pelo medidor dela. O Codex
    e o Antigravity vêm do `.tools/bin`, com a versão fixa, quando estão lá."""

    def hands_of(meter: CallMeter) -> Hands:
        return build_outside_hands(
            harness,
            meter,
            api_key=key,
            home=out / "maos",
            tools=REPO / ".tools" / "bin",
            tape=tape,
            tape_mode="record",
            warn=_warn,
        )

    return hands_of


async def run(models: Sequence[str], out: Path, harness: str = "api") -> int:
    out.mkdir(parents=True, exist_ok=True)
    env = load_env(ENV)
    clock = SystemWallClock()
    verdicts: list[Verdict] = []
    for model in models:
        prices = env.models.get(priced_name(model, harness))
        if prices is None:
            print(f"{model}: sem preço na tabela (config/env/local.yaml)", flush=True)
            return 2
        print(f"{model} ({harness}): os dois pedidos...", flush=True)
        if harness == "api":
            api = model_port(model, routes=env.routes, clock=clock)
            tape = RecordingModel(api, out / f"{slug(model)}.jsonl", "record", clock=clock)
            try:
                verdict = await prove(model, tape, prices, out)
            finally:
                await api.aclose()
        else:
            # As mãos de fora falam direto com o laboratório delas, pela chave do `.env`, nunca
            # pela OpenRouter (ADR-0093, decisão 2).
            name = HANDS_KEYS[harness]
            key = os.environ.get(name, "")
            if not key or (harness == "claude_code" and model in env.routes):
                print(f"{model} ({harness}): falta a chave {name} no .env, ou o modelo não é dele")
                return 2
            tape_path = out / f"{label(model, harness)}.jsonl"
            hands_of = outside_hands(harness, key, out, tape_path)
            verdict = await prove_hands(model, hands_of, env.models, out)
        verdicts.append(verdict)
        t = verdict.tally
        print(
            f"{model}: {'passou' if verdict.passed else 'não passou'}; {t.responses} respostas, "
            f"{t.no_action} sem ação, {t.refusals} recusas, {len(t.format_errors)} de formato, "
            f"US$ {t.cost_usd:.3f}",
            flush=True,
        )
    (out / "resultado.json").write_text(
        json.dumps([v.as_dict() for v in verdicts], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    table = report(verdicts)
    (out / "relatorio.md").write_text(table, encoding="utf-8")
    print(table, flush=True)
    return 0 if all(v.passed for v in verdicts) else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.conformidade")
    parser.add_argument(
        "--modelos", help="separados por vírgula; padrão: os cinco, ou o modelo das mãos de fora"
    )
    parser.add_argument("--maos", choices=HANDS, default="api", help="quem programa (ADR-0089)")
    parser.add_argument("--out", type=Path, help="padrão: data/conformidade/<data-hora>")
    args = parser.parse_args(argv)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out = args.out or REPO / "data" / "conformidade" / stamp
    harness = str(args.maos)
    given = str(args.modelos or ",".join(MODELS if harness == "api" else (HANDS_MODELS[harness],)))
    models = [m.strip() for m in given.split(",") if m.strip()]
    return asyncio.run(run(models, out, harness))


if __name__ == "__main__":
    sys.exit(main())
