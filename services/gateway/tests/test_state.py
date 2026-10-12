"""Merge patch do estado (RFC 7386): aplicar o diff de A para B em A dá B (ADR-0050)."""

from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from campsverso_gateway.state import apply_merge_patch, merge_diff, without_nulls

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
