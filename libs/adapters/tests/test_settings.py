from pathlib import Path

import pytest

from campsverso_adapters import load_env, load_world
from campsverso_adapters.settings import duration_seconds, size_bytes

REPO = Path(__file__).resolve().parents[3]


def test_ambiente_local() -> None:
    env = load_env(REPO / "config" / "env" / "local.yaml", root=REPO)
    assert env.data_dir == REPO / "data"
    assert env.archive_dir == REPO / "data" / "archive"
    assert env.snapshot_every_ticks == 60
    assert env.nats.duplicate_window_seconds == 120
    assert {s.name for s in env.nats.streams} == {
        "WORLD",
        "AGENT",
        "OBSERVER",
        "INTERNAL",
        "COMMANDS",
    }


def test_mundo_da_fazenda() -> None:
    world = load_world(REPO / "config" / "worlds" / "farm-camps-01.yaml", root=REPO)
    assert (world.worldid, world.cartridge, world.seed) == ("farm-camps-01", "farm_camps", 20261010)
    assert world.start.isoformat() == "2026-10-10T06:00:00-03:00"
    assert (world.mode, world.scale, world.paused, world.rules_file) == (
        "continuous",
        72,
        False,
        None,
    )


def test_unidades() -> None:
    assert duration_seconds("30d") == 30 * 86400
    assert size_bytes("256MiB") == 256 * 1024 * 1024
    with pytest.raises(ValueError, match="duração"):
        duration_seconds("30 dias")
