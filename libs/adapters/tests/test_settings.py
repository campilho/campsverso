from pathlib import Path

import pytest

from campsverso_adapters import load_env, load_world
from campsverso_adapters.settings import duration_seconds, size_bytes

REPO = Path(__file__).resolve().parents[3]


def test_ambiente_local() -> None:
    env = load_env(REPO / "config" / "env" / "local.yaml", root=REPO)
    assert env.data_dir == REPO / "data"
    assert env.archive_dir == REPO / "data" / "archive"
    assert env.snapshot_every_minutes == 60
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
    assert world.budget is not None
    assert (world.budget.usd_per_sim_day, world.budget.usd_total) == (0.6, 10.0)
    camps = world.minds["camps"]  # ADR-0059
    assert (camps.id, camps.mind, camps.model, camps.effort, camps.max_tokens) == (
        "llm/camps",
        "camps",
        "claude-haiku-5-5",
        "low",
        1024,
    )
    assert camps.cassette_path == REPO / "data" / "llm" / "farm-camps-01.jsonl"
    assert camps.cassette_mode == "record"


def test_as_variantes_do_mapa_da_morada_do_sol() -> None:
    worlds = REPO / "config" / "worlds"
    base = load_world(worlds / "farm-morada-do-sol-01.yaml", root=REPO)
    assert base.map is None  # o mapa do cartucho
    for number, variant in (("02", "b"), ("03", "c"), ("04", "d")):  # ADR-0070; ADR-0074
        world = load_world(worlds / f"farm-morada-do-sol-{number}.yaml", root=REPO)
        assert (world.cartridge, world.map, world.seed) == (base.cartridge, variant, base.seed)
        assert world.worldid == f"farm-morada-do-sol-{number}"
        assert world.helpers == base.helpers  # os mesmos ajudantes nos três mapas (ADR-0072)
    assert (base.helper_script, base.helpers) == (
        "ajudante",
        ("dita", "nina", "seu-bento", "tiao", "ze-graudo"),
    )
    assert load_world(worlds / "farm-camps-01.yaml", root=REPO).helpers == ()


def test_unidades() -> None:
    assert duration_seconds("30d") == 30 * 86400
    assert size_bytes("256MiB") == 256 * 1024 * 1024
    with pytest.raises(ValueError, match="duração"):
        duration_seconds("30 dias")


def test_o_relogio_ancorado_no_real(tmp_path: Path) -> None:
    """ADR-0078: `clock.anchor: wall` só no modo contínuo; sem ele, o relógio é o de sempre."""
    base = "worldid: lab-01\ncartridge: lab\nseed: 1\nstart: 2026-11-16T00:00:00-03:00\n"
    world = tmp_path / "mundo.yaml"
    world.write_text(base + "clock: {mode: continuous, scale: 1, anchor: wall}\n", encoding="utf-8")
    assert load_world(world).anchor == "wall"
    world.write_text(base, encoding="utf-8")
    assert load_world(world).anchor is None
    world.write_text(base + "clock: {mode: max, anchor: wall}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="modo contínuo"):
        load_world(world)
    world.write_text(base + "clock: {anchor: lua}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="anchor inválido"):
        load_world(world)


def test_o_orcamento_do_escritorio() -> None:
    """ADR-0080: o escritório tem teto por pedido e, no teto do dia ou do total, desliga a mente em
    vez de pausar o mundo. Sem orçamento, a guarda não sobe, e o `make escritorio` caía junto."""
    for name in ("office-campsverso-01", "office-campsverso-demo"):
        budget = load_world(REPO / "config" / "worlds" / f"{name}.yaml", root=REPO).budget
        assert budget is not None
        assert (budget.usd_per_ticket, budget.on_exceeded) == (1.0, "mind_off")


def test_o_que_fazer_no_teto(tmp_path: Path) -> None:
    base = "worldid: lab-01\ncartridge: lab\nseed: 1\nstart: 2026-11-16T00:00:00-03:00\n"
    world = tmp_path / "mundo.yaml"
    world.write_text(base + "budget: {usd_per_sim_day: 1, usd_total: 5}\n", encoding="utf-8")
    budget = load_world(world).budget
    assert budget is not None
    assert (budget.on_exceeded, budget.usd_per_ticket) == ("pause", None)  # o padrão das fazendas
    world.write_text(base + "budget: {usd_per_sim_day: 1, usd_total: 5, on_exceeded: dormir}\n")
    with pytest.raises(ValueError, match="on_exceeded inválido"):
        load_world(world)
