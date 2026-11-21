"""Raiz de composição do supervisor do escritório vivo (ADR-0083).

    make escritorio   # uv run --env-file .env python -m campsverso_supervisor.main

O escritório vivo roda numa pasta só dele, `--home` (padrão: `../campsverso-vivo`, ao lado do
repositório de trabalho), que o git e a pasta de trabalho não tocam:

    a/ b/        as duas worktrees, presas num commit do origin/main; uma é a viva
    dados/       o mundo: o estado do kernel, a memória do dev, o gateway, a guarda, o publicador
    arquivo/     o registro histórico, que nunca se reescreve
    nats/        o JetStream
    versoes/     as três últimas cópias para a volta e o diário da troca (supervisor.jsonl)
    logs/        um log por processo de cada pilha
    estado.json  qual worktree está viva, o commit, os recusados e a troca em andamento

As senhas do NATS são geradas a cada subida. O `.env` chega pelo ambiente (`--env-file`), para a
mente que chama o modelo; o supervisor não o lê. A chave do App fica em `privado/`, que cada
worktree vê por um link.
"""

import argparse
import asyncio
import os
import signal
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from campsverso_adapters import JsonTelemetry, load_world
from campsverso_supervisor.cycle import Settings, Supervisor
from campsverso_supervisor.releases import GitReleases
from campsverso_supervisor.stack import DirVault, ProcessStacks, StackConfig, reap
from campsverso_supervisor.state import Journal


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="campsverso_supervisor.main")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="o repositório de trabalho")
    parser.add_argument("--home", type=Path, help="a pasta do escritório vivo")
    parser.add_argument("--world", default="config/worlds/office-campsverso-01.yaml")
    parser.add_argument("--port", type=int, default=8765, help="a porta do gateway")
    parser.add_argument("--nats-port", type=int, default=4232, help="a porta do NATS da pilha")
    parser.add_argument("--poll", type=float, default=60.0, help="segundos entre as voltas")
    parser.add_argument("--health", type=float, default=120.0, help="segundos de saúde na troca")
    parser.add_argument("--smoke", type=float, default=50.0, help="segundos de fumaça na cópia")
    parser.add_argument("--mind", help="a mente do dev, que chama o modelo (sem ela, o dev-script)")
    parser.add_argument(
        "--offline", action="store_true", help="preparar as worktrees sem rede (uv e pnpm)"
    )
    return parser.parse_args(argv)


def compose(args: argparse.Namespace) -> Supervisor:
    repo = args.repo.resolve()
    home = (args.home or repo.parent / "campsverso-vivo").resolve()
    world = load_world(repo / args.world, repo)
    config = StackConfig(
        world=args.world,
        data=home / "dados",
        archive=home / "arquivo",
        nats_store=home / "nats",
        logs=home / "logs",
        nats_bin=repo / ".tools" / "bin" / "nats-server",
        nats_port=args.nats_port,
        gateway_port=args.port,
        environ=dict(os.environ),
        pids=home / "pids.json",
        script=world.script,
        budget=world.budget is not None,
        codehost=world.codehost is not None,
        mind=args.mind,
        smoke_seconds=args.smoke,
    )
    releases = GitReleases(repo, links={"privado": repo / "privado"}, offline=args.offline)

    def now() -> datetime:
        return datetime.now().astimezone()

    return Supervisor(
        home,
        releases,
        ProcessStacks(home, config),
        DirVault(config.data, config.nats_store, home / "versoes", now),
        Journal(home / "versoes" / "supervisor.jsonl", now),
        Settings(poll_seconds=args.poll, health_seconds=args.health),
    )


async def run(args: argparse.Namespace) -> int:
    telemetry = JsonTelemetry("supervisor")
    supervisor = compose(args)
    if killed := reap(supervisor.home / "pids.json", str(supervisor.home)):
        telemetry.warning("supervisor.reaped", pids=killed)
    stop = asyncio.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(signum, stop.set)
    telemetry.info("supervisor.running", home=str(supervisor.home), port=args.port)
    try:
        await supervisor.run(stop)
    except Exception as error:
        telemetry.error("supervisor.failed", error=repr(error))
        return 1
    telemetry.info("supervisor.stopped", commit=supervisor.state.commit)
    return 0


def main() -> None:
    sys.exit(asyncio.run(run(_parse(sys.argv[1:]))))


if __name__ == "__main__":
    main()
