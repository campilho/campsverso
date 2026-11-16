"""A revisão da entrega da oficina (o plano do M24, §3.6; ADR-0080, decisão 12): o que recusa um
patch antes de ele chegar ao gerente, e de novo no `make aplicar`.

Função pura do texto do diff e da lista de palavras: sem git, sem disco.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

# A constituição: o que o dev nunca muda. Os caminhos são prefixos, a partir da raiz do repositório.
CONSTITUTION = (
    "CLAUDE.md",
    "contracts/",
    ".github/",
    "Makefile",
    "services/budget/",
    "config/",
    "data/archive/",
)
# As ADRs aceitas não mudam; uma ADR nova pode entrar.
ADRS = "docs/decisoes/"
# O que desliga uma verificação, numa linha nova.
DISABLES = (
    "pytest.mark.skip",
    "pytest.skip(",
    "pytest.mark.xfail",
    "noqa",
    "type: ignore",
    "pyright: ignore",
    "eslint-disable",
    "@ts-ignore",
    "@ts-expect-error",
)
_TEST_DEF = re.compile(r"^\s*(async\s+)?def\s+test_\w*|^\s*(it|test)\(")


@dataclass
class _File:
    path: str
    old_path: str | None = None
    created: bool = False
    deleted: bool = False
    added: list[str] = field(default_factory=list[str])
    removed: list[str] = field(default_factory=list[str])


def _files(diff: str) -> list[_File]:
    files: list[_File] = []
    current: _File | None = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" ")
            old = parts[2][2:] if len(parts) > 2 else ""
            new = parts[3][2:] if len(parts) > 3 else old
            current = _File(new, old)
            files.append(current)
        elif current is None:
            continue
        elif line.startswith("new file mode"):
            current.created = True
        elif line.startswith("deleted file mode"):
            current.deleted = True
        elif line.startswith("+++ ") or line.startswith("--- "):
            continue
        elif line.startswith("+"):
            current.added.append(line[1:])
        elif line.startswith("-"):
            current.removed.append(line[1:])
    return files


def _is_test(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or ".test." in name
        or ".spec." in name
        or "/tests/" in f"/{path}"
    )


def review(diff: str, forbidden: Sequence[str] = ()) -> list[str]:
    """Os motivos para recusar o patch, em português; vazio quando ele pode ir ao gerente."""
    reasons: list[str] = []
    words = [w.strip().lower() for w in forbidden if w.strip()]
    for f in _files(diff):
        for path in {f.path, f.old_path or f.path}:
            if any(path == c or path.startswith(c) for c in CONSTITUTION):
                reasons.append(f"{path}: a constituição não muda pela oficina")
            if path.startswith(ADRS) and not f.created:
                reasons.append(f"{path}: uma ADR aceita não muda")
        if f.deleted and _is_test(f.path):
            reasons.append(f"{f.path}: um teste apagado")
        elif _is_test(f.path):
            gone = sum(1 for line in f.removed if _TEST_DEF.match(line))
            new = sum(1 for line in f.added if _TEST_DEF.match(line))
            if gone > new:
                reasons.append(f"{f.path}: {gone - new} teste(s) a menos")
        for line in f.added:
            hit = next((d for d in DISABLES if d in line), None)
            if hit is not None:
                reasons.append(f"{f.path}: desliga uma verificação ({hit})")
                break
        haystack = "\n".join([f.path, *f.added]).lower()
        if any(word in haystack for word in words):
            reasons.append(f"{f.path}: tem uma palavra da lista proibida")
    return list(dict.fromkeys(reasons))
