"""As mãos do Codex (ADR-0089, decisão 11): uma sessão com um Codex falso que imprime o exemplo do
`codex exec --json`, os passos, o custo pela tabela, os limites e o ambiente sem chaves."""

import asyncio
import json
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from campsverso_adapters.hands_codex import (
    GRACE_SECONDS,
    CodexHands,
    CodexUsage,
    clean_environment,
    codex_cost_usd,
    resolve_command,
    steps_of,
)
from campsverso_adapters.model_metered import ModelPrices
from campsverso_ports import HandsJob, HandsLimits, HandsStep, Robot, ToolResult, Workspace

FAKE = Path(__file__).parents[3] / "tests" / "fixtures" / "codex" / "codex_falso.py"
MODEL = "gpt-codex-teste"
PRICES = {MODEL: ModelPrices(1.0, 10.0, 0.1, 2.0)}


class World:
    def __init__(self, stop_after: int | None = None) -> None:
        self.steps: list[HandsStep] = []
        self.stop_after = stop_after

    @property
    def robots(self) -> Sequence[Robot]:
        return []

    async def robot(self, name: str, args: Sequence[str]) -> ToolResult:
        return ToolResult(False, "sem bancada", "sem bancada")

    async def note(self, text: str) -> ToolResult:
        return ToolResult(False, "sem memória", "sem memória")

    async def step(self, step: HandsStep) -> None:
        self.steps.append(step)

    def should_stop(self) -> bool:
        return self.stop_after is not None and len(self.steps) >= self.stop_after


class Space:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.ticket_id = "pedido-2"
        self.base = "0" * 40


@pytest.fixture
def space(tmp_path: Path) -> Space:
    root = tmp_path / "espaco"
    root.mkdir()
    return Space(root)


def _job(**limits: Any) -> HandsJob:
    return HandsJob(
        ticket_id="pedido-2",
        opening="Pedido 2: o robô eco.",
        system="Você é o Camps.",
        model=MODEL,
        avatar_id="camps",
        limits=HandsLimits(**limits),
    )


def _hands(*options: str) -> CodexHands:
    return CodexHands(PRICES, command=(sys.executable, str(FAKE), *options))


def _run(hands: CodexHands, space: Space, world: World, **limits: Any) -> Any:
    return asyncio.run(hands.run(cast(Workspace, space), _job(**limits), world))


def test_uma_sessao_vira_os_passos_na_ordem(space: Space) -> None:
    world = World()
    result = _run(_hands(), space, world)
    assert [(s.tool, s.path, s.ok) for s in world.steps] == [
        ("command_execution", None, True),
        ("command_execution", None, True),
        ("file_change", "tools/robos/eco.py", True),
        ("file_change", "tools/robos/tests/test_eco.py", True),
        ("command_execution", None, False),
        ("file_change", "tools/robos/eco.py", True),
        ("command_execution", None, True),
    ]
    assert "ls tools/robos" in world.steps[0].summary
    assert result.done
    assert result.reason == "pronto"
    assert result.steps == 7
    assert result.turns == 7  # seis itens de ferramenta e a mensagem final
    assert result.summary.startswith("Escrevi o robô tools/robos/eco.py")


def test_o_custo_sai_dos_tokens_pela_tabela(space: Space) -> None:
    result = _run(_hands(), space, World())
    # 48213 de entrada, 41984 do cache: 6229 frescos; 1873 de saída, o raciocínio dentro dela.
    expected = round((6229 * 1.0 + 41984 * 0.1 + 1873 * 10.0) / 1_000_000, 8)
    assert result.cost_usd == expected


def test_o_custo_conta_o_cache_e_o_raciocinio_uma_vez_so() -> None:
    usage = CodexUsage().plus(
        {"input_tokens": 1000, "cached_input_tokens": 600, "output_tokens": 100}
    )
    usage = usage.plus({"input_tokens": 1000, "cache_write_input_tokens": 400})
    assert usage.input_tokens == 2000
    prices = ModelPrices(1.0, 10.0, 0.1, 2.0)
    assert codex_cost_usd(usage, prices) == round((1000 + 60 + 800 + 1000) / 1_000_000, 8)


def test_um_modelo_sem_preco_e_recusado_antes_de_abrir_o_codex(space: Space) -> None:
    hands = CodexHands({}, command=(sys.executable, str(FAKE)))
    with pytest.raises(ValueError, match="preço"):
        asyncio.run(hands.run(cast(Workspace, space), _job(), World()))


def test_uma_sessao_que_passa_do_limite_de_tempo_e_parada(space: Space) -> None:
    world = World()
    result = _run(_hands("--dorme", "30"), space, world, max_seconds=0.5)
    assert not result.done
    assert result.reason == "limite de tempo"
    assert world.steps == []


def test_a_sessao_para_no_limite_de_voltas(space: Space) -> None:
    world = World()
    result = _run(_hands(), space, world, max_turns=2)
    assert not result.done
    assert result.reason == "limite de voltas"
    assert len(world.steps) == 2


def test_a_sessao_para_quando_o_mundo_pede(space: Space) -> None:
    world = World(stop_after=1)
    result = _run(_hands(), space, world)
    assert not result.done
    assert result.reason == "parada"
    assert len(world.steps) == 1


def test_o_ambiente_do_processo_nao_tem_chave(
    space: Space, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-de-verdade")
    monkeypatch.setenv("OPENAI_API_KEY", "outra-chave")
    monkeypatch.setenv("GITHUB_TOKEN", "um-token")
    dump = tmp_path / "ambiente.json"
    briefing = tmp_path / "entrada.txt"
    _run(_hands("--ambiente", str(dump), "--entrada", str(briefing)), space, World())
    seen: dict[str, str] = json.loads(dump.read_text(encoding="utf-8"))
    assert [k for k in seen if "KEY" in k.upper() or "TOKEN" in k.upper()] == []
    assert "chave-de-verdade" not in seen.values()
    assert seen["HOME"].startswith(str(space.root))
    assert briefing.read_text(encoding="utf-8") == "Você é o Camps.\n\nPedido 2: o robô eco."


def test_o_ambiente_limpo_nao_herda_nada(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "x")
    environment = clean_environment(tmp_path)
    assert set(environment) == {
        "PATH",
        "HOME",
        "CODEX_HOME",
        "TMPDIR",
        "LANG",
        "PYTHONDONTWRITEBYTECODE",
    }


def test_os_passos_aceitam_o_caminho_absoluto_e_ignoram_o_que_nao_e_ferramenta(
    tmp_path: Path,
) -> None:
    absolute = str(tmp_path / "a" / "b.py")
    item = {
        "type": "file_change",
        "status": "failed",
        "changes": [{"path": absolute, "kind": "add"}],
    }
    [step] = steps_of(item, tmp_path, 3)
    assert (step.path, step.ok, step.duration_ms) == ("a/b.py", False, 3)
    assert steps_of({"type": "reasoning", "text": "pensando"}, tmp_path, 0) == []
    assert steps_of({"type": "todo_list", "items": []}, tmp_path, 0) == []
    mcp = {"type": "mcp_tool_call", "server": "oficina", "tool": "anotar", "status": "completed"}
    assert steps_of(mcp, tmp_path, 0)[0].summary == "mcp_tool_call: oficina.anotar"


def test_o_limite_de_voltas_nao_corta_a_resposta_final(space: Space) -> None:
    # Seis ferramentas e a mensagem final: com sete voltas, a sessão acaba no turn.completed.
    world = World()
    result = _run(_hands(), space, world, max_turns=7)
    assert result.done
    assert result.reason == "pronto"
    assert result.cost_usd is not None
    assert result.cost_usd > 0


def test_parada_no_meio_ainda_conta_o_usage_que_chega(space: Space) -> None:
    result = _run(_hands(), space, World(), max_turns=2)
    assert result.reason == "limite de voltas"
    assert result.cost_usd == round((6229 * 1.0 + 41984 * 0.1 + 1873 * 10.0) / 1_000_000, 8)


def test_o_briefing_entra_dentro_do_limite_de_tempo(space: Space) -> None:
    # Um Codex que nunca lê a entrada: o briefing grande enche o cano, e o relógio para a sessão.
    hands = _hands("--sem-ler", "1")
    job = HandsJob(
        ticket_id="pedido-2",
        opening="x" * (4 * 1024 * 1024),
        system="",
        model=MODEL,
        avatar_id="camps",
        limits=HandsLimits(max_seconds=0.5),
    )
    began = time.monotonic()
    result = asyncio.run(hands.run(cast(Workspace, space), job, World()))
    assert result.reason == "limite de tempo"
    assert time.monotonic() - began < 15


def test_a_espera_do_fim_do_codex_fica_dentro_do_limite_de_tempo(space: Space) -> None:
    # O Codex fecha a saída depois do exemplo mas não sai: o relógio da sessão o para.
    began = time.monotonic()
    result = _run(_hands("--fica", "30"), space, World(), max_seconds=1.0)
    assert result.reason == "limite de tempo"
    assert not result.done
    assert time.monotonic() - began < GRACE_SECONDS


def _alive(pid: int) -> bool:
    """Vivo de verdade: um zumbi (já morto, à espera de quem o colha) não conta."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    state = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
    ).stdout.strip()
    return bool(state) and not state.startswith("Z")


def test_a_parada_encerra_o_grupo_de_processos(space: Space, tmp_path: Path) -> None:
    grandchild = tmp_path / "neto.txt"
    result = _run(
        _hands("--neto", str(grandchild), "--dorme", "30"), space, World(), max_seconds=1.0
    )
    assert result.reason == "limite de tempo"
    pid = int(grandchild.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 5
    while _alive(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _alive(pid)


def _program(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    program = folder / "codex"
    program.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    program.chmod(0o755)
    return program


def test_o_codex_vem_do_path_de_quem_chama_e_nao_do_espaco(
    space: Space, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    planted = _program(space.root / ".venv" / "bin")
    real = _program(tmp_path / "fora")
    monkeypatch.setenv("PATH", str(real.parent))
    assert resolve_command(("codex", "--x"), space.root) == [str(real), "--x"]
    assert str(planted) not in resolve_command(("codex",), space.root)


def test_um_codex_dentro_do_espaco_ou_ausente_e_recusado(
    space: Space, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    planted = _program(space.root / "bin")
    monkeypatch.setenv("PATH", str(planted.parent))
    with pytest.raises(ValueError, match="espaço"):
        resolve_command(("codex",), space.root)
    monkeypatch.setenv("PATH", str(tmp_path / "vazio"))
    with pytest.raises(FileNotFoundError):
        resolve_command(("codex",), space.root)
