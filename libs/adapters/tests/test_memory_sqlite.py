"""A memória em SQLite (ADR-0060): registrar, lembrar, refletir, e sobreviver a um reinício."""

import sqlite3
from dataclasses import replace
from pathlib import Path

from campsverso_adapters import SqliteMemory
from campsverso_ports import (
    BeliefRevision,
    Episode,
    Experiment,
    Meal,
    Note,
    Place,
    Planting,
    Reflection,
    Tile,
)


def episode(tick: int, text: str, importance: int, day: int = 1, kind: str = "x") -> Episode:
    return Episode(
        tick, day, text, importance, kind, ("camps",), f"2026-10-10T06:{tick:02d}:00-03:00"
    )


def reflection(day: int, *beliefs: BeliefRevision, tick: int = 900) -> Reflection:
    return Reflection(day, tick, f"resumo do dia {day}", "plano", tuple(beliefs), "ab" * 32)


def test_registra_e_lembra_episodios_e_anotacoes() -> None:
    memory = SqliteMemory(":memory:")
    memory.record(episode(1, "acordei", 2))
    memory.record(episode(5, "plantei", 3))
    memory.record(episode(1500, "colhi", 7, day=2))
    memory.note(Note(10, 1, "o poço fica longe"))
    assert [e.text for e in memory.episodes(1)] == ["acordei", "plantei"]
    assert [e.text for e in memory.episodes(1, limit=1)] == ["plantei"]
    assert [e.text for e in memory.episodes(2)] == ["colhi"]
    assert memory.episodes(3) == []
    (note,) = memory.notes(1)
    assert (note.tick, note.text) == (10, "o poço fica longe")
    assert memory.notes(2) == []
    assert memory.episodes(1)[0].tags == ("camps",)


def test_marcantes_por_importancia_e_recencia() -> None:
    memory = SqliteMemory(":memory:")
    memory.record(episode(0, "andei", 1))
    memory.record(episode(10, "desmaiei", 10))
    memory.record(episode(600, "esperei", 1))
    memory.record(episode(700, "colhi", 7))
    memory.record(episode(710, "andei de novo", 1))
    chosen = memory.salient(1, now_tick=720, limit=2)
    assert [e.text for e in chosen] == ["desmaiei", "colhi"]  # na ordem do dia, não do score
    assert [e.text for e in memory.salient(1, now_tick=720, limit=10)] == [
        "andei",
        "desmaiei",
        "esperei",
        "colhi",
        "andei de novo",
    ]


def test_a_reflexao_forma_atualiza_e_retira_crencas() -> None:
    memory = SqliteMemory(":memory:")
    assert memory.beliefs() == []
    assert memory.last_reflection() is None
    changes = memory.save_reflection(
        reflection(
            1,
            BeliefRevision("O quiosque fecha às 18:00.", 0.7, ("tick 743: closed",), "new"),
            BeliefRevision("A chuva não rega.", 0.4, (), "new", reason="palpite"),
            BeliefRevision("fantasma", 0.9, (), "retracted", belief_id="bel-9999"),  # não existia
        )
    )
    assert [(c.kind, c.belief.belief_id) for c in changes] == [
        ("formed", "bel-0001"),
        ("formed", "bel-0002"),
    ]
    assert [b.belief_id for b in memory.beliefs()] == ["bel-0001", "bel-0002"]  # por confiança
    assert memory.has_reflection(1)
    assert not memory.has_reflection(2)
    assert memory.last_reflection() is not None
    assert memory.last_reflection().summary == "resumo do dia 1"  # type: ignore[union-attr]

    changes = memory.save_reflection(
        reflection(
            2,
            BeliefRevision(
                "O quiosque fecha às 18:00.", 0.95, ("tick 743",), "confirmed", belief_id="bel-0001"
            ),
            BeliefRevision("A chuva não rega.", 0.4, (), "retracted", "choveu e regou", "bel-0002"),
            BeliefRevision("O leste amadurece antes.", 0.55, ("tick 1500",), "new"),
            BeliefRevision(
                "O leste amadurece antes.", 0.55, (), "retracted"
            ),  # novo e retirado: nada
        )
    )
    assert [(c.kind, c.belief.belief_id, c.previous_confidence) for c in changes] == [
        ("updated", "bel-0001", 0.7),
        ("retracted", "bel-0002", 0.4),
        ("formed", "bel-0003", None),
    ]
    alive = memory.beliefs()
    assert [(b.belief_id, b.confidence, b.last_day) for b in alive] == [
        ("bel-0001", 0.95, 2),
        ("bel-0003", 0.55, 2),
    ]
    assert alive[0].first_day == 1
    assert alive[0].evidence == ("tick 743",)
    # Confirmar com a mesma confiança não muda nada; retirar o já retirado também não.
    again = memory.save_reflection(
        reflection(
            3,
            BeliefRevision(
                "O quiosque fecha às 18:00.", 0.95, (), "confirmed", belief_id="bel-0001"
            ),
            BeliefRevision("A chuva não rega.", 0.4, (), "retracted", belief_id="bel-0002"),
        )
    )
    assert again == []
    assert memory.last_reflection().day == 3  # type: ignore[union-attr]


def test_a_memoria_sobrevive_a_um_reinicio(tmp_path: Path) -> None:
    path = tmp_path / "memory" / "camps.sqlite"
    memory = SqliteMemory(path)
    memory.record(episode(5, "plantei", 3))
    memory.note(Note(10, 1, "anotação"))
    memory.save_reflection(reflection(1, BeliefRevision("crença", 0.6, ("tick 5",), "new")))
    memory.close()

    reopened = SqliteMemory(path)
    assert [b.statement for b in reopened.beliefs()] == ["crença"]
    assert reopened.last_reflection() is not None
    assert reopened.last_reflection().plan == "plano"  # type: ignore[union-attr]
    assert [n.text for n in reopened.notes(1)] == ["anotação"]
    assert [e.text for e in reopened.episodes(1)] == ["plantei"]
    changes = reopened.save_reflection(reflection(2, BeliefRevision("outra", 0.3, (), "new")))
    assert changes[0].belief.belief_id == "bel-0002"  # os ids continuam de onde pararam


def test_lugares_lembrados_e_esquecidos_sobrevivem_a_um_reinicio(tmp_path: Path) -> None:
    """ADR-0067: o último estado visto de cada coisa, o mais recente primeiro."""
    path = tmp_path / "camps.sqlite"
    memory = SqliteMemory(path)
    memory.remember([Place("plot-001", "plot", 3, 4, (("crop", '"milho"'),), 100, 1)])
    memory.remember([Place("kiosk", "kiosk", 30, 36, (), 200, 1)])
    memory.remember([Place("plot-001", "plot", 3, 4, (("crop", "null"),), 300, 2)])
    assert [(p.entity_id, p.tick) for p in memory.places()] == [("plot-001", 300), ("kiosk", 200)]
    memory.forget(["kiosk"])
    memory.close()
    reopened = SqliteMemory(path)
    (place,) = reopened.places()
    assert (place.entity_id, place.x, place.y, place.attributes) == (
        "plot-001",
        3,
        4,
        (("crop", "null"),),
    )


def test_o_caderno_de_campo_volta_ao_reabrir(tmp_path: Path) -> None:
    # Os plantios, as refeições e os experimentos (ADR-0070), num arquivo que um processo reabre.
    path = tmp_path / "camps.sqlite"
    memory = SqliteMemory(path)
    planting = Planting("plot-001", 130, 1, "rabanete", 3, 3)
    memory.save_planting(planting)
    memory.save_planting(replace(planting, watered_days=(1, 2), matured_day=3, outcome="colhida"))
    memory.save_planting(Planting("plot-001", 2900, 3, "milho", 3, 3, previous="rabanete"))
    memory.eat(Meal(110, 1, "rabanete", 70.0, 45.0))
    memory.save_experiment(Experiment(1, "h", "t", "p"))
    memory.save_experiment(Experiment(1, "h", "t", "p", result="cumpriu", result_day=2))
    memory.close()
    reopened = SqliteMemory(path)
    first, second = reopened.plantings()
    assert (first.watered_days, first.outcome, second.previous) == ((1, 2), "colhida", "rabanete")
    assert reopened.meals() == [Meal(110, 1, "rabanete", 70.0, 45.0)]
    assert reopened.experiments() == [Experiment(1, "h", "t", "p", "cumpriu", 2)]


def test_o_terreno_visto_e_a_estacao_do_plantio(tmp_path: Path) -> None:
    """ADR-0074: o terreno que a comparação mede, por cima do que havia em cada tile; e uma
    memória de antes da estação no plantio ganha as colunas ao reabrir (o sandbox retomado)."""
    memory = SqliteMemory(":memory:")
    memory.see([Tile(3, 1, "river"), Tile(0, 2, "tree")])
    memory.see([Tile(3, 1, "river"), Tile(1, 0, "path")])
    assert memory.terrain() == [Tile(1, 0, "path"), Tile(3, 1, "river"), Tile(0, 2, "tree")]
    path = tmp_path / "antiga.sqlite"
    old = sqlite3.connect(path)
    old.execute(
        "CREATE TABLE plantings (plot_id TEXT NOT NULL, tick INTEGER NOT NULL, day INTEGER NOT"
        " NULL, crop TEXT NOT NULL, x INTEGER, y INTEGER, previous TEXT, fertilized INTEGER NOT"
        " NULL, watered_days TEXT NOT NULL, matured_day INTEGER, outcome TEXT, outcome_day"
        " INTEGER, PRIMARY KEY (plot_id, tick))"
    )
    old.execute(
        "INSERT INTO plantings VALUES ('plot-1', 5, 1, 'milho', 1, 1, NULL, 0, '[]',"
        " NULL, NULL, NULL)"
    )
    old.commit()
    old.close()
    reopened = SqliteMemory(path)
    (before,) = reopened.plantings()
    assert (before.crop, before.season) == ("milho", None)
    reopened.save_planting(replace(before, season="verão", matured_season="outono"))
    (after,) = reopened.plantings()
    assert (after.season, after.matured_season) == ("verão", "outono")
