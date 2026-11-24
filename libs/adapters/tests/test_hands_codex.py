"""As mãos do Codex (ADR-0089, decisão 11; ADR-0093): uma sessão com um Codex falso que imprime o
exemplo do `codex exec --json` e chama o modelo pela porta das mãos, como o de verdade, diante de um
provedor falso da OpenAI. Os passos, o custo medido pela porta, os tetos (o da sessão também na
porta), o ambiente sem chaves, o `config.toml` da sessão e o cercado."""

import asyncio
import json
import os
import subprocess
import sys
import time
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import httpx2
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from campsverso_adapters.hands_codex import (
    SESSION_VARIABLE,
    CodexHands,
    CodexStream,
    CodexUsage,
    clean_environment,
    codex_config,
    resolve_command,
    shown_command,
    steps_of,
)
from campsverso_adapters.hands_fence import readable_for
from campsverso_adapters.hands_process import GRACE_SECONDS
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

FAKE = Path(__file__).parents[3] / "tests" / "fixtures" / "codex" / "codex_falso.py"
MODEL = "gpt-6.2-astra"
PRICED = "openai/gpt-6.2-astra"
KEY = "chave-de-verdade"
PRICES = {PRICED: (8.0, 40.0)}
# Cada chamada do provedor falso: 1000 de entrada, 400 delas do cache, e 200 de saída.
PER_CALL = (600 * 8.0 + 200 * 40.0) / 1_000_000
# O exemplo tem nove itens, e o falso chama o modelo antes de cada um.
CALLS = 9
MACOS = pytest.mark.skipif(sys.platform != "darwin", reason="o sandbox-exec é do macOS")

RESPONSE_EVENTS: list[Mapping[str, Any]] = [
    {"type": "response.created", "response": {"id": "resp_1", "model": MODEL}},
    {
        "type": "response.output_item.done",
        "item": {"type": "function_call", "name": "shell", "arguments": '{"command": ["ls"]}'},
    },
    {
        "type": "response.completed",
        "response": {
            "id": "resp_1",
            "model": MODEL,
            "status": "completed",
            "usage": {
                "input_tokens": 1000,
                "input_tokens_details": {"cached_tokens": 400},
                "output_tokens": 200,
            },
        },
    },
]


class Meter:
    """O medidor dos testes: guarda o que a porta mediu e cobra pela tabela."""

    def __init__(self, prices: Mapping[str, tuple[float, float]] = PRICES) -> None:
        self.prices = dict(prices)
        self.calls: list[tuple[ModelRequest, ModelResponse, str]] = []

    def assert_priced(self, model: str) -> None:
        if model not in self.prices:
            raise LookupError(f"modelo sem preço na tabela do ambiente: {model}")

    async def observed(
        self, request: ModelRequest, response: ModelResponse, *, harness: str
    ) -> float:
        self.calls.append((request, response, harness))
        price_in, price_out = self.prices[request.model]
        usage = response.usage
        return (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1_000_000


class Provider:
    """A OpenAI falsa, atrás da porta: guarda os cabeçalhos e devolve sempre a mesma resposta."""

    def __init__(self) -> None:
        self.seen: list[dict[str, str]] = []
        self.body = b"".join(
            f"event: {e['type']}\ndata: {json.dumps(e)}\n\n".encode() for e in RESPONSE_EVENTS
        )

    def app(self) -> Starlette:
        async def handle(request: Request) -> Response:
            self.seen.append(dict(request.headers))
            return Response(self.body, media_type="text/event-stream")

        return Starlette(routes=[Route("/{path:path}", handle, methods=["GET", "POST"])])


@dataclass
class Kit:
    home: Path
    meter: Meter = field(default_factory=Meter)
    provider: Provider = field(default_factory=Provider)


@pytest.fixture
def kit(tmp_path: Path) -> Kit:
    return Kit(tmp_path / "sessoes")


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


def _job(model: str = MODEL, **limits: Any) -> HandsJob:
    return HandsJob(
        ticket_id="pedido-2",
        opening="Pedido 2: o robô eco.",
        system="Você é o Camps.",
        model=model,
        avatar_id="camps",
        limits=HandsLimits(**limits),
    )


def _hands(kit: Kit, *options: str, **kwargs: Any) -> CodexHands:
    kwargs.setdefault("sandbox", False)
    return CodexHands(
        kit.meter,
        api_key=KEY,
        home=kit.home,
        command=(sys.executable, str(FAKE), *options),
        upstream="http://provedor-falso",
        transport=httpx2.ASGITransport(app=kit.provider.app()),
        **kwargs,
    )


def _run(hands: CodexHands, space: Space, world: World, **limits: Any) -> Any:
    return asyncio.run(hands.run(cast(Workspace, space), _job(**limits), world))


def test_uma_sessao_vira_os_passos_na_ordem(space: Space, kit: Kit) -> None:
    world = World()
    result = _run(_hands(kit), space, world)
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


# ------------------------------------------------------------------ a porta


def test_o_modelo_passa_pela_porta_e_o_custo_e_o_que_ela_mediu(space: Space, kit: Kit) -> None:
    result = _run(_hands(kit, "--chama-porta", "1"), space, World())
    assert result.reason == "pronto"
    assert len(kit.meter.calls) == CALLS
    assert {(r.model, h, r.avatar_id, r.ticket_id) for r, _, h in kit.meter.calls} == {
        (PRICED, "codex", "camps", "pedido-2")
    }
    assert result.cost_usd == pytest.approx(CALLS * PER_CALL)
    # A chave de verdade só sai da porta; a da sessão nunca chega ao provedor.
    assert {h["authorization"] for h in kit.provider.seen} == {f"Bearer {KEY}"}


def test_o_codex_conta_os_proprios_tokens_para_conferir_com_a_porta(space: Space, kit: Kit) -> None:
    hands = _hands(kit)
    _run(hands, space, World())
    assert hands.last_usage == CodexUsage(48213, 41984, 0, 1873, 512)


def test_o_teto_da_sessao_vale_pela_porta_entre_as_ferramentas(space: Space, kit: Kit) -> None:
    # Três chamadas antes da primeira ferramenta passam do teto: a sessão para depois dela.
    world = World()
    result = _run(_hands(kit, "--chama-porta", "1"), space, world, max_usd=2.5 * PER_CALL)
    assert result.reason == "teto da sessão"
    assert not result.done
    assert len(world.steps) == 1
    assert len(kit.meter.calls) == 3


def test_a_porta_recusa_a_chamada_acima_do_teto_da_sessao(space: Space, kit: Kit) -> None:
    # Uma chamada só já passa do teto: a porta recusa a segunda, e o Codex encerra a volta.
    result = _run(_hands(kit, "--chama-porta", "1"), space, World(), max_usd=0.5 * PER_CALL)
    assert result.reason == "teto da sessão"
    assert len(kit.meter.calls) == 1
    assert result.cost_usd == pytest.approx(PER_CALL)


def test_a_porta_recusa_quando_o_mundo_pede_para_parar(space: Space, kit: Kit) -> None:
    result = _run(_hands(kit, "--chama-porta", "1"), space, World(stop_after=0))
    assert result.reason == "parada"
    assert kit.meter.calls == []
    assert result.cost_usd == 0


def test_um_modelo_sem_preco_e_recusado_antes_de_abrir_o_codex(space: Space, kit: Kit) -> None:
    hands = _hands(kit)
    with pytest.raises(ValueError, match="preço"):
        asyncio.run(hands.run(cast(Workspace, space), _job("gpt-sem-preco"), World()))
    assert hands.sessions == 0


@MACOS
def test_com_a_pasta_das_sessoes_relativa_o_cercado_acha_o_perfil(
    space: Space, kit: Kit, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O `PASTA=data/maos/...` da comparação de 23/nov: a pasta das sessões relativa, e o harness
    rodando com o diretório no espaço. O perfil do cercado tem de ser achado, e a saída de erro do
    harness fica ao lado da conversa."""
    monkeypatch.chdir(tmp_path)
    space.root = space.root.relative_to(tmp_path)  # o espaço relativo, como o da comparação
    hands = CodexHands(
        kit.meter,
        api_key=KEY,
        home=Path("sessoes-relativas"),
        command=(sys.executable, str(FAKE)),
        upstream="http://provedor-falso",
        transport=httpx2.ASGITransport(app=kit.provider.app()),
        readable=[Path(sys.prefix), Path(sys.base_prefix), FAKE.parent],
    )
    result = _run(hands, space, World())
    assert result.reason == "pronto", result
    (errors,) = (tmp_path / "sessoes-relativas" / "pedido-2").glob("codex-*.stderr")
    assert "No such file" not in errors.read_text()


def test_o_config_da_sessao_aponta_o_provedor_para_a_porta() -> None:
    config = tomllib.loads(codex_config("http://127.0.0.1:5123", MODEL, "max"))
    provider = config["model_providers"][config["model_provider"]]
    assert provider == {
        "name": "a porta das mãos do Campsverso",
        "base_url": "http://127.0.0.1:5123/v1",
        "env_key": SESSION_VARIABLE,
        "wire_api": "responses",
    }
    assert (config["model"], config["model_reasoning_effort"]) == (MODEL, "xhigh")
    # A cerca é a nossa: o sandbox e as aprovações do Codex ficam desligados.
    assert (config["sandbox_mode"], config["approval_policy"]) == ("danger-full-access", "never")
    assert "model_reasoning_effort" not in tomllib.loads(codex_config("http://x", MODEL, None))
    # As ferramentas do mundo no /mcp da mesma porta, com a chave da sessão (ADR-0093, decisão 18).
    world = config["mcp_servers"]["oficina"]
    assert (world["url"], world["bearer_token_env_var"]) == (
        "http://127.0.0.1:5123/mcp",
        SESSION_VARIABLE,
    )


# ------------------------------------------------------------------ os tetos


def test_uma_sessao_que_passa_do_limite_de_tempo_e_parada(space: Space, kit: Kit) -> None:
    world = World()
    result = _run(_hands(kit, "--dorme", "30"), space, world, max_seconds=0.5)
    assert not result.done
    assert result.reason == "limite de tempo"
    assert world.steps == []


def test_a_sessao_para_no_limite_de_voltas(space: Space, kit: Kit) -> None:
    world = World()
    result = _run(_hands(kit), space, world, max_turns=2)
    assert not result.done
    assert result.reason == "limite de voltas"
    assert len(world.steps) == 2


def test_a_sessao_para_quando_o_mundo_pede(space: Space, kit: Kit) -> None:
    world = World(stop_after=1)
    result = _run(_hands(kit), space, world)
    assert not result.done
    assert result.reason == "parada"
    assert len(world.steps) == 1


TALK = [
    {"type": "thread.started", "thread_id": "t-1"},
    {"type": "turn.started"},
    {"type": "item.completed", "item": {"id": "i0", "type": "agent_message", "text": "Vou olhar."}},
    {"type": "item.completed", "item": {"id": "i1", "type": "agent_message", "text": "Ainda."}},
    {
        "type": "item.started",
        "item": {"id": "i2", "type": "command_execution", "command": "ls", "status": "in_progress"},
    },
    {
        "type": "item.completed",
        "item": {
            "id": "i2",
            "type": "command_execution",
            "command": "ls",
            "exit_code": 0,
            "status": "completed",
        },
    },
    {"type": "item.completed", "item": {"id": "i3", "type": "agent_message", "text": "Pronto."}},
    {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}},
]


def _talk(tmp_path: Path) -> Path:
    example = tmp_path / "conversa.jsonl"
    example.write_text("\n".join(json.dumps(e) for e in TALK) + "\n", encoding="utf-8")
    return example


def test_o_passo_mostra_o_comando_sem_o_shell_em_volta() -> None:
    assert shown_command("/bin/zsh -lc 'ls -a'") == "ls -a"
    assert shown_command("/bin/zsh -lc false") == "false"
    assert shown_command("bash -lc 'python -m pytest -q'") == "python -m pytest -q"
    assert shown_command("sh -c 'echo \"oi\"' && ls") == "'echo \"oi\"' && ls"
    assert shown_command("bash -lc 'aspas sem fim") == "'aspas sem fim"
    assert shown_command("python -m pytest") == "python -m pytest"


SESSION = Path(__file__).parents[3] / "tests" / "fixtures" / "codex" / "sessao-0.171.0.jsonl"


def test_a_sessao_do_codex_de_verdade_vira_os_passos(tmp_path: Path) -> None:
    """A saída do Codex 0.171.0 (o pacote, com o modo código) no cercado, diante de uma OpenAI
    falsa que pede cinco ferramentas pelo `exec` (o ensaio de 23/nov): as chamadas de dentro do
    JavaScript saem como os itens de sempre, e as do mundo, pelo `/mcp` da porta, como as do
    Claude Code."""
    stream = CodexStream(tmp_path)
    steps: list[HandsStep] = []
    turns: list[str] = []
    for line in SESSION.read_text(encoding="utf-8").splitlines():
        data = json.loads(line.replace("{espaco}", str(tmp_path)))
        stream.account(data)
        read = stream.read(data)
        steps.extend(read.steps)
        if read.turn is not None:
            turns.append(read.turn)
    assert [(s.tool, s.summary, s.path, s.ok) for s in steps] == [
        ("command_execution", "command_execution: ls -a", None, True),
        ("file_change", "file_change: add notas/ensaio.md", "notas/ensaio.md", True),
        ("chamar_robo", "chamar_robo: robô testador", None, True),
        ("anotar", "anotar", None, True),
        ("command_execution", "command_execution: false", None, False),
    ]
    assert turns == ["tool", "tool", "tool", "tool", "tool", "message"]
    assert stream.completed
    assert stream.failed is None
    assert stream.notices == []
    assert stream.usage == CodexUsage(6000, 2400, 0, 300, 0)


NOTICE = (
    "Code Mode is unavailable because failed to spawn code-mode host: "
    "host executable was not found."
)


def test_um_item_de_erro_do_codex_vira_um_aviso(space: Space, kit: Kit, tmp_path: Path) -> None:
    """O Codex avisa num item `error` e segue (o modo código sem o programa dele, no ensaio de
    23/nov): a sessão acaba bem, e o aviso chega a quem roda as mãos."""
    events = [
        {"type": "thread.started", "thread_id": "t-1"},
        {"type": "item.completed", "item": {"id": "item_0", "type": "error", "message": NOTICE}},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"id": "item_1", "type": "agent_message", "text": "Ok."},
        },
        {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}},
    ]
    example = tmp_path / "aviso.jsonl"
    example.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    warnings: list[tuple[str, dict[str, Any]]] = []

    def warn(event: str, fields: Mapping[str, Any]) -> None:
        warnings.append((event, dict(fields)))

    hands = _hands(kit, "--exemplo", str(example), warn=warn)
    result = _run(hands, space, World())
    assert (result.done, result.reason, result.summary) == (True, "pronto", "Ok.")
    assert warnings == [("hands.codex_notice", {"message": NOTICE})]


def test_a_mensagem_antes_da_ferramenta_vai_no_passo(tmp_path: Path) -> None:
    """ADR-0093, decisão 12: o que o modelo escreveu antes da ferramenta vai no passo dela, uma
    vez; a mensagem final não vira passo."""
    stream = CodexStream(tmp_path)
    steps: list[HandsStep] = []
    for event in TALK:
        steps.extend(stream.read(event).steps)
    assert [(s.tool, s.note) for s in steps] == [("command_execution", "Ainda.")]


def test_o_limite_de_voltas_vale_numa_mensagem_do_meio(
    space: Space, kit: Kit, tmp_path: Path
) -> None:
    # Duas mensagens antes da ferramenta: com uma volta, a segunda mensagem já não sai.
    world = World()
    result = _run(_hands(kit, "--exemplo", str(_talk(tmp_path))), space, world, max_turns=1)
    assert result.reason == "limite de voltas"
    assert result.summary == "Vou olhar."
    assert world.steps == []


def test_o_limite_de_voltas_nao_corta_a_resposta_final(
    space: Space, kit: Kit, tmp_path: Path
) -> None:
    # Duas mensagens, a ferramenta e a resposta final: com quatro voltas, a sessão acaba bem.
    result = _run(_hands(kit, "--exemplo", str(_talk(tmp_path))), space, World(), max_turns=4)
    assert result.done
    assert result.reason == "pronto"
    assert result.summary == "Pronto."
    hands = _hands(kit)
    assert _run(hands, space, World(), max_turns=7).reason == "pronto"  # seis ferramentas e a final
    assert hands.last_usage.output_tokens == 1873


def test_parada_no_meio_ainda_conta_o_usage_que_chega(space: Space, kit: Kit) -> None:
    hands = _hands(kit)
    result = _run(hands, space, World(), max_turns=2)
    assert result.reason == "limite de voltas"
    assert hands.last_usage.input_tokens == 48213


def test_o_briefing_entra_dentro_do_limite_de_tempo(space: Space, kit: Kit) -> None:
    # Um Codex que nunca lê a entrada: o briefing grande enche o cano, e o relógio para a sessão.
    hands = _hands(kit, "--sem-ler", "1")
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


def test_a_espera_do_fim_do_codex_fica_dentro_do_limite_de_tempo(space: Space, kit: Kit) -> None:
    # O Codex fecha a saída depois do exemplo mas não sai: o relógio da sessão o para.
    began = time.monotonic()
    result = _run(_hands(kit, "--fica", "30"), space, World(), max_seconds=1.0)
    assert result.reason == "limite de tempo"
    assert not result.done
    assert time.monotonic() - began < GRACE_SECONDS + 2


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


def test_a_parada_encerra_o_grupo_de_processos(space: Space, kit: Kit, tmp_path: Path) -> None:
    grandchild = tmp_path / "neto.txt"
    result = _run(
        _hands(kit, "--neto", str(grandchild), "--dorme", "30"), space, World(), max_seconds=1.0
    )
    assert result.reason == "limite de tempo"
    pid = int(grandchild.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 5
    while _alive(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _alive(pid)


# ------------------------------------------------------------------ o ambiente e o cercado


def test_o_ambiente_do_processo_nao_tem_chave(
    space: Space, kit: Kit, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-de-verdade")
    monkeypatch.setenv("OPENAI_API_KEY", "outra-chave")
    monkeypatch.setenv("GITHUB_TOKEN", "um-token")
    dump = tmp_path / "ambiente.json"
    briefing = tmp_path / "entrada.txt"
    _run(_hands(kit, "--ambiente", str(dump), "--entrada", str(briefing)), space, World())
    seen: dict[str, str] = json.loads(dump.read_text(encoding="utf-8"))
    assert [k for k in seen if "KEY" in k.upper() or "TOKEN" in k.upper()] == []
    assert KEY not in seen.values()
    assert seen["HOME"].startswith(str(space.root))
    # Só a chave da sessão, que vale na porta enquanto a sessão dura.
    assert seen[SESSION_VARIABLE].startswith("sessao-")
    config = Path(seen["CODEX_HOME"]) / "config.toml"
    assert KEY not in config.read_text(encoding="utf-8")
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


def test_a_conversa_fica_num_arquivo_fora_do_espaco(space: Space, kit: Kit) -> None:
    _run(_hands(kit), space, World())
    [transcript] = (kit.home / "pedido-2").glob("codex-1-*.jsonl")
    lines = transcript.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["type"] == "thread.started"
    assert json.loads(lines[-1])["type"] == "turn.completed"
    assert not transcript.resolve().is_relative_to(space.root.resolve())


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
    # As ferramentas do mundo saem como no Claude Code; as de outro servidor, pelo nome completo.
    mcp: dict[str, Any] = {
        "type": "mcp_tool_call",
        "server": "oficina",
        "tool": "anotar",
        "status": "completed",
    }
    assert (steps_of(mcp, tmp_path, 0)[0].tool, steps_of(mcp, tmp_path, 0)[0].summary) == (
        "anotar",
        "anotar",
    )
    robot = {**mcp, "tool": "chamar_robo", "arguments": {"nome": "testador"}}
    refused: dict[str, Any] = {**robot, "result": {"content": [], "is_error": True}}
    assert steps_of(robot, tmp_path, 0)[0].summary == "chamar_robo: robô testador"
    assert not steps_of(refused, tmp_path, 0)[0].ok
    other = {**mcp, "server": "busca", "tool": "achar"}
    assert steps_of(other, tmp_path, 0)[0].summary == "mcp_tool_call: busca.achar"


def test_o_usage_do_codex_soma_cada_campo() -> None:
    usage = CodexUsage().plus(
        {"input_tokens": 1000, "cached_input_tokens": 600, "output_tokens": 100}
    )
    usage = usage.plus({"input_tokens": 1000, "cache_write_input_tokens": 400, "x": "y"})
    assert usage == CodexUsage(2000, 600, 400, 100, 0)


@MACOS
def test_no_cercado_o_codex_chama_a_porta_e_nao_escreve_fora(
    space: Space, kit: Kit, tmp_path: Path
) -> None:
    outside = tmp_path / "fora.txt"
    # O Python do projeto (o `.venv` e a instalação de base) e o falso moram na casa do usuário.
    readable = [Path(sys.prefix), Path(sys.base_prefix), FAKE.parent]
    hands = _hands(
        kit, "--chama-porta", "1", "--escreve-fora", str(outside), sandbox=True, readable=readable
    )
    result = _run(hands, space, World())
    assert result.reason == "pronto", result
    assert len(kit.meter.calls) == CALLS
    assert not outside.exists()
    assert (kit.home / "pedido-2" / "sandbox.sb").exists()


# ------------------------------------------------------------------ o programa


def _program(folder: Path, first: str = "#!/bin/sh") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    program = folder / "codex"
    program.write_text(f"{first}\nexit 0\n", encoding="utf-8")
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


def _interpreter(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    node = folder / "node-falso"
    node.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    node.chmod(0o755)
    return node


def test_o_interpretador_de_um_lancador_do_env_vem_de_fora_do_espaco(
    space: Space, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # O `.venv/bin` do espaço vem à frente no PATH do processo; o `env` acharia ali o plantado.
    _interpreter(space.root / ".venv" / "bin")
    node = _interpreter(tmp_path / "node")
    program = _program(tmp_path / "pacote", "#!/usr/bin/env -S node-falso --sem-aviso")
    monkeypatch.setenv("PATH", f"{program.parent}{os.pathsep}{node.parent}")
    assert resolve_command(("codex", "exec"), space.root) == [
        str(node),
        "--sem-aviso",
        str(program),
        "exec",
    ]
    # Achado só no espaço, o interpretador é recusado como o próprio Codex.
    monkeypatch.setenv("PATH", f"{program.parent}{os.pathsep}{space.root / '.venv' / 'bin'}")
    with pytest.raises(ValueError, match="espaço"):
        resolve_command(("codex",), space.root)


def test_o_cercado_le_a_instalacao_de_cada_programa_menos_a_casa(tmp_path: Path) -> None:
    home = tmp_path / "casa"
    node = _interpreter(tmp_path / "opt" / "node" / "bin")
    agy = _interpreter(home / ".local" / "bin")
    tool = _interpreter(tmp_path / "ferramentas" / "codex-1.0")
    found = readable_for([str(node), str(agy), str(tool), "exec", "--json"], home)
    assert found == [
        (tmp_path / "opt" / "node").resolve(),
        agy.parent.resolve(),
        tool.parent.resolve(),
    ]
