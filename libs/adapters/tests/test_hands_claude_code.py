"""As mãos do Claude Code (ADR-0089): os ganchos, o lançador com o ambiente limpo, o cercado do
macOS e uma sessão do Claude Code de verdade contra o modelo falso, sem a API."""

import asyncio
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import httpx2
import pytest

from campsverso_adapters.hands_claude_code import (
    ClaudeCodeHands,
    bundled_cli,
    launcher,
    refusal,
    sandbox_profile,
    step_of,
)
from campsverso_adapters.model_fake_http import FakeModel, text, use
from campsverso_ports import (
    HandsJob,
    HandsLimits,
    HandsStep,
    ModelRequest,
    ModelResponse,
    Robot,
    ToolResult,
    Workspace,
)

MACOS = pytest.mark.skipif(sys.platform != "darwin", reason="o sandbox-exec é do macOS")


# ------------------------------------------------------------------ os ganchos


@pytest.fixture
def space(tmp_path: Path) -> Path:
    root = tmp_path / "espaco"
    (root / ".git").mkdir(parents=True)
    (root / "app.py").write_text("print('oi')\n")
    return root


def test_as_ferramentas_de_arquivo_so_aceitam_caminhos_do_espaco(
    space: Path, tmp_path: Path
) -> None:
    assert refusal(space, "Read", {"file_path": str(space / "app.py")}) is None
    assert refusal(space, "Edit", {"file_path": "app.py"}) is None
    assert refusal(space, "Glob", {"pattern": "**/*.py"}) is None
    assert refusal(space, "Grep", {"pattern": "oi", "path": "."}) is None
    assert refusal(space, "Read", {"file_path": "/etc/passwd"}) is not None
    assert refusal(space, "Write", {"file_path": "../fora.txt"}) is not None
    assert refusal(space, "Read", {"file_path": str(space / ".git" / "config")}) is not None
    assert refusal(space, "Glob", {"pattern": "/Users/**/.env"}) is not None
    (tmp_path / "segredo.txt").write_text("x")
    (space / "atalho").symlink_to(tmp_path / "segredo.txt")
    assert refusal(space, "Read", {"file_path": "atalho"}) is not None


def test_o_bash_recusa_a_rede_o_git_para_fora_e_os_alvos_que_chamam_a_api(space: Path) -> None:
    for command in (
        "git push origin dev/pedido-7",
        "cd x && git fetch",
        "curl https://example.com",
        "make corrida DIAS=1",
        "make -s arena",
        "uv run make fita",
        "echo a; ssh host",
    ):
        assert refusal(space, "Bash", {"command": command}) is not None, command
    for command in (
        "uv run --offline pytest tools/robos",
        "python -m pytest -q",
        "git diff --stat",
        "git status",
        "ruff check .",
        "make check",
    ):
        assert refusal(space, "Bash", {"command": command}) is None, command


def test_ferramentas_fora_da_lista_sao_recusadas_e_as_do_mundo_passam(space: Path) -> None:
    assert refusal(space, "WebFetch", {"url": "https://example.com"}) is not None
    assert refusal(space, "Task", {"prompt": "x"}) is not None
    assert refusal(space, "mcp__oficina__chamar_robo", {"nome": "testador"}) is None
    assert refusal(space, "mcp__oficina__anotar", {"texto": "x"}) is None


def test_o_passo_diz_a_ferramenta_o_caminho_e_a_recusa(space: Path) -> None:
    ok = step_of("Edit", {"file_path": str(space / "app.py")}, "feito", False, space, 12)
    assert ok == HandsStep("Edit", "Edit: app.py", True, 12, "app.py")
    bash = step_of(
        "Bash", {"command": "pytest -q", "description": "Roda os testes"}, "", False, space, 5
    )
    assert bash.summary == "Bash: Roda os testes"
    denied = step_of("Read", {"file_path": "/etc/passwd"}, "o caminho fica fora", True, space, 1)
    assert not denied.ok
    assert "recusado" in denied.summary
    robot = step_of("mcp__oficina__chamar_robo", {"nome": "testador"}, "ok", False, space, 3)
    assert (robot.tool, robot.summary) == ("chamar_robo", "chamar_robo: robô testador")


# ------------------------------------------------------------------ o lançador


def _fake_cli(folder: Path, body: str) -> Path:
    cli = folder / "claude-falso"
    cli.write_text(f"#!/bin/sh\n{body}\n")
    cli.chmod(0o755)
    return cli


def test_o_lancador_abre_um_ambiente_limpo_sem_os_segredos_do_controlador(tmp_path: Path) -> None:
    cli = _fake_cli(tmp_path, "env")
    script = tmp_path / "claude.sh"
    script.write_text(launcher(cli, {"HOME": str(tmp_path), "ANTHROPIC_API_KEY": "sessao-x"}, None))
    script.chmod(0o755)
    env = {
        "PATH": os.environ["PATH"],
        "ANTHROPIC_API_KEY": "chave-de-verdade",
        "OPENROUTER_API_KEY": "outra-chave",
        "NATS_PASSWORD": "senha",
        "CLAUDE_CODE_ENTRYPOINT": "sdk-py",
    }
    out = subprocess.run(
        [str(script), "--version"], env=env, capture_output=True, text=True, check=True
    )
    seen = dict(line.split("=", 1) for line in out.stdout.splitlines() if "=" in line)
    assert seen["ANTHROPIC_API_KEY"] == "sessao-x"
    assert seen["CLAUDE_CODE_ENTRYPOINT"] == "sdk-py"
    assert "OPENROUTER_API_KEY" not in seen
    assert "NATS_PASSWORD" not in seen
    assert "CLAUDE_AGENT_SDK_VERSION" not in seen  # o que não existe não passa nem vazio


@MACOS
def test_o_cercado_nega_a_leitura_da_casa_a_escrita_fora_e_a_rede(tmp_path: Path) -> None:
    home = (tmp_path / "casa").resolve()
    secret = home / ".env"
    home.mkdir()
    secret.write_text("SEGREDO=isca\n")
    root = (home / "espaco").resolve()
    root.mkdir()
    outside = home / "fora.txt"
    bin_dir = tmp_path / "bin"  # fora da casa: o que se libera para ler é só o Claude Code
    bin_dir.mkdir()
    cli = _fake_cli(
        bin_dir,
        f"cat {secret} && echo leu; echo x > {outside} && echo escreveu; "
        f"echo dentro > {root}/ok.txt && echo dentro; "
        "/usr/bin/curl -s -m 3 -o /dev/null https://example.com && echo rede",
    )
    profile = tmp_path / "perfil.sb"
    profile.write_text(sandbox_profile(root, "1", home, [cli.parent.resolve()]))
    script = tmp_path / "claude.sh"
    script.write_text(launcher(cli, {"HOME": str(root)}, profile))
    script.chmod(0o755)
    out = subprocess.run([str(script)], capture_output=True, text=True, timeout=30, check=False)
    assert "leu" not in out.stdout
    assert "escreveu" not in out.stdout
    assert "rede" not in out.stdout
    assert "dentro" in out.stdout
    assert not outside.exists()
    assert (root / "ok.txt").read_text() == "dentro\n"


# ------------------------------------------------------------------ uma sessão de verdade


class Meter:
    def __init__(self) -> None:
        self.calls: list[tuple[ModelRequest, ModelResponse, str]] = []

    def assert_priced(self, model: str) -> None:
        return None

    async def observed(
        self, request: ModelRequest, response: ModelResponse, *, harness: str
    ) -> float:
        self.calls.append((request, response, harness))
        return 0.001


class World:
    def __init__(self) -> None:
        self.steps: list[HandsStep] = []
        self.robots_called: list[tuple[str, list[str]]] = []
        self.notes: list[str] = []
        self.stop = False

    @property
    def robots(self) -> Sequence[Robot]:
        return [Robot("testador", "roda as verificações dos arquivos mudados")]

    async def robot(self, name: str, args: Sequence[str]) -> ToolResult:
        self.robots_called.append((name, list(args)))
        return ToolResult(True, "1 passaram", "testador: 1 passaram")

    async def note(self, text: str) -> ToolResult:
        self.notes.append(text)
        return ToolResult(True, "anotado", "anotado")

    async def step(self, step: HandsStep) -> None:
        self.steps.append(step)

    def should_stop(self) -> bool:
        return self.stop


class Space:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.ticket_id = "pedido-7"
        self.base = "0" * 40


def _job(**limits: Any) -> HandsJob:
    return HandsJob(
        ticket_id="pedido-7",
        opening="Pedido 7: um arquivo ola.py que imprime olá.",
        system="Você é o Camps, o dev do escritório.",
        model="claude-opus-5-5",
        avatar_id="camps",
        limits=HandsLimits(**limits),
    )


def _hands(fake: FakeModel, meter: Meter, home: Path, **kwargs: Any) -> ClaudeCodeHands:
    return ClaudeCodeHands(
        meter,
        api_key="chave-de-verdade",
        home=home,
        upstream="http://modelo-falso",
        transport=httpx2.ASGITransport(app=fake.app()),
        **kwargs,
    )


@pytest.fixture
def cli() -> Path:
    try:
        return bundled_cli()
    except FileNotFoundError:
        pytest.skip("o SDK veio sem o Claude Code nesta plataforma")


async def test_uma_sessao_do_claude_code_escreve_no_espaco_chama_o_robo_e_termina(
    cli: Path, tmp_path: Path
) -> None:
    root = (tmp_path / "espaco").resolve()
    root.mkdir()
    fake = FakeModel(
        [
            use("Write", file_path=str(root / "ola.py"), content="print('olá')\n"),
            use("Read", file_path="/etc/hosts"),
            use("mcp__oficina__chamar_robo", nome="testador", argumentos=["ola.py"]),
            use("mcp__oficina__anotar", texto="o pedido 7 era só um arquivo"),
            text("Pronto: escrevi o ola.py."),
        ]
    )
    meter, world = Meter(), World()
    hands = _hands(fake, meter, tmp_path / "maos", cli=cli)
    result = await asyncio.wait_for(hands.run(cast(Workspace, Space(root)), _job(), world), 180)

    assert result.done, result
    assert result.reason == "pronto"
    assert result.summary == "Pronto: escrevi o ola.py."
    assert (root / "ola.py").read_text() == "print('olá')\n"
    assert [s.tool for s in world.steps] == ["Write", "Read", "chamar_robo", "anotar"]
    assert [s.ok for s in world.steps] == [True, False, True, True]
    assert "fora do espaço" in world.steps[1].summary  # o gancho recusou, com o motivo
    assert world.robots_called == [("testador", ["ola.py"])]
    assert world.notes == ["o pedido 7 era só um arquivo"]
    # Todas as chamadas passaram pela porta, medidas, com a chave de verdade só na de fora.
    assert fake.used == 5
    assert meter.calls
    assert {h for _, _, h in meter.calls} == {"claude_code"}
    assert {r.ticket_id for r, _, _ in meter.calls} == {"pedido-7"}
    assert {s["headers"]["x-api-key"] for s in fake.seen} == {"chave-de-verdade"}
    tools = {t["name"] for t in fake.seen[0]["body"]["tools"]}
    assert {"Read", "Write", "Edit", "Bash", "Glob", "Grep"} <= tools
    assert not tools & {"WebFetch", "WebSearch", "Task", "Agent"}
    assert {"mcp__oficina__chamar_robo", "mcp__oficina__anotar"} <= tools
    (session,) = (tmp_path / "maos" / "pedido-7").glob("sessao-*.jsonl")
    assert "ResultMessage" in session.read_text()


async def test_acima_do_teto_a_sessao_para_e_diz_o_motivo(cli: Path, tmp_path: Path) -> None:
    root = (tmp_path / "espaco").resolve()
    root.mkdir()
    fake = FakeModel([use("Read", file_path="app.py"), text("fim")])
    meter, world = Meter(), World()
    world.stop = True  # a guarda já disse que o pedido estourou
    hands = _hands(fake, meter, tmp_path / "maos", cli=cli)
    result = await asyncio.wait_for(hands.run(cast(Workspace, Space(root)), _job(), world), 180)
    assert not result.done
    assert result.reason == "parada"  # o mesmo motivo do nosso harness
    assert fake.seen == []  # nenhuma chamada passou da porta
