"""Projeção comum: sessão, relógio, posse, último pedido e o vai e volta em JSON (ADR-0050)."""

import json
from typing import Any

from campsverso_world_view import Projection, diff_views, path_from

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
            intent="plantar rabanete perto da casa",
        ),
    )
    assert p.actions["camps"] == {
        "action_id": "act-1",
        "action": "plant",
        "params": {"target": "plot-e-01"},
        "applied_tick": 10,
        "end_tick": 15,
        "interrupt": "never",
        "intent": "plantar rabanete perto da casa",  # ADR-0059
    }
    p.apply(
        "world",
        ev(
            3,
            20,
            "avatar.sleep.started.v2",
            avatar_id="camps",
            cause="voluntary",
            bed_id="bed",
            position={"x": 3, "y": 4},
            wake_at_tick=80,
        ),
    )
    assert p.sleep == {"camps": {"since_tick": 20, "wake_at_tick": 80, "bed_id": "bed"}}
    assert Projection(json.loads(json.dumps(p.export()))).sleep == p.sleep
    p.apply(
        "world",
        ev(4, 80, "avatar.sleep.ended.v2", avatar_id="camps", cause="voluntary", energy=100.0),
    )
    assert (p.sleep, p.asleep) == ({}, {"camps": False})


CATALOG = [
    {
        "id": "colheitas",
        "label": "Colheitas",
        "kind": "count",
        "event": "campsverso.action.completed.v1",
        "where": {"action": "harvest"},
        "by": {"field": "params.target", "attribute": "group"},
    },
    {
        "id": "recusas",
        "label": "Recusas",
        "kind": "count",
        "event": "campsverso.action.rejected.v1",
        "by": {"field": "reason"},
    },
    {
        "id": "desmaios",
        "label": "Desmaios",
        "kind": "count",
        "event": "campsverso.avatar.fainted.v1",
    },
    {"id": "pico_fome", "label": "Pico de fome", "kind": "max_need", "need": "fome"},
    {"id": "moedas", "label": "Moedas", "kind": "item", "item": "moeda"},
]


def _farm() -> Projection:
    p = Projection()
    p.apply(
        "world",
        ev(
            0,
            0,
            "world.session.started.v1",
            cartridge_version="0.2.0",
            seed=7,
            tick_seconds=60,
            mode="max",
            paused=False,
            scale=72,
            metrics=CATALOG,
        ),
    )
    p.apply("world", ev(1, 0, "world.entity.spawned.v1", entity_id="camps", kind="avatar"))
    for seq, (plot, group) in enumerate((("plot-w-01", "oeste"), ("plot-e-01", "leste")), start=2):
        p.apply(
            "world",
            ev(
                seq,
                0,
                "world.entity.spawned.v1",
                entity_id=plot,
                kind="plot",
                attributes={"group": group},
            ),
        )
    p.apply(
        "world",
        ev(
            4,
            0,
            "world.item.created.v1",
            item="moeda",
            qty=100,
            container_id="camps",
            reason="initial",
        ),
    )
    return p


def test_metricas_do_dia_pelo_catalogo_do_cartucho() -> None:
    """A projeção conta sem saber o que é fazenda: tudo vem do catálogo (ADR-0054)."""
    p = _farm()
    assert p.session is not None
    assert [m["id"] for m in p.session["metrics"]] == [m["id"] for m in CATALOG]
    harvest = {"action": "harvest", "avatar_id": "camps", "action_id": "a", "duration_ticks": 3}
    p.apply("world", ev(5, 100, "action.completed.v1", **harvest, params={"target": "plot-e-01"}))
    p.apply("world", ev(6, 110, "action.completed.v1", **harvest, params={"target": "plot-e-01"}))
    p.apply("world", ev(7, 120, "action.completed.v1", **harvest, params={"target": "plot-w-01"}))
    p.apply(
        "world", ev(8, 130, "action.completed.v1", **(harvest | {"action": "plant"}), params={})
    )
    for seq, reason in enumerate(("busy", "busy", "not_adjacent"), start=9):
        p.apply(
            "world",
            ev(
                seq,
                140,
                "action.rejected.v1",
                avatar_id="camps",
                action="x",
                params={},
                reason=reason,
            ),
        )
    p.apply(
        "agent", ev(0, 150, "world.need.changed.v1", avatar_id="camps", need="fome", value=41.5)
    )
    p.apply(
        "agent", ev(1, 160, "world.need.changed.v1", avatar_id="camps", need="fome", value=38.0)
    )
    p.apply(
        "world",
        ev(
            12,
            170,
            "world.item.consumed.v1",
            item="moeda",
            qty=40,
            container_id="camps",
            reason="buy",
        ),
    )
    assert p.metrics["1"] == {
        "moedas": 60,
        "colheitas": {"leste": 2, "oeste": 1},
        "recusas": {"busy": 2, "not_adjacent": 1},
        "pico_fome": 41.5,
    }
    # Dia 2 começa no tick 1440; só os últimos 8 dias ficam.
    p.apply("world", ev(13, 1440, "avatar.fainted.v1", avatar_id="camps", reason="exhausted"))
    assert p.metrics["2"] == {"desmaios": 1, "moedas": 60}
    for day in range(3, 12):
        p.apply(
            "world",
            ev(
                11 + day,
                (day - 1) * 1440,
                "avatar.fainted.v1",
                avatar_id="camps",
                reason="exhausted",
            ),
        )
    assert sorted(p.metrics, key=int) == [str(d) for d in range(4, 12)]
    assert Projection(json.loads(json.dumps(p.export()))).metrics == p.metrics


def test_metricas_nao_dependem_da_ordem_entre_os_streams() -> None:
    """A fome (stream agent) pode chegar antes do session.started (stream world)."""
    p = Projection()
    p.apply("agent", ev(0, 30, "world.need.changed.v1", avatar_id="camps", need="fome", value=3.65))
    p.apply(
        "world",
        ev(
            0,
            0,
            "world.session.started.v1",
            cartridge_version="0.2.0",
            seed=7,
            tick_seconds=60,
            mode="max",
            paused=False,
            scale=72,
            metrics=CATALOG,
        ),
    )
    p.apply("world", ev(1, 0, "world.entity.spawned.v1", entity_id="camps", kind="avatar"))
    p.apply(
        "world",
        ev(
            2,
            0,
            "world.item.created.v1",
            item="moeda",
            qty=100,
            container_id="camps",
            reason="initial",
        ),
    )
    in_order = _farm()
    in_order.apply(
        "agent", ev(0, 30, "world.need.changed.v1", avatar_id="camps", need="fome", value=3.65)
    )
    assert p.metrics == in_order.metrics == {"1": {"moedas": 100, "pico_fome": 3.65}}


def test_sessao_guarda_o_terreno_e_a_percepcao() -> None:
    """ADR-0056: o terreno e o raio chegam no session.started e ficam na sessão."""
    p = Projection()
    legend = {
        "F": {"kind": "floor", "properties": {"passable": True}},
        "W": {"kind": "wall", "properties": {"passable": False}},
    }
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
            map={"id": "lab", "width": 2, "height": 1, "rows": ["FW"], "legend": legend},
            perception={"radius": None},
        ),
    )
    session = p.session
    assert session is not None
    assert session["map"]["rows"] == ["FW"]
    assert session["map"]["legend"] == legend
    assert (
        "perception" not in session
    )  # raio nulo (o mapa inteiro) é ausência: o estado não carrega null
    p.apply(
        "world",
        ev(
            1,
            0,
            "world.session.started.v1",
            cartridge_version="0.1.0",
            seed=7,
            tick_seconds=60,
            mode="continuous",
            paused=False,
            scale=72,
            map={"id": "lab", "width": 2, "height": 1},
            perception={"radius": 3},
        ),
    )
    assert p.session is not None
    assert p.session["perception"] == {"radius": 3}


def test_o_caderno_do_avatar_vem_dos_eventos_de_memoria() -> None:
    """ADR-0060: anotações, crenças por confiança e a última reflexão, do stream observer."""
    p = started()
    p.apply(
        "observer", ev(10, 100, "memory.noted.v1", avatar_id="camps", day=1, text="o poço é longe")
    )
    p.apply(
        "observer",
        ev(
            11,
            900,
            "memory.belief.formed.v1",
            avatar_id="camps",
            belief_id="bel-0001",
            statement="O quiosque fecha às 18:00.",
            confidence=0.7,
            evidence=["18:23 closed"],
            source={"kind": "observation"},
        ),
    )
    p.apply(
        "observer",
        ev(
            12,
            900,
            "memory.belief.formed.v1",
            avatar_id="camps",
            belief_id="bel-0002",
            statement="Chuva rega.",
            confidence=0.9,
            evidence=[],
            source={"kind": "observation"},
        ),
    )
    p.apply(
        "observer",
        ev(
            13,
            900,
            "memory.reflected.v1",
            avatar_id="camps",
            day=1,
            summary="Plantei.",
            plan="Regar.",
            beliefs={"formed": 2, "updated": 0, "retracted": 0, "total": 2},
        ),
    )
    assert p.memory["camps"] == {
        "notes": [{"tick": 100, "text": "o poço é longe"}],
        "beliefs": [
            {"belief_id": "bel-0002", "statement": "Chuva rega.", "confidence": 0.9},
            {"belief_id": "bel-0001", "statement": "O quiosque fecha às 18:00.", "confidence": 0.7},
        ],
        "day": 1,
        "summary": "Plantei.",
        "plan": "Regar.",
    }
    p.apply(
        "observer",
        ev(
            14,
            2340,
            "memory.belief.updated.v1",
            avatar_id="camps",
            belief_id="bel-0001",
            statement="O quiosque fecha às 18:00: comprar de manhã.",
            confidence={"before": 0.7, "after": 0.95},
            evidence=[],
            source={"kind": "observation"},
        ),
    )
    p.apply(
        "observer",
        ev(
            15,
            2340,
            "memory.belief.retracted.v1",
            avatar_id="camps",
            belief_id="bel-0002",
            statement="Chuva rega.",
        ),
    )
    p.apply(
        "observer",
        ev(
            16,
            2340,
            "memory.reflected.v1",
            avatar_id="camps",
            day=2,
            summary="Choveu.",
            beliefs={"formed": 0, "updated": 1, "retracted": 1, "total": 1},
        ),
    )
    book = p.memory["camps"]
    assert book["beliefs"] == [
        {
            "belief_id": "bel-0001",
            "statement": "O quiosque fecha às 18:00: comprar de manhã.",
            "confidence": 0.95,
        }
    ]
    assert (book["day"], book["summary"]) == (2, "Choveu.")
    assert "plan" not in book  # a reflexão sem plano apaga o de ontem
    again = Projection(json.loads(json.dumps(p.export())))
    assert again.memory == p.memory


def test_lotes_com_validade_seguem_os_itens() -> None:
    """ADR-0062: os eventos de item que trazem `expires_day` formam lotes; a validade na foto é
    a do lote mais antigo, contada do dia corrente; sem `expires_day`, nada de lote."""
    p = started()
    p.apply("world", ev(2, 0, "world.clock.phase_changed.v1", phase="amanhecer", day=1))
    p.apply(
        "world",
        ev(
            3,
            10,
            "world.item.created.v1",
            item="rabanete",
            qty=2,
            container_id="camps",
            reason="harvest",
            expires_day=5,
        ),
    )
    p.apply(
        "world",
        ev(
            4,
            11,
            "world.item.created.v1",
            item="rabanete",
            qty=1,
            container_id="camps",
            reason="harvest",
            expires_day=3,
        ),
    )
    p.apply(
        "world",
        ev(
            5,
            12,
            "world.item.created.v1",
            item="moeda",
            qty=3,
            container_id="camps",
            reason="payment",
        ),
    )
    assert p.containers["camps"] == {"rabanete": 3, "moeda": 3}
    assert p.lots == {"camps": {"rabanete": {"5": 2, "3": 1}}}
    assert (p.expires_in("camps", "rabanete"), p.expires_in("camps", "moeda")) == (2, None)
    assert p.stack("camps", "rabanete", 3) == {"item": "rabanete", "qty": 3, "expires_in_days": 2}
    assert p.stack("camps", "moeda", 3) == {"item": "moeda", "qty": 3}
    p.apply(
        "world",
        ev(
            6,
            20,
            "world.item.transferred.v1",
            item="rabanete",
            qty=1,
            from_container="camps",
            to_container="chest",
            reason="deposit",
            expires_day=3,
        ),
    )
    p.apply(
        "world",
        ev(
            7,
            30,
            "world.item.consumed.v1",
            item="rabanete",
            qty=1,
            container_id="camps",
            reason="eat",
            expires_day=5,
        ),
    )
    assert p.lots == {"camps": {"rabanete": {"5": 1}}, "chest": {"rabanete": {"3": 1}}}
    p.apply("world", ev(8, 1440, "world.clock.phase_changed.v1", phase="amanhecer", day=2))
    assert (p.expires_in("camps", "rabanete"), p.expires_in("chest", "rabanete")) == (3, 1)
    again = Projection(json.loads(json.dumps(p.export())))
    assert again.lots == p.lots


def test_entidade_guardada_sai_do_mapa_e_entra_no_conteiner() -> None:
    """ADR-0062: `entity.stored` troca o contêiner da entidade e apaga a posição."""
    p = started()
    p.apply(
        "world",
        ev(
            2,
            0,
            "world.entity.spawned.v1",
            entity_id="arado",
            kind="plow",
            position={"x": 5, "y": 5},
        ),
    )
    p.apply("world", ev(3, 1, "world.entity.stored.v1", entity_id="arado", to_container="chest"))
    assert p.entities["arado"] == {"kind": "plow", "attributes": {}, "container_id": "chest"}
    p.apply(
        "world",
        ev(
            4,
            2,
            "world.entity.stored.v1",
            entity_id="arado",
            from_container="chest",
            to_container="camps",
        ),
    )
    assert p.entities["arado"]["container_id"] == "camps"


def test_entidade_removida_some_da_projecao() -> None:
    """ADR-0067: `entity.despawned` tira a entidade da vista (o delta a dá como `gone`)."""
    p = started()
    p.apply(
        "world",
        ev(
            2,
            0,
            "world.entity.spawned.v1",
            entity_id="plot-001",
            kind="plot",
            position={"x": 5, "y": 5},
        ),
    )
    assert "plot-001" in p.entities
    p.apply(
        "world",
        ev(3, 1, "world.entity.despawned.v1", entity_id="plot-001", kind="plot", reason="filled"),
    )
    assert "plot-001" not in p.entities


def test_o_delta_separa_o_que_saiu_da_vista_do_que_deixou_de_existir() -> None:
    """ADR-0067: `out_of_view` continua no mundo; `gone` não."""
    base: dict[str, Any] = {"weather": {"condition": "sun"}, "containers": []}
    before: dict[str, Any] = {
        **base,
        "entities": [{"entity_id": "plot-001"}, {"entity_id": "plot-002"}],
    }
    after: dict[str, Any] = {**base, "entities": []}
    assert diff_views(before, after) == {"gone": ["plot-001", "plot-002"]}
    split = diff_views(before, after, lambda entity_id: entity_id == "plot-002")
    assert split == {"gone": ["plot-001"], "out_of_view": ["plot-002"]}


def test_a_metrica_com_campo_soma_em_vez_de_contar() -> None:
    """ADR-0069: um `count` com `field` soma o campo: as moedas recebidas por canal."""
    p = Projection()
    coins = {
        "id": "moedas_por_canal",
        "label": "Moedas recebidas por canal",
        "kind": "count",
        "event": "campsverso.world.item.created.v1",
        "where": {"item": "moeda"},
        "by": {"field": "reason"},
        "field": "qty",
    }
    p.apply(
        "world",
        ev(
            0,
            0,
            "world.session.started.v1",
            cartridge_version="0.2.0",
            seed=7,
            tick_seconds=60,
            mode="max",
            paused=False,
            scale=72,
            metrics=[coins],
        ),
    )
    for seq, (qty, reason) in enumerate(
        (
            (100, "initial"),
            (60, "payment"),
            (270, "order_payment"),
            (80, "fair_payment"),
            (40, "payment"),
        ),
        start=1,
    ):
        p.apply(
            "world",
            ev(
                seq,
                10 * seq,
                "world.item.created.v1",
                item="moeda",
                qty=qty,
                container_id="camps",
                reason=reason,
            ),
        )
    p.apply(
        "world",
        ev(
            9,
            99,
            "world.item.created.v1",
            item="milho",
            qty=3,
            container_id="camps",
            reason="harvest",
        ),
    )
    assert p.metrics["1"]["moedas_por_canal"] == {
        "initial": 100,
        "payment": 100,
        "order_payment": 270,
        "fair_payment": 80,
    }


def test_o_avatar_que_entra_e_sai_ganha_e_perde_a_posicao() -> None:
    """ADR-0072: o ajudante declarado fora do mundo aparece ao entrar e some ao sair."""
    p = started()
    p.apply("world", ev(2, 0, "world.entity.spawned.v1", entity_id="dita", kind="avatar"))
    assert "position" not in p.entities["dita"]
    p.apply(
        "world",
        ev(3, 60, "avatar.entered.v1", avatar_id="dita", position={"x": 33, "y": 38}, reason="dia"),
    )
    assert p.entities["dita"]["position"] == {"x": 33, "y": 38}
    p.apply("world", ev(4, 700, "avatar.left.v1", avatar_id="dita", reason="end_of_day"))
    assert "position" not in p.entities["dita"]
    assert "dita" not in p.motion
