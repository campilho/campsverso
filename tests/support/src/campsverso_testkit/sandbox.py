"""Mundo descartável com tudo ligado, para testar e mostrar sem criar o mundo oficial (ADR-0050).

    make sandbox   # = uv run python -m campsverso_testkit.sandbox --out data/sandbox/<data-hora>

Sobe um NATS próprio e os cinco processos (kernel, percepção, script, arquivador e gateway) no modo
contínuo na escala 72, com tudo dentro da pasta `--out`. O gateway serve a UI compilada
(`make ui-build`) em http://127.0.0.1:8765/?view=operator. Ctrl+C derruba tudo; a pasta fica.
"""

import argparse
import signal
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import yaml

from campsverso_testkit.nats_server import nats_server
from campsverso_testkit.soak import WORLD, Processes

PORT = 8765


def _world_file(out: Path) -> Path:
    world = yaml.safe_load(WORLD.read_text(encoding="utf-8"))
    world["clock"] = {"mode": "continuous", "scale": 72, "paused": False}
    path = out / "world.yaml"
    path.write_text(yaml.safe_dump(world, allow_unicode=True), encoding="utf-8")
    return path


def run(out: Path, port: int = PORT) -> int:
    out.mkdir(parents=True, exist_ok=True)
    world = _world_file(out)
    stop = {"now": False}

    def interrupt(_signum: int, _frame: object) -> None:
        stop["now"] = True

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    with nats_server(out) as nats:
        processes = Processes(nats, out, world)
        processes.start()
        processes.spawn(
            "gateway",
            "campsverso_gateway.main",
            "--world",
            str(world),
            "--data-dir",
            str(out / "data"),
            "--port",
            str(port),
        )
        print(f"sandbox em {out}", flush=True)
        print(f"  operador: http://127.0.0.1:{port}/?view=operator", flush=True)
        print(f"  jogador:  http://127.0.0.1:{port}/?view=player", flush=True)
        print("  Ctrl+C para parar (os logs ficam na pasta)", flush=True)
        code = 0
        try:
            while not stop["now"]:
                if dead := processes.dead():
                    print(f"processo caiu: {', '.join(dead)} (veja os .log em {out})", flush=True)
                    code = 1
                    break
                time.sleep(0.5)
        finally:
            processes.stop("kernel")  # parada elegante primeiro: o último snapshot vai ao arquivo
            processes.stop("gateway", "controller", "perception", "archiver")
    return code


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.sandbox")
    parser.add_argument("--out", type=Path, required=True, help="pasta do mundo descartável")
    parser.add_argument("--port", type=int, default=PORT, help="porta do gateway")
    args = parser.parse_args(argv)
    return run(args.out, args.port)


if __name__ == "__main__":
    sys.exit(main())
