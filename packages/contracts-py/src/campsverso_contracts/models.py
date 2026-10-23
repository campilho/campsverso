# GERADO por tools/contracts a partir de contracts/: não editar à mão.

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel
from typing import Annotated, Any, Literal
from typing_extensions import TypeAliasType
from datetime import date as date_aliased


class ContractsBundle(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )


class EntityId(RootModel[str]):
    root: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """


class Token(RootModel[str]):
    root: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """


class Position(BaseModel):
    """
    Posição em tiles.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    x: Annotated[int, Field(ge=0)]
    y: Annotated[int, Field(ge=0)]


class ItemStack(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    item: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(_[a-z0-9]+)*$", title="ItemId")]
    """
    Id de item ou cultura; conteúdo do cartucho, em português, sem acento: moeda, semente_rabanete.
    """
    qty: Annotated[int, Field(ge=1)]
    expires_in_days: int | None = None
    """
    Dias até o lote mais antigo vencer pela validade nominal, quando o item tem validade (ADR-0062); zero vence hoje, negativo já passou da data e ainda não estragou (o contêiner conserva).
    """


class ControllerRef(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    type: Annotated[
        Literal["human", "script", "replay", "llm", "mcp", "supervised"],
        Field(title="ControllerType"),
    ]
    id: Annotated[str, Field(max_length=128, min_length=1)]


NeedsAdditionalProperty = TypeAliasType(
    "NeedsAdditionalProperty", Annotated[float, Field(ge=0.0, le=100.0)]
)


class Choice(RootModel[str]):
    root: Annotated[str, Field(max_length=64, min_length=1)]


class AffordanceParam(BaseModel):
    """
    Um parâmetro que quem joga escolhe (ADR-0051). Sem `choices`, é um número inteiro.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    name: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    O nome do parâmetro na ação (crop, item, qty…).
    """
    label: Annotated[str, Field(max_length=64, min_length=1)]
    choices: list[Choice] | None = None
    source: Literal["any", "inventory", "target"]
    """
    Onde as escolhas valem: a lista toda, o que o avatar tem ou o que a entidade clicada guarda.
    """
    minimum: int | None = None
    default: int | None = None


class Affordance(BaseModel):
    """
    Uma ação no menu de um tipo de entidade, ou do próprio avatar (`self`). O menu só sugere; quem decide é o kernel (ADR-0051).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    action: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    label: Annotated[str, Field(max_length=64, min_length=1)]
    on: Annotated[list[Token], Field(min_length=1)]
    """
    Tipos de entidade em que a ação aparece; `self` é o próprio avatar.
    """
    target: bool
    """
    A entidade clicada vai no parâmetro `target`.
    """
    params: list[AffordanceParam] | None = None


class MetricGroup(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    field: Annotated[str, Field(pattern="^[a-z0-9_]+(\\.[a-z0-9_]+)*$")]
    attribute: Annotated[
        str | None, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")
    ] = None
    """
    Agrupa pelo atributo da entidade cujo id está no campo (o `group` do canteiro).
    """


class Metric(BaseModel):
    """
    Uma métrica do dia simulado, declarada pelo cartucho e contada pela projeção comum (ADR-0054). `count` conta um tipo de evento; `max_need` guarda o pico de uma necessidade; `item` guarda a quantidade de um item com os avatares no fim do dia.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    id: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    label: Annotated[str, Field(max_length=60, min_length=1)]
    kind: Literal["count", "max_need", "item"]
    event: Annotated[
        str | None, Field(pattern="^campsverso\\.[a-z0-9_]+(\\.[a-z0-9_]+)*\\.v[0-9]+$")
    ] = None
    """
    O tipo de evento contado (`count`).
    """
    where: dict[str, str | float | bool | None] | None = None
    """
    Campos do evento que precisam bater; caminhos com ponto (`params.target`).
    """
    by: Annotated[MetricGroup | None, Field(title="MetricGroup")] = None
    need: Annotated[
        str | None, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")
    ] = None
    """
    A necessidade (`max_need`).
    """
    item: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(_[a-z0-9]+)*$", title="ItemId"),
    ] = None
    """
    O item (`item`).
    """


class SeenClock(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    sim_time: AwareDatetime
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    phase: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    date: date_aliased | None = None
    """
    A data do calendário do ano acelerado (ADR-0067), à parte do simtime; ausente sem ano declarado.
    """
    season: Annotated[
        str | None, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")
    ] = None
    """
    A estação da data (primavera, verao…), declarada pelo cartucho; ausente sem ano declarado.
    """


class SeenWeather(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    condition: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """


class SeenAction(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    action_id: Annotated[str, Field(pattern="^act-[0-9]{6,}$", title="ActionId")]
    """
    Id de ação: contador determinístico do kernel.
    """
    action: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    params: dict[str, Any]
    end_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    applied_tick: Annotated[int | None, Field(ge=0, title="Tick")] = None
    """
    Tick em que a ação começou (ADR-0052).
    """
    interrupt: Annotated[Literal["never", "cancel", "partial"] | None, Field(title="Interrupt")] = (
        None
    )
    """
    O que um comando novo do mesmo controlador faz com esta ação em andamento (ADR-0052).
    """


class SeenSelf(BaseModel):
    """
    O próprio avatar: posição, necessidades, se dorme e a ação em curso.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    position: Position
    needs: dict[str, NeedsAdditionalProperty]
    asleep: bool
    action: SeenAction | None = None


class SeenContainer(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    container_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    items: list[ItemStack]


class SeenEntity(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    kind: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    position: Position | None = None
    container_id: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    attributes: dict[str, str | float | bool | None]


class DecisionRequest(BaseModel):
    """
    O pedido de decisão que a entrega da percepção responde: o motivo e quem deve responder (ADR-0048).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    reason: Literal[
        "session_started",
        "possessed",
        "action_completed",
        "action_rejected",
        "action_interrupted",
        "phase_changed",
        "need_threshold",
        "woke_up",
    ]
    controller: ControllerRef


class SeenEvent(BaseModel):
    """
    Um evento que o avatar percebeu desde a última entrega: o tick, o tipo e o payload, como foram publicados.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    type: Annotated[
        str,
        Field(
            max_length=128,
            pattern="^campsverso\\.[a-z0-9_]+(\\.[a-z0-9_]+)*\\.v[0-9]+$",
        ),
    ]
    data: dict[str, Any]


class TerrainTile(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    kind: Annotated[str, Field(max_length=64, pattern="^[a-z0-9_]*$")]
    """
    A classe do tile no tileset (grass, river…); vazia quando o tile não tem classe.
    """
    properties: dict[str, str | float | bool | None]
    """
    As propriedades do tile no tileset, como passable e water.
    """


class TerrainLegend(RootModel[dict[str, TerrainTile]]):
    """
    Legenda do terreno: o que cada caractere das linhas significa (ADR-0056).
    """

    root: Annotated[dict[str, TerrainTile], Field(min_length=1)]


class TerrainRow(RootModel[str]):
    root: Annotated[str, Field(max_length=1024, min_length=1)]


class TerrainWindow(BaseModel):
    """
    O terreno ao alcance do avatar: as linhas a partir de origin (o canto superior esquerdo da janela), com a legenda.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    origin: Position
    rows: Annotated[list[TerrainRow], Field(max_length=1024, min_length=1, title="TerrainRows")]
    """
    O terreno, uma string por linha e um caractere por tile, de cima para baixo e da esquerda para a direita (ADR-0056).
    """
    legend: TerrainLegend


class PerceptionConfig(BaseModel):
    """
    O que o cartucho declara sobre a percepção (ADR-0056).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    radius: Annotated[int | None, Field(ge=0)]
    """
    Distância de Chebyshev, em tiles, do que um avatar enxerga; null é o mapa inteiro.
    """


class LlmUsage(BaseModel):
    """
    Tokens de uma chamada de modelo, como o provedor os contou (ADR-0058): entrada, saída, lidos do cache e gravados no cache.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    input_tokens: Annotated[int, Field(ge=0)]
    output_tokens: Annotated[int, Field(ge=0)]
    cache_read_input_tokens: Annotated[int | None, Field(ge=0)] = None
    cache_creation_input_tokens: Annotated[int | None, Field(ge=0)] = None


class BeliefSource(BaseModel):
    """
    De onde a crença veio (contratos §8.4): do que o agente observou, ou de quem lhe contou (`by`).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    kind: Literal["observation", "told"]
    by: Annotated[str | None, Field(max_length=128, min_length=1)] = None
    """
    Quem contou, quando `kind` é `told`.
    """


class BeliefEvidenceItem(RootModel[str]):
    root: Annotated[str, Field(max_length=300, min_length=1)]


class CmdActionProposeV1(BaseModel):
    """
    Controlador propõe uma ação para o avatar.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    action: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    params: dict[str, Any]
    intent: Annotated[str | None, Field(max_length=500, min_length=1)] = None
    at_tick: Annotated[int | None, Field(ge=0, title="Tick")] = None
    """
    Tick exato de aplicação; só aceito do controlador replay em modo máximo.
    """


class CmdAvatarPossessV1(BaseModel):
    """
    Pede a posse do avatar para um controlador.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    controller: ControllerRef


class CmdAvatarReleaseV1(BaseModel):
    """
    Devolve o avatar ao controlador padrão do cartucho.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """


class CmdClockPauseV1(BaseModel):
    """
    Pede a pausa do relógio.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    reason: Literal["debug", "maintenance", "budget"]


class CmdClockResumeV1(BaseModel):
    """
    Pede a retomada do relógio.
    """

    model_config = ConfigDict(
        extra="ignore",
    )


class CmdClockSetModeV1(BaseModel):
    """
    Pede a troca de modo do relógio.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    mode: Annotated[Literal["continuous", "max"], Field(title="ClockMode")]
    """
    Modos do relógio na v0.1; a pausa é um estado à parte (ADR-0026).
    """
    reason: Annotated[str | None, Field(max_length=200, min_length=1)] = None


class CmdClockSetScaleV1(BaseModel):
    """
    Pede a troca de escala do relógio.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    scale: Annotated[float, Field(gt=0.0)]
    reason: Literal["operator", "experiment", "budget", "human"]


class CmdClockStepV1(BaseModel):
    """
    Avança N ticks com o relógio pausado.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    ticks: Annotated[int, Field(ge=1, le=1440)]


class CmdRulesToggleV1(BaseModel):
    """
    Pede a alternância de uma regra (ADR-0015).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    rule: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    enabled: bool
    params: dict[str, str | float | bool | None] | None = None
    """
    Parâmetros da regra.
    """
    reason: Annotated[str, Field(max_length=500, min_length=1)]
    experiment_id: Annotated[str | None, Field(max_length=64, min_length=1)] = None


class EnvelopeV1(BaseModel):
    """
    Envelope CloudEvents 1.0 com as extensões do Campsverso (contratos §5; ADR-0012, ADR-0013, ADR-0031). Os nomes dos atributos seguem o CloudEvents: minúsculas sem separador (ADR-0030).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    specversion: Literal["1.0"]
    id: Annotated[
        str,
        Field(
            pattern="^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            title="Uuid7",
        ),
    ]
    """
    UUID versão 7 (RFC 9562), ordenável por tempo.
    """
    source: Annotated[str, Field(max_length=256, min_length=1)]
    type: Annotated[str, Field(pattern="^campsverso\\.[a-z0-9_]+(\\.[a-z0-9_]+)+\\.v[0-9]+$")]
    time: AwareDatetime
    subject: Annotated[str | None, Field(max_length=256)] = None
    datacontenttype: Literal["application/json"]
    dataschema: Annotated[
        str,
        Field(pattern="^contracts://(events|commands)/[a-z0-9_]+/[a-z0-9_.]+\\.v[0-9]+$"),
    ]
    worldid: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$")]
    cartridge: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$")]
    tick: Annotated[int | None, Field(ge=0)] = None
    simtime: AwareDatetime | None = None
    seq: Annotated[int, Field(ge=0)]
    actor: Annotated[str | None, Field(max_length=128)] = None
    controller: Annotated[
        Literal["human", "script", "replay", "llm", "mcp", "supervised"] | None,
        Field(title="ControllerType"),
    ] = None
    controllerid: Annotated[str | None, Field(max_length=128)] = None
    causationid: Annotated[
        str | None,
        Field(
            pattern="^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            title="Uuid7",
        ),
    ] = None
    """
    UUID versão 7 (RFC 9562), ordenável por tempo.
    """
    correlationid: Annotated[
        str | None,
        Field(
            pattern="^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            title="Uuid7",
        ),
    ] = None
    """
    UUID versão 7 (RFC 9562), ordenável por tempo.
    """
    provenance: Literal["simulated", "real", "staged"]
    visibility: Literal["world", "agent", "observer", "internal"]
    traceparent: Annotated[str | None, Field(max_length=128)] = None
    data: dict[str, Any]


class ActionAcceptedV1(BaseModel):
    """
    Ação validada e agendada; applied_tick permite o replay exato.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    action_id: Annotated[str, Field(pattern="^act-[0-9]{6,}$", title="ActionId")]
    """
    Id de ação: contador determinístico do kernel.
    """
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    action: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    params: dict[str, Any]
    applied_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    duration_ticks: Annotated[int, Field(ge=0)]
    """
    Duração prevista.
    """
    replaces: Annotated[str | None, Field(pattern="^act-[0-9]{6,}$", title="ActionId")] = None
    """
    Ação em andamento cancelada por esta.
    """
    interrupt: Annotated[Literal["never", "cancel", "partial"] | None, Field(title="Interrupt")] = (
        None
    )
    """
    O que um comando novo do mesmo controlador faz com esta ação em andamento (ADR-0052).
    """
    intent: Annotated[str | None, Field(max_length=500, min_length=1)] = None
    """
    A intenção declarada na proposta (cmd.action.propose), copiada pelo kernel; a tela e a linha do tempo a mostram (ADR-0059).
    """


class ObservableChange(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    property: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    before: Annotated[str | float | bool | None, Field(title="Scalar")]
    after: Annotated[str | float | bool | None, Field(title="Scalar")]


class ActionCompletedV1(BaseModel):
    """
    Ação concluída; observable é só um resumo legível.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    action_id: Annotated[str, Field(pattern="^act-[0-9]{6,}$", title="ActionId")]
    """
    Id de ação: contador determinístico do kernel.
    """
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    action: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    params: dict[str, Any]
    duration_ticks: Annotated[int, Field(ge=0)]
    """
    Duração real.
    """
    observable: list[ObservableChange] | None = None


class RuleApplied(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    rule: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    version: Annotated[
        str,
        Field(
            pattern="^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$",
            title="Semver",
        ),
    ]
    hidden: bool
    multiplier: float | None = None


class ActionEffectsExplainedV1(BaseModel):
    """
    Regras, inclusive ocultas, que contribuíram para o resultado de uma ação.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    action_id: Annotated[str, Field(pattern="^act-[0-9]{6,}$", title="ActionId")]
    """
    Id de ação: contador determinístico do kernel.
    """
    rules_applied: Annotated[list[RuleApplied], Field(min_length=1)]


class ActionFailedV1(BaseModel):
    """
    Ação iniciada que não chegou ao fim.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    action_id: Annotated[str, Field(pattern="^act-[0-9]{6,}$", title="ActionId")]
    """
    Id de ação: contador determinístico do kernel.
    """
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    action: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    reason: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Ex.: cancelled, fainted, blocked, precondition_lost.
    """
    elapsed_ticks: Annotated[int | None, Field(ge=0)] = None
    """
    Quantos ticks a ação durou antes de parar (ADR-0052).
    """


class ActionRejectedV1(BaseModel):
    """
    Ação recusada, com motivo legível por máquina.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    action: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    params: dict[str, Any]
    reason: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Ex.: not_in_control, not_adjacent, missing_item, closed, not_ripe.
    """
    detail: Annotated[str | None, Field(max_length=500, min_length=1)] = None


class AvatarDecisionRequestedV1(BaseModel):
    """
    O avatar está ocioso; o controlador com a posse responde com cmd.action.propose e o mesmo correlationid.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    reason: Literal[
        "session_started",
        "possessed",
        "action_completed",
        "action_rejected",
        "action_interrupted",
        "phase_changed",
        "need_threshold",
        "woke_up",
    ]
    controller: ControllerRef
    """
    Quem deve responder.
    """
    needs: dict[str, NeedsAdditionalProperty]
    """
    Valores exatos no momento do pedido.
    """
    position: Position


class AvatarFaintedV1(BaseModel):
    """
    O avatar desmaiou: acordado às 02:00 ou sem energia (ADR-0014).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    reason: Literal["late_night", "exhausted"]
    position: Position


class AvatarPossessedV1(BaseModel):
    """
    Posse do avatar assumida por um controlador.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    previous_controller: ControllerRef | None = None
    """
    Ausente na abertura da sessão.
    """
    controller: ControllerRef
    by: Annotated[str, Field(max_length=128, min_length=1, title="Actor")]
    """
    Quem causou: human/operator, script/farmer-v1, system/kernel.
    """


class AvatarReleasedV1(BaseModel):
    """
    Posse devolvida ao controlador padrão do cartucho.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    previous_controller: ControllerRef
    controller: ControllerRef
    by: Annotated[str, Field(max_length=128, min_length=1, title="Actor")]
    """
    Quem causou: human/operator, script/farmer-v1, system/kernel.
    """


class AvatarSleepEndedV1(BaseModel):
    """
    O avatar acordou (ADR-0014). Substituído pelo v2, sem produtor desde o M2 (ADR-0042).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    cause: Literal["bed", "faint"]
    energy: Annotated[float, Field(ge=0.0, le=100.0)]


class AvatarSleepEndedV2(BaseModel):
    """
    O avatar acordou (ADR-0014, ADR-0041, ADR-0042).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    cause: Literal["voluntary", "faint"]
    """
    voluntary: o controlador mandou dormir; faint: desmaio.
    """
    bed_id: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    Cama ou entidade análoga usada no sono. Ausente quando o avatar dormiu onde estava.
    """
    energy: Annotated[float, Field(ge=0.0, le=100.0)]


class AvatarSleepStartedV1(BaseModel):
    """
    O avatar dormiu na cama ou desmaiou (ADR-0014). Substituído pelo v2, sem produtor desde o M2 (ADR-0042).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    cause: Literal["bed", "faint"]
    position: Position
    wake_at_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """


class AvatarSleepStartedV2(BaseModel):
    """
    O avatar dormiu por escolha, na cama ou onde estava, ou desmaiou (ADR-0014, ADR-0041, ADR-0042).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    cause: Literal["voluntary", "faint"]
    """
    voluntary: o controlador mandou dormir; faint: desmaio.
    """
    bed_id: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    Cama ou entidade análoga usada no sono. Ausente quando o avatar dorme onde está.
    """
    position: Position
    wake_at_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """


class PaidItem(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    item: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(_[a-z0-9]+)*$", title="ItemId")]
    """
    Id de item ou cultura; conteúdo do cartucho, em português, sem acento: moeda, semente_rabanete.
    """
    qty: Annotated[int, Field(ge=1)]
    unit_price: Annotated[int, Field(ge=0)]


class FarmBuyerPaidV1(BaseModel):
    """
    Pagamento das vendas às 06:00, com o preço de cada item.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    container_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    items: Annotated[list[PaidItem], Field(min_length=1)]
    total: Annotated[int, Field(ge=0)]
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """


class FarmCropEatenV1(BaseModel):
    """
    Uma planta madura amanheceu comida por um bicho, e o canteiro ficou vazio (ADR-0067). O efeito é visível; por que este canteiro e não outro, não.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    plot_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    crop: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(_[a-z0-9]+)*$", title="ItemId")]
    """
    Id de item ou cultura; conteúdo do cartucho, em português, sem acento: moeda, semente_rabanete.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    by: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Quem comeu, como se vê no canteiro: corvo…
    """


class FarmCropMaturedV1(BaseModel):
    """
    Planta madura; days é a evidência observável da regra oculta (bíblia §13).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    plot_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    crop: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(_[a-z0-9]+)*$", title="ItemId")]
    """
    Id de item ou cultura; conteúdo do cartucho, em português, sem acento: moeda, semente_rabanete.
    """
    planted_day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    days: Annotated[int, Field(ge=1)]
    """
    Dias entre o plantio e a maturidade.
    """


class FarmCropWitheredV1(BaseModel):
    """
    Planta murchou por falta de água.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    plot_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    crop: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(_[a-z0-9]+)*$", title="ItemId")]
    """
    Id de item ou cultura; conteúdo do cartucho, em português, sem acento: moeda, semente_rabanete.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    dry_days: Annotated[int, Field(ge=1)]
    """
    Viradas seguidas sem rega.
    """


class LlmCallCompletedV1(BaseModel):
    """
    Uma chamada de modelo terminou (ADR-0058): quem chamou, qual modelo, tokens, custo e latência. Nunca leva o prompt nem a resposta. Publicado pelo decorador da porta, não pelo adaptador.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    controller: ControllerRef
    """
    Quem fez a chamada.
    """
    purpose: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Para que a chamada serviu: decision, reflection, probe…
    """
    avatar_id: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    O avatar em nome de quem se decidiu, quando houver.
    """
    provider: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    O provedor do adaptador: anthropic, openrouter…
    """
    model: Annotated[str, Field(max_length=128, pattern="^[a-z0-9][a-z0-9._:/-]*$")]
    prompt_sha256: Annotated[str, Field(pattern="^[0-9a-f]{64}$")]
    """
    Hash do pedido canônico: identifica a chamada e a linha da fita, sem levar o prompt.
    """
    latency_ms: Annotated[int, Field(ge=0)]
    request_id: Annotated[str | None, Field(max_length=128)] = None
    """
    O id do pedido no provedor, para suporte.
    """
    usage: LlmUsage
    cost_usd: Annotated[float, Field(ge=0.0)]
    """
    Custo nominal pela tabela de preços do ambiente.
    """
    charged: bool
    """
    Falso quando a resposta veio da fita: ninguém pagou, e a guarda não conta.
    """
    stop_reason: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Como o modelo parou: end_turn, tool_use, max_tokens, refusal…
    """
    effort: Literal["low", "medium", "high", "xhigh", "max"] | None = None


class LlmCallFailedV1(BaseModel):
    """
    Uma chamada de modelo falhou (ADR-0058): o erro classificado, se vale repetir, e a latência até a falha.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    controller: ControllerRef
    """
    Quem fez a chamada.
    """
    purpose: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Para que a chamada serviu: decision, reflection, probe…
    """
    avatar_id: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    O avatar em nome de quem se decidiu, quando houver.
    """
    provider: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    O provedor do adaptador: anthropic, openrouter…
    """
    model: Annotated[str, Field(max_length=128, pattern="^[a-z0-9][a-z0-9._:/-]*$")]
    prompt_sha256: Annotated[str, Field(pattern="^[0-9a-f]{64}$")]
    """
    Hash do pedido canônico: identifica a chamada e a linha da fita, sem levar o prompt.
    """
    latency_ms: Annotated[int, Field(ge=0)]
    error: Literal[
        "rate_limit",
        "timeout",
        "connection",
        "auth",
        "bad_request",
        "server",
        "cassette_miss",
    ]
    message: Annotated[str, Field(max_length=1000)]
    retryable: bool


class MemoryBeliefFormedV1(BaseModel):
    """
    Uma crença nova (ADR-0060; contratos §8.4): o que o agente passou a acreditar, com quanta confiança, por que evidências e de que origem.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    O avatar cuja memória é esta.
    """
    belief_id: Annotated[
        str,
        Field(max_length=64, pattern="^bel-[0-9a-z]+(-[0-9a-z]+)*$", title="BeliefId"),
    ]
    """
    Id de uma crença do agente (ADR-0060): bel-0001.
    """
    statement: Annotated[str, Field(max_length=500, min_length=1)]
    """
    A crença, em uma frase.
    """
    confidence: Annotated[float, Field(ge=0.0, le=1.0, title="Confidence")]
    """
    Quanto o agente acredita, de 0 a 1 (ADR-0060).
    """
    evidence: Annotated[list[BeliefEvidenceItem], Field(max_length=20, title="BeliefEvidence")]
    """
    Evidências de uma crença: ticks e fatos de uma linha, do que o agente percebeu; nunca o `internal`.
    """
    source: BeliefSource
    reason: Annotated[str | None, Field(max_length=500, min_length=1)] = None
    """
    Por que a reflexão fez isso.
    """


class MemoryBeliefRetractedV1(BaseModel):
    """
    O agente abandonou uma crença (ADR-0060; contratos §8.4).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    O avatar cuja memória é esta.
    """
    belief_id: Annotated[
        str,
        Field(max_length=64, pattern="^bel-[0-9a-z]+(-[0-9a-z]+)*$", title="BeliefId"),
    ]
    """
    Id de uma crença do agente (ADR-0060): bel-0001.
    """
    statement: Annotated[str, Field(max_length=500, min_length=1)]
    """
    A crença, em uma frase.
    """
    reason: Annotated[str | None, Field(max_length=500, min_length=1)] = None
    """
    Por que a reflexão fez isso.
    """


class Confidence1(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    before: Annotated[float, Field(ge=0.0, le=1.0, title="Confidence")]
    """
    Quanto o agente acredita, de 0 a 1 (ADR-0060).
    """
    after: Annotated[float, Field(ge=0.0, le=1.0, title="Confidence")]
    """
    Quanto o agente acredita, de 0 a 1 (ADR-0060).
    """


class MemoryBeliefUpdatedV1(BaseModel):
    """
    A confiança de uma crença mudou, ou o enunciado foi refinado (ADR-0060; contratos §8.4), com a evidência que pesou.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    O avatar cuja memória é esta.
    """
    belief_id: Annotated[
        str,
        Field(max_length=64, pattern="^bel-[0-9a-z]+(-[0-9a-z]+)*$", title="BeliefId"),
    ]
    """
    Id de uma crença do agente (ADR-0060): bel-0001.
    """
    statement: Annotated[str, Field(max_length=500, min_length=1)]
    """
    A crença, em uma frase.
    """
    confidence: Confidence1
    evidence: Annotated[list[BeliefEvidenceItem], Field(max_length=20, title="BeliefEvidence")]
    """
    Evidências de uma crença: ticks e fatos de uma linha, do que o agente percebeu; nunca o `internal`.
    """
    source: BeliefSource
    reason: Annotated[str | None, Field(max_length=500, min_length=1)] = None
    """
    Por que a reflexão fez isso.
    """


class MemoryNotedV1(BaseModel):
    """
    O agente anotou algo no caderno (ADR-0060): o parâmetro `note` de uma ferramenta, com o tick do envelope. Publicado pela mente; é o que o operador vê no caderno.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    O avatar cuja memória é esta.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    text: Annotated[str, Field(max_length=500, min_length=1)]


class Beliefs(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    formed: Annotated[int, Field(ge=0)]
    updated: Annotated[int, Field(ge=0)]
    retracted: Annotated[int, Field(ge=0)]
    total: Annotated[int, Field(ge=0)]


class MemoryReflectedV1(BaseModel):
    """
    A reflexão de um dia terminou (ADR-0060): o resumo, o plano para amanhã e quantas crenças foram formadas, atualizadas e retiradas. Nunca leva o prompt: só o hash do pedido.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    O avatar cuja memória é esta.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    O dia refletido.
    """
    summary: Annotated[str, Field(max_length=2000, min_length=1)]
    plan: Annotated[str | None, Field(max_length=1000, min_length=1)] = None
    """
    O que o agente pretende amanhã.
    """
    beliefs: Beliefs
    prompt_sha256: Annotated[str | None, Field(pattern="^[0-9a-f]{64}$")] = None
    """
    Hash do pedido da reflexão, o mesmo do llm.call.completed.
    """


class OpsBudgetExceededV1(BaseModel):
    """
    O gasto com modelos estourou um teto e a guarda pediu a pausa do mundo (ADR-0058). Só o operador retoma.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    scope: Literal["day", "total"]
    """
    O teto do dia simulado ou o do mundo inteiro.
    """
    day: Annotated[int | None, Field(ge=1, title="Day")] = None
    """
    O dia simulado, quando o escopo é day.
    """
    spent_usd: Annotated[float, Field(ge=0.0)]
    limit_usd: Annotated[float, Field(gt=0.0)]
    paused: bool
    """
    Verdadeiro quando a guarda publicou cmd.clock.pause com reason budget.
    """


class OpsBudgetThresholdReachedV1(BaseModel):
    """
    O gasto com modelos passou de 50, 80 ou 100% de um teto (ADR-0058). Publicado pela guarda de orçamento.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    scope: Literal["day", "total"]
    """
    O teto do dia simulado ou o do mundo inteiro.
    """
    day: Annotated[int | None, Field(ge=1, title="Day")] = None
    """
    O dia simulado, quando o escopo é day.
    """
    spent_usd: Annotated[float, Field(ge=0.0)]
    limit_usd: Annotated[float, Field(gt=0.0)]
    threshold_pct: Literal[50, 80, 100]


class PerceptionDecision(BaseModel):
    """
    O pedido de decisão que esta foto responde: o motivo e quem deve responder. Basta este evento para o controlador agir (ADR-0048).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    reason: Literal[
        "session_started",
        "possessed",
        "action_completed",
        "action_rejected",
        "action_interrupted",
        "phase_changed",
        "need_threshold",
        "woke_up",
    ]
    controller: ControllerRef


class ViewClock(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    sim_time: AwareDatetime
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    phase: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    date: date_aliased | None = None
    """
    A data do calendário do ano acelerado (ADR-0067), à parte do simtime; ausente sem ano declarado.
    """
    season: Annotated[
        str | None, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")
    ] = None
    """
    A estação da data (primavera, verao…), declarada pelo cartucho; ausente sem ano declarado.
    """


class ViewWeather(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    condition: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """


class ViewAction(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    action_id: Annotated[str, Field(pattern="^act-[0-9]{6,}$", title="ActionId")]
    """
    Id de ação: contador determinístico do kernel.
    """
    action: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    params: dict[str, Any]
    end_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    applied_tick: Annotated[int | None, Field(ge=0, title="Tick")] = None
    """
    Tick em que a ação começou (ADR-0052).
    """
    interrupt: Annotated[Literal["never", "cancel", "partial"] | None, Field(title="Interrupt")] = (
        None
    )
    """
    O que um comando novo do mesmo controlador faz com esta ação em andamento (ADR-0052).
    """


class ViewSelf(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    position: Position
    needs: dict[str, NeedsAdditionalProperty]
    asleep: bool
    action: Annotated[ViewAction | None, Field(title="ViewAction")] = None


class ViewContainer(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    container_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    items: list[ItemStack]


class ViewEntity(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    kind: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    position: Position | None = None
    container_id: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    attributes: dict[str, str | float | bool | None]


class PerceptionView(BaseModel):
    """
    Visão genérica: o que é da fazenda chega como atributo de entidade (ADR-0025).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    clock: Annotated[ViewClock, Field(title="ViewClock")]
    weather: Annotated[ViewWeather, Field(title="ViewWeather")]
    self: Annotated[ViewSelf, Field(title="ViewSelf")]
    containers: list[ViewContainer]
    entities: list[ViewEntity]
    map: TerrainWindow | None = None
    """
    O terreno ao alcance do avatar, recortado ao raio (ADR-0056). Só na foto; o delta nunca o repete.
    """


class PerceptionDeliveredV1(BaseModel):
    """
    Instantâneo do que o avatar percebe, a cada pedido de decisão (ADR-0028).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    kind: Literal["snapshot"]
    as_of_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    decision: Annotated[PerceptionDecision | None, Field(title="PerceptionDecision")] = None
    """
    O pedido de decisão que esta foto responde: o motivo e quem deve responder. Basta este evento para o controlador agir (ADR-0048).
    """
    view: Annotated[PerceptionView, Field(title="PerceptionView")]
    """
    Visão genérica: o que é da fazenda chega como atributo de entidade (ADR-0025).
    """


class PerceptionUpdatedV1(BaseModel):
    """
    O delta da percepção (ADR-0028, ADR-0056): o que mudou desde a última entrega ao avatar e o que aconteceu no meio-tempo. Responde a um pedido de decisão como a foto, para os controladores que pedem deltas; a foto continua em perception.delivered.v1.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    since_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    O tick da entrega anterior (foto ou delta): este delta cobre o que mudou depois dele.
    """
    as_of_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    decision: DecisionRequest
    clock: SeenClock
    """
    Sempre presente: o relógio agora.
    """
    weather: SeenWeather | None = None
    """
    Só quando o clima mudou desde a entrega anterior.
    """
    self: SeenSelf
    """
    O próprio avatar, inteiro, sempre: é pequeno e é o que mais muda.
    """
    containers: list[SeenContainer] | None = None
    """
    Os contêineres cujo conteúdo mudou, inteiros.
    """
    entities: list[SeenEntity] | None = None
    """
    As entidades que apareceram ou mudaram (posição, contêiner ou atributos), com o registro inteiro.
    """
    gone: list[EntityId] | None = None
    """
    As entidades que deixaram de ser percebidas desde a entrega anterior.
    """
    events: Annotated[list[SeenEvent], Field(max_length=1000)]
    """
    O que aconteceu desde a entrega anterior, na ordem em que foi publicado: alimenta a memória e a narrativa (M11).
    """


class RulesEffectAppliedV1(BaseModel):
    """
    Efeito numérico de uma regra sobre uma entidade.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    rule: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    version: Annotated[
        str,
        Field(
            pattern="^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$",
            title="Semver",
        ),
    ]
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    property: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    base: float
    applied: float


class LoadedRule(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    rule: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    version: Annotated[
        str,
        Field(
            pattern="^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$",
            title="Semver",
        ),
    ]
    hidden: bool
    enabled: bool
    params: dict[str, str | float | bool | None]
    """
    Parâmetros da regra.
    """


class RulesLoadedV1(BaseModel):
    """
    Conjunto de regras carregado, com versões e estado inicial.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    rules: list[LoadedRule]
    source_ref: Annotated[str, Field(max_length=256, min_length=1)]


class RulesToggledV1(BaseModel):
    """
    Regra ligada, desligada ou parametrizada a quente (ADR-0015).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    rule: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    from_version: Annotated[
        str,
        Field(
            pattern="^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$",
            title="Semver",
        ),
    ]
    to_version: Annotated[
        str,
        Field(
            pattern="^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$",
            title="Semver",
        ),
    ]
    enabled: bool
    params: dict[str, str | float | bool | None] | None = None
    """
    Parâmetros da regra.
    """
    by: Annotated[str, Field(max_length=128, min_length=1, title="Actor")]
    """
    Quem causou: human/operator, script/farmer-v1, system/kernel.
    """
    reason: Annotated[str, Field(max_length=500, min_length=1)]
    experiment_id: Annotated[str | None, Field(max_length=64, min_length=1)] = None
    effective_at_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """


class WorldClockJumpedV1(BaseModel):
    """
    Salto de tempo até o próximo evento agendado (simulação de eventos discretos).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    from_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    to_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """


class WorldClockModeChangedV1(BaseModel):
    """
    Mudança de modo do relógio (ADR-0026).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    previous_mode: Annotated[Literal["continuous", "max"], Field(title="ClockMode")]
    """
    Modos do relógio na v0.1; a pausa é um estado à parte (ADR-0026).
    """
    mode: Annotated[Literal["continuous", "max"], Field(title="ClockMode")]
    """
    Modos do relógio na v0.1; a pausa é um estado à parte (ADR-0026).
    """
    reason: Annotated[str, Field(max_length=200, min_length=1)]
    by: Annotated[str, Field(max_length=128, min_length=1, title="Actor")]
    """
    Quem causou: human/operator, script/farmer-v1, system/kernel.
    """


class WorldClockPausedV1(BaseModel):
    """
    Relógio pausado; a pausa é um estado, não um modo (ADR-0026).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    reason: Literal["debug", "maintenance", "budget"]
    by: Annotated[str, Field(max_length=128, min_length=1, title="Actor")]
    """
    Quem causou: human/operator, script/farmer-v1, system/kernel.
    """


class WorldClockPhaseChangedV1(BaseModel):
    """
    Mudança de fase do dia; os nomes das fases vêm do cartucho.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    phase: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Ex.: amanhecer, meio_dia, entardecer, noite, madrugada.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    date: date_aliased | None = None
    """
    A data do calendário do ano acelerado (ADR-0067), à parte do simtime; ausente sem ano declarado.
    """
    season: Annotated[
        str | None, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")
    ] = None
    """
    A estação da data (primavera, verao…), declarada pelo cartucho; ausente sem ano declarado.
    """


class WorldClockResumedV1(BaseModel):
    """
    Relógio retomado no modo em que estava (ADR-0026).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    by: Annotated[str, Field(max_length=128, min_length=1, title="Actor")]
    """
    Quem causou: human/operator, script/farmer-v1, system/kernel.
    """


class WorldClockScaleChangedV1(BaseModel):
    """
    Mudança de escala do relógio.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    previous_scale: Annotated[float, Field(gt=0.0)]
    scale: Annotated[float, Field(gt=0.0)]
    reason: Literal["operator", "experiment", "budget", "human"]
    by: Annotated[str, Field(max_length=128, min_length=1, title="Actor")]
    """
    Quem causou: human/operator, script/farmer-v1, system/kernel.
    """


class WorldClockSeasonChangedV1(BaseModel):
    """
    A estação mudou na virada do dia, num mundo com ano declarado pelo cartucho (ADR-0067). A data é a do calendário do ano acelerado, à parte do simtime.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    date: date_aliased
    """
    A data do calendário no dia da troca.
    """
    season: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    A estação que começa: primavera, verao, outono, inverno…
    """
    previous_season: Annotated[
        str | None, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")
    ] = None
    """
    A estação que termina.
    """


class WorldClockSteppedV1(BaseModel):
    """
    Avanço passo a passo com o relógio pausado.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    ticks: Annotated[int, Field(ge=1, le=1440)]
    from_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    to_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """


class WorldCommandRejectedV1(BaseModel):
    """
    Comando que não é ação (posse, relógio, regras) foi recusado.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    command_id: Annotated[
        str,
        Field(
            pattern="^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            title="Uuid7",
        ),
    ]
    """
    UUID versão 7 (RFC 9562), ordenável por tempo.
    """
    command_type: Annotated[
        str, Field(pattern="^campsverso\\.cmd\\.[a-z0-9_]+(\\.[a-z0-9_]+)+\\.v[0-9]+$")
    ]
    reason: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    detail: Annotated[str | None, Field(max_length=500, min_length=1)] = None


class WorldEntityDespawnedV1(BaseModel):
    """
    Entidade removida do mundo em tempo de execução (o canteiro vazio que volta a ser grama; ADR-0067). Avatares, contêineres com itens e alvos de ações em andamento não se removem.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    kind: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    O tipo da entidade removida.
    """
    position: Position | None = None
    """
    Onde ela estava no mapa; ausente se estava dentro de um contêiner.
    """
    reason: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    O motivo, dado pelo cartucho: reverted_to_grass…
    """
    action_id: Annotated[str | None, Field(pattern="^act-[0-9]{6,}$", title="ActionId")] = None
    """
    A ação que removeu a entidade, se foi uma ação; ausente quando foi um sistema.
    """


class WorldEntityMoveInterruptedV1(BaseModel):
    """
    Movimento interrompido; traz a posição real no momento (D1).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    action_id: Annotated[str, Field(pattern="^act-[0-9]{6,}$", title="ActionId")]
    """
    Id de ação: contador determinístico do kernel.
    """
    position: Position
    reason: Literal["cancelled", "blocked", "fainted"]


class WorldEntityMovedV1(BaseModel):
    """
    Movimento como trajeto: só esquinas e destino; a UI interpola (D1).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    action_id: Annotated[str, Field(pattern="^act-[0-9]{6,}$", title="ActionId")]
    """
    Id de ação: contador determinístico do kernel.
    """
    origin: Position
    waypoints: Annotated[list[Position], Field(min_length=1)]
    """
    Pontos de inflexão do trajeto e o destino.
    """
    depart_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    arrival_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    tiles_per_tick: Annotated[float, Field(gt=0.0)]


class WorldEntitySpawnedV1(BaseModel):
    """
    Entidade criada: no mapa (position) ou dentro de um contêiner (container_id).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    kind: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Tipo definido pelo cartucho: avatar, plot, bed, chest, well, kiosk, watering_can…
    """
    position: Position | None = None
    container_id: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    blocking: bool
    """
    Se a entidade bloqueia a passagem no mapa.
    """
    display_name: Annotated[str | None, Field(max_length=64, min_length=1)] = None
    attributes: dict[str, str | float | bool | None] | None = None
    """
    Estado visível inicial.
    """
    action_id: Annotated[str | None, Field(pattern="^act-[0-9]{6,}$", title="ActionId")] = None
    """
    A ação que criou a entidade em tempo de execução (um canteiro cavado; ADR-0062); ausente no início da sessão.
    """


class WorldEntityStateChangedV1(BaseModel):
    """
    Mudança de atributos visíveis de uma entidade (ADR-0025).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    changes: dict[str, str | float | bool | None]
    cause: Annotated[
        str | None, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")
    ] = None
    """
    Ação ou nome do sistema que causou a mudança.
    """
    action_id: Annotated[str | None, Field(pattern="^act-[0-9]{6,}$", title="ActionId")] = None
    """
    Id de ação: contador determinístico do kernel.
    """


class WorldEntityStoredV1(BaseModel):
    """
    Entidade guardada noutro contêiner (uma ferramenta que vai do avatar para o baú, ou volta), sem posição no mapa (ADR-0062).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    entity_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    from_container: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    De onde saiu; ausente quando estava no mapa.
    """
    to_container: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    action_id: Annotated[str | None, Field(pattern="^act-[0-9]{6,}$", title="ActionId")] = None
    """
    Id de ação: contador determinístico do kernel.
    """


class WorldItemConsumedV1(BaseModel):
    """
    Item saiu do mundo.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    item: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(_[a-z0-9]+)*$", title="ItemId")]
    """
    Id de item ou cultura; conteúdo do cartucho, em português, sem acento: moeda, semente_rabanete.
    """
    qty: Annotated[int, Field(ge=1)]
    container_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    reason: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Ex.: eat, plant, buy_payment, buyer_collect.
    """
    action_id: Annotated[str | None, Field(pattern="^act-[0-9]{6,}$", title="ActionId")] = None
    """
    Id de ação: contador determinístico do kernel.
    """
    expires_day: Annotated[int | None, Field(ge=1, title="Day")] = None
    """
    O dia em que o lote consumido vencia; o motivo `spoiled` é o estrago na virada do dia (ADR-0062).
    """


class WorldItemCreatedV1(BaseModel):
    """
    Item surgiu num contêiner.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    item: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(_[a-z0-9]+)*$", title="ItemId")]
    """
    Id de item ou cultura; conteúdo do cartucho, em português, sem acento: moeda, semente_rabanete.
    """
    qty: Annotated[int, Field(ge=1)]
    container_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    reason: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Ex.: initial, harvest, buy, payment.
    """
    action_id: Annotated[str | None, Field(pattern="^act-[0-9]{6,}$", title="ActionId")] = None
    """
    Id de ação: contador determinístico do kernel.
    """
    expires_day: Annotated[int | None, Field(ge=1, title="Day")] = None
    """
    O dia em que o lote criado vence pela validade nominal do item, quando o item tem validade (ADR-0062).
    """


class WorldItemTransferredV1(BaseModel):
    """
    Item passou de um contêiner para outro.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    item: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(_[a-z0-9]+)*$", title="ItemId")]
    """
    Id de item ou cultura; conteúdo do cartucho, em português, sem acento: moeda, semente_rabanete.
    """
    qty: Annotated[int, Field(ge=1)]
    from_container: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    to_container: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Id legível e estável de uma entidade: camps, plot-e-03, bed.
    """
    reason: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Ex.: deposit, withdraw, sell.
    """
    action_id: Annotated[str | None, Field(pattern="^act-[0-9]{6,}$", title="ActionId")] = None
    """
    Id de ação: contador determinístico do kernel.
    """
    expires_day: Annotated[int | None, Field(ge=1, title="Day")] = None
    """
    O dia em que o lote movido vence pela validade nominal; com validade, o kernel publica um evento por lote (ADR-0062).
    """


class WorldNeedChangedV1(BaseModel):
    """
    Valor de uma necessidade; no máximo um por hora simulada por necessidade.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    need: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Ex.: fome, energia.
    """
    previous_value: Annotated[float, Field(ge=0.0, le=100.0)]
    value: Annotated[float, Field(ge=0.0, le=100.0)]


class WorldNeedThresholdCrossedV1(BaseModel):
    """
    Uma necessidade cruzou um limiar definido pelo cartucho.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    Avatar (o corpo), independente de quem o controla (ADR-0027).
    """
    need: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    threshold: Annotated[float, Field(ge=0.0, le=100.0)]
    direction: Literal["up", "down"]
    value: Annotated[float, Field(ge=0.0, le=100.0)]


class SessionMap(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    id: Annotated[str, Field(max_length=64, min_length=1, pattern="^[a-z0-9_-]+$")]
    width: Annotated[int, Field(ge=1)]
    height: Annotated[int, Field(ge=1)]
    rows: Annotated[
        list[TerrainRow] | None,
        Field(max_length=1024, min_length=1, title="TerrainRows"),
    ] = None
    """
    O terreno do mapa inteiro, publicado uma vez (ADR-0056): quem decide passa a enxergar onde pode pisar.
    """
    legend: TerrainLegend | None = None


class WorldSessionStartedV1(BaseModel):
    """
    Mundo carregado ou retomado a partir de snapshot.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    cartridge_version: Annotated[
        str,
        Field(
            pattern="^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$",
            title="Semver",
        ),
    ]
    seed: Annotated[int, Field(ge=0)]
    """
    Seed registrada; os fluxos de RNG nomeados derivam dela.
    """
    tick_seconds: Annotated[int, Field(ge=1)]
    """
    Duração de um tick em segundos simulados.
    """
    mode: Annotated[Literal["continuous", "max"], Field(title="ClockMode")]
    """
    Modos do relógio na v0.1; a pausa é um estado à parte (ADR-0026).
    """
    paused: bool
    scale: Annotated[float, Field(gt=0.0)]
    """
    Segundos simulados por segundo real.
    """
    resumed: bool
    """
    Verdadeiro quando o mundo foi retomado a partir de snapshot.
    """
    map: Annotated[SessionMap, Field(title="SessionMap")]
    affordances: list[Affordance] | None = None
    """
    Catálogo de ações que o cartucho oferece a quem joga (ADR-0051). O menu só sugere; quem decide é o kernel.
    """
    metrics: Annotated[list[Metric] | None, Field(max_length=64)] = None
    """
    Catálogo de métricas do dia que o cartucho declara (ADR-0054).
    """
    perception: PerceptionConfig | None = None
    """
    O raio de percepção declarado pelo cartucho; vale para todos os atores (ADR-0056).
    """


class WorldSnapshotCreatedV1(BaseModel):
    """
    Snapshot persistido no BlobStore.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    snapshot_id: Annotated[str, Field(max_length=64, min_length=1)]
    ref: Annotated[str, Field(max_length=256, min_length=1)]
    last_seq: Annotated[int, Field(ge=0)]
    sha256: Annotated[str, Field(pattern="^[0-9a-f]{64}$")]
    size_bytes: Annotated[int, Field(ge=0)]


class WorldWeatherChangedV1(BaseModel):
    """
    Clima sorteado para um dia agrícola (ADR-0018).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    condition: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Ex.: sun, rain.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """


class LiveKernelV1(BaseModel):
    """
    Pulso do kernel: o tick de verdade e o relógio, a cada kernel.pulse_seconds de tempo real. Vai para campsverso.<mundo>.live.kernel, que nenhum stream guarda: não entra no histórico, no arquivo JSONL nem no replay (ADR-0051).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    type: Literal["campsverso.live.kernel.v1"]
    worldid: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$")]
    tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    O tick em que o kernel está agora, mesmo sem evento.
    """
    sim_time: AwareDatetime
    mode: Annotated[Literal["continuous", "max"], Field(title="ClockMode")]
    """
    Modos do relógio na v0.1; a pausa é um estado à parte (ADR-0026).
    """
    scale: Annotated[float, Field(gt=0.0)]
    paused: bool
    pulse_seconds: Annotated[float, Field(gt=0.0)]
    """
    O intervalo entre pulsos; quem escuta usa para saber quando o kernel ficou sem sinal.
    """
    sent_at: AwareDatetime
    """
    Relógio de parede de quem mandou.
    """


class RealtimeCommandV1(BaseModel):
    """
    Pedido da UI para o gateway publicar um comando. O gateway monta o envelope e o valida contra o contrato do comando (ADR-0050).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    type: Literal["campsverso.realtime.command.v1"]
    request_id: Annotated[str, Field(max_length=64, min_length=1)]
    """
    Escolhido pela UI; volta no reply.
    """
    command: Annotated[
        str, Field(pattern="^campsverso\\.cmd\\.[a-z0-9_]+(\\.[a-z0-9_]+)+\\.v[0-9]+$")
    ]
    data: dict[str, Any]
    """
    O payload do comando, como no contrato dele.
    """


class RealtimeError(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    code: Literal["not_allowed", "invalid_command", "unavailable", "invalid_message"]
    message: Annotated[str, Field(max_length=500, min_length=1)]


class RealtimeReplyV1(BaseModel):
    """
    Resposta do gateway a um command: publicado ou recusado. Quem aceita ou recusa o comando no mundo é o kernel, com um evento (ADR-0050).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    type: Literal["campsverso.realtime.reply.v1"]
    request_id: Annotated[str, Field(max_length=64, min_length=1)]
    ok: bool
    command_id: Annotated[
        str | None,
        Field(
            pattern="^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            title="Uuid7",
        ),
    ] = None
    """
    Id do envelope publicado, quando ok.
    """
    error: Annotated[RealtimeError | None, Field(title="RealtimeError")] = None


class RealtimeUpdateV1(BaseModel):
    """
    O que mudou desde a última mensagem: um merge patch do estado (RFC 7386) e os eventos do intervalo, filtrados pela visão (ADR-0050).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    type: Literal["campsverso.realtime.update.v1"]
    patch: dict[str, Any]
    """
    Merge patch (RFC 7386) sobre o ObserverState; null apaga a chave.
    """
    events: Annotated[list[EnvelopeV1], Field(max_length=5000)]


class Command(RootModel[str]):
    root: Annotated[str, Field(pattern="^campsverso\\.cmd\\.[a-z0-9_]+(\\.[a-z0-9_]+)+\\.v[0-9]+$")]


class ObserverMap(BaseModel):
    """
    O mapa do cartucho; o arquivo fica no gateway em /content/maps/<id>.tmj (ADR-0050).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    id: Annotated[str, Field(max_length=64, min_length=1, pattern="^[a-z0-9_-]+$")]
    width: Annotated[int, Field(ge=1)]
    height: Annotated[int, Field(ge=1)]
    rows: Annotated[
        list[TerrainRow] | None,
        Field(max_length=1024, min_length=1, title="TerrainRows"),
    ] = None
    """
    O terreno, como o kernel publicou no session.started (ADR-0056).
    """
    legend: TerrainLegend | None = None


class ObserverSession(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    cartridge_version: Annotated[
        str,
        Field(
            pattern="^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)$",
            title="Semver",
        ),
    ]
    tick_seconds: Annotated[int, Field(ge=1)]
    map: Annotated[ObserverMap | None, Field(title="ObserverMap")] = None
    """
    O mapa do cartucho; o arquivo fica no gateway em /content/maps/<id>.tmj (ADR-0050).
    """
    affordances: list[Affordance] | None = None
    """
    O catálogo de ações do session.started, para montar os menus (ADR-0051).
    """
    metrics: list[Metric] | None = None
    """
    O catálogo de métricas do session.started (ADR-0054).
    """
    perception: PerceptionConfig | None = None


class ObserverClock(BaseModel):
    """
    Vazio até o session.started; a pausa é estado, não modo (ADR-0026).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    mode: Annotated[Literal["continuous", "max"] | None, Field(title="ClockMode")] = None
    """
    Modos do relógio na v0.1; a pausa é um estado à parte (ADR-0026).
    """
    scale: Annotated[float | None, Field(gt=0.0)] = None
    paused: bool | None = None


class ObserverPulse(BaseModel):
    """
    O último pulso do kernel (ADR-0051): o tick de verdade, mesmo sem evento. `alive` vira falso depois de 3 pulsos perdidos. Ausente até o primeiro pulso.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    sim_time: AwareDatetime | None = None
    alive: bool


class ObserverEntity(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    kind: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Tipo definido pelo cartucho; cada renderer escolhe como desenhar.
    """
    position: Position | None = None
    """
    Onde está, ou onde vai estar ao fim do trajeto em `motion`.
    """
    container_id: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    Dentro de outra entidade (inventário), sem posição.
    """
    display_name: Annotated[str | None, Field(max_length=64, min_length=1)] = None
    attributes: dict[str, str | float | bool | None]


ContainersAdditionalProperty = TypeAliasType(
    "ContainersAdditionalProperty", Annotated[int, Field(ge=1)]
)


class ObserverMotion(BaseModel):
    """
    Trajeto em andamento: tile a tile, a partir de depart_tick, a tiles_per_tick.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    path: Annotated[list[Position], Field(min_length=1)]
    depart_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    tiles_per_tick: Annotated[float, Field(gt=0.0)]


class ObserverAction(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    action_id: Annotated[str, Field(pattern="^act-[0-9]{6,}$", title="ActionId")]
    """
    Id de ação: contador determinístico do kernel.
    """
    action: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    params: dict[str, Any]
    end_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    applied_tick: Annotated[int | None, Field(ge=0, title="Tick")] = None
    """
    Tick em que a ação começou (ADR-0052).
    """
    interrupt: Annotated[Literal["never", "cancel", "partial"] | None, Field(title="Interrupt")] = (
        None
    )
    """
    O que um comando novo do mesmo controlador faz com esta ação em andamento (ADR-0052).
    """
    intent: Annotated[str | None, Field(max_length=500, min_length=1)] = None
    """
    A intenção declarada na proposta aceita, quando o controlador a deu (ADR-0059).
    """


class ObserverSleep(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    since_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    wake_at_tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    bed_id: Annotated[
        str | None,
        Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId"),
    ] = None
    """
    A cama em que dorme; ausente quando dorme onde está.
    """


class ObserverBelief(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    belief_id: Annotated[
        str,
        Field(max_length=64, pattern="^bel-[0-9a-z]+(-[0-9a-z]+)*$", title="BeliefId"),
    ]
    """
    Id de uma crença do agente (ADR-0060): bel-0001.
    """
    statement: Annotated[str, Field(max_length=500)]
    confidence: Annotated[float, Field(ge=0.0, le=1.0, title="Confidence")]
    """
    Quanto o agente acredita, de 0 a 1 (ADR-0060).
    """


class ObserverNote(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    text: Annotated[str, Field(max_length=500)]


class ObserverMemory(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )
    day: Annotated[int | None, Field(ge=1, title="Day")] = None
    """
    O dia da última reflexão.
    """
    summary: Annotated[str | None, Field(max_length=2000)] = None
    plan: Annotated[str | None, Field(max_length=1000)] = None
    beliefs: Annotated[list[ObserverBelief], Field(max_length=50)]
    notes: Annotated[list[ObserverNote], Field(max_length=50)]


class ObserverDecision(BaseModel):
    """
    Último pedido de decisão do avatar.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    reason: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
    """
    tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """


class ObserverState(BaseModel):
    """
    O mundo como se vê de fora, montado só com eventos publicados (ADR-0050). Genérico e sem nada de desenho: posições em tiles, trajetos em ticks, o que é do cartucho chega como atributo. Não carrega null: atributo nulo é atributo ausente, porque no merge patch null apaga.
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    cartridge: Annotated[
        str | None, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")
    ] = None
    """
    Cartucho do mundo, como no envelope.
    """
    tick: Annotated[int, Field(ge=0, title="Tick")]
    """
    Tick do kernel (1 minuto simulado na fazenda).
    """
    sim_time: AwareDatetime | None = None
    """
    Hora simulada do tick mais recente.
    """
    day: Annotated[int, Field(ge=1, title="Day")]
    """
    Dia simulado (dia agrícola, ADR-0018), começando em 1.
    """
    phase: Annotated[str, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")]
    """
    Fase do dia; `desconhecida` antes do primeiro evento de fase.
    """
    date: date_aliased | None = None
    """
    A data do calendário do ano acelerado (ADR-0067), da última mudança de fase; ausente sem ano declarado.
    """
    season: Annotated[
        str | None, Field(max_length=64, pattern="^[a-z][a-z0-9_]*$", title="Token")
    ] = None
    """
    A estação da data; ausente sem ano declarado.
    """
    session: Annotated[ObserverSession | None, Field(title="ObserverSession")] = None
    clock: Annotated[ObserverClock, Field(title="ObserverClock")]
    """
    Vazio até o session.started; a pausa é estado, não modo (ADR-0026).
    """
    pulse: Annotated[ObserverPulse | None, Field(title="ObserverPulse")] = None
    """
    O último pulso do kernel (ADR-0051): o tick de verdade, mesmo sem evento. `alive` vira falso depois de 3 pulsos perdidos. Ausente até o primeiro pulso.
    """
    weather: dict[str, Token]
    """
    Condição do clima por dia (a chave é o número do dia).
    """
    entities: dict[str, ObserverEntity]
    containers: dict[str, dict[str, ContainersAdditionalProperty]]
    motion: dict[str, ObserverMotion]
    actions: dict[str, ObserverAction]
    needs: dict[str, dict[str, NeedsAdditionalProperty]]
    """
    Último valor exato recebido de cada necessidade, por avatar.
    """
    asleep: dict[str, bool]
    sleep: dict[str, ObserverSleep] | None = None
    """
    O sono em andamento, por avatar: quando começou, o tick previsto para acordar e a cama, se houver (ADR-0052). Só com `sleep.started.v2`.
    """
    controllers: dict[str, ControllerRef]
    """
    Quem controla cada avatar.
    """
    memory: dict[str, ObserverMemory] | None = None
    """
    O caderno de cada avatar com controlador LLM (ADR-0060): as crenças atuais, as últimas anotações e a última reflexão, projetados dos eventos memory.*.
    """
    decisions: dict[str, ObserverDecision]
    metrics: dict[str, dict[str, float | dict[str, float]]] | None = None
    """
    As métricas dos últimos dias simulados (no máximo 8), por dia e por id; com agrupamento, um valor por grupo (ADR-0054).
    """


class RealtimeWelcomeV1(BaseModel):
    """
    Primeira mensagem do gateway para a UI: o estado do mundo e a linha do tempo recente (ADR-0050).
    """

    model_config = ConfigDict(
        extra="ignore",
    )
    type: Literal["campsverso.realtime.welcome.v1"]
    worldid: Annotated[str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$")]
    view: Literal["player", "operator"]
    """
    player: world e agent do avatar; operator: também internal e observer.
    """
    avatar_id: Annotated[
        str, Field(max_length=64, pattern="^[a-z0-9]+(-[a-z0-9]+)*$", title="EntityId")
    ]
    """
    O avatar que esta conexão acompanha.
    """
    commands: list[Command]
    """
    Tipos de comando que esta conexão pode mandar.
    """
    state: Annotated[ObserverState, Field(title="ObserverState")]
    """
    O mundo como se vê de fora, montado só com eventos publicados (ADR-0050). Genérico e sem nada de desenho: posições em tiles, trajetos em ticks, o que é do cartucho chega como atributo. Não carrega null: atributo nulo é atributo ausente, porque no merge patch null apaga.
    """
    events: Annotated[list[EnvelopeV1], Field(max_length=5000)]
    """
    As entradas mais recentes da linha do tempo, da mais antiga para a mais nova, já filtradas pela visão.
    """
