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
   * Tipos de entidade em que a ação aparece; `self` é o próprio avatar.
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
 * Planta murchou por falta de água.
 *
 * This interface was referenced by `ContractsBundle`'s JSON-Schema
 * via the `definition` "FarmCropWitheredV1".
 */
export interface FarmCropWitheredV1 {
  plot_id: EntityId;
  crop: ItemId;
  day: Day;
  /**
   * Viradas seguidas sem rega.
   */
  dry_days: number;
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
}
export interface ViewClock {
  tick: Tick;
  sim_time: string;
  day: Day;
  phase: Token;
}
export interface ViewWeather {
  condition: Token;
  day: Day;
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
}
export interface SessionMap {
  id: string;
  width: number;
  height: number;
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
  decisions: {
    [k: string]: ObserverDecision | undefined;
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
}
/**
 * O mapa do cartucho; o arquivo fica no gateway em /content/maps/<id>.tmj (ADR-0050).
 */
export interface ObserverMap {
  id: string;
  width: number;
  height: number;
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
}
export interface ObserverSleep {
  since_tick: Tick;
  wake_at_tick: Tick;
  bed_id?: EntityId;
}
/**
 * Último pedido de decisão do avatar.
 */
export interface ObserverDecision {
  reason: Token;
  tick: Tick;
}
