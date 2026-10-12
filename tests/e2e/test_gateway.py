"""Gateway com NATS e processos de verdade: visões, comandos do relógio, A6 (ADR-0050) e o A9
jogado pela tela (ADR-0051).

A UI é simulada por um cliente WebSocket. O mundo roda no modo contínuo na escala 720, com os cinco
processos, como no `make sandbox`.
"""

import asyncio
import json
import socket
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any

import websockets
import yaml

from campsverso_adapters import NatsBus, Uuid7Ids, load_env
from campsverso_gateway.state import apply_merge_patch, observer_state
from campsverso_ports import Envelope
from campsverso_testkit.nats_server import REPO, NatsServer
from campsverso_testkit.soak import ENV, WORLD, Processes
from campsverso_world_view import Projection

STREAMS = load_env(ENV, root=REPO).nats.streams
Message = dict[str, Any]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _world(out: Path) -> Path:
    world = yaml.safe_load(WORLD.read_text(encoding="utf-8"))
    world["clock"] = {"mode": "continuous", "scale": 720, "paused": False}
    path = out / "world.yaml"
    path.write_text(yaml.safe_dump(world, allow_unicode=True), encoding="utf-8")
    return path


class Gateway:
    def __init__(self, processes: Processes, out: Path, world: Path) -> None:
        self.processes, self.out, self.world, self.port = processes, out, world, _free_port()

    def spawn(self) -> None:
        self.processes.spawn(
            "gateway",
            "campsverso_gateway.main",
            "--world",
            str(self.world),
            "--data-dir",
            str(self.out / "data"),
            "--port",
            str(self.port),
        )

    def url(self, view: str) -> str:
        return f"ws://127.0.0.1:{self.port}/ws?view={view}"

    async def welcome(self, view: str, timeout: float = 30) -> Message:
        """O welcome de uma conexão nova, já com a sessão; espera o gateway subir e alcançar."""
        async with asyncio.timeout(timeout):
            while True:
                try:
                    async with websockets.connect(self.url(view)) as ws:
                        message: Message = json.loads(await ws.recv())
                    if "session" in message["state"]:
                        return message
                except OSError:
                    pass
                await asyncio.sleep(0.2)


async def _until(
    ws: websockets.ClientConnection, check: Callable[[Message], bool], timeout: float = 15
) -> Message:
    async with asyncio.timeout(timeout):
        while True:
            message: Message = json.loads(await ws.recv())
            if check(message):
                return message


async def _command(ws: websockets.ClientConnection, command: str, data: Message) -> Message:
    request_id = f"teste-{command}"
    payload = {
        "type": "campsverso.realtime.command.v1",
        "request_id": request_id,
        "command": f"campsverso.cmd.clock.{command}.v1",
        "data": data,
    }
    await ws.send(json.dumps(payload))
    return await _until(ws, lambda m: m.get("request_id") == request_id)


async def _reference(nats: NatsServer, name: str) -> dict[str, Any]:
    """O estado montado do zero, lendo os streams com a credencial do operador."""
    projection = Projection()
    bus = await NatsBus.connect(
        nats.url,
        user="operator",
        password=nats.passwords["operator"],
        name="teste-referencia",
        streams=STREAMS,
    )

    def apply(stream: str) -> Callable[[Sequence[tuple[str, Envelope]]], Awaitable[None]]:
        async def handler(batch: Sequence[tuple[str, Envelope]]) -> None:
            for _, envelope in batch:
                skip = envelope["type"] == "campsverso.perception.delivered.v1"
                if not skip and not projection.seen(stream, envelope):
                    projection.apply(stream, envelope)

        return handler

    world = await bus.consume("campsverso.*.world.>", f"{name}-world", apply("world"))
    agent = await bus.consume("campsverso.*.agent.camps.>", f"{name}-agent", apply("agent"))
    await world.caught_up()
    await agent.caught_up()
    await bus.close()
    return observer_state(projection)


def _diff(a: dict[str, Any], b: dict[str, Any]) -> str:
    return "; ".join(
        f"{k}: {a.get(k)!r:.200} != {b.get(k)!r:.200}" for k in a | b if a.get(k) != b.get(k)
    )


async def test_gateway_visoes_comandos_e_a6(tmp_path: Path, nats: NatsServer) -> None:
    world = _world(tmp_path)
    processes = Processes(nats, tmp_path, world)
    gateway = Gateway(processes, tmp_path, world)
    processes.start()
    gateway.spawn()
    try:
        operator = await gateway.welcome("operator")
        assert operator["state"]["session"]["map"]["id"] == "farm_camps"
        assert "campsverso.cmd.clock.pause.v1" in operator["commands"]
        await asyncio.sleep(3)  # o mundo anda uns 36 minutos simulados
        player = await gateway.welcome("player")
        assert "campsverso.cmd.clock.pause.v1" not in player["commands"]  # o relógio é do operador
        assert {e["visibility"] for e in player["events"]} <= {"world", "agent"}
        seen = {e["visibility"] for e in (await gateway.welcome("operator"))["events"]}
        assert "internal" in seen  # o snapshot do tick 0, por exemplo

        # A6: kill -9 no gateway; o kernel segue sozinho; o gateway volta do arquivo.
        before = (await gateway.welcome("operator"))["state"]["tick"]
        processes.running["gateway"].kill()
        processes.running["gateway"].wait()
        await asyncio.sleep(2)
        assert "kernel" not in processes.dead()
        gateway.spawn()
        async with asyncio.timeout(30):
            while (await gateway.welcome("operator"))["state"]["tick"] <= before:
                await asyncio.sleep(0.2)

        async with websockets.connect(gateway.url("operator")) as ws:
            await ws.recv()  # welcome
            reply = await _command(ws, "pause", {"reason": "debug"})
            assert reply["ok"] is True, reply
            await _until(ws, lambda m: m.get("patch", {}).get("clock", {}).get("paused") is True)
            refused = await _command(ws, "step", {"ticks": 0})
            assert refused["error"]["code"] == "invalid_command"

        await asyncio.sleep(1)  # o mundo pausado não publica mais nada
        reference = await _reference(nats, "referencia")
        state = (await gateway.welcome("operator"))["state"]
        pulse = state.pop("pulse")  # o pulso não vem dos streams (ADR-0051)
        assert state == reference, _diff(state, reference)
        assert pulse["alive"] is True
        assert pulse["tick"] >= state["tick"]

        # Pulso: com o kernel morto, o gateway marca "sem sinal" depois de 3 pulsos perdidos.
        processes.running["kernel"].kill()
        processes.running["kernel"].wait()
        async with asyncio.timeout(10):
            while (await gateway.welcome("operator"))["state"]["pulse"]["alive"]:
                await asyncio.sleep(0.5)
    finally:
        processes.stop("kernel")
        processes.stop("gateway", "controller", "perception", "archiver")
    log = (tmp_path / "gateway.log").read_text(encoding="utf-8")
    assert "gateway.failed" not in log
    archived = [line for path in (tmp_path / "archive").rglob("*.jsonl") for line in path.open()]
    assert archived
    assert not any("campsverso.live." in line for line in archived)


# ---------------------------------------------------------------- A9 pela tela (M5; ADR-0051)

PROPOSE = "campsverso.cmd.action.propose.v1"
POSSESS = "campsverso.cmd.avatar.possess.v1"
RELEASE = "campsverso.cmd.avatar.release.v1"


class Player:
    """Uma UI de mentira: aplica os merge patches e guarda os eventos, como a de verdade."""

    def __init__(self, ws: websockets.ClientConnection) -> None:
        self.ws = ws
        self.state: dict[str, Any] = {}
        self.events: list[Message] = []
        self._n = 0

    async def start(self) -> None:
        welcome: Message = json.loads(await self.ws.recv())
        self.state = welcome["state"]

    def _take(self, message: Message) -> None:
        if message["type"] == "campsverso.realtime.update.v1":
            self.state = apply_merge_patch(self.state, message["patch"])
            self.events += message["events"]

    async def ask(self, command: str, data: Message) -> Message:
        self._n += 1
        request_id = f"jogo-{self._n}"
        payload = {
            "type": "campsverso.realtime.command.v1",
            "request_id": request_id,
            "command": command,
            "data": data,
        }
        await self.ws.send(json.dumps(payload))
        async with asyncio.timeout(15):
            while True:
                message: Message = json.loads(await self.ws.recv())
                if message.get("request_id") == request_id:
                    assert message["ok"] is True, message
                    return message
                self._take(message)

    async def until(self, check: Callable[[Player], bool], timeout: float = 20) -> None:
        async with asyncio.timeout(timeout):
            while not check(self):
                self._take(json.loads(await self.ws.recv()))

    def saw(self, kind: str, since: int = 0, **data: Any) -> bool:
        return any(
            e["type"] == f"campsverso.{kind}"
            and all(e["data"].get(k) == v for k, v in data.items())
            for e in self.events[since:]
        )


def _forged_script_command() -> Message:
    """Um comando do script enquanto o humano tem a posse: o kernel recusa (not_in_control)."""
    return {
        "specversion": "1.0",
        "id": Uuid7Ids().new_id(),
        "source": "/controller-runner/script/farmer-v1",
        "type": PROPOSE,
        "time": "2026-10-12T15:00:00Z",
        "datacontenttype": "application/json",
        "dataschema": "contracts://commands/action/propose.v1",
        "worldid": "farm-camps-01",
        "cartridge": "farm_camps",
        "seq": 0,
        "controller": "script",
        "controllerid": "script/farmer-v1",
        "actor": "script/farmer-v1",
        "provenance": "simulated",
        "visibility": "observer",
        "data": {"avatar_id": "camps", "action": "wait", "params": {"ticks": 1}},
    }


async def test_a9_humano_joga_pela_ui_e_devolve(tmp_path: Path, nats: NatsServer) -> None:
    world = _world(tmp_path)
    processes = Processes(nats, tmp_path, world)
    gateway = Gateway(processes, tmp_path, world)
    processes.start()
    gateway.spawn()
    try:
        await gateway.welcome("player")
        async with websockets.connect(gateway.url("player")) as ws:
            player = Player(ws)
            await player.start()
            assert player.state["session"]["affordances"]
            await player.ask(POSSESS, {"avatar_id": "camps"})
            await player.until(lambda p: p.state["controllers"]["camps"]["type"] == "human")

            # Um canteiro vazio longe da casa, onde o script ainda não chegou.
            empty = sorted(
                (i for i, e in player.state["entities"].items() if e["kind"] == "plot"),
                reverse=True,
            )
            plot = next(i for i in empty if "crop" not in player.state["entities"][i]["attributes"])
            mark = len(player.events)
            await player.ask(
                PROPOSE, {"avatar_id": "camps", "action": "move", "params": {"near": plot}}
            )
            await player.until(lambda p: p.saw("action.completed.v1", mark, action="move"))
            plant = {"target": plot, "crop": "rabanete"}
            await player.ask(PROPOSE, {"avatar_id": "camps", "action": "plant", "params": plant})
            await player.until(
                lambda p: p.state["entities"][plot]["attributes"].get("crop") == "rabanete"
            )

            bus = await NatsBus.connect(
                nats.url,
                user="operator",
                password=nats.passwords["operator"],
                name="teste-script",
                streams=STREAMS,
            )
            await bus.publish(
                "campsverso.farm-camps-01.cmd.action.propose.v1", _forged_script_command()
            )
            await bus.close()
            await player.until(lambda p: p.saw("action.rejected.v1", reason="not_in_control"))

            mark = len(player.events)
            await player.ask(RELEASE, {"avatar_id": "camps"})
            await player.until(lambda p: p.state["controllers"]["camps"]["type"] == "script")
            await player.until(lambda p: p.saw("action.accepted.v1", mark))  # o script voltou
    finally:
        processes.stop("kernel")
        processes.stop("gateway", "controller", "perception", "archiver")
