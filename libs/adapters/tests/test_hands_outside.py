"""As mãos de fora pela tabela comum (ADR-0093, decisão 18): cada harness com a classe dele, e o
programa fixado no `.tools/bin` pelo endereço real."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters.hands_antigravity import AntigravityHands
from campsverso_adapters.hands_claude_code import ClaudeCodeHands
from campsverso_adapters.hands_codex import CodexHands
from campsverso_adapters.hands_outside import OUTSIDE_KEYS, outside_hands, pinned_program
from campsverso_ports import HARNESSES, ModelRequest, ModelResponse


class Meter:
    def assert_priced(self, model: str) -> None:
        return None

    async def observed(
        self, request: ModelRequest, response: ModelResponse, *, harness: str
    ) -> float:
        return 0.0


def _build(harness: str, tools: Path, **options: Any) -> Any:
    return outside_hands(
        harness, Meter(), api_key="k", home=tools / "sessoes", tools=tools, **options
    )


def test_cada_mao_de_fora_tem_a_classe_dela(tmp_path: Path) -> None:
    assert set(OUTSIDE_KEYS) == set(HARNESSES) - {"api"}
    assert isinstance(_build("claude_code", tmp_path), ClaudeCodeHands)
    assert isinstance(_build("codex", tmp_path), CodexHands)
    assert isinstance(_build("antigravity", tmp_path), AntigravityHands)
    with pytest.raises(ValueError, match="desconhecidas"):
        _build("cursor", tmp_path)


def test_o_programa_fixado_vai_pelo_endereco_real(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    assert pinned_program("codex", bin_dir) is None  # sem ele, o do PATH
    package = tmp_path / "codex-pacote" / "bin"
    package.mkdir(parents=True)
    (package / "codex").write_text("#!/bin/sh\n", encoding="utf-8")
    (bin_dir / "codex").symlink_to(Path("..") / "codex-pacote" / "bin" / "codex")
    real = str((package / "codex").resolve())
    assert pinned_program("codex", bin_dir) == [real]
    warnings: list[tuple[str, Mapping[str, Any]]] = []

    def warn(event: str, fields: Mapping[str, Any]) -> None:
        warnings.append((event, fields))

    hands = _build("codex", bin_dir, warn=warn)
    assert hands._command == [real]  # pyright: ignore[reportPrivateUsage]
