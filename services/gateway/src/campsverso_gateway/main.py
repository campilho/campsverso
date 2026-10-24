"""Raiz de composição do gateway (ADR-0050).

    uv run python -m campsverso_gateway.main --env config/env/local.yaml \\
        --world config/worlds/farm-camps-01.yaml

Serve o WebSocket da UI em ws://127.0.0.1:8765/ws (porta em `gateway` no ambiente). A senha do NATS
vem de NATS_GATEWAY_PASSWORD (gerada por `make secrets` em .env).
"""

import argparse
import asyncio
import contextlib
import os
import signal
import sys
from collections.abc import Sequence
from pathlib import Path

from campsverso_adapters import (
    ContractValidator,
    DiskBlobStore,
    JsonTelemetry,
    NatsBus,
    SystemWallClock,
    Uuid7Ids,
    load_env,
    load_world,
)

# Fora do __init__ dos adaptadores: só o gateway carrega o FastAPI.
from campsverso_adapters.realtime_fastapi import FastApiRealtime
from campsverso_gateway.service import GatewayService
from campsverso_gateway.watch import WatchService

AVATAR = "camps"  # o único avatar da v0.1 (ADR-0022)


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_gateway.main")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument("--world", type=Path, default=Path("config/worlds/farm-camps-01.yaml"))
    parser.add_argument("--data-dir", type=Path, help="substitui data_dir do ambiente")
    parser.add_argument("--nats-url", help="substitui nats.url do ambiente")
    parser.add_argument("--port", type=int, help="substitui gateway.port do ambiente")
    parser.add_argument("--avatar", default=AVATAR, help="avatar acompanhado pela UI")
    parser.add_argument(
        "--watch", type=Path, help="assistir as corridas de uma rodada da arena (ADR-0068)"
    )
    return parser.parse_args(argv)


async def watch(args: argparse.Namespace) -> int:
    """O modo de assistir: sem NATS, a tela lê os arquivos de eventos de uma rodada (ADR-0068)."""
    telemetry = JsonTelemetry("gateway")
    env = load_env(args.env)
    service = WatchService(args.watch, Uuid7Ids(), telemetry)
    cartridge = service.cartridge() or load_world(args.world).cartridge
    settings = env.gateway
    port = args.port or settings.port
    realtime = FastApiRealtime(
        settings.host,
        port,
        settings.maps,
        settings.ui_dir,
        settings.art_for(cartridge),
        runs=service.runs,
    )
    stop = asyncio.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(signum, stop.set)
    await service.start()
    server = asyncio.create_task(realtime.serve(service.handle))
    telemetry.info("gateway.watching", folder=str(args.watch), url=f"http://{settings.host}:{port}")
    try:
        while not stop.is_set() and service.failure is None and not server.done():
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), 0.5)
    finally:
        await realtime.stop()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(server, 5)
        await service.stop()
    return 1 if service.failure is not None else 0


async def run(args: argparse.Namespace) -> int:
    if args.watch is not None:
        return await watch(args)
    telemetry = JsonTelemetry("gateway")
    env, world = load_env(args.env), load_world(args.world)
    password = os.environ.get("NATS_GATEWAY_PASSWORD")
    if not password:
        telemetry.error("gateway.no_credentials", hint="rode `make secrets`")
        return 2
    nats = await NatsBus.connect(
        args.nats_url or env.nats.url,
        user="gateway",
        password=password,
        name=f"gateway-{world.worldid}",
        streams=env.nats.streams,
        telemetry=telemetry,
    )
    data_dir: Path = args.data_dir or env.data_dir
    service = GatewayService(
        world.worldid,
        args.avatar,
        world.cartridge,
        nats,
        DiskBlobStore(data_dir / "gateway"),
        SystemWallClock(),
        Uuid7Ids(),
        telemetry,
        ContractValidator(),
    )
    settings = env.gateway
    port = args.port or settings.port
    realtime = FastApiRealtime(
        settings.host, port, settings.maps, settings.ui_dir, settings.art_for(world.cartridge)
    )
    stop = asyncio.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(signum, stop.set)
    server: asyncio.Task[None] | None = None
    try:
        await service.start()
        server = asyncio.create_task(realtime.serve(service.handle))
        telemetry.info(
            "gateway.running", worldid=world.worldid, url=f"ws://{settings.host}:{port}/ws"
        )
        while not stop.is_set() and service.failure is None and not server.done():
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), 0.5)
        if service.failure is not None:
            telemetry.error("gateway.failed", error=repr(service.failure))
            return 1
        if server.done() and not stop.is_set() and server.exception() is not None:
            telemetry.error("gateway.server_failed", error=repr(server.exception()))
            return 1
        telemetry.info("gateway.stopped")
    finally:
        await realtime.stop()
        if server is not None:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(server, 5)
        await service.stop()
        await nats.close()
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(_parse(sys.argv[1:]))))


if __name__ == "__main__":
    main()
