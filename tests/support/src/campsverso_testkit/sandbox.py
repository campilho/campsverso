"""Mundo descartável com tudo ligado, para testar e mostrar sem criar o mundo oficial (ADR-0050).

    make sandbox   # = uv run python -m campsverso_testkit.sandbox --out data/sandbox/<data-hora>

Sobe um NATS próprio e os cinco processos (kernel, percepção, script, arquivador e gateway) no modo
contínuo na escala 72, com tudo dentro da pasta `--out`. O gateway serve a UI compilada
(`make ui-build`) em http://127.0.0.1:8765/?view=operator. Ctrl+C derruba tudo; a pasta fica.

Com `--mind camps` (ADR-0059) sobem também a mente, que assume o Camps ao conectar, e a guarda de
orçamento; a fita da mente fica em `<out>/llm.jsonl`, gravando. Precisa de ANTHROPIC_API_KEY.

Com `--pausado`, o relógio começa parado: quem vai jogar assume o Camps antes do script agir e
retoma o relógio pela tela (a rodada do humano, ADR-0066).
"""

import argparse
import signal
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import yaml

from campsverso_testkit.nats_server import nats_server
from campsverso_testkit.soak import WORLD, Processes

PORT = 8765


def _world_file(
    out: Path, mind: str | None = None, source: Path = WORLD, *, paused: bool = False
) -> Path:
    world = yaml.safe_load(source.read_text(encoding="utf-8"))
    world["clock"] = {"mode": "continuous", "scale": 72, "paused": paused}
    minds = cast(dict[str, dict[str, Any]], world.get("minds") or {})
    for avatar, settings in list(minds.items()):
        if mind is not None and settings.get("mind") == mind:
            settings["cassette"] = {"path": str(out / "llm.jsonl"), "mode": "record"}
        elif mind is None:
            minds.pop(avatar)  # sem mente, a seção some: o sandbox fica igual ao de sempre
    path = out / "world.yaml"
    path.write_text(yaml.safe_dump(world, allow_unicode=True), encoding="utf-8")
    return path


def run(
    out: Path,
    port: int = PORT,
    mind: str | None = None,
    source: Path = WORLD,
    *,
    paused: bool = False,
) -> int:
    out.mkdir(parents=True, exist_ok=True)
    world = _world_file(out, mind, source, paused=paused)
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
        if mind is not None:
            processes.spawn(
                "budget",
                "campsverso_budget.main",
                "--world",
                str(world),
                "--data-dir",
                str(out / "data"),
            )
            processes.spawn(
                "mind", "campsverso_controller_runner.main", "--world", str(world), "--mind", mind
            )
            print(
                f"  mente: {mind} assume o Camps ao conectar (fita em {out / 'llm.jsonl'})",
                flush=True,
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
            processes.stop(*[n for n in ("mind", "budget") if n in processes.running])
            processes.stop("gateway", "controller", "perception", "archiver")
    return code


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.sandbox")
    parser.add_argument("--out", type=Path, required=True, help="pasta do mundo descartável")
    parser.add_argument("--port", type=int, default=PORT, help="porta do gateway")
    parser.add_argument("--mind", help="a mente que assume o Camps, ex.: camps (ADR-0059)")
    parser.add_argument("--world", type=Path, default=WORLD, help="o arquivo do mundo")
    parser.add_argument("--pausado", action="store_true", help="o relógio começa parado")
    args = parser.parse_args(argv)
    return run(args.out, args.port, args.mind, args.world, paused=args.pausado)


if __name__ == "__main__":
    sys.exit(main())
