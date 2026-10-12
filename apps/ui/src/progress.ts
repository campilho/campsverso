/** A barra de progresso sobre o avatar e o "ocupado" da recusa `busy` (ADR-0052).
 *
 * Tudo sai do estado: o início e o fim previsto da ação, ou do sono. A tela só mostra; quem recusa
 * um comando durante uma ação é o kernel.
 */
import type { ObserverState } from "@campsverso/contracts";

import { clockText } from "./simclock.ts";

export interface Progress {
  readonly label: string;
  /** De 0 a 1; ausente quando o estado não diz quando começou (arquivos antigos). */
  readonly fraction?: number;
}

function fraction(start: number, end: number, tick: number): number {
  return end <= start ? 1 : Math.min(1, Math.max(0, (tick - start) / (end - start)));
}

/** O rótulo da ação no catálogo do cartucho ("Plantar"), ou o nome dela. */
export function actionLabel(state: ObserverState, action: string): string {
  return state.session?.affordances?.find((a) => a.action === action)?.label ?? action;
}

export function progressOf(state: ObserverState, avatarId: string, tick: number): Progress | undefined {
  if (state.asleep[avatarId] === true) {
    const sleep = state.sleep?.[avatarId];
    return sleep === undefined
      ? { label: "Zz" }
      : { label: "Zz", fraction: fraction(sleep.since_tick, sleep.wake_at_tick, tick) };
  }
  const action = state.actions[avatarId];
  if (action === undefined) {
    return undefined;
  }
  const label = actionLabel(state, action.action);
  return action.applied_tick === undefined ? { label } : { label, fraction: fraction(action.applied_tick, action.end_tick, tick) };
}

/** O texto da recusa `busy`: o que ocupa o avatar e quanto falta. */
export function busyText(state: ObserverState, avatarId: string, tick: number): string {
  const name = state.entities[avatarId]?.display_name ?? avatarId;
  const sleep = state.sleep?.[avatarId];
  if (state.asleep[avatarId] === true) {
    return sleep === undefined ? `${name} está dormindo.` : `${name} está dormindo; acorda às ${clockText(state, sleep.wake_at_tick)}.`;
  }
  const action = state.actions[avatarId];
  if (action === undefined) {
    return `${name} está ocupado.`;
  }
  const seconds = Math.max(0, action.end_tick - tick) * (state.session?.tick_seconds ?? 60);
  const minutes = Math.max(1, Math.ceil(seconds / 60));
  return `${name} está ocupado: ${actionLabel(state, action.action).toLowerCase()}, faltam ${String(minutes)} min.`;
}
