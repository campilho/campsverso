from typing import Any

import pytest

from campsverso_tools.contracts.compat import compare

BASE: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["day"],
    "properties": {
        "day": {"type": "integer", "minimum": 1},
        "phase": {"type": "string", "maxLength": 64},
        "reason": {"enum": ["debug", "budget"]},
    },
}


def _with(**changes: Any) -> dict[str, Any]:
    schema: dict[str, Any] = {**BASE, "properties": {**BASE["properties"]}}
    for key, value in changes.items():
        if key == "required":
            schema["required"] = value
        else:
            schema["properties"][key] = value
    return schema


def _codes(new: dict[str, Any]) -> set[str]:
    return {p.code for p in compare(BASE, new, "T")}


def test_campo_opcional_novo_e_compativel() -> None:
    assert _codes(_with(note={"type": "string"})) == set()


def test_descricao_nova_e_compativel() -> None:
    assert _codes(_with(day={"type": "integer", "minimum": 1, "description": "dia"})) == set()


def test_campo_removido_e_incompativel() -> None:
    new = {**BASE, "properties": {k: v for k, v in BASE["properties"].items() if k != "phase"}}
    assert _codes(new) == {"compat_removed_field"}


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"required": ["day", "phase"]}, "compat_new_required"),
        ({"day": {"type": "number", "minimum": 1}}, "compat_changed"),
        ({"phase": {"type": "string", "maxLength": 32}}, "compat_tightened"),
        ({"day": {"type": "integer", "minimum": 2}}, "compat_tightened"),
        ({"reason": {"enum": ["debug"]}}, "compat_enum"),
        ({"reason": {"enum": ["debug", "budget", "maintenance"]}}, "compat_enum"),
    ],
)
def test_mudancas_incompativeis(change: dict[str, Any], code: str) -> None:
    assert _codes(_with(**change)) == {code}


def test_restricao_afrouxada_e_compativel() -> None:
    assert _codes(_with(phase={"type": "string", "maxLength": 128})) == set()
