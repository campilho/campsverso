"""Raiz de composição do arquivador.

    uv run python -m campsverso_archiver.main --env config/env/local.yaml

A senha do NATS vem de NATS_ARCHIVER_PASSWORD (gerada por `make secrets` em .env).
"""

import argparse
import asyncio
import contextlib
import os
import signal
import sys
from collections.abc import Sequence
from pathlib import Path

from campsverso_adapters import JsonlArchive, JsonTelemetry, NatsBus, load_env
from campsverso_archiver.service import ArchiverService


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_archiver.main")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument("--archive-dir", type=Path, help="substitui archive.dir do ambiente")
    parser.add_argument("--nats-url", help="substitui nats.url do ambiente")
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("archiver")
    env = load_env(args.env)
    password = os.environ.get("NATS_ARCHIVER_PASSWORD")
    if not password:
        telemetry.error("archiver.no_credentials", hint="rode `make secrets` e suba com `make run`")
        return 2
    archive = JsonlArchive(
        args.archive_dir or env.archive_dir, env.archive_compress_after_days, telemetry
    )
    bus = await NatsBus.connect(
        args.nats_url or env.nats.url,
        user="archiver",
        password=password,
        name="archiver",
        streams=env.nats.streams,
        manage_streams=True,
        duplicate_window_seconds=env.nats.duplicate_window_seconds,
        telemetry=telemetry,
    )
    service = ArchiverService(bus, archive, telemetry)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signum, stop.set)
    try:
        await service.start()
        telemetry.info("archiver.running", archive=str(args.archive_dir or env.archive_dir))
        while not stop.is_set() and service.failure is None:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), 0.5)
        if service.failure is not None:
            telemetry.error("archiver.failed", error=repr(service.failure))
            return 1
        telemetry.info("archiver.stopped", written=service.written, duplicates=service.duplicates)
    finally:
        await service.stop()
        await bus.close()
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(_parse(sys.argv[1:]))))


if __name__ == "__main__":
    main()
