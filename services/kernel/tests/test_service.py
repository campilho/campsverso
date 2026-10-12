"""O serviço publica pelo barramento validador: nenhum evento sai fora do contrato (critério A2)."""

from typing import Any

from campsverso_adapters import FakeWallClock, InMemoryBus, SequentialUuid7Ids, ValidatingBus
from campsverso_kernel import KernelService
from campsverso_kernel.testing import SCRIPT, make_core
from campsverso_ports import Envelope

ids = SequentialUuid7Ids()


def _command(action: str, params: dict[str, Any], correlation: str | None = None) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "specversion": "1.0",
        "id": ids.new_id(),
        "source": "/controller-runner/script/lab-v1",
        "type": "campsverso.cmd.action.propose.v1",
        "time": "2026-10-10T09:00:00Z",
        "datacontenttype": "application/json",
        "dataschema": "contracts://commands/action/propose.v1",
        "worldid": "lab-01",
        "cartridge": "lab",
        "seq": 0,
        "controller": "script",
        "controllerid": SCRIPT.id,
        "provenance": "simulated",
        "visibility": "observer",
        "data": {"avatar_id": "ana", "action": action, "params": params},
    }
    if correlation:
        envelope["correlationid"] = correlation
    return envelope


async def test_dois_dias_publicados_pelo_barramento_validador() -> None:
    inner = InMemoryBus()
    bus = ValidatingBus(inner)
    service = KernelService(make_core(), bus, FakeWallClock(), SequentialUuid7Ids())
    decisions: list[Envelope] = []

    async def on_decision(_: str, envelope: Envelope) -> None:
        decisions.append(envelope)

    await bus.subscribe("campsverso.lab-01.agent.ana.avatar.decision_requested.v1", on_decision)
    await service.start()
    await service.run_ticks(5)
    correlation = str(decisions[-1]["correlationid"])
    await bus.publish(
        "campsverso.lab-01.cmd.action.propose.v1",
        _command("move", {"target": {"x": 3, "y": 1}}, correlation),
    )
    await service.run_ticks(2 * 1440)

    kernel_events = [e for s, e in inner.published if ".cmd." not in s]
    assert len(kernel_events) > 25  # mundo de laboratório: pouca coisa acontece com o avatar parado
    assert [e["seq"] for e in kernel_events] == list(range(len(kernel_events)))  # seq contínua
    completed = next(e for e in kernel_events if e["type"] == "campsverso.action.completed.v1")
    assert completed["correlationid"] == correlation  # a cadeia da decisão fica ligada
    assert "causationid" in completed
    subjects = {s.split(".")[2] for s, _ in inner.published}
    assert subjects == {"world", "agent", "internal", "cmd"}
