"""Raiz de composição do controller-runner.

    uv run python -m campsverso_controller_runner.main --controller farmer
    uv run python -m campsverso_controller_runner.main --replay data/archive/farm-camps-01
    uv run python -m campsverso_controller_runner.main --mind camps
    uv run python -m campsverso_controller_runner.main --helpers --world config/worlds/<morada>.yaml

O script vem de um entry point do grupo `campsverso.controllers` (ADR-0011); a mente, do grupo
`campsverso.minds`, com o modelo, o esforço e a fita lidos de `minds.<avatar>` no arquivo do mundo
(ADR-0059), e a porta de modelo montada aqui: adaptador da Anthropic, fita e medidor (ADR-0058).
O replay lê as propostas de um arquivo de eventos gravado. Os ajudantes (ADR-0072) são vários
avatares num processo, um script de cada um, com a lista em `helpers.avatars` no arquivo do mundo;
sem ajudantes no mundo, o processo só espera. A senha do NATS vem de NATS_CONTROLLER_PASSWORD
(script e replay), NATS_MIND_PASSWORD (a mente) ou NATS_HELPERS_PASSWORD (os ajudantes).
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
    which.add_argument(
        "--helpers", action="store_true", help="os ajudantes do mundo, um script cada (ADR-0072)"
    )
    parser.add_argument("--replay-id", default="replay/sessao", help="controllerid do replay")
    return parser.parse_args(argv)


async def _until_stopped(
    runners: Sequence[ControllerRunner | ReplayRunner],
) -> BaseException | None:
    stop = asyncio.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(signum, stop.set)
    while not stop.is_set():
        failed = next((r.failure for r in runners if r.failure is not None), None)
        if failed is not None:
            return failed
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), 0.5)
    return None


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("controller-runner")
    env, world = load_env(args.env), load_world(args.world)
    if args.helpers and not world.helpers:
        # O Procfile sobe o processo em todo mundo; sem ajudantes, ele só espera o fim.
        telemetry.info("helpers.none", world=world.worldid)
        await _until_stopped(())
        return 0
    user = "mind" if args.mind is not None else "helpers" if args.helpers else "controller"
    password = os.environ.get(f"NATS_{user.upper()}_PASSWORD")
    if not password:
        telemetry.error("controller.no_credentials", user=user, hint="rode `make secrets`")
        return 2
    nats = await NatsBus.connect(
        args.nats_url or env.nats.url,
        user=user,
        password=password,
        name=f"{user}-{world.worldid}-{'ajudantes' if args.helpers else args.avatar}",
        streams=env.nats.streams,
        telemetry=telemetry,
    )
    bus: EventBus = ValidatingBus(nats) if env.validate_events else nats
    clock, ids = SystemWallClock(), Uuid7Ids()
    runners: list[ControllerRunner | ReplayRunner] = []
    if args.helpers:
        runners = [
            ControllerRunner(
                world.worldid,
                avatar,
                load_controller(world.helper_script, avatar),
                bus,
                ids,
                clock,
                telemetry,
            )
            for avatar in world.helpers
        ]
        telemetry.info("helpers.loaded", avatars=list(world.helpers), script=world.helper_script)
    elif args.replay is not None:
        recording = recorded_proposals(read_world_archive(args.replay), args.avatar)
        runners = [
            ReplayRunner(
                world.worldid, args.avatar, args.replay_id, recording, bus, ids, clock, telemetry
            )
        ]
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
        runners = [
            ControllerRunner(
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
        ]
        telemetry.info(
            "mind.loaded",
            mind=args.mind,
            model=settings.model,
            effort=settings.effort,
            cassette=str(settings.cassette_path),
            mode=settings.cassette_mode,
        )
    else:
        controller = load_controller(args.controller, args.avatar)
        runners = [
            ControllerRunner(world.worldid, args.avatar, controller, bus, ids, clock, telemetry)
        ]
    try:
        for each in runners:
            await each.start()
        telemetry.info("controller.running", avatars=[r.avatar_id for r in runners])
        failure = await _until_stopped(runners)
        if failure is not None:
            telemetry.error("controller.failed", error=repr(failure))
            return 1
        telemetry.info("controller.stopped")
    finally:
        for each in runners:
            await each.stop()
        await nats.close()
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(_parse(sys.argv[1:]))))


if __name__ == "__main__":
    main()
