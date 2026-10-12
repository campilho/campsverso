"""Projeção da percepção: só eventos visíveis, trajeto pela metade, itens e necessidades."""

import json
from typing import Any

from campsverso_perception.projection import Projection


def ev(seq: int, tick: int, kind: str, /, **data: Any) -> dict[str, Any]:
    return {
        "type": f"campsverso.{kind}",
        "seq": seq,
        "tick": tick,
        "simtime": f"t{tick}",
        "cartridge": "farm_camps",
        "data": data,
    }


def world() -> Projection:
    p = Projection()
    for envelope in (
        ev(
            0,
            0,
            "world.entity.spawned.v1",
            entity_id="camps",
            kind="avatar",
            position={"x": 1, "y": 1},
        ),
        ev(
            1,
            0,
            "world.entity.spawned.v1",
            entity_id="plot-a",
            kind="plot",
            position={"x": 5, "y": 1},
            attributes={"crop": None, "stage": None},
        ),
        ev(
            2,
            0,
            "world.entity.spawned.v1",
            entity_id="can",
            kind="watering_can",
            container_id="camps",
            attributes={"charges": 10},
        ),
        ev(
            3,
            0,
            "world.item.created.v1",
            item="moeda",
            qty=100,
            container_id="camps",
            reason="initial",
        ),
        ev(4, 0, "world.clock.phase_changed.v1", phase="amanhecer", day=1),
        ev(5, 0, "world.weather.changed.v1", condition="sun", day=1),
    ):
        p.apply("world", envelope)
    return p


def test_trajeto_pela_metade_e_posicao_no_tick() -> None:
    p = world()
    p.apply(
        "world",
        ev(
            6,
            10,
            "action.accepted.v1",
            action_id="act-1",
            avatar_id="camps",
            action="move",
            params={},
            applied_tick=10,
            duration_ticks=2,
        ),
    )
    p.apply(
        "world",
        ev(
            7,
            10,
            "world.entity.moved.v1",
            entity_id="camps",
            action_id="act-1",
            origin={"x": 1, "y": 1},
            waypoints=[{"x": 3, "y": 1}, {"x": 3, "y": 3}],
            depart_tick=10,
            arrival_tick=12,
            tiles_per_tick=2.0,
        ),
    )
    assert p.position_at("camps", 10) == {"x": 1, "y": 1}
    assert p.position_at("camps", 11) == {"x": 3, "y": 1}
    assert p.position_at("camps", 13) == {"x": 3, "y": 3}
    view = p.view("camps")
    assert view["self"]["action"]["end_tick"] == 12


def test_itens_atributos_e_pedido_de_decisao() -> None:
    p = world()
    p.apply(
        "world",
        ev(
            6,
            5,
            "world.item.transferred.v1",
            item="moeda",
            qty=30,
            from_container="camps",
            to_container="kiosk",
            reason="buy",
        ),
    )
    p.apply(
        "world",
        ev(
            7,
            5,
            "world.entity.state_changed.v1",
            entity_id="plot-a",
            changes={"crop": "rabanete", "stage": "semente"},
        ),
    )
    p.apply(
        "agent",
        ev(
            8,
            6,
            "avatar.decision_requested.v1",
            avatar_id="camps",
            reason="woke_up",
            controller={"type": "script", "id": "s"},
            needs={"fome": 10.5, "energia": 90},
            position={"x": 2, "y": 1},
        ),
    )
    view = p.view("camps")
    assert view["self"]["needs"] == {"energia": 90.0, "fome": 10.5}
    assert view["self"]["position"] == {"x": 2, "y": 1}
    assert {"container_id": "camps", "items": [{"item": "moeda", "qty": 70}]} in view["containers"]
    plot = next(e for e in view["entities"] if e["entity_id"] == "plot-a")
    assert plot["attributes"] == {"crop": "rabanete", "stage": "semente"}
    assert (view["clock"]["phase"], view["weather"]) == (
        "amanhecer",
        {"condition": "sun", "day": 1},
    )


def test_reentrega_e_ignorada_e_estado_vai_e_volta_em_json() -> None:
    p = world()
    again = ev(
        3, 0, "world.item.created.v1", item="moeda", qty=100, container_id="camps", reason="initial"
    )
    assert p.seen("world", again)
    copy = Projection(json.loads(json.dumps(p.export())))
    assert copy.view("camps") == p.view("camps")
