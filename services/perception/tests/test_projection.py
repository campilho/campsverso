"""A foto da percepção sobre a projeção comum: trajeto pela metade, itens e necessidades."""

import json
from typing import Any

from campsverso_perception.view import PerceptionState as Projection


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


def session(radius: int | None) -> dict[str, Any]:
    """Um mundo 5 x 3 com terreno: parede em volta, chão no meio e água no canto (ADR-0056)."""
    legend = {
        "F": {"kind": "floor", "properties": {"passable": True, "water": False}},
        "W": {"kind": "wall", "properties": {"passable": False, "water": False}},
        "A": {"kind": "water", "properties": {"passable": False, "water": True}},
    }
    return ev(
        10,
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
            "width": 5,
            "height": 3,
            "rows": ["WWWWW", "WFFFA", "WWWWW"],
            "legend": legend,
        },
        perception={"radius": radius},
    )


def test_terreno_na_foto_inteiro_sem_raio_e_recortado_com_raio() -> None:
    p = world()
    p.apply("world", session(None))
    view = p.view("camps")
    assert view["map"]["origin"] == {"x": 0, "y": 0}
    assert view["map"]["rows"] == ["WWWWW", "WFFFA", "WWWWW"]
    assert sorted(view["map"]["legend"]) == ["A", "F", "W"]
    assert {e["entity_id"] for e in view["entities"]} == {"camps", "can", "plot-a"}

    p.apply("world", session(1))  # o avatar está em (1, 1): enxerga de (0, 0) a (2, 2)
    view = p.view("camps")
    assert view["map"] == {
        "origin": {"x": 0, "y": 0},
        "rows": ["WWW", "WFF", "WWW"],
        "legend": {
            "F": {"kind": "floor", "properties": {"passable": True, "water": False}},
            "W": {"kind": "wall", "properties": {"passable": False, "water": False}},
        },
    }
    # O canteiro em (5, 1) ficou fora; o regador, que está com o avatar, continua visível.
    assert {e["entity_id"] for e in view["entities"]} == {"camps", "can"}
    assert [c["container_id"] for c in view["containers"]] == ["camps"]


def test_delta_leva_o_que_mudou_e_o_que_aconteceu_desde_a_ultima_entrega() -> None:
    p = world()
    p.apply("world", session(None))
    assert p.wants_snapshot("camps", "llm/um", "action_completed", 20)  # nunca recebeu nada
    p.deliver("camps", "llm/um", snapshot=True)
    assert p.pending == {"camps": []}
    p.apply(
        "world",
        ev(11, 7, "world.entity.state_changed.v1", entity_id="plot-a", changes={"stage": "broto"}),
    )
    p.apply(
        "world",
        ev(
            12,
            8,
            "world.item.transferred.v1",
            item="moeda",
            qty=30,
            from_container="camps",
            to_container="kiosk",
            reason="buy",
        ),
    )
    p.apply(
        "agent",
        ev(
            13,
            8,
            "world.need.changed.v1",
            avatar_id="camps",
            need="fome",
            previous_value=0,
            value=3,
        ),
    )
    delta = p.delta("camps")
    assert (delta["since_tick"], delta["as_of_tick"]) == (0, 8)
    assert [e["entity_id"] for e in delta["entities"]] == ["plot-a"]
    assert delta["entities"][0]["attributes"] == {"crop": None, "stage": "broto"}
    assert delta["containers"] == [
        {"container_id": "camps", "items": [{"item": "moeda", "qty": 70}]},
        {"container_id": "kiosk", "items": [{"item": "moeda", "qty": 30}]},
    ]
    assert [(e["tick"], e["type"]) for e in delta["events"]] == [
        (7, "campsverso.world.entity.state_changed.v1"),
        (8, "campsverso.world.item.transferred.v1"),
        (8, "campsverso.world.need.changed.v1"),
    ]
    assert "weather" not in delta
    assert "gone" not in delta

    assert not p.wants_snapshot("camps", "llm/um", "action_completed", 20)
    p.deliver("camps", "llm/um", snapshot=False)
    assert p.delivered["camps"]["deltas"] == 1
    assert p.pending["camps"] == []
    assert p.wants_snapshot("camps", "llm/um", "possessed", 20)  # a posse pede foto
    assert p.wants_snapshot("camps", "llm/dois", "action_completed", 20)  # trocou o controlador
    assert p.wants_snapshot("camps", "llm/um", "action_completed", 1)  # chegou ao limite de deltas

    copy = Projection(json.loads(json.dumps(p.export())))
    assert copy.delivered == p.delivered
    assert copy.delta("camps") == p.delta("camps")
