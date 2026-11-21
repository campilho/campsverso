"""As versões, pelo git do repositório de trabalho (ADR-0083).

O supervisor só lê o `origin/main`: nunca mescla, nunca empurra. As duas worktrees do escritório
vivo (`a` e `b`) saem do repositório de trabalho, presas num commit, sem ramo: ninguém edita ali
por engano. Cada uma ganha os links para o que fica fora do git e vale para todas as versões (a
pasta `privado/`, com a chave do App e a lista de palavras proibidas).

Preparar uma worktree é o que o `make setup` e o `make ui-build` fazem: as dependências Python e
TypeScript, pelos arquivos de trava, e a tela compilada. Com `offline`, nada vem da rede.
"""

import asyncio
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from campsverso_supervisor.cycle import Build

_MERGE = re.compile(r"Merge pull request #(\d+)")
_SQUASH = re.compile(r"\(#(\d+)\)\s*$")
TIMEOUT_SECONDS = 900.0  # o uv sync e o pnpm install de uma worktree nova


class CommandError(Exception):
    """Um comando da preparação falhou."""


async def _run(args: Sequence[str], cwd: Path, timeout: float = TIMEOUT_SECONDS) -> str:
    process = await asyncio.create_subprocess_exec(
        *args,
        cwd=cwd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(process.communicate(), timeout)
    except TimeoutError as error:
        process.kill()
        await process.wait()
        raise CommandError(f"{' '.join(args)}: passou de {timeout:.0f} s") from error
    text = out.decode(errors="replace")
    if process.returncode != 0:
        raise CommandError(f"{' '.join(args)}: {text.strip()[-600:]}")
    return text


class GitReleases:
    def __init__(
        self,
        repo: Path,
        *,
        remote: str = "origin",
        branch: str = "main",
        links: Mapping[str, Path] | None = None,
        offline: bool = False,
    ) -> None:
        self._repo = repo.resolve()
        self._remote, self._branch = remote, branch
        self._links = dict(links or {})
        self._offline = offline

    async def _git(self, *args: str, cwd: Path | None = None) -> str:
        return (await _run(["git", *args], cwd or self._repo, timeout=120)).strip()

    async def fetch(self) -> str:
        await self._git("fetch", "-q", self._remote, self._branch)
        return await self._git("rev-parse", f"{self._remote}/{self._branch}")

    async def build(self, commit: str, since: str | None) -> Build:
        date = await self._git("show", "-s", "--format=%cI", commit)
        prs: list[int] = []
        if since is not None:
            log = await self._git("log", "--format=%s", f"{since}..{commit}")
            for subject in log.splitlines():
                found = _MERGE.search(subject) or _SQUASH.search(subject)
                if found is not None and int(found.group(1)) not in prs:
                    prs.append(int(found.group(1)))
        return Build(commit, date, tuple(sorted(prs)[:100]))

    async def place(self, slot: Path, commit: str) -> None:
        if not (slot / ".git").exists():
            if slot.exists() and any(slot.iterdir()):
                raise CommandError(f"{slot} existe e não é uma worktree")
            slot.parent.mkdir(parents=True, exist_ok=True)
            await self._git("worktree", "add", "-q", "--detach", str(slot), commit)
        else:
            await self._git("checkout", "-q", "--force", "--detach", commit, cwd=slot)
        for name, target in self._links.items():
            link = slot / name
            if link.is_symlink() and link.resolve() == target.resolve():
                continue
            if link.is_symlink():
                link.unlink()
            elif link.exists():
                raise CommandError(f"{link} existe e não é o link para {target}")
            link.symlink_to(target)

    def prepared(self, slot: Path) -> bool:
        return (slot / ".venv" / "bin" / "python").exists()

    async def prepare(self, slot: Path) -> None:
        offline = ["--offline"] if self._offline else []
        await _run(["uv", "sync", "--locked", *offline], slot)
        await _run(["pnpm", "install", "--frozen-lockfile", *offline], slot)
        await _run(["pnpm", "-s", "--filter", "@campsverso/ui", "build"], slot)
