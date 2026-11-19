from pathlib import Path

from tools.robos.testador import run


def test_run_counts_all_green_package(tmp_path: Path) -> None:
    (tmp_path / "test_green.py").write_text(
        "def test_a() -> None:\n    assert True\n\n\ndef test_b() -> None:\n    assert True\n"
    )
    lines = run([str(tmp_path)]).splitlines()
    assert lines == ["passaram: 2", "falharam: 0"]


def test_run_counts_failure(tmp_path: Path) -> None:
    (tmp_path / "test_red.py").write_text(
        "def test_a() -> None:\n    assert True\n\n\ndef test_b() -> None:\n    assert 1 == 2\n"
    )
    lines = run([str(tmp_path)]).splitlines()
    assert lines[0] == "passaram: 1"
    assert lines[1] == "falharam: 1"
    assert "test_red.py:6" in lines[2]
