"""Briefing: monta o briefing de uma sessão do Claude Code (Markdown, até 150 linhas).

Uso: python -m tools.robos.briefing <pedido.md> <notas.md>
"""

from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from pathlib import Path

MAX_LINES = 150
_MAX_FILES = 8
_MAX_NOTES = 15
_RULE_SECTIONS = ("Princípios inegociáveis", "Convenções")
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "data", "privado"}
_FORBIDDEN = (".env", "data/", "privado/")
_STOPWORDS = {
    "para", "com", "uma", "que", "dos", "das", "nos", "nas", "pelo", "pela", "como", "mais",
    "sem", "nem", "ele", "ela", "seu", "sua", "vem", "traz", "pedido", "teste", "aceite",
    "fazer", "recebe", "devolve", "texto", "dois", "arquivos", "uso", "python",
}  # fmt: skip
_REPO_ROOT = Path(__file__).resolve().parents[2]


def keywords(text: str) -> list[str]:
    """Palavras do pedido (minúsculas, sem repetir, sem as comuns), na ordem em que aparecem."""
    seen: dict[str, None] = {}
    for word in re.findall(r"[a-zà-ú_]{4,}", text.lower()):
        if word not in _STOPWORDS:
            seen.setdefault(word)
    return list(seen)


def rules(claude_md: str) -> list[str]:
    """Os princípios e as convenções do CLAUDE.md, sem o resto."""
    out: list[str] = []
    keep = False
    for line in claude_md.splitlines():
        if line.startswith("## "):
            keep = line[3:].strip() in _RULE_SECTIONS
            if keep:
                out.append(line.replace("## ", "### ", 1))
            continue
        if keep and line.strip():
            out.append(line)
    return out


def _allowed(path: str) -> bool:
    return not any(part in path for part in _FORBIDDEN)


def find_files(root: Path, words: Sequence[str]) -> list[str]:
    """Arquivos do repositório cujo caminho tem palavras do pedido, os melhores primeiro."""
    scored: list[tuple[int, str]] = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in _SKIP_DIRS or part.startswith(".env") for part in rel.parts):
            continue
        if not path.is_file():
            continue
        name = rel.as_posix()
        score = sum(1 for word in words if word in name.lower())
        if score and _allowed(name):
            scored.append((score, name))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [name for _, name in scored[:_MAX_FILES]]


def relevant_notes(notes: str, words: Sequence[str]) -> list[str]:
    """Linhas das notas que falam de alguma palavra do pedido (sem segredos)."""
    out = []
    for line in notes.splitlines():
        low = line.lower()
        if line.strip() and _allowed(low) and any(word in low for word in words):
            out.append(line.strip())
    return out[:_MAX_NOTES]


def build(request: str, notes: str, claude_md: str, root: Path) -> str:
    """Monta o briefing. O pedido entra como veio; o resto é cortado para caber."""
    words = keywords(request)
    request_lines = request.strip().splitlines()
    files = find_files(root, words)
    notes_lines = relevant_notes(notes, words)
    rule_lines = rules(claude_md)

    def assemble(rule_part: list[str]) -> list[str]:
        lines = ["# Briefing", "", "## Pedido", "", *request_lines, "", "## Regras do CLAUDE.md", ""]
        lines += rule_part
        lines += ["", "## Arquivos prováveis", ""]
        lines += [f"- `{name}`" for name in files] or ["- (nenhum achado)"]
        lines += ["", "## Notas da memória", ""]
        lines += [f"- {n.lstrip('- ')}" for n in notes_lines] or ["- (nada sobre o assunto)"]
        return lines

    lines = assemble(rule_lines)
    # Se passar do limite, corta as regras (a parte mais longa), nunca o pedido.
    while len(lines) > MAX_LINES and rule_lines:
        rule_lines = rule_lines[:-1]
        lines = assemble(rule_lines)
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("uso: python -m tools.robos.briefing <pedido.md> <notas.md>")
        return 2
    request = Path(argv[0]).read_text(encoding="utf-8")
    notes = Path(argv[1]).read_text(encoding="utf-8")
    claude_md = (_REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    print(build(request, notes, claude_md, _REPO_ROOT), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
