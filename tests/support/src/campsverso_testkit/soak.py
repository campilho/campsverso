"""Resistência (A3) com processos de verdade: NATS, kernel em modo máximo, percepção, script e
arquivador, sem intervenção, por N dias simulados (ADR-0047, decisão 3).

    uv run python -m campsverso_testkit.soak --days 30 [--out data/soak/agora]

Ao fim, mostra o tempo real, a memória máxima de cada processo e as métricas da bíblia §13, lidas
do arquivo JSONL da própria execução. Nada vai para o mundo oficial: tudo fica na pasta `--out`.
"""

import argparse
import asyncio
import contextlib
import json
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from campsverso_adapters import NatsBus, load_env
from campsverso_ports import Envelope
from campsverso_testkit.nats_server import REPO, NatsServer, nats_server
from campsverso_tools.metrics import compute, read_archive

ENV = REPO / "config" / "env" / "local.yaml"
WORLD = REPO / "config" / "worlds" / "farm-camps-01.yaml"
DAY = 1440
STALL_SECONDS = 60  # sem nenhum tick novo por este tempo, é travamento


@dataclass
class SoakResult:
    days: int
    ok: bool
    reason: str
    real_seconds: float
    ticks: int
    max_rss_mb: dict[str, float] = field(default_factory=dict[str, float])
    metrics: dict[str, Any] = field(default_factory=dict[str, Any])
    out: str = ""


def _world_file(out: Path, river_bonus: bool) -> Path:
    world = yaml.safe_load(WORLD.read_text(encoding="utf-8"))
    world["clock"] = {"mode": "max", "paused": False}
    if not river_bonus:
        rules = REPO / "cartridges/farm_camps/sim/src/campsverso_farm_camps_sim/data/rules.yaml"
        flags = yaml.safe_load(rules.read_text(encoding="utf-8"))
        for rule in flags["rules"].values():
            rule["enabled"] = False
        (out / "rules.yaml").write_text(yaml.safe_dump(flags), encoding="utf-8")
        world["rules_file"] = str(out / "rules.yaml")
    path = out / "world.yaml"
    path.write_text(yaml.safe_dump(world, allow_unicode=True), encoding="utf-8")
    return path


async def _archive_settled(folder: Path, quiet: float = 1.0, limit: float = 20.0) -> None:
    """Espera o arquivador alcançar: os arquivos param de crescer por `quiet` segundos."""
    deadline, size, since = time.monotonic() + limit, -1, time.monotonic()
    while time.monotonic() < deadline:
        now = sum(p.stat().st_size for p in folder.rglob("*.jsonl*")) if folder.exists() else 0
        if now != size:
            size, since = now, time.monotonic()
        elif time.monotonic() - since >= quiet:
            return
        await asyncio.sleep(0.2)


class Processes:
    def __init__(self, nats: NatsServer, out: Path, world: Path) -> None:
        self.nats, self.out, self.world = nats, out, world
        self.running: dict[str, subprocess.Popen[bytes]] = {}
        self.max_rss: dict[str, float] = {}

    def spawn(self, name: str, module: str, *args: str) -> None:
        with (self.out / f"{name}.log").open("ab") as log:
            self.running[name] = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    module,
                    "--env",
                    str(ENV),
                    "--nats-url",
                    self.nats.url,
                    *args,
                ],
                cwd=REPO,
                env={**os.environ, **self.nats.env()},
                stdout=log,
                stderr=subprocess.STDOUT,
            )

    def start(self) -> None:
        world, data = str(self.world), str(self.out / "data")
        self.spawn(
            "archiver", "campsverso_archiver.main", "--archive-dir", str(self.out / "archive")
        )
        self.spawn("perception", "campsverso_perception.main", "--world", world, "--data-dir", data)
        self.spawn(
            "controller",
            "campsverso_controller_runner.main",
            "--world",
            world,
            "--controller",
            "farmer",
        )
        self.spawn("kernel", "campsverso_kernel.main", "--world", world, "--data-dir", data)

    def dead(self) -> list[str]:
        return [name for name, p in self.running.items() if p.poll() is not None]

    def sample_memory(self) -> None:
        for name, process in self.running.items():
            probe = subprocess.run(
                ["ps", "-o", "rss=", "-p", str(process.pid)],
                capture_output=True,
                text=True,
                check=False,
            )
            if probe.stdout.strip():
                rss = int(probe.stdout.strip()) / 1024
                self.max_rss[name] = round(max(self.max_rss.get(name, 0.0), rss), 1)

    def stop(self, *names: str) -> None:
        for name in names or tuple(self.running):
            process = self.running[name]
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


async def run(days: int, out: Path, *, river_bonus: bool = True, quiet: bool = False) -> SoakResult:
    out.mkdir(parents=True, exist_ok=True)
    world = _world_file(out, river_bonus)
    target = days * DAY
    with nats_server(out) as nats:
        bus = await NatsBus.connect(
            nats.url,
            user="operator",
            password=nats.passwords["operator"],
            name="soak",
            streams=load_env(ENV, root=REPO).nats.streams,
            manage_streams=True,
        )
        latest = {"tick": -1}

        async def watch(batch: Sequence[tuple[str, Envelope]]) -> None:
            for _, envelope in batch:
                tick = envelope.get("tick")
                if isinstance(tick, int) and tick > latest["tick"]:
                    latest["tick"] = tick

        await bus.consume("campsverso.*.world.>", "soak-world", watch)
        processes = Processes(nats, out, world)
        started = time.monotonic()
        result = SoakResult(days, False, "", 0.0, 0, out=str(out))
        processes.start()
        try:
            last_tick, last_change, reported = -1, time.monotonic(), 0
            while latest["tick"] < target:
                await asyncio.sleep(0.5)
                processes.sample_memory()
                if dead := processes.dead():
                    result.reason = f"processo caiu: {', '.join(dead)} (veja os .log em {out})"
                    break
                if latest["tick"] != last_tick:
                    last_tick, last_change = latest["tick"], time.monotonic()
                elif time.monotonic() - last_change > STALL_SECONDS:
                    result.reason = f"travou no tick {last_tick}"
                    break
                day = latest["tick"] // DAY
                if not quiet and day > reported:
                    reported = day
                    print(f"dia {day:3d} em {time.monotonic() - started:7.1f} s", flush=True)
            else:
                result.ok, result.reason = True, "ok"
        finally:
            result.real_seconds = round(time.monotonic() - started, 1)
            result.ticks = latest["tick"]
            processes.stop("kernel")  # parada elegante primeiro: o último snapshot vai ao arquivo
            await _archive_settled(out / "archive")
            processes.stop("controller", "perception", "archiver")
            with contextlib.suppress(Exception):
                await bus.close()
        result.max_rss_mb = processes.max_rss
    folder = out / "archive" / "farm-camps-01"
    if folder.exists():
        result.metrics = compute(read_archive(folder)).totals()
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.soak")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--out", type=Path, help="pasta da execução (padrão: uma pasta temporária)")
    parser.add_argument("--sem-regra", action="store_true", help="desliga a regra oculta R-001")
    args = parser.parse_args(argv)
    out = args.out or Path(tempfile.mkdtemp(prefix="campsverso-soak-"))
    result = asyncio.run(run(args.days, out, river_bonus=not args.sem_regra))
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
