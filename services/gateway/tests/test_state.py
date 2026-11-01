"""Merge patch do estado (RFC 7386): aplicar o diff de A para B em A dá B (ADR-0050)."""

from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from campsverso_gateway.state import (
    apply_merge_patch,
    merge_diff,
    observer_state,
    player_state,
    without_nulls,
)
from campsverso_world_view import Projection

keys = st.sampled_from(["a", "b", "c", "camps", "plot-e-01"])
scalars = st.one_of(st.integers(-5, 5), st.booleans(), st.text(max_size=3))
json_values = st.recursive(
    scalars,
    lambda inner: st.one_of(st.lists(inner, max_size=3), st.dictionaries(keys, inner, max_size=4)),
    max_leaves=12,
)
states = st.dictionaries(keys, json_values, max_size=5)


@given(states, states)
def test_aplicar_o_diff_leva_ao_novo_estado(old: dict[str, Any], new: dict[str, Any]) -> None:
    assert apply_merge_patch(old, merge_diff(old, new)) == new


@given(states)
def test_sem_mudanca_nao_ha_patch(state: dict[str, Any]) -> None:
    assert merge_diff(state, state) == {}


def test_nulos_somem_do_estado() -> None:
    raw = {"crop": None, "stage": "semente", "nested": {"x": None, "y": [1, None]}}
    assert without_nulls(raw) == {"stage": "semente", "nested": {"y": [1, None]}}
    patch = merge_diff({"motion": {"camps": {"path": [1]}}}, {"motion": {}})
    assert patch == {"motion": {"camps": None}}


def test_o_custo_e_do_operador() -> None:
    """ADR-0074: o custo das mentes vai para a visão do operador; a do jogador não o vê."""
    p = Projection()
    p.apply(
        "world",
        {
            "type": "campsverso.world.session.started.v1",
            "seq": 0,
            "tick": 0,
            "simtime": "t0",
            "data": {
                "cartridge_version": "0.1.0",
                "seed": 7,
                "tick_seconds": 60,
                "mode": "continuous",
                "paused": False,
                "scale": 72,
            },
        },
    )
    p.apply(
        "observer",
        {
            "type": "campsverso.llm.call.completed.v1",
            "seq": 1,
            "tick": 10,
            "simtime": "t10",
            "data": {
                "controller": {"type": "llm", "id": "llm/camps"},
                "model": "claude-haiku-5-5",
                "cost_usd": 0.0004,
                "charged": True,
            },
        },
    )
    assert observer_state(p)["costs"]["minds"]["llm/camps"]["total_usd"] == 0.0004
    assert "costs" not in player_state(p, "camps")


def _event(stream: str, seq: int, tick: int, kind: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": f"campsverso.{kind}.v1",
        "seq": seq,
        "tick": tick,
        "simtime": f"t{tick}",
        "data": data,
    }


def test_a_vista_do_jogador_anda_com_o_pulso() -> None:
    """Numa caminhada não sai evento até a chegada: a vista segue o tick do pulso, e o canteiro do
    caminho aparece enquanto o Camps passa por ele (achado do usuário no mapa d)."""
    p = Projection()
    session = {
        "cartridge_version": "0.1.0",
        "seed": 7,
        "tick_seconds": 60,
        "mode": "continuous",
        "paused": False,
        "scale": 72,
        "perception": {"radius": 2},
    }
    p.apply("world", _event("world", 0, 0, "world.session.started", session))
    for seq, (entity, kind, x) in enumerate([("camps", "avatar", 0), ("plot-01", "plot", 10)], 1):
        spawned = {"entity_id": entity, "kind": kind, "position": {"x": x, "y": 0}}
        p.apply("world", _event("world", seq, 0, "world.entity.spawned", spawned))
    moved = {
        "entity_id": "camps",
        "origin": {"x": 0, "y": 0},
        "waypoints": [{"x": 20, "y": 0}],
        "depart_tick": 1,
        "tiles_per_tick": 1.0,
    }
    p.apply("world", _event("world", 3, 1, "world.entity.moved", moved))
    # Sem pulso, a vista é a de onde a caminhada começou.
    assert "plot-01" not in player_state(p, "camps")["entities"]
    walking = player_state(p, "camps", {"tick": 11, "sim_time": "t11", "alive": True})
    assert "plot-01" in walking["entities"]  # no tick 11, o Camps está no tile 10
    stale = player_state(p, "camps", {"tick": 0, "sim_time": "t0", "alive": True})
    assert "plot-01" not in stale["entities"]  # um pulso atrasado não volta a vista para trás
