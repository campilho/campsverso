"""A partida de um humano no sandbox vira uma corrida da arena (ADR-0066)."""

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from campsverso_tools.arena import load_runs
from campsverso_tools.arena import main as report
from campsverso_tools.arena_humano import import_sandbox, main


def ev(tick: int, kind: str, time: str, /, **data: Any) -> dict[str, Any]:
    return {
        "source": "/kernel/w",
        "seq": tick,
        "tick": tick,
        "type": f"campsverso.{kind}",
        "time": time,
        "data": data,
    }


HUMAN = {"type": "human", "id": "human/camps-browser"}
SCRIPT = {"type": "script", "id": "script/farmer2-v1"}


def _sandbox(root: Path) -> Path:
    sandbox = root / "sandbox"
    world = {
        "worldid": "farm-boavista-01",
        "cartridge": "farm_boavista",
        "seed": 7,
        "rules_file": None,
    }
    days = sandbox / "archive" / "farm-boavista-01"
    days.mkdir(parents=True)
    (sandbox / "world.yaml").write_text(yaml.safe_dump(world), encoding="utf-8")
    first = [
        ev(0, "world.session.started.v1", "2026-10-22T22:00:00Z", tick_seconds=60),
        ev(
            0,
            "world.item.created.v1",
            "2026-10-22T22:00:00Z",
            item="moeda",
            qty=100,
            container_id="camps",
        ),
        ev(
            3,
            "avatar.possessed.v1",
            "2026-10-22T22:00:05Z",
            avatar_id="camps",
            previous_controller=SCRIPT,
            controller=HUMAN,
            by="human/operador",
        ),
        ev(1440, "world.clock.phase_changed.v1", "2026-10-22T22:20:00Z"),
    ]
    second = [
        ev(
            1500,
            "world.item.created.v1",
            "2026-10-22T22:21:00Z",
            item="moeda",
            qty=30,
            container_id="camps",
        ),
        ev(2880, "world.clock.phase_changed.v1", "2026-10-22T22:40:00Z"),
    ]
    for name, envelopes in (("2026-10-10.jsonl", first), ("2026-10-11.jsonl", second)):
        (days / name).write_text("".join(json.dumps(e) + "\n" for e in envelopes), "utf-8")
    return sandbox


def test_a_partida_entra_na_rodada_ao_lado_das_corridas(tmp_path: Path) -> None:
    arena = tmp_path / "20261020-233814"
    out = import_sandbox(_sandbox(tmp_path), arena)
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["spec"]["controller"] == "human"
    assert summary["spec"]["seed"] == 7
    assert summary["spec"]["river_bonus"] is True
    assert summary["human_from_tick"] == 3  # antes disso, jogou o script
    assert summary["real_seconds"] == 40 * 60  # do primeiro ao último evento, com as pausas
    assert len((out / "archive.jsonl").read_text(encoding="utf-8").splitlines()) == 6
    assert [r.name for r in load_runs(arena)] == ["humano"]
    md = tmp_path / "relatorio.md"
    assert report([str(arena), "--out", str(md)]) == 0
    text = md.read_text(encoding="utf-8")
    assert "| Métrica | humano |" in text
    assert "| humano | humano |" in text  # a linha da corrida diz quem controlou


def test_a_partida_de_outra_noite_nao_se_apaga(tmp_path: Path) -> None:
    sandbox, arena = _sandbox(tmp_path), tmp_path / "rodada"
    import_sandbox(sandbox, arena)
    with pytest.raises(FileExistsError):
        import_sandbox(sandbox, arena)
    assert main([str(sandbox), "--arena", str(arena)]) == 2
    assert main([str(sandbox), "--arena", str(arena), "--name", "humano-2"]) == 0
    assert (arena / "humano-2" / "summary.json").exists()
