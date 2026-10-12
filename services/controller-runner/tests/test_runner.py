"""Controller-runner: gravação do replay e a trava contra repetir uma proposta recusada."""

from collections.abc import Mapping
from typing import Any

from campsverso_adapters import FakeWallClock, InMemoryBus, MemoryTelemetry, SequentialUuid7Ids
from campsverso_controller_runner.replay import recorded_proposals
from campsverso_controller_runner.runner import ControllerRunner

PROPOSE = "campsverso.cmd.action.propose.v1"


def test_replay_usa_o_tick_em_que_cada_proposta_valeu() -> None:
    envelopes: list[dict[str, Any]] = [
        {
            "type": PROPOSE,
            "id": "c1",
            "data": {"avatar_id": "camps", "action": "wait", "params": {}},
        },
        {
            "type": PROPOSE,
            "id": "c2",
            "data": {"avatar_id": "camps", "action": "move", "params": {}},
        },
        {
            "type": PROPOSE,
            "id": "c3",
            "data": {"avatar_id": "outro", "action": "wait", "params": {}},
        },
        {
            "type": PROPOSE,
            "id": "c4",
            "data": {"avatar_id": "camps", "action": "eat", "params": {}},
        },
        {
            "type": "campsverso.action.rejected.v1",
            "causationid": "c2",
            "seq": 9,
            "tick": 7,
            "data": {},
        },
        {
            "type": "campsverso.action.accepted.v1",
            "causationid": "c1",
            "seq": 5,
            "tick": 3,
            "data": {"applied_tick": 3},
        },
    ]
    recorded = recorded_proposals(envelopes, "camps")
    assert [(r.tick, r.data["action"]) for r in recorded] == [
        (3, "wait"),
        (7, "move"),
    ]  # c4: sem fato


class Stubborn:
    controller_type = "script"
    controller_id = "script/teimoso"

    def decide(self, view: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"action": "sleep", "params": {}}


async def test_proposta_recusada_nao_se_repete() -> None:
    bus, ids = InMemoryBus(), SequentialUuid7Ids()
    runner = ControllerRunner(
        "w", "camps", Stubborn(), bus, ids, FakeWallClock(), MemoryTelemetry()
    )
    await runner.start()
    for n, reason in enumerate(("woke_up", "action_rejected")):
        await bus.publish(
            "campsverso.w.agent.camps.perception.delivered.v1",
            {
                "id": ids.new_id(),
                "type": "campsverso.perception.delivered.v1",
                "cartridge": "farm_camps",
                "seq": n,
                "data": {
                    "view": {},
                    "decision": {
                        "reason": reason,
                        "controller": {"type": "script", "id": "script/teimoso"},
                    },
                },
            },
        )
    await bus.publish(
        "campsverso.w.agent.camps.perception.delivered.v1",
        {
            "id": ids.new_id(),
            "type": "campsverso.perception.delivered.v1",
            "cartridge": "farm_camps",
            "seq": 2,
            "data": {
                "view": {},
                "decision": {
                    "reason": "possessed",
                    "controller": {"type": "human", "id": "human/outro"},
                },
            },
        },
    )  # a vez é do humano: o script fica quieto
    actions = [e["data"]["action"] for s, e in bus.published if s.endswith("propose.v1")]
    assert actions == ["sleep", "wait"]
