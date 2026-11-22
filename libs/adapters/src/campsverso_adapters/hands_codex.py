"""As mãos do Codex (ADR-0089, decisão 11): uma sessão do `codex exec --json` no espaço de um
pedido.

O conector abre o Codex como um processo, na pasta do espaço, com o briefing na entrada padrão, e
lê os eventos que ele imprime, um JSON por linha (o formato em `tests/fixtures/codex/README.md`):

- cada item de ferramenta concluído (`command_execution`, `file_change`, `mcp_tool_call`,
  `web_search`) vira um passo para a tela, com o caminho quando houver;
- o `usage` de cada `turn.completed` soma nos tokens, e o custo sai da tabela de preços;
- a última `agent_message` é o resumo da entrega.

A sessão para no limite de tempo (que conta desde a entrega do briefing), no de voltas (os itens
de ferramenta e as mensagens, como as respostas do modelo), no teto da sessão ou quando o mundo
pede. Os tetos só valem entre uma ferramenta e outra: a mensagem final e o `turn.completed` que
a segue nunca são cortados. Parada a sessão, o conector ainda lê um pouco a saída, pelo `usage` de
um `turn.completed` que chegue, e encerra o grupo de processos inteiro (o Codex e o que ele abriu).

O Codex é achado pelo `PATH` de quem chama, nunca pelo do espaço: um `codex` escrito no espaço não
roda no lugar dele. O processo recebe um ambiente do zero, sem nenhuma chave: o login e a ponte até
o modelo são do M27, que liga o Codex de verdade.
"""

import asyncio
import contextlib
import json
import os
import shutil
import signal
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
# Depois de parar, quanto tempo ainda ler a saída pelo `usage`, e esperar o processo acabar.
GRACE_SECONDS = 5.0
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


def resolve_command(command: Sequence[str], root: Path) -> list[str]:
    """O comando do Codex com o programa pelo caminho absoluto, achado no `PATH` de quem chama.
    Recusa um programa que não existe ou que mora dentro do espaço."""
    if not command:
        raise ValueError("o comando do Codex está vazio")
    program, *rest = command
    found = shutil.which(program, path=os.environ.get("PATH", os.defpath))
    if found is None:
        raise FileNotFoundError(f"o Codex não foi achado: {program}")
    real = Path(found).resolve()
    space = root.resolve()
    if real == space or space in real.parents:
        raise ValueError(f"o Codex não pode vir do espaço do pedido: {found}")
    return [str(Path(found).absolute()), *rest]


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
        command = resolve_command(self._command, root)
        return [*command, "exec", "--json", "--model", job.model, "--cd", str(root), "-"]

    def _parse(self, line: bytes) -> Mapping[str, Any] | None:
        """Um evento da saída, ou nada para a linha vazia, a quebrada e a que não é um objeto."""
        text = line.decode("utf-8", errors="replace").strip()
        if not text:
            return None
        try:
            event = json.loads(text)
        except json.JSONDecodeError:
            self._warn("hands.codex_bad_line", {"line": text[:200]})
            return None
        return cast(Mapping[str, Any], event) if isinstance(event, Mapping) else None

    async def run(self, space: Workspace, job: HandsJob, world: HandsWorld) -> HandsResult:
        if job.model not in self._prices:
            raise ValueError(f"o modelo {job.model} não tem preço na tabela")
        prices = self._prices[job.model]
        root = space.root
        argv = self.argv(root, job)
        environment = clean_environment(root)
        self.last_environment = dict(environment)
        process = await asyncio.create_subprocess_exec(
            *argv,
            cwd=str(root),
            env=environment,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            limit=16 * 1024 * 1024,
            start_new_session=True,
        )
        assert process.stdin is not None
        assert process.stdout is not None
        stdin = process.stdin
        stdout = process.stdout
        briefing = f"{job.system}\n\n{job.opening}" if job.system else job.opening

        usage = CodexUsage()
        began: dict[str, float] = {}
        steps = 0
        turns = 0
        last_text = ""
        completed = False
        failed: str | None = None
        stopped: str | None = None

        def account(data: Mapping[str, Any]) -> None:
            """O que vale mesmo depois de parar: o `usage`, a falha e o fim da volta."""
            nonlocal usage, completed, failed
            kind = data.get("type")
            if kind == "turn.completed":
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

        try:
            async with asyncio.timeout(job.limits.max_seconds):
                stdin.write(briefing.encode("utf-8"))
                with contextlib.suppress(ConnectionError):
                    await stdin.drain()
                stdin.close()
                async for line in stdout:
                    data = self._parse(line)
                    if data is None:
                        continue
                    account(data)
                    if data.get("type") != "item.completed":
                        if data.get("type") == "item.started":
                            started: Mapping[str, Any] = _item(data)
                            began.setdefault(str(started.get("id") or ""), time.monotonic())
                        continue
                    item: Mapping[str, Any] = _item(data)
                    start = began.pop(str(item.get("id") or ""), None)
                    ms = 0 if start is None else round((time.monotonic() - start) * 1000)
                    for step in steps_of(item, root, ms):
                        steps += 1
                        await world.step(step)
                    kind = item.get("type")
                    if kind == "agent_message":
                        turns += 1
                        last_text = str(item.get("text") or "") or last_text
                    elif kind in TOOL_ITEMS:
                        turns += 1
                        # Os tetos valem entre uma ferramenta e outra, nunca na resposta final.
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
            if stopped is not None and not completed:
                _signal_group(process, signal.SIGTERM)
                with contextlib.suppress(TimeoutError, ValueError):
                    async with asyncio.timeout(GRACE_SECONDS):
                        async for line in stdout:
                            data = self._parse(line)
                            if data is not None:
                                account(data)
            await _end(process)
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


def _item(data: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = data.get("item")
    return cast(Mapping[str, Any], raw) if isinstance(raw, Mapping) else {}


def _signal_group(process: asyncio.subprocess.Process, sig: signal.Signals) -> None:
    """Um sinal para o grupo do Codex: ele abre o seu próprio (`start_new_session`), e os
    comandos que ele roda ficam no mesmo grupo."""
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(process.pid, sig)


async def _end(process: asyncio.subprocess.Process) -> None:
    """Espera o fim do processo; se ele ainda roda, termina o grupo e, sem resposta, mata. No fim,
    mata o que sobrou no grupo, mesmo com o Codex já fora."""
    with contextlib.suppress(TimeoutError):
        async with asyncio.timeout(GRACE_SECONDS):
            await process.wait()
    if process.returncode is None:
        _signal_group(process, signal.SIGTERM)
        with contextlib.suppress(TimeoutError):
            async with asyncio.timeout(GRACE_SECONDS):
                await process.wait()
    _signal_group(process, signal.SIGKILL)
    await process.wait()


def _no_warning(_event: str, _fields: Mapping[str, Any]) -> None:
    return None
