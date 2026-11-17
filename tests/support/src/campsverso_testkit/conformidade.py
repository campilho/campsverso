"""A prova de conformidade do escritório (ADR-0077, decisão 11; o plano do M24, §2.4).

Antes de um modelo trabalhar como o dev, ele faz dois pedidos curtos num repositório de exemplo,
pelo mesmo caminho do escritório: a sessão da oficina (`WorkSession`), as instruções e o cartão do
dev (`camps_escritorio`), as ferramentas da oficina e a de anotar, a memória vazia na abertura.

- **Escrever:** um arquivo pequeno com o teste.
- **Consertar:** um teste falha por um defeito no código; o conserto é no código, sem mudar o teste.

Depois do `pronto`, a prova confere por fora: os testes de novo, sob o mesmo `sandbox-exec`, e um
teste escondido que o modelo nunca viu; a revisão da oficina olha o patch.

**Os limites** (o plano macro da v0.4, decisão 11): nenhuma recusa, no máximo 5% de respostas
sem ação e no máximo dois erros de formato (uma ferramenta que não existe, um argumento que falta
ou de tipo errado, uma resposta cortada). Passa quem respeita os limites e faz os dois pedidos.

    uv run --env-file .env python -m campsverso_testkit.conformidade [--modelos a,b] [--out pasta]

Cada modelo grava a fita dele (`<modelo>.jsonl`, magra) e o resultado vai em `resultado.json` e
`relatorio.md` na pasta da prova. O CI nunca chama a API: os testes usam um modelo de mentira.
"""

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from campsverso_adapters import ModelPrices, RecordingModel, SystemWallClock, cost_usd, load_env
from campsverso_adapters.model_routes import model_port
from campsverso_adapters.workshop_local import LocalWorkshop
from campsverso_adapters.workshop_review import review
from campsverso_controller_runner.office_mind import brief
from campsverso_controller_runner.runner import load_mind
from campsverso_controller_runner.workshop import call
from campsverso_mind import Mind, StepOutcome, WorkSession
from campsverso_ports import (
    Effort,
    ModelCapabilities,
    ModelPort,
    ModelRequest,
    ModelResponse,
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
MIND = "camps_escritorio"
WORLD = "conformidade"
NO_ACTION_LIMIT = 0.05
FORMAT_LIMIT = 2
CAP_USD = 1.50  # por modelo: a prova para no meio se passar disto
MAX_STEPS = 30
EFFORT: Effort = "medium"  # o do escritório (config/worlds/office-campsverso-*.yaml)

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
        tally.responses += 1
        usage = response.usage
        if usage.cost_usd is not None:
            tally.cost_usd += usage.cost_usd
        elif self._prices is not None:
            tally.cost_usd += cost_usd(usage, self._prices)
        if response.stop_reason == "refusal":
            tally.refusals += 1
        if response.stop_reason == "max_tokens":
            tally.format_errors.append("resposta cortada (max_tokens)")
        uses = response.tool_uses()
        if not uses:
            tally.no_action += 1
        for use in uses:
            problem = format_problem(use, self._tools)
            if problem is not None:
                tally.format_errors.append(problem)
        return response


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


def system_of(mind: Mind) -> str:
    """O sistema da sessão do dev, como o da mente do escritório (`OfficeMind`)."""
    identity = f"{mind.card.strip()}\n\n{mind.notes.strip()}"
    return f"{identity}\n\n{mind.session.strip()}"


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


async def run_task(
    port: ModelPort,
    mind: Mind,
    model: str,
    task: Task,
    scratch: Path,
    should_stop: Callable[[], bool],
) -> TaskResult:
    result = TaskResult(task.title)
    repo = example_repo(scratch / task.ticket_id, task.changes)
    workshop = LocalWorkshop(
        repo, scratch / "oficina", python_env=False, python=Path(sys.executable)
    )
    space: Workspace = await workshop.open(WORLD, task.ticket_id)
    note = None if mind.memory is None else mind.memory.note_tool
    tools = [dict(t) for t in mind.workshop] + ([] if note is None else [dict(note)])

    async def execute(tool: str, args: Mapping[str, Any]) -> StepOutcome:
        if note is not None and tool == note["name"]:
            result.notes += 1
            return StepOutcome("anotado: você vai rever isso de manhã", True)
        outcome = await call(space, tool, args)
        return StepOutcome(outcome.text, outcome.ok, tool == "pronto")

    session = WorkSession(
        port,
        model=model,
        system=system_of(mind),
        tools=tools,
        avatar_id="camps",
        ticket_id=task.ticket_id,
        max_steps=MAX_STEPS,
        effort=EFFORT,
    )
    ran = await session.run(opening(mind, task), execute, should_stop)
    result.done, result.steps, result.reason = ran.done, ran.steps, ran.reason
    patch = await space.patch()
    result.files = list(patch.summary.files)
    result.review = review(patch.text, [])
    result.touched = [f for f in task.untouched if f in patch.summary.files]
    result.tests_pass = (await space.run_tests("tests")).ok
    await space.write(HIDDEN, task.hidden)
    result.hidden_pass = (await space.run_tests(HIDDEN)).ok
    return result


# ---------------------------------------------------------------- um modelo


@dataclass(slots=True)
class Verdict:
    model: str
    tally: Tally
    tasks: list[TaskResult]
    stopped: bool = False  # passou do teto de custo

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
    """Os dois pedidos com um modelo, cada um num espaço novo clonado do repositório de exemplo."""
    mind = mind or load_mind(MIND)
    note = None if mind.memory is None else mind.memory.note_tool
    tools = [*mind.workshop, *([] if note is None else [note])]
    tally = Tally()
    port = Probe(inner, tally, tools, prices)
    verdict = Verdict(model, tally, [])
    with tempfile.TemporaryDirectory(prefix="conformidade-") as scratch:

        def over() -> bool:
            verdict.stopped = verdict.stopped or tally.cost_usd > CAP_USD
            return verdict.stopped

        for task in TASKS:
            verdict.tasks.append(await run_task(port, mind, model, task, Path(scratch), over))
    (out / f"{slug(model)}.json").write_text(
        json.dumps(verdict.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return verdict


def slug(model: str) -> str:
    return model.replace("/", "-")


def report(verdicts: Sequence[Verdict]) -> str:
    """A tabela da prova, em Markdown."""
    lines = [
        "| Modelo | Passou | Respostas | Sem ação | Recusas | Formato | Escrever | Consertar "
        "| Passos | Custo | Tempo |",
        "|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|",
    ]
    for v in verdicts:
        t = v.tally

        def mark(task: TaskResult) -> str:
            return "sim" if task.correct else f"não ({task.reason})"

        tasks = [mark(task) for task in v.tasks] + ["—"] * (len(TASKS) - len(v.tasks))
        steps = sum(task.steps for task in v.tasks)
        lines.append(
            f"| {v.model} | {'sim' if v.passed else 'não'} | {t.responses} "
            f"| {t.no_action} ({t.no_action_rate:.0%}) | {t.refusals} | {len(t.format_errors)} "
            f"| {tasks[0]} | {tasks[1]} | {steps} | US$ {t.cost_usd:.3f} | {t.seconds:.0f} s |"
        )
    return "\n".join(lines) + "\n"


async def run(models: Sequence[str], out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    env = load_env(ENV)
    clock = SystemWallClock()
    verdicts: list[Verdict] = []
    for model in models:
        prices = env.models.get(model)
        if prices is None:
            print(f"{model}: sem preço na tabela (config/env/local.yaml)", flush=True)
            return 2
        api = model_port(model, routes=env.routes, clock=clock)
        tape = RecordingModel(api, out / f"{slug(model)}.jsonl", "record", clock=clock)
        print(f"{model}: os dois pedidos...", flush=True)
        try:
            verdict = await prove(model, tape, prices, out)
        finally:
            await api.aclose()
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
    parser.add_argument("--modelos", default=",".join(MODELS), help="separados por vírgula")
    parser.add_argument("--out", type=Path, help="padrão: data/conformidade/<data-hora>")
    args = parser.parse_args(argv)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out = args.out or REPO / "data" / "conformidade" / stamp
    models = [m.strip() for m in str(args.modelos).split(",") if m.strip()]
    return asyncio.run(run(models, out))


if __name__ == "__main__":
    sys.exit(main())
