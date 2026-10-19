"""O runner com a mente (ADR-0059): posse e devolução, fotos e deltas, pedidos superados e a
desistência que devolve o avatar ao script."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import pytest

from campsverso_adapters import FakeWallClock, InMemoryBus, MemoryTelemetry, SequentialUuid7Ids
from campsverso_controller_runner.runner import ControllerRunner

DELIVERED = "campsverso.w.agent.camps.perception.delivered.v1"
UPDATED = "campsverso.w.agent.camps.perception.updated.v1"


class FakeMind:
    controller_type = "llm"
    controller_id = "llm/camps"

    def __init__(self) -> None:
        self.decided: list[Mapping[str, Any]] = []
        self.observed: list[Mapping[str, Any]] = []
        self.gave_up = False
        self.give_up_next = False

    def observe(self, delivery: Mapping[str, Any]) -> None:
        self.observed.append(delivery)

    async def decide(self, delivery: Mapping[str, Any]) -> Mapping[str, Any] | None:
        self.decided.append(delivery)
        if self.give_up_next:
            self.gave_up = True
            return None
        return {"action": "wait", "params": {"ticks": 3}, "intent": f"decisão {len(self.decided)}"}


class Script:
    controller_type = "script"
    controller_id = "script/x"

    def decide(self, view: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"action": "sleep", "params": {}}


def delivery(
    ids: SequentialUuid7Ids,
    kind: str,
    seq: int,
    *,
    controller: tuple[str, str] = ("llm", "llm/camps"),
    time: str = "2026-10-10T09:00:00.000Z",
    tick: int | None = None,
) -> dict[str, Any]:
    delivered = kind == "delivered"
    data: dict[str, Any] = (
        {"view": {"self": {}}} if delivered else {"since_tick": 1, "as_of_tick": 2, "events": []}
    )
    data["decision"] = {
        "reason": "action_completed",
        "controller": {"type": controller[0], "id": controller[1]},
    }
    envelope: dict[str, Any] = {
        "id": ids.new_id(),
        "type": f"campsverso.perception.{'delivered' if delivered else 'updated'}.v1",
        "cartridge": "farm_camps",
        "seq": seq,
        "time": time,
        "correlationid": f"corr-{seq}",
        "data": data,
    }
    if tick is not None:
        envelope |= {"tick": tick, "simtime": "2026-10-10T06:05:00-03:00"}
    return envelope


def published(bus: InMemoryBus, suffix: str) -> list[dict[str, Any]]:
    return [dict(e) for s, e in bus.published if s.endswith(suffix)]


def runner(
    bus: InMemoryBus,
    mind: FakeMind | Script,
    *,
    possess: bool = False,
    clock: FakeWallClock | None = None,
) -> tuple[ControllerRunner, SequentialUuid7Ids, MemoryTelemetry]:
    ids, notes = SequentialUuid7Ids(), MemoryTelemetry()
    made = ControllerRunner(
        "w",
        "camps",
        mind,
        bus,
        ids,
        clock or FakeWallClock(),
        notes,
        cartridge="farm_camps",
        possess=possess,
    )
    return made, ids, notes


async def test_a_mente_assume_ao_subir_e_devolve_ao_descer() -> None:
    bus = InMemoryBus()
    made, _, notes = runner(bus, FakeMind(), possess=True)
    await made.start()
    (possess,) = published(bus, "cmd.avatar.possess.v1")
    assert possess["data"] == {
        "avatar_id": "camps",
        "controller": {"type": "llm", "id": "llm/camps"},
    }
    assert possess["actor"] == "llm/camps"
    assert possess["cartridge"] == "farm_camps"
    assert possess["dataschema"] == "contracts://commands/avatar/possess.v1"
    assert possess["visibility"] == "observer"
    assert possess["seq"] == 0
    assert made.possessing
    assert made.is_mind
    await made.stop()
    (release,) = published(bus, "cmd.avatar.release.v1")
    assert release["data"] == {"avatar_id": "camps"}
    assert release["seq"] == 1
    assert not made.possessing
    assert "controller.released" in notes.events("warning")


def test_assumir_exige_o_cartucho() -> None:
    with pytest.raises(ValueError, match="cartucho"):
        ControllerRunner(
            "w",
            "camps",
            FakeMind(),
            InMemoryBus(),
            SequentialUuid7Ids(),
            FakeWallClock(),
            MemoryTelemetry(),
            possess=True,
        )


async def test_fotos_e_deltas_viram_propostas_com_a_correlacao() -> None:
    bus, mind = InMemoryBus(), FakeMind()
    made, ids, _ = runner(bus, mind)
    await made.start()
    first = delivery(ids, "delivered", 0, tick=5)
    await bus.publish(DELIVERED, first)
    await bus.publish(UPDATED, delivery(ids, "updated", 1, tick=9))
    proposals = published(bus, "cmd.action.propose.v1")
    assert [p["data"]["intent"] for p in proposals] == ["decisão 1", "decisão 2"]
    assert proposals[0]["data"]["action"] == "wait"
    assert proposals[0]["correlationid"] == "corr-0"
    assert proposals[0]["causationid"] == first["id"]
    assert proposals[0]["tick"] == 5
    assert proposals[0]["controller"] == "llm"
    assert proposals[0]["controllerid"] == "llm/camps"
    assert "since_tick" in mind.decided[1]  # a mente recebe a entrega inteira, delta inclusive
    assert made.sim_time() == (9, "2026-10-10T06:05:00-03:00")
    assert made.answered == 2


async def test_pedido_superado_entra_na_janela_sem_chamada() -> None:
    bus, mind = InMemoryBus(), FakeMind()
    clock = FakeWallClock(datetime(2026, 10, 10, 9, 0, 5, tzinfo=UTC))
    made, ids, notes = runner(bus, mind, clock=clock)
    await made.start()
    await bus.publish(DELIVERED, delivery(ids, "delivered", 0, time="2026-10-10T09:00:00.000Z"))
    # Publicada antes de a proposta sair (09:00:05): superada, só entra na janela.
    await bus.publish(UPDATED, delivery(ids, "updated", 1, time="2026-10-10T09:00:02.000Z"))
    assert len(mind.decided) == 1
    assert len(mind.observed) == 1
    assert made.superseded == 1
    assert "controller.superseded" in notes.events("info")
    clock.advance(10)
    await bus.publish(UPDATED, delivery(ids, "updated", 2, time="2026-10-10T09:00:12.000Z"))
    assert len(mind.decided) == 2
    assert len(published(bus, "cmd.action.propose.v1")) == 2


async def test_desistir_devolve_o_avatar_ao_script() -> None:
    bus, mind = InMemoryBus(), FakeMind()
    made, ids, notes = runner(bus, mind, possess=True)
    await made.start()
    await bus.publish(DELIVERED, delivery(ids, "delivered", 0))
    mind.give_up_next = True
    await bus.publish(UPDATED, delivery(ids, "updated", 1))
    assert len(published(bus, "cmd.action.propose.v1")) == 1
    (release,) = published(bus, "cmd.avatar.release.v1")
    assert release["data"] == {"avatar_id": "camps"}
    assert not made.possessing
    assert made.released == 1
    assert "controller.gave_up" in notes.events("error")
    await made.stop()  # já devolveu: não devolve de novo
    assert len(published(bus, "cmd.avatar.release.v1")) == 1


async def test_o_script_so_entende_a_foto_e_a_vez_dos_outros_e_ignorada() -> None:
    bus = InMemoryBus()
    made, ids, _ = runner(bus, Script())
    await made.start()
    assert not made.is_mind
    await bus.publish(UPDATED, delivery(ids, "updated", 0, controller=("script", "script/x")))
    await bus.publish(DELIVERED, delivery(ids, "delivered", 1, controller=("llm", "llm/camps")))
    assert published(bus, "cmd.action.propose.v1") == []
    await bus.publish(DELIVERED, delivery(ids, "delivered", 2, controller=("script", "script/x")))
    assert [p["data"]["action"] for p in published(bus, "cmd.action.propose.v1")] == ["sleep"]
