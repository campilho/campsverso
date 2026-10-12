"""NATS de verdade para testes: o binário de `make tools` com o `nats.conf` do repositório.

Cada teste sobe o seu servidor numa porta livre, com pasta própria e senhas geradas na hora.
Sem o binário (ninguém rodou `make tools`), os testes que precisam dele são pulados.
"""

import os
import secrets
import socket
import subprocess
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
NATS_BIN = REPO / ".tools" / "bin" / "nats-server"
NATS_CONF = REPO / "config" / "nats" / "nats.conf"
ROLES = ("kernel", "archiver", "perception", "controller", "gateway", "operator")


@dataclass(frozen=True)
class NatsServer:
    url: str
    passwords: dict[str, str]
    store_dir: Path

    def env(self) -> dict[str, str]:
        """Variáveis de ambiente com as senhas, como o .env de `make secrets`."""
        return {f"NATS_{role.upper()}_PASSWORD": pw for role, pw in self.passwords.items()}


def available() -> bool:
    return NATS_BIN.exists()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_ready(port: int, process: subprocess.Popen[bytes], timeout: float = 10) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"o nats-server saiu com código {process.returncode}")
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise TimeoutError("o nats-server não ficou pronto")


@contextmanager
def nats_server(directory: Path) -> Generator[NatsServer]:
    port = _free_port()
    store = directory / "jetstream"
    server = NatsServer(
        url=f"nats://127.0.0.1:{port}",
        passwords={role: secrets.token_hex(16) for role in ROLES},
        store_dir=store,
    )
    process = subprocess.Popen(
        [str(NATS_BIN), "-c", str(NATS_CONF), "-p", str(port), "-sd", str(store)],
        env={**os.environ, **server.env()},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_ready(port, process)
        yield server
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
