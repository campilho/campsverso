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
    assert (world.player, world.avatar) == ("camps", "camps")  # o script conduz o próprio Camps
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
    for name in ("office-campsverso-02", "office-campsverso-demo"):
        world = load_world(REPO / "config" / "worlds" / f"{name}.yaml", root=REPO)
        budget = world.budget
        assert budget is not None
        # Os tetos do M26 (ADR-0089, decisão 8): US$ 5 por pedido e US$ 10 por dia.
        assert (budget.usd_per_ticket, budget.usd_per_sim_day) == (5.0, 10.0)
        assert budget.on_exceeded == "mind_off"
    # Quem programa sem escolha na prancheta: no escritório vivo, o Claude Code com o Opus 5.5, como
    # recomendou a comparação das mãos (22/nov); na demonstração, o nosso harness.
    live = load_world(REPO / "config" / "worlds" / "office-campsverso-02.yaml", root=REPO)
    assert (live.minds["tiago"].hands, live.minds["tiago"].model) == (
        "claude_code",
        "claude-opus-5-5",
    )
    demo = load_world(REPO / "config" / "worlds" / "office-campsverso-demo.yaml", root=REPO)
    assert demo.minds["tiago"].hands == "api"


def test_as_maos_do_mundo(tmp_path: Path) -> None:
    """ADR-0089: quem programa os pedidos sem escolha; sem a chave, o nosso harness."""
    base = (
        "worldid: lab-01\ncartridge: lab\nseed: 1\nstart: 2026-11-16T00:00:00-03:00\n"
        "minds:\n  camps: {mind: camps, model: claude-opus-5-5"
    )
    world = tmp_path / "mundo.yaml"
    world.write_text(base + "}\n", encoding="utf-8")
    assert load_world(world).minds["camps"].hands == "api"
    world.write_text(base + ", hands: claude_code}\n", encoding="utf-8")
    assert load_world(world).minds["camps"].hands == "claude_code"
    assert load_world(world).minds["camps"].hands_model is None  # o modelo da mente
    # A mente e o sistema são independentes (ADR-0093, decisão 18).
    world.write_text(base + ", hands: codex, hands_model: gpt-6.2-astra}\n", encoding="utf-8")
    camps = load_world(world).minds["camps"]
    assert (camps.model, camps.hands, camps.hands_model) == (
        "claude-opus-5-5",
        "codex",
        "gpt-6.2-astra",
    )
    world.write_text(base + ", hands: cursor}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hands inválido"):
        load_world(world)


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


def test_o_codehost_do_escritorio_vivo_e_o_prefixo_dos_ramos(tmp_path: Path) -> None:
    """ADR-0083: o revisor em ordem (o plano A primeiro) e os ramos do dev sob `dev/`; no mundo 02,
    os do Tiago sob `dev/tiago/`, para não colidir com os do mundo 01 (ADR-0092)."""
    live = load_world(REPO / "config" / "worlds" / "office-campsverso-02.yaml", root=REPO).codehost
    assert live is not None
    assert live.reviewers == ("openai/gpt-6.2-astra", "google/gemini-4-neon")
    assert live.branch_prefix == "dev/tiago/"
    base = "worldid: lab-01\ncartridge: lab\nseed: 1\nstart: 2026-11-16T00:00:00-03:00\n"
    world = tmp_path / "mundo.yaml"
    host = "codehost: {host: memory, repo: a/b, branch_prefix: %s}\n"
    world.write_text(base + host % "dev/sandbox-1/", encoding="utf-8")
    codehost = load_world(world).codehost
    assert codehost is not None
    assert codehost.branch_prefix == "dev/sandbox-1/"
    world.write_text(base + host % "main/", encoding="utf-8")
    with pytest.raises(ValueError, match="branch_prefix inválido"):
        load_world(world)


def test_o_dev_do_escritorio_e_o_tiago() -> None:
    """ADR-0092: nos mundos do escritório, o script e a mente conduzem o Tiago, e o humano entra
    como o gerente, o Camps; o mundo vivo é o 02."""
    for name in ("office-campsverso-02", "office-campsverso-demo", "office-campsverso-teste"):
        world = load_world(REPO / "config" / "worlds" / f"{name}.yaml", root=REPO)
        assert (world.player, world.avatar) == ("gerente", "tiago"), name
    live = load_world(REPO / "config" / "worlds" / "office-campsverso-02.yaml", root=REPO)
    assert live.worldid == "office-campsverso-02"
    assert (live.minds["tiago"].id, live.minds["tiago"].mind) == ("llm/tiago", "tiago_escritorio")
    assert not (REPO / "config" / "worlds" / "office-campsverso-01.yaml").exists()
