"""As mãos do Claude Code (ADR-0089): uma sessão do Claude Code, pelo Claude Agent SDK, no espaço de
um pedido da oficina.

O SDK abre o Claude Code que vem dentro dele, sem interface, e conversa com ele em JSON. Em volta
da sessão ficam as três camadas do isolamento (ADR-0089, decisão 6):

1. **O lançador:** o SDK não abre o Claude Code direto, e sim um script nosso, fora do espaço, que o
   abre com um ambiente limpo (só o que ele precisa, sem os segredos do controlador) e, no macOS,
   sob o `sandbox-exec`:
   - escrita só no espaço;
   - leitura negada na casa do usuário, menos o espaço, o Python do espaço e o próprio Claude Code;
   - rede só para a porta das mãos, em `127.0.0.1`.

   O macOS não deixa um sandbox dentro do outro: o sandbox do próprio Claude Code fica desligado,
   e o nosso cobre também o `Bash` (a sondagem de 22/nov).
2. **A chave fora do processo:** o Claude Code chama o modelo pela porta das mãos (`HandsGate`), com
   uma chave que só vale para a sessão.
3. **O gancho de cada ferramenta:** as de arquivo só aceitam caminhos dentro do espaço, fora do
   `.git`; o `Bash` recusa o que não cabe na oficina.

As ferramentas do mundo (chamar um robô da bancada, anotar na memória) são servidas no mesmo
processo, pelo SDK. Cada ferramenta usada vira um passo para a tela, e a conversa inteira fica num
arquivo fora do espaço, para a análise.
"""

import asyncio
import contextlib
import dataclasses
import json
import os
import re
import shlex
import stat
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookJSONOutput,
    HookMatcher,
    PreToolUseHookSpecificOutput,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    create_sdk_mcp_server,
    tool,
)

from campsverso_adapters.hands_fence import sandbox_profile
from campsverso_adapters.hands_gate import ANTHROPIC, HandsGate, Tape
from campsverso_adapters.hands_world_tools import (
    NOTE,
    ROBOT,
    SERVER,
    WorldTool,
    call_world_tool,
    world_tools,
)
from campsverso_ports import (
    CallMeter,
    HandsJob,
    HandsResult,
    HandsStep,
    HandsWorld,
    ToolResult,
    Workspace,
    note_of,
)

HARNESS = "claude_code"
# As ferramentas do Claude Code na oficina (ADR-0089, decisão 5). A web, os subagentes e os MCPs
# de fora ficam de fora.
TOOLS = ("Read", "Write", "Edit", "Glob", "Grep", "TodoWrite", "Bash")
WORLD_TOOLS = (f"mcp__{SERVER}__{ROBOT}", f"mcp__{SERVER}__{NOTE}")
PATH_KEYS = ("file_path", "path", "notebook_path")
# O que o `Bash` não roda na oficina: a rede (que o sandbox já corta, mas a recusa explica), o git
# que fala com fora, e os alvos do `make` que chamam a API ou sobem o mundo.
FORBIDDEN_COMMAND = re.compile(
    r"(^|[\s;&|(`])("
    r"git\s+(push|pull|fetch|clone|remote)\b"
    r"|curl\b|wget\b|nc\b|ncat\b|ssh\b|scp\b|sftp\b|rsync\b|telnet\b"
    r"|make\s+(\S+\s+)*(arena|arena-humano|corrida|fita|juiz|revisar|revisor-calibrar|conformidade"
    r"|llm-smoke|escritorio|escritorio-aqui|sandbox|jogar|run|up|soak|assistir)\b"
    r")"
)
MAX_SUMMARY = 200
MAX_RESULT = 500

type Warn = Callable[[str, Mapping[str, Any]], None]


# ------------------------------------------------------------------ os ganchos


def _inside(root: Path, given: str) -> Path | None:
    """O caminho dentro do espaço, resolvido (com os links), ou nada se ele sai do espaço ou entra
    no `.git`."""
    raw = Path(given).expanduser()
    target = (raw if raw.is_absolute() else root / raw).resolve()
    real = root.resolve()
    if target != real and real not in target.parents:
        return None
    if (real / ".git") == target or (real / ".git") in target.parents:
        return None
    return target


def refusal(root: Path, tool_name: str, tool_input: Mapping[str, Any]) -> str | None:
    """Por que a oficina recusa esta ferramenta com estes argumentos, ou nada se ela pode rodar."""
    if tool_name in WORLD_TOOLS or tool_name == "TodoWrite":
        return None
    if tool_name not in TOOLS:
        return f"a ferramenta {tool_name} não está na oficina"
    if tool_name == "Bash":
        command = str(tool_input.get("command") or "")
        if FORBIDDEN_COMMAND.search(command):
            return (
                "este comando não roda na oficina: sem rede, sem git para fora e sem os alvos que"
                " chamam a API ou sobem o mundo"
            )
        return None
    for key in PATH_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value and _inside(root, value) is None:
            return f"o caminho {value} fica fora do espaço do pedido"
    pattern = tool_input.get("pattern")
    if (
        tool_name == "Glob"
        and isinstance(pattern, str)
        and Path(pattern).is_absolute()
        and _inside(root, pattern.split("*", 1)[0] or "/") is None
    ):
        return f"o padrão {pattern} fica fora do espaço do pedido"
    return None


# ------------------------------------------------------------------ o lançador


# As variáveis que o SDK põe e o Claude Code lê; passam pelo lançador só se existirem.
SDK_VARIABLES = (
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_AGENT_SDK_VERSION",
    "CLAUDE_AGENT_SDK_CLIENT_APP",
    "CLAUDE_AGENT_SDK_DERIVED_CLIENT_APP",
    "CLAUDE_CODE_SDK_READS_SESSION_STATE",
    "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING",
    "PWD",
)


def launcher(cli: Path, environment: Mapping[str, str], profile: Path | None) -> str:
    """O script que o SDK abre no lugar do Claude Code: o ambiente do zero, e o sandbox no macOS."""
    fixed = " ".join(f"{k}={shlex.quote(v)}" for k, v in sorted(environment.items()))
    passed = " ".join(f'${{{name}+"{name}=${name}"}}' for name in SDK_VARIABLES)
    sandbox = "" if profile is None else f"/usr/bin/sandbox-exec -f {shlex.quote(str(profile))} "
    return (
        "#!/bin/sh\n"
        "# O lançador do Claude Code na oficina (ADR-0089): gerado por sessão, fora do espaço.\n"
        f'exec {sandbox}/usr/bin/env -i {fixed} {passed} {shlex.quote(str(cli))} "$@"\n'
    )


def bundled_cli() -> Path:
    """O Claude Code que vem dentro do SDK, preso na versão dele (ADR-0089, decisão 2)."""
    import claude_agent_sdk

    name = "claude.exe" if sys.platform == "win32" else "claude"
    path = Path(claude_agent_sdk.__file__).parent / "_bundled" / name
    if not path.is_file():
        raise FileNotFoundError(f"o SDK veio sem o Claude Code: {path}")
    return path


# ------------------------------------------------------------------ os passos


def _first_line(text: str, limit: int = MAX_SUMMARY) -> str:
    line = next((x.strip() for x in text.splitlines() if x.strip()), "")
    return line[:limit]


def _result_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            str(cast(Mapping[str, Any], c).get("text", ""))
            for c in cast(list[Any], content)
            if isinstance(c, Mapping)
        ]
        return "\n".join(parts)
    return ""


def step_of(
    name: str, given: Mapping[str, Any], content: object, is_error: bool, root: Path, ms: int
) -> HandsStep:
    """O passo de uma ferramenta usada, para a tela: o nome sem o prefixo do MCP, o que ela fez numa
    linha e o caminho relativo ao espaço."""
    short = name.removeprefix(f"mcp__{SERVER}__")
    path: str | None = None
    for key in PATH_KEYS:
        value = given.get(key)
        if isinstance(value, str) and value:
            inside = _inside(root, value)
            path = str(inside.relative_to(root.resolve())) if inside is not None else value
            break
    if short == "Bash":
        what = _first_line(str(given.get("description") or given.get("command") or ""))
    elif short == ROBOT:
        what = f"robô {given.get('nome', '')}"
    elif path is not None:
        what = path
    else:
        what = _first_line(str(given.get("pattern") or ""))
    result = _first_line(_result_text(content), 120)
    summary = f"{short}: {what}" if what else short
    if is_error and result:
        summary = f"{summary} (recusado: {result})"
    return HandsStep(short, summary[:MAX_SUMMARY], not is_error, ms, path)


REASONS = {
    "success": "pronto",
    "error_max_turns": "limite de voltas",
    "error_max_budget_usd": "teto da sessão",
    "error_during_execution": "erro na sessão",
}


def _plain(value: object) -> object:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {"_": type(value).__name__, **dataclasses.asdict(value)}
    return str(value)


# ------------------------------------------------------------------ as mãos


class ClaudeCodeHands:
    """As mãos do Claude Code. `home` é a pasta das sessões, fora dos espaços: o lançador, o perfil
    do sandbox e a conversa de cada uma."""

    def __init__(
        self,
        meter: CallMeter,
        *,
        api_key: str,
        home: Path,
        cli: Path | None = None,
        sandbox: bool | None = None,
        upstream: str = ANTHROPIC,
        transport: Any = None,
        tape: Path | None = None,
        tape_mode: str | None = None,
        warn: Warn | None = None,
        user_home: Path | None = None,
    ) -> None:
        self._meter = meter
        self._key = api_key
        self._home = home.resolve()  # o cercado e a conversa, de qualquer diretório
        self._cli = cli
        self._sandbox = sys.platform == "darwin" if sandbox is None else sandbox
        self._upstream = upstream
        self._transport = transport
        self._reel = None if tape is None or tape_mode is None else Tape(tape, tape_mode)
        self._warn: Warn = warn or _no_warning
        self._user_home = (user_home or Path.home()).resolve()
        self.sessions = 0

    @property
    def harness(self) -> str:
        return HARNESS

    def _readable(self, root: Path, cli: Path) -> list[Path]:
        """O que o Claude Code lê fora do espaço: ele mesmo e o Python do ambiente do espaço."""
        found = [cli.resolve().parent]
        python = root / ".venv" / "bin" / "python"
        if python.exists():
            found.append(python.resolve().parents[1])
        return found

    def _environment(self, root: Path, gate: HandsGate) -> dict[str, str]:
        local = root / ".oficina"
        tmp = local / "tmp"
        casa = local / "casa"
        for folder in (tmp, casa):
            folder.mkdir(parents=True, exist_ok=True)
        bins = [str(root / ".venv" / "bin"), "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
        return {
            "PATH": os.pathsep.join(bins),
            "HOME": str(casa),
            "TMPDIR": str(tmp),
            "CLAUDE_CODE_TMPDIR": str(tmp),
            # O zsh põe o here-doc em /tmp, que o sandbox fecha; o Opus escreve arquivos assim.
            "TMPPREFIX": str(tmp / "zsh"),
            "LANG": "C.UTF-8",
            "ANTHROPIC_API_KEY": gate.token,
            "ANTHROPIC_BASE_URL": gate.url,
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "DISABLE_AUTOUPDATER": "1",
            "DISABLE_TELEMETRY": "1",
            "DISABLE_ERROR_REPORTING": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            # O pyright do espaço não pergunta ao PyPI por uma versão nova: a conexão o sandbox
            # corta, mas a consulta de DNS passaria (ADR-0090).
            "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1",
        }

    def _write_launcher(self, folder: Path, root: Path, gate: HandsGate, cli: Path) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        profile: Path | None = None
        if self._sandbox:
            port = gate.url.rsplit(":", 1)[-1]
            profile = folder / "sandbox.sb"
            profile.write_text(
                sandbox_profile(root.resolve(), port, self._user_home, self._readable(root, cli)),
                encoding="utf-8",
            )
        script = folder / "claude.sh"
        script.write_text(launcher(cli, self._environment(root, gate), profile), encoding="utf-8")
        script.chmod(stat.S_IRWXU)
        return script

    def _world_server(self, world: HandsWorld) -> Any:
        """As ferramentas do mundo num servidor MCP do processo, pelo SDK, com a definição comum a
        todas as mãos (`hands_world_tools.py`)."""

        def wrapped(spec: WorldTool) -> Any:
            @tool(spec.name, spec.description, dict(spec.schema))
            async def call(args: dict[str, Any]) -> dict[str, Any]:
                return _tool_answer(await call_world_tool(world, spec.name, args))

            return call

        return create_sdk_mcp_server(SERVER, tools=[wrapped(s) for s in world_tools(world)])

    async def run(self, space: Workspace, job: HandsJob, world: HandsWorld) -> HandsResult:
        root = space.root.resolve()
        cli = self._cli or bundled_cli()
        self.sessions += 1
        folder = self._home / job.ticket_id
        transcript = folder / f"sessao-{self.sessions}-{int(time.time())}.jsonl"
        tape = None if self._reel is None else self._reel.at(root)

        async def guard(hook_input: Any, _tool_use_id: str | None, _context: Any) -> HookJSONOutput:
            data = cast(Mapping[str, Any], hook_input)
            why = refusal(
                root,
                str(data.get("tool_name") or ""),
                cast(Mapping[str, Any], data.get("tool_input") or {}),
            )
            if why is None:
                return {}
            denied: PreToolUseHookSpecificOutput = {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": why,
            }
            return {"hookSpecificOutput": denied}

        stopped: str | None = None

        def refuse() -> str | None:
            return "o teto do pedido ou do dia" if world.should_stop() else None

        async with HandsGate(
            self._meter,
            api_key=self._key,
            harness=HARNESS,
            avatar_id=job.avatar_id,
            ticket_id=job.ticket_id,
            refuse=refuse,
            upstream=self._upstream,
            transport=self._transport,
            tape=tape,
        ) as gate:
            script = self._write_launcher(folder / ".lancador", root, gate, cli)
            errors: list[str] = []
            options = ClaudeAgentOptions(
                tools=list(TOOLS),
                allowed_tools=[*TOOLS, *WORLD_TOOLS],
                permission_mode="dontAsk",
                system_prompt={"type": "preset", "preset": "claude_code", "append": job.system},
                mcp_servers={SERVER: self._world_server(world)},
                strict_mcp_config=True,
                setting_sources=["project"],
                model=job.model,
                effort=cast(Any, job.effort),
                max_turns=job.limits.max_turns,
                max_budget_usd=job.limits.max_usd,
                cwd=str(root),
                cli_path=str(script),
                hooks={"PreToolUse": [HookMatcher(hooks=[guard], on_failure="block")]},
                stderr=lambda line: errors.append(line[-500:]) if len(errors) < 50 else None,
            )
            # Cada ferramenta pedida, com o texto do modelo antes dela na mesma resposta (ADR-0093,
            # decisão 12): o passo o mostra como um comentário.
            pending: dict[str, tuple[str, Mapping[str, Any], float, str]] = {}
            # O Claude Code manda cada bloco da resposta numa mensagem: o texto fica até a
            # ferramenta seguinte o levar.
            said = ""
            steps = 0
            final: ResultMessage | None = None
            last_text = ""
            try:
                async with asyncio.timeout(job.limits.max_seconds):
                    async with ClaudeSDKClient(options) as client:
                        await client.query(job.opening)
                        with transcript.open("w", encoding="utf-8") as log:
                            async for message in client.receive_response():
                                log.write(
                                    json.dumps(message, default=_plain, ensure_ascii=False) + "\n"
                                )
                                # Uma sessão que cai no meio (a rede da máquina, 22/nov) deixa o
                                # que já aconteceu no arquivo.
                                log.flush()
                                if isinstance(message, AssistantMessage):
                                    for block in message.content:
                                        if isinstance(block, ToolUseBlock):
                                            pending[block.id] = (
                                                block.name,
                                                block.input,
                                                time.monotonic(),
                                                said,
                                            )
                                            said = ""
                                        elif isinstance(block, TextBlock) and block.text.strip():
                                            last_text = block.text
                                            said = f"{said} {block.text}".strip()
                                elif isinstance(message, UserMessage) and isinstance(
                                    message.content, list
                                ):
                                    for block in message.content:
                                        if (
                                            isinstance(block, ToolResultBlock)
                                            and block.tool_use_id in pending
                                        ):
                                            name, given, began, before = pending.pop(
                                                block.tool_use_id
                                            )
                                            ms = round((time.monotonic() - began) * 1000)
                                            steps += 1
                                            step = step_of(
                                                name,
                                                given,
                                                block.content,
                                                bool(block.is_error),
                                                root,
                                                ms,
                                            )
                                            await world.step(replace(step, note=note_of(before)))
                                elif isinstance(message, ResultMessage):
                                    final = message
                                if world.should_stop() and stopped is None and final is None:
                                    stopped = "parada"
                                    with contextlib.suppress(Exception):
                                        await client.interrupt()
            except TimeoutError:
                stopped = "limite de tempo"
            except Exception as error:  # o Claude Code caiu: a sessão acaba com o motivo
                self._warn(
                    "hands.claude_code_failed", {"error": repr(error)[:500], "stderr": errors[-5:]}
                )
                stopped = stopped or "o Claude Code falhou"
            measured = round(gate.cost_usd, 8)
            refused = gate.refused
        estimate = None if final is None else final.total_cost_usd
        if estimate and measured and abs(estimate - measured) > 0.25 * max(estimate, measured):
            self._warn("hands.cost_mismatch", {"estimate_usd": estimate, "measured_usd": measured})
        if final is None:
            # Parado pelo mundo, na porta ou entre um passo e outro: o motivo do nosso harness.
            reason = "parada" if refused else (stopped or "sem resposta final")
            return HandsResult(False, "", 0, steps, reason, measured)
        reason = REASONS.get(final.subtype, final.subtype)
        if refused:
            reason = "parada"
        elif stopped is not None:
            reason = stopped
        done = final.subtype == "success" and not final.is_error and stopped is None and not refused
        summary = (final.result or last_text or "").strip()
        return HandsResult(done, summary[:MAX_RESULT], final.num_turns, steps, reason, measured)


def _no_warning(_event: str, _fields: Mapping[str, Any]) -> None:
    return None


def _tool_answer(result: ToolResult) -> dict[str, Any]:
    answer: dict[str, Any] = {"content": [{"type": "text", "text": result.text or "(vazio)"}]}
    if not result.ok:
        answer["is_error"] = True
    return answer
