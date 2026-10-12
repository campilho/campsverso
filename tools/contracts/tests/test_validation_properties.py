"""Propriedades do validador, conferidas com entradas geradas pelo hypothesis."""

import copy
import json
import uuid
from functools import cache
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from campsverso_tools.contracts import catalog
from campsverso_tools.contracts.catalog import JsonObject
from campsverso_tools.contracts.validation import EventValidator

REPO_CONTRACTS = catalog.find_contracts_dir(Path(__file__).resolve().parent)


@cache
def _setup() -> tuple[EventValidator, tuple[JsonObject, ...], catalog.Contracts]:
    contracts = catalog.load(REPO_CONTRACTS)
    documents = (
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((contracts.examples_dir / "valid").glob("*.json"))
    )  # só envelopes: as mensagens do WebSocket têm o validador delas (ADR-0050)
    examples = tuple(d for d in documents if not d["type"].startswith(catalog.MESSAGE_PREFIXES))
    return EventValidator(contracts), examples, contracts


def _example(index: int) -> JsonObject:
    _, examples, _ = _setup()
    return copy.deepcopy(examples[index % len(examples)])


def _codes(event: JsonObject) -> set[str]:
    validator, _, _ = _setup()
    return {p.code for p in validator.validate(event)}


examples_index = st.integers(min_value=0, max_value=10_000)
snake_names = st.from_regex(r"\Azz_[a-z]{1,10}\Z")  # prefixo que nenhum schema usa


@given(examples_index, snake_names)
def test_campo_desconhecido_no_payload_e_recusado(index: int, name: str) -> None:
    event = _example(index)
    event["data"][name] = 1
    assert _codes(event) == {"payload_schema"}


@given(examples_index)
def test_id_uuid7_e_aceito(index: int) -> None:
    event = _example(index)
    event["id"] = str(uuid.uuid7())
    assert _codes(event) == set()


@given(examples_index)
def test_id_uuid4_e_recusado(index: int) -> None:
    event = _example(index)
    event["id"] = str(uuid.uuid4())
    assert _codes(event) == {"envelope_schema"}


@given(examples_index, st.sampled_from(catalog.VISIBILITIES))
def test_visibilidade_diferente_da_declarada_e_recusada(index: int, visibility: str) -> None:
    event = _example(index)
    _, _, contracts = _setup()
    declared = contracts.by_type[event["type"]].visibility
    event["visibility"] = visibility
    assert _codes(event) == (set() if visibility == declared else {"visibility_mismatch"})
