"""As mãos do Antigravity (ADR-0093): uma sessão com um `agy` falso que imprime o exemplo do
`stream-json` e chama o modelo pela porta das mãos, como o de verdade com a chave de API, diante de
um Gemini falso. Os passos, o resumo, o custo medido pela porta, os tetos, os argumentos, o ambiente
e a casa da sessão, e o cercado."""

import asyncio
import json
import subprocess
import sys
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

from campsverso_adapters.hands_antigravity import (
    MAX_PROMPT_BYTES,
    AntigravityHands,
    AntigravityStream,
    AntigravityUsage,
    api_model,
    slug_of,
    step_of,
)
from campsverso_adapters.hands_fence import sandbox_profile
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

FAKE = Path(__file__).parents[3] / "tests" / "fixtures" / "antigravity" / "agy_falso.py"
MODEL = "gemini-4-neon"
PRICED = "google/gemini-4-neon"
KEY = "chave-de-verdade"
PRICES = {PRICED: (3.0, 15.0)}
# Cada chamada do Gemini falso: 1000 de entrada, 400 delas do cache, e 200 de saída (150 dos
# candidatos e 50 do pensamento).
PER_CALL = (600 * 3.0 + 200 * 15.0) / 1_000_000
# O exemplo tem dez passos do modelo (duas respostas e oito ferramentas), e o falso chama o modelo
# antes de cada um.
CALLS = 10
SUMMARY = "Escrevi o robô tools/robos/eco.py, que repete os argumentos"
MACOS = pytest.mark.skipif(sys.platform != "darwin", reason="o sandbox-exec é do macOS")

GEMINI_CHUNKS: list[Mapping[str, Any]] = [
    {
        "candidates": [
            {
                "content": {
                    "role": "model",
                    "parts": [{"functionCall": {"name": "run_command", "args": {}}}],
                },
                "finishReason": "STOP",
            }
        ],
        "modelVersion": MODEL,
        "usageMetadata": {
            "promptTokenCount": 1000,
            "cachedContentTokenCount": 400,
            "candidatesTokenCount": 150,
            "thoughtsTokenCount": 50,
        },
    }
]


class Meter:
    """O medidor dos testes: guarda o que a porta mediu e cobra pela tabela."""

    def __init__(self) -> None:
        self.calls: list[tuple[ModelRequest, ModelResponse, str]] = []

    def assert_priced(self, model: str) -> None:
        if model not in PRICES:
            raise LookupError(f"modelo sem preço na tabela do ambiente: {model}")

    async def observed(
        self, request: ModelRequest, response: ModelResponse, *, harness: str
    ) -> float:
        self.calls.append((request, response, harness))
        price_in, price_out = PRICES[request.model]
        usage = response.usage
        return (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1_000_000


class Provider:
    """O Gemini falso, atrás da porta: guarda a URL e os cabeçalhos e devolve a mesma resposta."""

    def __init__(self) -> None:
        self.seen: list[tuple[str, dict[str, str]]] = []
        self.body = b"".join(f"data: {json.dumps(c)}\n\n".encode() for c in GEMINI_CHUNKS)

    def app(self) -> Starlette:
        async def handle(request: Request) -> Response:
            self.seen.append((str(request.url), dict(request.headers)))
            return Response(self.body, media_type="text/event-stream")

        return Starlette(routes=[Route("/{path:path}", handle, methods=["GET", "POST"])])


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
        self.ticket_id = "pedido-3"
        self.base = "0" * 40


@dataclass
class Kit:
    home: Path
    meter: Meter = field(default_factory=Meter)
    provider: Provider = field(default_factory=Provider)
    warnings: list[tuple[str, Mapping[str, Any]]] = field(
        default_factory=lambda: list[tuple[str, Mapping[str, Any]]]()
    )


@pytest.fixture
def space(tmp_path: Path) -> Space:
    root = tmp_path / "espaco"
    root.mkdir()
    return Space(root.resolve())


@pytest.fixture
def kit(tmp_path: Path) -> Kit:
    return Kit(tmp_path / "sessoes")


def _job(model: str = MODEL, opening: str = "Pedido 3: o robô eco.", **limits: Any) -> HandsJob:
    return HandsJob(
        ticket_id="pedido-3",
        opening=opening,
        system="Você é a Lívia.",
        model=model,
        avatar_id="livia",
        effort="high",
        limits=HandsLimits(**limits),
    )


def _hands(kit: Kit, *options: str, **kwargs: Any) -> AntigravityHands:
    kwargs.setdefault("sandbox", False)
    return AntigravityHands(
        kit.meter,
        api_key=KEY,
        home=kit.home,
        command=(sys.executable, str(FAKE), *options),
        upstream="http://gemini-falso",
        transport=httpx2.ASGITransport(app=kit.provider.app()),
        warn=lambda event, fields: kit.warnings.append((event, fields)),
        **kwargs,
    )


def _run(hands: AntigravityHands, space: Space, world: World, **limits: Any) -> Any:
    return asyncio.run(hands.run(cast(Workspace, space), _job(**limits), world))


INIT: Mapping[str, Any] = {"event": "init", "conversation_id": "c", "init": {"cwd": "/x"}}


def _example(tmp_path: Path, events: Sequence[Mapping[str, Any]]) -> Path:
    example = tmp_path / "exemplo.jsonl"
    example.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return example


# ------------------------------------------------------------------ a sessão


def test_uma_sessao_vira_os_passos_na_ordem(space: Space, kit: Kit) -> None:
    world = World()
    result = _run(_hands(kit), space, world)
    assert [(s.tool, s.path, s.ok) for s in world.steps] == [
        ("run_command", None, True),
        ("read_file", "tools/robos/testador.py", True),
        ("write_file", "tools/robos/eco.py", True),
        ("write_file", "tools/robos/tests/test_eco.py", True),
        ("run_command", None, False),  # o pytest que falha sai com 1
        ("read_file", "tools/robos/eco_antigo.py", False),
        ("edit_file", "tools/robos/eco.py", True),
        ("run_command", None, True),
    ]
    assert world.steps[0].summary == "run_command: ls tools/robos tools/robos/tests"
    assert world.steps[0].duration_ms == 70
    assert world.steps[5].summary == (
        "read_file: tools/robos/eco_antigo.py (erro: file does not exist)"
    )
    assert result.done
    assert result.reason == "pronto"
    assert (result.steps, result.turns) == (8, 10)  # oito ferramentas e duas respostas
    assert result.summary.startswith(SUMMARY)
    assert kit.warnings == []


def test_o_agy_recebe_o_briefing_o_slug_e_o_limite_de_tempo(
    space: Space, kit: Kit, tmp_path: Path
) -> None:
    given = tmp_path / "argumentos.json"
    briefing = tmp_path / "entrada.txt"
    hands = _hands(kit, "--argumentos", str(given), "--entrada", str(briefing))
    _run(hands, space, World(), max_seconds=90.5)
    assert json.loads(given.read_text(encoding="utf-8"))[2:] == [
        "--output-format",
        "stream-json",
        "--model",
        "gemini-4-neon-high",
        "--dangerously-skip-permissions",
        "--disable-slash-commands",
        "--print-timeout",
        "91s",
    ]
    assert briefing.read_text(encoding="utf-8") == "Você é a Lívia.\n\nPedido 3: o robô eco."


def test_o_ambiente_tem_so_a_chave_da_sessao_e_a_casa_no_espaco(
    space: Space, kit: Kit, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", KEY)
    monkeypatch.setenv("GOOGLE_API_KEY", "outra-chave")
    dump = tmp_path / "ambiente.json"
    _run(_hands(kit, "--ambiente", str(dump)), space, World())
    seen: dict[str, str] = json.loads(dump.read_text(encoding="utf-8"))
    assert KEY not in seen.values()
    secrets = {k: v for k, v in seen.items() if "KEY" in k.upper() or "TOKEN" in k.upper()}
    assert list(secrets) == ["GEMINI_API_KEY"]
    assert secrets["GEMINI_API_KEY"].startswith("sessao-")
    assert seen["GOOGLE_GEMINI_BASE_URL"].startswith("http://127.0.0.1:")
    home = Path(seen["HOME"])
    assert home.is_relative_to(space.root)
    settings = home / ".gemini" / "antigravity-cli" / "settings.json"
    assert json.loads(settings.read_text(encoding="utf-8")) == {"modelProvider": "gemini"}


def test_a_conversa_fica_num_arquivo_fora_do_espaco(space: Space, kit: Kit) -> None:
    _run(_hands(kit), space, World())
    [transcript] = (kit.home / "pedido-3").glob("antigravity-1-*.jsonl")
    lines = transcript.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["event"] == "init"
    assert json.loads(lines[-1])["event"] == "result"


def test_o_agy_conta_os_proprios_tokens_para_conferir_com_a_porta(space: Space, kit: Kit) -> None:
    hands = _hands(kit)
    _run(hands, space, World())
    assert hands.last_usage == AntigravityUsage(52310, 3734, 1630, 38912, 56044)


# ------------------------------------------------------------------ a porta


def test_o_modelo_passa_pela_porta_e_o_custo_e_o_que_ela_mediu(space: Space, kit: Kit) -> None:
    result = _run(_hands(kit, "--chama-porta", "1"), space, World())
    assert result.reason == "pronto"
    assert len(kit.meter.calls) == CALLS
    assert {(r.model, h, r.avatar_id, r.ticket_id) for r, _, h in kit.meter.calls} == {
        (PRICED, "antigravity", "livia", "pedido-3")
    }
    assert result.cost_usd == pytest.approx(CALLS * PER_CALL)
    # A chave de verdade só sai da porta, no cabeçalho, e nunca na URL.
    assert {h["x-goog-api-key"] for _, h in kit.provider.seen} == {KEY}
    assert all("key=" not in url for url, _ in kit.provider.seen)


def test_o_teto_da_sessao_vale_pela_porta_entre_as_ferramentas(space: Space, kit: Kit) -> None:
    # Três chamadas (a resposta e duas ferramentas) passam do teto: a sessão para na segunda.
    world = World()
    result = _run(_hands(kit, "--chama-porta", "1"), space, world, max_usd=2.5 * PER_CALL)
    assert result.reason == "teto da sessão"
    assert len(world.steps) == 2
    assert len(kit.meter.calls) == 3


def test_a_porta_recusa_a_chamada_acima_do_teto_da_sessao(space: Space, kit: Kit) -> None:
    result = _run(_hands(kit, "--chama-porta", "1"), space, World(), max_usd=0.5 * PER_CALL)
    assert result.reason == "teto da sessão"
    assert len(kit.meter.calls) == 1
    assert result.cost_usd == pytest.approx(PER_CALL)


def test_a_porta_recusa_quando_o_mundo_pede_para_parar(space: Space, kit: Kit) -> None:
    result = _run(_hands(kit, "--chama-porta", "1"), space, World(stop_after=0))
    assert result.reason == "parada"
    assert kit.meter.calls == []


def test_um_modelo_sem_preco_e_recusado_antes_de_abrir_o_agy(space: Space, kit: Kit) -> None:
    hands = _hands(kit)
    with pytest.raises(ValueError, match="preço"):
        asyncio.run(hands.run(cast(Workspace, space), _job("gemini-9-sem-preco"), World()))
    assert hands.sessions == 0


def test_um_briefing_grande_demais_e_recusado_antes_de_abrir_o_agy(space: Space, kit: Kit) -> None:
    hands = _hands(kit)
    job = _job(opening="x" * (MAX_PROMPT_BYTES + 1))
    with pytest.raises(ValueError, match="linha de comando"):
        asyncio.run(hands.run(cast(Workspace, space), job, World()))
    assert hands.sessions == 0


# ------------------------------------------------------------------ os tetos e o fim


def test_uma_sessao_que_passa_do_limite_de_tempo_e_parada(space: Space, kit: Kit) -> None:
    world = World()
    result = _run(_hands(kit, "--dorme", "30"), space, world, max_seconds=0.5)
    assert result.reason == "limite de tempo"
    assert world.steps == []


def test_o_limite_de_voltas_vale_numa_resposta_do_meio(space: Space, kit: Kit) -> None:
    # A primeira resposta já é a volta do limite, e a sessão segue depois dela: para ali.
    hands = _hands(kit)
    world = World()
    result = _run(hands, space, world, max_turns=1)
    assert result.reason == "limite de voltas"
    assert world.steps == []
    # Na sessão parada, o resumo é a última resposta lida antes da parada.
    assert result.summary == "Vou ler os robôs da bancada antes de escrever o eco."
    # O fim que chega depois da parada traz os tokens, e a falha dele não é avisada.
    assert hands.last_usage.input_tokens == 52310
    assert kit.warnings == []


def test_o_limite_de_voltas_nao_corta_a_resposta_final(space: Space, kit: Kit) -> None:
    result = _run(_hands(kit), space, World(), max_turns=10)
    assert result.reason == "pronto"
    assert result.summary.startswith(SUMMARY)


def test_um_result_com_erro_e_um_erro_na_sessao(space: Space, kit: Kit, tmp_path: Path) -> None:
    events: list[Mapping[str, Any]] = [
        INIT,
        {"event": "result", "result": {"status": "ERROR", "error": "o modelo não existe"}},
    ]
    result = _run(_hands(kit, "--exemplo", str(_example(tmp_path, events))), space, World())
    assert result.reason == "erro na sessão"
    assert kit.warnings == [("hands.antigravity_failed", {"error": "o modelo não existe"})]


def test_sem_result_a_sessao_acaba_sem_resposta_final(
    space: Space, kit: Kit, tmp_path: Path
) -> None:
    result = _run(_hands(kit, "--exemplo", str(_example(tmp_path, [INIT]))), space, World())
    assert result.reason == "sem resposta final"


# ------------------------------------------------------------------ as peças


def test_o_slug_leva_o_esforco_e_a_tabela_fica_com_o_modelo() -> None:
    assert slug_of("gemini-4-neon", "high") == "gemini-4-neon-high"
    assert slug_of("gemini-4-neon", "max") == "gemini-4-neon-xhigh"
    assert slug_of("gemini-4-neon-low", "high") == "gemini-4-neon-low"
    assert slug_of("gemini-4-neon", None) == "gemini-4-neon"
    assert api_model("gemini-4-neon-xhigh") == "gemini-4-neon"
    assert api_model("gemini-pro-orchestrator") == "gemini-pro-orchestrator"


def test_o_passo_de_uma_ferramenta(tmp_path: Path) -> None:
    update = {
        "state": "ERROR",
        "tool_name": "write_file",
        "tool_info": {
            "name": "write_file",
            "parameters": {"Path": str(tmp_path / "a" / "b.py")},
            "error": {"type": "TOOL_ERROR", "message": "negado\noutra linha"},
        },
    }
    step = step_of(update, tmp_path, 5)
    assert (step.tool, step.path, step.ok) == ("write_file", "a/b.py", False)
    assert step.duration_ms == 5
    assert step.summary == "write_file: a/b.py (erro: negado)"
    bare = step_of({"tool_info": {"name": "list_dir", "parameters": {}}}, tmp_path, 0)
    assert (bare.summary, bare.path, bare.ok) == ("list_dir", None, True)
    # O estado `ERROR` sem a mensagem também é uma falha.
    assert not step_of({"state": "ERROR", "tool_name": "read_file"}, tmp_path, 0).ok


def _command(output: str) -> Mapping[str, Any]:
    info = {"name": "run_command", "parameters": {"CommandLine": "pytest -q"}, "output": output}
    return {"state": "DONE", "tool_name": "run_command", "tool_info": info}


HEAD = "Created At: 2026-11-23T07:15:17-03:00\nCompleted At: 2026-11-23T07:15:17-03:00\n"


def test_o_comando_vale_pelo_codigo_de_saida(tmp_path: Path) -> None:
    passed = step_of(
        _command(HEAD + "Command exited with code 0.\n\nCommand output:\nok"), tmp_path, 0
    )
    assert (passed.ok, passed.summary) == (True, "run_command: pytest -q")
    failed = step_of(
        _command(HEAD + "Command exited with code 1.\n\nNo output from the command."), tmp_path, 0
    )
    assert (failed.ok, failed.summary) == (False, "run_command: pytest -q")
    refused = step_of(
        _command(HEAD + "Command failed to run: failed to create PTY: operation not permitted.\n"),
        tmp_path,
        0,
    )
    assert not refused.ok
    assert refused.summary == (
        "run_command: pytest -q (erro: failed to create PTY: operation not permitted.)"
    )


SESSION = Path(__file__).parents[3] / "tests" / "fixtures" / "antigravity" / "sessao-1.5.14.jsonl"


def test_a_sessao_do_agy_de_verdade_vira_os_passos(tmp_path: Path) -> None:
    """A saída do `agy` 1.5.14 no cercado, diante de um Gemini falso que pede seis ferramentas
    (o ensaio de 23/nov): um comando, escrever, ler e editar arquivos, ler um que não existe e um
    comando que sai com 1."""
    stream = AntigravityStream(tmp_path)
    steps: list[HandsStep] = []
    turns: list[str] = []
    for line in SESSION.read_text(encoding="utf-8").splitlines():
        data = json.loads(line.replace("{espaco}", str(tmp_path)))
        stream.account(data)
        read = stream.read(data)
        steps.extend(read.steps)
        if read.turn is not None:
            turns.append(read.turn)
        assert stream.closes(data) == (data["event"] == "result")
    assert [(s.tool, s.path, s.ok) for s in steps] == [
        ("run_command", None, True),
        ("write_file", "notas/ensaio.md", True),
        ("read_file", "README.md", True),
        ("edit_file", "README.md", True),
        ("read_file", "nao-existe.md", False),
        ("run_command", None, False),
    ]
    assert steps[0].summary == "run_command: ls -a"
    assert steps[4].summary == "read_file: nao-existe.md (erro: file does not exist)"
    assert turns.count("message") == 7
    assert turns.count("tool") == 6
    assert stream.completed
    assert stream.failed is None
    assert stream.response.startswith("Ensaio pronto")
    assert stream.usage == AntigravityUsage(4200, 350, 70, 2800, 4550)


def test_a_resposta_soma_os_pedacos_ate_o_done(tmp_path: Path) -> None:
    stream = AntigravityStream(tmp_path)

    def update(state: str, text: str) -> Mapping[str, Any]:
        body = {"step_index": 4, "state": state, "step_type": "agent_response", "text_delta": text}
        return {"event": "step_update", "step_update": body}

    assert stream.read(update("ACTIVE", "Vou ")).turn is None
    assert stream.read(update("ACTIVE", "ler ")).turn is None
    done = stream.read(update("DONE", "o arquivo."))
    assert (done.turn, done.text) == ("message", "Vou ler o arquivo.")
    checkpoint = {"event": "step_update", "step_update": {"step_type": "checkpoint"}}
    assert stream.read(checkpoint).turn is None


@MACOS
def test_no_cercado_o_agy_chama_a_porta_e_nao_escreve_fora(
    space: Space, kit: Kit, tmp_path: Path
) -> None:
    outside = tmp_path / "fora.txt"
    readable = [Path(sys.prefix), Path(sys.base_prefix), FAKE.parent]
    hands = _hands(
        kit, "--chama-porta", "1", "--escreve-fora", str(outside), sandbox=True, readable=readable
    )
    result = _run(hands, space, World())
    assert result.reason == "pronto", result
    assert len(kit.meter.calls) == CALLS
    assert not outside.exists()


@MACOS
def test_o_cercado_deixa_abrir_um_terminal_novo(tmp_path: Path) -> None:
    """O `agy` roda cada comando num terminal novo, tirado do `/dev/ptmx`: sem ele no cercado, o
    comando nem roda ("failed to create PTY", o ensaio de 23/nov)."""
    root = tmp_path / "espaco"
    root.mkdir()
    readable = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()]
    profile = tmp_path / "perfil.sb"
    profile.write_text(sandbox_profile(root.resolve(), "1", Path.home().resolve(), readable))
    code = "import os; _, s = os.openpty(); print('terminal', os.ttyname(s))"
    out = subprocess.run(
        ["/usr/bin/sandbox-exec", "-f", str(profile), sys.executable, "-I", "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.startswith("terminal /dev/ttys"), out.stdout
