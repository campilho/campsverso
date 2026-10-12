"""O serviço publica pelo barramento validador: nenhum evento sai fora do contrato (critério A2)."""

from typing import Any

from campsverso_adapters import (
    FakeWallClock,
    InMemoryBus,
    MemoryBlobStore,
    MemoryTelemetry,
    SequentialUuid7Ids,
    SqliteWorldStore,
    ValidatingBus,
)
from campsverso_kernel import Engine, KernelService, run_version
from campsverso_kernel.testing import SCRIPT, LabCartridge, make_core
from campsverso_ports import Envelope, EventBus

ids = SequentialUuid7Ids()


def lab_service(bus: EventBus) -> KernelService:
    engine = Engine(make_core(), run_version("lab", 60, {"lab": LabCartridge()}))
    return KernelService(
        engine,
        bus,
        FakeWallClock(),
        SequentialUuid7Ids(),
        SqliteWorldStore(":memory:"),
        MemoryBlobStore(),
        MemoryTelemetry(),
    )


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
    service = lab_service(bus)
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
