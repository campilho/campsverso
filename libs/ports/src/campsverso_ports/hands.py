"""A porta das mãos (ADR-0089): quem programa no espaço de um pedido.

O dev tem uma mente só, que decide no mundo pela porta de modelo. As mãos são quem trabalha no
espaço da oficina: o nosso harness (a `WorkSession`, com as oito ferramentas) ou um harness de
fora, como o Claude Code. Do patch em diante, nada depende de quem programou: a revisão da oficina,
o depósito de entregas, o PR e o revisor seguem iguais.

As mãos recebem o pedido (`HandsJob`) e o que o mundo oferece a elas (`HandsWorld`): chamar um robô
da bancada, anotar na memória, mostrar um passo na tela e saber se é hora de parar.

Quando quem chama o modelo é um harness de fora, a chamada passa pela porta das mãos (`CallMeter`):
ela mede cada resposta como a porta de modelo mede as nossas, e a guarda soma como sempre.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from campsverso_ports.model import Effort, ModelRequest, ModelResponse
from campsverso_ports.workshop import ToolResult, Workspace

# As mãos que o escritório conhece, pelo nome dos contratos (o campo `harness`).
HARNESSES = ("api", "claude_code")


@dataclass(frozen=True, slots=True)
class HandsLimits:
    """Os tetos de uma sessão (ADR-0089, decisão 8): as voltas, o custo estimado pelo harness e
    o relógio. O teto do pedido e o do dia são da guarda."""

    max_turns: int = 80
    max_usd: float = 4.0
    max_seconds: float = 45 * 60


@dataclass(frozen=True, slots=True)
class HandsJob:
    """O trabalho de um pedido: o texto que abre a sessão (o briefing), as instruções de quem é o
    dev e das regras do escritório, o modelo, o esforço e os tetos."""

    ticket_id: str
    opening: str
    system: str
    model: str
    avatar_id: str
    effort: Effort | None = "medium"
    limits: HandsLimits = HandsLimits()


@dataclass(frozen=True, slots=True)
class HandsStep:
    """Um passo das mãos, para a tela: a ferramenta pelo nome que o harness usa."""

    tool: str
    summary: str
    ok: bool
    duration_ms: int
    path: str | None = None


@dataclass(frozen=True, slots=True)
class HandsResult:
    """Como a sessão acabou. `done` é o fim normal (o `pronto`, ou a resposta final do harness);
    `summary` é o resumo do dev para a entrega; `cost_usd` é o que as mãos mediram, quando medem
    (o custo que vale é o da guarda); `tests` é a primeira linha dos últimos testes, quando as mãos
    os rodam por uma ferramenta própria."""

    done: bool
    summary: str
    turns: int
    steps: int
    reason: str
    cost_usd: float | None = None
    tests: str = ""


@dataclass(frozen=True, slots=True)
class Robot:
    """Um robô da bancada, como as mãos o oferecem ao modelo."""

    name: str
    description: str


class HandsWorld(Protocol):
    """O que o mundo oferece às mãos, de um pedido."""

    @property
    def robots(self) -> Sequence[Robot]: ...

    async def robot(self, name: str, args: Sequence[str]) -> ToolResult:
        """Chama um robô da bancada no espaço; a bancada anima na tela."""
        ...

    async def note(self, text: str) -> ToolResult:
        """Anota na memória do dev (sem memória ligada, recusa)."""
        ...

    async def step(self, step: HandsStep) -> None:
        """Mostra um passo na tela e no diário."""
        ...

    def should_stop(self) -> bool:
        """O teto do pedido ou do dia, ou a mente desligada: parar entre um passo e outro."""
        ...


class Hands(Protocol):
    @property
    def harness(self) -> str:
        """O nome das mãos, um de `HARNESSES`."""
        ...

    async def run(self, space: Workspace, job: HandsJob, world: HandsWorld) -> HandsResult: ...


class CallMeter(Protocol):
    """Quem mede as chamadas que um harness de fora faz ao modelo: o mesmo evento e a mesma guarda
    da porta de modelo (ADR-0058, ADR-0089)."""

    def assert_priced(self, model: str) -> None: ...

    async def observed(
        self, request: ModelRequest, response: ModelResponse, *, harness: str
    ) -> float:
        """Publica a chamada como a porta de modelo publica as nossas e devolve o custo dela."""
        ...
