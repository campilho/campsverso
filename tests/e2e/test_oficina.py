"""A oficina de ponta a ponta (ADR-0080): a sessão do dev num clone, a entrega no depósito e o
`make aplicar`, que confere de novo e põe o patch num ramo, sem mexer no checkout de quem roda."""

import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import DiskBlobStore
from campsverso_adapters.workshop_local import LocalWorkshop
from campsverso_adapters.workshop_review import review
from campsverso_controller_runner.workshop import WorkshopSession
from campsverso_testkit.aplicar import apply, latest

GIT = [
    "git",
    "-c",
    "user.name=Teste",
    "-c",
    "user.email=teste@exemplo",
    "-c",
    "commit.gpgsign=false",
]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        [*GIT, "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("Um repositório de exemplo.\n")
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    (root / "rascunho.txt").write_text("o checkout de quem roda não muda\n")
    return root


async def test_a_entrega_vira_um_ramo(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Teste")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "teste@exemplo")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Teste")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "teste@exemplo")
    deliveries = tmp_path / "entregas"
    steps: list[Mapping[str, Any]] = []

    async def publish(_: str, data: Mapping[str, Any]) -> None:
        steps.append(data)

    session = WorkshopSession(
        "office-teste",
        "tiago",
        LocalWorkshop(repo, tmp_path / "oficina", python_env=False, python=Path(sys.executable)),
        DiskBlobStore(deliveries),
        lambda diff: review(diff, []),
        publish,
    )
    work: dict[str, Any] = {
        "ticket_id": "pedido-003",
        "steps": [
            {
                "tool": "escrever",
                "args": {"path": "tools/robos/testador.py", "content": "OK = 1\n"},
            },
            {"tool": "pronto", "args": {}},
        ],
    }
    await session.run({"action": "deliver", "params": {}}, work, "01xyz")
    patch, about = latest(deliveries, "office-teste", 3)
    monkeypatch.chdir(tmp_path)  # o caminho relativo do patch, como o make aplicar o passa
    branch = apply(patch.relative_to(tmp_path), about, 3, [], repo)
    assert branch == "dev/pedido-3"
    assert "OK = 1" in _git(repo, "show", f"{branch}:tools/robos/testador.py")
    assert _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() == "main"  # o checkout não mudou
    assert (repo / "rascunho.txt").exists()
    assert not (repo / "tools").exists()
    with pytest.raises(SystemExit, match="já existe"):
        apply(patch, about, 3, [], repo)
    with pytest.raises(SystemExit, match="revisão"):
        apply(patch, about, 4, ["testador"], repo)  # a lista proibida vale de novo
    broken = tmp_path / "quebrado.patch"
    broken.write_text("diff --git a/x b/x\nlixo\n")
    with pytest.raises(SystemExit):
        apply(broken, about, 5, [], repo)
    assert not _git(repo, "branch", "--list", "dev/pedido-5").strip()  # sem ramo vazio
