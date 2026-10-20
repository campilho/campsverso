/* GERADO por tools/contracts-ts a partir de contracts/: não editar à mão. */
import type * as T from "./types.ts";

export type Visibility = "world" | "agent" | "observer" | "internal";
export type Kind = "event" | "command";

export interface ContractTypeInfo {
  readonly kind: Kind;
  readonly visibility: Visibility;
  readonly producer: string;
  readonly dataschema: string;
}

export const CONTRACT_TYPES = {
  "campsverso.action.accepted.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/action/accepted.v1",
  },
  "campsverso.action.completed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/action/completed.v1",
  },
  "campsverso.action.effects_explained.v1": {
    kind: "event",
    visibility: "internal",
    producer: "kernel",
    dataschema: "contracts://events/action/effects_explained.v1",
  },
  "campsverso.action.failed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/action/failed.v1",
  },
  "campsverso.action.rejected.v1": {
    kind: "event",
    visibility: "agent",
    producer: "kernel",
    dataschema: "contracts://events/action/rejected.v1",
  },
  "campsverso.avatar.decision_requested.v1": {
    kind: "event",
    visibility: "agent",
    producer: "kernel",
    dataschema: "contracts://events/avatar/decision_requested.v1",
  },
  "campsverso.avatar.fainted.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/avatar/fainted.v1",
  },
  "campsverso.avatar.possessed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/avatar/possessed.v1",
  },
  "campsverso.avatar.released.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/avatar/released.v1",
  },
  "campsverso.avatar.sleep.ended.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/avatar/sleep.ended.v1",
  },
  "campsverso.avatar.sleep.ended.v2": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/avatar/sleep.ended.v2",
  },
  "campsverso.avatar.sleep.started.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/avatar/sleep.started.v1",
  },
  "campsverso.avatar.sleep.started.v2": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/avatar/sleep.started.v2",
  },
  "campsverso.cmd.action.propose.v1": {
    kind: "command",
    visibility: "observer",
    producer: "controller",
    dataschema: "contracts://commands/action/propose.v1",
  },
  "campsverso.cmd.avatar.possess.v1": {
    kind: "command",
    visibility: "observer",
    producer: "operator",
    dataschema: "contracts://commands/avatar/possess.v1",
  },
  "campsverso.cmd.avatar.release.v1": {
    kind: "command",
    visibility: "observer",
    producer: "operator",
    dataschema: "contracts://commands/avatar/release.v1",
  },
  "campsverso.cmd.clock.pause.v1": {
    kind: "command",
    visibility: "observer",
    producer: "operator",
    dataschema: "contracts://commands/clock/pause.v1",
  },
  "campsverso.cmd.clock.resume.v1": {
    kind: "command",
    visibility: "observer",
    producer: "operator",
    dataschema: "contracts://commands/clock/resume.v1",
  },
  "campsverso.cmd.clock.set_mode.v1": {
    kind: "command",
    visibility: "observer",
    producer: "operator",
    dataschema: "contracts://commands/clock/set_mode.v1",
  },
  "campsverso.cmd.clock.set_scale.v1": {
    kind: "command",
    visibility: "observer",
    producer: "operator",
    dataschema: "contracts://commands/clock/set_scale.v1",
  },
  "campsverso.cmd.clock.step.v1": {
    kind: "command",
    visibility: "observer",
    producer: "operator",
    dataschema: "contracts://commands/clock/step.v1",
  },
  "campsverso.cmd.rules.toggle.v1": {
    kind: "command",
    visibility: "observer",
    producer: "operator",
    dataschema: "contracts://commands/rules/toggle.v1",
  },
  "campsverso.farm.buyer.paid.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/farm/buyer.paid.v1",
  },
  "campsverso.farm.crop.matured.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/farm/crop.matured.v1",
  },
  "campsverso.farm.crop.withered.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/farm/crop.withered.v1",
  },
  "campsverso.llm.call.completed.v1": {
    kind: "event",
    visibility: "observer",
    producer: "controller",
    dataschema: "contracts://events/llm/call.completed.v1",
  },
  "campsverso.llm.call.failed.v1": {
    kind: "event",
    visibility: "observer",
    producer: "controller",
    dataschema: "contracts://events/llm/call.failed.v1",
  },
  "campsverso.memory.belief.formed.v1": {
    kind: "event",
    visibility: "observer",
    producer: "controller",
    dataschema: "contracts://events/memory/belief.formed.v1",
  },
  "campsverso.memory.belief.retracted.v1": {
    kind: "event",
    visibility: "observer",
    producer: "controller",
    dataschema: "contracts://events/memory/belief.retracted.v1",
  },
  "campsverso.memory.belief.updated.v1": {
    kind: "event",
    visibility: "observer",
    producer: "controller",
    dataschema: "contracts://events/memory/belief.updated.v1",
  },
  "campsverso.memory.noted.v1": {
    kind: "event",
    visibility: "observer",
    producer: "controller",
    dataschema: "contracts://events/memory/noted.v1",
  },
  "campsverso.memory.reflected.v1": {
    kind: "event",
    visibility: "observer",
    producer: "controller",
    dataschema: "contracts://events/memory/reflected.v1",
  },
  "campsverso.ops.budget.exceeded.v1": {
    kind: "event",
    visibility: "observer",
    producer: "budget",
    dataschema: "contracts://events/ops/budget.exceeded.v1",
  },
  "campsverso.ops.budget.threshold_reached.v1": {
    kind: "event",
    visibility: "observer",
    producer: "budget",
    dataschema: "contracts://events/ops/budget.threshold_reached.v1",
  },
  "campsverso.perception.delivered.v1": {
    kind: "event",
    visibility: "agent",
    producer: "perception",
    dataschema: "contracts://events/perception/delivered.v1",
  },
  "campsverso.perception.updated.v1": {
    kind: "event",
    visibility: "agent",
    producer: "perception",
    dataschema: "contracts://events/perception/updated.v1",
  },
  "campsverso.rules.effect_applied.v1": {
    kind: "event",
    visibility: "internal",
    producer: "kernel",
    dataschema: "contracts://events/rules/effect_applied.v1",
  },
  "campsverso.rules.loaded.v1": {
    kind: "event",
    visibility: "internal",
    producer: "kernel",
    dataschema: "contracts://events/rules/loaded.v1",
  },
  "campsverso.rules.toggled.v1": {
    kind: "event",
    visibility: "internal",
    producer: "kernel",
    dataschema: "contracts://events/rules/toggled.v1",
  },
  "campsverso.world.clock.jumped.v1": {
    kind: "event",
    visibility: "internal",
    producer: "kernel",
    dataschema: "contracts://events/world/clock.jumped.v1",
  },
  "campsverso.world.clock.mode_changed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/clock.mode_changed.v1",
  },
  "campsverso.world.clock.paused.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/clock.paused.v1",
  },
  "campsverso.world.clock.phase_changed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/clock.phase_changed.v1",
  },
  "campsverso.world.clock.resumed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/clock.resumed.v1",
  },
  "campsverso.world.clock.scale_changed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/clock.scale_changed.v1",
  },
  "campsverso.world.clock.stepped.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/clock.stepped.v1",
  },
  "campsverso.world.command.rejected.v1": {
    kind: "event",
    visibility: "observer",
    producer: "kernel",
    dataschema: "contracts://events/world/command.rejected.v1",
  },
  "campsverso.world.entity.move_interrupted.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/entity.move_interrupted.v1",
  },
  "campsverso.world.entity.moved.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/entity.moved.v1",
  },
  "campsverso.world.entity.spawned.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/entity.spawned.v1",
  },
  "campsverso.world.entity.state_changed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/entity.state_changed.v1",
  },
  "campsverso.world.entity.stored.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/entity.stored.v1",
  },
  "campsverso.world.item.consumed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/item.consumed.v1",
  },
  "campsverso.world.item.created.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/item.created.v1",
  },
  "campsverso.world.item.transferred.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/item.transferred.v1",
  },
  "campsverso.world.need.changed.v1": {
    kind: "event",
    visibility: "agent",
    producer: "kernel",
    dataschema: "contracts://events/world/need.changed.v1",
  },
  "campsverso.world.need.threshold_crossed.v1": {
    kind: "event",
    visibility: "agent",
    producer: "kernel",
    dataschema: "contracts://events/world/need.threshold_crossed.v1",
  },
  "campsverso.world.session.started.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/session.started.v1",
  },
  "campsverso.world.snapshot.created.v1": {
    kind: "event",
    visibility: "internal",
    producer: "kernel",
    dataschema: "contracts://events/world/snapshot.created.v1",
  },
  "campsverso.world.weather.changed.v1": {
    kind: "event",
    visibility: "world",
    producer: "kernel",
    dataschema: "contracts://events/world/weather.changed.v1",
  },
} as const satisfies Record<string, ContractTypeInfo>;

export type ContractTypeName = keyof typeof CONTRACT_TYPES;

export interface PayloadByType {
  "campsverso.action.accepted.v1": T.ActionAcceptedV1;
  "campsverso.action.completed.v1": T.ActionCompletedV1;
  "campsverso.action.effects_explained.v1": T.ActionEffectsExplainedV1;
  "campsverso.action.failed.v1": T.ActionFailedV1;
  "campsverso.action.rejected.v1": T.ActionRejectedV1;
  "campsverso.avatar.decision_requested.v1": T.AvatarDecisionRequestedV1;
  "campsverso.avatar.fainted.v1": T.AvatarFaintedV1;
  "campsverso.avatar.possessed.v1": T.AvatarPossessedV1;
  "campsverso.avatar.released.v1": T.AvatarReleasedV1;
  "campsverso.avatar.sleep.ended.v1": T.AvatarSleepEndedV1;
  "campsverso.avatar.sleep.ended.v2": T.AvatarSleepEndedV2;
  "campsverso.avatar.sleep.started.v1": T.AvatarSleepStartedV1;
  "campsverso.avatar.sleep.started.v2": T.AvatarSleepStartedV2;
  "campsverso.cmd.action.propose.v1": T.CmdActionProposeV1;
  "campsverso.cmd.avatar.possess.v1": T.CmdAvatarPossessV1;
  "campsverso.cmd.avatar.release.v1": T.CmdAvatarReleaseV1;
  "campsverso.cmd.clock.pause.v1": T.CmdClockPauseV1;
  "campsverso.cmd.clock.resume.v1": T.CmdClockResumeV1;
  "campsverso.cmd.clock.set_mode.v1": T.CmdClockSetModeV1;
  "campsverso.cmd.clock.set_scale.v1": T.CmdClockSetScaleV1;
  "campsverso.cmd.clock.step.v1": T.CmdClockStepV1;
  "campsverso.cmd.rules.toggle.v1": T.CmdRulesToggleV1;
  "campsverso.farm.buyer.paid.v1": T.FarmBuyerPaidV1;
  "campsverso.farm.crop.matured.v1": T.FarmCropMaturedV1;
  "campsverso.farm.crop.withered.v1": T.FarmCropWitheredV1;
  "campsverso.llm.call.completed.v1": T.LlmCallCompletedV1;
  "campsverso.llm.call.failed.v1": T.LlmCallFailedV1;
  "campsverso.memory.belief.formed.v1": T.MemoryBeliefFormedV1;
  "campsverso.memory.belief.retracted.v1": T.MemoryBeliefRetractedV1;
  "campsverso.memory.belief.updated.v1": T.MemoryBeliefUpdatedV1;
  "campsverso.memory.noted.v1": T.MemoryNotedV1;
  "campsverso.memory.reflected.v1": T.MemoryReflectedV1;
  "campsverso.ops.budget.exceeded.v1": T.OpsBudgetExceededV1;
  "campsverso.ops.budget.threshold_reached.v1": T.OpsBudgetThresholdReachedV1;
  "campsverso.perception.delivered.v1": T.PerceptionDeliveredV1;
  "campsverso.perception.updated.v1": T.PerceptionUpdatedV1;
  "campsverso.rules.effect_applied.v1": T.RulesEffectAppliedV1;
  "campsverso.rules.loaded.v1": T.RulesLoadedV1;
  "campsverso.rules.toggled.v1": T.RulesToggledV1;
  "campsverso.world.clock.jumped.v1": T.WorldClockJumpedV1;
  "campsverso.world.clock.mode_changed.v1": T.WorldClockModeChangedV1;
  "campsverso.world.clock.paused.v1": T.WorldClockPausedV1;
  "campsverso.world.clock.phase_changed.v1": T.WorldClockPhaseChangedV1;
  "campsverso.world.clock.resumed.v1": T.WorldClockResumedV1;
  "campsverso.world.clock.scale_changed.v1": T.WorldClockScaleChangedV1;
  "campsverso.world.clock.stepped.v1": T.WorldClockSteppedV1;
  "campsverso.world.command.rejected.v1": T.WorldCommandRejectedV1;
  "campsverso.world.entity.move_interrupted.v1": T.WorldEntityMoveInterruptedV1;
  "campsverso.world.entity.moved.v1": T.WorldEntityMovedV1;
  "campsverso.world.entity.spawned.v1": T.WorldEntitySpawnedV1;
  "campsverso.world.entity.state_changed.v1": T.WorldEntityStateChangedV1;
  "campsverso.world.entity.stored.v1": T.WorldEntityStoredV1;
  "campsverso.world.item.consumed.v1": T.WorldItemConsumedV1;
  "campsverso.world.item.created.v1": T.WorldItemCreatedV1;
  "campsverso.world.item.transferred.v1": T.WorldItemTransferredV1;
  "campsverso.world.need.changed.v1": T.WorldNeedChangedV1;
  "campsverso.world.need.threshold_crossed.v1": T.WorldNeedThresholdCrossedV1;
  "campsverso.world.session.started.v1": T.WorldSessionStartedV1;
  "campsverso.world.snapshot.created.v1": T.WorldSnapshotCreatedV1;
  "campsverso.world.weather.changed.v1": T.WorldWeatherChangedV1;
}

/** Envelope com o payload tipado pelo tipo do evento ou comando (união discriminada por `type`). */
export type Envelope<K extends ContractTypeName = ContractTypeName> = {
  [P in K]: Omit<T.EnvelopeV1, "type" | "data"> & { readonly type: P; readonly data: PayloadByType[P] };
}[K];

/** Assunto NATS de um tipo de evento ou comando (catálogo §1.1). */
export function subject(type: ContractTypeName, worldid: string, avatarId?: string): string {
  const info: ContractTypeInfo = CONTRACT_TYPES[type];
  const name = type.slice("campsverso.".length);
  if (info.kind === "command") {
    return `campsverso.${worldid}.${name}`;
  }
  if (info.visibility === "agent") {
    if (avatarId === undefined) {
      throw new Error(`${type} tem visibilidade agent e exige avatarId`);
    }
    return `campsverso.${worldid}.agent.${avatarId}.${name}`;
  }
  return `campsverso.${worldid}.${info.visibility}.${name}`;
}
