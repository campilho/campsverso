"""Gateway: o mundo para a UI e os comandos do operador para o kernel (ADR-0022, ADR-0050).

- Lê `world`, `agent` do avatar, `internal` e `observer` com consumidores duráveis. Só `world` e
  `agent` entram na projeção; `internal` e `observer` só vão para a linha do tempo do operador.
- A projeção e o que já foi visto vão para um arquivo antes de cada confirmação, como na
  percepção: se o gateway cair, volta de onde parou.
- Cada conexão recebe um `welcome` com o estado e a linha do tempo recente, filtrada pela visão,
  e depois um `update` a cada `flush_seconds` com novidade: merge patch do estado e eventos.
- Comandos chegam como `campsverso.realtime.command.v1`. O gateway monta o envelope, valida contra
  o contrato e publica. Quem aceita ou recusa no mundo é o kernel, com um evento.
"""

import asyncio
import contextlib
import json
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import partial
from typing import Any, cast

from campsverso_contracts import CONTRACT_TYPES, subject
from campsverso_gateway.state import merge_diff, observer_state
from campsverso_ports import (
    BlobStore,
    BusUnavailableError,
    ConnectionClosedError,
    Consumer,
    Envelope,
    EnvelopeValidator,
    EventBus,
    IdGenerator,
    Message,
    RealtimeConnection,
    Subscription,
    Telemetry,
    View,
    WallClock,
)
from campsverso_world_view import Projection

WELCOME = "campsverso.realtime.welcome.v1"
UPDATE = "campsverso.realtime.update.v1"
COMMAND = "campsverso.realtime.command.v1"
REPLY = "campsverso.realtime.reply.v1"

# O relógio é só do operador (ADR-0050); jogar, assumir e devolver valem nas duas visões (ADR-0051).
CLOCK_COMMANDS = tuple(
    f"campsverso.cmd.clock.{verb}.v1"
    for verb in ("pause", "resume", "step", "set_scale", "set_mode")
)
PROPOSE = "campsverso.cmd.action.propose.v1"
POSSESS = "campsverso.cmd.avatar.possess.v1"
RELEASE = "campsverso.cmd.avatar.release.v1"
PLAY_COMMANDS = (PROPOSE, POSSESS, RELEASE)
COMMANDS: Mapping[View, tuple[str, ...]] = {
    "player": PLAY_COMMANDS,
    "operator": (*CLOCK_COMMANDS, *PLAY_COMMANDS),
}
# Quem joga pelo browser. Na v0.1 é sempre a mesma pessoa, nas duas visões (ADR-0051).
HUMAN_ID = "human/camps-browser"
ACTORS: Mapping[View, str] = {"player": "human/jogador", "operator": "human/operador"}
VISIBLE: Mapping[View, frozenset[str]] = {
    "player": frozenset({"world", "agent"}),
    "operator": frozenset({"world", "agent", "internal", "observer"}),
}
# As fotos da percepção são para os controladores: pesadas e sem uso na tela.
SKIPPED = frozenset({"campsverso.perception.delivered.v1"})
PROJECTED = ("world", "agent")
QUEUE_LIMIT = 2000  # mensagens esperando uma UI lenta; acima disso, a conexão cai
PULSE = "campsverso.live.kernel.v1"
COMMAND_REJECTED = "campsverso.world.command.rejected.v1"
PULSES_TO_SILENCE = 3  # pulsos perdidos até o kernel ficar "sem sinal" (ADR-0051)


@dataclass(eq=False)
class _Client:
    connection: RealtimeConnection
    queue: asyncio.Queue[Message] = field(
        default_factory=lambda: asyncio.Queue[Message](QUEUE_LIMIT)
    )
    sent: set[str] = field(default_factory=set[str])  # ids dos comandos que esta conexão mandou

    @property
    def view(self) -> View:
        return self.connection.view

    def sees(self, envelope: Envelope) -> bool:
        """O que a visão vê, mais a recusa dos próprios comandos: quem joga precisa saber por que
        o kernel não aceitou o seu "Assumir", mesmo sem ver os eventos `observer` (ADR-0051)."""
        if envelope["visibility"] in VISIBLE[self.view]:
            return True
        data: Mapping[str, Any] = envelope["data"]
        return envelope["type"] == COMMAND_REJECTED and data.get("command_id") in self.sent


def _order(envelope: Envelope) -> tuple[int, str, int]:
    return int(envelope.get("tick") or 0), str(envelope["source"]), int(envelope["seq"])


class GatewayService:
    def __init__(
        self,
        worldid: str,
        avatar_id: str,
        cartridge: str,
        bus: EventBus,
        blobs: BlobStore,
        clock: WallClock,
        ids: IdGenerator,
        telemetry: Telemetry,
        validator: EnvelopeValidator,
        *,
        flush_seconds: float = 0.1,
        timeline: int = 500,
    ) -> None:
        self._worldid = worldid
        self._avatar = avatar_id
        self._cartridge = cartridge
        self._bus = bus
        self._blobs = blobs
        self._clock = clock
        self._ids = ids
        self._telemetry = telemetry
        self._validator = validator
        self._flush_seconds = flush_seconds
        self._key = f"{worldid}/gateway.json"
        self.projection = Projection()
        self._seen: dict[str, int] = {}  # último seq por source, nos streams fora da projeção
        self._out_seq = 0  # seq dos comandos publicados pelo gateway
        self._load()
        self._state = observer_state(self.projection)  # como ficou no último flush
        self._timeline: deque[Envelope] = deque(maxlen=timeline)
        self._pending: list[Envelope] = []
        self._clients: set[_Client] = set()
        self._consumers: list[Consumer] = []
        self._live: Subscription | None = None
        self._pulse: dict[str, Any] | None = None  # o último pulso e quando chegou
        self._flusher: asyncio.Task[None] | None = None
        self.failure: BaseException | None = None

    # ------------------------------------------------------------- estado em arquivo

    def _load(self) -> None:
        try:
            raw = json.loads(self._blobs.get(self._key))
        except FileNotFoundError, KeyError:
            return
        self.projection = Projection(raw)
        own = raw.get("gateway", {})
        self._seen = {str(k): int(v) for k, v in own.get("seen", {}).items()}
        self._out_seq = int(own.get("out_seq", 0))

    def _save(self) -> None:
        document = {
            **self.projection.export(),
            "gateway": {"seen": self._seen, "out_seq": self._out_seq},
        }
        data = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
        self._blobs.put(self._key, data.encode())

    # ------------------------------------------------------------- ciclo de vida

    async def start(self) -> None:
        w = self._worldid
        patterns = {
            "world": f"campsverso.{w}.world.>",
            "agent": f"campsverso.{w}.agent.{self._avatar}.>",
            "internal": f"campsverso.{w}.internal.>",
            "observer": f"campsverso.{w}.observer.>",
        }
        for stream, pattern in patterns.items():
            handler = partial(self._on_batch, stream)
            self._consumers.append(
                await self._bus.consume(pattern, f"gateway-{w}-{stream}", handler)
            )
        self._live = await self._bus.subscribe(f"campsverso.{w}.live.kernel", self._on_pulse)
        self._flusher = asyncio.create_task(self._flush_loop())

    async def stop(self) -> None:
        if self._flusher is not None:
            self._flusher.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._flusher
        for consumer in self._consumers:
            await consumer.unsubscribe()
        self._consumers.clear()
        if self._live is not None:
            await self._live.unsubscribe()
            self._live = None

    async def caught_up(self) -> None:
        """Todos os streams entregues até agora já estão na projeção (para testes e para subir)."""
        for consumer in self._consumers:
            await consumer.caught_up()

    # ------------------------------------------------------------- eventos

    async def _on_batch(self, stream: str, batch: Sequence[tuple[str, Envelope]]) -> None:
        try:
            for _, envelope in batch:
                if envelope["type"] in SKIPPED or self._seen_before(stream, envelope):
                    continue
                if stream in PROJECTED:
                    self.projection.apply(stream, envelope)
                else:
                    self._seen[str(envelope["source"])] = int(envelope["seq"])
                self._pending.append(envelope)
            self._save()
        except Exception as error:
            self.failure = error
            raise

    async def _on_pulse(self, _: str, message: Envelope) -> None:
        """O pulso do kernel: fica só na memória; nada dele vai para o arquivo do gateway."""
        if message.get("type") != PULSE or not isinstance(message.get("tick"), int):
            return
        self._pulse = {
            "tick": int(message["tick"]),
            "sim_time": message.get("sim_time"),
            "every": float(message.get("pulse_seconds") or 1.0),
            "at": self._clock.monotonic(),
        }

    def _pulse_state(self) -> dict[str, Any] | None:
        if self._pulse is None:
            return None
        silent = (
            self._clock.monotonic() - self._pulse["at"] > PULSES_TO_SILENCE * self._pulse["every"]
        )
        return {
            "tick": self._pulse["tick"],
            "sim_time": self._pulse["sim_time"],
            "alive": not silent,
        }

    def _seen_before(self, stream: str, envelope: Envelope) -> bool:
        if stream in PROJECTED:
            return self.projection.seen(stream, envelope)
        return int(envelope["seq"]) <= self._seen.get(str(envelope["source"]), -1)

    async def _flush_loop(self) -> None:
        while True:
            await asyncio.sleep(self._flush_seconds)
            self.flush()

    def flush(self) -> None:
        """Manda o que mudou desde o último flush. Sem `await`: conexão nova não entra no meio."""
        state = observer_state(self.projection, self._pulse_state())
        patch = merge_diff(self._state, state)
        events = sorted(self._pending, key=_order)
        self._pending = []
        if not patch and not events:
            return
        self._state = state
        self._timeline.extend(events)
        for client in list(self._clients):
            visible = [e for e in events if client.sees(e)]
            if patch or visible:
                self._enqueue(client, {"type": UPDATE, "patch": patch, "events": visible})

    # ------------------------------------------------------------- conexões

    async def handle(self, connection: RealtimeConnection) -> None:
        """Uma UI conectada: welcome, updates e os comandos que ela mandar, até desconectar."""
        client = _Client(connection)
        view = client.view
        welcome: Message = {
            "type": WELCOME,
            "worldid": self._worldid,
            "view": view,
            "avatar_id": self._avatar,
            "commands": list(COMMANDS[view]),
            "state": self._state,
            "events": [e for e in self._timeline if e["visibility"] in VISIBLE[view]],
        }
        client.queue.put_nowait(welcome)
        self._clients.add(client)  # sem await desde o welcome: o próximo flush já vale para ela
        self._telemetry.info("gateway.connected", view=view, clients=len(self._clients))
        writer = asyncio.create_task(self._write(client))
        try:
            async for message in connection.messages():
                reply = await self._command(view, message)
                if reply.get("ok"):
                    client.sent.add(str(reply["command_id"]))
                self._enqueue(client, reply)
        finally:
            self._clients.discard(client)
            writer.cancel()
            self._telemetry.info("gateway.disconnected", view=view, clients=len(self._clients))

    def _enqueue(self, client: _Client, message: Message) -> None:
        try:
            client.queue.put_nowait(message)
        except asyncio.QueueFull:
            self._clients.discard(client)
            self._telemetry.warning("gateway.slow_client", view=client.view)
            task = asyncio.create_task(client.connection.close())
            task.add_done_callback(lambda _: None)

    async def _write(self, client: _Client) -> None:
        while True:
            message = await client.queue.get()
            try:
                await client.connection.send(message)
            except ConnectionClosedError:
                self._clients.discard(client)
                return

    # ------------------------------------------------------------- comandos

    def _reply(self, request_id: str, code: str, text: str) -> Message:
        return {
            "type": REPLY,
            "request_id": request_id,
            "ok": False,
            "error": {"code": code, "message": text[:500]},
        }

    async def _command(self, view: View, message: Message) -> Message:
        raw_id = message.get("request_id")
        request_id = raw_id if isinstance(raw_id, str) and 0 < len(raw_id) <= 64 else "desconhecido"
        command, data = message.get("command"), message.get("data")
        if message.get("type") != COMMAND or not isinstance(command, str):
            return self._reply(request_id, "invalid_message", "esperado um command com `command`")
        if not isinstance(data, Mapping):
            return self._reply(request_id, "invalid_message", "`data` precisa ser um objeto")
        if command not in COMMANDS[view]:
            return self._reply(request_id, "not_allowed", f"a visão {view} não manda {command}")
        envelope = self._envelope(view, command, dict(cast(Mapping[str, Any], data)))
        problems = self._validator.validate(envelope)
        if problems:
            text = "; ".join(str(p) for p in problems)
            return self._reply(request_id, "invalid_command", text)
        try:
            await self._bus.publish(subject(command, self._worldid), envelope)
        except BusUnavailableError as error:
            return self._reply(request_id, "unavailable", f"barramento indisponível: {error}")
        self._out_seq += 1
        self._save()
        self._telemetry.info("gateway.command", command=command, id=envelope["id"])
        return {"type": REPLY, "request_id": request_id, "ok": True, "command_id": envelope["id"]}

    def _envelope(self, view: View, command: str, data: dict[str, Any]) -> dict[str, Any]:
        """O envelope completo. Quem é o humano é o gateway que diz, nunca a UI (ADR-0051)."""
        info = CONTRACT_TYPES[command]
        if command == POSSESS:
            data = {**data, "controller": {"type": "human", "id": HUMAN_ID}}
        envelope: dict[str, Any] = {
            "specversion": "1.0",
            "id": self._ids.new_id(),
            "source": f"/gateway/{self._worldid}",
            "type": command,
            "time": self._clock.now().isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "datacontenttype": "application/json",
            "dataschema": info.dataschema,
            "worldid": self._worldid,
            "cartridge": self.projection.cartridge or self._cartridge,
            "seq": self._out_seq,
            "actor": ACTORS[view],
            "provenance": "simulated",
            "visibility": info.visibility,
            "data": data,
        }
        if command == PROPOSE:
            envelope |= {"controller": "human", "controllerid": HUMAN_ID}
        return envelope
