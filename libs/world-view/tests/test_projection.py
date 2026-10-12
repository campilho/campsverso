"""Projeção comum: sessão, relógio, posse, último pedido e o vai e volta em JSON (ADR-0050)."""

import json
from typing import Any

from campsverso_world_view import Projection, path_from

SCRIPT = {"type": "script", "id": "script/farmer-v1"}
HUMAN = {"type": "human", "id": "human/camps-browser"}


def ev(seq: int, tick: int, kind: str, /, **data: Any) -> dict[str, Any]:
    return {
        "type": f"campsverso.{kind}",
        "seq": seq,
        "tick": tick,
        "simtime": f"t{tick}",
        "data": data,
    }


def started() -> Projection:
    p = Projection()
    p.apply(
        "world",
        ev(
            0,
            0,
            "world.session.started.v1",
            cartridge_version="0.1.0",
            seed=7,
            tick_seconds=60,
            mode="continuous",
            paused=False,
            scale=72,
            map={"id": "farm_camps", "width": 32, "height": 18},
            affordances=[{"action": "water", "label": "Regar", "on": ["plot"], "target": True}],
        ),
    )
    p.apply(
        "world",
        ev(
            1,
            0,
            "world.entity.spawned.v1",
            entity_id="bed",
            kind="bed",
            position={"x": 3, "y": 3},
            display_name="Cama",
        ),
    )
    return p


def test_sessao_e_relogio() -> None:
    p = started()
    assert p.session == {
        "cartridge_version": "0.1.0",
        "tick_seconds": 60,
        "map": {"id": "farm_camps", "width": 32, "height": 18},
        "affordances": [{"action": "water", "label": "Regar", "on": ["plot"], "target": True}],
    }
    assert p.clock == {"mode": "continuous", "scale": 72.0, "paused": False}
    p.apply("world", ev(2, 5, "world.clock.paused.v1", reason="debug", by="human/operador"))
    p.apply(
        "world",
        ev(
            3,
            5,
            "world.clock.scale_changed.v1",
            previous_scale=72,
            scale=720,
            reason="operator",
            by="x",
        ),
    )
    p.apply(
        "world",
        ev(
            4,
            5,
            "world.clock.mode_changed.v1",
            previous_mode="continuous",
            mode="max",
            reason="r",
            by="x",
        ),
    )
    assert p.clock == {"mode": "max", "scale": 720.0, "paused": True}
    p.apply("world", ev(5, 5, "world.clock.resumed.v1", by="human/operador"))
    assert p.clock["paused"] is False
    assert p.entities["bed"]["display_name"] == "Cama"


def test_posse_e_ultimo_pedido_de_decisao() -> None:
    p = started()
    p.apply(
        "agent",
        ev(
            0,
            9,
            "avatar.decision_requested.v1",
            avatar_id="camps",
            reason="session_started",
            controller=SCRIPT,
            needs={"fome": 0, "energia": 100},
            position={"x": 4, "y": 4},
        ),
    )
    assert p.controllers == {"camps": SCRIPT}
    assert p.decisions == {"camps": {"reason": "session_started", "tick": 9}}
    p.apply(
        "world",
        ev(2, 12, "avatar.possessed.v1", avatar_id="camps", controller=HUMAN, by="human/operador"),
    )
    assert p.controllers["camps"] == HUMAN
    p.apply(
        "world",
        ev(
            3,
            20,
            "avatar.released.v1",
            avatar_id="camps",
            previous_controller=HUMAN,
            controller=SCRIPT,
            by="human/operador",
        ),
    )
    assert p.controllers["camps"] == SCRIPT


def test_vai_e_volta_em_json_e_ignora_chaves_de_outros() -> None:
    p = started()
    saved = {**json.loads(json.dumps(p.export())), "out_seq": 3}
    copy = Projection(saved)
    assert copy.export() == p.export()
    assert "out_seq" not in copy.export()


def test_trajeto_tile_a_tile_pelas_esquinas() -> None:
    path = path_from({"x": 1, "y": 1}, [{"x": 3, "y": 1}, {"x": 3, "y": 2}])
    assert path == [{"x": 1, "y": 1}, {"x": 2, "y": 1}, {"x": 3, "y": 1}, {"x": 3, "y": 2}]


def test_pedido_de_decisao_guarda_o_tick_do_proprio_evento() -> None:
    """world pode chegar antes de agent: o tick do pedido não pode vir do maior tick já visto."""
    p = started()
    p.apply("world", ev(2, 40, "world.clock.phase_changed.v1", phase="meio_dia", day=1))
    p.apply(
        "agent",
        ev(
            0,
            35,
            "avatar.decision_requested.v1",
            avatar_id="camps",
            reason="action_completed",
            controller=SCRIPT,
            needs={"fome": 1, "energia": 99},
            position={"x": 4, "y": 4},
        ),
    )
    assert p.decisions["camps"]["tick"] == 35
    assert p.tick == 40


def test_acao_com_inicio_e_politica_e_sono_com_hora_de_acordar() -> None:
    """A barra de progresso da tela sai daqui (ADR-0052)."""
    p = started()
    p.apply(
        "world",
        ev(
            2,
            10,
            "action.accepted.v1",
            action_id="act-1",
            avatar_id="camps",
            action="plant",
            params={"target": "plot-e-01"},
            applied_tick=10,
            duration_ticks=5,
            interrupt="never",
        ),
    )
    assert p.actions["camps"] == {
        "action_id": "act-1",
        "action": "plant",
        "params": {"target": "plot-e-01"},
        "applied_tick": 10,
        "end_tick": 15,
        "interrupt": "never",
    }
    p.apply(
        "world",
        ev(
            3,
            20,
            "avatar.sleep.started.v2",
            avatar_id="camps",
            cause="voluntary",
            position={"x": 3, "y": 4},
            wake_at_tick=80,
        ),
    )
    assert p.sleep == {"camps": {"since_tick": 20, "wake_at_tick": 80}}
    assert Projection(json.loads(json.dumps(p.export()))).sleep == p.sleep
    p.apply(
        "world",
        ev(4, 80, "avatar.sleep.ended.v2", avatar_id="camps", cause="voluntary", energy=100.0),
    )
    assert (p.sleep, p.asleep) == ({}, {"camps": False})
