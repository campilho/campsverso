"""A mente com rotina do dev do escritório (ADR-0080): a rotina conduz, o modelo trabalha na
oficina numa sessão em segundo plano e responde a quem fala; a entrega sai sem pedido de decisão."""

import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest
import yaml

from campsverso_adapters import MemoryBlobStore, MemoryTelemetry, SqliteMemory
from campsverso_adapters.workshop_local import LocalWorkshop
from campsverso_adapters.workshop_review import review
from campsverso_controller_runner.office_mind import OfficeMind
from campsverso_controller_runner.runner import load_mind
from campsverso_controller_runner.workshop import WorkshopSession
from campsverso_mind import Memory, MemorySettings, Mind
from campsverso_ports import (
    Episode,
    HandsJob,
    HandsResult,
    HandsStep,
    HandsWorld,
    ModelCallError,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
    Workspace,
)

GIT = [
    "git",
    "-c",
    "user.name=Teste",
    "-c",
    "user.email=teste@exemplo",
    "-c",
    "commit.gpgsign=false",
]
TOOLS: list[dict[str, Any]] = [
    {"name": "escrever", "description": "x", "input_schema": {"type": "object", "properties": {}}},
    {"name": "pronto", "description": "x", "input_schema": {"type": "object", "properties": {}}},
]


class Scripted:
    """Uma porta de modelo de mentira: as respostas na ordem, e os pedidos guardados."""

    def __init__(self, *answers: Sequence[Mapping[str, Any]] | Exception) -> None:
        self.answers = list(answers)
        self.requests: list[ModelRequest] = []

    @property
    def provider(self) -> str:
        return "roteiro"

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def count_tokens(self, request: ModelRequest) -> int:
        return 0

    async def complete(self, request: ModelRequest) -> ModelResponse:
        self.requests.append(request)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        uses = [b for b in answer if b.get("type") == "tool_use"]
        return ModelResponse(
            content=[dict(b) for b in answer],
            stop_reason="tool_use" if uses else "end_turn",
            usage=ModelUsage(10, 5),
            model=request.model,
            latency_ms=1,
        )


class Routine:
    """A rotina de mentira: trabalha no pedido em fazendo; sem pedido, espera."""

    controller_type = "script"
    controller_id = "script/dev"

    def __init__(self) -> None:
        self.views: list[Mapping[str, Any]] = []

    def decide(self, view: Mapping[str, Any]) -> Mapping[str, Any]:
        self.views.append(view)
        doing = [e for e in view["entities"] if e.get("attributes", {}).get("estado") == "fazendo"]
        if doing:
            return {
                "action": "work",
                "params": {"seconds": 60},
                "intent": "trabalhar",
                "workshop": {},
            }
        return {"action": "wait", "params": {"seconds": 60}, "intent": "rotina: esperar"}


def _use(name: str, **given: Any) -> dict[str, Any]:
    return {"type": "tool_use", "id": f"t-{name}", "name": name, "input": given}


def _snapshot(
    *,
    heard: list[dict[str, Any]] | None = None,
    estado: str = "fazendo",
    day: int = 1,
    extra: Sequence[dict[str, Any]] = (),
    chosen: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    ticket = {
        "entity_id": "pedido-001",
        "kind": "ticket",
        "attributes": {
            "numero": 1,
            "titulo": "Testador",
            "descricao": "Rodar os testes.",
            "estado": estado,
            "dono": "tiago",
            **(chosen or {}),  # as mãos e o modelo da prancheta (ADR-0089)
        },
    }
    view: dict[str, Any] = {
        "clock": {"tick": 5, "sim_time": "2026-11-16T10:00:00-03:00", "day": day},
        "self": {"entity_id": "tiago", "position": {"x": 4, "y": 5}},
        "weather": {},
        "entities": [ticket, *extra],
        "containers": [],
    }
    if heard:
        view["heard"] = heard
    return {
        "avatar_id": "tiago",
        "decision": {"reason": "action_completed"},
        "as_of_tick": 5,
        "view": view,
    }


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("Um repositório de exemplo.\n")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run([*GIT, "-C", str(root), "add", "-A"], check=True)
    subprocess.run([*GIT, "-C", str(root), "commit", "-q", "-m", "base"], check=True)
    return root


def _mind(
    port: Scripted,
    repo: Path,
    tmp_path: Path,
    memory: Memory | None = None,
    robot_tool: Mapping[str, Any] | None = None,
    background: bool = True,
    events: list[tuple[str, Mapping[str, Any]]] | None = None,
    model: str = "claude-sonnet-5-5",
    card: str = "Você é o Camps.",
    **extra: Any,
) -> tuple[OfficeMind, list[Mapping[str, Any]], list[str]]:
    proposed: list[Mapping[str, Any]] = []
    steps: list[str] = []

    async def propose(proposal: Mapping[str, Any]) -> None:
        proposed.append(proposal)

    async def publish(kind: str, data: Mapping[str, Any]) -> None:
        if events is not None:
            events.append((kind, data))
        if "tool" in data:
            steps.append(str(data["tool"]))
        elif "robot_id" in data:
            steps.append(f"{kind}:{data['robot_id']}")
        else:  # o fim da sessão (ADR-0089), com as mãos e o motivo
            steps.append(f"fim:{data['harness']}:{data['reason']}")

    shop = WorkshopSession(
        "office-teste",
        "tiago",
        LocalWorkshop(repo, tmp_path / "oficina", python_env=False, python=Path(sys.executable)),
        MemoryBlobStore(),
        lambda diff: review(diff, []),
        publish,
    )
    mind = OfficeMind(
        Routine(),
        Mind(
            "office",
            card=card,
            notes="O escritório.",
            tools=(),
            robot_tool=robot_tool,
        ),
        port,
        shop,
        controller_id="llm/tiago",
        avatar_id="tiago",
        model=model,
        session_tools=TOOLS,
        session_instructions="Trabalhe.",
        chat_instructions="Responda curto.",
        memory=memory,
        background=background,
        **extra,
    )
    mind.propose = propose
    return mind, proposed, steps


async def test_o_modelo_trabalha_na_oficina_e_a_entrega_sai_sozinha(
    repo: Path, tmp_path: Path
) -> None:
    port = Scripted(
        [
            {"type": "thinking", "thinking": "vou escrever", "signature": "s"},
            _use("escrever", path="tools/testador.py", content="OK = 1\n"),
        ],
        [_use("pronto", resumo="Escrevi o testador.")],
    )
    mind, proposed, steps = _mind(port, repo, tmp_path)
    first = await mind.decide(_snapshot())
    assert first is not None
    assert (first["action"], first["intent"]) == (
        "work",
        "pensando no pedido 1 (claude-sonnet-5-5)",
    )
    assert "workshop" not in first  # a sessão fixa do script não sai
    assert mind._task is not None  # pyright: ignore[reportPrivateUsage]
    await mind._task  # pyright: ignore[reportPrivateUsage]
    (deliver,) = proposed
    assert deliver["action"] == "deliver"
    assert deliver["intent"] == "entregar o pedido 1: Escrevi o testador."
    assert deliver["params"]["patch"]["files"] == ["tools/testador.py"]
    assert steps == ["escrever", "pronto", "fim:api:pronto"]  # o fim da sessão (ADR-0089)
    # O pedido da sessão leva o do quadro, o ticket para a guarda e o resultado da ferramenta.
    assert "Pedido 1: Testador" in port.requests[0].messages[0]["content"][0]["text"]
    assert {r.ticket_id for r in port.requests} == {"pedido-001"}
    assert port.requests[1].messages[-1]["content"][0]["type"] == "tool_result"


async def test_fora_do_mundo_vivo_o_mundo_espera_a_sessao(repo: Path, tmp_path: Path) -> None:
    """Os testes e a fita do escritório (`background=False`): a sessão roda dentro da decisão, e a
    entrega com o patch é a própria decisão; a mesma fita reproduz o mesmo dia (20/nov)."""
    port = Scripted(
        [_use("escrever", path="tools/testador.py", content="OK = 1\n")],
        [_use("pronto", resumo="Escrevi o testador.")],
    )
    mind, proposed, steps = _mind(port, repo, tmp_path, background=False)
    deliver = await mind.decide(_snapshot())
    assert deliver is not None
    assert deliver["action"] == "deliver"
    assert deliver["params"]["patch"]["files"] == ["tools/testador.py"]
    assert steps == ["escrever", "pronto", "fim:api:pronto"]
    assert not mind.working
    assert proposed == []  # nada sai por fora da decisão
    assert mind.sessions == 1


async def test_quem_fala_com_o_dev_recebe_a_resposta_do_modelo(repo: Path, tmp_path: Path) -> None:
    port = Scripted(
        [{"type": "text", "text": "Tudo certo, já estou\\n nisso."}],
        ModelCallError("server", "caiu"),
    )
    mind, _, _ = _mind(port, repo, tmp_path)
    heard = [
        {"tick": 4, "avatar_id": "gerente", "text": "Como vai o testador?", "listener_id": "tiago"}
    ]
    reply = await mind.decide(_snapshot(heard=heard, estado="a_fazer"))
    assert reply == {
        "action": "say",
        "params": {"text": "Tudo certo, já estou\\n nisso.", "to": "gerente"},
        "intent": "responder a quem falou comigo",
    }
    assert "Como vai o testador?" in port.requests[0].messages[0]["content"][0]["text"]
    fallback = await mind.decide(_snapshot(heard=heard, estado="a_fazer"))
    assert fallback is not None
    assert fallback["action"] == "wait"  # o modelo caiu: a rotina decide


async def test_a_sessao_que_nao_chega_ao_pronto_vira_uma_fala(repo: Path, tmp_path: Path) -> None:
    port = Scripted(*[[{"type": "text", "text": "hum"}]] * 3)
    mind, proposed, _ = _mind(port, repo, tmp_path)
    await mind.decide(_snapshot())
    assert mind._task is not None  # pyright: ignore[reportPrivateUsage]
    await mind._task  # pyright: ignore[reportPrivateUsage]
    (said,) = proposed
    assert said["action"] == "say"
    assert said["params"]["text"] == "Não consegui terminar o pedido 1: sem ferramenta."
    assert mind.failed == {"pedido-001"}
    again = await mind.decide(_snapshot())
    assert again is not None
    assert again["action"] == "work"  # a rotina trabalha, sem recomeçar a sessão
    assert mind.sessions == 1


async def test_o_teto_estourado_desliga_a_mente_e_o_dev_avisa_uma_vez(
    repo: Path, tmp_path: Path
) -> None:
    """ADR-0080, decisão 15: no escritório, o teto do dia desliga a mente, a rotina conduz e o dev
    avisa uma vez; o teto subido a liga de novo. O teto de um pedido para a sessão dele."""
    port = Scripted()
    mind, _, _ = _mind(port, repo, tmp_path)
    limits = {"usd_per_sim_day": 3.0, "usd_total": 30.0}
    mind.on_budget({"type": "campsverso.live.budget.v1", "limits": limits, "exceeded": ["day"]})
    said = await mind.decide(_snapshot(estado="a_fazer"))
    assert said == {
        "action": "say",
        "params": {"text": "Fiquei sem bateria: não consigo mais programar hoje."},
        "intent": "avisar sobre o pedido",
    }
    routine = await mind.decide(_snapshot())  # com pedido: a rotina trabalha, sem modelo
    assert routine is not None
    assert routine["action"] == "work"
    assert port.requests == []
    assert mind.sessions == 0
    mind.on_budget({"type": "campsverso.live.budget.v1", "limits": limits, "exceeded": []})
    assert not mind.off


# ---------------------------------------------------------------- a memória (o plano do M24, §2.3)

ROOT = Path(__file__).resolve().parents[3]
LESSON = {
    "id": "",
    "statement": "O gerente devolve o pedido que não cobre o caso vazio.",
    "confidence": 0.7,
    "evidence": ["o pedido 1, devolvido às 17:00"],
    "status": "new",
    "reason": "",
}


def _memory() -> Memory:
    """A memória do dev com o perfil do escritório, e o dia 1 com um pedido devolvido."""
    profile = load_mind("tiago_escritorio").memory
    assert profile is not None
    memory = Memory(SqliteMemory(":memory:"), "tiago", MemorySettings(profile=profile))
    memory.port.record(
        Episode(100, 1, "17:00 gerente devolveu o pedido 1: falta o caso vazio", 9, "returned")
    )
    return memory


def test_o_perfil_do_escritorio_tem_o_tick_e_as_ferramentas_do_escritorio() -> None:
    profile = load_mind("tiago_escritorio").memory
    assert profile is not None
    office = ROOT / "cartridges/office/sim/src/campsverso_office_sim/data/office.yaml"
    sim = yaml.safe_load(office.read_text(encoding="utf-8"))
    assert profile.tick_seconds == sim["clock"]["tick_seconds"]
    assert not profile.places
    assert profile.note_tool is not None
    assert profile.note_tool["name"] == "anotar"
    assert profile.review_tool is not None
    assert profile.review_tool["name"] == "revisar"
    # A rotina inteira fica quieta: cada ação do escritório que ela faz está na lista.
    assert {"work", "coffee", "lunch", "videogame"} <= profile.quiet_actions
    assert set(profile.quiet_actions) <= set(sim["actions"]) | {"move", "wait", "say"}


async def test_ao_chegar_o_dev_reve_a_vespera_e_a_sessao_comeca_com_a_memoria(
    repo: Path, tmp_path: Path
) -> None:
    memory = _memory()
    port = Scripted(
        [
            _use(
                "revisar",
                summary="O gerente devolveu o pedido 1.",
                plan="Cobrir o caso vazio.",
                beliefs=[LESSON],
            )
        ],
        [_use("anotar", texto="O gerente sempre pede o caso vazio.")],
        [_use("escrever", path="tools/testador.py", content="OK = 1\n")],
        [_use("pronto", resumo="Escrevi o testador.")],
    )
    mind, proposed, steps = _mind(port, repo, tmp_path, memory)
    await mind.decide(_snapshot(day=2))
    assert mind._task is not None  # pyright: ignore[reportPrivateUsage]
    await mind._task  # pyright: ignore[reportPrivateUsage]
    assert mind.reviews == 1
    review_request, opening = port.requests[0], port.requests[1]
    assert review_request.purpose == "reflection"
    assert [t["name"] for t in review_request.tools] == ["revisar"]
    assert "Dia 1. O que aconteceu, na ordem:" in review_request.messages[0]["content"][0]["text"]
    # A sessão espera a revisão e abre com a memória antes do pedido; anotar é dela.
    text = opening.messages[0]["content"][0]["text"]
    assert text.startswith("## O que você lembra\nDia 1, na revisão: O gerente devolveu")
    assert "Plano: Cobrir o caso vazio." in text
    assert "O gerente devolve o pedido que não cobre o caso vazio." in text
    assert text.index("## O que você lembra") < text.index("Pedido 1: Testador")
    assert "anotar" in [t["name"] for t in opening.tools]
    assert steps == ["escrever", "pronto", "fim:api:pronto"]  # a anotação não passa pela oficina
    assert proposed[0]["action"] == "deliver"
    (note,) = memory.port.notes(2)
    assert note.text == "O gerente sempre pede o caso vazio."
    (line,) = memory.port.episodes(2)
    assert line.text.startswith(
        "10:00 trabalhei no pedido 1 na oficina com as ferramentas de sempre"
        " (claude-sonnet-5-5), em "
    )
    assert line.text.endswith("passos; terminei: Escrevi o testador.")
    kinds = [e["type"] for e in mind.drain_events()]
    assert kinds == [
        "campsverso.memory.reflected.v1",
        "campsverso.memory.belief.formed.v1",
        "campsverso.memory.noted.v1",
    ]
    # No mesmo dia, nada a rever de novo.
    await mind.decide(_snapshot(day=2, estado="aceito"))
    assert mind.reviews == 1


async def test_a_revisao_que_falha_nao_segura_o_trabalho(repo: Path, tmp_path: Path) -> None:
    memory = _memory()
    port = Scripted(ModelCallError("server", "caiu"), [_use("pronto", resumo="Feito.")])
    mind, proposed, _ = _mind(port, repo, tmp_path, memory)
    await mind.decide(_snapshot(day=2))
    assert mind._task is not None  # pyright: ignore[reportPrivateUsage]
    await mind._task  # pyright: ignore[reportPrivateUsage]
    assert mind.reviews == 0
    assert proposed[0]["action"] == "deliver"
    opening = port.requests[1].messages[0]["content"][0]["text"]
    assert "Dia 1, na revisão" not in opening  # sem revisão, a memória ainda vem, sem o resumo
    assert "17:00 gerente devolveu" not in opening  # os momentos são só os de hoje
    assert len(port.requests) == 2  # e não tenta de novo no mesmo dia


async def test_a_conversa_leva_a_memoria(repo: Path, tmp_path: Path) -> None:
    memory = _memory()
    port = Scripted([{"type": "text", "text": "Já vi o caso vazio."}])
    mind, _, _ = _mind(port, repo, tmp_path, memory)
    heard = [{"tick": 4, "avatar_id": "gerente", "text": "E o caso vazio?", "listener_id": "tiago"}]
    mind._review_day = 1  # pyright: ignore[reportPrivateUsage]  # sem revisão neste teste
    reply = await mind.decide(_snapshot(heard=heard, estado="a_fazer"))
    assert reply is not None
    assert reply["action"] == "say"
    asked = port.requests[0].messages[0]["content"][0]["text"]
    assert asked.startswith("## O que você lembra")
    assert asked.index("## O que você lembra") < asked.index("E o caso vazio?")


# ---------------------------------------------------------------- a bancada (o plano do M24, §4)

ROBOT = {
    "entity_id": "robo-eco",
    "kind": "robot",
    "position": {"x": 7, "y": 4},
    "attributes": {"nome": "eco", "modulo": "tools.eco", "descricao": "Repete os argumentos."},
}


async def test_o_dev_chama_o_robo_da_bancada_na_oficina(repo: Path, tmp_path: Path) -> None:
    (repo / "tools").mkdir()
    (repo / "tools" / "__init__.py").write_text("")
    (repo / "tools" / "eco.py").write_text("import sys\n\nprint('eco:', *sys.argv[1:])\n")
    subprocess.run([*GIT, "-C", str(repo), "add", "-A"], check=True)
    subprocess.run([*GIT, "-C", str(repo), "commit", "-q", "-m", "eco"], check=True)
    template = load_mind("tiago_escritorio").robot_tool
    assert template is not None
    port = Scripted(
        [_use("chamar_robo", nome="eco", argumentos=["tools", "tests"])],
        [_use("chamar_robo", nome="sumido", argumentos=[])],
        [_use("pronto", resumo="Chamei o eco.")],
    )
    mind, proposed, steps = _mind(port, repo, tmp_path, robot_tool=template)
    await mind.decide(_snapshot(extra=[ROBOT]))
    assert mind._task is not None  # pyright: ignore[reportPrivateUsage]
    await mind._task  # pyright: ignore[reportPrivateUsage]
    offered = {t["name"]: t for t in port.requests[0].tools}
    bench = offered["chamar_robo"]
    assert bench["input_schema"]["properties"]["nome"]["enum"] == ["eco"]
    assert "eco: Repete os argumentos." in bench["description"]
    first = port.requests[1].messages[-1]["content"][0]
    assert first["type"] == "tool_result"
    assert "eco: tools tests" in first["content"]
    second = port.requests[2].messages[-1]["content"][0]
    assert second["is_error"] is True
    assert "não há robô 'sumido' na bancada" in second["content"]
    called = steps.index("campsverso.workshop.robot_called.v1:robo-eco")
    assert steps[called - 1] == "campsverso.workshop.robot_started.v1:robo-eco"  # antes de rodar
    assert proposed[0]["action"] == "deliver"


async def test_sem_robo_na_bancada_nao_ha_chamar_robo(repo: Path, tmp_path: Path) -> None:
    template = load_mind("tiago_escritorio").robot_tool
    port = Scripted([_use("pronto", resumo="Nada.")])
    mind, _, _ = _mind(port, repo, tmp_path, robot_tool=template)
    await mind.decide(_snapshot())
    assert mind._task is not None  # pyright: ignore[reportPrivateUsage]
    await mind._task  # pyright: ignore[reportPrivateUsage]
    assert "chamar_robo" not in {t["name"] for t in port.requests[0].tools}


# ---------------------------------------------------------------- as mãos (ADR-0089)


class FakeHands:
    """Umas mãos de fora de mentira: escrevem um arquivo, mostram um passo e terminam."""

    def __init__(self, harness: str = "claude_code") -> None:
        self.harness = harness
        self.jobs: list[HandsJob] = []

    async def run(self, space: Workspace, job: HandsJob, world: HandsWorld) -> HandsResult:
        self.jobs.append(job)
        (space.root / "ola.py").write_text("print('olá')\n")
        await world.step(HandsStep("Write", "Write: ola.py", True, 12, "ola.py"))
        return HandsResult(True, f"Escrevi o ola.py pelo {self.harness}.", 3, 1, "pronto", 0.42)


async def test_o_pedido_escolhe_as_maos_e_o_modelo(repo: Path, tmp_path: Path) -> None:
    hands = FakeHands()
    events: list[tuple[str, Mapping[str, Any]]] = []
    mind, _, steps = _mind(
        Scripted(),
        repo,
        tmp_path,
        background=False,
        events=events,
        hands={"claude_code": hands},
        hands_instructions="Termine com um resumo.",
    )
    chosen = {"maos": "claude_code", "modelo": "claude-opus-5-5"}
    deliver = await mind.decide(_snapshot(chosen=chosen))
    assert deliver is not None
    assert deliver["action"] == "deliver"
    assert deliver["params"]["patch"]["files"] == ["ola.py"]
    (job,) = hands.jobs
    assert job.model == "claude-opus-5-5"
    assert job.system.endswith("Termine com um resumo.")  # as instruções das mãos de fora
    assert "Trabalhe." not in job.system
    assert job.limits.max_turns == 80  # os tetos da sessão (ADR-0089, decisão 8)
    assert steps == ["Write", "fim:claude_code:pronto"]
    step = dict(events[0][1])
    assert (events[0][0], step["harness"], step["model"]) == (
        "campsverso.workshop.step.v2",
        "claude_code",
        "claude-opus-5-5",
    )
    kind, finished = events[-1]
    assert kind == "campsverso.workshop.session_finished.v1"
    assert (finished["turns"], finished["steps"], finished["cost_usd"]) == (3, 1, 0.42)
    assert finished["model"] == "claude-opus-5-5"


def _not_outside(model: str) -> bool:
    return model != "gpt-de-fora"


async def test_maos_que_nao_estao_ligadas_viram_o_sistema_padrao_do_dev(
    repo: Path, tmp_path: Path
) -> None:
    """O Codex escolhido sem a chave da OpenAI: o pedido vai ao sistema padrão do dev, com o modelo
    dele, e nunca ao par que não fecha (o Claude Code com o Astra)."""
    hands = FakeHands()
    telemetry = MemoryTelemetry()
    mind, _, steps = _mind(
        Scripted(),
        repo,
        tmp_path,
        background=False,
        telemetry=telemetry,
        hands={"claude_code": hands},
        default_harness="claude_code",
        hands_model="claude-opus-5-5",
    )
    deliver = await mind.decide(_snapshot(chosen={"maos": "codex", "modelo": "gpt-6.2-astra"}))
    assert deliver is not None
    assert deliver["action"] == "deliver"
    assert hands.jobs[0].model == "claude-opus-5-5"
    assert steps[-1] == "fim:claude_code:pronto"
    assert "mind.hands_unavailable" in set(telemetry.events())


async def test_sem_o_padrao_ligado_o_nosso_harness_com_o_modelo_da_mente(
    repo: Path, tmp_path: Path
) -> None:
    port = Scripted([_use("escrever", path="a.py", content="A = 1\n")], [_use("pronto")])
    telemetry = MemoryTelemetry()
    mind, _, steps = _mind(
        port, repo, tmp_path, background=False, telemetry=telemetry, default_harness="codex"
    )
    deliver = await mind.decide(_snapshot())
    assert deliver is not None
    assert steps == ["escrever", "pronto", "fim:api:pronto"]
    assert port.requests[0].model == "claude-sonnet-5-5"
    assert "mind.hands_unavailable" in set(telemetry.events())


async def test_um_modelo_que_a_porta_nao_atende_vira_o_da_mente(repo: Path, tmp_path: Path) -> None:
    port = Scripted([_use("escrever", path="a.py", content="A = 1\n")], [_use("pronto")])
    telemetry = MemoryTelemetry()
    mind, _, steps = _mind(
        port, repo, tmp_path, background=False, telemetry=telemetry, model_ok=_not_outside
    )
    deliver = await mind.decide(_snapshot(chosen={"maos": "api", "modelo": "gpt-de-fora"}))
    assert deliver is not None
    assert steps == ["escrever", "pronto", "fim:api:pronto"]
    assert port.requests[0].model == "claude-sonnet-5-5"
    assert "mind.model_unavailable" in set(telemetry.events())


async def test_o_texto_do_modelo_antes_da_ferramenta_vai_no_passo(
    repo: Path, tmp_path: Path
) -> None:
    """ADR-0093, decisão 12: no nosso harness, o texto da resposta vai no passo da primeira
    ferramenta dela, como o comentário da tela do dev."""
    said = {"type": "text", "text": "Vou criar o a.py\ncom a constante."}
    port = Scripted([said, _use("escrever", path="a.py", content="A = 1\n")], [_use("pronto")])
    events: list[tuple[str, Mapping[str, Any]]] = []
    mind, _, _ = _mind(port, repo, tmp_path, background=False, events=events)
    deliver = await mind.decide(_snapshot())
    assert deliver is not None
    notes = [d.get("note") for kind, d in events if kind == "campsverso.workshop.step.v2"]
    assert notes == ["Vou criar o a.py com a constante.", None]


# O elenco do M27 e um dev só de teste, cada um com a mente e o sistema padrão dele.
DEVS: dict[str, dict[str, Any]] = {
    "tiago": {"model": "claude-opus-5-5", "default_harness": "claude_code"},
    "kenji": {
        "model": "openai/gpt-6.2-astra",
        "default_harness": "codex",
        "hands_model": "gpt-6.2-astra",
    },
}
# Os sistemas do catálogo do escritório (o office.yaml), e o padrão do dev (None).
SYSTEMS: list[tuple[str, str] | None] = [
    None,
    ("api", "claude-sonnet-5-5"),
    ("claude_code", "claude-opus-5-5"),
    ("codex", "gpt-6.2-astra"),
]


@pytest.mark.parametrize("system", SYSTEMS, ids=lambda s: "padrao" if s is None else s[0])
@pytest.mark.parametrize("dev", list(DEVS))
async def test_cada_dev_programa_com_cada_sistema(
    repo: Path, tmp_path: Path, dev: str, system: tuple[str, str] | None
) -> None:
    """A ADR-0093, decisão 18: o dev e o sistema são independentes. Cada dev, com a mente e o
    cartão dele, programa por qualquer sistema do catálogo; sem escolha, pelo padrão dele."""
    settings = DEVS[dev]
    outside = {"claude_code": FakeHands("claude_code"), "codex": FakeHands("codex")}
    port = Scripted([_use("escrever", path="a.py", content="A = 1\n")], [_use("pronto")])
    card = f"Você é o {dev.capitalize()}."
    mind, _, steps = _mind(
        port, repo, tmp_path, background=False, card=card, hands=outside, **settings
    )
    chosen = None if system is None else {"maos": system[0], "modelo": system[1]}
    deliver = await mind.decide(_snapshot(chosen=chosen))
    assert deliver is not None
    assert deliver["action"] == "deliver"
    default = (settings["default_harness"], settings.get("hands_model", settings["model"]))
    harness, model = default if system is None else system
    assert steps[-1] == f"fim:{harness}:pronto"
    for name, hands in outside.items():
        assert len(hands.jobs) == (1 if name == harness else 0)
    if harness == "api":
        assert port.requests[0].model == model
        assert card in str(port.requests[0].system)
    else:
        (job,) = outside[harness].jobs
        assert job.model == model
        assert job.system.startswith(card)
        assert port.requests == []


BRIEFING_ROBOT = {
    "entity_id": "robo-briefing",
    "kind": "robot",
    "position": {"x": 8, "y": 4},
    "attributes": {
        "nome": "briefing",
        "modulo": "tools.briefing",
        "descricao": "Monta o briefing.",
    },
}


def _briefing(repo: Path, body: str) -> None:
    (repo / "tools").mkdir(exist_ok=True)
    (repo / "tools" / "__init__.py").write_text("")
    (repo / "tools" / "briefing.py").write_text(body)
    subprocess.run([*GIT, "-C", str(repo), "add", "-A"], check=True)
    subprocess.run([*GIT, "-C", str(repo), "commit", "-q", "-m", "briefing"], check=True)


async def test_o_briefing_abre_a_sessao(repo: Path, tmp_path: Path) -> None:
    _briefing(
        repo,
        "import sys\nfrom pathlib import Path\n\n"
        "print('# Briefing')\nprint(Path(sys.argv[1]).read_text())\n"
        "print('## Notas da memória')\nprint(Path(sys.argv[2]).read_text())\n",
    )
    port = Scripted([_use("pronto", resumo="Feito.")])
    mind, _, steps = _mind(port, repo, tmp_path, background=False)
    await mind.decide(_snapshot(extra=[BRIEFING_ROBOT]))
    opening = port.requests[0].messages[0]["content"][0]["text"]
    assert opening.startswith("# Briefing\nPedido 1: Testador")
    assert "chamando o robô" not in opening  # a linha da tela não entra
    assert steps[:2] == [
        "campsverso.workshop.robot_started.v1:robo-briefing",
        "campsverso.workshop.robot_called.v1:robo-briefing",
    ]
    space = tmp_path / "oficina" / "office-teste" / "pedido-001"
    assert (space / ".oficina" / "pedido.md").read_text().startswith("Pedido 1: Testador")


async def test_se_o_briefing_falha_a_sessao_abre_como_antes(repo: Path, tmp_path: Path) -> None:
    _briefing(repo, "raise SystemExit('quebrado')\n")
    port = Scripted([_use("pronto", resumo="Feito.")])
    telemetry = MemoryTelemetry()
    mind, _, _ = _mind(port, repo, tmp_path, background=False, telemetry=telemetry)
    await mind.decide(_snapshot(extra=[BRIEFING_ROBOT]))
    assert port.requests[0].messages[0]["content"][0]["text"].startswith("Pedido 1: Testador")
    assert "mind.briefing_failed" in telemetry.events("warning")
