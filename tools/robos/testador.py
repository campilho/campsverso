"""Testador: roda os testes dos caminhos dados e devolve um resumo de até 5 linhas.

Uso: python -m tools.robos.testador <caminho> [<caminho> ...]
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Sequence
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


def _ruff(*args: str) -> str:
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout + proc.stderr


def ruff_summary(paths: Sequence[str]) -> str:
    """Roda `ruff check` e `ruff format --check` nos .py dos caminhos; devolve uma linha."""
    targets = [p for p in paths if Path(p).is_dir() or p.endswith(".py")]
    if not targets:
        return "ruff: nenhum arquivo .py"
    config = ["--config", str(_REPO_ROOT / "pyproject.toml")]
    check_out = _ruff("check", *config, "--output-format=concise", "--no-cache", *targets)
    format_out = _ruff("format", *config, "--check", "--no-cache", *targets)
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
    return "ruff: passou"


def main(argv: Sequence[str]) -> int:
    if not argv:
        print("uso: python -m tools.robos.testador <caminho> [<caminho> ...]")
        return 2
    print(run(argv))
    print(ruff_summary(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
