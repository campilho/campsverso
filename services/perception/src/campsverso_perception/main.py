"""Raiz de composição da percepção.

    uv run python -m campsverso_perception.main --env config/env/local.yaml \\
        --world config/worlds/farm-camps-01.yaml

A senha do NATS vem de NATS_PERCEPTION_PASSWORD (gerada por `make secrets` em .env).
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
    DiskBlobStore,
    JsonTelemetry,
    NatsBus,
    SystemWallClock,
    Uuid7Ids,
    ValidatingBus,
    load_env,
    load_world,
)
from campsverso_perception.service import PerceptionPolicy, PerceptionService
from campsverso_ports import EventBus


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_perception.main")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument("--world", type=Path, default=Path("config/worlds/farm-camps-01.yaml"))
    parser.add_argument("--data-dir", type=Path, help="substitui data_dir do ambiente")
    parser.add_argument("--nats-url", help="substitui nats.url do ambiente")
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("perception")
    env, world = load_env(args.env), load_world(args.world)
    password = os.environ.get("NATS_PERCEPTION_PASSWORD")
    if not password:
        telemetry.error("perception.no_credentials", hint="rode `make secrets`")
        return 2
    nats = await NatsBus.connect(
        args.nats_url or env.nats.url,
        user="perception",
        password=password,
        name=f"perception-{world.worldid}",
        streams=env.nats.streams,
        telemetry=telemetry,
    )
    bus: EventBus = ValidatingBus(nats) if env.validate_events else nats
    data_dir: Path = args.data_dir or env.data_dir
    service = PerceptionService(
        world.worldid,
        bus,
        DiskBlobStore(data_dir / "perception"),
        SystemWallClock(),
        Uuid7Ids(),
        telemetry,
        PerceptionPolicy(frozenset(env.perception.deltas_for), env.perception.snapshot_every),
    )
    stop = asyncio.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(signum, stop.set)
    try:
        await service.start()
        telemetry.info("perception.running", worldid=world.worldid)
        while not stop.is_set() and service.failure is None:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), 0.5)
        if service.failure is not None:
            telemetry.error("perception.failed", error=repr(service.failure))
            return 1
        telemetry.info("perception.stopped", delivered=service.delivered)
    finally:
        await service.stop()
        await nats.close()
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(_parse(sys.argv[1:]))))


if __name__ == "__main__":
    main()
