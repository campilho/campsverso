"""A revisão da entrega da oficina (o plano do M24, §3.6; ADR-0080, decisão 12): o que recusa um
patch antes de ele chegar ao gerente, de novo no `make aplicar` e no publicador do GitHub, e uma
terceira vez no CI de cada PR do dev (ADR-0083).

Função pura do texto do diff e da lista de palavras: sem git, sem disco, e só da biblioteca padrão.
No CI, o arquivo roda sozinho, tirado do `main` e não do PR, para que o dev não mude a regra no
mesmo PR que ela confere: `git diff origin/main...HEAD | python workshop_review.py`.
"""

import re
import sys
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
    # O caminho até o GitHub (ADR-0083): o publicador, o App e esta regra.
    "services/codehost/",
    "libs/adapters/src/campsverso_adapters/codehost_",
    "libs/adapters/src/campsverso_adapters/workshop_review.py",
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
# Uma chave ou um segredo numa linha nova (ADR-0089, decisão 6): a das APIs de modelo, a do GitHub,
# a do Slack e uma chave privada. A chave da sessão de um harness (`sessao-…`) não vale fora dela.
_SECRET = re.compile(
    r"(sk-ant-|sk-or-v1-|sk-proj-|ghp_|github_pat_|xox[abp]-)[A-Za-z0-9_\-]{16,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
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
        if any(_SECRET.search(line) for line in f.added):
            reasons.append(f"{f.path}: parece trazer uma chave ou um segredo")
        haystack = "\n".join([f.path, *f.added]).lower()
        if any(word in haystack for word in words):
            reasons.append(f"{f.path}: tem uma palavra da lista proibida")
    return list(dict.fromkeys(reasons))


def main() -> int:
    """O passo do CI nos PRs do dev: o diff na entrada, os motivos na saída, e 1 se houver algum."""
    reasons = review(sys.stdin.read())
    for reason in reasons:
        print(f"::error title=constituição::{reason}")
    print("a constituição está inteira" if not reasons else f"{len(reasons)} motivo(s)")
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())
