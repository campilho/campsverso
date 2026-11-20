"""A sessão do dev na oficina (ADR-0080): os passos pela porta, um `workshop.step.v1` por passo, o
patch no depósito de entregas e o resumo na proposta de entrega; a revisão recusa e o dev diz por
quê."""

import json
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import MemoryBlobStore
from campsverso_adapters.workshop_local import LocalWorkshop
from campsverso_adapters.workshop_review import review
from campsverso_controller_runner.workshop import STEP, WorkshopSession

GIT = [
    "git",
    "-c",
    "user.name=Teste",
    "-c",
    "user.email=teste@exemplo",
    "-c",
    "commit.gpgsign=false",
]
SESSION: dict[str, Any] = {
    "ticket_id": "pedido-001",
    "steps": [
        {"tool": "ler", "args": {"path": "README.md", "start": 1, "end": 5}},
        {
            "tool": "escrever",
            "args": {"path": "docs/oficina/pedido-001.md", "content": "# Pedido 1\n"},
        },
        {"tool": "ferramenta-que-nao-existe", "args": {}},
        {"tool": "ver_mudancas", "args": {}},
        {"tool": "pronto", "args": {}},
        {"tool": "escrever", "args": {"path": "depois.md", "content": "não roda"}},
    ],
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


def _session(
    repo: Path, tmp_path: Path, words: list[str]
) -> tuple[WorkshopSession, MemoryBlobStore, list[Mapping[str, Any]]]:
    steps: list[Mapping[str, Any]] = []

    async def publish(event_type: str, data: Mapping[str, Any]) -> None:
        assert event_type == STEP
        steps.append(data)

    blobs = MemoryBlobStore()
    shop = LocalWorkshop(repo, tmp_path / "oficina", python_env=False, python=Path(sys.executable))
    session = WorkshopSession(
        "office-teste", "camps", shop, blobs, lambda diff: review(diff, words), publish
    )
    return session, blobs, steps


async def test_a_sessao_entrega_o_patch_com_o_resumo(repo: Path, tmp_path: Path) -> None:
    session, blobs, steps = _session(repo, tmp_path, [])
    deliver: dict[str, Any] = {"action": "deliver", "params": {}, "intent": "entregar o pedido"}
    proposal = await session.run(deliver, SESSION, "01ABC")
    # A ferramenta desconhecida roda como recusa e não vira passo (o contrato só conhece as oito);
    # o passo depois do pronto não roda.
    assert [s["tool"] for s in steps] == ["ler", "escrever", "ver_mudancas", "pronto"]
    assert all(s["ok"] for s in steps)
    assert steps[1]["summary"] == "escrevendo docs/oficina/pedido-001.md"
    assert steps[1]["path"] == "docs/oficina/pedido-001.md"
    patch = proposal["params"]["patch"]
    assert patch["ref"] == "office-teste/pedido-001/01abc.patch"
    assert (patch["files"], patch["added"], patch["removed"]) == (
        ["docs/oficina/pedido-001.md"],
        1,
        0,
    )
    assert len(patch["base"]) == 40
    assert "+# Pedido 1" in blobs.get(patch["ref"]).decode()
    about = json.loads(blobs.get("office-teste/pedido-001/01abc.json"))
    assert about["files"] == ["docs/oficina/pedido-001.md"]
    assert proposal["action"] == "deliver"


async def test_a_revisao_recusa_e_o_dev_diz_por_que(repo: Path, tmp_path: Path) -> None:
    session, _, _ = _session(repo, tmp_path, ["pedido"])  # a palavra está no arquivo
    deliver: dict[str, Any] = {"action": "deliver", "params": {}, "intent": "entregar o pedido"}
    proposal = await session.run(deliver, SESSION, "01ABD")
    assert proposal["action"] == "say"
    assert "lista proibida" in proposal["params"]["text"]


async def test_sem_pronto_a_entrega_vai_sem_patch(repo: Path, tmp_path: Path) -> None:
    session, _, steps = _session(repo, tmp_path, [])
    unfinished: dict[str, Any] = {"ticket_id": "pedido-002", "steps": SESSION["steps"][:2]}
    deliver: dict[str, Any] = {"action": "deliver", "params": {}, "intent": "entregar o pedido"}
    assert await session.run(deliver, unfinished, "01ABE") == deliver
    assert len(steps) == 2


async def test_a_oficina_que_cai_vira_uma_fala_e_nao_derruba_o_controlador(tmp_path: Path) -> None:
    """O clone falha (aqui, o repositório não existe; no CI de 19/nov, o ambiente Python): o dev diz
    que a oficina falhou, e a proposta segue para o kernel em vez de derrubar o controlador."""
    session, blobs, steps = _session(tmp_path / "nao-existe", tmp_path, [])
    deliver: dict[str, Any] = {"action": "deliver", "params": {}, "intent": "entregar o pedido"}
    proposal = await session.run(deliver, SESSION, "01ABF")
    assert proposal["action"] == "say"
    assert proposal["params"]["text"] == "Não consegui trabalhar no pedido: a oficina falhou."
    assert proposal["intent"].startswith("a oficina falhou: o clone falhou")
    assert steps == []
    assert session.delivered == 0
    assert blobs.blobs == {}


async def test_a_sessao_fixa_chama_o_robo_e_entrega_mesmo_se_ele_falhar(
    repo: Path, tmp_path: Path
) -> None:
    """O dev-script chama o robô da bancada antes de entregar (o plano do M24, §4): o robô começa e
    termina nos fatos da oficina, para a tela o animar; um robô que falha não segura a entrega."""
    (repo / "tools").mkdir()
    (repo / "tools" / "__init__.py").write_text("")
    (repo / "tools" / "eco.py").write_text("import sys\n\nprint('eco:', *sys.argv[1:])\n")
    subprocess.run([*GIT, "-C", str(repo), "add", "-A"], check=True)
    subprocess.run([*GIT, "-C", str(repo), "commit", "-q", "-m", "eco"], check=True)
    events: list[tuple[str, Mapping[str, Any]]] = []

    async def publish(event_type: str, data: Mapping[str, Any]) -> None:
        events.append((event_type, data))

    shop = LocalWorkshop(repo, tmp_path / "oficina", python_env=False, python=Path(sys.executable))
    session = WorkshopSession(
        "office-teste", "camps", shop, MemoryBlobStore(), lambda diff: review(diff, []), publish
    )

    def robot(robot_id: str, module: str) -> dict[str, Any]:
        args = {"robo": robot_id, "modulo": module, "argumentos": ["tools", "tests"]}
        return {"tool": "chamar_robo", "args": args}

    steps = SESSION["steps"]
    fixed: dict[str, Any] = {
        "ticket_id": "pedido-001",
        "steps": [
            steps[0],
            steps[1],
            robot("robo-eco", "tools.eco"),
            robot("robo-sumido", "tools.sumido"),  # o módulo não existe: o robô falha
            {"tool": "chamar_robo", "args": {"argumentos": []}},  # sem robô: não roda
            steps[3],
            steps[4],
        ],
    }
    deliver: dict[str, Any] = {"action": "deliver", "params": {}, "intent": "entregar o pedido"}
    proposal = await session.run(deliver, fixed, "01AC0")
    assert proposal["action"] == "deliver"
    assert proposal["params"]["patch"]["files"] == ["docs/oficina/pedido-001.md"]
    robots = [(t.rsplit(".", 2)[-2], d["robot_id"]) for t, d in events if "robot_id" in d]
    assert robots == [
        ("robot_started", "robo-eco"),
        ("robot_called", "robo-eco"),
        ("robot_started", "robo-sumido"),
        ("robot_called", "robo-sumido"),
    ]
    called = [d for t, d in events if t == "campsverso.workshop.robot_called.v1"]
    assert [d["ok"] for d in called] == [True, False]
    assert called[0]["args"] == ["tools", "tests"]
    tools = [d["tool"] for t, d in events if t == STEP]
    assert tools == ["ler", "escrever", "ver_mudancas", "pronto"]
