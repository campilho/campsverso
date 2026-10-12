"""Gateway com NATS e processos de verdade: visões, comandos do relógio e A6 (ADR-0050).

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

from campsverso_adapters import NatsBus, load_env
from campsverso_gateway.state import observer_state
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
        assert player["commands"] == []
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
