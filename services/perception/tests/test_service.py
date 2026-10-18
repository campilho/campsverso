"""Foto ou delta pelo barramento (ADR-0056): tudo o que a percepção publica passa pelo contrato."""

from collections.abc import Mapping
from typing import Any

from campsverso_adapters import (
    FakeWallClock,
    InMemoryBus,
    MemoryBlobStore,
    MemoryTelemetry,
    SequentialUuid7Ids,
    ValidatingBus,
)
from campsverso_contracts import subject
from campsverso_perception.service import DELIVERED, UPDATED, PerceptionPolicy, PerceptionService

WORLD = "lab-01"
ids = SequentialUuid7Ids()
LEGEND = {
    "F": {"kind": "floor", "properties": {"passable": True, "water": False}},
    "W": {"kind": "wall", "properties": {"passable": False, "water": False}},
}


def ev(seq: int, tick: int, kind: str, /, **data: Any) -> dict[str, Any]:
    minute = tick % 60
    return {
        "id": ids.new_id(),
        "type": f"campsverso.{kind}",
        "seq": seq,
        "tick": tick,
        "simtime": f"2026-10-10T06:{minute:02d}:00-03:00",
        "cartridge": "farm_camps",
        "data": data,
    }


def decision(seq: int, tick: int, reason: str, controller: str) -> dict[str, Any]:
    kind, _ = controller.split("/")
    return ev(
        seq,
        tick,
        "avatar.decision_requested.v1",
        avatar_id="ana",
        reason=reason,
        controller={"type": kind, "id": controller},
        needs={"fome": 10.0, "energia": 90.0},
        position={"x": 1, "y": 1},
    )


class Lab:
    def __init__(self, policy: PerceptionPolicy | None = None) -> None:
        self.inner = InMemoryBus()
        self.service = PerceptionService(
            WORLD,
            ValidatingBus(self.inner),
            MemoryBlobStore(),
            FakeWallClock(),
            SequentialUuid7Ids(),
            MemoryTelemetry(),
            policy,
        )
        self.world_seq = 0
        self.agent_seq = 0

    async def start(self) -> None:
        await self.service.start()
        await self.world(
            0,
            "world.session.started.v1",
            cartridge_version="0.1.0",
            seed=7,
            tick_seconds=60,
            mode="continuous",
            paused=False,
            scale=72,
            resumed=False,
            map={
                "id": "lab",
                "width": 4,
                "height": 3,
                "rows": ["WWWW", "WFFW", "WWWW"],
                "legend": LEGEND,
            },
            perception={"radius": None},
        )
        await self.world(
            0, "world.entity.spawned.v1", entity_id="ana", kind="avatar", position={"x": 1, "y": 1}
        )
        await self.world(
            0,
            "world.entity.spawned.v1",
            entity_id="plot-a",
            kind="plot",
            position={"x": 2, "y": 1},
            attributes={"stage": "semente"},
        )

    async def world(self, tick: int, kind: str, /, **data: Any) -> None:
        envelope = ev(self.world_seq, tick, kind, **data)
        self.world_seq += 1
        await self.inner.publish(subject(envelope["type"], WORLD), envelope)

    async def decide(self, tick: int, reason: str, controller: str) -> Mapping[str, Any]:
        """Publica o pedido e devolve a entrega que a percepção respondeu."""
        before = len(self.inner.published)
        envelope = decision(self.agent_seq, tick, reason, controller)
        self.agent_seq += 1
        await self.inner.publish(subject(envelope["type"], WORLD, "ana"), envelope)
        delivered = [
            e for _, e in self.inner.published[before:] if e["type"] in (DELIVERED, UPDATED)
        ]
        assert len(delivered) == 1
        assert delivered[0]["causationid"] == envelope["id"]
        return delivered[0]


async def test_llm_recebe_foto_depois_deltas_e_foto_de_novo_a_cada_n() -> None:
    lab = Lab(PerceptionPolicy(frozenset({"llm"}), snapshot_every=2))
    await lab.start()
    first = await lab.decide(1, "session_started", "llm/um")
    assert first["type"] == DELIVERED
    assert first["data"]["view"]["map"]["rows"] == ["WWWW", "WFFW", "WWWW"]

    await lab.world(
        5, "world.entity.state_changed.v1", entity_id="plot-a", changes={"stage": "broto"}
    )
    second = await lab.decide(6, "action_completed", "llm/um")
    assert second["type"] == UPDATED
    assert (second["data"]["since_tick"], second["data"]["as_of_tick"]) == (1, 6)
    assert second["data"]["entities"] == [
        {
            "entity_id": "plot-a",
            "kind": "plot",
            "position": {"x": 2, "y": 1},
            "attributes": {"stage": "broto"},
        }
    ]
    assert [e["type"] for e in second["data"]["events"]] == [
        "campsverso.world.entity.state_changed.v1"
    ]
    assert second["data"]["decision"] == {
        "reason": "action_completed",
        "controller": {"type": "llm", "id": "llm/um"},
    }
    assert "map" not in second["data"]

    third = await lab.decide(7, "action_completed", "llm/um")
    assert third["type"] == UPDATED
    assert third["data"]["events"] == []  # nada aconteceu desde o delta anterior
    fourth = await lab.decide(8, "action_completed", "llm/um")
    assert fourth["type"] == DELIVERED  # dois deltas: a foto volta
    fifth = await lab.decide(9, "possessed", "llm/um")
    assert fifth["type"] == DELIVERED  # a posse sempre recebe foto
    sixth = await lab.decide(10, "action_completed", "llm/dois")
    assert sixth["type"] == DELIVERED  # trocou o controlador
    assert lab.service.delivered == 6
    sent = [e["seq"] for _, e in lab.inner.published if e["type"] in (DELIVERED, UPDATED)]
    assert sent == list(range(6))


async def test_script_recebe_sempre_a_foto() -> None:
    lab = Lab()
    await lab.start()
    for tick, reason in ((1, "session_started"), (2, "action_completed"), (3, "action_completed")):
        delivered = await lab.decide(tick, reason, "script/farmer-v1")
        assert delivered["type"] == DELIVERED
        assert delivered["data"]["kind"] == "snapshot"
