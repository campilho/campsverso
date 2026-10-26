"""A visão do jogador é a percepção do avatar dele (ADR-0072, decisão 8); o operador vê tudo."""

import asyncio
from collections.abc import Mapping
from typing import Any

from campsverso_adapters import MemoryBlobStore, MemoryRealtime, MemoryTelemetry
from campsverso_gateway.service import GatewayService
from campsverso_testkit.pipeline import DAY, Pipeline

MORADA = "farm_morada_do_sol"


async def test_o_jogador_ve_o_que_o_camps_ve_e_o_operador_ve_tudo() -> None:
    pipeline = Pipeline(cartridge=MORADA)
    gateway = GatewayService(
        pipeline.worldid,
        "camps",
        MORADA,
        pipeline.bus,
        MemoryBlobStore(),
        pipeline.clock,
        pipeline.ids,
        MemoryTelemetry(),
        pipeline.validator,
        flush_seconds=3600,
    )
    realtime = MemoryRealtime()
    await gateway.start()
    serving = asyncio.create_task(realtime.serve(gateway.handle))
    try:
        await pipeline.start()
        world = pipeline.core.world
        first = world.day + 1  # a Dita contratada desde amanhã, como faria o quadro
        world.set_attributes(
            "dita",
            visible={"patrao": "camps", "dias": 1, "ordem": "parar"},
            hidden={"primeiro_dia": first, "ultimo_dia": first},
        )
        await pipeline.run_until(DAY + 30)  # 06:30 do dia 2: ela entrou pela entrada
        await gateway.caught_up()
        gateway.flush()
        assert world.present("dita")
        player, _ = await _connect(realtime, "player")
        operator, _ = await _connect(realtime, "operator")
        seen = player["state"]
        everything = operator["state"]
        assert "dita" in everything["entities"]
        assert "dita-regador" in everything["entities"]
        assert "dita" not in seen["entities"]  # longe do Camps, fora do raio
        assert "dita-regador" not in seen["entities"]  # o que outro avatar carrega
        assert "camps" in seen["entities"]
        assert "chest" in seen["entities"]
        assert set(seen["needs"]) == {"camps"}
        assert "dita" in everything["needs"]
        assert set(seen.get("decisions", {})) <= {"camps"}
        theirs = [
            e
            for e in operator["events"]
            if e["visibility"] == "agent" and e["data"].get("avatar_id") == "dita"
        ]
        assert theirs  # o operador vê os pedidos de decisão da Dita
        assert not [
            e
            for e in player["events"]
            if e["visibility"] == "agent" and e["data"].get("avatar_id") == "dita"
        ]
    finally:
        await realtime.stop()
        await gateway.stop()
        serving.cancel()


async def _connect(realtime: MemoryRealtime, view: str) -> tuple[Mapping[str, Any], Any]:
    client = await realtime.connect(view)  # pyright: ignore[reportArgumentType]
    return dict(await client.receive()), client
