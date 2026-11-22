"""Um Codex falso para os testes das mãos do Codex: imprime o `exemplo.jsonl`, linha a linha.

As opções vêm antes do `exec` que o conector acrescenta:
- `--dorme N`: espera N segundos depois da primeira linha (para o limite de tempo);
- `--ambiente ARQUIVO`: grava o ambiente do processo em JSON;
- `--entrada ARQUIVO`: grava o que chegou pela entrada padrão (o briefing);
- `--neto ARQUIVO`: abre um processo filho que dorme e grava o pid dele (para o grupo de processos);
- `--sem-ler 1`: não lê a entrada padrão (para o briefing dentro do limite de tempo).
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

EXAMPLE = Path(__file__).with_name("exemplo.jsonl")


def main(argv: list[str]) -> int:
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
    if "--sem-ler" in options:
        time.sleep(60)
    received = sys.stdin.read()
    if "--entrada" in options:
        Path(options["--entrada"]).write_text(received, encoding="utf-8")
    pause = float(options.get("--dorme", "0"))
    for index, line in enumerate(EXAMPLE.read_text(encoding="utf-8").splitlines()):
        print(line, flush=True)
        if index == 0 and pause:
            time.sleep(pause)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
