"""Raiz de composição do controller-runner.

    uv run python -m campsverso_controller_runner.main --controller farmer
    uv run python -m campsverso_controller_runner.main --replay data/archive/farm-camps-01

O script vem de um entry point do grupo `campsverso.controllers` (ADR-0011). O replay lê as
propostas de um arquivo de eventos gravado. A senha vem de NATS_CONTROLLER_PASSWORD.
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
    JsonTelemetry,
    NatsBus,
    SystemWallClock,
    Uuid7Ids,
    ValidatingBus,
    load_env,
    load_world,
    read_world_archive,
)
from campsverso_controller_runner.replay import ReplayRunner, recorded_proposals
from campsverso_controller_runner.runner import ControllerRunner, load_controller
from campsverso_ports import EventBus


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_controller_runner.main")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument("--world", type=Path, default=Path("config/worlds/farm-camps-01.yaml"))
    parser.add_argument("--avatar", default="camps")
    parser.add_argument("--nats-url", help="substitui nats.url do ambiente")
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--controller", help="nome do controlador (entry point), ex.: farmer")
    which.add_argument("--replay", type=Path, help="pasta do arquivo de eventos da sessão")
    parser.add_argument("--replay-id", default="replay/sessao", help="controllerid do replay")
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("controller-runner")
    env, world = load_env(args.env), load_world(args.world)
    password = os.environ.get("NATS_CONTROLLER_PASSWORD")
    if not password:
        telemetry.error("controller.no_credentials", hint="rode `make secrets`")
        return 2
    nats = await NatsBus.connect(
        args.nats_url or env.nats.url,
        user="controller",
        password=password,
        name=f"controller-{world.worldid}-{args.avatar}",
        streams=env.nats.streams,
        telemetry=telemetry,
    )
    bus: EventBus = ValidatingBus(nats) if env.validate_events else nats
    clock, ids = SystemWallClock(), Uuid7Ids()
    runner: ControllerRunner | ReplayRunner
    if args.replay is not None:
        recording = recorded_proposals(read_world_archive(args.replay), args.avatar)
        runner = ReplayRunner(
            world.worldid, args.avatar, args.replay_id, recording, bus, ids, clock, telemetry
        )
        telemetry.info("replay.loaded", proposals=len(recording), source=str(args.replay))
    else:
        controller = load_controller(args.controller)
        runner = ControllerRunner(
            world.worldid, args.avatar, controller, bus, ids, clock, telemetry
        )
    stop = asyncio.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(signum, stop.set)
    try:
        await runner.start()
        telemetry.info("controller.running", avatar=args.avatar)
        while not stop.is_set() and runner.failure is None:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), 0.5)
        if runner.failure is not None:
            telemetry.error("controller.failed", error=repr(runner.failure))
            return 1
        telemetry.info("controller.stopped")
    finally:
        await runner.stop()
        await nats.close()
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(_parse(sys.argv[1:]))))


if __name__ == "__main__":
    main()
