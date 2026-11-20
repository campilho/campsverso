"""Raiz de composição do publicador e do vigia do GitHub (ADR-0083).

    uv run python -m campsverso_codehost.main --env config/env/local.yaml \
        --world config/worlds/office-campsverso-01.yaml [--key privado/<chave>.pem]

Num mundo sem `codehost`, o processo só espera, como os ajudantes num mundo sem ajudantes. Com o
GitHub, a chave do App fica num arquivo fora do git, que só o `openssl` lê para assinar, e a lista
de palavras proibidas é obrigatória: o PR é público. Sem uma das duas, o processo avisa e só espera:
o escritório segue, e as entregas ficam no depósito, como no M24 (o honcho derrubaria todos os
processos com um que saísse). A senha do NATS vem de NATS_CODEHOST_PASSWORD, gerada por
`make secrets`. O patch de cada entrega se aplica sobre um clone deste repositório.
"""

import argparse
import asyncio
import contextlib
import functools
import os
import signal
import sys
from collections.abc import Sequence
from pathlib import Path

from campsverso_adapters import (
    DiskBlobStore,
    GitHubCodeHost,
    JsonTelemetry,
    MemoryCodeHost,
    NatsBus,
    SystemWallClock,
    Uuid7Ids,
    files_after_patch,
    load_env,
    load_world,
)
from campsverso_adapters.workshop_review import review
from campsverso_codehost.service import CodeHostService


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_codehost.main")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument(
        "--world", type=Path, default=Path("config/worlds/office-campsverso-01.yaml")
    )
    parser.add_argument("--data-dir", type=Path, help="substitui data_dir do ambiente (o sandbox)")
    parser.add_argument("--nats-url", help="substitui nats.url do ambiente")
    parser.add_argument("--key", type=Path, help="substitui a chave do App do arquivo do mundo")
    return parser.parse_args(argv)


async def _wait(stop: asyncio.Event) -> None:
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop.wait(), 0.5)


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("codehost")
    env, world = load_env(args.env), load_world(args.world)
    stop = asyncio.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(signum, stop.set)
    settings = world.codehost
    if settings is None or env.workshop is None:
        telemetry.info("codehost.idle", worldid=world.worldid, hint="o mundo não tem `codehost`")
        await stop.wait()
        return 0
    password = os.environ.get("NATS_CODEHOST_PASSWORD")
    if not password:
        telemetry.error("codehost.no_credentials", hint="rode `make secrets`")
        return 2
    path = env.workshop.forbidden_words
    words: list[str] = []
    if path is not None and path.is_file():
        words = [w.strip() for w in path.read_text(encoding="utf-8").splitlines() if w.strip()]
    if settings.host == "github":
        key = args.key or settings.key
        missing = None
        if key is None or not key.is_file():
            missing = "a chave do App, em privado/ (ADR-0083)"
        elif not words:
            missing = "a lista de palavras proibidas, em privado/: o PR é público"
        if missing is not None:
            telemetry.error("codehost.disabled", worldid=world.worldid, missing=missing)
            await stop.wait()
            return 0
        assert key is not None
        assert settings.app_id is not None
        assert settings.installation_id is not None
        host: GitHubCodeHost | MemoryCodeHost = GitHubCodeHost.connect(
            settings.repo, settings.app_id, settings.installation_id, key
        )
    else:
        host = MemoryCodeHost()
    data_dir: Path = args.data_dir or env.data_dir
    deliveries = env.workshop.deliveries if args.data_dir is None else data_dir / "entregas"
    bus = await NatsBus.connect(
        args.nats_url or env.nats.url,
        user="codehost",
        password=password,
        name=f"codehost-{world.worldid}",
        streams=env.nats.streams,
        telemetry=telemetry,
    )
    clock = SystemWallClock()
    service = CodeHostService(
        world.worldid,
        bus,
        host,
        DiskBlobStore(deliveries),
        DiskBlobStore(data_dir / "codehost"),
        functools.partial(files_after_patch, Path.cwd()),
        lambda diff: review(diff, words),
        words,
        clock,
        Uuid7Ids(),
        telemetry,
    )
    try:
        await service.start()
        telemetry.info(
            "codehost.running",
            worldid=world.worldid,
            host=settings.host,
            repo=settings.repo,
            open=len(service.open),
            poll_seconds=settings.poll_seconds,
        )
        next_watch = 0.0
        while not stop.is_set() and service.failure is None:
            if clock.monotonic() >= next_watch:
                next_watch = clock.monotonic() + settings.poll_seconds
                await service.watch()
            await _wait(stop)
        if service.failure is not None:
            telemetry.error("codehost.failed", error=repr(service.failure))
            return 1
        telemetry.info("codehost.stopped", open=len(service.open))
    finally:
        await service.stop()
        await bus.close()
        if isinstance(host, GitHubCodeHost):
            await host.aclose()
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(_parse(sys.argv[1:]))))


if __name__ == "__main__":
    main()
