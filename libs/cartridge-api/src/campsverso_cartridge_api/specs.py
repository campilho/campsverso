"""Ações, sistemas e regras que um cartucho registra no kernel."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from campsverso_cartridge_api.model import Direction, EntityView, Scalar
from campsverso_cartridge_api.world import WorldOps, WorldView


@dataclass(frozen=True, slots=True)
class Rejection:
    reason: str  # legível por máquina: not_adjacent, missing_item, closed...
    detail: str | None = None


type Interrupt = Literal["never", "cancel", "partial"]
"""O que um comando novo do mesmo controlador faz com a ação em andamento (ADR-0052):
`never` recusa com `busy`; `cancel` cancela, e nada da ação acontece; `partial` interrompe, e o
cartucho grava o trabalho feito (`ActionSpec.interrupted`)."""


@dataclass(frozen=True, slots=True)
class Accepted:
    duration_ticks: int  # pelo menos 1 (ADR-0038)
    interrupt: Interrupt = "never"  # decidida na validação, com os dados do mundo (ADR-0052)


type Validation = Rejection | Accepted


@dataclass(frozen=True, slots=True)
class ActionContext:
    avatar_id: str
    action_id: str
    params: Mapping[str, Any]
    view: WorldView


class ActionSpec(Protocol):
    @property
    def name(self) -> str: ...

    def validate(self, ctx: ActionContext) -> Validation:
        """Pré-condições na hora da proposta. Não muda o mundo."""
        ...

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        """Efeitos na conclusão, inclusive o custo (ADR-0038)."""
        ...

    def interrupted(self, ctx: ActionContext, ops: WorldOps, elapsed_ticks: int) -> None:
        """Só nas ações `partial`: grava o trabalho feito em `elapsed_ticks` (ADR-0052)."""
        ...


@runtime_checkable
class Rechecked(Protocol):
    """Uma ação que, na conclusão, confere se outro avatar não a desfez no meio (ADR-0072): o
    canteiro que ele colheu antes, a semente que ele plantou no mesmo lugar, o item que ele tirou
    do baú. Se não vale mais, o kernel publica `action.failed` (`precondition_lost`) em vez de
    concluir. Só o que outro avatar pode mudar: o que muda com a hora não entra aqui."""

    def recheck(self, ctx: ActionContext) -> Rejection | None: ...


@dataclass(frozen=True, slots=True)
class DailyAt:
    times: tuple[str, ...]  # "HH:MM"


@dataclass(frozen=True, slots=True)
class OnThreshold:
    need: str
    value: float
    direction: Direction


@dataclass(frozen=True, slots=True)
class OnSessionStart:
    pass


type Trigger = DailyAt | OnThreshold | OnSessionStart


@dataclass(frozen=True, slots=True)
class SystemContext:
    view: WorldView
    trigger: Trigger
    avatar_id: str | None = None  # quem cruzou o limiar, em OnThreshold


class SystemSpec(Protocol):
    """Sistema do mundo: função de estado, tick e RNG nomeado (princípio 4)."""

    @property
    def name(self) -> str: ...

    @property
    def stage(self) -> str:
        """Etapa do tick em que roda (ADR-0037)."""
        ...

    @property
    def priority(self) -> int: ...

    @property
    def triggers(self) -> tuple[Trigger, ...]: ...

    def run(self, ctx: SystemContext, ops: WorldOps) -> None: ...


class RuleImpl(Protocol):
    """Implementação de regra; a instância (ligada, parâmetros, oculta) vem das flags."""

    @property
    def name(self) -> str: ...

    @property
    def target(self) -> str:
        """O que a regra modifica, ex.: growth_points."""
        ...

    def apply(
        self, view: WorldView, entity: EntityView, value: float, params: Mapping[str, Scalar]
    ) -> float: ...
