"""Ações, sistemas e regras que um cartucho registra no kernel."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from campsverso_cartridge_api.model import Direction, EntityView, Scalar
from campsverso_cartridge_api.world import WorldOps, WorldView


@dataclass(frozen=True, slots=True)
class Rejection:
    reason: str  # legível por máquina: not_adjacent, missing_item, closed...
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class Accepted:
    duration_ticks: int  # pelo menos 1 (ADR-0038)


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

    @property
    def cancellable(self) -> bool: ...

    def validate(self, ctx: ActionContext) -> Validation:
        """Pré-condições na hora da proposta. Não muda o mundo."""
        ...

    def complete(self, ctx: ActionContext, ops: WorldOps) -> None:
        """Efeitos na conclusão, inclusive o custo (ADR-0038)."""
        ...


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
