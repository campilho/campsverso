"""Os arquivos de uma entrega do dev (ADR-0083): o patch aplicado sobre a base, num clone local.

O publicador manda ao repositório de fora o texto inteiro de cada arquivo mudado, e não o patch.
Para isso, um clone compartilhado do repositório (sem copiar os objetos e sem mexer nele) vai para
a base e recebe o patch; o próprio git diz quais arquivos mudaram, e cada um sai com o texto novo,
ou `None` se o patch o apagou. Um arquivo renomeado aparece duas vezes: apagado no nome velho e
criado no novo.
"""

import asyncio
import tempfile
from pathlib import Path

from campsverso_ports import CodeHostError


async def _git(*args: str, cwd: Path | None = None, stdin: bytes | None = None) -> str:
    process = await asyncio.create_subprocess_exec(
        "git",
        *args,
        cwd=cwd,
        stdin=asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await process.communicate(stdin)
    if process.returncode != 0:
        raise CodeHostError(f"git {args[0]}: {err.decode(errors='replace').strip()[:300]}")
    return out.decode(errors="replace")


async def files_after_patch(repo: Path, base: str, patch: str) -> dict[str, str | None]:
    """O texto de cada arquivo que o patch muda sobre `base`; `None` para o que ele apaga."""
    with tempfile.TemporaryDirectory(prefix="campsverso-publicador-") as folder:
        clone = Path(folder) / "clone"
        await _git("clone", "-q", "--shared", "--no-checkout", str(repo), str(clone))
        await _git("checkout", "-q", "--detach", base, cwd=clone)
        if patch.strip():
            await _git(
                "apply", "--index", "--whitespace=nowarn", "-", cwd=clone, stdin=patch.encode()
            )
        names = await _git("diff", "--cached", "--name-only", "--no-renames", "-z", base, cwd=clone)
        files: dict[str, str | None] = {}
        for path in sorted(name for name in names.split("\0") if name):
            target = clone / path
            if target.is_symlink():
                raise CodeHostError(f"{path}: um link simbólico não vai ao repositório de fora")
            if not target.exists():
                files[path] = None
                continue
            try:
                files[path] = target.read_text(encoding="utf-8")
            except UnicodeDecodeError as error:
                raise CodeHostError(f"{path}: não é texto em UTF-8") from error
        return files
