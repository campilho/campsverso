"""O que o supervisor lembra entre uma volta e outra, e o diário da troca (ADR-0083).

**O estado** (`estado.json`): qual das duas worktrees está viva, o commit que ela roda, os commits
recusados e a troca em andamento. Ele vai para o disco antes de cada passo que mexe em algo: se o
supervisor cai no meio de uma troca, ao subir de novo ele acha a troca anotada e volta.

**O diário** (`versoes/supervisor.jsonl`): cada passo numa linha, com a hora, o commit, o
resultado e o tempo. É dele que saem os números do auto-update: quanto tempo o escritório ficou
fora do ar em cada troca, quantas deram certo e quantas voltaram.
"""

import json
import os
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, cast

SLOTS = ("a", "b")


@dataclass
class Swap:
    """Uma troca em andamento: de onde, para onde e a cópia dos dados para a volta."""

    from_slot: str
    from_commit: str
    to_slot: str
    to_commit: str
    backup: str


@dataclass
class State:
    live: str = "a"
    commit: str | None = None
    rejected: list[str] = field(default_factory=list[str])
    swap: Swap | None = None

    @property
    def other(self) -> str:
        return SLOTS[1 - SLOTS.index(self.live)]

    @classmethod
    def load(cls, path: Path) -> State:
        if not path.is_file():
            return cls()
        raw = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
        swap = raw.get("swap")
        return cls(
            live=str(raw["live"]),
            commit=None if raw.get("commit") is None else str(raw["commit"]),
            rejected=[str(c) for c in cast(list[Any], raw.get("rejected") or [])],
            swap=None if swap is None else Swap(**cast(dict[str, str], swap)),
        )

    def save(self, path: Path) -> None:
        """Grava inteiro ou não grava: um arquivo novo, trocado de nome por cima do antigo."""
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        with temp.open("rb") as handle:
            os.fsync(handle.fileno())
        temp.replace(path)


class Journal:
    def __init__(self, path: Path, now: Callable[[], datetime]) -> None:
        self._path = path
        self._now = now

    def write(self, step: str, **fields: Any) -> dict[str, Any]:
        entry = {"at": self._now().isoformat(timespec="seconds"), "step": step, **fields}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def entries(self) -> list[dict[str, Any]]:
        if not self._path.is_file():
            return []
        lines = self._path.read_text(encoding="utf-8").splitlines()
        return [cast(dict[str, Any], json.loads(line)) for line in lines if line.strip()]
