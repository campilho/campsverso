"""Briefing: monta o briefing de uma sessão do Claude Code (Markdown, até 150 linhas).

Uso: python -m tools.robos.briefing <pedido.md> <notas.md>
"""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path

MAX_LINES = 150
_MAX_FILES = 8
_MAX_NOTES = 15
_RULE_SECTIONS = ("Princípios inegociáveis", "Convenções")
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
_FORBIDDEN_DIRS = {"data", "privado"}
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


class RequestTooLongError(ValueError):
    """O pedido sozinho não cabe no teto de linhas do briefing."""


def _forbidden_path(path: str) -> bool:
    """Diz se um caminho a partir da raiz cai em .env, data/ ou privado/."""
    parts = [p for p in path.strip().replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts:
        return False
    first = parts[0]
    return first.startswith(".env") or first in _FORBIDDEN_DIRS


def _allowed(path: str) -> bool:
    return not _forbidden_path(path)


def _line_allowed(line: str) -> bool:
    """Uma linha de nota é barrada se citar um caminho proibido (palavra a palavra)."""
    for token in line.split():
        if _forbidden_path(token.strip("`'\"()[],;:.")):
            return False
        if _forbidden_path(token.strip("`'\"()[],;")):
            return False
    return True


def find_files(root: Path, words: Sequence[str]) -> list[str]:
    """Arquivos do repositório cujo caminho tem palavras do pedido, os melhores primeiro."""
    scored: list[tuple[int, str]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Poda antes de descer: nem entra em node_modules, .venv, data/ etc.
        here = Path(dirpath).relative_to(root)
        dirnames[:] = [
            d for d in dirnames if d not in _SKIP_DIRS and _allowed((here / d).as_posix())
        ]
        for filename in filenames:
            name = (here / filename).as_posix()
            if not _allowed(name):
                continue
            score = sum(1 for word in words if word in name.lower())
            if score:
                scored.append((score, name))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [name for _, name in scored[:_MAX_FILES]]


def relevant_notes(notes: str, words: Sequence[str]) -> list[str]:
    """Linhas das notas que falam de alguma palavra do pedido (sem segredos)."""
    out = []
    for line in notes.splitlines():
        low = line.lower()
        if line.strip() and _line_allowed(line) and any(word in low for word in words):
            out.append(line.strip())
    return out[:_MAX_NOTES]


def build(request: str, notes: str, claude_md: str, root: Path) -> str:
    """Monta o briefing. O pedido entra como veio; o resto é cortado para caber."""
    words = keywords(request)
    request_lines = request.strip().splitlines()
    files = find_files(root, words)
    notes_lines = relevant_notes(notes, words)
    rule_lines = rules(claude_md)

    def assemble(rule_part: list[str], file_part: list[str], note_part: list[str]) -> list[str]:
        lines = ["# Briefing", "", "## Pedido", "", *request_lines]
        lines += ["", "## Regras do CLAUDE.md", ""]
        lines += rule_part
        lines += ["", "## Arquivos prováveis", ""]
        lines += [f"- `{name}`" for name in file_part] or ["- (nenhum achado)"]
        lines += ["", "## Notas da memória", ""]
        lines += [f"- {n.lstrip('- ')}" for n in note_part] or ["- (nada sobre o assunto)"]
        return lines

    if len(assemble([], [], [])) > MAX_LINES:
        raise RequestTooLongError(
            f"o pedido sozinho não cabe em {MAX_LINES} linhas; encurte o pedido"
        )
    # Se passar do limite, corta regras, depois notas, depois arquivos; nunca o pedido.
    lines = assemble(rule_lines, files, notes_lines)
    while len(lines) > MAX_LINES:
        if rule_lines:
            rule_lines = rule_lines[:-1]
        elif notes_lines:
            notes_lines = notes_lines[:-1]
        else:
            files = files[:-1]
        lines = assemble(rule_lines, files, notes_lines)
    return "\n".join(lines) + "\n"


def _read_input(arg: str) -> str | None:
    """Lê pedido ou notas; recusa o que estiver em .env, data/ ou privado/ do repositório."""
    path = Path(arg).resolve()
    try:
        rel = path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        rel = ""
    if rel and _forbidden_path(rel):
        return None
    return path.read_text(encoding="utf-8")


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print("uso: python -m tools.robos.briefing <pedido.md> <notas.md>")
        return 2
    request = _read_input(argv[0])
    notes = _read_input(argv[1])
    if request is None or notes is None:
        print("recusado: não leio arquivos de .env, data/ nem privado/")
        return 2
    claude_md = (_REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    try:
        text = build(request, notes, claude_md, _REPO_ROOT)
    except RequestTooLongError as error:
        print(f"erro: {error}")
        return 1
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
