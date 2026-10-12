"""O que um cartucho declara para montar o mundo."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from campsverso_cartridge_api.model import Attributes, ControllerRef, Direction, Position, Scalar


@dataclass(frozen=True, slots=True)
class ClockDef:
    """Passo fixo e fases do dia (tempo §3.1; bíblia §3)."""

    tick_seconds: int
    day_starts_at: str  # "HH:MM": virada do dia (dia agrícola na fazenda)
    phases: tuple[tuple[str, str], ...]  # (nome, "HH:MM")
    default_scale: float = 1.0  # segundos simulados por segundo real no modo contínuo


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
    role: Literal["energy"] | None = (
        None  # qual necessidade os eventos de sono reportam como energia
    )


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


type ChoiceSource = Literal["any", "inventory", "target"]


@dataclass(frozen=True, slots=True)
class AffordanceParam:
    """Um parâmetro que quem joga escolhe (ADR-0051). Sem `choices`, é um número inteiro.

    `source` diz onde as escolhas valem: `any` (a lista toda), `inventory` (só o que o avatar tem)
    ou `target` (só o que a entidade clicada guarda). É sugestão para o menu; o kernel decide.
    """

    name: str
    label: str
    choices: tuple[str, ...] = ()
    source: ChoiceSource = "any"
    minimum: int | None = None
    default: int | None = None


@dataclass(frozen=True, slots=True)
class AffordanceDef:
    """Uma ação no menu de um tipo de entidade, ou do próprio avatar (`self`) (ADR-0051).

    Com `target`, a entidade clicada vai no parâmetro `target` da ação.
    """

    action: str
    label: str
    on: tuple[str, ...]
    target: bool = True
    params: tuple[AffordanceParam, ...] = ()
