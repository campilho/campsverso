"""O adaptador FastAPI de verdade: WebSocket por visão, mapa do cartucho e saúde (ADR-0050)."""

import asyncio
import json
import socket
import urllib.error
import urllib.request
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from typing import Any

import pytest
import websockets

from campsverso_adapters.realtime_fastapi import FastApiRealtime, local_origin
from campsverso_ports import RealtimeConnection


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


NOTICES: list[dict[str, Any]] = []


def _notice(given: Mapping[str, Any]) -> str | None:
    if given.get("kind") != "troca":
        return "kind é troca"
    NOTICES.append(dict(given))
    return None


async def _echo(connection: RealtimeConnection) -> None:
    await connection.send({"view": connection.view})
    async for message in connection.messages():
        await connection.send({"echo": dict(message)})


@pytest.fixture
async def server(tmp_path: Path) -> AsyncIterator[str]:
    tmj = tmp_path / "map.tmj"
    tmj.write_text('{"type": "map"}', encoding="utf-8")
    genre, scenario = tmp_path / "farm" / "art", tmp_path / "camps" / "art"
    (genre / "tiles").mkdir(parents=True)
    (tmp_path / "farm" / "locale").mkdir()
    (tmp_path / "farm" / "locale" / "pt-BR.json").write_text('{"names": {}}', encoding="utf-8")
    (genre / "tiles" / "grass.png").write_bytes(b"png")
    scenario.mkdir(parents=True)
    (scenario / "art.json").write_text('{"version": 1}', encoding="utf-8")
    (tmp_path / "segredo.txt").write_text("fora da arte", encoding="utf-8")
    delivered = tmp_path / "entregas" / "office-x" / "pedido-001"
    delivered.mkdir(parents=True)
    (delivered / "abc-1.patch").write_text("diff --git a/x b/x\n+olá\n", encoding="utf-8")
    (delivered / "abc-1.json").write_text('{"files": ["x"]}', encoding="utf-8")
    (delivered / "abc-1.txt").write_text("outro tipo", encoding="utf-8")
    realtime = FastApiRealtime(
        "127.0.0.1",
        _free_port(),
        maps={"farm_camps": tmj},
        art=(("farm", genre), ("farm_camps", scenario), ("sem_pasta", tmp_path / "nada")),
        deliveries=tmp_path / "entregas",
        notice=_notice,
    )
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


async def test_a_pagina_de_outro_site_nao_abre_o_websocket(server: str) -> None:
    # A tela desta máquina, pelo gateway ou pelo Vite, em qualquer porta.
    for origin in ("http://127.0.0.1:8765", "http://localhost:5173", "http://[::1]:8765"):
        async with websockets.connect(f"ws://{server}/ws?view=operator", origin=origin) as ws:  # pyright: ignore[reportArgumentType]
            assert json.loads(await ws.recv()) == {"view": "operator"}
    # Outro site, um nome que aponta para 127.0.0.1 (DNS rebinding) e uma página sem origem.
    for origin in ("https://evil.example", f"http://evil.example:{server.split(':')[1]}", "null"):
        with pytest.raises(websockets.exceptions.InvalidStatus) as refused:
            async with websockets.connect(f"ws://{server}/ws?view=player", origin=origin) as ws:  # pyright: ignore[reportArgumentType]
                await ws.recv()
        assert refused.value.response.status_code == 403


def test_origem_local() -> None:
    assert local_origin(None, "127.0.0.1")  # um processo desta máquina, não um navegador
    assert local_origin("http://localhost:8765", "127.0.0.1")
    assert local_origin("http://192.168.0.7:8765", "192.168.0.7")  # o endereço em que escuta
    assert not local_origin("http://192.168.0.7:8765", "127.0.0.1")
    assert not local_origin("http://localhost.evil.example", "127.0.0.1")
    assert not local_origin("null", "127.0.0.1")
    assert not local_origin("http://[::1", "127.0.0.1")  # origem malformada


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


async def test_arte_em_camadas_sem_sair_da_pasta(server: str) -> None:
    def get(path: str) -> tuple[int, str]:
        try:
            with urllib.request.urlopen(f"http://{server}{path}", timeout=5) as response:
                return response.status, response.read().decode()
        except urllib.error.HTTPError as error:
            return error.code, ""

    index = await asyncio.to_thread(get, "/content/art/index.json")
    assert index == (200, '{"layers":["farm","farm_camps"]}')
    assert await asyncio.to_thread(get, "/content/art/farm/tiles/grass.png") == (200, "png")
    assert await asyncio.to_thread(get, "/content/art/farm_camps/art.json") == (
        200,
        '{"version": 1}',
    )
    assert (await asyncio.to_thread(get, "/content/art/farm/art.json"))[0] == 404
    assert (await asyncio.to_thread(get, "/content/art/farm/..%2Fsegredo.txt"))[0] == 404
    assert (await asyncio.to_thread(get, "/content/art/outra/art.json"))[0] == 404


async def test_mapas_e_arte_se_conferem_a_cada_vez(server: str) -> None:
    # Um terrain.png antigo no cache do navegador deixou pretas as margens novas da água (ADR-0070).
    def cache_control(path: str) -> str | None:
        with urllib.request.urlopen(f"http://{server}{path}", timeout=5) as response:
            return response.headers.get("Cache-Control")

    assert await asyncio.to_thread(cache_control, "/content/maps/farm_camps.tmj") == "no-cache"
    assert await asyncio.to_thread(cache_control, "/content/art/farm/tiles/grass.png") == "no-cache"


async def test_os_nomes_por_lingua_ao_lado_da_arte(server: str) -> None:
    """ADR-0075: `locale/<língua>.json` de cada camada, sem sair da pasta."""

    def get(path: str) -> tuple[int, str]:
        try:
            with urllib.request.urlopen(f"http://{server}{path}", timeout=5) as response:
                return response.status, response.read().decode()
        except urllib.error.HTTPError as error:
            return error.code, ""

    assert await asyncio.to_thread(get, "/content/locale/farm/pt-BR.json") == (200, '{"names": {}}')
    assert (await asyncio.to_thread(get, "/content/locale/farm_camps/pt-BR.json"))[0] == 404
    assert (await asyncio.to_thread(get, "/content/locale/farm/..%2F..%2Fsegredo.txt"))[0] == 404
    assert (await asyncio.to_thread(get, "/content/locale/outra/pt-BR.json"))[0] == 404


async def test_o_patch_entregue_so_para_ler(server: str) -> None:
    """ADR-0080: o gerente vê o patch e o resumo antes de aceitar; nada além disso sai daqui."""

    def get(path: str) -> tuple[int, str, str]:
        try:
            with urllib.request.urlopen(f"http://{server}{path}", timeout=5) as response:
                kind = str(response.headers.get("content-type"))
                return response.status, response.read().decode(), kind
        except urllib.error.HTTPError as error:
            return error.code, "", ""

    status, body, kind = await asyncio.to_thread(
        get, "/content/entregas/office-x/pedido-001/abc-1.patch"
    )
    assert (status, body) == (200, "diff --git a/x b/x\n+olá\n")
    assert kind.startswith("text/plain")
    assert (await asyncio.to_thread(get, "/content/entregas/office-x/pedido-001/abc-1.json"))[
        :2
    ] == (200, '{"files": ["x"]}')
    for refused in (
        "/content/entregas/office-x/pedido-001/abc-1.txt",  # outro tipo
        "/content/entregas/office-x/pedido-001/nada.patch",
        "/content/entregas/..%2Fsegredo.txt",
    ):
        assert (await asyncio.to_thread(get, refused))[0] == 404


async def test_o_aviso_do_supervisor_entra_por_post_local(server: str) -> None:
    """A parte 5 do M25: o supervisor, na mesma máquina, avisa as telas pelo gateway."""

    def post(body: object) -> int:
        request = urllib.request.Request(
            f"http://{server}/aviso",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status
        except urllib.error.HTTPError as error:
            return error.code

    NOTICES.clear()
    assert await asyncio.to_thread(post, {"kind": "troca", "text": "agora"}) == 200
    assert NOTICES == [{"kind": "troca", "text": "agora"}]
    assert await asyncio.to_thread(post, {"kind": "outro", "text": "x"}) == 422
    assert await asyncio.to_thread(post, ["não", "é", "objeto"]) == 422
