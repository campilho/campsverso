"""Um Antigravity CLI falso para os testes das mãos do Antigravity: imprime o `exemplo.jsonl`,
linha a linha, com o `{espaco}` trocado pela pasta onde roda.

As opções do falso vêm antes do `-p` que o conector acrescenta:
- `--dorme N`: espera N segundos depois da primeira linha (para o limite de tempo);
- `--ambiente ARQUIVO`: grava o ambiente do processo em JSON;
- `--entrada ARQUIVO`: grava o pedido que chegou pelo `-p` (o briefing);
- `--argumentos ARQUIVO`: grava os argumentos do `agy`, do `-p` em diante;
- `--neto ARQUIVO`: abre um processo filho que dorme e grava o pid dele (para o grupo de processos);
- `--chama-porta 1`: antes de cada passo novo do modelo (uma resposta ou uma ferramenta), chama o
  modelo como o `agy` com a chave de API: o `streamGenerateContent` no `GOOGLE_GEMINI_BASE_URL`,
  com o `GEMINI_API_KEY` no `x-goog-api-key`. Uma recusa da porta vira um `result` com o `status`
  `ERROR`, e o falso sai com 1;
- `--exemplo ARQUIVO`: imprime este exemplo no lugar do `exemplo.jsonl`;
- `--escreve-fora ARQUIVO`: tenta escrever ali, e segue se o cercado negar.

No SIGTERM, o falso entrega um `result` com o `status` `CANCELED` e os tokens do exemplo (se ainda
não entregou o fim) e sai. O sinal só marca a parada; quem escreve é sempre o laço principal.
"""

import contextlib
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from types import FrameType
from typing import Any, cast

EXAMPLE = Path(__file__).with_name("exemplo.jsonl")
TICK = 0.02
EFFORTS = ("low", "medium", "high", "xhigh")
MODEL_STEPS = ("agent_response", "tool")

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


def _call_gate(model: str) -> str | None:
    """Uma chamada ao modelo pelo endereço e a chave do ambiente; o erro da porta, se houver."""
    base = os.environ["GOOGLE_GEMINI_BASE_URL"].rstrip("/")
    body = {"contents": [{"role": "user", "parts": [{"text": "x"}]}]}
    request = urllib.request.Request(
        f"{base}/v1beta/models/{model}:streamGenerateContent?alt=sse",
        data=json.dumps(body).encode(),
        headers={
            "x-goog-api-key": os.environ["GEMINI_API_KEY"],
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


def _api_model(slug: str) -> str:
    """O modelo da API por trás do slug do `agy models`: sem o esforço no fim."""
    head, _, tail = slug.rpartition("-")
    return head if head and tail in EFFORTS else slug


def main(argv: list[str]) -> int:
    signal.signal(signal.SIGTERM, _on_term)
    options: dict[str, str] = {}
    rest = list(argv)
    while rest and rest[0] != "-p":
        options[rest[0]] = rest[1]
        rest = rest[2:]
    arguments = dict(zip(rest[::2], rest[1::2], strict=False))
    if "--argumentos" in options:
        Path(options["--argumentos"]).write_text(json.dumps(rest), encoding="utf-8")
    if "--entrada" in options:
        Path(options["--entrada"]).write_text(arguments.get("-p", ""), encoding="utf-8")
    if "--ambiente" in options:
        Path(options["--ambiente"]).write_text(json.dumps(dict(os.environ)), encoding="utf-8")
    if "--neto" in options:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        Path(options["--neto"]).write_text(str(child.pid), encoding="utf-8")
    if "--escreve-fora" in options:
        with contextlib.suppress(OSError):
            Path(options["--escreve-fora"]).write_text("fora", encoding="utf-8")
    model = _api_model(arguments.get("--model", "gemini-4-neon-high"))
    example = Path(options.get("--exemplo", str(EXAMPLE)))
    here = os.getcwd()
    lines = [x.replace("{espaco}", here) for x in example.read_text(encoding="utf-8").splitlines()]
    final = next((x for x in lines if json.loads(x).get("event") == "result"), None)
    calls = "--chama-porta" in options
    seen: set[int] = set()
    delivered = False
    pause = float(options.get("--dorme", "0"))
    for index, line in enumerate(lines):
        if stopping:
            break
        event: dict[str, Any] = json.loads(line)
        step = cast(dict[str, Any], event.get("step_update") or {})
        number = step.get("step_index")
        if calls and isinstance(number, int) and number not in seen:
            seen.add(number)
            if step.get("step_type") in MODEL_STEPS:
                refused = _call_gate(model)
                if refused is not None:
                    error = {"status": "ERROR", "error": refused, "num_turns": 1}
                    _emit(json.dumps({"event": "result", "result": error}))
                    return 1
        _emit(line)
        delivered = delivered or line == final
        if index == 0 and pause:
            _wait(pause)
    if stopping:
        if not delivered and final is not None:
            result = cast(dict[str, Any], json.loads(final)["result"])
            canceled = {**result, "status": "CANCELED", "response": ""}
            _emit(json.dumps({"event": "result", "result": canceled}, ensure_ascii=False))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
