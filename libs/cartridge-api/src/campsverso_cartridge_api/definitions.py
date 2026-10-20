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
    weight: float = 0.0  # por unidade; conta contra a capacidade do contêiner (ADR-0062)
    shelf_life_days: int | None = None  # com validade, o item vive em lotes e estraga (ADR-0062)


@dataclass(frozen=True, slots=True)
class KindDef:
    """Valores padrão de um tipo de entidade, aplicados a cada entidade criada desse tipo."""

    kind: str
    blocking: bool = False
    attributes: Attributes = field(default_factory=dict[str, Scalar])
    hidden: Attributes = field(default_factory=dict[str, Scalar])
    capacity: float | None = None  # peso máximo que guarda; None é sem limite (ADR-0062)
    shelf_life_factor: float = 1.0  # multiplica a validade do que guarda (o baú conserva; oculto)
    weight: float = 0.0  # o que uma entidade deste tipo pesa quando guardada (uma ferramenta)


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


type MetricKind = Literal["count", "max_need", "item"]


@dataclass(frozen=True, slots=True)
class MetricDef:
    """Uma métrica do dia simulado, contada pela projeção comum e mostrada ao operador (ADR-0054).

    - `count`: quantos eventos `event` houve no dia, só os que batem com `where` (caminhos com
      ponto, ex. `params.target`). Com `by_field`, um valor por grupo: o valor do campo, ou, com
      `by_attribute`, o atributo da entidade cujo id está no campo.
    - `max_need`: o pico da necessidade `need` no dia.
    - `item`: a quantidade do item `item` com os avatares no fim do dia.
    """

    id: str
    label: str
    kind: MetricKind
    event: str | None = None
    where: Mapping[str, Scalar] = field(default_factory=dict[str, Scalar])
    by_field: str | None = None
    by_attribute: str | None = None
    need: str | None = None
    item: str | None = None
