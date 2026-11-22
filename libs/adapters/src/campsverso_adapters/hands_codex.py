"""As mãos do Codex (ADR-0089, decisão 11): uma sessão do `codex exec --json` no espaço de um
pedido.

O conector abre o Codex como um processo, na pasta do espaço, com o briefing na entrada padrão, e
lê os eventos que ele imprime, um JSON por linha (o formato em `tests/fixtures/codex/README.md`):

- cada item de ferramenta concluído (`command_execution`, `file_change`, `mcp_tool_call`,
  `web_search`) vira um passo para a tela, com o caminho quando houver;
- o `usage` de cada `turn.completed` soma nos tokens, e o custo sai da tabela de preços;
- a última `agent_message` é o resumo da entrega.

A sessão para no limite de tempo, no de voltas (os itens de ferramenta e as mensagens, como as
respostas do modelo), no teto da sessão ou quando o mundo pede. O processo recebe um ambiente do
zero, sem nenhuma chave: o login e a ponte até o modelo são do M27, que liga o Codex de verdade.
"""

import asyncio
import contextlib
import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from campsverso_adapters.model_metered import ModelPrices
from campsverso_ports import HandsJob, HandsResult, HandsStep, HandsWorld, Workspace

HARNESS = "codex"
TOOL_ITEMS = ("command_execution", "file_change", "mcp_tool_call", "web_search")
MAX_SUMMARY = 200
MAX_RESULT = 500
# Nenhuma variável com estes pedaços no nome entra no processo do Codex.
SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")

type Warn = Callable[[str, Mapping[str, Any]], None]


@dataclass(frozen=True, slots=True)
class CodexUsage:
    """Os tokens no sentido da OpenAI: `input_tokens` já inclui o que veio do cache, e
    `output_tokens` já inclui o raciocínio; o custo conta cada token uma vez só."""

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


def codex_cost_usd(usage: CodexUsage, prices: ModelPrices) -> float:
    """O custo pela tabela: a entrada sem cache, o cache lido, o cache gravado e a saída."""
    fresh = max(0, usage.input_tokens - usage.cached_input_tokens - usage.cache_write_input_tokens)
    total = (
        fresh * prices.input_per_mtok
        + usage.cached_input_tokens * prices.cache_read_per_mtok
        + usage.cache_write_input_tokens * prices.cache_write_per_mtok
        + usage.output_tokens * prices.output_per_mtok
    )
    return round(total / 1_000_000, 8)


def clean_environment(root: Path) -> dict[str, str]:
    """O ambiente do Codex, do zero: o caminho dos programas, uma casa e um temporário dentro do
    espaço, e a língua. Nada vem do ambiente de quem chama."""
    local = root / ".oficina"
    casa = local / "casa-codex"
    tmp = local / "tmp"
    for folder in (casa, tmp):
        folder.mkdir(parents=True, exist_ok=True)
    bins = [str(root / ".venv" / "bin"), "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    environment = {
        "PATH": os.pathsep.join(bins),
        "HOME": str(casa),
        "CODEX_HOME": str(casa),
        "TMPDIR": str(tmp),
        "LANG": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return {k: v for k, v in environment.items() if not any(m in k.upper() for m in SECRET_MARKERS)}


def _relative(root: Path, given: str) -> str:
    """O caminho relativo ao espaço; o Codex pode dar o absoluto. Fora do espaço, fica como veio."""
    raw = Path(given)
    if not raw.is_absolute():
        return given
    real = root.resolve()
    target = raw.resolve()
    if target == real or real in target.parents:
        return str(target.relative_to(real))
    return given


def _first_line(text: str, limit: int = MAX_SUMMARY) -> str:
    return next((x.strip() for x in text.splitlines() if x.strip()), "")[:limit]


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
            path = _relative(root, str(change.get("path") or ""))
            summary = f"{kind}: {change.get('kind', '')} {path}".strip()
            found.append(HandsStep(kind, summary[:MAX_SUMMARY], ok, ms, path or None))
        return found
    if kind == "command_execution":
        ok = status == "completed" and item.get("exit_code") == 0
        what = _first_line(str(item.get("command") or ""))
    elif kind == "mcp_tool_call":
        ok = status == "completed" and not item.get("error")
        tool = str(item.get("tool") or "")
        what = f"{item.get('server', '')}.{tool}" if item.get("server") else tool
    elif kind == "web_search":
        ok = status != "failed"
        what = _first_line(str(item.get("query") or ""))
    else:
        return []
    summary = f"{kind}: {what}" if what else kind
    return [HandsStep(kind, summary[:MAX_SUMMARY], ok, ms)]


class CodexHands:
    """As mãos do Codex. `command` é como abrir o Codex (o binário, ou um falso nos testes); o
    conector acrescenta `exec --json`, o modelo, a pasta e o `-` da entrada padrão."""

    def __init__(
        self,
        prices: Mapping[str, ModelPrices],
        *,
        command: Sequence[str] = ("codex",),
        warn: Warn | None = None,
    ) -> None:
        self._prices = dict(prices)
        self._command = list(command)
        self._warn: Warn = warn or _no_warning
        self.last_environment: dict[str, str] = {}

    @property
    def harness(self) -> str:
        return HARNESS

    def argv(self, root: Path, job: HandsJob) -> list[str]:
        return [*self._command, "exec", "--json", "--model", job.model, "--cd", str(root), "-"]

    async def run(self, space: Workspace, job: HandsJob, world: HandsWorld) -> HandsResult:
        if job.model not in self._prices:
            raise ValueError(f"o modelo {job.model} não tem preço na tabela")
        prices = self._prices[job.model]
        root = space.root
        environment = clean_environment(root)
        self.last_environment = dict(environment)
        process = await asyncio.create_subprocess_exec(
            *self.argv(root, job),
            cwd=str(root),
            env=environment,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            limit=16 * 1024 * 1024,
        )
        assert process.stdin is not None
        assert process.stdout is not None
        briefing = f"{job.system}\n\n{job.opening}" if job.system else job.opening
        process.stdin.write(briefing.encode("utf-8"))
        with contextlib.suppress(ConnectionError):
            await process.stdin.drain()
        process.stdin.close()

        usage = CodexUsage()
        began: dict[str, float] = {}
        steps = 0
        turns = 0
        last_text = ""
        completed = False
        failed: str | None = None
        stopped: str | None = None
        try:
            async with asyncio.timeout(job.limits.max_seconds):
                async for line in process.stdout:
                    text = line.decode("utf-8", errors="replace").strip()
                    if not text:
                        continue
                    try:
                        event = json.loads(text)
                    except json.JSONDecodeError:
                        self._warn("hands.codex_bad_line", {"line": text[:200]})
                        continue
                    if not isinstance(event, Mapping):
                        continue
                    data = cast(Mapping[str, Any], event)
                    kind = data.get("type")
                    raw_item = data.get("item")
                    item = (
                        cast(Mapping[str, Any], raw_item) if isinstance(raw_item, Mapping) else {}
                    )
                    item_id = str(item.get("id") or "")
                    if kind == "item.started":
                        began.setdefault(item_id, time.monotonic())
                    elif kind == "item.completed":
                        start = began.pop(item_id, None)
                        ms = 0 if start is None else round((time.monotonic() - start) * 1000)
                        for step in steps_of(item, root, ms):
                            steps += 1
                            await world.step(step)
                        if item.get("type") in TOOL_ITEMS or item.get("type") == "agent_message":
                            turns += 1
                        if item.get("type") == "agent_message":
                            last_text = str(item.get("text") or "") or last_text
                    elif kind == "turn.completed":
                        raw_usage = data.get("usage")
                        if isinstance(raw_usage, Mapping):
                            usage = usage.plus(cast(Mapping[str, Any], raw_usage))
                        completed = True
                    elif kind == "turn.failed":
                        error = data.get("error")
                        message = (
                            cast(Mapping[str, Any], error).get("message")
                            if isinstance(error, Mapping)
                            else None
                        )
                        failed = str(message or "a volta falhou")
                    elif kind == "error":
                        failed = str(data.get("message") or "erro na sessão")
                    if world.should_stop():
                        stopped = "parada"
                    elif turns >= job.limits.max_turns:
                        stopped = "limite de voltas"
                    elif codex_cost_usd(usage, prices) >= job.limits.max_usd:
                        stopped = "teto da sessão"
                    if stopped is not None:
                        break
        except TimeoutError:
            stopped = "limite de tempo"
        finally:
            await _end(process, patient=stopped is None)
        cost = codex_cost_usd(usage, prices)
        if failed is not None:
            self._warn("hands.codex_failed", {"error": failed[:500]})
        if stopped is not None:
            reason = stopped
        elif failed is not None:
            reason = "erro na sessão"
        elif not completed:
            reason = "sem resposta final"
        elif process.returncode != 0:
            reason = "o Codex falhou"
        else:
            reason = "pronto"
        done = reason == "pronto"
        summary = last_text.strip()[:MAX_RESULT]
        return HandsResult(done, summary, turns, steps, reason, cost)


async def _end(process: asyncio.subprocess.Process, *, patient: bool) -> None:
    """Espera o fim do processo (um pouco, se a sessão acabou sozinha); se ele ainda roda, termina
    e, sem resposta, mata."""
    if patient:
        with contextlib.suppress(TimeoutError):
            async with asyncio.timeout(5):
                await process.wait()
    if process.returncode is not None:
        return
    with contextlib.suppress(ProcessLookupError):
        process.terminate()
    try:
        async with asyncio.timeout(5):
            await process.wait()
    except TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            process.kill()
        await process.wait()


def _no_warning(_event: str, _fields: Mapping[str, Any]) -> None:
    return None
