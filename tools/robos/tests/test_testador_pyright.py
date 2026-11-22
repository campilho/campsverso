import json
from collections.abc import Sequence
from pathlib import Path

from tools.robos.testador import pyright_files, pyright_summary

_ROOT = Path(__file__).resolve().parents[3]
_LIB_FILE = _ROOT / "libs/ports/src/campsverso_ports/hands.py"
_ROBOT_FILE = _ROOT / "tools/robos/testador.py"


def _report(*errors: tuple[Path, int, str]) -> str:
    diagnostics = [
        {
            "file": str(file),
            "severity": "error",
            "rule": rule,
            "range": {"start": {"line": line, "character": 0}},
        }
        for file, line, rule in errors
    ]
    return json.dumps({"generalDiagnostics": diagnostics})


def test_pyright_gives_line_of_type_error() -> None:
    seen: list[Sequence[str]] = []

    def runner(files: Sequence[str]) -> tuple[int, str]:
        seen.append(files)
        return 1, _report((_LIB_FILE, 9, "reportAssignmentType"))

    result = pyright_summary([str(_LIB_FILE)], runner)
    assert result == (
        "pyright: 1 erro(s); primeiro: "
        "libs/ports/src/campsverso_ports/hands.py:10 reportAssignmentType"
    )
    assert seen == [[str(_LIB_FILE)]]


def test_pyright_passes_clean_file() -> None:
    assert pyright_summary([str(_LIB_FILE)], lambda files: (0, _report())) == "pyright: passou"


def test_pyright_skips_files_outside_include() -> None:
    def runner(files: Sequence[str]) -> tuple[int, str]:
        raise AssertionError("não devia rodar")

    assert pyright_files([str(_ROBOT_FILE)]) == []
    assert pyright_summary([str(_ROBOT_FILE)], runner) == "pyright: nenhum arquivo coberto"


def test_pyright_skips_excluded_fixture() -> None:
    fixture = _ROOT / "tests/fixtures/oficina/tools/robos/testador.py"
    assert pyright_files([str(fixture)]) == []


def test_pyright_never_passes_on_garbage_output() -> None:
    result = pyright_summary([str(_LIB_FILE)], lambda files: (1, "boom"))
    assert result.startswith("pyright: não consegui rodar")


def test_pyright_never_passes_on_nonzero_exit() -> None:
    result = pyright_summary([str(_LIB_FILE)], lambda files: (3, _report()))
    assert result != "pyright: passou"
