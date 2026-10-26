/* GERADO por tools/contracts-ts a partir de contracts/: não editar à mão. */

/**
 * UUID versão 7 (RFC 9562), ordenável por tempo.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Uuid7".
 */
export type Uuid7 = string;
/**
 * Id legível e estável de uma entidade: camps, plot-e-03, bed.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EntityId".
 */
export type EntityId = string;
/**
 * Id de item ou cultura; conteúdo do cartucho, em português, sem acento: moeda, semente_rabanete.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ItemId".
 */
export type ItemId = string;
/**
 * Id de ação: contador determinístico do kernel.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ActionId".
 */
export type ActionId = string;
/**
 * Nome definido pelo cartucho ou pelo kernel: ação, fase, estágio, necessidade, tipo de entidade, motivo.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Token".
 */
export type Token = string;
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Semver".
 */
export type Semver = string;
/**
 * Quem causou: human/operator, script/farmer-v1, system/kernel.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Actor".
 */
export type Actor = string;
/**
 * Tick do kernel (1 minuto simulado na fazenda).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Tick".
 */
export type Tick = number;
/**
 * Dia simulado (dia agrícola, ADR-0018), começando em 1.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Day".
 */
export type Day = number;
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ControllerType".
 */
export type ControllerType = "human" | "script" | "replay" | "llm" | "mcp" | "supervised";
/**
 * Modos do relógio na v0.1; a pausa é um estado à parte (ADR-0026).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ClockMode".
 */
export type ClockMode = "continuous" | "max";
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Scalar".
 */
export type Scalar = string | number | boolean | null;
/**
 * Política de interrupção de uma ação (ADR-0052): `never`, um comando novo é recusado com `busy`; `cancel`, cancela a ação e nada dela acontece; `partial`, interrompe e o cartucho grava o trabalho feito.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Interrupt".
 */
export type Interrupt = "never" | "cancel" | "partial";
/**
 * O terreno, uma string por linha e um caractere por tile, de cima para baixo e da esquerda para a direita (ADR-0056).
 *
 * @minItems 1
 * @maxItems 1024
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "TerrainRows".
 */
export type TerrainRows = [string, ...string[]];
/**
 * Id de uma crença do agente (ADR-0060): bel-0001.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "BeliefId".
 */
export type BeliefId = string;
/**
 * Quanto o agente acredita, de 0 a 1 (ADR-0060).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Confidence".
 */
export type Confidence = number;
/**
 * Evidências de uma crença: ticks e fatos de uma linha, do que o agente percebeu; nunca o `internal`.
 *
 * @maxItems 20
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "BeliefEvidence".
 */
export type BeliefEvidence =
  | []
  | [string]
  | [string, string]
  | [string, string, string]
  | [string, string, string, string]
  | [string, string, string, string, string]
  | [string, string, string, string, string, string]
  | [string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string]
  | [string, string, string, string, string, string, string, string, string, string, string, string]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ]
  | [
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
      string,
    ];

export interface ContractsBundle {}
/**
 * Posição em tiles.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Position".
 */
export interface Position {
  x: number;
  y: number;
}
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ItemStack".
 */
export interface ItemStack {
  item: ItemId;
  qty: number;
  /**
   * Dias até o lote mais antigo vencer pela validade nominal, quando o item tem validade (ADR-0062); zero vence hoje, negativo já passou da data e ainda não estragou (o contêiner conserva).
   */
  expires_in_days?: number;
}
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ControllerRef".
 */
export interface ControllerRef {
  type: ControllerType;
  id: string;
}
/**
 * Atributos visíveis de uma entidade (ADR-0025): nomes em snake_case, valores escalares.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Attributes".
 */
export interface Attributes {
  [k: string]: Scalar | undefined;
}
/**
 * Valor atual de cada necessidade (0 a 100), pelo nome definido no cartucho.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Needs".
 */
export interface Needs {
  [k: string]: number | undefined;
}
/**
 * Parâmetros de uma ação. A forma depende da ação e é validada pelo cartucho, não por este schema.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Params".
 */
export interface Params {
  [k: string]: unknown | undefined;
}
/**
 * Um parâmetro que quem joga escolhe (ADR-0051). Sem `choices`, é um número inteiro.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AffordanceParam".
 */
export interface AffordanceParam {
  name: Token;
  label: string;
  choices?: string[];
  /**
   * Onde as escolhas valem: a lista toda, o que o avatar tem ou o que a entidade clicada guarda.
   */
  source: "any" | "inventory" | "target";
  minimum?: number;
  default?: number;
  /**
   * As escolhas incluem também as entidades guardadas na fonte, pelo id: as ferramentas no inventário ou no baú (ADR-0068).
   */
  entities?: boolean;
}
/**
 * Uma ação no menu de um tipo de entidade, ou do próprio avatar (`self`). O menu só sugere; quem decide é o kernel (ADR-0051).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Affordance".
 */
export interface Affordance {
  action: Token;
  label: string;
  /**
   * Tipos de entidade em que a ação aparece; `self` é o próprio avatar; um tipo de terreno (`grass`) põe a ação no menu de um tile vazio desse terreno, e o tile vai em `target` como `{x, y}` (ADR-0068).
   *
   * @minItems 1
   */
  on: [Token, ...Token[]];
  /**
   * A entidade clicada vai no parâmetro `target`.
   */
  target: boolean;
  params?: AffordanceParam[];
}
/**
 * Como a linha do tempo conta um tipo de evento, declarado pelo cartucho (ADR-0068). Vale o rótulo mais específico (mais campos em `where`) cujos campos do texto existem no evento; no empate, o primeiro declarado. Sem rótulo, a tela mostra o tipo cru.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EventLabel".
 */
export interface EventLabel {
  event: string;
  /**
   * Campos do evento que precisam bater; caminhos com ponto (`params.action`).
   */
  where?: {
    [k: string]: Scalar | undefined;
  };
  /**
   * O texto, com campos do evento entre chaves e caminhos com ponto (`plantou {params.crop} no {params.target}`).
   */
  text: string;
}
/**
 * Uma métrica do dia simulado, declarada pelo cartucho e contada pela projeção comum (ADR-0054). `count` conta um tipo de evento, ou soma um campo dele com `field` (ADR-0069); `max_need` guarda o pico de uma necessidade; `item` guarda a quantidade de um item com os avatares no fim do dia.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "Metric".
 */
export interface Metric {
  id: Token;
  label: string;
  kind: "count" | "max_need" | "item";
  /**
   * Num `count`, o campo numérico do evento que se soma no lugar de contar: as moedas recebidas, por exemplo (ADR-0069).
   */
  field?: string;
  /**
   * O tipo de evento contado (`count`).
   */
  event?: string;
  /**
   * Campos do evento que precisam bater; caminhos com ponto (`params.target`).
   */
  where?: {
    [k: string]: Scalar | undefined;
  };
  by?: MetricGroup;
  need?: Token;
  item?: ItemId;
}
export interface MetricGroup {
  field: string;
  attribute?: Token;
}
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "SeenClock".
 */
export interface SeenClock {
  tick: Tick;
  sim_time: string;
  day: Day;
  phase: Token;
  /**
   * A data do calendário do ano acelerado (ADR-0067), à parte do simtime; ausente sem ano declarado.
   */
  date?: string;
  season?: Token;
}
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "SeenWeather".
 */
export interface SeenWeather {
  condition: Token;
  day: Day;
  tomorrow?: Token;
}
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "SeenAction".
 */
export interface SeenAction {
  action_id: ActionId;
  action: Token;
  params: Params;
  end_tick: Tick;
  applied_tick?: Tick;
  interrupt?: Interrupt;
}
/**
 * O próprio avatar: posição, necessidades, se dorme e a ação em curso.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "SeenSelf".
 */
export interface SeenSelf {
  entity_id: EntityId;
  position: Position;
  needs: Needs;
  asleep: boolean;
  action?: SeenAction;
}
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "SeenContainer".
 */
export interface SeenContainer {
  container_id: EntityId;
  items: ItemStack[];
}
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "SeenEntity".
 */
export interface SeenEntity {
  entity_id: EntityId;
  kind: Token;
  position?: Position;
  container_id?: EntityId;
  attributes: Attributes;
}
/**
 * O pedido de decisão que a entrega da percepção responde: o motivo e quem deve responder (ADR-0048).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "DecisionRequest".
 */
export interface DecisionRequest {
  reason:
    | "session_started"
    | "possessed"
    | "action_completed"
    | "action_rejected"
    | "action_interrupted"
    | "phase_changed"
    | "need_threshold"
    | "woke_up";
  controller: ControllerRef;
}
/**
 * Um evento que o avatar percebeu desde a última entrega: o tick, o tipo e o payload, como foram publicados.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "SeenEvent".
 */
export interface SeenEvent {
  tick: Tick;
  type: string;
  data: {
    [k: string]: unknown | undefined;
  };
}
/**
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "TerrainTile".
 */
export interface TerrainTile {
  /**
   * A classe do tile no tileset (grass, river…); vazia quando o tile não tem classe.
   */
  kind: string;
  properties: Attributes;
}
/**
 * Legenda do terreno: o que cada caractere das linhas significa (ADR-0056).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "TerrainLegend".
 */
export interface TerrainLegend {
  [k: string]: TerrainTile | undefined;
}
/**
 * O terreno ao alcance do avatar: as linhas a partir de origin (o canto superior esquerdo da janela), com a legenda.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "TerrainWindow".
 */
export interface TerrainWindow {
  origin: Position;
  rows: TerrainRows;
  legend: TerrainLegend;
}
/**
 * O que o cartucho declara sobre a percepção (ADR-0056).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "PerceptionConfig".
 */
export interface PerceptionConfig {
  /**
   * Distância de Chebyshev, em tiles, do que um avatar enxerga; null é o mapa inteiro.
   */
  radius: number | null;
  /**
   * Tipos de entidade que todo avatar enxerga além do raio: as construções fixas, que quem mora ali conhece (ADR-0067). Ausente: nenhum.
   */
  landmarks?: Token[];
  /**
   * O raio em cada fase do dia, por nome da fase; a fase que não aparece usa `radius` (ADR-0068).
   */
  by_phase?: {
    [k: string]: number | undefined;
  };
  /**
   * Itens que, no inventário do avatar, garantem um raio mínimo: item -> raio (a lanterna; ADR-0068).
   */
  lights?: {
    [k: string]: number | undefined;
  };
}
/**
 * Tokens de uma chamada de modelo, como o provedor os contou (ADR-0058): entrada, saída, lidos do cache e gravados no cache.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "LlmUsage".
 */
export interface LlmUsage {
  input_tokens: number;
  output_tokens: number;
  cache_read_input_tokens?: number;
  cache_creation_input_tokens?: number;
}
/**
 * De onde a crença veio (contratos §8.4): do que o agente observou, ou de quem lhe contou (`by`).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "BeliefSource".
 */
export interface BeliefSource {
  kind: "observation" | "told";
  /**
   * Quem contou, quando `kind` é `told`.
   */
  by?: string;
}
/**
 * Controlador propõe uma ação para o avatar.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "CmdActionProposeV1".
 */
export interface CmdActionProposeV1 {
  avatar_id: EntityId;
  action: Token;
  params: Params;
  intent?: string;
  at_tick?: Tick;
}
/**
 * Pede a posse do avatar para um controlador.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "CmdAvatarPossessV1".
 */
export interface CmdAvatarPossessV1 {
  avatar_id: EntityId;
  controller: ControllerRef;
}
/**
 * Devolve o avatar ao controlador padrão do cartucho.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "CmdAvatarReleaseV1".
 */
export interface CmdAvatarReleaseV1 {
  avatar_id: EntityId;
}
/**
 * Pede a pausa do relógio.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "CmdClockPauseV1".
 */
export interface CmdClockPauseV1 {
  reason: "debug" | "maintenance" | "budget";
}
/**
 * Pede a retomada do relógio.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "CmdClockResumeV1".
 */
export interface CmdClockResumeV1 {}
/**
 * Pede a troca de modo do relógio.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "CmdClockSetModeV1".
 */
export interface CmdClockSetModeV1 {
  mode: ClockMode;
  reason?: string;
}
/**
 * Pede a troca de escala do relógio.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "CmdClockSetScaleV1".
 */
export interface CmdClockSetScaleV1 {
  scale: number;
  reason: "operator" | "experiment" | "budget" | "human";
}
/**
 * Avança N ticks com o relógio pausado.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "CmdClockStepV1".
 */
export interface CmdClockStepV1 {
  ticks: number;
}
/**
 * Pede a alternância de uma regra (ADR-0015).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "CmdRulesToggleV1".
 */
export interface CmdRulesToggleV1 {
  rule: Token;
  enabled: boolean;
  params?: Attributes;
  reason: string;
  experiment_id?: string;
}
/**
 * Envelope CloudEvents 1.0 com as extensões do Campsverso (contratos §5; ADR-0012, ADR-0013, ADR-0031). Os nomes dos atributos seguem o CloudEvents: minúsculas sem separador (ADR-0030).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EnvelopeV1".
 */
export interface EnvelopeV1 {
  specversion: "1.0";
  id: Uuid7;
  source: string;
  type: string;
  time: string;
  subject?: string;
  datacontenttype: "application/json";
  dataschema: string;
  worldid: string;
  cartridge: string;
  tick?: number;
  simtime?: string;
  seq: number;
  actor?: string;
  controller?: ControllerType;
  controllerid?: string;
  causationid?: Uuid7;
  correlationid?: Uuid7;
  provenance: "simulated" | "real" | "staged";
  visibility: "world" | "agent" | "observer" | "internal";
  traceparent?: string;
  data: {};
}
/**
 * Ação validada e agendada; applied_tick permite o replay exato.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ActionAcceptedV1".
 */
export interface ActionAcceptedV1 {
  action_id: ActionId;
  avatar_id: EntityId;
  action: Token;
  params: Params;
  applied_tick: Tick;
  /**
   * Duração prevista.
   */
  duration_ticks: number;
  replaces?: ActionId;
  interrupt?: Interrupt;
  /**
   * A intenção declarada na proposta (cmd.action.propose), copiada pelo kernel; a tela e a linha do tempo a mostram (ADR-0059).
   */
  intent?: string;
}
/**
 * Ação concluída; observable é só um resumo legível.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ActionCompletedV1".
 */
export interface ActionCompletedV1 {
  action_id: ActionId;
  avatar_id: EntityId;
  action: Token;
  params: Params;
  /**
   * Duração real.
   */
  duration_ticks: number;
  observable?: ObservableChange[];
}
export interface ObservableChange {
  entity_id: EntityId;
  property: Token;
  before: Scalar;
  after: Scalar;
}
/**
 * Regras, inclusive ocultas, que contribuíram para o resultado de uma ação.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ActionEffectsExplainedV1".
 */
export interface ActionEffectsExplainedV1 {
  action_id: ActionId;
  /**
   * @minItems 1
   */
  rules_applied: [RuleApplied, ...RuleApplied[]];
}
export interface RuleApplied {
  rule: Token;
  version: Semver;
  hidden: boolean;
  multiplier?: number;
}
/**
 * Ação iniciada que não chegou ao fim.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ActionFailedV1".
 */
export interface ActionFailedV1 {
  action_id: ActionId;
  avatar_id: EntityId;
  action: Token;
  reason: Token;
  /**
   * Quantos ticks a ação durou antes de parar (ADR-0052).
   */
  elapsed_ticks?: number;
}
/**
 * Ação recusada, com motivo legível por máquina.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "ActionRejectedV1".
 */
export interface ActionRejectedV1 {
  avatar_id: EntityId;
  action: Token;
  params: Params;
  reason: Token;
  detail?: string;
}
/**
 * O avatar está ocioso; o controlador com a posse responde com cmd.action.propose e o mesmo correlationid.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarDecisionRequestedV1".
 */
export interface AvatarDecisionRequestedV1 {
  avatar_id: EntityId;
  reason:
    | "session_started"
    | "possessed"
    | "action_completed"
    | "action_rejected"
    | "action_interrupted"
    | "phase_changed"
    | "need_threshold"
    | "woke_up";
  controller: ControllerRef;
  needs: Needs;
  position: Position;
}
/**
 * O avatar entrou no mundo (ADR-0072): um avatar declarado fora dele, como o ajudante que chega para trabalhar, aparece numa posição e passa a receber pedidos de decisão.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarEnteredV1".
 */
export interface AvatarEnteredV1 {
  avatar_id: EntityId;
  position: Position;
  reason: Token;
}
/**
 * O avatar desmaiou: acordado às 02:00 ou sem energia (ADR-0014).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarFaintedV1".
 */
export interface AvatarFaintedV1 {
  avatar_id: EntityId;
  reason: "late_night" | "exhausted";
  position: Position;
}
/**
 * O avatar saiu do mundo (ADR-0072): some do mapa, a ação em andamento é cancelada, as necessidades param, e ele não recebe pedidos de decisão até entrar de novo.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarLeftV1".
 */
export interface AvatarLeftV1 {
  avatar_id: EntityId;
  position?: Position;
  reason: Token;
}
/**
 * Posse do avatar assumida por um controlador.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarPossessedV1".
 */
export interface AvatarPossessedV1 {
  avatar_id: EntityId;
  previous_controller?: ControllerRef;
  controller: ControllerRef;
  by: Actor;
}
/**
 * Posse devolvida ao controlador padrão do cartucho.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarReleasedV1".
 */
export interface AvatarReleasedV1 {
  avatar_id: EntityId;
  previous_controller: ControllerRef;
  controller: ControllerRef;
  by: Actor;
}
/**
 * @deprecated
 * O avatar acordou (ADR-0014). Substituído pelo v2, sem produtor desde o M2 (ADR-0042).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarSleepEndedV1".
 */
export interface AvatarSleepEndedV1 {
  avatar_id: EntityId;
  cause: "bed" | "faint";
  energy: number;
}
/**
 * O avatar acordou (ADR-0014, ADR-0041, ADR-0042).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarSleepEndedV2".
 */
export interface AvatarSleepEndedV2 {
  avatar_id: EntityId;
  /**
   * voluntary: o controlador mandou dormir; faint: desmaio.
   */
  cause: "voluntary" | "faint";
  bed_id?: EntityId;
  energy: number;
}
/**
 * @deprecated
 * O avatar dormiu na cama ou desmaiou (ADR-0014). Substituído pelo v2, sem produtor desde o M2 (ADR-0042).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarSleepStartedV1".
 */
export interface AvatarSleepStartedV1 {
  avatar_id: EntityId;
  cause: "bed" | "faint";
  position: Position;
  wake_at_tick: Tick;
}
/**
 * O avatar dormiu por escolha, na cama ou onde estava, ou desmaiou (ADR-0014, ADR-0041, ADR-0042).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "AvatarSleepStartedV2".
 */
export interface AvatarSleepStartedV2 {
  avatar_id: EntityId;
  /**
   * voluntary: o controlador mandou dormir; faint: desmaio.
   */
  cause: "voluntary" | "faint";
  bed_id?: EntityId;
  position: Position;
  wake_at_tick: Tick;
}
/**
 * Quem contratou dispensou o ajudante antes do fim (ADR-0072): ele vai embora, e os dias pagos não voltam.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EconomyLaborDismissedV1".
 */
export interface EconomyLaborDismissedV1 {
  helper: EntityId;
  employer: EntityId;
  /**
   * Os dias pagos que ficaram sem trabalho.
   */
  days_left: number;
  day: Day;
}
/**
 * O contrato do ajudante terminou (ADR-0072): ele trabalhou o último dia pago e volta a ficar livre no quadro.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EconomyLaborEndedV1".
 */
export interface EconomyLaborEndedV1 {
  helper: EntityId;
  employer: EntityId;
  day: Day;
}
/**
 * Alguém contratou um ajudante no quadro (ADR-0072): por `days` dias, pago adiantado; ele chega na manhã de `first_day`.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EconomyLaborHiredV1".
 */
export interface EconomyLaborHiredV1 {
  helper: EntityId;
  employer: EntityId;
  /**
   * Os dias contratados.
   */
  days: number;
  /**
   * A diária, em moedas.
   */
  wage: number;
  /**
   * O que se pagou na hora: a diária vezes os dias.
   */
  total: number;
  first_day: Day;
  day: Day;
}
/**
 * Alguém aceitou um pedido do quadro (ADR-0069): o pedido fica com ele até a entrega ou o prazo.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EconomyOrderAcceptedV1".
 */
export interface EconomyOrderAcceptedV1 {
  order_id: EntityId;
  taker: EntityId;
  day: Day;
}
/**
 * Um pedido aceito foi entregue no prazo e pago na hora (ADR-0069).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EconomyOrderDeliveredV1".
 */
export interface EconomyOrderDeliveredV1 {
  order_id: EntityId;
  /**
   * Quem pediu, como aparece no quadro (Dona Cida, a padaria da praça).
   */
  client: string;
  item: ItemId;
  qty: number;
  /**
   * O pagamento total, em moedas, na entrega.
   */
  reward: number;
  taker: EntityId;
  day: Day;
}
/**
 * O prazo de um pedido passou e ele saiu do quadro (ADR-0069). Com `taker`, era um pedido aceito e não entregue.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EconomyOrderExpiredV1".
 */
export interface EconomyOrderExpiredV1 {
  order_id: EntityId;
  /**
   * Quem pediu, como aparece no quadro (Dona Cida, a padaria da praça).
   */
  client: string;
  item: ItemId;
  qty: number;
  due_day: Day;
  taker?: EntityId;
  day: Day;
}
/**
 * Um pedido novo apareceu num quadro de encomendas (ADR-0069): quem pede, o quê, quanto, até quando e quanto paga. O pedido é uma entidade dentro do quadro.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "EconomyOrderPostedV1".
 */
export interface EconomyOrderPostedV1 {
  order_id: EntityId;
  board_id: EntityId;
  /**
   * Quem pediu, como aparece no quadro (Dona Cida, a padaria da praça).
   */
  client: string;
  item: ItemId;
  qty: number;
  /**
   * O pagamento total, em moedas, na entrega.
   */
  reward: number;
  posted_day: Day;
  due_day: Day;
}
/**
 * Pagamento das vendas às 06:00, com o preço de cada item.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "FarmBuyerPaidV1".
 */
export interface FarmBuyerPaidV1 {
  container_id: EntityId;
  /**
   * @minItems 1
   */
  items: [PaidItem, ...PaidItem[]];
  total: number;
  day: Day;
}
export interface PaidItem {
  item: ItemId;
  qty: number;
  unit_price: number;
}
/**
 * Uma planta madura amanheceu comida por um bicho, e o canteiro ficou vazio (ADR-0067). O efeito é visível; por que este canteiro e não outro, não.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "FarmCropEatenV1".
 */
export interface FarmCropEatenV1 {
  plot_id: EntityId;
  crop: ItemId;
  day: Day;
  by: Token;
}
/**
 * Uma planta madura foi derrubada pela tempestade da noite, e o canteiro ficou vazio (ADR-0069). A tempestade vem na previsão da véspera.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "FarmCropKnockedDownV1".
 */
export interface FarmCropKnockedDownV1 {
  plot_id: EntityId;
  crop: ItemId;
  day: Day;
}
/**
 * Planta madura; days é a evidência observável da regra oculta (bíblia §13).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "FarmCropMaturedV1".
 */
export interface FarmCropMaturedV1 {
  plot_id: EntityId;
  crop: ItemId;
  planted_day: Day;
  day: Day;
  /**
   * Dias entre o plantio e a maturidade.
   */
  days: number;
}
/**
 * Planta murchou por falta de água ou, madura, porque ninguém a colheu.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "FarmCropWitheredV1".
 */
export interface FarmCropWitheredV1 {
  plot_id: EntityId;
  crop: ItemId;
  day: Day;
  /**
   * Viradas seguidas sem rega; 0 quando a planta madura murchou porque ninguém a colheu (ADR-0062).
   */
  dry_days: number;
}
/**
 * Uma chamada de modelo terminou (ADR-0058): quem chamou, qual modelo, tokens, custo e latência. Nunca leva o prompt nem a resposta. Publicado pelo decorador da porta, não pelo adaptador.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "LlmCallCompletedV1".
 */
export interface LlmCallCompletedV1 {
  controller: ControllerRef;
  purpose: Token;
  avatar_id?: EntityId;
  provider: Token;
  model: string;
  /**
   * Hash do pedido canônico: identifica a chamada e a linha da fita, sem levar o prompt.
   */
  prompt_sha256: string;
  latency_ms: number;
  /**
   * O id do pedido no provedor, para suporte.
   */
  request_id?: string;
  usage: LlmUsage;
  /**
   * Custo nominal pela tabela de preços do ambiente.
   */
  cost_usd: number;
  /**
   * Falso quando a resposta veio da fita: ninguém pagou, e a guarda não conta.
   */
  charged: boolean;
  stop_reason: Token;
  effort?: "low" | "medium" | "high" | "xhigh" | "max";
}
/**
 * Uma chamada de modelo falhou (ADR-0058): o erro classificado, se vale repetir, e a latência até a falha.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "LlmCallFailedV1".
 */
export interface LlmCallFailedV1 {
  controller: ControllerRef;
  purpose: Token;
  avatar_id?: EntityId;
  provider: Token;
  model: string;
  /**
   * Hash do pedido canônico: identifica a chamada e a linha da fita, sem levar o prompt.
   */
  prompt_sha256: string;
  latency_ms: number;
  error:
    "rate_limit" | "timeout" | "connection" | "auth" | "bad_request" | "server" | "cassette_miss";
  message: string;
  retryable: boolean;
}
/**
 * Uma crença nova (ADR-0060; contratos §8.4): o que o agente passou a acreditar, com quanta confiança, por que evidências e de que origem.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "MemoryBeliefFormedV1".
 */
export interface MemoryBeliefFormedV1 {
  avatar_id: EntityId;
  belief_id: BeliefId;
  /**
   * A crença, em uma frase.
   */
  statement: string;
  confidence: Confidence;
  evidence: BeliefEvidence;
  source: BeliefSource;
  /**
   * Por que a reflexão fez isso.
   */
  reason?: string;
}
/**
 * O agente abandonou uma crença (ADR-0060; contratos §8.4).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "MemoryBeliefRetractedV1".
 */
export interface MemoryBeliefRetractedV1 {
  avatar_id: EntityId;
  belief_id: BeliefId;
  /**
   * A crença, em uma frase.
   */
  statement: string;
  /**
   * Por que a reflexão fez isso.
   */
  reason?: string;
}
/**
 * A confiança de uma crença mudou, ou o enunciado foi refinado (ADR-0060; contratos §8.4), com a evidência que pesou.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "MemoryBeliefUpdatedV1".
 */
export interface MemoryBeliefUpdatedV1 {
  avatar_id: EntityId;
  belief_id: BeliefId;
  /**
   * A crença, em uma frase.
   */
  statement: string;
  confidence: {
    before: Confidence;
    after: Confidence;
  };
  evidence: BeliefEvidence;
  source: BeliefSource;
  /**
   * Por que a reflexão fez isso.
   */
  reason?: string;
}
/**
 * O agente anotou algo no caderno (ADR-0060): o parâmetro `note` de uma ferramenta, com o tick do envelope. Publicado pela mente; é o que o operador vê no caderno.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "MemoryNotedV1".
 */
export interface MemoryNotedV1 {
  avatar_id: EntityId;
  day: Day;
  text: string;
}
/**
 * A reflexão de um dia terminou (ADR-0060): o resumo, o plano para amanhã e quantas crenças foram formadas, atualizadas e retiradas. Nunca leva o prompt: só o hash do pedido.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "MemoryReflectedV1".
 */
export interface MemoryReflectedV1 {
  avatar_id: EntityId;
  day: Day;
  summary: string;
  /**
   * O que o agente pretende amanhã.
   */
  plan?: string;
  beliefs: {
    formed: number;
    updated: number;
    retracted: number;
    total: number;
  };
  /**
   * O experimento que a reflexão propôs para o dia seguinte (ADR-0070).
   */
  experiment?: {
    hypothesis: string;
    test: string;
    prediction: string;
  };
  /**
   * O veredito da reflexão sobre o experimento da noite anterior (ADR-0070).
   */
  experiment_result?: "cumpriu" | "falhou" | "inconclusivo";
  /**
   * Hash do pedido da reflexão, o mesmo do llm.call.completed.
   */
  prompt_sha256?: string;
}
/**
 * O gasto com modelos estourou um teto e a guarda pediu a pausa do mundo (ADR-0058). Só o operador retoma.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "OpsBudgetExceededV1".
 */
export interface OpsBudgetExceededV1 {
  /**
   * O teto do dia simulado ou o do mundo inteiro.
   */
  scope: "day" | "total";
  day?: Day;
  spent_usd: number;
  limit_usd: number;
  /**
   * Verdadeiro quando a guarda publicou cmd.clock.pause com reason budget.
   */
  paused: boolean;
}
/**
 * O gasto com modelos passou de 50, 80 ou 100% de um teto (ADR-0058). Publicado pela guarda de orçamento.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "OpsBudgetThresholdReachedV1".
 */
export interface OpsBudgetThresholdReachedV1 {
  /**
   * O teto do dia simulado ou o do mundo inteiro.
   */
  scope: "day" | "total";
  day?: Day;
  spent_usd: number;
  limit_usd: number;
  threshold_pct: 50 | 80 | 100;
}
/**
 * Instantâneo do que o avatar percebe, a cada pedido de decisão (ADR-0028).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "PerceptionDeliveredV1".
 */
export interface PerceptionDeliveredV1 {
  avatar_id: EntityId;
  kind: "snapshot";
  as_of_tick: Tick;
  decision?: PerceptionDecision;
  view: PerceptionView;
}
/**
 * O pedido de decisão que esta foto responde: o motivo e quem deve responder. Basta este evento para o controlador agir (ADR-0048).
 */
export interface PerceptionDecision {
  reason:
    | "session_started"
    | "possessed"
    | "action_completed"
    | "action_rejected"
    | "action_interrupted"
    | "phase_changed"
    | "need_threshold"
    | "woke_up";
  controller: ControllerRef;
}
/**
 * Visão genérica: o que é da fazenda chega como atributo de entidade (ADR-0025).
 */
export interface PerceptionView {
  clock: ViewClock;
  weather: ViewWeather;
  self: ViewSelf;
  containers: ViewContainer[];
  entities: ViewEntity[];
  map?: TerrainWindow;
}
export interface ViewClock {
  tick: Tick;
  sim_time: string;
  day: Day;
  phase: Token;
  /**
   * A data do calendário do ano acelerado (ADR-0067), à parte do simtime; ausente sem ano declarado.
   */
  date?: string;
  season?: Token;
}
export interface ViewWeather {
  condition: Token;
  day: Day;
  tomorrow?: Token;
}
export interface ViewSelf {
  entity_id: EntityId;
  position: Position;
  needs: Needs;
  asleep: boolean;
  action?: ViewAction;
}
export interface ViewAction {
  action_id: ActionId;
  action: Token;
  params: Params;
  end_tick: Tick;
  applied_tick?: Tick;
  interrupt?: Interrupt;
}
export interface ViewContainer {
  container_id: EntityId;
  items: ItemStack[];
}
export interface ViewEntity {
  entity_id: EntityId;
  kind: Token;
  position?: Position;
  container_id?: EntityId;
  attributes: Attributes;
}
/**
 * O delta da percepção (ADR-0028, ADR-0056): o que mudou desde a última entrega ao avatar e o que aconteceu no meio-tempo. Responde a um pedido de decisão como a foto, para os controladores que pedem deltas; a foto continua em perception.delivered.v1.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "PerceptionUpdatedV1".
 */
export interface PerceptionUpdatedV1 {
  avatar_id: EntityId;
  since_tick: Tick;
  as_of_tick: Tick;
  decision: DecisionRequest;
  clock: SeenClock;
  weather?: SeenWeather;
  self: SeenSelf;
  /**
   * Os contêineres cujo conteúdo mudou, inteiros.
   */
  containers?: SeenContainer[];
  /**
   * As entidades que apareceram ou mudaram (posição, contêiner ou atributos), com o registro inteiro.
   */
  entities?: SeenEntity[];
  /**
   * As entidades que deixaram de existir à vista do avatar desde a entrega anterior (removidas do mundo). As que só saíram do raio vêm em `out_of_view` (ADR-0067).
   */
  gone?: EntityId[];
  /**
   * As entidades que saíram do raio de percepção desde a entrega anterior e continuam no mundo: quem lembra delas sabe que estão lá (ADR-0067).
   */
  out_of_view?: EntityId[];
  /**
   * O que aconteceu desde a entrega anterior, na ordem em que foi publicado: alimenta a memória e a narrativa (M11).
   *
   * @maxItems 1000
   */
  events: SeenEvent[];
}
/**
 * Efeito numérico de uma regra sobre uma entidade.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "RulesEffectAppliedV1".
 */
export interface RulesEffectAppliedV1 {
  rule: Token;
  version: Semver;
  entity_id: EntityId;
  property: Token;
  base: number;
  applied: number;
}
/**
 * Conjunto de regras carregado, com versões e estado inicial.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "RulesLoadedV1".
 */
export interface RulesLoadedV1 {
  rules: LoadedRule[];
  source_ref: string;
}
export interface LoadedRule {
  rule: Token;
  version: Semver;
  hidden: boolean;
  enabled: boolean;
  params: Attributes;
}
/**
 * Regra ligada, desligada ou parametrizada a quente (ADR-0015).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "RulesToggledV1".
 */
export interface RulesToggledV1 {
  rule: Token;
  from_version: Semver;
  to_version: Semver;
  enabled: boolean;
  params?: Attributes;
  by: Actor;
  reason: string;
  experiment_id?: string;
  effective_at_tick: Tick;
}
/**
 * Salto de tempo até o próximo evento agendado (simulação de eventos discretos).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldClockJumpedV1".
 */
export interface WorldClockJumpedV1 {
  from_tick: Tick;
  to_tick: Tick;
}
/**
 * Mudança de modo do relógio (ADR-0026).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldClockModeChangedV1".
 */
export interface WorldClockModeChangedV1 {
  previous_mode: ClockMode;
  mode: ClockMode;
  reason: string;
  by: Actor;
}
/**
 * Relógio pausado; a pausa é um estado, não um modo (ADR-0026).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldClockPausedV1".
 */
export interface WorldClockPausedV1 {
  reason: "debug" | "maintenance" | "budget";
  by: Actor;
}
/**
 * Mudança de fase do dia; os nomes das fases vêm do cartucho.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldClockPhaseChangedV1".
 */
export interface WorldClockPhaseChangedV1 {
  phase: Token;
  day: Day;
  /**
   * A data do calendário do ano acelerado (ADR-0067), à parte do simtime; ausente sem ano declarado.
   */
  date?: string;
  season?: Token;
}
/**
 * Relógio retomado no modo em que estava (ADR-0026).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldClockResumedV1".
 */
export interface WorldClockResumedV1 {
  by: Actor;
}
/**
 * Mudança de escala do relógio.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldClockScaleChangedV1".
 */
export interface WorldClockScaleChangedV1 {
  previous_scale: number;
  scale: number;
  reason: "operator" | "experiment" | "budget" | "human";
  by: Actor;
}
/**
 * A estação mudou na virada do dia, num mundo com ano declarado pelo cartucho (ADR-0067). A data é a do calendário do ano acelerado, à parte do simtime.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldClockSeasonChangedV1".
 */
export interface WorldClockSeasonChangedV1 {
  day: Day;
  /**
   * A data do calendário no dia da troca.
   */
  date: string;
  season: Token;
  previous_season?: Token;
}
/**
 * Avanço passo a passo com o relógio pausado.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldClockSteppedV1".
 */
export interface WorldClockSteppedV1 {
  ticks: number;
  from_tick: Tick;
  to_tick: Tick;
}
/**
 * Comando que não é ação (posse, relógio, regras) foi recusado.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldCommandRejectedV1".
 */
export interface WorldCommandRejectedV1 {
  command_id: Uuid7;
  command_type: string;
  reason: Token;
  detail?: string;
}
/**
 * Entidade removida do mundo em tempo de execução (o canteiro vazio que volta a ser grama; ADR-0067). Avatares, contêineres com itens e alvos de ações em andamento não se removem.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldEntityDespawnedV1".
 */
export interface WorldEntityDespawnedV1 {
  entity_id: EntityId;
  kind: Token;
  position?: Position;
  reason: Token;
  action_id?: ActionId;
}
/**
 * Movimento interrompido; traz a posição real no momento (D1).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldEntityMoveInterruptedV1".
 */
export interface WorldEntityMoveInterruptedV1 {
  entity_id: EntityId;
  action_id: ActionId;
  position: Position;
  reason: "cancelled" | "blocked" | "fainted";
}
/**
 * Movimento como trajeto: só esquinas e destino; a UI interpola (D1).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldEntityMovedV1".
 */
export interface WorldEntityMovedV1 {
  entity_id: EntityId;
  action_id: ActionId;
  origin: Position;
  /**
   * Pontos de inflexão do trajeto e o destino.
   *
   * @minItems 1
   */
  waypoints: [Position, ...Position[]];
  depart_tick: Tick;
  arrival_tick: Tick;
  tiles_per_tick: number;
}
/**
 * Entidade criada: no mapa (position) ou dentro de um contêiner (container_id).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldEntitySpawnedV1".
 */
export interface WorldEntitySpawnedV1 {
  entity_id: EntityId;
  kind: Token;
  position?: Position;
  container_id?: EntityId;
  /**
   * Se a entidade bloqueia a passagem no mapa.
   */
  blocking: boolean;
  display_name?: string;
  attributes?: Attributes;
  action_id?: ActionId;
}
/**
 * Mudança de atributos visíveis de uma entidade (ADR-0025).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldEntityStateChangedV1".
 */
export interface WorldEntityStateChangedV1 {
  entity_id: EntityId;
  changes: Attributes;
  cause?: Token;
  action_id?: ActionId;
}
/**
 * Entidade guardada noutro contêiner (uma ferramenta que vai do avatar para o baú, ou volta), sem posição no mapa (ADR-0062).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldEntityStoredV1".
 */
export interface WorldEntityStoredV1 {
  entity_id: EntityId;
  from_container?: EntityId;
  to_container: EntityId;
  action_id?: ActionId;
}
/**
 * Item saiu do mundo.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldItemConsumedV1".
 */
export interface WorldItemConsumedV1 {
  item: ItemId;
  qty: number;
  container_id: EntityId;
  reason: Token;
  action_id?: ActionId;
  expires_day?: Day;
}
/**
 * Item surgiu num contêiner.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldItemCreatedV1".
 */
export interface WorldItemCreatedV1 {
  item: ItemId;
  qty: number;
  container_id: EntityId;
  reason: Token;
  action_id?: ActionId;
  expires_day?: Day;
}
/**
 * Item passou de um contêiner para outro.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldItemTransferredV1".
 */
export interface WorldItemTransferredV1 {
  item: ItemId;
  qty: number;
  from_container: EntityId;
  to_container: EntityId;
  reason: Token;
  action_id?: ActionId;
  expires_day?: Day;
}
/**
 * Valor de uma necessidade; no máximo um por hora simulada por necessidade.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldNeedChangedV1".
 */
export interface WorldNeedChangedV1 {
  avatar_id: EntityId;
  need: Token;
  previous_value: number;
  value: number;
}
/**
 * Uma necessidade cruzou um limiar definido pelo cartucho.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldNeedThresholdCrossedV1".
 */
export interface WorldNeedThresholdCrossedV1 {
  avatar_id: EntityId;
  need: Token;
  threshold: number;
  direction: "up" | "down";
  value: number;
}
/**
 * Mundo carregado ou retomado a partir de snapshot.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldSessionStartedV1".
 */
export interface WorldSessionStartedV1 {
  cartridge_version: Semver;
  /**
   * Seed registrada; os fluxos de RNG nomeados derivam dela.
   */
  seed: number;
  /**
   * Duração de um tick em segundos simulados.
   */
  tick_seconds: number;
  mode: ClockMode;
  paused: boolean;
  /**
   * Segundos simulados por segundo real.
   */
  scale: number;
  /**
   * Verdadeiro quando o mundo foi retomado a partir de snapshot.
   */
  resumed: boolean;
  map: SessionMap;
  /**
   * Catálogo de ações que o cartucho oferece a quem joga (ADR-0051). O menu só sugere; quem decide é o kernel.
   */
  affordances?: Affordance[];
  /**
   * Catálogo de métricas do dia que o cartucho declara (ADR-0054).
   *
   * @maxItems 64
   */
  metrics?: Metric[];
  /**
   * Os rótulos da linha do tempo que o cartucho declara (ADR-0068).
   *
   * @maxItems 256
   */
  labels?: EventLabel[];
  perception?: PerceptionConfig;
}
export interface SessionMap {
  id: string;
  width: number;
  height: number;
  rows?: TerrainRows;
  legend?: TerrainLegend;
}
/**
 * Snapshot persistido no BlobStore.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldSnapshotCreatedV1".
 */
export interface WorldSnapshotCreatedV1 {
  snapshot_id: string;
  ref: string;
  last_seq: number;
  sha256: string;
  size_bytes: number;
}
/**
 * Clima sorteado para um dia agrícola (ADR-0018).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "WorldWeatherChangedV1".
 */
export interface WorldWeatherChangedV1 {
  condition: Token;
  day: Day;
  /**
   * O tempo de um dia que ainda não chegou: a previsão, publicada na véspera (ADR-0069).
   */
  forecast?: boolean;
}
/**
 * Pulso do kernel: o tick de verdade e o relógio, a cada kernel.pulse_seconds de tempo real. Vai para campsverso.<mundo>.live.kernel, que nenhum stream guarda: não entra no histórico, no arquivo JSONL nem no replay (ADR-0051).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "LiveKernelV1".
 */
export interface LiveKernelV1 {
  type: "campsverso.live.kernel.v1";
  worldid: string;
  tick: Tick;
  sim_time: string;
  mode: ClockMode;
  scale: number;
  paused: boolean;
  /**
   * O intervalo entre pulsos; quem escuta usa para saber quando o kernel ficou sem sinal.
   */
  pulse_seconds: number;
  /**
   * Relógio de parede de quem mandou.
   */
  sent_at: string;
}
/**
 * Pedido da UI para o gateway publicar um comando. O gateway monta o envelope e o valida contra o contrato do comando (ADR-0050).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "RealtimeCommandV1".
 */
export interface RealtimeCommandV1 {
  type: "campsverso.realtime.command.v1";
  /**
   * Escolhido pela UI; volta no reply.
   */
  request_id: string;
  command: string;
  data: Params;
}
/**
 * Resposta do gateway a um command: publicado ou recusado. Quem aceita ou recusa o comando no mundo é o kernel, com um evento (ADR-0050).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "RealtimeReplyV1".
 */
export interface RealtimeReplyV1 {
  type: "campsverso.realtime.reply.v1";
  request_id: string;
  ok: boolean;
  command_id?: Uuid7;
  error?: RealtimeError;
}
export interface RealtimeError {
  code: "not_allowed" | "invalid_command" | "unavailable" | "invalid_message";
  message: string;
}
/**
 * O que mudou desde a última mensagem: um merge patch do estado (RFC 7386) e os eventos do intervalo, filtrados pela visão (ADR-0050).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "RealtimeUpdateV1".
 */
export interface RealtimeUpdateV1 {
  type: "campsverso.realtime.update.v1";
  /**
   * Merge patch (RFC 7386) sobre o ObserverState; null apaga a chave.
   */
  patch: {};
  /**
   * @maxItems 5000
   */
  events: EnvelopeV1[];
}
/**
 * Primeira mensagem do gateway para a UI: o estado do mundo e a linha do tempo recente (ADR-0050).
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "RealtimeWelcomeV1".
 */
export interface RealtimeWelcomeV1 {
  type: "campsverso.realtime.welcome.v1";
  worldid: string;
  /**
   * player: world e agent do avatar; operator: também internal e observer.
   */
  view: "player" | "operator";
  avatar_id: EntityId;
  /**
   * Tipos de comando que esta conexão pode mandar.
   */
  commands: string[];
  state: ObserverState;
  /**
   * As entradas mais recentes da linha do tempo, da mais antiga para a mais nova, já filtradas pela visão.
   *
   * @maxItems 5000
   */
  events: EnvelopeV1[];
}
/**
 * O mundo como se vê de fora, montado só com eventos publicados (ADR-0050). Genérico e sem nada de desenho: posições em tiles, trajetos em ticks, o que é do cartucho chega como atributo. Não carrega null: atributo nulo é atributo ausente, porque no merge patch null apaga.
 */
export interface ObserverState {
  cartridge?: Token;
  tick: Tick;
  /**
   * Hora simulada do tick mais recente.
   */
  sim_time?: string;
  day: Day;
  phase: Token;
  /**
   * A data do calendário do ano acelerado (ADR-0067), da última mudança de fase; ausente sem ano declarado.
   */
  date?: string;
  season?: Token;
  session?: ObserverSession;
  clock: ObserverClock;
  pulse?: ObserverPulse;
  /**
   * Condição do clima por dia (a chave é o número do dia).
   */
  weather: {
    [k: string]: Token | undefined;
  };
  entities: {
    [k: string]: ObserverEntity | undefined;
  };
  containers: {
    [k: string]:
      | {
          [k: string]: number | undefined;
        }
      | undefined;
  };
  motion: {
    [k: string]: ObserverMotion | undefined;
  };
  actions: {
    [k: string]: ObserverAction | undefined;
  };
  /**
   * Último valor exato recebido de cada necessidade, por avatar.
   */
  needs: {
    [k: string]: Needs | undefined;
  };
  asleep: {
    [k: string]: boolean | undefined;
  };
  /**
   * O sono em andamento, por avatar: quando começou, o tick previsto para acordar e a cama, se houver (ADR-0052). Só com `sleep.started.v2`.
   */
  sleep?: {
    [k: string]: ObserverSleep | undefined;
  };
  /**
   * Quem controla cada avatar.
   */
  controllers: {
    [k: string]: ControllerRef | undefined;
  };
  /**
   * O caderno de cada avatar com controlador LLM (ADR-0060): as crenças atuais, as últimas anotações e a última reflexão, projetados dos eventos memory.*.
   */
  memory?: {
    [k: string]: ObserverMemory | undefined;
  };
  decisions: {
    [k: string]: ObserverDecision | undefined;
  };
  /**
   * As métricas dos últimos dias simulados (no máximo 8), por dia e por id; com agrupamento, um valor por grupo (ADR-0054).
   */
  metrics?: {
    [k: string]: ObserverDayMetrics | undefined;
  };
}
export interface ObserverSession {
  cartridge_version: Semver;
  tick_seconds: number;
  map?: ObserverMap;
  /**
   * O catálogo de ações do session.started, para montar os menus (ADR-0051).
   */
  affordances?: Affordance[];
  /**
   * O catálogo de métricas do session.started (ADR-0054).
   */
  metrics?: Metric[];
  /**
   * Os rótulos da linha do tempo do session.started (ADR-0068).
   */
  labels?: EventLabel[];
  perception?: PerceptionConfig;
}
/**
 * O mapa do cartucho; o arquivo fica no gateway em /content/maps/<id>.tmj (ADR-0050).
 */
export interface ObserverMap {
  id: string;
  width: number;
  height: number;
  rows?: TerrainRows;
  legend?: TerrainLegend;
}
/**
 * Vazio até o session.started; a pausa é estado, não modo (ADR-0026).
 */
export interface ObserverClock {
  mode?: ClockMode;
  scale?: number;
  paused?: boolean;
}
/**
 * O último pulso do kernel (ADR-0051): o tick de verdade, mesmo sem evento. `alive` vira falso depois de 3 pulsos perdidos. Ausente até o primeiro pulso.
 */
export interface ObserverPulse {
  tick: Tick;
  sim_time?: string;
  alive: boolean;
}
export interface ObserverEntity {
  kind: Token;
  position?: Position;
  container_id?: EntityId;
  display_name?: string;
  attributes: Attributes;
}
/**
 * Trajeto em andamento: tile a tile, a partir de depart_tick, a tiles_per_tick.
 */
export interface ObserverMotion {
  /**
   * @minItems 1
   */
  path: [Position, ...Position[]];
  depart_tick: Tick;
  tiles_per_tick: number;
}
export interface ObserverAction {
  action_id: ActionId;
  action: Token;
  params: Params;
  end_tick: Tick;
  applied_tick?: Tick;
  interrupt?: Interrupt;
  /**
   * A intenção declarada na proposta aceita, quando o controlador a deu (ADR-0059).
   */
  intent?: string;
}
export interface ObserverSleep {
  since_tick: Tick;
  wake_at_tick: Tick;
  bed_id?: EntityId;
}
export interface ObserverMemory {
  day?: Day;
  summary?: string;
  plan?: string;
  /**
   * @maxItems 50
   */
  beliefs: ObserverBelief[];
  /**
   * @maxItems 50
   */
  notes: ObserverNote[];
}
export interface ObserverBelief {
  belief_id: BeliefId;
  statement: string;
  confidence: Confidence;
}
export interface ObserverNote {
  tick: Tick;
  text: string;
}
/**
 * Último pedido de decisão do avatar.
 */
export interface ObserverDecision {
  reason: Token;
  tick: Tick;
}
export interface ObserverDayMetrics {
  [k: string]:
    | number
    | {
        [k: string]: number | undefined;
      }
    | undefined;
}
