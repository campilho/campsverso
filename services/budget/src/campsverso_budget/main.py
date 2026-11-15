"""Raiz de composição da guarda de orçamento (ADR-0058).

    uv run python -m campsverso_budget.main --env config/env/local.yaml \
        --world config/worlds/farm-camps-01.yaml

O teto vem do arquivo do mundo (`budget`), até o operador mudá-lo com o mundo vivo
(`cmd.ops.budget.set`, ADR-0080); o sinal de vida sai a cada PULSE_SECONDS. A senha do NATS vem
de NATS_BUDGET_PASSWORD, gerada por `make secrets`.
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
    load_env,
    load_world,
)
from campsverso_budget.ledger import BudgetLimits
from campsverso_budget.service import BudgetService

# O sinal de vida da guarda (ADR-0080): a mente do escritório desliga depois de 3 sinais perdidos.
PULSE_SECONDS = 5.0


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_budget.main")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument("--world", type=Path, default=Path("config/worlds/farm-camps-01.yaml"))
    parser.add_argument("--data-dir", type=Path, help="substitui data_dir do ambiente")
    parser.add_argument("--nats-url", help="substitui nats.url do ambiente")
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("budget")
    env, world = load_env(args.env), load_world(args.world)
    if world.budget is None:
        telemetry.error("budget.no_limits", hint="o arquivo do mundo precisa de `budget`")
        return 2
    password = os.environ.get("NATS_BUDGET_PASSWORD")
    if not password:
        telemetry.error("budget.no_credentials", hint="rode `make secrets`")
        return 2
    bus = await NatsBus.connect(
        args.nats_url or env.nats.url,
        user="budget",
        password=password,
        name=f"budget-{world.worldid}",
        streams=env.nats.streams,
        telemetry=telemetry,
    )
    data_dir: Path = args.data_dir or env.data_dir
    clock = SystemWallClock()
    service = BudgetService(
        world.worldid,
        BudgetLimits(
            world.budget.usd_per_sim_day, world.budget.usd_total, world.budget.usd_per_ticket
        ),
        bus,
        DiskBlobStore(data_dir / "budget"),
        clock,
        Uuid7Ids(),
        telemetry,
        on_exceeded=world.budget.on_exceeded,
    )
    stop = asyncio.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(signum, stop.set)
    try:
        await service.start()
        telemetry.info(
            "budget.running",
            worldid=world.worldid,
            usd_per_sim_day=world.budget.usd_per_sim_day,
            usd_total=world.budget.usd_total,
            usd_per_ticket=world.budget.usd_per_ticket,
            on_exceeded=world.budget.on_exceeded,
            spent_usd=service.ledger.total,
        )
        next_pulse = 0.0
        while not stop.is_set() and service.failure is None:
            if clock.monotonic() >= next_pulse:
                next_pulse = clock.monotonic() + PULSE_SECONDS
                await service.announce_pulse(PULSE_SECONDS)
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), 0.5)
        if service.failure is not None:
            telemetry.error("budget.failed", error=repr(service.failure))
            return 1
        telemetry.info("budget.stopped", paused_times=service.paused_times)
    finally:
        await service.stop()
        await bus.close()
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(_parse(sys.argv[1:]))))


if __name__ == "__main__":
    main()
