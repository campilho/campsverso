"""As mãos de um harness de fora que roda como processo (ADR-0093): o Codex e o Antigravity rodam
do mesmo jeito, e cada um só diz como se abre e como se lê a saída dele.

Numa sessão, o conector:
- **abre a porta das mãos** na língua do laboratório (`HandsGate`), com a recusa do teto do pedido,
  do dia e da sessão (`Refusal`). O custo da sessão é o que a porta mediu;
- **abre o harness** num grupo de processos próprio, na pasta do espaço, com um ambiente do zero e,
  no macOS, sob o nosso `sandbox-exec` (o cercado; `hands_fence.py`), e entrega o briefing;
- **lê a saída,** um JSON por linha, com o leitor do harness (`Stream`): cada evento pode dar passos
  para a tela e uma volta (uma ferramenta ou uma mensagem do modelo). Toda a saída vai, linha a
  linha, para a conversa, num arquivo fora do espaço.

Os tetos (o mundo pede, as voltas, o custo medido) valem depois de cada ferramenta e depois de cada
mensagem que não é a última: a resposta final e o evento que fecha a sessão nunca são cortados. O
limite de tempo conta desde a entrega do briefing e cobre a espera do fim do processo. Parada a
sessão, o conector manda o SIGTERM ao grupo, ainda lê um pouco a saída, pelos tokens de um fim que
chegue, e encerra o grupo de processos inteiro (o harness e o que ele abriu).
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
from typing import IO, Any, Literal, Protocol, cast

from campsverso_adapters.hands_fence import (
    SANDBOX_EXEC,
    readable_for,
    sandbox_profile,
    workspace_python,
)
from campsverso_adapters.hands_gate import Dialect, HandsGate, Tape
from campsverso_ports import (
    CallMeter,
    HandsJob,
    HandsLimits,
    HandsResult,
    HandsStep,
    HandsWorld,
    Workspace,
)

MAX_SUMMARY = 200
MAX_RESULT = 500
# Depois de parar, quanto tempo ainda ler a saída pelos tokens, e esperar o processo acabar.
GRACE_SECONDS = 5.0
# Nenhuma variável com estes pedaços no nome vem do ambiente de quem chama.
SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD")

type Turn = Literal["tool", "message"]
type Warn = Callable[[str, Mapping[str, Any]], None]


@dataclass(frozen=True, slots=True)
class Read:
    """O que um evento é para a sessão: os passos para a tela e, se for o caso, uma volta (uma
    ferramenta concluída, ou uma mensagem do modelo, com o texto)."""

    steps: tuple[HandsStep, ...] = ()
    turn: Turn | None = None
    text: str = ""


class Stream(Protocol):
    """O leitor da saída de um harness, um por sessão."""

    completed: bool
    failed: str | None

    def account(self, data: Mapping[str, Any]) -> None:
        """O que vale mesmo depois de parar: os tokens, a falha e o fim da sessão."""
        ...

    def read(self, data: Mapping[str, Any]) -> Read:
        """O que o evento é para a sessão, enquanto ela corre."""
        ...

    def closes(self, data: Mapping[str, Any]) -> bool:
        """O evento fecha a resposta: uma mensagem logo antes dele era a final."""
        ...


@dataclass(frozen=True, slots=True)
class Outcome:
    stopped: str | None
    returncode: int | None
    turns: int
    steps: int
    last_text: str


class Refusal:
    """A recusa da porta das mãos numa sessão: o mundo pede para parar (o teto do pedido ou do dia)
    ou o custo medido chegou ao teto da sessão, que só a porta vê a cada chamada."""

    def __init__(self, world: HandsWorld, max_usd: float) -> None:
        self._world = world
        self._max = max_usd
        self.reason: str | None = None
        self.spent: Callable[[], float] = lambda: 0.0

    def __call__(self) -> str | None:
        if self._world.should_stop():
            self.reason = "parada"
        elif self.spent() >= self._max:
            self.reason = "teto da sessão"
        else:
            return None
        return self.reason


def clean_environment(root: Path, casa: str) -> dict[str, str]:
    """O ambiente de um harness, do zero: o caminho dos programas (o `.venv` do espaço à frente,
    para os comandos do dev), uma casa e um temporário dentro do espaço, e a língua. Nada vem do
    ambiente de quem chama."""
    local = root / ".oficina"
    home = local / casa
    tmp = local / "tmp"
    for folder in (home, tmp):
        folder.mkdir(parents=True, exist_ok=True)
    bins = [str(root / ".venv" / "bin"), "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    environment = {
        "PATH": os.pathsep.join(bins),
        "HOME": str(home),
        "TMPDIR": str(tmp),
        "LANG": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return {k: v for k, v in environment.items() if not any(m in k.upper() for m in SECRET_MARKERS)}


def relative(root: Path, given: str) -> str:
    """O caminho relativo ao espaço; o harness pode dar o absoluto. Fora do espaço, fica como
    veio."""
    raw = Path(given)
    if not raw.is_absolute():
        return given
    real = root.resolve()
    target = raw.resolve()
    if target == real or real in target.parents:
        return str(target.relative_to(real))
    return given


def first_line(text: str, limit: int = MAX_SUMMARY) -> str:
    return next((x.strip() for x in text.splitlines() if x.strip()), "")[:limit]


def parse_line(line: bytes, warn: Warn, harness: str) -> Mapping[str, Any] | None:
    """Um evento da saída, ou nada para a linha vazia, a quebrada e a que não é um objeto."""
    text = line.decode("utf-8", errors="replace").strip()
    if not text:
        return None
    try:
        event = json.loads(text)
    except json.JSONDecodeError:
        warn(f"hands.{harness}_bad_line", {"line": text[:200]})
        return None
    return cast(Mapping[str, Any], event) if isinstance(event, Mapping) else None


async def run_session(
    argv: Sequence[str],
    *,
    root: Path,
    environment: Mapping[str, str],
    briefing: bytes | None,
    limits: HandsLimits,
    world: HandsWorld,
    spent: Callable[[], float],
    stream: Stream,
    log: IO[bytes],
    parse: Callable[[bytes], Mapping[str, Any] | None],
    errors: IO[bytes] | None = None,
) -> Outcome:
    """Roda o processo de uma sessão e lê a saída até o fim, um teto ou o limite de tempo. A saída
    de erro do harness vai para `errors` (um arquivo ao lado da conversa), quando dado."""
    process = await asyncio.create_subprocess_exec(
        *argv,
        cwd=str(root),
        env=dict(environment),
        stdin=asyncio.subprocess.DEVNULL if briefing is None else asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL if errors is None else errors,
        limit=16 * 1024 * 1024,
        start_new_session=True,
    )
    assert process.stdout is not None
    stdout = process.stdout
    steps = 0
    turns = 0
    last_text = ""
    stopped: str | None = None
    # Um teto alcançado numa mensagem: só vale se a sessão seguir depois dela.
    held: str | None = None

    def over() -> str | None:
        if world.should_stop():
            return "parada"
        if turns >= limits.max_turns:
            return "limite de voltas"
        if spent() >= limits.max_usd:
            return "teto da sessão"
        return None

    def record(line: bytes) -> Mapping[str, Any] | None:
        log.write(line if line.endswith(b"\n") else line + b"\n")
        # Uma sessão que cai no meio deixa no arquivo o que já aconteceu.
        log.flush()
        data = parse(line)
        if data is not None:
            stream.account(data)
        return data

    try:
        async with asyncio.timeout(limits.max_seconds):
            if briefing is not None:
                assert process.stdin is not None
                process.stdin.write(briefing)
                with contextlib.suppress(ConnectionError):
                    await process.stdin.drain()
                process.stdin.close()
            async for line in stdout:
                data = record(line)
                if data is None:
                    continue
                if held is not None and not stream.closes(data):
                    # A mensagem não era a final: a sessão seguiu depois dela.
                    stopped = held
                    break
                got = stream.read(data)
                for step in got.steps:
                    steps += 1
                    await world.step(step)
                if got.turn is None:
                    continue
                turns += 1
                if got.turn == "message":
                    last_text = got.text or last_text
                    # A resposta final nunca é cortada: o teto espera o que vem depois.
                    held = over()
                else:
                    stopped = over()
                    if stopped is not None:
                        break
            if stopped is None:
                # A saída acabou; o fim do harness também cabe no limite de tempo.
                await process.wait()
    except TimeoutError:
        stopped = "limite de tempo"
    finally:
        if stopped is not None:
            _signal_group(process, signal.SIGTERM)
            if not stream.completed:
                with contextlib.suppress(TimeoutError, ValueError):
                    async with asyncio.timeout(GRACE_SECONDS):
                        async for line in stdout:
                            record(line)
        await _end(process)
    return Outcome(stopped, process.returncode, turns, steps, last_text)


def _signal_group(process: asyncio.subprocess.Process, sig: signal.Signals) -> None:
    """Um sinal para o grupo do harness: ele abre o seu próprio (`start_new_session`), e os
    comandos que ele roda ficam no mesmo grupo."""
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(process.pid, sig)


async def _end(process: asyncio.subprocess.Process) -> None:
    """Espera o fim do processo; se ele ainda roda, termina o grupo e, sem resposta, mata. No fim,
    mata o que sobrou no grupo, mesmo com o harness já fora."""
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


class ProcessHands:
    """As mãos de um harness que roda como processo. Cada harness diz o nome (`harness`, o do
    contrato; `title`, o da tela e dos erros), a língua da porta (`dialect`), o comando, o ambiente
    e a configuração da sessão (`prepare`), o briefing e o leitor da saída.

    `command` é como abrir o harness: o programa dele, achado no `PATH` de quem chama, ou um falso
    nos testes. `home` é a pasta das
    sessões, fora dos espaços: o perfil do cercado e a conversa de cada uma. `readable` é o que o
    cercado ainda deixa ler fora do espaço, além do harness e do Python do espaço."""

    harness = ""
    title = ""
    program = ""

    def __init__(
        self,
        meter: CallMeter,
        *,
        api_key: str,
        home: Path,
        command: Sequence[str] | None = None,
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
        # Absoluta: o harness roda com o diretório no espaço, e o perfil do cercado e a conversa
        # ficam aqui (uma pasta relativa, como o `PASTA=` da comparação, não era achada; 23/nov).
        self._home = home.resolve()
        self._command = list(command or (self.program,))
        self._sandbox = sys.platform == "darwin" if sandbox is None else sandbox
        self._upstream = upstream
        self._transport = transport
        self._reel = None if tape is None or tape_mode is None else Tape(tape, tape_mode)
        self._readable = [p.resolve() for p in readable]
        self._warn: Warn = warn or _no_warning
        self._user_home = (user_home or Path.home()).resolve()
        self.sessions = 0
        self.last_environment: dict[str, str] = {}

    # ------------------------------------------------------------- o que cada harness diz

    def dialect(self) -> Dialect:
        raise NotImplementedError

    def priced_model(self, job: HandsJob) -> str:
        """O nome do modelo na tabela de preços, conferido antes de abrir o harness."""
        return self.dialect().priced(job.model)

    def argv(self, root: Path, job: HandsJob) -> list[str]:
        raise NotImplementedError

    def prepare(self, root: Path, gate: HandsGate, job: HandsJob) -> dict[str, str]:
        """O ambiente da sessão, com a configuração do provedor escrita na casa dela."""
        raise NotImplementedError

    def briefing(self, job: HandsJob) -> bytes | None:
        """O que vai pela entrada padrão; nada, quando o briefing vai na linha de comando."""
        return None

    def stream(self, root: Path) -> Stream:
        raise NotImplementedError

    def finished(self, stream: Stream) -> None:
        """Depois da sessão, com o leitor dela: o que o harness guarda para conferir."""
        return None

    def summary(self, outcome: Outcome, stream: Stream) -> str:
        """O resumo da entrega: a última mensagem do modelo."""
        return outcome.last_text

    # ------------------------------------------------------------- a sessão

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
        try:
            self._meter.assert_priced(self.priced_model(job))
        except LookupError as error:
            raise ValueError(f"o modelo {job.model} não tem preço na tabela") from error
        # O espaço absoluto: a casa do harness, o `--cd` e o cercado valem de qualquer diretório.
        root = space.root.resolve()
        argv = self.argv(root, job)
        self.sessions += 1
        folder = self._home / job.ticket_id
        folder.mkdir(parents=True, exist_ok=True)
        transcript = folder / f"{self.harness}-{self.sessions}-{int(time.time())}.jsonl"
        tape = None if self._reel is None else self._reel.at(root)
        refusal = Refusal(world, job.limits.max_usd)
        gate = HandsGate(
            self._meter,
            api_key=self._key,
            harness=self.harness,
            avatar_id=job.avatar_id,
            ticket_id=job.ticket_id,
            refuse=refusal,
            upstream=self._upstream,
            transport=self._transport,
            tape=tape,
            dialect=self.dialect(),
            world=world,
        )
        refusal.spent = lambda: gate.cost_usd
        stream = self.stream(root)
        async with gate:
            environment = self.prepare(root, gate, job)
            self.last_environment = dict(environment)
            fenced = self._fence(folder, root, gate, argv)
            # A saída de erro do harness, ao lado da conversa: a sessão que cai sem dizer nada na
            # saída deixa ali o porquê (a prova de 23/nov).
            with transcript.open("wb") as log, transcript.with_suffix(".stderr").open("wb") as err:
                outcome = await run_session(
                    fenced,
                    root=root,
                    environment=environment,
                    briefing=self.briefing(job),
                    limits=job.limits,
                    world=world,
                    spent=lambda: gate.cost_usd,
                    stream=stream,
                    log=log,
                    parse=lambda line: parse_line(line, self._warn, self.harness),
                    errors=err,
                )
        self.finished(stream)
        # A falha que vem da nossa parada é a própria parada.
        if stream.failed is not None and outcome.stopped is None:
            self._warn(f"hands.{self.harness}_failed", {"error": stream.failed[:500]})
        if outcome.stopped is not None:
            reason = outcome.stopped
        elif refusal.reason is not None:
            reason = refusal.reason
        elif stream.failed is not None:
            reason = "erro na sessão"
        elif not stream.completed:
            reason = "sem resposta final"
        elif outcome.returncode != 0:
            reason = f"o {self.title} falhou"
        else:
            reason = "pronto"
        return HandsResult(
            reason == "pronto",
            self.summary(outcome, stream).strip()[:MAX_RESULT],
            outcome.turns,
            outcome.steps,
            reason,
            round(gate.cost_usd, 8),
        )
