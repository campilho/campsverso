"""Testador: roda os testes dos caminhos dados e devolve um resumo de até 5 linhas.

Uso: python -m tools.robos.testador <caminho> [<caminho> ...]
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path

_COUNT = re.compile(r"(\d+) (passed|failed|error|errors)")
_FAIL_LINE = re.compile(r"^(?P<where>\S+?\.py:\d+): (?P<msg>.*)$")


def summarize(output: str) -> str:
    """Resume a saída do pytest (rodado com `-q --tb=line`) em até 5 linhas."""
    counts = {"passed": 0, "failed": 0, "error": 0}
    for number, kind in _COUNT.findall(output):
        counts["error" if kind.startswith("error") else kind] += int(number)
    lines = [
        f"passaram: {counts['passed']}",
        f"falharam: {counts['failed']}",
    ]
    if counts["error"]:
        lines.append(f"erros: {counts['error']}")
    for raw in output.splitlines():
        match = _FAIL_LINE.match(raw.strip())
        if match:
            lines.append(f"primeira falha: {match['where']} {match['msg']}".rstrip())
            break
    else:
        if counts["failed"] or counts["error"]:
            lines.append("primeira falha: não achei arquivo e linha na saída")
    if not any(counts.values()):
        lines.append("nenhum teste rodou")
    return "\n".join(lines[:5])


def run(paths: Sequence[str]) -> str:
    """Roda o pytest nos caminhos e devolve o resumo."""
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            # O addopts do projeto já tem `-q`; um segundo `-q` some com a linha de resumo.
            "-o",
            "addopts=",
            "--import-mode=importlib",
            "-q",
            "--tb=line",
            "-p",
            "no:cacheprovider",
            *paths,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return summarize(proc.stdout + proc.stderr)


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CHECK_LINE = re.compile(r"^(?P<where>\S+?\.py:\d+):\d+: (?P<code>\S+)")
# Ruff antigo diz `Would reformat: arq.py`; o novo, `unformatted: ...` e ` --> arq.py:1:6`.
_FORMAT_LINE = re.compile(r"^(?:Would reformat: |--> )(?P<file>.+?\.py)(?::\d+:\d+)?$")


def _ruff(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def ruff_summary(paths: Sequence[str]) -> str:
    """Roda `ruff check` e `ruff format --check` nos .py dos caminhos; devolve uma linha."""
    targets = [p for p in paths if Path(p).is_dir() or p.endswith(".py")]
    if not targets:
        return "ruff: nenhum arquivo .py"
    config = ["--config", str(_REPO_ROOT / "pyproject.toml")]
    check_code, check_out = _ruff(
        "check", *config, "--output-format=concise", "--no-cache", *targets
    )
    format_code, format_out = _ruff("format", *config, "--check", "--no-cache", *targets)
    problems: list[str] = []
    for raw in check_out.splitlines():
        match = _CHECK_LINE.match(raw.strip())
        if match:
            problems.append(f"{match['where']} {match['code']}")
    for raw in format_out.splitlines():
        match = _FORMAT_LINE.match(raw.strip())
        if match:
            problems.append(f"{match['file']} formato")
    if problems:
        return f"ruff: {len(problems)} problemas; primeiro: {problems[0]}"
    if "No module named" in check_out + format_out:
        return "ruff: não consegui rodar (módulo ruff ausente)"
    if check_code != 0 or format_code != 0:
        return f"ruff: falhou (código {check_code} no check, {format_code} no format)"
    return "ruff: passou"


def _pyright_config() -> tuple[list[str], list[str]]:
    with (_REPO_ROOT / "pyproject.toml").open("rb") as handle:
        section = tomllib.load(handle)["tool"]["pyright"]
    return list(section["include"]), list(section["exclude"])


def _matches(relative: str, pattern: str) -> bool:
    """Casa um caminho relativo com um item do include/exclude do pyright."""
    pattern = pattern.rstrip("/")
    parts = relative.split("/")
    if pattern.startswith("**/"):
        return pattern[3:] in parts
    return relative == pattern or relative.startswith(pattern + "/")


def pyright_files(paths: Sequence[str]) -> list[str]:
    """Os .py dos caminhos que o include/exclude do pyright cobre (caminhos absolutos)."""
    include, exclude = _pyright_config()
    found: set[Path] = set()
    for raw in paths:
        path = Path(raw).resolve()
        if path.is_dir():
            found.update(p for p in path.rglob("*.py") if p.is_file())
        elif path.suffix == ".py" and path.is_file():
            found.add(path)
    covered: list[str] = []
    for file in sorted(found):
        try:
            relative = file.relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            continue
        if any(_matches(relative, p) for p in exclude):
            continue
        if any(_matches(relative, p) for p in include):
            covered.append(str(file))
    return covered


def _pyright(files: Sequence[str]) -> tuple[int, str]:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--project",
            str(_REPO_ROOT / "pyproject.toml"),
            "--outputjson",
            *files,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=_REPO_ROOT,
    )
    return proc.returncode, proc.stdout + proc.stderr


def pyright_summary(
    paths: Sequence[str],
    runner: Callable[[Sequence[str]], tuple[int, str]] = _pyright,
) -> str:
    """Roda o pyright estrito nos .py cobertos pela configuração; devolve uma linha."""
    files = pyright_files(paths)
    if not files:
        return "pyright: nenhum arquivo coberto"
    code, output = runner(files)
    try:
        report = json.loads(output)
        diagnostics = report["generalDiagnostics"]
    except (ValueError, KeyError, TypeError):
        return f"pyright: não consegui rodar (código {code})"
    errors = [d for d in diagnostics if d.get("severity") == "error"]
    if errors:
        first = errors[0]
        where = Path(str(first.get("file", "?")))
        try:
            shown = where.relative_to(_REPO_ROOT).as_posix()
        except ValueError:
            shown = where.as_posix()
        line = int(first.get("range", {}).get("start", {}).get("line", 0)) + 1
        rule = first.get("rule", "erro")
        return f"pyright: {len(errors)} erro(s); primeiro: {shown}:{line} {rule}"
    if code != 0:
        return f"pyright: falhou (código {code})"
    return "pyright: passou"


def main(argv: Sequence[str]) -> int:
    if not argv:
        print("uso: python -m tools.robos.testador <caminho> [<caminho> ...]")
        return 2
    print(run(argv))
    print(ruff_summary(argv))
    print(pyright_summary(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
