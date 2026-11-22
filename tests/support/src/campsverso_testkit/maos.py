"""A comparação das mãos (ADR-0089, decisão 10; o plano do M26, §7).

O mesmo pedido, feito pelas duas mãos com o mesmo modelo: o nosso harness (`api`) e o Claude Code
(`claude_code`), o Opus 5.5 nas duas, e depois o Fable 5.2 no Claude Code num dos pedidos. Cada
corrida é o escritório de teste em processo, do quadro à entrega, sem o humano:

- o gerente-script escreve o pedido às 9:30, com as mãos e o modelo na ficha;
- o dev senta, e o robô do briefing abre a sessão;
- o dev trabalha num clone deste repositório, no commit de agora, com o ambiente Python do espaço,
  como o escritório vivo (`uv sync`, sem rede);
- a memória começa limpa, e a ordem das mãos alterna de um pedido para o outro.

Depois da sessão, a comparação confere por fora, no espaço do pedido:
- **o CI de perto:** o `ruff` e o `pyright` nos arquivos mudados e os testes da bancada
  (`tools/robos/tests`), sob o `sandbox-exec` da oficina;
- **o aceite:** um teste escondido, que o dev nunca viu, conferindo o teste de aceite do pedido.

**O teto** de cada corrida é o do pedido no escritório, US$ 5, somando as duas portas. As mãos de
fora param também no teto da sessão (US$ 4, pela estimativa do SDK), nas 80 voltas e nos 45
minutos.

    uv run --env-file .env python -m campsverso_testkit.maos [--so 1,2] [--out pasta]
    uv run python -m campsverso_testkit.maos --relatorio [--out pasta]

Cada corrida fica em `<pasta>/<n>-<pedido>-<mãos>-<modelo>/`: os fatos (`fatos.jsonl`), o
resultado (`resultado.json`), o patch, a fita das duas portas e a conversa do Claude Code. O
relatório (`make maos-relatorio`) é lido daí. O CI nunca roda isto.
"""

import argparse
import asyncio
import fnmatch
import json
import os
import subprocess
import sys
import time
import tomllib
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from campsverso_adapters import RecordingModel, SystemWallClock, load_env
from campsverso_adapters.hands_claude_code import ClaudeCodeHands
from campsverso_adapters.model_routes import ANTHROPIC_KEY, model_port
from campsverso_adapters.workshop_local import LocalWorkshop
from campsverso_ports import (
    CallMeter,
    Hands,
    ModelPort,
    ModelRequest,
    ModelResponse,
    Workspace,
)
from campsverso_testkit.fita import Capped
from campsverso_testkit.nats_server import REPO
from campsverso_testkit.pipeline import ENV, Pipeline

CAP_USD = 5.00  # o teto do pedido no escritório (ADR-0089, decisão 8)
OFFICE = "office_campsverso"
WORLD = "office-campsverso-teste"
TICKET_ID = "pedido-001"
HIDDEN = "tools/robos/tests/test_aceite_escondido.py"
OPUS = "claude-opus-5-5"
FABLE = "claude-fable-5-2"
FACTS = (
    "campsverso.office.ticket.",
    "campsverso.workshop.",
    "campsverso.llm.call.",
    "campsverso.agent.said.",
)


@dataclass(frozen=True, slots=True)
class Ticket:
    slug: str
    title: str
    description: str
    acceptance: str
    size: str
    hidden: str  # o teste escondido do aceite


CONTADOR = Ticket(
    "contador",
    "Robô contador de linhas",
    "Um robô novo, tools/robos/contador.py, que conta as linhas dos arquivos .py por pasta: "
    "`python -m tools.robos.contador <pasta> [<pasta> ...]` imprime uma linha por pasta dada, no "
    "formato `<pasta>: <código> de código, <teste> de teste`, em que as de teste são as dos "
    "arquivos test_*.py e as de código, as dos outros .py, contadas como linhas do arquivo. "
    "Pula .venv, node_modules, __pycache__, data e privado. Sem argumentos, imprime o uso e sai "
    "com 2. Ponha o robô na bancada (a lista robos: no escritorio.yaml do cenário), com o teste.",
    "Numa pasta com a.py de 3 linhas e tests/test_a.py de 2, o robô imprime "
    "`<pasta>: 3 de código, 2 de teste`. Os testes de tools/robos/tests passam.",
    "P",
    '''"""O aceite do contador, escondido do dev (a comparação das mãos, ADR-0089)."""

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_conta_codigo_e_teste_por_pasta(tmp_path: Path) -> None:
    pasta = tmp_path / "pasta"
    (pasta / "tests").mkdir(parents=True)
    (pasta / ".venv").mkdir()
    (pasta / "a.py").write_text("a = 1\\nb = 2\\nc = 3\\n", encoding="utf-8")
    (pasta / "tests" / "test_a.py").write_text("def test_a() -> None:\\n    pass\\n")
    (pasta / ".venv" / "fora.py").write_text("x = 1\\n" * 50, encoding="utf-8")
    out = subprocess.run(
        [sys.executable, "-m", "tools.robos.contador", str(pasta)],
        capture_output=True, text=True, cwd=ROOT, check=False,
    )
    assert out.returncode == 0, out.stderr
    assert f"{pasta}: 3 de código, 2 de teste" in out.stdout


def test_sem_argumentos_sai_com_2() -> None:
    out = subprocess.run(
        [sys.executable, "-m", "tools.robos.contador"],
        capture_output=True, text=True, cwd=ROOT, check=False,
    )
    assert out.returncode == 2


def test_esta_na_bancada() -> None:
    sim = ROOT / "cartridges/office_campsverso/sim/src/campsverso_office_campsverso_sim"
    doc = yaml.safe_load((sim / "data/escritorio.yaml").read_text(encoding="utf-8"))
    assert "tools.robos.contador" in [r["modulo"] for r in doc["robos"]]
''',
)

HISTORIA = Ticket(
    "historia",
    "Briefing com a história",
    "No robô do briefing (tools/robos/briefing.py), uma seção nova, `## História recente`, logo "
    "depois de `## Arquivos prováveis`: para cada arquivo provável, os dois últimos commits que o "
    "tocaram, o mais novo primeiro, um por linha, no formato "
    "`- <arquivo>: <data AAAA-MM-DD> <assunto do commit>`, pelo git do repositório. Arquivo sem "
    "commit, ou fora de um repositório git, fica de fora; sem nenhum, a seção diz "
    "`- (sem história)`. A função `build(request, notes, claude_md, root)` continua com os mesmos "
    "parâmetros, e o briefing, dentro do teto de 150 linhas: quando passa, a história é cortada "
    "antes de tudo.",
    "Num repositório git de teste com dois commits num arquivo que o pedido cita, o briefing traz "
    "os dois na seção, o mais novo primeiro. Os testes de tools/robos/tests passam.",
    "M",
    '''"""O aceite da história no briefing, escondido do dev (a comparação das mãos, ADR-0089)."""

import os
import subprocess
from pathlib import Path

from tools.robos import briefing


def _git(root: Path, *args: str, when: str) -> None:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Teste",
        "GIT_AUTHOR_EMAIL": "teste@exemplo",
        "GIT_COMMITTER_NAME": "Teste",
        "GIT_COMMITTER_EMAIL": "teste@exemplo",
        "GIT_AUTHOR_DATE": when,
        "GIT_COMMITTER_DATE": when,
    }
    subprocess.run(["git", "-C", str(root), *args], check=True, env=env, capture_output=True)


def test_a_historia_traz_os_dois_commits_do_arquivo(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "ferramentas").mkdir(parents=True)
    _git(tmp_path, "init", "-q", "-b", "main", str(root), when="2026-11-01T10:00:00+00:00")
    target = root / "ferramentas" / "busca.py"
    target.write_text("A = 1\\n", encoding="utf-8")
    _git(root, "add", "-A", when="2026-11-01T10:00:00+00:00")
    _git(root, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "primeira busca",
         when="2026-11-01T10:00:00+00:00")
    target.write_text("A = 2\\n", encoding="utf-8")
    _git(root, "add", "-A", when="2026-11-03T10:00:00+00:00")
    _git(root, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "busca melhor",
         when="2026-11-03T10:00:00+00:00")
    text = briefing.build("Pedido 1: a busca nas ferramentas", "", "", root)
    assert "## História recente" in text
    assert text.index("## Arquivos prováveis") < text.index("## História recente")
    new = "- ferramentas/busca.py: 2026-11-03 busca melhor"
    old = "- ferramentas/busca.py: 2026-11-01 primeira busca"
    assert new in text
    assert old in text
    assert text.index(new) < text.index(old)
    assert len(text.splitlines()) <= briefing.MAX_LINES


def test_fora_do_git_a_secao_diz_sem_historia(tmp_path: Path) -> None:
    (tmp_path / "ferramentas").mkdir()
    (tmp_path / "ferramentas" / "busca.py").write_text("A = 1\\n", encoding="utf-8")
    text = briefing.build("Pedido 1: a busca nas ferramentas", "", "", tmp_path)
    assert "## História recente" in text
    assert "- (sem história)" in text
''',
)

APONTA = Ticket(
    "aponta",
    "Testador aponta o que não tem teste",
    "No robô testador (tools/robos/testador.py), depois da linha do ruff, uma linha "
    "`sem teste: <arquivos>` com os arquivos .py dados que não são de teste (fora de tests/ e sem "
    "o prefixo test_) e cujo módulo nenhum arquivo test_*.py do repositório importa. O módulo de "
    "`ferramentas/contar.py` é `ferramentas.contar`, e contam tanto `import ferramentas.contar` "
    "quanto `from ferramentas.contar import x`. Sem nenhum, a linha é `sem teste: nenhum`. A "
    "função nova `untested(paths, root)` devolve a lista dos arquivos sem teste, na ordem dada, "
    "com os caminhos relativos a `root` como vieram.",
    "Num repositório de teste com pkg/a.py, pkg/b.py e tests/test_a.py, que importa pkg.a, o "
    "testador aponta só pkg/b.py. Os testes de tools/robos/tests passam.",
    "M",
    '''"""O aceite do testador que aponta, escondido do dev (a comparação das mãos, ADR-0089)."""

from pathlib import Path

from tools.robos import testador


def _repo(root: Path, test_text: str) -> None:
    (root / "pkg").mkdir()
    (root / "tests").mkdir()
    (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (root / "pkg" / "a.py").write_text("X = 1\\n", encoding="utf-8")
    (root / "pkg" / "b.py").write_text("Y = 2\\n", encoding="utf-8")
    (root / "tests" / "test_a.py").write_text(test_text, encoding="utf-8")


def test_aponta_so_o_arquivo_sem_teste(tmp_path: Path) -> None:
    _repo(tmp_path, "from pkg.a import X\\n\\n\\ndef test_x() -> None:\\n    assert X == 1\\n")
    paths = ["pkg/a.py", "pkg/b.py", "tests/test_a.py"]
    assert testador.untested(paths, tmp_path) == ["pkg/b.py"]


def test_o_import_direto_tambem_conta(tmp_path: Path) -> None:
    _repo(tmp_path, "import pkg.a\\nimport pkg.b\\n")
    assert testador.untested(["pkg/a.py", "pkg/b.py"], tmp_path) == []
''',
)

TICKETS = {t.slug: t for t in (CONTADOR, HISTORIA, APONTA)}


@dataclass(frozen=True, slots=True)
class Run:
    number: int
    ticket: Ticket
    harness: str
    model: str

    @property
    def label(self) -> str:
        model = self.model.removeprefix("claude-")
        return f"{self.number}-{self.ticket.slug}-{self.harness}-{model}"


# A ordem alterna de um pedido para o outro (o plano do M26, §7); o Fable 5.2 entra por último, no
# Claude Code, no pedido do meio.
RUNS = (
    Run(1, CONTADOR, "api", OPUS),
    Run(2, CONTADOR, "claude_code", OPUS),
    Run(3, HISTORIA, "claude_code", OPUS),
    Run(4, HISTORIA, "api", OPUS),
    Run(5, APONTA, "api", OPUS),
    Run(6, APONTA, "claude_code", OPUS),
    Run(7, HISTORIA, "claude_code", FABLE),
)


class CappedMeter:
    """O medidor das mãos de fora com o teto da corrida: acima dele, a porta recusa a chamada
    seguinte (o `assert_priced` diz que não), e a sessão termina com o motivo."""

    def __init__(self, inner: CallMeter, spent: Callable[[], float], cap: float) -> None:
        self._inner = inner
        self._spent = spent
        self._cap = cap

    def assert_priced(self, model: str) -> None:
        if self._spent() >= self._cap:
            raise LookupError(f"o teto da corrida: US$ {self._cap:.2f}")
        self._inner.assert_priced(model)

    async def observed(
        self, request: ModelRequest, response: ModelResponse, *, harness: str
    ) -> float:
        return await self._inner.observed(request, response, harness=harness)


def _tool(name: str) -> list[str]:
    """Uma ferramenta do ambiente deste repositório (o ruff, o pyright)."""
    return [str(Path(sys.executable).parent / name)]


def _changed_py(space: Path, files: Sequence[str]) -> list[str]:
    return [f for f in files if f.endswith(".py") and (space / f).is_file()]


def _pyright_scope(space: Path) -> tuple[list[str], list[str]]:
    """O que o `pyright` do projeto olha (o `include` e o `exclude` do pyproject do espaço)."""
    doc = tomllib.loads((space / "pyproject.toml").read_text(encoding="utf-8"))
    config = cast(Mapping[str, Any], doc.get("tool", {}).get("pyright", {}))
    include = [str(p) for p in cast(Sequence[Any], config.get("include") or ["."])]
    exclude = [str(p) for p in cast(Sequence[Any], config.get("exclude") or ())]
    return include, exclude


def _covered(path: str, include: Sequence[str], exclude: Sequence[str]) -> bool:
    inside = any(path == p or path.startswith(p.rstrip("/") + "/") or p == "." for p in include)
    return inside and not any(fnmatch.fnmatch(path, p) or path.startswith(p) for p in exclude)


def static_checks(space: Path, files: Sequence[str]) -> dict[str, Any]:
    """O `ruff` e o `pyright` estrito nos .py mudados, como o CI: o `pyright` só nos que a
    configuração do projeto cobre (o CI não olha `tools/robos`). Não rodam o código do dev."""
    targets = _changed_py(space, files)
    if not targets:
        return {"ruff": True, "pyright": True, "files": [], "pyright_files": []}
    ruff = subprocess.run(
        [*_tool("ruff"), "check", "--no-cache", *targets],
        cwd=space,
        capture_output=True,
        text=True,
        check=False,
    )
    fmt = subprocess.run(
        [*_tool("ruff"), "format", "--check", "--no-cache", *targets],
        cwd=space,
        capture_output=True,
        text=True,
        check=False,
    )
    include, exclude = _pyright_scope(space)
    typed = [t for t in targets if _covered(t, include, exclude)]
    pyright_ok, pyright_out = True, "fora do pyright do projeto"
    if typed:
        pyright = subprocess.run(
            [*_tool("pyright"), "--pythonpath", str(space / ".venv" / "bin" / "python"), *typed],
            cwd=space,
            capture_output=True,
            text=True,
            check=False,
        )
        pyright_ok, pyright_out = pyright.returncode == 0, pyright.stdout[-1500:]
    return {
        "ruff": ruff.returncode == 0 and fmt.returncode == 0,
        "pyright": pyright_ok,
        "files": targets,
        "pyright_files": typed,
        "ruff_out": (ruff.stdout + fmt.stdout)[-1500:],
        "pyright_out": pyright_out,
    }


def test_paths(files: Sequence[str]) -> list[str]:
    """Os testes que a conferência roda: os da bancada e as pastas de teste que o patch mudou."""
    paths = ["tools/robos/tests"]
    for name in files:
        parts = Path(name).parts
        if "tests" in parts and name.endswith(".py"):
            folder = str(Path(*parts[: parts.index("tests") + 1]))
            if folder not in paths:
                paths.append(folder)
    return paths


async def check(space: Workspace, root: Path, files: Sequence[str]) -> dict[str, Any]:
    """A conferência por fora: o CI de perto (o estático e os testes, sob o sandbox da oficina)."""
    found: dict[str, Any] = {"static": static_checks(root, files)}
    runs = [(path, await space.run_tests(path)) for path in test_paths(files)]
    found["bench_tests"] = {
        "ok": all(result.ok for _, result in runs),
        "summary": "; ".join(f"{path}: {result.summary}" for path, result in runs),
    }
    return found


async def recheck(folder: Path) -> None:
    """Refaz a conferência por fora das corridas da pasta, sem a API (o aceite fica)."""
    for child in sorted(folder.iterdir()):
        result_file = child / "resultado.json"
        space_root = child / "oficina" / WORLD / TICKET_ID
        if not result_file.is_file() or not space_root.is_dir():
            continue
        result = json.loads(result_file.read_text(encoding="utf-8"))
        hidden = space_root / HIDDEN
        hidden.unlink(missing_ok=True)  # o aceite escondido não entra nos testes da bancada
        workshop = LocalWorkshop(REPO, child / "oficina", python_env=True)
        space = await workshop.open(WORLD, TICKET_ID)
        result.update(await check(space, space_root, [str(f) for f in result["files"]]))
        result_file.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{child.name}: {result['bench_tests']['summary']}", flush=True)


def _facts(pipeline: Pipeline) -> list[dict[str, Any]]:
    return [dict(e) for e in pipeline.envelopes if str(e["type"]).startswith(FACTS)]


def _of(facts: Sequence[Mapping[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [dict(f["data"]) for f in facts if f["type"] == f"campsverso.{kind}"]


async def run_one(run: Run, out: Path, commit: str) -> dict[str, Any]:
    """Uma corrida: o pedido pelas mãos e o modelo dela, do quadro à entrega, e a conferência."""
    out.mkdir(parents=True, exist_ok=True)
    env = load_env(ENV)
    clock = SystemWallClock()
    key = os.environ.get(ANTHROPIC_KEY, "")
    holder: dict[str, Pipeline] = {}

    def spent() -> float:
        pipeline = holder.get("pipeline")
        if pipeline is None:
            return 0.0
        calls = pipeline.of_type("llm.call.completed.v1")
        return sum(float(c["cost_usd"]) for c in calls if c["charged"])

    api = model_port(run.model, routes=env.routes, clock=clock)
    capped = Capped(api, CAP_USD)
    port: ModelPort = RecordingModel(capped, out / "nosso.jsonl", "record", clock=clock)

    def hands(meter: CallMeter) -> Mapping[str, Hands]:
        return {
            "claude_code": ClaudeCodeHands(
                CappedMeter(meter, spent, CAP_USD),
                api_key=key,
                home=out / "maos",
                tape=out / "claude-code.jsonl",
                tape_mode="record",
                warn=lambda event, fields: print(f"{event}: {dict(fields)}", file=sys.stderr),
            )
        }

    ticket = run.ticket
    pipeline = Pipeline(
        controller="llm",
        port=port,
        cartridge=OFFICE,
        workshop_repo=REPO,
        workshop_root=out / "oficina",
        python_env=True,
        model=run.model,
        hands=hands,
        helper_config={
            "gerente": {
                "tickets": [
                    {
                        "at": "09:30",
                        "title": ticket.title,
                        "description": ticket.description,
                        "acceptance": ticket.acceptance,
                        "size": ticket.size,
                        "harness": run.harness,
                        "model": run.model,
                    }
                ]
            }
        },
    )
    holder["pipeline"] = pipeline
    capped.pipeline = pipeline
    started = time.monotonic()
    try:
        await pipeline.start()
        end = pipeline.core.tick + pipeline.day
        while not pipeline.of_type("workshop.session_finished.v1"):
            if pipeline.core.tick >= end:
                break
            await pipeline.run_until(pipeline.core.tick + pipeline.day // 96)
        # A entrega (ou a fala com o motivo) sai na decisão seguinte.
        await pipeline.run_until(pipeline.core.tick + pipeline.day // 96)
    finally:
        await api.aclose()
    seconds = time.monotonic() - started
    facts = _facts(pipeline)
    with (out / "fatos.jsonl").open("w", encoding="utf-8") as handle:
        for fact in facts:
            handle.write(json.dumps(fact, ensure_ascii=False) + "\n")
    space = out / "oficina" / WORLD / TICKET_ID
    base = subprocess.run(
        ["git", "-C", str(space), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    delivered = _of(facts, "office.ticket.delivered.v1")
    patch = dict(delivered[0].get("patch") or {}) if delivered else {}
    blob = next((v for k, v in pipeline.deliveries.blobs.items() if k.endswith(".patch")), b"")
    (out / "entrega.patch").write_bytes(blob)
    files = [str(f) for f in patch.get("files") or ()]
    result: dict[str, Any] = {
        "run": run.number,
        "ticket": ticket.slug,
        "harness": run.harness,
        "model": run.model,
        "commit": commit,
        "base": base,
        "same_commit": base == commit,
        "wall_seconds": round(seconds, 1),
        "delivered": bool(delivered),
        "files": files,
        "added": int(patch.get("added") or 0),
        "removed": int(patch.get("removed") or 0),
        "spent_usd": round(spent(), 4),
    }
    if space.is_dir():
        workshop = LocalWorkshop(REPO, out / "oficina", python_env=True)
        opened: Workspace = await workshop.open(WORLD, TICKET_ID)
        result.update(await check(opened, space, files))
        await opened.write(HIDDEN, ticket.hidden)
        hidden = await opened.run_tests(HIDDEN)
        result["acceptance"] = {"ok": hidden.ok, "summary": hidden.summary, "text": hidden.text}
    (out / "resultado.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def headline(result: Mapping[str, Any], facts: Sequence[Mapping[str, Any]]) -> str:
    finished = _of(facts, "workshop.session_finished.v1")
    end = finished[-1] if finished else {}
    robots = Counter(str(c["robot_id"]) for c in _of(facts, "workshop.robot_called.v1"))
    accepted = dict(result.get("acceptance") or {}).get("ok")
    return (
        f"{result['run']} {result['ticket']} {result['harness']} {result['model']}: "
        f"{'entregou' if result['delivered'] else 'não entregou'} ({end.get('reason', '?')}), "
        f"{end.get('turns', '?')} voltas, {end.get('steps', '?')} passos, "
        f"US$ {result['spent_usd']:.3f}, {result['wall_seconds']:.0f} s, robôs {dict(robots)}, "
        f"aceite {'sim' if accepted else 'não'}"
    )


# ---------------------------------------------------------------- o relatório

REPORT = REPO / "docs" / "arena" / "m26-as-maos.md"
BEGIN = "<!-- tabela: make maos-relatorio -->"
END = "<!-- /tabela -->"
HANDS_NAME = {"api": "nosso harness", "claude_code": "Claude Code"}


def _load(folder: Path) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    result_file, facts_file = folder / "resultado.json", folder / "fatos.jsonl"
    if not result_file.is_file() or not facts_file.is_file():
        return None
    facts = [
        json.loads(line) for line in facts_file.read_text(encoding="utf-8").splitlines() if line
    ]
    return json.loads(result_file.read_text(encoding="utf-8")), facts


def _yes(value: object) -> str:
    return "sim" if value else "não"


def _num(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def row(result: Mapping[str, Any], facts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Uma corrida em números, lida dos fatos (a sessão, os passos, os robôs, a entrega) e da
    conferência por fora (o CI de perto e o aceite)."""
    finished = _of(facts, "workshop.session_finished.v1")
    end = finished[-1] if finished else {}
    tools = Counter(str(s["tool"]) for s in _of(facts, "workshop.step.v2"))
    robots = Counter(str(c["robot_id"]) for c in _of(facts, "workshop.robot_called.v1"))
    static = dict(result.get("static") or {})
    bench = dict(result.get("bench_tests") or {})
    ci = bool(static.get("ruff")) and bool(static.get("pyright")) and bool(bench.get("ok"))
    return {
        "run": result["run"],
        "ticket": result["ticket"],
        "harness": HANDS_NAME.get(str(result["harness"]), str(result["harness"])),
        "model": str(result["model"]).removeprefix("claude-"),
        "delivered": bool(result["delivered"]),
        "reason": str(end.get("reason", "?")),
        "turns": int(end.get("turns", 0)),
        "steps": int(end.get("steps", 0)),
        "tester": robots.get("robo-testador", 0),
        "bash": tools.get("Bash", 0),
        "cost": float(end.get("cost_usd", result.get("spent_usd", 0.0))),
        "minutes": int(end.get("duration_ms", 0)) / 60000,
        "files": len(result.get("files") or ()),
        "added": int(result.get("added", 0)),
        "removed": int(result.get("removed", 0)),
        "ruff": bool(static.get("ruff")),
        "pyright": bool(static.get("pyright")),
        "bench": bool(bench.get("ok")),
        "ci": ci,
        "accepted": bool(dict(result.get("acceptance") or {}).get("ok")),
        "same_commit": bool(result.get("same_commit")),
        "tools": dict(sorted(tools.items())),
    }


def table(rows: Sequence[Mapping[str, Any]]) -> str:
    """A tabela lado a lado, em Markdown, e o total."""
    lines = [
        "| # | Pedido | Mãos | Modelo | Entregou | Voltas | Passos | Testador | Custo | Tempo "
        "| Patch | CI de perto | Aceite |",
        "|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for r in rows:
        ci = (
            "sim"
            if r["ci"]
            else (
                f"não (ruff {_yes(r['ruff'])}, pyright {_yes(r['pyright'])}, "
                f"bancada {_yes(r['bench'])})"
            )
        )
        delivered = "sim" if r["delivered"] else f"não ({r['reason']})"
        lines.append(
            f"| {r['run']} | {r['ticket']} | {r['harness']} | {r['model']} | {delivered} "
            f"| {r['turns']} | {r['steps']} | {r['tester']} | US$ {_num(r['cost'])} "
            f"| {_num(r['minutes'], 1)} min | {r['files']} arq., +{r['added']} -{r['removed']} "
            f"| {ci} | {_yes(r['accepted'])} |"
        )
    total = sum(float(r["cost"]) for r in rows)
    lines.append("")
    runs = "corrida" if len(rows) == 1 else "corridas"
    lines.append(f"**Total:** {len(rows)} {runs}, US$ {_num(total)}.")
    lines.append("")
    lines.append("**As ferramentas de cada corrida**, pelos passos (`workshop.step.v2`):")
    lines.append("")
    for r in rows:
        used = ", ".join(f"{name} {count}" for name, count in r["tools"].items()) or "nenhuma"
        lines.append(f"- {r['run']} ({r['ticket']}, {r['harness']}, {r['model']}): {used}.")
    return "\n".join(lines) + "\n"


def write_report(folder: Path, target: Path = REPORT) -> str:
    """A tabela das corridas da pasta, entre os marcadores do relatório; o texto fora deles fica."""
    rows: list[dict[str, Any]] = []
    runs = [c for c in folder.iterdir() if c.is_dir() and c.name.split("-", 1)[0].isdigit()]
    for child in sorted(runs, key=lambda p: int(p.name.split("-", 1)[0])):
        loaded = _load(child)
        if loaded is not None:
            rows.append(row(*loaded))
    block = f"{BEGIN}\n\n{table(rows)}\n{END}"
    if target.is_file() and BEGIN in (text := target.read_text(encoding="utf-8")):
        before, rest = text.split(BEGIN, 1)
        after = rest.split(END, 1)[1] if END in rest else ""
        target.write_text(before + block + after, encoding="utf-8")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# A comparação das mãos\n\n{block}\n", encoding="utf-8")
    return block


async def run(selected: Sequence[int], out: Path) -> int:
    if not os.environ.get(ANTHROPIC_KEY):
        print(f"{ANTHROPIC_KEY} ausente: rode com --env-file .env (ADR-0058)", file=sys.stderr)
        return 2
    commit = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    print(f"a comparação no commit {commit[:12]}, em {out}", flush=True)
    for item in RUNS:
        if selected and item.number not in selected:
            continue
        folder = out / item.label
        print(f"{item.label}: correndo...", flush=True)
        result = await run_one(item, folder, commit)
        facts = [
            json.loads(line)
            for line in (folder / "fatos.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]
        print(headline(result, facts), flush=True)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.maos")
    parser.add_argument("--so", default="", help="as corridas, por número: 1,2")
    parser.add_argument("--out", type=Path, help="padrão: data/maos/<data>")
    parser.add_argument(
        "--relatorio", action="store_true", help="só a tabela do relatório, lida da pasta"
    )
    parser.add_argument(
        "--reconferir", action="store_true", help="refaz a conferência por fora, sem a API"
    )
    args = parser.parse_args(argv)
    selected = [int(x) for x in str(args.so).split(",") if x.strip()]
    out = args.out or REPO / "data" / "maos" / datetime.now(UTC).strftime("%Y%m%d")
    if args.reconferir:
        asyncio.run(recheck(out))
        return 0
    if args.relatorio:
        print(write_report(out), flush=True)
        return 0
    return asyncio.run(run(selected, out))


if __name__ == "__main__":
    sys.exit(main())
