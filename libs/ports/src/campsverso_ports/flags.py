"""Porta das flags de regras: estado inicial de cada regra, inclusive as ocultas (contratos §12)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

type Scalar = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class RuleConfig:
    rule: str  # instância no mundo, ex.: river_proximity_bonus
    impl: str  # implementação no cartucho, ex.: water_proximity_bonus
    version: str
    hidden: bool
    enabled: bool
    params: Mapping[str, Scalar] = field(default_factory=dict[str, Scalar])


class FlagPort(Protocol):
    def rules(self) -> Sequence[RuleConfig]: ...
