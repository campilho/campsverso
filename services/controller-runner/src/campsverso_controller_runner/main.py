"""Raiz de composição do controller-runner.

    uv run python -m campsverso_controller_runner.main --controller farmer
    uv run python -m campsverso_controller_runner.main --replay data/archive/farm-camps-01
    uv run python -m campsverso_controller_runner.main --mind camps

O script vem de um entry point do grupo `campsverso.controllers` (ADR-0011); a mente, do grupo
`campsverso.minds`, com o modelo, o esforço e a fita lidos de `minds.<avatar>` no arquivo do mundo
(ADR-0059), e a porta de modelo montada aqui: adaptador da Anthropic, fita e medidor (ADR-0058).
O replay lê as propostas de um arquivo de eventos gravado. A senha do NATS vem de
NATS_CONTROLLER_PASSWORD (script e replay) ou NATS_MIND_PASSWORD (a mente).
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
    AnthropicModel,
    JsonTelemetry,
    MeteredModel,
    NatsBus,
    RecordingModel,
    SqliteMemory,
    SystemWallClock,
    Uuid7Ids,
    ValidatingBus,
    load_env,
    load_world,
    read_world_archive,
)
from campsverso_controller_runner.replay import ReplayRunner, recorded_proposals
from campsverso_controller_runner.runner import (
    ControllerRunner,
    SimTime,
    load_controller,
    load_mind,
)
from campsverso_mind import LlmController, Memory, MemorySettings
from campsverso_ports import EventBus, ModelPort


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_controller_runner.main")
    parser.add_argument("--env", type=Path, default=Path("config/env/local.yaml"))
    parser.add_argument("--world", type=Path, default=Path("config/worlds/farm-camps-01.yaml"))
    parser.add_argument("--avatar", default="camps")
    parser.add_argument("--nats-url", help="substitui nats.url do ambiente")
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--controller", help="nome do controlador (entry point), ex.: farmer")
    which.add_argument("--replay", type=Path, help="pasta do arquivo de eventos da sessão")
    which.add_argument(
        "--mind", help="nome da mente (entry point campsverso.minds), ex.: camps (ADR-0059)"
    )
    parser.add_argument("--replay-id", default="replay/sessao", help="controllerid do replay")
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("controller-runner")
    env, world = load_env(args.env), load_world(args.world)
    user = "mind" if args.mind is not None else "controller"
    password = os.environ.get(f"NATS_{user.upper()}_PASSWORD")
    if not password:
        telemetry.error("controller.no_credentials", user=user, hint="rode `make secrets`")
        return 2
    nats = await NatsBus.connect(
        args.nats_url or env.nats.url,
        user=user,
        password=password,
        name=f"{user}-{world.worldid}-{args.avatar}",
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
    elif args.mind is not None:
        settings = world.minds.get(args.avatar)
        if settings is None or settings.mind != args.mind:
            telemetry.error(
                "mind.not_configured",
                avatar=args.avatar,
                mind=args.mind,
                hint=f"minds.{args.avatar}.mind no arquivo do mundo (ADR-0059)",
            )
            await nats.close()
            return 2
        if settings.cassette_mode != "replay" and not os.environ.get("ANTHROPIC_API_KEY"):
            telemetry.error("mind.no_api_key", hint="ANTHROPIC_API_KEY no .env (ADR-0058)")
            await nats.close()
            return 2
        sim_time = SimTime()
        ref = {"type": "llm", "id": settings.id}
        # Em replay a fita basta: nem chave nem rede.
        inner: ModelPort | None = (
            None if settings.cassette_mode == "replay" else AnthropicModel(clock=clock)
        )
        recorder = RecordingModel(
            inner, settings.cassette_path, settings.cassette_mode, clock=clock
        )
        port = MeteredModel(
            recorder,
            bus=bus,
            worldid=world.worldid,
            cartridge=world.cartridge,
            controller=ref,
            prices=env.models,
            clock=clock,
            ids=ids,
            sim_clock=sim_time,
        )
        port.assert_priced(settings.model)
        if settings.reflection_model is not None:
            port.assert_priced(settings.reflection_model)
        memory: Memory | None = None
        if settings.memory_enabled:  # o caderno (ADR-0060): um arquivo por avatar, fora do snapshot
            memory_path = settings.memory_path or (
                env.data_dir / world.worldid / "memory" / f"{args.avatar}.sqlite"
            )
            memory = Memory(
                SqliteMemory(memory_path),
                args.avatar,
                MemorySettings(
                    reflection_model=settings.reflection_model,
                    reflection_effort=settings.reflection_effort,
                    reflection_max_tokens=settings.reflection_max_tokens,
                ),
            )
            telemetry.info("mind.memory", path=str(memory_path))
        controller = LlmController(
            load_mind(args.mind),
            port,
            controller_id=settings.id,
            avatar_id=args.avatar,
            model=settings.model,
            effort=settings.effort,
            max_tokens=settings.max_tokens,
            telemetry=telemetry,
            memory=memory,
        )
        runner = ControllerRunner(
            world.worldid,
            args.avatar,
            controller,
            bus,
            ids,
            clock,
            telemetry,
            cartridge=world.cartridge,
            possess=True,
            sim_time=sim_time,
        )
        telemetry.info(
            "mind.loaded",
            mind=args.mind,
            model=settings.model,
            effort=settings.effort,
            cassette=str(settings.cassette_path),
            mode=settings.cassette_mode,
        )
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
