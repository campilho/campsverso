"""Um Codex falso para os testes das mãos do Codex: imprime o `exemplo.jsonl`, linha a linha.

As opções vêm antes do `exec` que o conector acrescenta:
- `--dorme N`: espera N segundos depois da primeira linha (para o limite de tempo);
- `--ambiente ARQUIVO`: grava o ambiente do processo em JSON;
- `--entrada ARQUIVO`: grava o que chegou pela entrada padrão (o briefing);
- `--neto ARQUIVO`: abre um processo filho que dorme e grava o pid dele (para o grupo de processos);
- `--sem-ler 1`: não lê a entrada padrão (para o briefing dentro do limite de tempo);
- `--fica N`: depois do exemplo, fecha a saída e continua vivo por N segundos (para a espera do
  fim dentro do limite de tempo).

No SIGTERM, como o Codex de verdade, o falso entrega o `turn.completed` (se ainda não entregou) e
sai. O sinal só marca a parada; quem escreve é sempre o laço principal, entre uma linha e outra,
então uma linha nunca sai pela metade e o `usage` nunca sai duas vezes.
"""

import contextlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import FrameType

EXAMPLE = Path(__file__).with_name("exemplo.jsonl")
TICK = 0.02

stopping = False


def _on_term(_signum: int, _frame: FrameType | None) -> None:
    global stopping
    stopping = True


def _wait(seconds: float) -> None:
    """Dorme em pedaços, até o prazo ou até o SIGTERM."""
    deadline = time.monotonic() + seconds
    while not stopping and time.monotonic() < deadline:
        time.sleep(TICK)


def _emit(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def main(argv: list[str]) -> int:
    signal.signal(signal.SIGTERM, _on_term)
    options: dict[str, str] = {}
    rest = list(argv)
    while rest and rest[0].startswith("--") and rest[0] != "--json":
        options[rest[0]] = rest[1]
        rest = rest[2:]
    if "--ambiente" in options:
        Path(options["--ambiente"]).write_text(json.dumps(dict(os.environ)), encoding="utf-8")
    if "--neto" in options:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        Path(options["--neto"]).write_text(str(child.pid), encoding="utf-8")
    lines = EXAMPLE.read_text(encoding="utf-8").splitlines()
    final = next(x for x in lines if json.loads(x).get("type") == "turn.completed")
    delivered = False
    if "--sem-ler" in options:
        _wait(60)
    else:
        received = sys.stdin.read()
        if "--entrada" in options:
            Path(options["--entrada"]).write_text(received, encoding="utf-8")
    pause = float(options.get("--dorme", "0"))
    for index, line in enumerate(lines):
        if stopping:
            break
        _emit(line)
        delivered = delivered or line == final
        if index == 0 and pause:
            _wait(pause)
    if stopping:
        if not delivered:
            _emit(final)
        return 0
    if "--fica" in options:
        sys.stdout.close()
        with contextlib.suppress(OSError):
            os.close(1)
        _wait(float(options["--fica"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
