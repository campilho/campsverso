"""As mãos do Antigravity (ADR-0093): uma sessão do Antigravity CLI (`agy -p … --output-format
stream-json`) no espaço de um pedido, pelo motor comum dos harnesses de fora (`hands_process.py`).

O briefing vai no `-p`, e a saída é um JSON por linha (o formato em
`tests/fixtures/antigravity/README.md`, da documentação oficial e do ensaio do `agy` 1.5.14 no
cercado, em 23/nov):
- cada `step_update` de ferramenta que acabou (`state` `DONE`, ou `ERROR` quando ela falha) vira
  um passo para a tela, com o caminho quando um parâmetro trouxer um, e conta uma volta; o comando
  que sai com código diferente de zero, ou que nem roda, é um passo que falhou;
- cada resposta do modelo concluída conta uma volta;
- o `result` fecha a sessão, com o `response` (o resumo da entrega) e o `usage`, que fica em
  `last_usage` para conferir com a porta.

**O modelo passa pela porta das mãos,** na língua do Gemini: o `agy` usa a chave de API quando o
`settings.json` da casa dele diz `"modelProvider": "gemini"` e o `GEMINI_API_KEY` existe, e chama o
endereço do `GOOGLE_GEMINI_BASE_URL`. A casa fica dentro do espaço, a chave é a da sessão, e o
endereço é o da porta. O `agy` roda sem o `--sandbox` dele e com o `--dangerously-skip-permissions`:
sem interface, o que pediria aprovação seria negado em silêncio, e a cerca é o nosso `sandbox-exec`.

O `agy` roda um servidor de linguagem dentro dele e conversa com ele por uma porta local que ele
mesmo escolhe: o cercado precisa deixá-lo abrir e chamar portas locais (o ensaio de 23/nov).
"""

import json
import math
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from campsverso_adapters.hands_dialects import GeminiDialect
from campsverso_adapters.hands_fence import resolve_program
from campsverso_adapters.hands_gate import Dialect, HandsGate
from campsverso_adapters.hands_process import (
    MAX_SUMMARY,
    Outcome,
    ProcessHands,
    Read,
    Stream,
    clean_environment,
    first_line,
    relative,
)
from campsverso_ports import HandsJob, HandsStep

HARNESS = "antigravity"
# O esforço no fim do slug do `agy models` (`gemini-4-neon-high`); o `max` do escritório é o
# `xhigh`, o maior da lista.
SLUG_EFFORTS = {"low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh", "max": "xhigh"}
# O briefing vai como um argumento: abaixo do limite de um argumento no Linux (128 KiB).
MAX_PROMPT_BYTES = 120 * 1024
SETTINGS = Path(".gemini") / "antigravity-cli" / "settings.json"
# Os estados de um passo que acabou: o `DONE` e, na ferramenta que falha, o `ERROR`.
ENDED = ("DONE", "ERROR")
# A saída de um `run_command`: o código de saída, ou o motivo de o comando nem rodar.
EXIT_CODE = re.compile(r"^Command exited with code (-?\d+)\.", re.MULTILINE)
NOT_RUN = re.compile(r"^Command failed to run: (.+)$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class AntigravityUsage:
    """Os tokens do `result`, como o `agy` 1.5.14 os conta, somados na sessão: a entrada sem o
    que veio do cache (`cache_read_tokens`), a saída com o pensamento (`thinking_tokens`), e o
    total, a entrada mais a saída."""

    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0

    @staticmethod
    def of(raw: Mapping[str, Any]) -> AntigravityUsage:
        def get(name: str) -> int:
            value = raw.get(name)
            return value if isinstance(value, int) else 0

        return AntigravityUsage(
            get("input_tokens"),
            get("output_tokens"),
            get("thinking_tokens"),
            get("cache_read_tokens"),
            get("total_tokens"),
        )


def slug_of(model: str, effort: str | None) -> str:
    """O slug do `agy models`: o modelo com o esforço no fim, se ainda não tiver."""
    if effort is None or model.rpartition("-")[2] in SLUG_EFFORTS.values():
        return model
    return f"{model}-{SLUG_EFFORTS.get(effort, effort)}"


def api_model(slug: str) -> str:
    """O modelo da API por trás de um slug, sem o esforço: o nome da tabela de preços."""
    head, _, tail = slug.rpartition("-")
    return head if head and tail in SLUG_EFFORTS.values() else slug


def _mapping(value: object) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], value) if isinstance(value, Mapping) else {}


def _path_of(parameters: Mapping[str, Any], root: Path) -> str | None:
    """O caminho de uma ferramenta: o primeiro parâmetro cujo nome termina em `path` ou `file`
    (o `Path` do `read_file`, do `write_file` e do `edit_file`), relativo ao espaço."""
    for name, value in parameters.items():
        if name.lower().endswith(("path", "file")) and isinstance(value, str) and value:
            return relative(root, value)
    return None


def step_of(update: Mapping[str, Any], root: Path, ms: int) -> HandsStep:
    """O passo de uma ferramenta que acabou, para a tela: o nome, o comando ou o caminho numa
    linha e, na falha, a mensagem do erro. Falha a ferramenta com erro ou no estado `ERROR`, e o
    comando que sai com código diferente de zero ou que nem roda."""
    info = _mapping(update.get("tool_info"))
    name = str(update.get("tool_name") or info.get("name") or "ferramenta")
    parameters = _mapping(info.get("parameters"))
    path = _path_of(parameters, root)
    command = parameters.get("CommandLine")
    shown = isinstance(command, str) and command.strip()
    what = first_line(command) if shown and isinstance(command, str) else path or ""
    summary = f"{name}: {what}" if what else name
    error = _mapping(info.get("error"))
    output = info.get("output")
    text = output if isinstance(output, str) else ""
    not_run = NOT_RUN.search(text)
    exited = EXIT_CODE.search(text)
    message = str(error.get("message") or "") if error else ""
    if not message and not_run:
        message = not_run.group(1)
    if message:
        summary = f"{summary} (erro: {first_line(message, 120)})"
    ok = (
        not error
        and not_run is None
        and update.get("state") != "ERROR"
        and (exited is None or exited.group(1) == "0")
    )
    return HandsStep(name, summary[:MAX_SUMMARY], ok, ms, path)


class AntigravityStream:
    """O leitor da saída do `agy` em `stream-json`: os passos de ferramenta e as respostas viram
    passos e voltas, e o `result` fecha a sessão."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._texts: dict[int, str] = {}
        self._began: dict[int, float] = {}
        self.usage = AntigravityUsage()
        self.response = ""
        self.completed = False
        self.failed: str | None = None

    def account(self, data: Mapping[str, Any]) -> None:
        if data.get("event") != "result":
            return
        result = _mapping(data.get("result"))
        usage = result.get("usage")
        if isinstance(usage, Mapping):
            # Os tokens do `result` já são a soma da sessão.
            self.usage = AntigravityUsage.of(cast(Mapping[str, Any], usage))
        status = str(result.get("status") or "")
        self.response = str(result.get("response") or "")
        if status == "SUCCESS":
            self.completed = True
        else:
            self.failed = str(result.get("error") or status or "a sessão falhou")

    def read(self, data: Mapping[str, Any]) -> Read:
        if data.get("event") != "step_update":
            return Read()
        update = _mapping(data.get("step_update"))
        index = update.get("step_index")
        number = index if isinstance(index, int) else -1
        kind = update.get("step_type")
        done = update.get("state") in ENDED
        if kind == "agent_response":
            text = self._texts.get(number, "") + str(update.get("text_delta") or "")
            if not done:
                self._texts[number] = text
                return Read()
            self._texts.pop(number, None)
            return Read((), "message", text)
        if kind != "tool":
            return Read()
        if not done:
            self._began.setdefault(number, time.monotonic())
            return Read()
        start = self._began.pop(number, None)
        seconds = update.get("duration_seconds")
        if isinstance(seconds, int | float):
            ms = round(seconds * 1000)
        else:
            ms = 0 if start is None else round((time.monotonic() - start) * 1000)
        return Read((step_of(update, self._root, ms),), "tool")

    def closes(self, data: Mapping[str, Any]) -> bool:
        return data.get("event") == "result"


class AntigravityHands(ProcessHands):
    """As mãos do Antigravity. O conector acrescenta ao comando o `-p` com o briefing, o formato,
    o slug do modelo com o esforço, a aprovação de tudo, o fim das barras de comando e o limite de
    tempo do próprio `agy`. O `usage` do `result` fica em `last_usage`."""

    harness = HARNESS
    title = "Antigravity"
    program = "agy"
    last_usage = AntigravityUsage()

    def dialect(self) -> Dialect:
        return GeminiDialect()

    def priced_model(self, job: HandsJob) -> str:
        return self.dialect().priced(api_model(slug_of(job.model, job.effort)))

    def argv(self, root: Path, job: HandsJob) -> list[str]:
        prompt = f"{job.system}\n\n{job.opening}" if job.system else job.opening
        if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ValueError("o briefing passa do que cabe na linha de comando do Antigravity")
        command = resolve_program(self._command, root, "o Antigravity")
        return [
            *command,
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--model",
            slug_of(job.model, job.effort),
            "--dangerously-skip-permissions",
            "--disable-slash-commands",
            "--print-timeout",
            f"{max(1, math.ceil(job.limits.max_seconds))}s",
        ]

    def prepare(self, root: Path, gate: HandsGate, job: HandsJob) -> dict[str, str]:
        environment = clean_environment(root, "casa-agy")
        # A chave da sessão, que só vale na porta, e o endereço da porta.
        environment["GEMINI_API_KEY"] = gate.token
        environment["GOOGLE_GEMINI_BASE_URL"] = gate.url
        settings = Path(environment["HOME"]) / SETTINGS
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(json.dumps({"modelProvider": "gemini"}, indent=2), encoding="utf-8")
        return environment

    def stream(self, root: Path) -> Stream:
        return AntigravityStream(root)

    def finished(self, stream: Stream) -> None:
        if isinstance(stream, AntigravityStream):
            self.last_usage = stream.usage

    def summary(self, outcome: Outcome, stream: Stream) -> str:
        """O `response` do `result`; na sessão parada, a última resposta lida antes da parada,
        como no Codex (o que chega depois dela só conta os tokens)."""
        if outcome.stopped is None and isinstance(stream, AntigravityStream) and stream.response:
            return stream.response
        return outcome.last_text
