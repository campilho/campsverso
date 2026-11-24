"""Mundo descartável com tudo ligado, para testar e mostrar sem criar o mundo oficial (ADR-0050).

    make sandbox   # = uv run python -m campsverso_testkit.sandbox --out data/sandbox/<data-hora>

Sobe um NATS próprio e os cinco processos (kernel, percepção, script, arquivador e gateway) no modo
contínuo na escala 72, com tudo dentro da pasta `--out`. O gateway serve a UI compilada
(`make ui-build`) em http://127.0.0.1:8765/?view=operator. Ctrl+C derruba tudo; a pasta fica.

Com `--mind camps` (ADR-0059) sobem também a mente, que assume o Camps ao conectar, e a guarda de
orçamento; a fita da mente fica em `<out>/llm.jsonl`, gravando. Precisa de ANTHROPIC_API_KEY.

Com `--pausado`, o relógio começa parado: quem vai jogar assume o Camps antes do script agir e
retoma o relógio pela tela (a rodada do humano, ADR-0066).

Com `--jogar` (`make jogar`), é o sandbox de quem joga: começa pausado, e a tela do jogador, aberta
pelo endereço que ele imprime (`&assumir=1`), assume o Camps sozinha; o script não age antes (achado
do usuário no mapa d: o `make sandbox` sem `PAUSADO=1` deixou o script cavar um canteiro).

Com `--github` (ADR-0083), o sandbox do escritório publica as entregas do dev no GitHub de
verdade, com o `codehost` do escritório vivo: cada entrega abre um PR público. A chave do App vem
de privado/, ou de `--chave`. Sem ele, o mundo do sandbox não tem `codehost`, e as entregas ficam
na pasta, como no M24.

    make sandbox MUNDO=office-campsverso-demo GITHUB=1 [CHAVE=<caminho da chave>]

Com `--retomar`, a pasta `--out` já tem um mundo: o sandbox sobe sobre ela, sem regravar o arquivo
do mundo, e o kernel continua do último snapshot e do diário de entradas (a recuperação da
ADR-0044), com o relógio como estava. Quem pausa antes do Ctrl+C volta pausado: é como o humano
joga um ano em várias noites (ADR-0074, decisão 16).

    make sandbox RETOMAR=data/sandbox/<pasta>
"""

import argparse
import re
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
LIVE_OFFICE = WORLD.parent / "office-campsverso-02.yaml"  # o `codehost` do escritório vivo


def mind_names(text: str | None) -> list[str]:
    """As mentes de `--mind`, separadas por vírgula (ADR-0093): uma por dev, cada uma no processo
    dela."""
    return [name.strip() for name in (text or "").split(",") if name.strip()]


def _world_file(
    out: Path,
    mind: str | None = None,
    source: Path = WORLD,
    *,
    paused: bool = False,
    github: bool = False,
) -> Path:
    world = yaml.safe_load(source.read_text(encoding="utf-8"))
    if github:
        live = yaml.safe_load(LIVE_OFFICE.read_text(encoding="utf-8"))
        # Os ramos de um sandbox são só dele: o escritório vivo e outro sandbox também têm um
        # pedido 1, e o ramo `dev/pedido-1` é do vivo (ADR-0083).
        name = re.sub(r"[^a-z0-9._-]", "-", out.name.lower()).strip("-.") or "sandbox"
        world["codehost"] = {**live["codehost"], "branch_prefix": f"dev/sandbox-{name}/"}
    clock = cast(dict[str, Any], world.get("clock") or {})
    if clock.get("anchor") == "wall":
        # O escritório anda em tempo real e, ao subir, salta até agora (ADR-0078): o relógio fica.
        world["clock"] = {**clock, "paused": paused}
    else:
        world["clock"] = {"mode": "continuous", "scale": 72, "paused": paused}
    minds = cast(dict[str, dict[str, Any]], world.get("minds") or {})
    wanted = mind_names(mind)
    for avatar, settings in list(minds.items()):
        if settings.get("mind") in wanted:
            # Uma fita por mente; com uma só, a de sempre (ADR-0093).
            tape = "llm.jsonl" if len(wanted) == 1 else f"llm-{avatar}.jsonl"
            settings["cassette"] = {"path": str(out / tape), "mode": "record"}
        else:
            minds.pop(avatar)  # a mente que não sobe sai da seção: o dev fica com o dev-script
    path = out / "world.yaml"
    path.write_text(yaml.safe_dump(world, allow_unicode=True), encoding="utf-8")
    return path


def world_of(
    out: Path,
    mind: str | None = None,
    source: Path = WORLD,
    *,
    paused: bool = False,
    resume: bool = False,
    github: bool = False,
) -> Path:
    """O arquivo do mundo do sandbox: o de uma pasta que já tem mundo (`resume`), ou um novo."""
    if resume:
        world = out / "world.yaml"
        if not world.is_file():
            raise FileNotFoundError(f"{out} não tem um mundo de sandbox para retomar")
        return world
    out.mkdir(parents=True, exist_ok=True)
    return _world_file(out, mind, source, paused=paused, github=github)


def run(
    out: Path,
    port: int = PORT,
    mind: str | None = None,
    source: Path = WORLD,
    *,
    paused: bool = False,
    resume: bool = False,
    play: bool = False,
    github: bool = False,
    key: Path | None = None,
) -> int:
    world = world_of(out, mind, source, paused=paused or play, resume=resume, github=github)
    publishes = yaml.safe_load(world.read_text(encoding="utf-8")).get("codehost") is not None
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
            "--relogio-do-jogador",  # quem joga o sandbox também pausa (ADR-0074)
        )
        wanted = mind_names(mind)
        if wanted:
            processes.spawn(
                "budget",
                "campsverso_budget.main",
                "--world",
                str(world),
                "--data-dir",
                str(out / "data"),
            )
            for name in wanted:
                processes.spawn(
                    "mind" if len(wanted) == 1 else f"mind-{name}",
                    "campsverso_controller_runner.main",
                    "--world",
                    str(world),
                    "--mind",
                    name,
                    "--data-dir",  # a oficina e as entregas da mente do escritório (ADR-0080)
                    str(out / "data"),
                )
                print(f"  mente: {name} assume o dev dela ao conectar (fitas em {out})", flush=True)
        if publishes:  # o publicador e o vigia do GitHub (ADR-0083)
            chave = () if key is None else ("--key", str(key.resolve()))
            processes.spawn(
                "codehost",
                "campsverso_codehost.main",
                "--world",
                str(world),
                "--data-dir",
                str(out / "data"),
                *chave,
            )
            print("  GitHub: cada entrega do dev abre um PR (veja codehost.log)", flush=True)
        print(f"sandbox {'retomado ' if resume else ''}em {out}", flush=True)
        print(f"  operador: http://127.0.0.1:{port}/?view=operator", flush=True)
        player = f"http://127.0.0.1:{port}/?view=player{'&assumir=1' if play else ''}"
        print(f"  jogador:  {player}", flush=True)
        if play:
            print("  a tela do jogador assume o Camps; retome o relógio com P", flush=True)
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
            minds = [n for n in processes.running if n == "mind" or n.startswith("mind-")]
            processes.stop(*minds, *[n for n in ("budget", "codehost") if n in processes.running])
            processes.stop(*[n for n in ("helpers",) if n in processes.running])
            processes.stop("gateway", "controller", "perception", "archiver")
    return code


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="campsverso_testkit.sandbox")
    parser.add_argument("--out", type=Path, required=True, help="pasta do mundo descartável")
    parser.add_argument("--port", type=int, default=PORT, help="porta do gateway")
    parser.add_argument(
        "--mind",
        help="as mentes, separadas por vírgula: camps na fazenda (ADR-0059); no escritório,"
        " tiago_escritorio,kenji_escritorio (ADR-0093)",
    )
    parser.add_argument("--world", type=Path, default=WORLD, help="o arquivo do mundo")
    parser.add_argument("--pausado", action="store_true", help="o relógio começa parado")
    parser.add_argument(
        "--jogar", action="store_true", help="pausado, e a tela do jogador assume o Camps ao abrir"
    )
    parser.add_argument(
        "--retomar", action="store_true", help="continua o mundo que já está em --out"
    )
    parser.add_argument(
        "--github", action="store_true", help="as entregas do dev viram PRs no GitHub (ADR-0083)"
    )
    parser.add_argument("--chave", type=Path, help="a chave do App, fora de privado/")
    args = parser.parse_args(argv)
    return run(
        args.out,
        args.port,
        args.mind,
        args.world,
        paused=args.pausado,
        resume=args.retomar,
        play=args.jogar,
        github=args.github,
        key=args.chave,
    )


if __name__ == "__main__":
    sys.exit(main())
