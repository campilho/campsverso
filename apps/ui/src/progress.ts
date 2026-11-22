/** A barra de progresso sobre o avatar e o "ocupado" da recusa `busy` (ADR-0052).
 *
 * Tudo sai do estado: o início e o fim previsto da ação, ou do sono. A tela só mostra; quem recusa
 * um comando durante uma ação é o kernel.
 */
import type { ObserverState } from "@campsverso/contracts";

import { actionName } from "./locale.ts";
import { clockText, tickSeconds } from "./simclock.ts";
import { sessionLine } from "./workshop.ts";

export interface Progress {
  readonly label: string;
  /** De 0 a 1; ausente quando o estado não diz quando começou (arquivos antigos). */
  readonly fraction?: number;
}

function fraction(start: number, end: number, tick: number): number {
  return end <= start ? 1 : Math.min(1, Math.max(0, (tick - start) / (end - start)));
}

/** As ações do próprio kernel (ADR-0038), que nenhum cartucho põe no catálogo. */
const KERNEL_LABELS: Readonly<Record<string, string>> = { move: "Andando", wait: "Esperando", say: "Falando" };

/** O que o avatar está fazendo: o nome da ação no arquivo da língua, quando o cartucho o dá
 * ("Jogando videogame", no escritório; ADR-0078), o rótulo do catálogo ("Plantar", na fazenda, que
 * não tem a seção), ou o nome dela. O arquivo da língua vem antes porque o rótulo do catálogo é o
 * que o menu oferece ("Jogar videogame"), e não o que se faz (ADR-0082). */
export function actionLabel(state: ObserverState, action: string): string {
  return (
    actionName(action) ??
    state.session?.affordances?.find((a) => a.action === action)?.label ??
    KERNEL_LABELS[action] ??
    action
  );
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

/** As ações que a tela não anuncia sobre a cabeça (18/nov): andar, que o desenho já mostra; esperar,
 * que não tem o que mostrar; e falar, que tem o balão da fala. O retrato do HUD continua dizendo. */
const QUIET: ReadonlySet<string> = new Set(["move", "wait", "say"]);

/** O que vai sobre a cabeça do avatar: o progresso da ação, menos o das ações óbvias. O sono aparece.
 * O dev na mesa com uma sessão na oficina mostra o último passo, e não a barra do bloco de
 * trabalho, que enche e recomeça (ADR-0089). */
export function overHead(state: ObserverState, avatarId: string, tick: number): Progress | undefined {
  const action = state.actions[avatarId];
  if (action !== undefined && (action.action === "work" || action.action === "wait")) {
    const line = sessionLine(state, avatarId, tick);
    if (line !== undefined) {
      return { label: line };
    }
  }
  if (state.asleep[avatarId] !== true && action !== undefined && QUIET.has(action.action)) {
    return undefined;
  }
  return progressOf(state, avatarId, tick);
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
  const seconds = Math.max(0, action.end_tick - tick) * tickSeconds(state.session);
  const minutes = Math.max(1, Math.ceil(seconds / 60));
  return `${name} está ocupado: ${actionLabel(state, action.action).toLowerCase()}, faltam ${String(minutes)} min.`;
}
