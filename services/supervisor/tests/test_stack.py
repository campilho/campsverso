"""As cópias dos dados para a volta e os processos que sobram de uma queda (ADR-0083). A pilha de
verdade sobe no ensaio do supervisor, fora do `make check`."""

import json
import subprocess
import sys
import threading
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from campsverso_supervisor.stack import DirVault, ProcessStack, StackConfig, free_port, reap


def test_a_copia_guarda_e_devolve_os_dados_e_o_nats_sem_a_oficina(tmp_path: Path) -> None:
    data, store = tmp_path / "dados", tmp_path / "nats"
    (data / "office-01").mkdir(parents=True)
    (data / "office-01" / "world.sqlite").write_text("antes")
    (data / "oficina" / "office-01" / "pedido-001").mkdir(parents=True)
    store.mkdir()
    (store / "stream").write_text("antes")
    moments = iter(
        datetime(2026, 11, 21, 3, 0, tzinfo=UTC) + timedelta(minutes=m) for m in range(9)
    )
    vault = DirVault(data, store, tmp_path / "versoes", lambda: next(moments))
    backup = vault.backup("1" * 40)
    assert backup.name == "20261121-030000-1111111"
    assert not (backup / "dados" / "oficina").exists()  # os clones do dev não vão para a cópia
    # A versão nova mexe em tudo; a volta devolve o de antes e deixa a oficina como está.
    (data / "office-01" / "world.sqlite").write_text("depois")
    (data / "novo").mkdir()
    (store / "stream").write_text("depois")
    vault.restore(backup)
    assert (data / "office-01" / "world.sqlite").read_text() == "antes"
    assert not (data / "novo").exists()
    assert (data / "oficina" / "office-01" / "pedido-001").is_dir()
    assert (store / "stream").read_text() == "antes"
    for _ in range(4):
        vault.backup("2" * 40)
    (tmp_path / "versoes" / "supervisor.jsonl").write_text("{}\n")
    vault.prune(3)
    kept = sorted(p.name for p in (tmp_path / "versoes").iterdir())
    assert kept == [
        "20261121-030200-2222222",
        "20261121-030300-2222222",
        "20261121-030400-2222222",
        "supervisor.jsonl",  # o diário fica
    ]


def test_os_processos_de_uma_queda_saem_so_os_do_escritorio(tmp_path: Path) -> None:
    marker = str(tmp_path / "vivo")
    ours = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", marker])
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    pids = tmp_path / "pids.json"
    pids.write_text(f'{{"vivo-a": {{"kernel": {ours.pid}, "gateway": {other.pid}}}}}')
    try:
        assert reap(pids, marker) == [ours.pid]
        assert ours.wait(timeout=5) != 0
        assert other.poll() is None  # o número herdado por outro processo não morre
        assert pids.read_text().strip() == "{}"
    finally:
        other.kill()
        other.wait()


async def test_o_aviso_vai_ao_gateway_da_pilha_e_nunca_derruba(tmp_path: Path) -> None:
    """A parte 5 do M25: o supervisor avisa as telas pelo `POST /aviso` do gateway da pilha."""
    received: list[dict[str, object]] = []

    class Gateway(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers["Content-Length"])
            received.append(json.loads(self.rfile.read(length)))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = HTTPServer(("127.0.0.1", 0), Gateway)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        config = StackConfig(
            world="w.yaml",
            data=tmp_path,
            archive=tmp_path,
            nats_store=tmp_path,
            logs=tmp_path,
            nats_bin=tmp_path / "nats-server",
            nats_port=1,
            gateway_port=server.server_address[1],
            environ={},
            pids=tmp_path / "pids.json",
        )

        def stack(port: int) -> ProcessStack:
            return ProcessStack(
                tmp_path,
                config,
                None,
                data=tmp_path,
                archive=tmp_path,
                nats_store=tmp_path,
                nats_port=1,
                gateway_port=port,
                label="vivo-a",
            )

        notice = {"kind": "troca", "text": "agora"}
        assert await stack(int(server.server_address[1])).notify(notice, tries=1)
        assert received == [notice]
        assert not await stack(free_port()).notify(notice, tries=2)  # ninguém ouvindo: só avisa
    finally:
        server.shutdown()
