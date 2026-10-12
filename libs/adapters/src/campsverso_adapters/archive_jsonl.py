"""EventArchive em JSONL: um arquivo por mundo e por data simulada, só acrescentando (ADR-0043).

`data/archive/<mundo>/<AAAA-MM-DD>.jsonl`, pela data do `simtime` do envelope. Comandos não têm
`simtime` e vão para o dia simulado mais recente daquele mundo. Os dias antigos são comprimidos em
`.jsonl.gz`; uma mensagem atrasada para um dia já comprimido entra como um novo membro gzip, sem
reescrever o que já estava lá.
"""

import gzip
import json
import os
from collections import OrderedDict
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import BinaryIO

from campsverso_ports import Envelope, Telemetry

_RECENT_IDS = 100_000  # entregas repetidas só acontecem com mensagens ainda não confirmadas


def _line(envelope: Envelope) -> bytes:
    return (json.dumps(envelope, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def _gz(path: Path) -> Path:
    return path.with_name(path.name + ".gz")


class JsonlArchive:
    def __init__(
        self, root: Path, compress_after_days: int, telemetry: Telemetry | None = None
    ) -> None:
        self._root = root
        self._compress_after = timedelta(days=compress_after_days)
        self._telemetry = telemetry
        self._handles: dict[Path, BinaryIO] = {}
        self._ids: OrderedDict[str, None] = OrderedDict()
        self._newest: dict[str, str] = {}  # mundo -> data simulada mais recente
        self._load()

    # ------------------------------------------------------------- abertura

    def _load(self) -> None:
        """Repara uma última linha cortada pela queda e relembra os ids dos dias mais recentes."""
        if not self._root.exists():
            return
        for world in sorted(p for p in self._root.iterdir() if p.is_dir()):
            days = sorted(world.glob("*.jsonl"))
            stems = [p.name.removesuffix(".jsonl.gz") for p in world.glob("*.jsonl.gz")]
            stems += [p.stem for p in days]
            if stems:
                self._newest[world.name] = max(stems)
            for path in days[-2:]:
                self._repair_tail(path)
                for raw in path.read_bytes().splitlines():
                    self._remember(str(json.loads(raw)["id"]))

    def _repair_tail(self, path: Path) -> None:
        data = path.read_bytes()
        if not data or data.endswith(b"\n"):
            return
        keep = data.rfind(b"\n") + 1
        with path.open("r+b") as handle:
            handle.truncate(keep)
            os.fsync(handle.fileno())
        if self._telemetry is not None:
            self._telemetry.warning(
                "archive.torn_line_removed", file=str(path), bytes=len(data) - keep
            )

    def _remember(self, event_id: str) -> None:
        self._ids[event_id] = None
        if len(self._ids) > _RECENT_IDS:
            self._ids.popitem(last=False)

    # ------------------------------------------------------------- escrita

    def _day(self, envelope: Envelope) -> tuple[str, str]:
        world = str(envelope["worldid"])
        simtime = envelope.get("simtime")
        if isinstance(simtime, str):
            day = simtime[:10]
        else:
            day = self._newest.get(world) or str(envelope["time"])[:10]
        return world, day

    def append(self, envelope: Envelope) -> bool:
        event_id = str(envelope["id"])
        if event_id in self._ids:
            return False
        world, day = self._day(envelope)
        path = self._root / world / f"{day}.jsonl"
        if _gz(path).exists():
            with gzip.open(_gz(path), "ab") as late:
                late.write(_line(envelope))
            with _gz(path).open("rb") as handle:
                os.fsync(handle.fileno())
        else:
            handle = self._handles.get(path)
            if handle is None:
                path.parent.mkdir(parents=True, exist_ok=True)
                handle = self._handles[path] = path.open("ab")
            handle.write(_line(envelope))
        self._remember(event_id)
        if day > self._newest.get(world, ""):
            self._newest[world] = day
            self.compress_old()
        return True

    def flush(self) -> None:
        for handle in self._handles.values():
            handle.flush()
            os.fsync(handle.fileno())

    # ------------------------------------------------------------- compressão

    def compress_old(self) -> Sequence[str]:
        done: list[str] = []
        for world, newest in sorted(self._newest.items()):
            limit = date.fromisoformat(newest) - self._compress_after
            for path in sorted((self._root / world).glob("*.jsonl")):
                if date.fromisoformat(path.stem) < limit and self._compress(path):
                    done.append(str(path))
        return done

    def _compress(self, path: Path) -> bool:
        handle = self._handles.pop(path, None)
        if handle is not None:
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()
        target = _gz(path)
        if target.exists():  # a queda veio entre comprimir e remover o original
            if gzip.decompress(target.read_bytes()) != path.read_bytes():
                if self._telemetry is not None:
                    self._telemetry.error("archive.compress_conflict", file=str(path))
                return False
            path.unlink()
            return True
        tmp = target.with_name(f".{target.name}.tmp")
        with (
            tmp.open("wb") as raw,
            gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz,
        ):
            gz.write(path.read_bytes())
        tmp.replace(target)
        path.unlink()
        if self._telemetry is not None:
            self._telemetry.info("archive.compressed", file=str(target))
        return True

    def close(self) -> None:
        self.flush()
        for handle in self._handles.values():
            handle.close()
        self._handles.clear()
