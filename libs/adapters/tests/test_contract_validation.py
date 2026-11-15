"""O validador de contratos de quem roda (critério A2): um número não finito não é um número."""

import json
from typing import Any

import pytest

from campsverso_adapters import ContractValidator


def _set_scale(scale: Any) -> dict[str, Any]:
    return {
        "specversion": "1.0",
        "id": "019a0000-0000-7000-8000-000000000001",
        "source": "/operator/teste",
        "type": "campsverso.cmd.clock.set_scale.v1",
        "time": "2026-11-14T12:00:00Z",
        "datacontenttype": "application/json",
        "dataschema": "contracts://commands/clock/set_scale.v1",
        "worldid": "lab-01",
        "cartridge": "lab",
        "seq": 0,
        "actor": "human/operator",
        "provenance": "simulated",
        "visibility": "observer",
        "data": {"scale": scale, "reason": "operator"},
    }


def test_numeros_finitos_passam_inteiros_ou_nao() -> None:
    validator = ContractValidator()
    for scale in (1, 72, 0.5, 10**30):
        assert validator.validate(_set_scale(scale)) == []


@pytest.mark.parametrize("text", ["1e999", "Infinity", "-Infinity", "NaN", "1" + "0" * 400])
def test_infinito_e_nan_nao_sao_numeros(text: str) -> None:
    """O `json` do Python lê todos (o último como um inteiro que não cabe num float); o ajv, em
    modo estrito, também não os aceita."""
    (problem,) = ContractValidator().validate(_set_scale(json.loads(text)))
    assert problem.code == "payload_schema"
    assert problem.message.startswith("scale:")


def test_o_tick_do_envelope_tambem_nao_aceita_infinito() -> None:
    envelope = _set_scale(72) | {"tick": json.loads("1e999")}
    assert [p.code for p in ContractValidator().validate(envelope)] == ["envelope_schema"]
