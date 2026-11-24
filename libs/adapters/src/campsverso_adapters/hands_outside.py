"""As mãos de fora que a plataforma conhece (ADR-0089; ADR-0093): o Claude Code, o Codex e o
Antigravity, cada um com a chave do laboratório dele e, os dois de fora do SDK, com o programa
fixado no `.tools/bin` pelo `make tools-maos`. A raiz de composição do escritório e a prova de
conformidade montam as mãos por aqui, e assim qualquer dev usa qualquer sistema (a ADR-0093,
decisão 18): a mão não sabe de dev nenhum.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from campsverso_adapters.hands_antigravity import AntigravityHands
from campsverso_adapters.hands_claude_code import ClaudeCodeHands
from campsverso_adapters.hands_codex import CodexHands
from campsverso_ports import CallMeter, Hands

# A chave de cada mão, a do laboratório dela, que só a porta das mãos vê.
OUTSIDE_KEYS: Mapping[str, str] = {
    "claude_code": "ANTHROPIC_API_KEY",
    "codex": "OPENAI_API_KEY",
    "antigravity": "GEMINI_API_KEY",
}
# O programa de cada mão que roda como processo.
PROGRAMS: Mapping[str, str] = {"codex": "codex", "antigravity": "agy"}


def pinned_program(program: str, tools: Path) -> list[str] | None:
    """O programa que o `make tools-maos` instalou com a versão fixa; sem ele, None (o do `PATH`).

    O `.tools/bin` só tem atalhos: o programa vai pelo endereço real, onde ele acha o que veio no
    pacote ao lado dele (o `codex-code-mode-host` do Codex, no ensaio de 23/nov)."""
    path = tools / program
    return [str(path.resolve())] if path.exists() else None


def outside_hands(
    harness: str,
    meter: CallMeter,
    *,
    api_key: str,
    home: Path,
    tools: Path,
    **options: Any,
) -> Hands:
    """As mãos de um harness de fora, com a chave, a pasta das sessões e, nas que rodam como
    processo, o programa fixado em `tools`. As `options` (a fita, o aviso) vão a todas."""
    common: dict[str, Any] = {"api_key": api_key, "home": home, **options}
    if harness == "claude_code":
        return ClaudeCodeHands(meter, **common)
    if harness not in PROGRAMS:
        raise ValueError(f"mãos de fora desconhecidas: {harness!r} (use {list(OUTSIDE_KEYS)})")
    command = pinned_program(PROGRAMS[harness], tools)
    if harness == "codex":
        return CodexHands(meter, command=command, **common)
    return AntigravityHands(meter, command=command, **common)
