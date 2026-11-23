"""O cercado das mãos de fora (ADR-0089, decisão 6; ADR-0093, decisão 5): o perfil do `sandbox-exec`
e o programa do harness lançado sem depender do `PATH` do espaço.

O macOS não deixa um sandbox dentro do outro: o do harness fica desligado, e o nosso é a cerca. O
perfil é o mesmo para o Claude Code, o Codex e o Antigravity:
- escrita só no espaço;
- leitura negada na casa do usuário, menos o espaço e o que o harness e o Python do espaço precisam
  ler;
- rede só para a porta das mãos, em `127.0.0.1`.
"""

import os
import shutil
from collections.abc import Sequence
from pathlib import Path

SANDBOX_EXEC = "/usr/bin/sandbox-exec"
# Quanto ler do começo de um programa para achar o `#!`.
SHEBANG_BYTES = 512


def sandbox_profile(space: Path, port_hint: str, home: Path, readable: Sequence[Path]) -> str:
    """O perfil do `sandbox-exec`: rede só para a porta das mãos, escrita só no espaço, e o conteúdo
    da casa do usuário fechado, menos o que o harness e o Python do espaço precisam ler.

    O nome dos arquivos continua visível (o `stat`); o conteúdo e a listagem, não."""
    allowed = " ".join(f'(subpath "{p}")' for p in (space, *readable))
    return (
        "(version 1)\n"
        "(allow default)\n"
        "(deny network*)\n"
        f'(allow network-outbound (remote ip "localhost:{port_hint}"))\n'
        "(allow network-outbound (remote unix-socket))\n"
        "(deny file-write*)\n"
        f'(allow file-write* (subpath "{space}") (literal "/dev/null") (literal "/dev/tty")'
        ' (subpath "/dev/fd") (regex #"^/dev/ttys"))\n'
        f'(deny file-read-data (subpath "{home}") (subpath "/private/tmp") (subpath "/tmp"))\n'
        f"(allow file-read-data {allowed})\n"
    )


def _inside(space: Path, found: str) -> bool:
    real = Path(found).resolve()
    root = space.resolve()
    return real == root or root in real.parents


def _which(program: str, space: Path, what: str) -> str:
    """Um programa pelo `PATH` de quem chama, nunca pelo do espaço; recusa o que mora no espaço."""
    found = shutil.which(program, path=os.environ.get("PATH", os.defpath))
    if found is None:
        raise FileNotFoundError(f"{what} não foi achado: {program}")
    if _inside(space, found):
        raise ValueError(f"{what} não pode vir do espaço do pedido: {found}")
    return str(Path(found).absolute())


def interpreter_of(program: Path, space: Path) -> list[str]:
    """O interpretador de um programa que começa com `#!/usr/bin/env`, como o lançador do Codex pelo
    npm (`#!/usr/bin/env node`), achado pelo `PATH` de quem chama.

    O processo do harness tem o `.venv/bin` do espaço à frente no `PATH`, para os comandos do dev;
    sem isto, o `env` acharia ali um `node` escrito no espaço. Um `#!` com o caminho absoluto, ou um
    binário, não procura nada: fica como está (a lista vazia)."""
    with program.open("rb") as handle:
        head = handle.read(SHEBANG_BYTES)
    if not head.startswith(b"#!"):
        return []
    words = head[2:].split(b"\n", 1)[0].decode("utf-8", errors="replace").split()
    if not words or Path(words[0]).name != "env":
        return []
    rest = words[1:]
    if rest and rest[0] == "-S":
        rest = rest[1:]
    if not rest or rest[0].startswith("-"):
        raise ValueError(f"o lançador de {program} pede ao env o que a oficina não sabe ler")
    name, *arguments = rest
    return [_which(name, space, "o interpretador do harness"), *arguments]


def resolve_program(command: Sequence[str], space: Path, what: str) -> list[str]:
    """O comando de um harness pronto para lançar: o programa pelo caminho absoluto, achado no
    `PATH` de quem chama, e o interpretador à frente quando o programa é um script do `env`.
    Recusa um programa ou um interpretador que não existe ou que mora no espaço."""
    if not command:
        raise ValueError(f"o comando de {what} está vazio")
    program, *rest = command
    found = _which(program, space, what)
    return [*interpreter_of(Path(found), space), found, *rest]


def readable_for(command: Sequence[str], home: Path) -> list[Path]:
    """O que o harness lê fora do espaço para rodar: a pasta de cada arquivo do comando (o
    interpretador, o programa), pelo caminho real. Numa pasta `bin`, a instalação inteira, um nível
    acima, onde ficam as bibliotecas (o Node, o Python, o pacote do npm); menos quando ela é a casa
    do usuário ou uma pasta direta dela, como a `~/.local`, que guarda de tudo."""
    home = home.resolve()
    found: list[Path] = []
    for given in command:
        path = Path(given)
        if not path.is_absolute() or not path.is_file():
            continue
        real = path.resolve()
        folder = real.parent
        install = folder.parent
        if folder.name == "bin" and home not in (install, install.parent):
            folder = install
        if folder not in found:
            found.append(folder)
    return found


def workspace_python(root: Path) -> list[Path]:
    """A instalação do Python do ambiente do espaço, que mora fora dele: o `uv` a guarda na
    casa do usuário."""
    python = root / ".venv" / "bin" / "python"
    return [python.resolve().parents[1]] if python.exists() else []
