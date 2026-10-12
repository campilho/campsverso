/** O relógio que a tela mostra entre um evento e outro (ADR-0050).
 *
 * Tick quieto não gera evento: o estado traz o tick do último evento. No modo contínuo, sem pausa,
 * a tela estima o tick pela escala e pelo tempo real desde que o estado chegou. A estimativa nunca
 * passa de `MAX_AHEAD` ticks, para não correr sozinha se o kernel parar.
 */
import type { ObserverState } from "@campsverso/contracts";

export const MAX_AHEAD = 120;

export function estimateTick(state: ObserverState, receivedAtMs: number, nowMs: number): number {
  const { clock, session } = state;
  if (session === undefined || clock.paused !== false || clock.mode !== "continuous" || clock.scale === undefined) {
    return state.tick;
  }
  const elapsed = Math.max(0, nowMs - receivedAtMs) / 1000;
  const ahead = Math.min(MAX_AHEAD, (elapsed * clock.scale) / session.tick_seconds);
  return state.tick + ahead;
}

/** Fuso da hora simulada, em minutos (`-03:00` vira -180; `Z`, 0). */
function offsetMinutes(simTime: string): number {
  const match = /([+-])(\d{2}):(\d{2})$/.exec(simTime);
  if (match === null) {
    return 0;
  }
  const minutes = Number(match[2]) * 60 + Number(match[3]);
  return match[1] === "-" ? -minutes : minutes;
}

/** Hora simulada (HH:MM) no tick dado, a partir da hora do último evento (`sim_time`). */
export function clockText(state: ObserverState, tick: number): string {
  const base = state.sim_time === undefined ? Number.NaN : Date.parse(state.sim_time);
  if (state.sim_time === undefined || state.session === undefined || Number.isNaN(base)) {
    return "--:--";
  }
  const elapsed = (Math.floor(tick) - state.tick) * state.session.tick_seconds * 1000;
  const local = base + elapsed + offsetMinutes(state.sim_time) * 60_000;
  return new Date(local).toISOString().slice(11, 16);
}
