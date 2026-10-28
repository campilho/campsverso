"""Foto ou delta pelo barramento (ADR-0056): tudo o que a percepção publica passa pelo contrato."""

from collections.abc import Mapping
from typing import Any

import pytest

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
from campsverso_ports import Envelope, EventBus

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


class Killed(BaseException):
    """O `kill -9`: nada mais roda no processo, nem o `except Exception` do serviço."""


class DyingBus(ValidatingBus):
    """O barramento de um processo que morre ao publicar a entrega `seq`: antes de a mensagem
    chegar ao servidor ou depois, sem ver a resposta."""

    def __init__(self, server: InMemoryBus, seq: int, *, stored: bool) -> None:
        super().__init__(server)
        self.server, self.seq, self.stored = server, seq, stored

    async def publish(self, subject: str, envelope: Envelope) -> None:
        if envelope["type"] == DELIVERED and envelope["seq"] == self.seq:
            if self.stored:
                self.server.published.append((subject, envelope))  # guardada, ninguém leu ainda
            raise Killed
        await super().publish(subject, envelope)


class Lab:
    def __init__(self, policy: PerceptionPolicy | None = None) -> None:
        self.inner = InMemoryBus()
        self.blobs = MemoryBlobStore()
        self.service = self.spawn(ValidatingBus(self.inner), policy)
        self.world_seq = 0
        self.agent_seq = 0

    def spawn(self, bus: EventBus, policy: PerceptionPolicy | None = None) -> PerceptionService:
        """Um processo da percepção; o arquivo da projeção é o mesmo de um processo para outro."""
        return PerceptionService(
            WORLD,
            bus,
            self.blobs,
            FakeWallClock(),
            SequentialUuid7Ids(),
            MemoryTelemetry(),
            policy,
        )

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

    def request(self, tick: int, reason: str, controller: str) -> dict[str, Any]:
        """O próximo pedido de decisão do kernel, ainda sem publicar."""
        envelope = decision(self.agent_seq, tick, reason, controller)
        self.agent_seq += 1
        return envelope

    async def ask(self, envelope: Mapping[str, Any]) -> None:
        await self.inner.publish(subject(str(envelope["type"]), WORLD, "ana"), envelope)

    async def decide(self, tick: int, reason: str, controller: str) -> Mapping[str, Any]:
        """Publica o pedido e devolve a entrega que a percepção respondeu."""
        before = len(self.inner.published)
        envelope = self.request(tick, reason, controller)
        await self.ask(envelope)
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


@pytest.mark.parametrize("stored", [False, True], ids=["antes-do-servidor", "depois-do-servidor"])
async def test_a_queda_na_entrega_nao_repete_o_seq_nem_perde_a_foto(stored: bool) -> None:
    """O A6 da percepção sem corrida: o processo morre publicando a terceira foto, antes de o
    servidor guardá-la ou depois. O que volta segue do seq seguinte, e cada pedido tem uma foto.

    Com o seq gravado só depois do publish, a volta reusava o 2 (o e2e do A6 viu isso uma vez,
    em 28/out); com o pedido dado por visto antes do publish, a foto se perdia."""
    lab = Lab()
    lab.service = lab.spawn(DyingBus(lab.inner, 2, stored=stored))
    await lab.start()
    asked = [await lab.decide(tick, "action_completed", "script/farmer-v1") for tick in (1, 2)]
    third = lab.request(3, "action_completed", "script/farmer-v1")
    with pytest.raises(Killed):
        await lab.ask(third)
    await lab.service.stop()

    lab.service = lab.spawn(ValidatingBus(lab.inner))
    await lab.service.start()
    fourth = await lab.decide(4, "action_completed", "script/farmer-v1")
    # O JetStream só reentrega o pedido sem confirmação depois do ack_wait, atrás dos novos.
    await lab.ask(third)

    sent = [e for _, e in lab.inner.published if e["type"] == DELIVERED]
    photos = {e["id"]: e for e in sent}  # o JetStream descarta o id repetido (Nats-Msg-Id)
    assert all(e == photos[e["id"]] for e in sent)  # repetida, só a mesma entrega
    assert sorted(e["seq"] for e in photos.values()) == [0, 1, 2, 3]
    answered = sorted(str(e["causationid"]) for e in photos.values())  # uma foto por pedido
    assert answered == sorted([*(str(e["causationid"]) for e in [*asked, fourth]), third["id"]])
