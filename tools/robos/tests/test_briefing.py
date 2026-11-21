from __future__ import annotations

from pathlib import Path

import pytest

from tools.robos import briefing

ACCEPT = "Teste de aceite: o robô aparece na bancada e   devolve o resumo."
REQUEST = f"""Pedido 1: Testador da bancada

O que fazer: ajustar o robô testador para resumir os testes.
{ACCEPT}
"""
NOTES = """- O testador fica em tools/robos.
- O gerente gosta de commits pequenos.
- A chave está no .env do testador.
- Veja data/testador para o testador.
"""
REPO_ROOT = Path(__file__).resolve().parents[3]


def _build() -> str:
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    return briefing.build(REQUEST, NOTES, claude_md, REPO_ROOT)


def test_briefing_is_short_and_keeps_acceptance_verbatim() -> None:
    text = _build()
    assert len(text.splitlines()) <= 150
    assert ACCEPT in text


def test_briefing_cites_an_existing_file() -> None:
    text = _build()
    cited = [
        line[3:-1] for line in text.splitlines() if line.startswith("- `") and line.endswith("`")
    ]
    assert cited
    assert any((REPO_ROOT / name).is_file() for name in cited)
    assert "tools/robos/testador.py" in cited


def test_briefing_has_only_rules_sections() -> None:
    text = _build()
    assert "Módulos só se conhecem por contrato" in text
    assert "**Idioma:**" in text
    assert "Nunca faça" not in text
    assert "## Stack" not in text


def test_briefing_leaves_out_secrets() -> None:
    text = _build()
    notes_part = text.split("## Notas da memória")[1]
    assert "commits pequenos" not in notes_part
    assert "tools/robos" in notes_part
    assert ".env" not in notes_part
    assert "data/" not in notes_part
    files_part = text.split("## Arquivos prováveis")[1].split("## Notas")[0]
    assert "privado/" not in files_part
    assert ".env" not in files_part


def test_briefing_truncates_rules_not_request() -> None:
    long_request = REQUEST + "\n".join(f"linha {i}" for i in range(120))
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    text = briefing.build(long_request, NOTES, claude_md, REPO_ROOT)
    assert len(text.splitlines()) <= 150
    assert ACCEPT in text


def test_briefing_caps_lines_even_without_rules() -> None:
    long_request = REQUEST + "\n".join(f"linha {i}" for i in range(120))
    notes = "\n".join(f"- testador nota {i}" for i in range(15))
    text = briefing.build(long_request, notes, "", REPO_ROOT)
    assert len(text.splitlines()) <= 150
    assert ACCEPT in text


def test_briefing_refuses_request_too_long_alone() -> None:
    huge = REQUEST + "\n".join(f"linha {i}" for i in range(200))
    with pytest.raises(briefing.RequestTooLongError):
        briefing.build(huge, NOTES, "", REPO_ROOT)


def test_forbidden_is_by_path_from_root_not_substring() -> None:
    assert briefing._forbidden_path("data/x.txt")
    assert briefing._forbidden_path("./privado/a")
    assert briefing._forbidden_path(".env.local")
    assert not briefing._forbidden_path("tools/metadata/x.py")
    assert not briefing._forbidden_path("tools/robos/data_utils.py")
    notes = "- tools/metadata/testador.py guarda o testador.\n- veja data/testador."
    kept = briefing.relevant_notes(notes, ["testador"])
    assert kept == ["- tools/metadata/testador.py guarda o testador."]


def test_find_files_prunes_heavy_and_forbidden_dirs(tmp_path: Path) -> None:
    for folder in ("node_modules", ".venv", "data", "src"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "robo.py").write_text("x", encoding="utf-8")
    assert briefing.find_files(tmp_path, ["robo"]) == ["src/robo.py"]


def test_main_refuses_forbidden_inputs(tmp_path: Path) -> None:
    forbidden = REPO_ROOT / "data" / "pedido_x.md"
    assert briefing._read_input(str(forbidden)) is None
    ok = tmp_path / "p.md"
    ok.write_text("oi", encoding="utf-8")
    assert briefing._read_input(str(ok)) == "oi"


def test_main_requires_two_arguments(capsys: object) -> None:
    assert briefing.main([]) == 2
