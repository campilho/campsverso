"""A memória de um avatar em SQLite (ADR-0060): um arquivo por avatar e por mundo, fora do
snapshot do mundo, que um processo novo reabre e um supervisor copia. `:memory:` nos testes.

Determinismo: os ids das crenças são sequenciais (`bel-0001`), as listas saem ordenadas, e a
diferença de uma reflexão é função só do que estava guardado e do que a reflexão disse.
"""

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, cast

from campsverso_ports import (
    Belief,
    BeliefChange,
    BeliefRevision,
    Episode,
    Experiment,
    Meal,
    Note,
    Place,
    Planting,
    Reflection,
    SourceKind,
    Tile,
)

DECAY_PER_HOUR = 0.9  # a recência do memory stream: a cada hora, 10% a menos

_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
  id INTEGER PRIMARY KEY, tick INTEGER NOT NULL, day INTEGER NOT NULL, sim_time TEXT NOT NULL,
  kind TEXT NOT NULL, text TEXT NOT NULL, importance INTEGER NOT NULL, tags TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS episodes_day ON episodes (day, id);
CREATE TABLE IF NOT EXISTS notes (
  id INTEGER PRIMARY KEY, tick INTEGER NOT NULL, day INTEGER NOT NULL, sim_time TEXT NOT NULL,
  text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_day ON notes (day, id);
CREATE TABLE IF NOT EXISTS beliefs (
  belief_id TEXT PRIMARY KEY, seq INTEGER NOT NULL, statement TEXT NOT NULL,
  confidence REAL NOT NULL, evidence TEXT NOT NULL, source_kind TEXT NOT NULL, source_by TEXT,
  reason TEXT, first_day INTEGER NOT NULL, last_day INTEGER NOT NULL,
  retracted INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS places (
  entity_id TEXT PRIMARY KEY, kind TEXT NOT NULL, x INTEGER NOT NULL, y INTEGER NOT NULL,
  attributes TEXT NOT NULL, tick INTEGER NOT NULL, day INTEGER NOT NULL, sim_time TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reflections (
  day INTEGER PRIMARY KEY, tick INTEGER NOT NULL, summary TEXT NOT NULL, plan TEXT,
  beliefs TEXT NOT NULL, prompt_sha256 TEXT
);
CREATE TABLE IF NOT EXISTS plantings (
  plot_id TEXT NOT NULL, tick INTEGER NOT NULL, day INTEGER NOT NULL, crop TEXT NOT NULL,
  x INTEGER, y INTEGER, previous TEXT, fertilized INTEGER NOT NULL, watered_days TEXT NOT NULL,
  matured_day INTEGER, outcome TEXT, outcome_day INTEGER, season TEXT, matured_season TEXT,
  PRIMARY KEY (plot_id, tick)
);
CREATE TABLE IF NOT EXISTS terrain (
  x INTEGER NOT NULL, y INTEGER NOT NULL, kind TEXT NOT NULL, PRIMARY KEY (y, x)
);
CREATE TABLE IF NOT EXISTS meals (
  id INTEGER PRIMARY KEY, tick INTEGER NOT NULL, day INTEGER NOT NULL, item TEXT NOT NULL,
  hunger_before REAL NOT NULL, hunger_after REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS experiments (
  day INTEGER PRIMARY KEY, hypothesis TEXT NOT NULL, test TEXT NOT NULL, prediction TEXT NOT NULL,
  result TEXT, result_day INTEGER
);
"""
# As colunas que chegaram depois da tabela: uma memória antiga (um sandbox retomado) as ganha.
_ADDED = {"plantings": ("season TEXT", "matured_season TEXT")}


def _belief(row: sqlite3.Row) -> Belief:
    return Belief(
        belief_id=str(row["belief_id"]),
        statement=str(row["statement"]),
        confidence=float(row["confidence"]),
        evidence=tuple(cast(list[str], json.loads(str(row["evidence"])))),
        source_kind=cast(SourceKind, str(row["source_kind"])),
        source_by=cast(str | None, row["source_by"]),
        reason=cast(str | None, row["reason"]),
        first_day=int(row["first_day"]),
        last_day=int(row["last_day"]),
        retracted=bool(row["retracted"]),
    )


class SqliteMemory:
    def __init__(self, path: Path | str) -> None:
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path))
        self._db.row_factory = sqlite3.Row
        self._db.executescript(_SCHEMA)
        for table, columns in _ADDED.items():
            have = {str(r["name"]) for r in self._db.execute(f"PRAGMA table_info({table})")}
            for column in columns:
                if column.split()[0] not in have:
                    self._db.execute(f"ALTER TABLE {table} ADD COLUMN {column}")
        self._db.commit()

    # ------------------------------------------------------------- registrar

    def record(self, episode: Episode) -> None:
        self._db.execute(
            "INSERT INTO episodes (tick, day, sim_time, kind, text, importance, tags)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                episode.tick,
                episode.day,
                episode.sim_time,
                episode.kind,
                episode.text,
                episode.importance,
                json.dumps(list(episode.tags)),
            ),
        )
        self._db.commit()

    def note(self, note: Note) -> None:
        self._db.execute(
            "INSERT INTO notes (tick, day, sim_time, text) VALUES (?, ?, ?, ?)",
            (note.tick, note.day, note.sim_time, note.text),
        )
        self._db.commit()

    # ------------------------------------------------------------- lembrar

    def episodes(self, day: int, *, limit: int | None = None) -> list[Episode]:
        rows = self._db.execute(
            "SELECT * FROM episodes WHERE day = ? ORDER BY id", (day,)
        ).fetchall()
        if limit is not None:
            rows = rows[-limit:]
        return [self._episode(r) for r in rows]

    @staticmethod
    def _episode(row: sqlite3.Row) -> Episode:
        return Episode(
            tick=int(row["tick"]),
            day=int(row["day"]),
            text=str(row["text"]),
            importance=int(row["importance"]),
            kind=str(row["kind"]),
            tags=tuple(cast(list[str], json.loads(str(row["tags"])))),
            sim_time=str(row["sim_time"]),
        )

    def notes(self, day: int) -> list[Note]:
        rows = self._db.execute("SELECT * FROM notes WHERE day = ? ORDER BY id", (day,)).fetchall()
        return [
            Note(int(r["tick"]), int(r["day"]), str(r["text"]), str(r["sim_time"])) for r in rows
        ]

    def beliefs(self) -> list[Belief]:
        rows = self._db.execute(
            "SELECT * FROM beliefs WHERE retracted = 0 ORDER BY confidence DESC, belief_id"
        ).fetchall()
        return [_belief(r) for r in rows]

    def last_reflection(self) -> Reflection | None:
        row = self._db.execute("SELECT * FROM reflections ORDER BY day DESC LIMIT 1").fetchone()
        return None if row is None else self._reflection(row)

    def has_reflection(self, day: int) -> bool:
        return (
            self._db.execute("SELECT 1 FROM reflections WHERE day = ?", (day,)).fetchone()
            is not None
        )

    @staticmethod
    def _reflection(row: sqlite3.Row) -> Reflection:
        raw = cast(list[dict[str, Any]], json.loads(str(row["beliefs"])))
        return Reflection(
            day=int(row["day"]),
            tick=int(row["tick"]),
            summary=str(row["summary"]),
            plan=cast(str | None, row["plan"]),
            beliefs=tuple(
                BeliefRevision(
                    statement=str(b["statement"]),
                    confidence=float(b["confidence"]),
                    evidence=tuple(cast(list[str], b.get("evidence") or [])),
                    status=b["status"],
                    reason=cast(str | None, b.get("reason")),
                    belief_id=cast(str | None, b.get("belief_id")),
                )
                for b in raw
            ),
            prompt_sha256=cast(str | None, row["prompt_sha256"]),
        )

    def salient(self, day: int, *, now_tick: int, limit: int) -> list[Episode]:
        """Importância vezes 0,9 por hora passada; empate pelo mais recente, depois pela ordem."""
        episodes = self.episodes(day)
        scored = sorted(
            enumerate(episodes),
            key=lambda pair: (
                -pair[1].importance * DECAY_PER_HOUR ** (max(0, now_tick - pair[1].tick) / 60),
                -pair[1].tick,
                -pair[0],
            ),
        )
        chosen = sorted(scored[:limit], key=lambda pair: pair[0])
        return [episode for _, episode in chosen]

    # ------------------------------------------------------------- refletir

    def save_reflection(self, reflection: Reflection) -> Sequence[BeliefChange]:
        known = {
            b.belief_id: b for b in (_belief(r) for r in self._db.execute("SELECT * FROM beliefs"))
        }
        next_seq = 1 + max(
            (int(r[0]) for r in self._db.execute("SELECT seq FROM beliefs")), default=0
        )
        changes: list[BeliefChange] = []
        for revision in reflection.beliefs:
            current = known.get(revision.belief_id or "")
            if current is None:
                if revision.status == "retracted":
                    continue  # retirar o que não existia não é nada
                belief = Belief(
                    belief_id=f"bel-{next_seq:04d}",
                    statement=revision.statement,
                    confidence=revision.confidence,
                    evidence=revision.evidence,
                    reason=revision.reason,
                    first_day=reflection.day,
                    last_day=reflection.day,
                )
                self._insert(belief, next_seq)
                next_seq += 1
                known[belief.belief_id] = belief
                changes.append(BeliefChange("formed", belief))
                continue
            if revision.status == "retracted":
                if current.retracted:
                    continue
                belief = replace(
                    current,
                    retracted=True,
                    last_day=reflection.day,
                    reason=revision.reason or current.reason,
                )
                self._update(belief)
                known[belief.belief_id] = belief
                changes.append(BeliefChange("retracted", belief, current.confidence))
                continue
            moved = (
                abs(current.confidence - revision.confidence) > 1e-9
                or current.statement != revision.statement
                or current.retracted
            )
            if not moved:
                continue
            belief = Belief(
                belief_id=current.belief_id,
                statement=revision.statement,
                confidence=revision.confidence,
                evidence=revision.evidence or current.evidence,
                source_kind=current.source_kind,
                source_by=current.source_by,
                reason=revision.reason or current.reason,
                first_day=current.first_day,
                last_day=reflection.day,
                retracted=False,
            )
            self._update(belief)
            known[belief.belief_id] = belief
            changes.append(BeliefChange("updated", belief, current.confidence))
        self._db.execute(
            "INSERT OR REPLACE INTO reflections (day, tick, summary, plan, beliefs, prompt_sha256)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                reflection.day,
                reflection.tick,
                reflection.summary,
                reflection.plan,
                json.dumps([asdict(b) for b in reflection.beliefs], ensure_ascii=False),
                reflection.prompt_sha256,
            ),
        )
        self._db.commit()
        return changes

    def _insert(self, belief: Belief, seq: int) -> None:
        self._db.execute(
            "INSERT INTO beliefs (belief_id, seq, statement, confidence, evidence, source_kind,"
            " source_by, reason, first_day, last_day, retracted)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
            (
                belief.belief_id,
                seq,
                belief.statement,
                belief.confidence,
                json.dumps(list(belief.evidence), ensure_ascii=False),
                belief.source_kind,
                belief.source_by,
                belief.reason,
                belief.first_day,
                belief.last_day,
            ),
        )

    def _update(self, belief: Belief) -> None:
        self._db.execute(
            "UPDATE beliefs SET statement = ?, confidence = ?, evidence = ?, reason = ?,"
            " last_day = ?, retracted = ? WHERE belief_id = ?",
            (
                belief.statement,
                belief.confidence,
                json.dumps(list(belief.evidence), ensure_ascii=False),
                belief.reason,
                belief.last_day,
                int(belief.retracted),
                belief.belief_id,
            ),
        )

    # ------------------------------------------------------------- lugares (ADR-0067)

    def places(self) -> list[Place]:
        rows = self._db.execute("SELECT * FROM places ORDER BY tick DESC, entity_id").fetchall()
        return [
            Place(
                entity_id=str(r["entity_id"]),
                kind=str(r["kind"]),
                x=int(r["x"]),
                y=int(r["y"]),
                attributes=tuple(
                    (str(k), str(v)) for k, v in cast(list[list[str]], json.loads(r["attributes"]))
                ),
                tick=int(r["tick"]),
                day=int(r["day"]),
                sim_time=str(r["sim_time"]),
            )
            for r in rows
        ]

    def remember(self, places: Sequence[Place]) -> None:
        self._db.executemany(
            "INSERT OR REPLACE INTO places (entity_id, kind, x, y, attributes, tick, day, sim_time)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    p.entity_id,
                    p.kind,
                    p.x,
                    p.y,
                    json.dumps([list(pair) for pair in p.attributes], ensure_ascii=False),
                    p.tick,
                    p.day,
                    p.sim_time,
                )
                for p in places
            ],
        )
        self._db.commit()

    def forget(self, entity_ids: Sequence[str]) -> None:
        self._db.executemany("DELETE FROM places WHERE entity_id = ?", [(i,) for i in entity_ids])
        self._db.commit()

    # ------------------------------------------------------------- o terreno (ADR-0074)

    def see(self, tiles: Sequence[Tile]) -> None:
        self._db.executemany(
            "INSERT OR REPLACE INTO terrain (x, y, kind) VALUES (?, ?, ?)",
            [(t.x, t.y, t.kind) for t in tiles],
        )
        self._db.commit()

    def terrain(self) -> list[Tile]:
        rows = self._db.execute("SELECT x, y, kind FROM terrain ORDER BY y, x")
        return [Tile(int(r["x"]), int(r["y"]), str(r["kind"])) for r in rows]

    # ------------------------------------------------------------- o caderno de campo (ADR-0070)

    def save_planting(self, planting: Planting) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO plantings (plot_id, tick, day, crop, x, y, previous,"
            " fertilized, watered_days, matured_day, outcome, outcome_day, season,"
            " matured_season) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                planting.plot_id,
                planting.tick,
                planting.day,
                planting.crop,
                planting.x,
                planting.y,
                planting.previous,
                int(planting.fertilized),
                json.dumps(list(planting.watered_days)),
                planting.matured_day,
                planting.outcome,
                planting.outcome_day,
                planting.season,
                planting.matured_season,
            ),
        )
        self._db.commit()

    def plantings(self) -> list[Planting]:
        rows = self._db.execute("SELECT * FROM plantings ORDER BY tick, plot_id")
        return [
            Planting(
                plot_id=str(r["plot_id"]),
                tick=int(r["tick"]),
                day=int(r["day"]),
                crop=str(r["crop"]),
                x=cast(int | None, r["x"]),
                y=cast(int | None, r["y"]),
                previous=cast(str | None, r["previous"]),
                fertilized=bool(r["fertilized"]),
                watered_days=tuple(cast(list[int], json.loads(str(r["watered_days"])))),
                matured_day=cast(int | None, r["matured_day"]),
                outcome=cast(str | None, r["outcome"]),
                outcome_day=cast(int | None, r["outcome_day"]),
                season=cast(str | None, r["season"]),
                matured_season=cast(str | None, r["matured_season"]),
            )
            for r in rows
        ]

    def eat(self, meal: Meal) -> None:
        self._db.execute(
            "INSERT INTO meals (tick, day, item, hunger_before, hunger_after)"
            " VALUES (?, ?, ?, ?, ?)",
            (meal.tick, meal.day, meal.item, meal.hunger_before, meal.hunger_after),
        )
        self._db.commit()

    def meals(self) -> list[Meal]:
        rows = self._db.execute("SELECT * FROM meals ORDER BY tick, id")
        return [
            Meal(
                int(r["tick"]),
                int(r["day"]),
                str(r["item"]),
                float(r["hunger_before"]),
                float(r["hunger_after"]),
            )
            for r in rows
        ]

    def save_experiment(self, experiment: Experiment) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO experiments VALUES (?, ?, ?, ?, ?, ?)",
            (
                experiment.day,
                experiment.hypothesis,
                experiment.test,
                experiment.prediction,
                experiment.result,
                experiment.result_day,
            ),
        )
        self._db.commit()

    def experiments(self) -> list[Experiment]:
        rows = self._db.execute("SELECT * FROM experiments ORDER BY day")
        return [
            Experiment(
                int(r["day"]),
                str(r["hypothesis"]),
                str(r["test"]),
                str(r["prediction"]),
                cast(str | None, r["result"]),
                cast(int | None, r["result_day"]),
            )
            for r in rows
        ]

    def close(self) -> None:
        self._db.close()
