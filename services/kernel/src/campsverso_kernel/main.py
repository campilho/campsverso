"""Raiz de composição do kernel: lê a configuração, monta os adaptadores e roda o relógio.

    uv run python -m campsverso_kernel.main --env config/env/local.yaml \\
        --world config/worlds/farm-camps-01.yaml

A senha do NATS vem de NATS_KERNEL_PASSWORD (gerada por `make secrets` em .env).
SIGINT e SIGTERM param com elegância (snapshot antes de sair); kill -9 exercita a recuperação.
"""

import argparse
import asyncio
import os
import signal
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from campsverso_adapters import (
    ContractValidator,
    DiskBlobStore,
    EnvSettings,
    JsonTelemetry,
    NatsBus,
    SqliteWorldStore,
    SystemWallClock,
    Uuid7Ids,
    ValidatingBus,
    WorldSettings,
    YamlFlags,
    load_env,
    load_world,
    read_world_archive,
)
from campsverso_cartridge_api import ControllerRef, ControllerType
from campsverso_kernel.core import WorldConfig
from campsverso_kernel.definition import WorldDefinition
from campsverso_kernel.loader import build_world, discover
from campsverso_kernel.recovery import open_world
from campsverso_kernel.replay import DayReplay, replay_day
from campsverso_kernel.runner import ClockLoop
from campsverso_kernel.service import KernelService
from campsverso_kernel.version import RunVersion, run_version
from campsverso_ports import EventBus, RuleConfig


@dataclass(frozen=True)
class Prepared:
    definition: WorldDefinition
    config: WorldConfig
    rules: Sequence[RuleConfig]
    rules_source: str
    version: RunVersion


def prepare(env: EnvSettings, world: WorldSettings) -> Prepared:
    """Tudo o que define o mundo, igual no processo e nos testes que comparam com ele."""
    cartridges = discover()
    definition = build_world(world.cartridge, cartridges)
    rules_path = world.rules_file or cartridges[world.cartridge].rules_file()
    rules = YamlFlags(rules_path).rules() if rules_path is not None else ()
    source = "(nenhum)" if rules_path is None else f"{world.cartridge}/{rules_path.name}"
    return Prepared(
        definition=definition,
        config=WorldConfig(world.worldid, world.seed, world.start),
        rules=rules,
        rules_source=source,
        version=run_version(world.cartridge, env.snapshot_every_ticks, cartridges),
    )


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_kernel.main")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument("--world", type=Path, default=Path("config/worlds/farm-camps-01.yaml"))
    parser.add_argument("--data-dir", type=Path, help="substitui data_dir do ambiente")
    parser.add_argument("--nats-url", help="substitui nats.url do ambiente")
    parser.add_argument("--scale", type=float, help="escala inicial de um mundo novo")
    parser.add_argument(
        "--replay-day", type=int, help="não sobe o kernel: reexecuta o dia N e compara (A5)"
    )
    parser.add_argument("--archive-dir", type=Path, help="substitui archive.dir do ambiente")
    return parser.parse_args(argv)


def replay(args: argparse.Namespace) -> int:
    """`make replay DAY=N`: reexecuta o dia a partir do snapshot e do diário e compara (A5)."""
    env, world = load_env(args.env), load_world(args.world)
    prepared = prepare(env, world)
    data_dir: Path = args.data_dir or env.data_dir
    archive_dir: Path = (args.archive_dir or env.archive_dir) / world.worldid
    store = SqliteWorldStore(data_dir / world.worldid / "world.sqlite")
    try:
        result = replay_day(
            prepared.definition,
            prepared.config,
            prepared.version,
            store,
            DiskBlobStore(data_dir),
            read_world_archive(archive_dir),
            args.replay_day,
            ContractValidator(),
        )
    finally:
        store.close()
    print(
        f"dia {result.day} (ticks {result.start} a {result.end - 1}), a partir de "
        f"{result.from_snapshot}: {len(result.regenerated)} fatos reexecutados, "
        f"{len(result.recorded)} no arquivo"
    )
    print(f"  reexecução: {DayReplay.digest(result.regenerated)}")
    print(f"  arquivo:    {DayReplay.digest(result.recorded)}")
    if result.equal:
        print("  iguais: o dia se reproduz.")
        return 0
    print(f"  DIFERENTES. Primeira diferença (reexecução, arquivo): {result.first_difference()}")
    return 1


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("kernel")
    env, world = load_env(args.env), load_world(args.world)
    prepared = prepare(env, world)
    data_dir: Path = args.data_dir or env.data_dir
    store = SqliteWorldStore(data_dir / world.worldid / "world.sqlite")
    blobs = DiskBlobStore(data_dir)
    validator = ContractValidator()
    engine, recovery = open_world(
        prepared.definition,
        prepared.config,
        prepared.rules,
        prepared.version,
        store,
        blobs,
        rules_source=prepared.rules_source,
        validator=validator,
    )
    core = engine.core
    if recovery is None:
        core.configure_controllers(
            {
                avatar: ControllerRef(cast(ControllerType, kind), cid)
                for avatar, (kind, cid) in world.controllers.items()
            }
        )
        core.configure_clock(world.mode, args.scale or world.scale, world.paused)
        telemetry.info("kernel.new_world", worldid=world.worldid, seed=world.seed)
    else:
        telemetry.info(
            "kernel.recovered",
            snapshot=recovery.snapshot_ref,
            from_tick=recovery.snapshot_tick,
            to_tick=recovery.tick,
            inputs=recovery.inputs,
            facts_verified=recovery.facts,
        )
    password = os.environ.get("NATS_KERNEL_PASSWORD")
    if not password:
        telemetry.error("kernel.no_credentials", hint="rode `make secrets` e suba com `make run`")
        return 2
    nats = await NatsBus.connect(
        args.nats_url or env.nats.url,
        user="kernel",
        password=password,
        name=f"kernel-{world.worldid}",
        streams=env.nats.streams,
        manage_streams=True,
        duplicate_window_seconds=env.nats.duplicate_window_seconds,
        telemetry=telemetry,
    )
    bus: EventBus = ValidatingBus(nats, validator) if env.validate_events else nats
    clock = SystemWallClock()
    service = KernelService(
        engine,
        bus,
        clock,
        Uuid7Ids(),
        store,
        blobs,
        telemetry,
        keep_full=env.snapshot_keep_full,
    )
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signum, stop.set)
    try:
        await service.start()
        telemetry.info(
            "kernel.running", tick=core.tick, mode=core.mode, scale=core.scale, paused=core.paused
        )
        await ClockLoop(service, clock, telemetry).run(stop)
        await service.stop()
        telemetry.info("kernel.stopped", tick=core.tick)
    finally:
        await nats.close()
        store.close()
    return 0


def main() -> None:
    args = _parse(sys.argv[1:])
    sys.exit(replay(args) if args.replay_day is not None else asyncio.run(run(args)))


if __name__ == "__main__":
    main()
