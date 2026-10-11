import json
from pathlib import Path
from typing import Any

import pytest

from campsverso_adapters import (
    ContractViolationError,
    InMemoryBus,
    ValidatingBus,
    subject_matches,
)
from campsverso_ports import Envelope

EXAMPLES = Path(__file__).resolve().parents[3] / "contracts" / "examples" / "valid"


def _example(event_type: str) -> dict[str, Any]:
    return json.loads((EXAMPLES / f"{event_type}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("pattern", "subject", "expected"),
    [
        ("campsverso.w.world.>", "campsverso.w.world.action.completed.v1", True),
        ("campsverso.*.world.>", "campsverso.w.world.action.completed.v1", True),
        ("campsverso.*.world.>", "campsverso.w.world", False),
        ("campsverso.w.agent.camps.>", "campsverso.w.agent.tomas.action.rejected.v1", False),
        ("campsverso.w.cmd.action.propose.v1", "campsverso.w.cmd.action.propose.v1", True),
        ("campsverso.w.cmd.*", "campsverso.w.cmd.action.propose.v1", False),
        ("campsverso.w.cmd.*.*.*", "campsverso.w.cmd.action.propose.v1", True),
    ],
)
def test_casamento_de_assunto_no_estilo_nats(pattern: str, subject: str, expected: bool) -> None:
    assert subject_matches(pattern, subject) is expected


async def test_entrega_na_ordem_so_para_quem_casa_e_respeita_o_cancelamento() -> None:
    bus = InMemoryBus()
    received: list[str] = []

    async def handler(subject: str, envelope: Envelope) -> None:
        received.append(f"{subject}:{envelope['n']}")

    subscription = await bus.subscribe("a.>", handler)
    await bus.publish("a.b", {"n": 1})
    await bus.publish("x.b", {"n": 2})
    await bus.publish("a.c", {"n": 3})
    await subscription.unsubscribe()
    await bus.publish("a.d", {"n": 4})

    assert received == ["a.b:1", "a.c:3"]
    assert len(bus.published) == 4


async def test_barramento_validador_aceita_evento_valido_no_assunto_certo() -> None:
    bus = ValidatingBus(InMemoryBus())
    event = _example("campsverso.action.rejected.v1")
    await bus.publish("campsverso.farm-camps-01.agent.camps.action.rejected.v1", event)


@pytest.mark.parametrize(
    ("change", "code"),
    [
        ({"visibility": "world"}, "visibility_mismatch"),
        ({"seq": -1}, "envelope_schema"),
        ({"type": "campsverso.world.entity.teleported.v1"}, "unknown_type"),
    ],
)
async def test_barramento_validador_recusa_evento_fora_do_contrato(
    change: dict[str, Any], code: str
) -> None:
    bus = ValidatingBus(InMemoryBus())
    event = {**_example("campsverso.rules.effect_applied.v1"), **change}
    with pytest.raises(ContractViolationError) as error:
        await bus.publish("campsverso.farm-camps-01.internal.rules.effect_applied.v1", event)
    assert code in {p.code for p in error.value.problems}


async def test_barramento_validador_recusa_assunto_errado() -> None:
    """Um evento internal publicado no assunto world vazaria a regra oculta (princípio 5)."""
    bus = ValidatingBus(InMemoryBus())
    event = _example("campsverso.rules.effect_applied.v1")
    with pytest.raises(ContractViolationError) as error:
        await bus.publish("campsverso.farm-camps-01.world.rules.effect_applied.v1", event)
    assert {p.code for p in error.value.problems} == {"subject_mismatch"}
