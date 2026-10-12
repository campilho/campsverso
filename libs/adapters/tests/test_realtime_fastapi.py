"""O adaptador FastAPI de verdade: WebSocket por visão, mapa do cartucho e saúde (ADR-0050)."""

import asyncio
import json
import socket
import urllib.error
import urllib.request
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import websockets

from campsverso_adapters.realtime_fastapi import FastApiRealtime
from campsverso_ports import RealtimeConnection


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


async def _echo(connection: RealtimeConnection) -> None:
    await connection.send({"view": connection.view})
    async for message in connection.messages():
        await connection.send({"echo": dict(message)})


@pytest.fixture
async def server(tmp_path: Path) -> AsyncIterator[str]:
    tmj = tmp_path / "map.tmj"
    tmj.write_text('{"type": "map"}', encoding="utf-8")
    realtime = FastApiRealtime("127.0.0.1", _free_port(), maps={"farm_camps": tmj})
    task = asyncio.create_task(realtime.serve(_echo))
    async with asyncio.timeout(10):
        while not realtime.started:
            await asyncio.sleep(0.02)
    yield f"127.0.0.1:{realtime.port}"
    await realtime.stop()
    await task


async def test_websocket_por_visao_e_json_invalido(server: str) -> None:
    async with websockets.connect(f"ws://{server}/ws?view=operator") as ws:
        assert json.loads(await ws.recv()) == {"view": "operator"}
        await ws.send(json.dumps({"type": "x"}))
        assert json.loads(await ws.recv()) == {"echo": {"type": "x"}}
        await ws.send("isto não é json")
        assert json.loads(await ws.recv()) == {"echo": {}}


async def test_visao_desconhecida_e_recusada(server: str) -> None:
    with pytest.raises(websockets.exceptions.WebSocketException):
        async with websockets.connect(f"ws://{server}/ws?view=visitor") as ws:
            await ws.recv()


async def test_mapa_do_cartucho_e_saude(server: str) -> None:
    def get(path: str) -> tuple[int, str]:
        try:
            with urllib.request.urlopen(f"http://{server}{path}", timeout=5) as response:
                return response.status, response.read().decode()
        except urllib.error.HTTPError as error:
            return error.code, ""

    assert await asyncio.to_thread(get, "/content/maps/farm_camps.tmj") == (200, '{"type": "map"}')
    assert (await asyncio.to_thread(get, "/content/maps/outro.tmj"))[0] == 404
    assert await asyncio.to_thread(get, "/health") == (200, '{"ok":true}')
