"""A memória em SQLite (ADR-0060): registrar, lembrar, refletir, e sobreviver a um reinício."""

from pathlib import Path

from campsverso_adapters import SqliteMemory
from campsverso_ports import BeliefRevision, Episode, Note, Reflection


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
