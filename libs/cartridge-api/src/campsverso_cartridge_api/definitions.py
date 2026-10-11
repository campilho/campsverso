"""O que um cartucho declara para montar o mundo."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from campsverso_cartridge_api.model import Attributes, ControllerRef, Direction, Position, Scalar


@dataclass(frozen=True, slots=True)
class ClockDef:
    """Passo fixo e fases do dia (tempo §3.1; bíblia §3)."""

    tick_seconds: int
    day_starts_at: str  # "HH:MM": virada do dia (dia agrícola na fazenda)
    phases: tuple[tuple[str, str], ...]  # (nome, "HH:MM")


@dataclass(frozen=True, slots=True)
class ItemDef:
    item_id: str
    category: str
    properties: Mapping[str, Scalar] = field(default_factory=dict[str, Scalar])


@dataclass(frozen=True, slots=True)
class KindDef:
    """Valores padrão de um tipo de entidade, aplicados a cada entidade criada desse tipo."""

    kind: str
    blocking: bool = False
    attributes: Attributes = field(default_factory=dict[str, Scalar])
    hidden: Attributes = field(default_factory=dict[str, Scalar])


@dataclass(frozen=True, slots=True)
class NeedDef:
    """Medidor de 0 a 100 com taxa por hora para cada estado do avatar (`awake`, `asleep`)."""

    need: str
    initial: float
    rates_per_hour: Mapping[str, float] = field(default_factory=dict[str, float])


@dataclass(frozen=True, slots=True)
class ThresholdDef:
    need: str
    value: float
    direction: Direction
    requests_decision: bool


@dataclass(frozen=True, slots=True)
class SpawnDef:
    entity_id: str
    kind: str
    position: Position | None = None
    container_id: str | None = None
    blocking: bool = False
    display_name: str | None = None
    attributes: Attributes = field(default_factory=dict[str, Scalar])
    hidden: Attributes = field(default_factory=dict[str, Scalar])


@dataclass(frozen=True, slots=True)
class AvatarDef:
    entity_id: str
    default_controller: ControllerRef
