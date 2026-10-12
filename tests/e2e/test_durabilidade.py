"""Critérios de pronto do M2 com processos e NATS de verdade (plano do M2 §4; escopo A6 e A7).

O kernel roda em modo contínuo a 5760x (um dia simulado em 15 s) e a referência é a mesma
configuração rodando sem queda, dentro do teste, pelo barramento em memória.
"""

import asyncio
import gzip
import json
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from campsverso_adapters import (
    ContractValidator,
    FakeWallClock,
    InMemoryBus,
    MemoryBlobStore,
    MemoryTelemetry,
    NatsBus,
    SequentialUuid7Ids,
    SqliteWorldStore,
    Uuid7Ids,
    ValidatingBus,
    load_env,
    load_world,
)
from campsverso_kernel import KernelService, open_world
from campsverso_kernel.main import prepare
from campsverso_ports import Envelope
from campsverso_testkit.hashing import canonical_hash
from campsverso_testkit.nats_server import REPO, NatsServer

ENV = REPO / "config" / "env" / "local.yaml"
WORLD = REPO / "config" / "worlds" / "farm-camps-01.yaml"
SCALE = 5760
DAY = 1440
EVENT_STREAMS = ("world", "agent", "observer", "internal")


def _spawn(
    module: str, args: Sequence[str], nats: NatsServer, logs: Path
) -> subprocess.Popen[bytes]:
    with (logs / f"{module}.log").open("ab") as log:
        return subprocess.Popen(
            [sys.executable, "-m", module, "--env", str(ENV), "--nats-url", nats.url, *args],
            cwd=REPO,
            env={**os.environ, **nats.env()},
            stdout=log,
            stderr=subprocess.STDOUT,
        )


def _kernel(nats: NatsServer, tmp: Path) -> subprocess.Popen[bytes]:
    args = ["--world", str(WORLD), "--data-dir", str(tmp / "data"), "--scale", str(SCALE)]
    return _spawn("campsverso_kernel.main", args, nats, tmp)


def _archiver(nats: NatsServer, tmp: Path) -> subprocess.Popen[bytes]:
    return _spawn("campsverso_archiver.main", ["--archive-dir", str(tmp / "archive")], nats, tmp)


def _stop(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


class Watcher:
    """Lê os streams como o operador, para acompanhar o progresso e conferir o resultado."""

    def __init__(self) -> None:
        self.events: list[Envelope] = []
        self.commands: list[Envelope] = []

    @classmethod
    async def start(cls, nats: NatsServer) -> tuple[Watcher, NatsBus]:
        watcher = cls()
        bus = await NatsBus.connect(
            nats.url,
            user="operator",
            password=nats.passwords["operator"],
            name="teste",
            streams=load_env(ENV, root=REPO).nats.streams,
            manage_streams=True,
        )

        async def events(batch: Sequence[tuple[str, Envelope]]) -> None:
            watcher.events += [envelope for _, envelope in batch]

        async def commands(batch: Sequence[tuple[str, Envelope]]) -> None:
            watcher.commands += [envelope for _, envelope in batch]

        for stream in EVENT_STREAMS:
            await bus.consume(f"campsverso.*.{stream}.>", f"teste-{stream}", events)
        await bus.consume("campsverso.*.cmd.>", "teste-cmd", commands)
        return watcher, bus

    def tick(self) -> int:
        return max((int(e["tick"]) for e in self.events), default=-1)

    def seq(self) -> int:
        return max((int(e["seq"]) for e in self.events), default=-1)

    async def until(self, condition: Callable[[], bool], timeout: float = 60) -> None:
        async with asyncio.timeout(timeout):
            while not condition():
                await asyncio.sleep(0.05)

    async def settle(self, quiet: float = 1.0) -> None:
        """Espera o fluxo parar: nenhum evento novo por `quiet` segundos."""
        seen = -1
        while seen != len(self.events):
            seen = len(self.events)
            await asyncio.sleep(quiet)


async def _reference(ticks: int) -> list[Envelope]:
    """O mesmo mundo, a mesma escala e o mesmo código, sem queda e sem processo à parte."""
    env, world = load_env(ENV, root=REPO), load_world(WORLD, root=REPO)
    prepared = prepare(env, world)
    store, blobs = SqliteWorldStore(":memory:"), MemoryBlobStore()
    engine, _ = open_world(
        prepared.definition,
        prepared.config,
        prepared.rules,
        prepared.version,
        store,
        blobs,
        rules_source=prepared.rules_source,
        validator=ContractValidator(),
    )
    engine.core.configure_clock(world.mode, SCALE, world.paused)
    bus = InMemoryBus()
    service = KernelService(
        engine,
        ValidatingBus(bus),
        FakeWallClock(),
        SequentialUuid7Ids(),
        store,
        blobs,
        MemoryTelemetry(),
    )
    await service.start()
    await service.run_ticks(ticks)
    return [envelope for _, envelope in bus.published]


async def test_a7_kill_9_no_kernel_no_meio_do_dia(nats: NatsServer, tmp_path: Path) -> None:
    reference = await _reference(DAY)
    last = int(reference[-1]["seq"])
    watcher, bus = await Watcher.start(nats)
    kernel = _kernel(nats, tmp_path)
    try:
        await watcher.until(lambda: watcher.tick() >= 700)
        kernel.kill()  # kill -9: sem snapshot de parada, sem fechar nada
        kernel.wait()
        killed_at = watcher.tick()
        kernel = _kernel(nats, tmp_path)
        await watcher.until(lambda: watcher.seq() >= last)
    finally:
        _stop(kernel)
        await bus.close()

    log = (tmp_path / "campsverso_kernel.main.log").read_text()
    assert '"event": "kernel.recovered"' in log
    assert 0 < killed_at < DAY
    seqs = sorted(int(e["seq"]) for e in watcher.events)
    assert seqs == list(range(len(seqs)))  # seq contínua: sem lacunas nem duplicatas
    prefix = sorted((e for e in watcher.events if int(e["seq"]) <= last), key=lambda e: e["seq"])
    assert canonical_hash(prefix) == canonical_hash(reference)  # igual a uma execução sem queda


def _archived(root: Path) -> list[dict[str, Any]]:
    lines: list[bytes] = []
    for path in sorted(root.rglob("*.jsonl*")):
        data = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
        lines += data.splitlines()
    return [json.loads(line) for line in lines]


async def test_a6_arquivador_cai_e_volta_sem_perder_nem_repetir(
    nats: NatsServer, tmp_path: Path
) -> None:
    watcher, bus = await Watcher.start(nats)
    kernel, archiver = _kernel(nats, tmp_path), _archiver(nats, tmp_path)
    command_id = Uuid7Ids().new_id()
    try:
        await watcher.until(lambda: watcher.tick() >= 400)
        archiver.kill()
        archiver.wait()
        await bus.publish(
            "campsverso.farm-camps-01.cmd.clock.set_scale.v1",
            {
                "specversion": "1.0",
                "id": command_id,
                "source": "/operator/teste",
                "type": "campsverso.cmd.clock.set_scale.v1",
                "time": "2026-10-12T01:00:00Z",
                "datacontenttype": "application/json",
                "dataschema": "contracts://commands/clock/set_scale.v1",
                "worldid": "farm-camps-01",
                "cartridge": "farm_camps",
                "seq": 0,
                "actor": "human/operator",
                "provenance": "simulated",
                "visibility": "observer",
                "data": {"scale": SCALE, "reason": "operator"},
            },
        )
        await watcher.until(lambda: watcher.tick() >= 900)
        archiver = _archiver(nats, tmp_path)
        await watcher.until(lambda: watcher.tick() >= DAY)
        _stop(kernel)  # parada elegante: o último snapshot também vai para o arquivo
        await watcher.settle()
        expected = {str(e["id"]) for e in watcher.events} | {command_id}
        await watcher.until(
            lambda: {str(e["id"]) for e in _archived(tmp_path / "archive")} >= expected, 30
        )
    finally:
        _stop(kernel)
        _stop(archiver)
        await bus.close()

    archived = _archived(tmp_path / "archive")
    ids = [str(e["id"]) for e in archived]
    assert len(ids) == len(set(ids))  # nada repetido, mesmo com a reentrega depois da queda
    assert set(ids) == expected  # nada perdido
    assert any(e["type"] == "campsverso.world.clock.scale_changed.v1" for e in archived)
    days = sorted(p.name for p in (tmp_path / "archive" / "farm-camps-01").iterdir())
    assert days == ["2026-10-10.jsonl", "2026-10-11.jsonl"]  # meia-noite simulada corta o arquivo
