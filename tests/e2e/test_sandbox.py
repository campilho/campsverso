"""O arquivo do mundo do sandbox; o começo parado é da rodada do humano (ADR-0066), e a retomada,
do ano dela em várias noites (ADR-0074)."""

import json
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import cast

import pytest
import yaml

from campsverso_testkit import sandbox
from campsverso_testkit.nats_server import REPO

BOAVISTA = Path(__file__).parents[2] / "config" / "worlds" / "farm-boavista-01.yaml"


def test_o_sandbox_pausado_comeca_com_o_relogio_parado(tmp_path: Path) -> None:
    write = sandbox._world_file  # pyright: ignore[reportPrivateUsage]
    parado = yaml.safe_load(write(tmp_path, source=BOAVISTA, paused=True).read_text("utf-8"))
    assert parado["clock"] == {"mode": "continuous", "scale": 72, "paused": True}
    assert not parado.get("minds")  # sem mente, nenhuma mente sobe
    andando = yaml.safe_load(write(tmp_path, source=BOAVISTA).read_text("utf-8"))
    assert andando["clock"]["paused"] is False


def test_retomar_pede_uma_pasta_com_mundo(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="não tem um mundo"):
        sandbox.world_of(tmp_path, resume=True)


def _start(out: Path, *extra: str) -> subprocess.Popen[bytes]:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
    command = [sys.executable, "-m", "campsverso_testkit.sandbox", "--out", str(out)]
    return subprocess.Popen(
        [*command, "--port", str(port), *extra],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _stop(process: subprocess.Popen[bytes]) -> None:
    process.send_signal(signal.SIGINT)  # como o Ctrl+C: o kernel grava o último snapshot
    process.wait(timeout=60)


def _wait_for(log: Path, event: str, timeout: float = 60) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if log.is_file():
            for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
                if f'"event": "{event}"' in line:
                    return cast(dict[str, object], json.loads(line))
        time.sleep(0.2)
    raise AssertionError(f"{event} não apareceu em {log}")


def test_o_sandbox_parado_e_retomado_continua_do_mesmo_mundo(tmp_path: Path) -> None:
    """ADR-0074, decisão 16: o humano joga um ano em várias noites."""
    out = tmp_path / "sandbox"
    first = _start(out)
    try:
        _wait_for(out / "kernel.log", "kernel.running")
        time.sleep(3)  # uns ticks a 72x
    finally:
        _stop(first)
    world = (out / "world.yaml").read_text(encoding="utf-8")
    second = _start(out, "--retomar")
    try:
        recovered = _wait_for(out / "kernel.log", "kernel.recovered")
    finally:
        _stop(second)
    assert (out / "world.yaml").read_text(encoding="utf-8") == world  # o arquivo não se regrava
    assert int(cast(int, recovered["to_tick"])) > 0  # continua de onde parou, não do zero
