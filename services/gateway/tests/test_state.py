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
