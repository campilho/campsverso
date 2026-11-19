from tools.robos.testador import summarize


def test_summarize_reports_counts_and_first_failure() -> None:
    output = (
        "..F.F\n"
        "/repo/pkg/tests/test_a.py:12: AssertionError: assert 1 == 2\n"
        "/repo/pkg/tests/test_b.py:30: ValueError: boom\n"
        "2 failed, 3 passed in 0.10s\n"
    )
    lines = summarize(output).splitlines()
    assert lines[0] == "passaram: 3"
    assert lines[1] == "falharam: 2"
    assert lines[2] == "primeira falha: /repo/pkg/tests/test_a.py:12 AssertionError: assert 1 == 2"
    assert len(lines) <= 5


def test_summarize_all_green_has_no_failure_line() -> None:
    lines = summarize("...\n3 passed in 0.01s\n").splitlines()
    assert lines == ["passaram: 3", "falharam: 0"]


def test_summarize_nothing_ran() -> None:
    assert "nenhum teste rodou" in summarize("no tests ran in 0.01s\n")
