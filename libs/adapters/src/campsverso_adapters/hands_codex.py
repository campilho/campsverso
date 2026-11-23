"""As mãos do Codex (ADR-0089, decisão 11; ADR-0093): uma sessão do `codex exec --json` no espaço de
um pedido.

O conector abre o Codex como um processo, na pasta do espaço, com o briefing na entrada padrão, e
lê os eventos que ele imprime, um JSON por linha (o formato em `tests/fixtures/codex/README.md`):

- cada item de ferramenta concluído (`command_execution`, `file_change`, `mcp_tool_call`,
  `web_search`) vira um passo para a tela, com o caminho quando houver;
- a última `agent_message` é o resumo da entrega;
- a conversa inteira fica num arquivo fora do espaço, para a análise.

**O modelo passa pela porta das mãos** (`HandsGate`, na língua da OpenAI): a configuração da sessão
(`config.toml`, na casa do Codex dentro do espaço) aponta um provedor próprio para a porta, com uma
chave que só vale para a sessão. A porta põe a chave de verdade do lado de fora, mede cada chamada
(o custo da sessão é o dela) e recusa a chamada seguinte quando o teto do pedido, o do dia ou o da
sessão estourou. O `usage` do `turn.completed` fica em `last_usage`, para conferir com a porta.

**A cerca é o nosso `sandbox-exec`** (ADR-0093, decisão 5): o do Codex fica desligado
(`danger-full-access`, sem aprovações), porque o macOS não deixa um sandbox dentro do outro.

A sessão para no limite de tempo (que conta desde a entrega do briefing), no de voltas (os itens
de ferramenta e as mensagens, como as respostas do modelo), no teto da sessão ou quando o mundo
pede. Os tetos valem depois de cada ferramenta e depois de cada mensagem que não é a última: a
mensagem final e o `turn.completed` que a segue nunca são cortados. A espera do fim do processo,
depois da saída, também cabe no limite de tempo. Parada a sessão, o conector manda o SIGTERM ao
grupo, ainda lê um pouco a saída, pelo `usage` de um `turn.completed` que chegue, e encerra o grupo
de processos inteiro (o Codex e o que ele abriu).

O Codex é achado pelo `PATH` de quem chama, nunca pelo do espaço: um `codex` escrito no espaço não
roda no lugar dele, e o interpretador de um lançador do `env` também vem de fora. O processo recebe
um ambiente do zero, sem nenhuma chave.
"""

import asyncio
import contextlib
import json
import os
import signal
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, cast

from campsverso_adapters.hands_dialects import OpenAIDialect
from campsverso_adapters.hands_fence import (
    SANDBOX_EXEC,
    readable_for,
    resolve_program,
    sandbox_profile,
    workspace_python,
)
from campsverso_adapters.hands_gate import HandsGate, Tape
from campsverso_ports import (
    CallMeter,
    HandsJob,
    HandsResult,
    HandsStep,
    HandsWorld,
    Workspace,
)

HARNESS = "codex"
TOOL_ITEMS = ("command_execution", "file_change", "mcp_tool_call", "web_search")
# Os eventos que fecham a volta: uma mensagem seguida de um deles era a resposta final.
TURN_ENDS = ("turn.completed", "turn.failed")
MAX_SUMMARY = 200
MAX_RESULT = 500
# Depois de parar, quanto tempo ainda ler a saída pelo `usage`, e esperar o processo acabar.
GRACE_SECONDS = 5.0
# Nenhuma variável com estes pedaços no nome entra no processo do Codex.
SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")
# O provedor da sessão no `config.toml` e a variável com a chave da sessão (que não é segredo: só
# vale na porta, enquanto a sessão dura).
PROVIDER = "campsverso"
SESSION_VARIABLE = "CAMPSVERSO_SESSAO"
# O esforço do escritório no do Codex, que não tem o `max`.
EFFORTS = {"low": "low", "medium": "medium", "high": "high", "xhigh": "xhigh", "max": "xhigh"}

type Warn = Callable[[str, Mapping[str, Any]], None]


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
    conector acrescenta `exec --json`, o modelo, a pasta e o `-` da entrada padrão. `home` é a pasta
    das sessões, fora dos espaços: o perfil do cercado e a conversa de cada uma. `readable` é o que
    o cercado ainda deixa ler fora do espaço, além do Codex e do Python do espaço."""

    def __init__(
        self,
        meter: CallMeter,
        *,
        api_key: str,
        home: Path,
        command: Sequence[str] = ("codex",),
        sandbox: bool | None = None,
        upstream: str | None = None,
        transport: Any = None,
        tape: Path | None = None,
        tape_mode: str | None = None,
        readable: Sequence[Path] = (),
        warn: Warn | None = None,
        user_home: Path | None = None,
    ) -> None:
        self._meter = meter
        self._key = api_key
        self._home = home
        self._command = list(command)
        self._sandbox = sys.platform == "darwin" if sandbox is None else sandbox
        self._upstream = upstream
        self._transport = transport
        self._reel = None if tape is None or tape_mode is None else Tape(tape, tape_mode)
        self._readable = [p.resolve() for p in readable]
        self._warn: Warn = warn or _no_warning
        self._user_home = (user_home or Path.home()).resolve()
        self.sessions = 0
        self.last_environment: dict[str, str] = {}
        self.last_usage = CodexUsage()

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

    def _fence(self, folder: Path, root: Path, gate: HandsGate, argv: list[str]) -> list[str]:
        """O comando sob o `sandbox-exec`, com o perfil da sessão fora do espaço; sem o cercado
        (fora do macOS, ou nos testes), o comando como está."""
        if not self._sandbox:
            return argv
        port = gate.url.rsplit(":", 1)[-1]
        readable = [*readable_for(argv, self._user_home), *workspace_python(root), *self._readable]
        profile = folder / "sandbox.sb"
        profile.write_text(
            sandbox_profile(root.resolve(), port, self._user_home, readable), encoding="utf-8"
        )
        return [SANDBOX_EXEC, "-f", str(profile), *argv]

    async def run(self, space: Workspace, job: HandsJob, world: HandsWorld) -> HandsResult:
        priced = OpenAIDialect().priced(job.model)
        try:
            self._meter.assert_priced(priced)
        except LookupError as error:
            raise ValueError(f"o modelo {job.model} não tem preço na tabela") from error
        root = space.root
        argv = self.argv(root, job)
        self.sessions += 1
        folder = self._home / job.ticket_id
        folder.mkdir(parents=True, exist_ok=True)
        transcript = folder / f"codex-{self.sessions}-{int(time.time())}.jsonl"
        tape = None if self._reel is None else self._reel.at(root)
        refused: str | None = None

        def refuse() -> str | None:
            """A recusa da porta: o teto do pedido ou do dia (o mundo pede para parar) e o da
            sessão, que só a porta vê a cada chamada."""
            nonlocal refused
            if world.should_stop():
                refused = "parada"
            elif gate.cost_usd >= job.limits.max_usd:
                refused = "teto da sessão"
            else:
                return None
            return refused

        gate = HandsGate(
            self._meter,
            api_key=self._key,
            harness=HARNESS,
            avatar_id=job.avatar_id,
            ticket_id=job.ticket_id,
            refuse=refuse,
            upstream=self._upstream,
            transport=self._transport,
            tape=tape,
            dialect=OpenAIDialect(),
        )
        async with gate:
            environment = clean_environment(root)
            environment[SESSION_VARIABLE] = gate.token
            self.last_environment = dict(environment)
            config = Path(environment["CODEX_HOME"]) / "config.toml"
            config.write_text(codex_config(gate.url, job.model, job.effort), encoding="utf-8")
            with transcript.open("wb") as log:
                fenced = self._fence(folder, root, gate, argv)
                outcome = await self._session(fenced, root, environment, job, world, gate, log)
        stopped, failed, completed, returncode, turns, steps, last_text = outcome
        if failed is not None:
            self._warn("hands.codex_failed", {"error": failed[:500]})
        if stopped is not None:
            reason = stopped
        elif refused is not None:
            reason = refused
        elif failed is not None:
            reason = "erro na sessão"
        elif not completed:
            reason = "sem resposta final"
        elif returncode != 0:
            reason = "o Codex falhou"
        else:
            reason = "pronto"
        done = reason == "pronto"
        summary = last_text.strip()[:MAX_RESULT]
        return HandsResult(done, summary, turns, steps, reason, round(gate.cost_usd, 8))

    async def _session(
        self,
        argv: list[str],
        root: Path,
        environment: Mapping[str, str],
        job: HandsJob,
        world: HandsWorld,
        gate: HandsGate,
        log: IO[bytes],
    ) -> tuple[str | None, str | None, bool, int | None, int, int, str]:
        """Roda o processo e lê a saída: o motivo da parada, a falha, se a volta fechou, o código de
        saída, as voltas, os passos e a última mensagem."""
        process = await asyncio.create_subprocess_exec(
            *argv,
            cwd=str(root),
            env=dict(environment),
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
        # Um teto alcançado numa mensagem: só vale se a sessão seguir depois dela.
        held: str | None = None

        def over() -> str | None:
            if world.should_stop():
                return "parada"
            if turns >= job.limits.max_turns:
                return "limite de voltas"
            if gate.cost_usd >= job.limits.max_usd:
                return "teto da sessão"
            return None

        def read(line: bytes) -> Mapping[str, Any] | None:
            log.write(line if line.endswith(b"\n") else line + b"\n")
            # Uma sessão que cai no meio deixa no arquivo o que já aconteceu.
            log.flush()
            data = self._parse(line)
            if data is not None:
                account(data)
            return data

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
                    data = read(line)
                    if data is None:
                        continue
                    event = data.get("type")
                    if held is not None and event not in TURN_ENDS:
                        # A mensagem não era a final: a sessão seguiu depois dela.
                        stopped = held
                        break
                    if event == "item.started":
                        started: Mapping[str, Any] = _item(data)
                        began.setdefault(str(started.get("id") or ""), time.monotonic())
                        continue
                    if event != "item.completed":
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
                        # A resposta final nunca é cortada: o teto espera o que vem depois.
                        held = over()
                    elif kind in TOOL_ITEMS:
                        turns += 1
                        stopped = over()
                        if stopped is not None:
                            break
                if stopped is None:
                    # A saída acabou; o fim do Codex também cabe no limite de tempo.
                    await process.wait()
        except TimeoutError:
            stopped = "limite de tempo"
        finally:
            if stopped is not None:
                _signal_group(process, signal.SIGTERM)
                if not completed:
                    with contextlib.suppress(TimeoutError, ValueError):
                        async with asyncio.timeout(GRACE_SECONDS):
                            async for line in stdout:
                                read(line)
            await _end(process)
            self.last_usage = usage
        return stopped, failed, completed, process.returncode, turns, steps, last_text


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
