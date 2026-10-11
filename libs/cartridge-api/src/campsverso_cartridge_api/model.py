"""Tipos básicos do modelo de mundo, vistos pelos cartuchos (ADR-0025)."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

type Scalar = str | int | float | bool | None
type Attributes = Mapping[str, Scalar]
type Direction = Literal["up", "down"]
type ControllerType = Literal["human", "script", "replay", "llm", "mcp", "supervised"]


@dataclass(frozen=True, slots=True, order=True)
class Position:
    x: int
    y: int

    def chebyshev(self, other: Position) -> int:
        """Distância com vizinhança de 8 (bíblia §4: interação a até 1 tile)."""
        return max(abs(self.x - other.x), abs(self.y - other.y))


@dataclass(frozen=True, slots=True)
class ControllerRef:
    type: ControllerType
    id: str


@dataclass(frozen=True, slots=True)
class EntityView:
    """Foto somente-leitura de uma entidade."""

    entity_id: str
    kind: str
    position: Position | None
    container_id: str | None
    blocking: bool
    display_name: str | None = None
    attributes: Attributes = field(default_factory=dict[str, Scalar])  # visíveis
    hidden: Attributes = field(default_factory=dict[str, Scalar])  # nunca saem em eventos world
