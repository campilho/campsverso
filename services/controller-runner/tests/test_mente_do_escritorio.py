"""A mente com rotina do dev do escritório (ADR-0080): a rotina conduz, o modelo trabalha na
oficina numa sessão em segundo plano e responde a quem fala; a entrega sai sem pedido de decisão."""

import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import MemoryBlobStore
from campsverso_adapters.workshop_local import LocalWorkshop
from campsverso_adapters.workshop_review import review
from campsverso_controller_runner.office_mind import OfficeMind
from campsverso_controller_runner.workshop import WorkshopSession
from campsverso_mind import Mind
from campsverso_ports import (
    ModelCallError,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    ModelUsage,
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
    *, heard: list[dict[str, Any]] | None = None, estado: str = "fazendo"
) -> dict[str, Any]:
    ticket = {
        "entity_id": "pedido-001",
        "kind": "ticket",
        "attributes": {
            "numero": 1,
            "titulo": "Testador",
            "descricao": "Rodar os testes.",
            "estado": estado,
            "dono": "camps",
        },
    }
    view: dict[str, Any] = {
        "clock": {"tick": 5, "sim_time": "2026-11-16T10:00:00-03:00", "day": 1},
        "self": {"entity_id": "camps", "position": {"x": 4, "y": 5}},
        "weather": {},
        "entities": [ticket],
        "containers": [],
    }
    if heard:
        view["heard"] = heard
    return {
        "avatar_id": "camps",
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
    port: Scripted, repo: Path, tmp_path: Path
) -> tuple[OfficeMind, list[Mapping[str, Any]], list[str]]:
    proposed: list[Mapping[str, Any]] = []
    steps: list[str] = []

    async def propose(proposal: Mapping[str, Any]) -> None:
        proposed.append(proposal)

    async def publish(_: str, data: Mapping[str, Any]) -> None:
        steps.append(str(data["tool"]))

    shop = WorkshopSession(
        "office-teste",
        "camps",
        LocalWorkshop(repo, tmp_path / "oficina", python_env=False, python=Path(sys.executable)),
        MemoryBlobStore(),
        lambda diff: review(diff, []),
        publish,
    )
    mind = OfficeMind(
        Routine(),
        Mind("office", card="Você é o Camps.", notes="O escritório.", tools=()),
        port,
        shop,
        controller_id="llm/camps",
        avatar_id="camps",
        model="claude-sonnet-5-5",
        session_tools=TOOLS,
        session_instructions="Trabalhe.",
        chat_instructions="Responda curto.",
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
    assert steps == ["escrever", "pronto"]
    # O pedido da sessão leva o do quadro, o ticket para a guarda e o resultado da ferramenta.
    assert "Pedido 1: Testador" in port.requests[0].messages[0]["content"][0]["text"]
    assert {r.ticket_id for r in port.requests} == {"pedido-001"}
    assert port.requests[1].messages[-1]["content"][0]["type"] == "tool_result"


async def test_quem_fala_com_o_dev_recebe_a_resposta_do_modelo(repo: Path, tmp_path: Path) -> None:
    port = Scripted(
        [{"type": "text", "text": "Tudo certo, já estou\\n nisso."}],
        ModelCallError("server", "caiu"),
    )
    mind, _, _ = _mind(port, repo, tmp_path)
    heard = [
        {"tick": 4, "avatar_id": "gerente", "text": "Como vai o testador?", "listener_id": "camps"}
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
