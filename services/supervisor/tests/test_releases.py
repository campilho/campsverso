"""As versões pelo git de verdade (ADR-0083): um repositório nu no papel do GitHub, um clone no
papel da pasta de trabalho, e as duas worktrees do escritório vivo. Sem `uv` nem `pnpm`."""

import subprocess
from pathlib import Path

import pytest

from campsverso_supervisor.releases import CommandError, GitReleases

GIT = ["git", "-c", "user.name=T", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def _git(where: Path, *args: str) -> str:
    return subprocess.run(
        [*GIT, "-C", str(where), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(work: Path, name: str, message: str) -> str:
    (work / name).write_text(message + "\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", message)
    _git(work, "push", "-q", "origin", "HEAD:main")
    return _git(work, "rev-parse", "HEAD")


@pytest.fixture
def repos(tmp_path: Path) -> tuple[Path, Path, Path]:
    """O GitHub (nu), quem mescla (o autor) e a pasta de trabalho, que o supervisor usa."""
    hub = tmp_path / "hub.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(hub)], check=True)
    author = tmp_path / "autor"
    subprocess.run(["git", "clone", "-q", str(hub), str(author)], check=True, capture_output=True)
    _commit(author, "README.md", "o começo")
    work = tmp_path / "trabalho"
    subprocess.run(["git", "clone", "-q", str(hub), str(work)], check=True, capture_output=True)
    return hub, author, work


async def test_busca_o_main_e_le_a_data_e_os_prs(repos: tuple[Path, Path, Path]) -> None:
    _, author, work = repos
    releases = GitReleases(work)
    first = await releases.fetch()
    _commit(author, "a.md", "Merge pull request #12 from campilho/dev/pedido-3")
    head = _commit(author, "b.md", "feat: uma busca no código (#14)")
    assert await releases.fetch() == head
    build = await releases.build(head, first)
    assert build.commit == head
    assert build.date[:4] >= "2026" or build.date[4] == "-"
    assert build.pull_requests == (12, 14)
    assert (await releases.build(head, None)).pull_requests == ()


async def test_as_duas_worktrees_presas_num_commit_com_os_links(
    repos: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    _, author, work = repos
    private = tmp_path / "privado"
    private.mkdir()
    releases = GitReleases(work, links={"privado": private})
    first = await releases.fetch()
    home = tmp_path / "vivo"
    await releases.place(home / "a", first)
    assert _git(home / "a", "rev-parse", "HEAD") == first
    assert (home / "a" / "privado").resolve() == private.resolve()
    # O link é só um arquivo solto na worktree: nada do repositório muda, e o commit é o mesmo.
    assert _git(home / "a", "status", "--porcelain") == "?? privado"
    second = _commit(author, "c.md", "outra versão")
    await releases.fetch()
    await releases.place(home / "b", second)
    await releases.place(home / "a", second)  # de novo, noutro commit: a mesma worktree
    assert _git(home / "a", "rev-parse", "HEAD") == second
    assert _git(home / "b", "rev-parse", "HEAD") == second
    (home / "c").mkdir()
    (home / "c" / "lixo").write_text("x")
    with pytest.raises(CommandError, match="não é uma worktree"):
        await releases.place(home / "c", second)
