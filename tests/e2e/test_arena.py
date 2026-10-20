"""A arena em processo (ADR-0061): a corrida do script, sem API, e a composição das pastas."""

from pathlib import Path

import pytest

from campsverso_testkit.arena import SEED, SPECS, Spec, main, run_spec


async def test_a_corrida_do_script_grava_a_pasta(tmp_path: Path) -> None:
    folder = tmp_path / "script"
    result = await run_spec(Spec("script", "script"), 2, folder)
    assert result["spec"] == {
        "name": "script",
        "controller": "script",
        "memory": False,
        "river_bonus": True,
        "seed": SEED,
        "cartridge": "farm_camps",
        "model": "claude-haiku-5-5",
    }
    assert result["totals"]["days"] == 2
    assert (result["calls"], result["gave_up"], result["aborted_day"]) == (0, False, None)
    assert "plantings" in result["totals"]
    assert (result["east"]["first_note"], result["east"]["beliefs"]) == (None, [])
    assert {p.name for p in folder.iterdir()} == {
        "summary.json",
        "metrics.txt",
        "archive.jsonl",
        "progresso.txt",
    }
    assert "script dia 2:" in (folder / "progresso.txt").read_text(encoding="utf-8")


def test_a_arena_so_completa_o_que_falta(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "arena"
    assert main(["--only", "script", "--days", "1", "--out", str(out)]) == 0
    stamp = (out / "script" / "summary.json").stat().st_mtime_ns
    assert main(["--only", "script", "--days", "1", "--out", str(out)]) == 0
    assert (out / "script" / "summary.json").stat().st_mtime_ns == stamp
    assert "script: feita, pulando" in capsys.readouterr().out


def test_as_corridas_da_arena() -> None:
    """ADR-0061, decisões 2 e 3: script, Haiku sem memória, Haiku com memória em quatro seeds e
    Haiku com memória sem a regra, todos no mesmo mundo."""
    assert [s.name for s in SPECS][:3] == ["script", "haiku", "haiku-memoria"]
    assert sum(s.memory for s in SPECS) == 5
    assert [s.name for s in SPECS if not s.river_bonus] == ["haiku-memoria-sem-regra"]
    assert len({s.seed for s in SPECS if s.name.startswith("haiku-memoria")}) == 4
    assert [s.name for s in SPECS if s.seed == SEED] == [
        "script",
        "haiku",
        "haiku-memoria",
        "haiku-memoria-sem-regra",
    ]
