"""Testador: roda os testes dos caminhos dados e devolve um resumo de até 5 linhas.

Uso: python -m tools.robos.testador <caminho> [<caminho> ...]
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Sequence

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
        [sys.executable, "-m", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider", *paths],
        capture_output=True,
        text=True,
        check=False,
    )
    return summarize(proc.stdout + proc.stderr)


def main(argv: Sequence[str]) -> int:
    if not argv:
        print("uso: python -m tools.robos.testador <caminho> [<caminho> ...]")
        return 2
    print(run(argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
