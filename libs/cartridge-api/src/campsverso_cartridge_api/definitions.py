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
class YearDef:
    """Um ano acelerado com estações (ADR-0067). A data do calendário anda à parte do `simtime`:
    o ano inteiro cabe em `days` dias simulados, e a estação vale pela data."""

    days: int  # dias simulados que o ano dura
    start: str  # "MM-DD": a data do calendário no dia 1
    seasons: tuple[tuple[str, str], ...]  # (nome, "MM-DD" em que a estação começa)


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
class AvatarTraits:
    """O que distingue um avatar dos outros no corpo (ADR-0072), em fatores sobre o mundo: o
    kernel aplica sem saber o que é uma plantadeira. O padrão é um avatar como os outros."""

    speed: float = 1.0  # fator nos tiles por tick ao andar
    action_time: Mapping[str, float] = field(default_factory=dict[str, float])  # ação ou "*"
    need_rates: Mapping[str, float] = field(default_factory=dict[str, float])  # fator no ritmo
    energy_cost: float = 1.0  # fator no que as ações gastam da necessidade de energia
    capacity: float | None = None  # o peso que carrega; sem isto, o do tipo
    faints: bool = True  # False: nunca desmaia
    vision: float = 1.0  # fator no raio da percepção
    night_vision: bool = False  # enxerga à noite com o raio do dia

    def time_factor(self, action: str) -> float:
        return float(self.action_time.get(action, self.action_time.get("*", 1.0)))


@dataclass(frozen=True, slots=True)
class AvatarDef:
    entity_id: str
    default_controller: ControllerRef
    traits: AvatarTraits = field(default_factory=AvatarTraits)
    # Fora do mundo no começo (ADR-0072): sem posição, sem pedidos de decisão, até `enter`.
    present: bool = True


type ChoiceSource = Literal["any", "inventory", "target"]


@dataclass(frozen=True, slots=True)
class AffordanceParam:
    """Um parâmetro que quem joga escolhe (ADR-0051). Sem `choices`, é um número inteiro.

    `source` diz onde as escolhas valem: `any` (a lista toda), `inventory` (só o que o avatar tem)
    ou `target` (só o que a entidade clicada guarda). É sugestão para o menu; o kernel decide.
    `entities` acrescenta às escolhas as entidades guardadas na fonte, pelo id (as ferramentas).
    Para o menu mostrar o preço (M21): `prices` é o de tabela de cada escolha; `price_attribute`,
    o começo do nome do atributo do alvo com o preço de agora (`preco_` + a escolha); e
    `stock_attribute`, o atributo do alvo com o que há hoje, separado por vírgula.
    """

    name: str
    label: str
    choices: tuple[str, ...] = ()
    source: ChoiceSource = "any"
    minimum: int | None = None
    default: int | None = None
    entities: bool = False
    prices: tuple[tuple[str, float], ...] = ()
    price_attribute: str | None = None
    stock_attribute: str | None = None


@dataclass(frozen=True, slots=True)
class AffordanceDef:
    """Uma ação no menu de um tipo de entidade, ou do próprio avatar (`self`) (ADR-0051).

    Com `target`, a entidade clicada vai no parâmetro `target` da ação. Para o menu (M21): `cost`
    é a energia e os minutos da tabela do cartucho, e `note`, uma nota como o horário.
    """

    action: str
    label: str
    on: tuple[str, ...]
    target: bool = True
    params: tuple[AffordanceParam, ...] = ()
    cost: tuple[float, int] | None = None  # (energia, minutos)
    note: str | None = None


type MetricKind = Literal["count", "max_need", "item"]


@dataclass(frozen=True, slots=True)
class EventLabelDef:
    """Como a linha do tempo conta um tipo de evento (ADR-0068): o texto, com campos do evento
    entre chaves (`colheu {qty} {item}`), para os eventos que batem com `where`. A tela usa o mais
    específico cujos campos existem no evento, e o tipo cru quando nenhum serve."""

    event: str
    text: str
    where: Mapping[str, Scalar] = field(default_factory=dict[str, Scalar])


@dataclass(frozen=True, slots=True)
class MetricDef:
    """Uma métrica do dia simulado, contada pela projeção comum e mostrada ao operador (ADR-0054).

    - `count`: quantos eventos `event` houve no dia, só os que batem com `where` (caminhos com
      ponto, ex. `params.target`). Com `by_field`, um valor por grupo: o valor do campo, ou, com
      `by_attribute`, o atributo da entidade cujo id está no campo.
      Com `field`, soma esse campo de cada evento, em vez de contar (ADR-0069).
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
    field: str | None = None
