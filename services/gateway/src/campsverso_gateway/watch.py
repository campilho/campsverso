"""O modo de assistir (ADR-0068): a tela de cada corrida de uma rodada da arena, montada a partir do
arquivo de eventos dela pela mesma projeção do gateway, sem barramento e sem kernel.

- Cada corrida é uma pasta com `archive.jsonl` (que cresce a cada dia simulado enquanto ela roda) e
  `estado.json` (o dia e se terminou).
- Uma corrida em andamento é seguida: o que chega ao arquivo vai para a tela. Uma terminada é
  tocada desde o começo num relógio de reprodução, que o operador pausa e acelera com os mesmos
  comandos de relógio do mundo (a escala é segundos simulados por segundo real; `max` é tudo de
  uma vez). O que a tela pede além disso é recusado: assistir não muda o mundo.
- Assistir é ler fatos: é determinístico por construção e não toca no princípio 7.
"""

import asyncio
import json
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from campsverso_gateway.service import (
    COMMAND,
    REPLY,
    UPDATE,
    VISIBLE,
    WELCOME,
    _Client,  # pyright: ignore[reportPrivateUsage]
)
from campsverso_gateway.state import merge_diff, observer_state
from campsverso_ports import (
    ConnectionClosedError,
    Envelope,
    IdGenerator,
    Message,
    RealtimeConnection,
    Telemetry,
)
from campsverso_world_view import Projection

SESSION = "campsverso.world.session.started.v1"
PROJECTED = frozenset({"world", "agent"})
NOTEBOOK = "campsverso.memory."
CLOCK = "campsverso.cmd.clock."
START_SCALE = 1440.0  # um dia por minuto, a velocidade com que uma corrida gravada começa
MAX_STEP = 20_000  # eventos aplicados por passada no modo máximo, para a tela não travar


@dataclass(eq=False)
class _Run:
    name: str
    folder: Path
    projection: Projection = field(default_factory=Projection)
    offset: int = 0  # bytes do arquivo já lidos
    loaded: deque[Envelope] = field(default_factory=deque[Envelope])  # lidos, ainda não aplicados
    timeline: deque[Envelope] = field(default_factory=lambda: deque[Envelope](maxlen=500))
    pending: list[Envelope] = field(default_factory=list[Envelope])  # aplicados desde o flush
    clients: set[_Client] = field(default_factory=set[_Client])
    state: dict[str, Any] = field(default_factory=dict[str, Any])
    mode: str = "continuous"
    scale: float = START_SCALE
    paused: bool = False
    play_tick: float = 0.0
    tick_seconds: int = 60
    worldid: str = ""

    def status(self) -> Mapping[str, Any]:
        path = self.folder / "estado.json"
        if not path.exists():
            return {"day": 0, "done": (self.folder / "summary.json").exists()}
        return cast(Mapping[str, Any], json.loads(path.read_text(encoding="utf-8")))

    @property
    def done(self) -> bool:
        return bool(self.status().get("done"))


class WatchService:
    def __init__(
        self, folder: Path, ids: IdGenerator, telemetry: Telemetry, *, flush_seconds: float = 0.1
    ) -> None:
        self._folder = folder
        self._ids = ids
        self._telemetry = telemetry
        self._flush_seconds = flush_seconds
        self._runs: dict[str, _Run] = {}
        self._task: asyncio.Task[None] | None = None
        self.failure: BaseException | None = None
        self._refresh()

    # ------------------------------------------------------------- as corridas

    def _refresh(self) -> None:
        if not self._folder.is_dir():
            return
        for sub in sorted(self._folder.iterdir()):
            if (sub / "archive.jsonl").exists() and sub.name not in self._runs:
                self._runs[sub.name] = _Run(sub.name, sub)

    def cartridge(self) -> str | None:
        """O cartucho da rodada, pelo primeiro evento da primeira corrida (a arte e o mapa)."""
        for run in self._runs.values():
            with (run.folder / "archive.jsonl").open(encoding="utf-8") as handle:
                first = handle.readline()
            if first:
                return str(json.loads(first).get("cartridge"))
        return None

    def runs(self) -> list[dict[str, Any]]:
        """A lista da página da arena: o nome, o dia, se terminou e o que o resumo diz."""
        self._refresh()
        listing: list[dict[str, Any]] = []
        for run in self._runs.values():
            status = run.status()
            entry: dict[str, Any] = {
                "name": run.name,
                "day": int(status.get("day") or 0),
                "done": bool(status.get("done")),
            }
            summary = run.folder / "summary.json"
            if summary.exists():
                data = json.loads(summary.read_text(encoding="utf-8"))
                spec = cast(Mapping[str, Any], data.get("spec") or {})
                entry["controller"] = spec.get("controller")
                entry["model"] = spec.get("model") if spec.get("controller") == "llm" else None
                entry["cost_usd"] = data.get("cost_usd")
                entry["coins"] = cast(Mapping[str, Any], data.get("totals") or {}).get("coins_end")
            listing.append(entry)
        return listing

    def _read(self, run: _Run) -> None:
        """O que chegou ao arquivo desde a última leitura, linha inteira por linha inteira."""
        path = run.folder / "archive.jsonl"
        size = path.stat().st_size
        if size <= run.offset:
            return
        with path.open("rb") as handle:
            handle.seek(run.offset)
            chunk = handle.read(size - run.offset)
        end = chunk.rfind(b"\n") + 1  # uma linha pela metade fica para a próxima leitura
        for line in chunk[:end].splitlines():
            if line.strip():
                run.loaded.append(cast(Envelope, json.loads(line)))
        run.offset += end

    def _apply(self, run: _Run, envelope: Envelope) -> None:
        kind = str(envelope["type"])
        if kind == SESSION:
            data = cast(Mapping[str, Any], envelope["data"])
            run.tick_seconds = int(data.get("tick_seconds") or 60)
            run.worldid = str(envelope.get("worldid") or "")
        visibility = str(envelope.get("visibility"))
        from_kernel = str(envelope.get("source", "")).startswith("/kernel/")
        if (visibility in PROJECTED and from_kernel) or kind.startswith(NOTEBOOK):
            run.projection.apply(visibility, envelope)
        run.pending.append(envelope)

    def advance(self, run: _Run, seconds: float) -> None:
        """Lê o arquivo e aplica o que a reprodução alcançou: tudo, numa corrida em andamento ou no
        modo máximo; até o tick do relógio de reprodução, numa terminada."""
        self._read(run)
        live = not run.done
        if not run.paused and not live and run.mode == "continuous":
            run.play_tick += seconds * run.scale / run.tick_seconds
        step = MAX_STEP if run.mode == "max" or live else len(run.loaded)
        while run.loaded and step > 0:
            envelope = run.loaded[0]
            if not live and run.mode != "max" and int(envelope.get("tick") or 0) > run.play_tick:
                break
            if run.paused and not live:
                break
            run.loaded.popleft()
            self._apply(run, envelope)
            step -= 1

    # ------------------------------------------------------------- a tela

    def _state(self, run: _Run) -> dict[str, Any]:
        state = observer_state(run.projection)
        state["clock"] = {"mode": run.mode, "scale": run.scale, "paused": run.paused}
        return state

    def flush(self, run: _Run) -> None:
        state = self._state(run)
        patch = merge_diff(run.state, state)
        events, run.pending = run.pending, []
        if not patch and not events:
            return
        run.state = state
        run.timeline.extend(events)
        for client in list(run.clients):
            visible = [e for e in events if e.get("visibility") in VISIBLE[client.view]]
            if patch or visible:
                self._send(run, client, {"type": UPDATE, "patch": patch, "events": visible})

    def _send(self, run: _Run, client: _Client, message: Message) -> None:
        try:
            client.queue.put_nowait(message)
        except asyncio.QueueFull:
            run.clients.discard(client)

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()

    async def _loop(self) -> None:
        loop = asyncio.get_running_loop()
        last = loop.time()
        try:
            while True:
                await asyncio.sleep(self._flush_seconds)
                now = loop.time()
                for run in list(self._runs.values()):
                    if run.clients:  # só toca a corrida que alguém está vendo
                        self.advance(run, now - last)
                        self.flush(run)
                last = now
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self.failure = error
            raise

    async def handle(self, connection: RealtimeConnection) -> None:
        self._refresh()
        run = self._runs.get(connection.run or "")
        if run is None:
            await connection.close()
            return
        client = _Client(connection)
        if not run.clients and not run.state:
            self.advance(run, 0.0)
            run.state = self._state(run)
            run.timeline.extend(run.pending)
            run.pending = []
        view = client.view
        client.queue.put_nowait(
            {
                "type": WELCOME,
                "worldid": run.worldid or run.name,
                "view": view,
                "avatar_id": "camps",
                "commands": [f"{CLOCK}{v}.v1" for v in ("pause", "resume", "set_scale", "set_mode")]
                if view == "operator"
                else [],
                "state": run.state,
                "events": [e for e in run.timeline if e.get("visibility") in VISIBLE[view]],
            }
        )
        run.clients.add(client)
        writer = asyncio.create_task(self._write(run, client))
        try:
            async for message in connection.messages():
                self._send(run, client, self._command(run, client, message))
        finally:
            run.clients.discard(client)
            writer.cancel()

    async def _write(self, run: _Run, client: _Client) -> None:
        while True:
            message = await client.queue.get()
            try:
                await client.connection.send(message)
            except ConnectionClosedError:
                run.clients.discard(client)
                return

    def _command(self, run: _Run, client: _Client, message: Message) -> Message:
        """Os comandos de relógio do operador viram o relógio de reprodução; o resto é recusado."""
        raw = message.get("request_id")
        request = raw if isinstance(raw, str) and 0 < len(raw) <= 64 else "desconhecido"
        command = str(message.get("command") or "")
        data = cast(Mapping[str, Any], message.get("data") or {})
        if message.get("type") != COMMAND or client.view != "operator":
            return _reply(request, "read_only", "assistir não muda o mundo")
        if command == f"{CLOCK}pause.v1":
            run.paused = True
        elif command == f"{CLOCK}resume.v1":
            run.paused = False
        elif command in (f"{CLOCK}set_scale.v1", f"{CLOCK}set_mode.v1"):
            run.mode = str(data.get("mode") or "continuous")
            if data.get("scale") is not None:
                run.scale = float(data["scale"])
        else:
            return _reply(request, "read_only", "assistir não muda o mundo")
        return {"type": REPLY, "request_id": request, "ok": True, "command_id": self._ids.new_id()}


def _reply(request_id: str, code: str, text: str) -> Message:
    return {
        "type": REPLY,
        "request_id": request_id,
        "ok": False,
        "error": {"code": code, "message": text},
    }


def runs_in(folder: Path) -> Sequence[str]:
    """As corridas de uma rodada: as pastas com arquivo de eventos."""
    return sorted(p.name for p in folder.iterdir() if (p / "archive.jsonl").exists())
