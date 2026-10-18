"""O serviço publica pelo barramento validador: nenhum evento sai fora do contrato (critério A2)."""

import asyncio
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
from campsverso_kernel.runner import ClockLoop
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


async def test_pulso_no_ritmo_configurado_e_fora_do_historico() -> None:
    """O pulso (ADR-0051) sai a cada `pulse_seconds` de tempo real e não vira fato publicado."""
    inner = InMemoryBus()
    clock = FakeWallClock()
    engine = Engine(make_core(), run_version("lab", 60, {"lab": LabCartridge()}))
    service = KernelService(
        engine,
        ValidatingBus(inner),
        clock,
        SequentialUuid7Ids(),
        SqliteWorldStore(":memory:"),
        MemoryBlobStore(),
        MemoryTelemetry(),
    )
    pulses: list[Envelope] = []

    async def on_pulse(_: str, message: Envelope) -> None:
        pulses.append(message)

    await inner.subscribe("campsverso.*.live.>", on_pulse)
    await service.start()
    stop = asyncio.Event()
    running = asyncio.create_task(ClockLoop(service, clock, pulse_seconds=1.0).run(stop))
    for _ in range(3):
        await asyncio.sleep(0.15)
        clock.advance(0.5)  # meio segundo: ainda não é hora do próximo pulso
        await asyncio.sleep(0.15)
        clock.advance(0.5)
    await asyncio.sleep(0.15)
    stop.set()
    await running
    assert len(pulses) == 4  # o primeiro na hora e um por segundo de relógio
    assert pulses[-1]["type"] == "campsverso.live.kernel.v1"
    assert pulses[-1]["tick"] == service.core.tick
    assert {p["pulse_seconds"] for p in pulses} == {1.0}
    assert all(".live." not in subject for subject, _ in inner.published)


async def test_tick_antecipado_no_modo_continuo() -> None:
    """ADR-0057: uma proposta no meio do minuto roda o próximo tick na hora; a seguinte espera."""
    inner = InMemoryBus()
    bus = ValidatingBus(inner)
    clock = FakeWallClock()
    engine = Engine(make_core(), run_version("lab", 60, {"lab": LabCartridge()}))
    service = KernelService(
        engine,
        bus,
        clock,
        SequentialUuid7Ids(),
        SqliteWorldStore(":memory:"),
        MemoryBlobStore(),
        MemoryTelemetry(),
    )
    await service.start()
    assert service.core.mode == "continuous"
    assert not service.core.paused
    stop = asyncio.Event()
    running = asyncio.create_task(ClockLoop(service, clock).run(stop))
    await asyncio.sleep(0.1)
    before = service.core.tick
    subject = "campsverso.lab-01.cmd.action.propose.v1"
    await bus.publish(subject, _command("move", {"target": {"x": 3, "y": 1}}))
    await asyncio.sleep(0.2)
    assert service.core.tick == before + 1  # o relógio de parede não andou: tick antecipado
    await bus.publish(subject, _command("move", {"target": {"x": 4, "y": 1}}))
    await asyncio.sleep(0.2)
    assert service.core.tick == before + 1  # dívida em aberto: a segunda espera o ritmo normal
    seconds = engine.core.calendar.tick_seconds / service.core.scale
    clock.advance(seconds)  # um tick de relógio: só paga a dívida
    await asyncio.sleep(0.2)
    assert service.core.tick == before + 1
    clock.advance(seconds)
    await asyncio.sleep(0.2)
    assert service.core.tick == before + 2  # dois ticks de relógio, dois ticks: nenhum a mais
    stop.set()
    await running
