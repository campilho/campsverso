"""A oficina local (ADR-0055, ADR-0080; o plano do M24, §3): um clone raso do repositório por
pedido, em `data/oficina/<mundo>/<pedido>/`, com as oito ferramentas e os limites delas.

- **O clone é isolado:** tem o próprio `.git` (um `git clone` pelo `file://`, e não uma worktree,
  que dividiria o `.git` com o repositório de verdade). Nele não há `.env`, `data/` nem `privado/`,
  que estão fora do git.
- **O ambiente Python** sai do cache do `uv`, sem rede (`uv sync --offline --frozen`).
- **Os caminhos:** toda ferramenta resolve o caminho e recusa o que sai do espaço, inclusive por
  link simbólico, e o que entra no `.git`.
- **Os testes** rodam sob o `sandbox-exec` do macOS: sem rede, escrita só no espaço, e um ambiente
  sem segredos (só o `PATH` e um `HOME` dentro do espaço).
"""

import asyncio
import contextlib
import os
import re
import shutil
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from campsverso_ports import Patch, PatchSummary, ToolResult, WorkshopError

MAX_NAMES = 200
MAX_READ_LINES = 300
MAX_RESULTS = 50
MAX_WRITE_LINES = 2000
MAX_TEST_LINES = 60
MAX_DIFF_LINES = 400
TEST_SECONDS = 120.0
SKIPPED_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".oficina", ".pytest_cache"}
# O que fica do espaço fora do diff: a casa e o temporário dos testes.
LOCAL = ".oficina"
# Os robôs da bancada (o plano do M24, §4): um módulo Python, com poucos argumentos curtos.
ROBOT_MODULE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*")
MAX_ROBOT_ARGS = 20
MAX_ROBOT_ARG = 300
_SUMMARY = re.compile(r"(\d+) (passed|failed|error|errors|skipped|xfailed|xpassed)")
_PLURAL = {"passed": "passaram", "failed": "falharam", "error": "erro", "errors": "erros"}


def _sandbox_profile(workspace: Path, temp: Path) -> str:
    """O perfil do `sandbox-exec`: tudo, menos a rede e a escrita fora do espaço."""
    return (
        "(version 1)\n"
        "(allow default)\n"
        "(deny network*)\n"
        "(deny file-write*)\n"
        f'(allow file-write* (subpath "{workspace}") (subpath "{temp}")'
        ' (literal "/dev/null") (literal "/dev/tty") (subpath "/dev/fd"))\n'
    )


def _one_line(text: str, limit: int = 120) -> str:
    line = " ".join(text.split())
    return line if len(line) <= limit else line[: limit - 1] + "…"


async def _run(
    args: Sequence[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float | None = None,
) -> tuple[int, str]:
    process = await asyncio.create_subprocess_exec(
        *args,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(process.communicate(), timeout)
    except TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            process.kill()
        await process.wait()
        return -1, ""
    return int(process.returncode or 0), out.decode("utf-8", errors="replace")


class LocalWorkspace:
    """Um espaço de trabalho aberto: o clone de um pedido."""

    def __init__(
        self,
        root: Path,
        ticket_id: str,
        base: str,
        *,
        python: Path | None = None,
        sandbox: bool = True,
        test_seconds: float = TEST_SECONDS,
    ) -> None:
        self._root = root.resolve()
        self._ticket_id = ticket_id
        self._base = base
        self._python = python or self._root / ".venv" / "bin" / "python"
        self._sandbox = sandbox
        self._test_seconds = test_seconds

    @property
    def ticket_id(self) -> str:
        return self._ticket_id

    @property
    def base(self) -> str:
        return self._base

    @property
    def root(self) -> Path:
        return self._root

    # ------------------------------------------------------------- os caminhos

    def _resolve(self, path: str) -> Path | None:
        """O caminho dentro do espaço, ou None se ele sai dele (por `..`, absoluto ou por um link
        simbólico) ou entra no `.git`."""
        target = (self._root / path).resolve()
        if target != self._root and self._root not in target.parents:
            return None
        relative = target.relative_to(self._root)
        if relative.parts and relative.parts[0] == ".git":
            return None
        return target

    def _relative(self, path: Path) -> str:
        return str(path.relative_to(self._root)) or "."

    def _refuse(self, path: str) -> ToolResult:
        return ToolResult(False, f"{path}: fora do espaço de trabalho", f"recusado: {path}", path)

    # ------------------------------------------------------------- as ferramentas

    async def list_files(self, path: str = ".") -> ToolResult:
        where = self._resolve(path)
        if where is None:
            return self._refuse(path)
        if not where.exists():
            return ToolResult(
                False, f"{path}: não existe", f"ver_arquivos {path}: não existe", path
            )
        if where.is_file():
            return ToolResult(True, self._relative(where), f"ver_arquivos {path}", path)
        names: list[str] = []
        total = 0
        for current, dirs, files in os.walk(where):
            dirs[:] = sorted(d for d in dirs if d not in SKIPPED_DIRS)
            for name in sorted(files):
                total += 1
                if len(names) < MAX_NAMES:
                    names.append(self._relative(Path(current) / name))
        more = f"\n... e mais {total - len(names)} arquivo(s)" if total > len(names) else ""
        summary = f"vendo {path}: {total} arquivo(s)"
        return ToolResult(True, "\n".join(names) + more, summary, path)

    async def read(self, path: str, start: int = 1, end: int | None = None) -> ToolResult:
        where = self._resolve(path)
        if where is None:
            return self._refuse(path)
        if not where.is_file():
            return ToolResult(False, f"{path}: não é um arquivo", f"lendo {path}: não existe", path)
        lines = where.read_text(encoding="utf-8", errors="replace").splitlines()
        first = max(1, start)
        last = min(len(lines), end if end is not None else len(lines), first + MAX_READ_LINES - 1)
        body = "\n".join(f"{n:>5}| {lines[n - 1]}" for n in range(first, last + 1))
        more = f"\n... o arquivo tem {len(lines)} linhas" if last < len(lines) else ""
        return ToolResult(True, body + more, f"lendo {path} ({first}-{last})", path)

    async def search(self, pattern: str, path: str = ".") -> ToolResult:
        where = self._resolve(path)
        if where is None:
            return self._refuse(path)
        try:
            expression = re.compile(pattern)
        except re.error as error:
            return ToolResult(False, f"expressão inválida: {error}", "buscando: inválida", path)
        found: list[str] = []
        files = [where] if where.is_file() else []
        if where.is_dir():
            for current, dirs, names in os.walk(where):
                dirs[:] = sorted(d for d in dirs if d not in SKIPPED_DIRS)
                files += [Path(current) / name for name in sorted(names)]
        for file in files:
            try:
                text = file.read_text(encoding="utf-8")
            except UnicodeDecodeError, OSError:
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                if expression.search(line):
                    found.append(f"{self._relative(file)}:{number}: {line.strip()[:200]}")
                    if len(found) >= MAX_RESULTS:
                        break
            if len(found) >= MAX_RESULTS:
                break
        summary = f"buscando {_one_line(pattern, 40)}: {len(found)} resultado(s)"
        return ToolResult(True, "\n".join(found) or "nenhum resultado", summary, path)

    async def write(self, path: str, content: str) -> ToolResult:
        where = self._resolve(path)
        if where is None or where == self._root:
            return self._refuse(path)
        lines = content.count("\n") + (0 if content.endswith("\n") or not content else 1)
        if lines > MAX_WRITE_LINES:
            text = f"{path}: {lines} linhas, mais que {MAX_WRITE_LINES}"
            return ToolResult(False, text, f"escrevendo {path}: grande demais", path)
        where.parent.mkdir(parents=True, exist_ok=True)
        where.write_text(content, encoding="utf-8")
        return ToolResult(True, f"{path}: {lines} linha(s)", f"escrevendo {path}", path)

    async def edit(self, path: str, old: str, new: str) -> ToolResult:
        where = self._resolve(path)
        if where is None:
            return self._refuse(path)
        if not where.is_file():
            return ToolResult(
                False, f"{path}: não é um arquivo", f"editando {path}: não existe", path
            )
        text = where.read_text(encoding="utf-8")
        count = text.count(old) if old else 0
        if count != 1:
            why = "não aparece" if count == 0 else f"aparece {count} vezes"
            return ToolResult(False, f"{path}: o trecho {why}", f"editando {path}: {why}", path)
        where.write_text(text.replace(old, new, 1), encoding="utf-8")
        return ToolResult(True, f"{path}: trocado", f"editando {path}", path)

    async def run_tests(self, path: str = ".") -> ToolResult:
        where = self._resolve(path)
        if where is None:
            return self._refuse(path)
        home, temp = self._root / LOCAL / "home", self._root / LOCAL / "tmp"
        home.mkdir(parents=True, exist_ok=True)
        temp.mkdir(parents=True, exist_ok=True)
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(home),
            "TMPDIR": str(temp),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TZ": "UTC",
        }
        command = [
            str(self._python),
            "-m",
            "pytest",
            self._relative(where),
            "-p",
            "no:cacheprovider",
            "--no-header",
            "--maxfail=20",
        ]
        if self._sandbox:
            command = ["/usr/bin/sandbox-exec", "-p", _sandbox_profile(self._root, temp), *command]
        started = time.monotonic()
        code, out = await _run(command, self._root, env, self._test_seconds)
        took = time.monotonic() - started
        if code == -1:
            text = f"os testes passaram de {int(self._test_seconds)} s e foram parados"
            return ToolResult(False, text, "rodando os testes: tempo esgotado", path)
        lines = out.splitlines()
        # A linha do resumo do pytest ("1 failed, 2 passed in 0.1s"), a última que aparece; o `-q`
        # do repositório e um outro somados a escondiam.
        last = next((line for line in reversed(lines) if _SUMMARY.search(line)), "")
        counts = {kind: int(n) for n, kind in _SUMMARY.findall(last)}
        failures = [line for line in lines if line.startswith(("FAILED", "ERROR", "E "))]
        tail = "\n".join((failures or lines)[:MAX_TEST_LINES])
        parts = [f"{n} {_PLURAL.get(kind, kind)}" for kind, n in counts.items()]
        summary = "rodando os testes: " + (", ".join(parts) or f"saída {code}")
        text = f"{summary} ({took:.1f} s)\n{tail}".rstrip()
        return ToolResult(code == 0, text, summary, path)

    async def run_robot(self, module: str, args: Sequence[str] = ()) -> ToolResult:
        """Um robô da bancada: `python -m <module> <args>`, no espaço, sem rede e sem escrever
        fora dele, até o limite de tempo dos testes. A saída volta inteira até 60 linhas; mais
        que isso, as últimas, onde fica o resumo."""
        line = f"chamando o robô {module}"
        if not ROBOT_MODULE.fullmatch(module):
            return ToolResult(False, f"{module!r} não é um módulo Python", f"{line}: recusado")
        given = [str(a) for a in args]
        if len(given) > MAX_ROBOT_ARGS or any(len(a) > MAX_ROBOT_ARG or "\0" in a for a in given):
            text = f"até {MAX_ROBOT_ARGS} argumentos, de até {MAX_ROBOT_ARG} caracteres"
            return ToolResult(False, text, f"{line}: recusado")
        home, temp = self._root / LOCAL / "home", self._root / LOCAL / "tmp"
        home.mkdir(parents=True, exist_ok=True)
        temp.mkdir(parents=True, exist_ok=True)
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(home),
            "TMPDIR": str(temp),
            "PYTHONDONTWRITEBYTECODE": "1",
            "TZ": "UTC",
        }
        command = [str(self._python), "-m", module, *given]
        if self._sandbox:
            command = ["/usr/bin/sandbox-exec", "-p", _sandbox_profile(self._root, temp), *command]
        started = time.monotonic()
        code, out = await _run(command, self._root, env, self._test_seconds)
        took = time.monotonic() - started
        if code == -1:
            text = f"o robô passou de {int(self._test_seconds)} s e foi parado"
            return ToolResult(False, text, f"{line}: tempo esgotado")
        lines = out.splitlines()
        shown = lines if len(lines) <= MAX_TEST_LINES else lines[-MAX_TEST_LINES:]
        summary = f"{line}: saída {code}"
        text = f"{summary} ({took:.1f} s)\n" + "\n".join(shown)
        return ToolResult(code == 0, text.rstrip(), summary)

    async def _git(self, *args: str) -> str:
        code, out = await _run(["git", "-C", str(self._root), *args], self._root)
        if code != 0:
            raise WorkshopError(f"git {' '.join(args)}: {out.strip()}")
        return out

    async def diff(self) -> ToolResult:
        text = await self._full_diff()
        lines = text.splitlines()
        shown = "\n".join(lines[:MAX_DIFF_LINES])
        more = f"\n... o diff tem {len(lines)} linhas" if len(lines) > MAX_DIFF_LINES else ""
        summary = await self._numstat()
        counts = f"{len(summary.files)} arquivo(s), +{summary.added} -{summary.removed}"
        line = f"vendo as mudanças: {counts}"
        return ToolResult(True, (shown + more) or "nenhuma mudança", line)

    async def _full_diff(self) -> str:
        await self._git("add", "-A", "-N")  # os arquivos novos entram no diff
        return await self._git("diff", "--no-color", "--no-ext-diff", self._base)

    async def _numstat(self) -> PatchSummary:
        await self._git("add", "-A", "-N")
        out = await self._git("diff", "--numstat", self._base)
        files: list[str] = []
        added = removed = 0
        for row in out.splitlines():
            plus, minus, name = row.split("\t", 2)
            files.append(name)
            added += int(plus) if plus.isdigit() else 0
            removed += int(minus) if minus.isdigit() else 0
        return PatchSummary(self._base, tuple(files), added, removed)

    async def patch(self) -> Patch:
        return Patch(await self._full_diff(), await self._numstat())


class LocalWorkshop:
    """A oficina na máquina: os espaços em `root/<mundo>/<pedido>/`, clonados de `repo`."""

    def __init__(
        self,
        repo: Path,
        root: Path,
        *,
        python_env: bool = True,
        python: Path | None = None,
        sandbox: bool | None = None,
        test_seconds: float = TEST_SECONDS,
    ) -> None:
        self._repo = repo.resolve()
        # Absoluto: o clone roda a partir da pasta do mundo, e um caminho relativo (o `--data-dir`
        # do sandbox) criava o espaço aninhado dentro dela.
        self._root = root.resolve()
        self._python_env = python_env
        self._python = python
        # O `sandbox-exec` é do macOS; noutro sistema, os testes rodam sem ele (o CI).
        self._sandbox = sys.platform == "darwin" if sandbox is None else sandbox
        self._test_seconds = test_seconds

    def _where(self, worldid: str, ticket_id: str) -> Path:
        for part in (worldid, ticket_id):
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", part):
                raise WorkshopError(f"nome inválido para a oficina: {part!r}")
        return self._root / worldid / ticket_id

    async def open(self, worldid: str, ticket_id: str) -> LocalWorkspace:
        where = self._where(worldid, ticket_id)
        if not (where / ".git").is_dir():
            where.parent.mkdir(parents=True, exist_ok=True)
            code, out = await _run(
                ["git", "clone", "--quiet", "--depth", "1", f"file://{self._repo}", str(where)],
                where.parent,
            )
            if code != 0:
                raise WorkshopError(f"o clone falhou: {out.strip()}")
            exclude = where / ".git" / "info" / "exclude"
            exclude.parent.mkdir(parents=True, exist_ok=True)
            with exclude.open("a", encoding="utf-8") as file:
                file.write(f"\n{LOCAL}/\n.venv/\n")
            if self._python_env:
                env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(Path.home())}
                code, out = await _run(
                    ["uv", "sync", "--offline", "--frozen", "--quiet"], where, env, 600
                )
                if code != 0:
                    raise WorkshopError(f"o ambiente Python não subiu: {out.strip()[-500:]}")
        code, out = await _run(["git", "-C", str(where), "rev-parse", "HEAD"], where)
        if code != 0:
            raise WorkshopError(f"o espaço não tem commit: {out.strip()}")
        return LocalWorkspace(
            where,
            ticket_id,
            out.strip(),
            python=self._python,
            sandbox=self._sandbox,
            test_seconds=self._test_seconds,
        )

    async def close(self, worldid: str, ticket_id: str) -> None:
        shutil.rmtree(self._where(worldid, ticket_id), ignore_errors=True)
