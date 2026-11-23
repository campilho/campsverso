"""As mãos do Codex (ADR-0089, decisão 11; ADR-0093): uma sessão do `codex exec --json` no espaço de
um pedido, pelo motor comum dos harnesses de fora (`hands_process.py`).

O briefing vai pela entrada padrão, e a saída é um JSON por linha (o formato em
`tests/fixtures/codex/README.md`):
- cada item de ferramenta concluído (`command_execution`, `file_change`, `mcp_tool_call`,
  `web_search`) vira um passo para a tela, com o caminho quando houver;
- cada `agent_message` é uma volta, e a última é o resumo da entrega;
- o `turn.completed` fecha a sessão, com o `usage`, que fica em `last_usage` para conferir com a
  porta.

**O modelo passa pela porta das mãos,** na língua da OpenAI: o `config.toml` da sessão, na casa do
Codex dentro do espaço, aponta um provedor próprio para a porta, com a chave da sessão. O sandbox e
as aprovações do Codex ficam desligados: a cerca é o nosso `sandbox-exec`, porque o macOS não deixa
um sandbox dentro do outro.

O Codex é achado pelo `PATH` de quem chama, nunca pelo do espaço: um `codex` escrito no espaço não
roda no lugar dele, e o interpretador de um lançador do `env` também vem de fora.
"""

import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from campsverso_adapters.hands_dialects import OpenAIDialect
from campsverso_adapters.hands_fence import resolve_program
from campsverso_adapters.hands_gate import Dialect, HandsGate
from campsverso_adapters.hands_process import (
    MAX_SUMMARY,
    ProcessHands,
    Read,
    Stream,
    first_line,
    relative,
)
from campsverso_adapters.hands_process import clean_environment as _clean
from campsverso_ports import HandsJob, HandsStep

HARNESS = "codex"
TOOL_ITEMS = ("command_execution", "file_change", "mcp_tool_call", "web_search")
# Os eventos que fecham a volta: uma mensagem seguida de um deles era a resposta final.
TURN_ENDS = ("turn.completed", "turn.failed")
# O provedor da sessão no `config.toml` e a variável com a chave da sessão (que não é segredo: só
# vale na porta, enquanto a sessão dura).
PROVIDER = "campsverso"
SESSION_VARIABLE = "CAMPSVERSO_SESSAO"
# O esforço do escritório no do Codex, que não tem o `max`.
EFFORTS = {"low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh", "max": "xhigh"}


@dataclass(frozen=True, slots=True)
class CodexUsage:
    """Os tokens no sentido da OpenAI, como o Codex os conta: `input_tokens` já inclui o que veio
    do cache, e `output_tokens` já inclui o raciocínio."""

    input_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0

    def plus(self, raw: Mapping[str, Any]) -> CodexUsage:
        def get(name: str) -> int:
            value = raw.get(name)
            return value if isinstance(value, int) else 0

        return CodexUsage(
            self.input_tokens + get("input_tokens"),
            self.cached_input_tokens + get("cached_input_tokens"),
            self.cache_write_input_tokens + get("cache_write_input_tokens"),
            self.output_tokens + get("output_tokens"),
            self.reasoning_output_tokens + get("reasoning_output_tokens"),
        )


def clean_environment(root: Path) -> dict[str, str]:
    """O ambiente do Codex, do zero, com a casa dele (`CODEX_HOME`) dentro do espaço."""
    environment = _clean(root, "casa-codex")
    environment["CODEX_HOME"] = environment["HOME"]
    return environment


def codex_config(gate_url: str, model: str, effort: str | None) -> str:
    """O `config.toml` da sessão: o provedor na porta das mãos, na língua da Responses API, e o
    sandbox e as aprovações do Codex desligados (a cerca é a nossa)."""

    def quoted(value: str) -> str:
        return json.dumps(value, ensure_ascii=False)  # uma string do TOML, com os mesmos escapes

    lines = [
        "# A configuração do Codex numa sessão da oficina (ADR-0093): gerada a cada sessão.",
        f"model = {quoted(model)}",
        f"model_provider = {quoted(PROVIDER)}",
        'approval_policy = "never"',
        'sandbox_mode = "danger-full-access"',
    ]
    if effort is not None and effort in EFFORTS:
        lines.append(f"model_reasoning_effort = {quoted(EFFORTS[effort])}")
    lines += [
        "",
        f"[model_providers.{PROVIDER}]",
        'name = "a porta das mãos do Campsverso"',
        f"base_url = {quoted(gate_url.rstrip('/') + '/v1')}",
        f"env_key = {quoted(SESSION_VARIABLE)}",
        'wire_api = "responses"',
        "",
    ]
    return "\n".join(lines)


def resolve_command(command: Sequence[str], root: Path) -> list[str]:
    """O comando do Codex com o programa pelo caminho absoluto, achado no `PATH` de quem chama, e o
    interpretador à frente quando ele é um lançador do `env`. Recusa um programa que não existe ou
    que mora dentro do espaço."""
    return resolve_program(command, root, "o Codex")


def steps_of(item: Mapping[str, Any], root: Path, ms: int) -> list[HandsStep]:
    """Os passos de um item concluído: um por mudança de arquivo, um para cada outra ferramenta,
    nenhum para o raciocínio, as mensagens e a lista de tarefas."""
    kind = str(item.get("type") or "")
    status = str(item.get("status") or "completed")
    if kind == "file_change":
        ok = status == "completed"
        found: list[HandsStep] = []
        for raw in cast(list[Any], item.get("changes") or []):
            if not isinstance(raw, Mapping):
                continue
            change = cast(Mapping[str, Any], raw)
            path = relative(root, str(change.get("path") or ""))
            summary = f"{kind}: {change.get('kind', '')} {path}".strip()
            found.append(HandsStep(kind, summary[:MAX_SUMMARY], ok, ms, path or None))
        return found
    if kind == "command_execution":
        ok = status == "completed" and item.get("exit_code") == 0
        what = first_line(str(item.get("command") or ""))
    elif kind == "mcp_tool_call":
        ok = status == "completed" and not item.get("error")
        tool = str(item.get("tool") or "")
        what = f"{item.get('server', '')}.{tool}" if item.get("server") else tool
    elif kind == "web_search":
        ok = status != "failed"
        what = first_line(str(item.get("query") or ""))
    else:
        return []
    summary = f"{kind}: {what}" if what else kind
    return [HandsStep(kind, summary[:MAX_SUMMARY], ok, ms)]


def _item(data: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = data.get("item")
    return cast(Mapping[str, Any], raw) if isinstance(raw, Mapping) else {}


class CodexStream:
    """O leitor da saída do `codex exec --json`: os itens viram passos e voltas, e o
    `turn.completed` fecha a sessão com o `usage`."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._began: dict[str, float] = {}
        self.usage = CodexUsage()
        self.completed = False
        self.failed: str | None = None

    def account(self, data: Mapping[str, Any]) -> None:
        kind = data.get("type")
        if kind == "turn.completed":
            raw_usage = data.get("usage")
            if isinstance(raw_usage, Mapping):
                self.usage = self.usage.plus(cast(Mapping[str, Any], raw_usage))
            self.completed = True
        elif kind == "turn.failed":
            error = data.get("error")
            message = (
                cast(Mapping[str, Any], error).get("message")
                if isinstance(error, Mapping)
                else None
            )
            self.failed = str(message or "a volta falhou")
        elif kind == "error":
            self.failed = str(data.get("message") or "erro na sessão")

    def read(self, data: Mapping[str, Any]) -> Read:
        event = data.get("type")
        if event == "item.started":
            self._began.setdefault(str(_item(data).get("id") or ""), time.monotonic())
            return Read()
        if event != "item.completed":
            return Read()
        item = _item(data)
        start = self._began.pop(str(item.get("id") or ""), None)
        ms = 0 if start is None else round((time.monotonic() - start) * 1000)
        steps = tuple(steps_of(item, self._root, ms))
        kind = item.get("type")
        if kind == "agent_message":
            return Read(steps, "message", str(item.get("text") or ""))
        if kind in TOOL_ITEMS:
            return Read(steps, "tool")
        return Read(steps)

    def closes(self, data: Mapping[str, Any]) -> bool:
        return data.get("type") in TURN_ENDS


class CodexHands(ProcessHands):
    """As mãos do Codex. O conector acrescenta ao comando `exec --json`, o modelo, a pasta e o `-`
    da entrada padrão, por onde vai o briefing. O `usage` do `turn.completed` fica em `last_usage`,
    para conferir com o que a porta mediu."""

    harness = HARNESS
    title = "Codex"
    program = "codex"
    last_usage = CodexUsage()

    def dialect(self) -> Dialect:
        return OpenAIDialect()

    def argv(self, root: Path, job: HandsJob) -> list[str]:
        command = resolve_command(self._command, root)
        return [*command, "exec", "--json", "--model", job.model, "--cd", str(root), "-"]

    def prepare(self, root: Path, gate: HandsGate, job: HandsJob) -> dict[str, str]:
        environment = clean_environment(root)
        environment[SESSION_VARIABLE] = gate.token
        config = Path(environment["CODEX_HOME"]) / "config.toml"
        config.write_text(codex_config(gate.url, job.model, job.effort), encoding="utf-8")
        return environment

    def briefing(self, job: HandsJob) -> bytes | None:
        text = f"{job.system}\n\n{job.opening}" if job.system else job.opening
        return text.encode("utf-8")

    def stream(self, root: Path) -> Stream:
        return CodexStream(root)

    def finished(self, stream: Stream) -> None:
        if isinstance(stream, CodexStream):
            self.last_usage = stream.usage
