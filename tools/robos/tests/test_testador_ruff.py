from pathlib import Path

from tools.robos.testador import ruff_summary


def test_ruff_flags_long_line(tmp_path: Path) -> None:
    file = tmp_path / "long.py"
    file.write_text(f'X = "{"a" * 110}"\n')
    result = ruff_summary([str(tmp_path)])
    assert result.startswith("ruff: 1 problemas")
    assert "long.py:1 E501" in result


def test_ruff_flags_format(tmp_path: Path) -> None:
    file = tmp_path / "fmt.py"
    file.write_text("X = [\n    1,\n    2\n]\n")
    result = ruff_summary([str(file)])
    assert result.startswith("ruff: 1 problemas")
    assert "fmt.py formato" in result


def test_ruff_passes_clean_file(tmp_path: Path) -> None:
    file = tmp_path / "ok.py"
    file.write_text("X = [1, 2]\n")
    assert ruff_summary([str(file)]) == "ruff: passou"


def test_ruff_never_passes_on_nonzero_exit(tmp_path: Path) -> None:
    file = tmp_path / "broken.py"
    file.write_text("def f(:\n")
    assert ruff_summary([str(file)]) != "ruff: passou"
