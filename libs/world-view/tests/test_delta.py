"""O delta da percepção aplicado sobre a foto (ADR-0080)."""

from typing import Any

from campsverso_world_view import apply_delta, diff_views


def test_aplicar_o_delta_refaz_a_foto() -> None:
    """ADR-0080: a rotina do dev, conduzida pela mente, recebe deltas e precisa da foto inteira."""
    me = {"entity_id": "camps", "position": {"x": 4, "y": 5}}
    before: dict[str, Any] = {
        "clock": {"tick": 1},
        "self": me,
        "weather": {"condition": "sol"},
        "entities": [
            {"entity_id": "quadro", "kind": "board"},
            {"entity_id": "pedido-001", "kind": "ticket", "attributes": {"estado": "a_fazer"}},
            {"entity_id": "gerente", "kind": "avatar"},
        ],
        "containers": [{"container_id": "quadro", "items": [{"item": "x"}]}],
        "map": {"rows": ["..."]},
    }
    after: dict[str, Any] = {
        **before,
        "clock": {"tick": 9},
        "self": {**me, "position": {"x": 4, "y": 6}},
        "entities": [
            {"entity_id": "quadro", "kind": "board"},
            {"entity_id": "pedido-001", "kind": "ticket", "attributes": {"estado": "fazendo"}},
            {"entity_id": "pedido-002", "kind": "ticket", "attributes": {"estado": "a_fazer"}},
        ],
        "containers": [],
    }
    delta = {
        **diff_views(before, after),
        "clock": after["clock"],
        "self": after["self"],
        "events": [
            {
                "type": "campsverso.avatar.spoke.v1",
                "tick": 8,
                "data": {"avatar_id": "gerente", "text": "Oi!", "listener_id": "camps"},
            },
            {
                "type": "campsverso.avatar.spoke.v1",
                "tick": 9,
                "data": {"avatar_id": "camps", "text": "Oi."},
            },
        ],
    }
    rebuilt = apply_delta(before, delta)
    assert rebuilt["entities"] == after["entities"]
    assert rebuilt["containers"] == []
    assert rebuilt["self"] == after["self"]
    assert rebuilt["heard"] == [
        {"tick": 8, "avatar_id": "gerente", "text": "Oi!", "listener_id": "camps"}
    ]
    assert "heard" not in apply_delta(rebuilt, {"clock": {"tick": 10}, "self": after["self"]})
