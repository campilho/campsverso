"""Um Codex falso para os testes das mãos do Codex: imprime o `exemplo.jsonl`, linha a linha.

As opções vêm antes do `exec` que o conector acrescenta:
- `--dorme N`: espera N segundos depois da primeira linha (para o limite de tempo);
- `--ambiente ARQUIVO`: grava o ambiente do processo em JSON;
- `--entrada ARQUIVO`: grava o que chegou pela entrada padrão (o briefing);
- `--neto ARQUIVO`: abre um processo filho que dorme e grava o pid dele (para o grupo de processos);
- `--sem-ler 1`: não lê a entrada padrão (para o briefing dentro do limite de tempo);
- `--fica N`: depois do exemplo, fecha a saída e continua vivo por N segundos (para a espera do
  fim dentro do limite de tempo);
- `--chama-porta 1`: antes de cada item novo, chama o modelo como o Codex chama, pelo provedor do
  `config.toml` da casa (`CODEX_HOME`): o `POST /responses` em streaming, com a chave da variável
  do provedor. Uma recusa da porta vira um `turn.failed`, e o falso sai com 1;
- `--exemplo ARQUIVO`: imprime este exemplo no lugar do `exemplo.jsonl`;
- `--escreve-fora ARQUIVO`: tenta escrever ali, e segue se o cercado negar.

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
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from types import FrameType
from typing import Any, cast

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


def _call_gate() -> str | None:
    """Uma chamada ao modelo pelo provedor da sessão; o erro da porta, se houver."""
    home = Path(os.environ["CODEX_HOME"])
    config = tomllib.loads((home / "config.toml").read_text(encoding="utf-8"))
    provider = config["model_providers"][config["model_provider"]]
    body = {"model": config["model"], "input": [{"role": "user", "content": "x"}], "stream": True}
    request = urllib.request.Request(
        str(provider["base_url"]).rstrip("/") + "/responses",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {os.environ[provider['env_key']]}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=10) as response:
            response.read()
    except urllib.error.HTTPError as error:
        return error.read().decode("utf-8", errors="replace")
    return None


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
    if "--escreve-fora" in options:
        with contextlib.suppress(OSError):
            Path(options["--escreve-fora"]).write_text("fora", encoding="utf-8")
    example = Path(options.get("--exemplo", str(EXAMPLE)))
    lines = example.read_text(encoding="utf-8").splitlines()
    final = next(x for x in lines if json.loads(x).get("type") == "turn.completed")
    calls = "--chama-porta" in options
    seen: set[str] = set()
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
        event: dict[str, Any] = json.loads(line)
        item = cast(dict[str, Any], event.get("item") or {})
        ident = str(item.get("id") or "")
        if calls and ident and ident not in seen:
            seen.add(ident)
            refused = _call_gate()
            if refused is not None:
                _emit(json.dumps({"type": "turn.failed", "error": {"message": refused}}))
                return 1
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
