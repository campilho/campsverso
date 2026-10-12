"""WorldStore em SQLite: outbox, diário de entradas e índice de snapshots (plano do M2 §1).

Modo WAL com `synchronous=NORMAL`: cada transação sobrevive à queda do processo (kill -9);
só uma queda de energia pode perder as últimas.
"""

import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from campsverso_ports import (
    Commit,
    Envelope,
    InputKind,
    InputRow,
    OutboxRow,
    SnapshotRef,
    StoreState,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS inputs (
  position INTEGER PRIMARY KEY,
  tick INTEGER NOT NULL,
  kind TEXT NOT NULL,
  command_id TEXT UNIQUE,
  envelope TEXT
);
CREATE TABLE IF NOT EXISTS outbox (
  seq INTEGER PRIMARY KEY,
  id TEXT NOT NULL UNIQUE,
  subject TEXT NOT NULL,
  envelope TEXT NOT NULL,
  published INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS outbox_pending ON outbox (seq) WHERE published = 0;
CREATE TABLE IF NOT EXISTS snapshots (
  ref TEXT PRIMARY KEY,
  tick INTEGER NOT NULL,
  sha256 TEXT NOT NULL,
  next_seq INTEGER NOT NULL,
  next_input INTEGER NOT NULL,
  version TEXT NOT NULL
);
"""


def _dumps(envelope: Envelope) -> str:
    return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))


def _loads(text: str) -> Envelope:
    return cast(dict[str, Any], json.loads(text))


class SqliteWorldStore:
    def __init__(self, path: Path | str) -> None:
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")
        self._db.executescript(SCHEMA)

    def commit(self, commit: Commit) -> None:
        db = self._db
        db.execute("BEGIN IMMEDIATE")
        try:
            db.executemany(
                "INSERT INTO inputs (position, tick, kind, command_id, envelope)"
                " VALUES (?,?,?,?,?)",
                [
                    (
                        i.position,
                        i.tick,
                        i.kind,
                        i.command_id,
                        None if i.envelope is None else _dumps(i.envelope),
                    )
                    for i in commit.inputs
                ],
            )
            db.executemany(
                "INSERT INTO outbox (seq, id, subject, envelope) VALUES (?,?,?,?)",
                [
                    (r.seq, str(r.envelope["id"]), r.subject, _dumps(r.envelope))
                    for r in commit.outbox
                ],
            )
            if commit.snapshot is not None:
                s = commit.snapshot
                db.execute(
                    "INSERT OR REPLACE INTO snapshots VALUES (?,?,?,?,?,?)",
                    (s.ref, s.tick, s.sha256, s.next_seq, s.next_input, s.version),
                )
            db.executemany(
                "INSERT OR REPLACE INTO meta VALUES (?,?)",
                [("tick", str(commit.tick)), ("version", commit.version)],
            )
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise

    def state(self) -> StoreState | None:
        meta = dict(self._db.execute("SELECT key, value FROM meta").fetchall())
        if "tick" not in meta:
            return None
        (max_seq,) = self._db.execute("SELECT MAX(seq) FROM outbox").fetchone()
        (max_input,) = self._db.execute("SELECT MAX(position) FROM inputs").fetchone()
        latest = self.snapshots()[-1:] or None
        floor_seq = latest[0].next_seq if latest else 0
        return StoreState(
            tick=int(meta["tick"]),
            version=str(meta["version"]),
            next_seq=max(floor_seq, 0 if max_seq is None else int(max_seq) + 1),
            next_input=1 if max_input is None else int(max_input) + 1,
        )

    def snapshots(self) -> Sequence[SnapshotRef]:
        rows = self._db.execute(
            "SELECT ref, tick, sha256, next_seq, next_input, version FROM snapshots"
            " ORDER BY next_seq"
        ).fetchall()
        return [SnapshotRef(*row) for row in rows]

    def forget_snapshot(self, ref: str) -> None:
        self._db.execute("DELETE FROM snapshots WHERE ref = ?", (ref,))

    def prune_outbox(self, before_seq: int) -> None:
        self._db.execute("DELETE FROM outbox WHERE published = 1 AND seq < ?", (before_seq,))

    def inputs_from(self, position: int) -> Sequence[InputRow]:
        rows = self._db.execute(
            "SELECT position, tick, kind, command_id, envelope FROM inputs"
            " WHERE position >= ? ORDER BY position",
            (position,),
        ).fetchall()
        return [
            InputRow(
                position=row[0],
                tick=row[1],
                kind=cast(InputKind, row[2]),
                command_id=row[3],
                envelope=None if row[4] is None else _loads(row[4]),
            )
            for row in rows
        ]

    def has_command(self, command_id: str) -> bool:
        found = self._db.execute(
            "SELECT 1 FROM inputs WHERE command_id = ?", (command_id,)
        ).fetchone()
        return found is not None

    def _rows(self, query: str, *args: object) -> Sequence[OutboxRow]:
        return [
            OutboxRow(seq, subject, _loads(envelope))
            for seq, subject, envelope in self._db.execute(query, args).fetchall()
        ]

    def outbox_from(self, seq: int) -> Sequence[OutboxRow]:
        return self._rows(
            "SELECT seq, subject, envelope FROM outbox WHERE seq >= ? ORDER BY seq", seq
        )

    def unpublished(self, limit: int) -> Sequence[OutboxRow]:
        return self._rows(
            "SELECT seq, subject, envelope FROM outbox WHERE published = 0 ORDER BY seq LIMIT ?",
            limit,
        )

    def mark_published(self, up_to_seq: int) -> None:
        self._db.execute(
            "UPDATE outbox SET published = 1 WHERE published = 0 AND seq <= ?", (up_to_seq,)
        )

    def recent_ids(self, limit: int) -> Sequence[tuple[int, str]]:
        rows = self._db.execute(
            "SELECT seq, id FROM outbox ORDER BY seq DESC LIMIT ?", (limit,)
        ).fetchall()
        return [(int(seq), str(event_id)) for seq, event_id in reversed(rows)]

    def close(self) -> None:
        self._db.close()
