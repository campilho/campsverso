/** O relógio que a tela mostra entre um evento e outro (ADR-0050).
 *
 * Tick quieto não gera evento: o estado traz o tick do último evento. No modo contínuo, sem pausa,
 * a tela estima o tick pela escala e pelo tempo real desde a última âncora (o último evento). Mas
 * o evento chega uns 100 ms depois de acontecer, e o kernel não anda exatamente na escala; corrigir
 * de uma vez faria o relógio voltar ou travar. Por isso:
 *
 * - **Nunca volta, e corrige devagar.** A tela anda no ritmo da escala e desfaz a diferença para a
 *   estimativa em cerca de um segundo: um pouco mais devagar quando está adiantada, um pouco mais
 *   depressa quando está atrasada. Muito atrasada (um passo com a pausa, por exemplo), ela pula.
 * - **Mudou o ritmo, a âncora vem para onde a tela está**, e a escala nova vale daí em diante.
 * - **Sem conexão, na pausa ou no modo máximo, não anda sozinha.** E nunca passa de `MAX_AHEAD`
 *   ticks além do último evento, caso o kernel pare.
 */
import type { ObserverState } from "@campsverso/contracts";

export const MAX_AHEAD = 120;
/** Ticks de atraso a partir dos quais a tela pula em vez de acelerar. */
export const CATCH_UP = 5;
/** Em quanto tempo real a tela desfaz a maior parte de uma diferença (constante de tempo). */
const SMOOTH_MS = 1000;

/** Ticks por milissegundo real; zero quando o relógio do mundo não anda sozinho. */
function rate(state: ObserverState): number {
  const { clock, session } = state;
  if (session === undefined || clock.paused !== false || clock.mode !== "continuous" || clock.scale === undefined) {
    return 0;
  }
  return clock.scale / session.tick_seconds / 1000;
}

function settings(state: ObserverState): string {
  return JSON.stringify([state.clock.mode, state.clock.scale, state.clock.paused]);
}

export class DisplayClock {
  private shown = 0;
  private frameAt = 0;
  private anchorTick = 0;
  private anchorAt = 0;
  private stateTick = 0;
  private settings = "";

  /** Um welcome: começa de novo, inclusive para trás (pode ser outra sessão do mundo). */
  reset(state: ObserverState, nowMs: number): void {
    this.shown = this.anchorTick = this.stateTick = state.tick;
    this.anchorAt = this.frameAt = nowMs;
    this.settings = settings(state);
  }

  /** O estado mudou: um tick novo ancora nele; um relógio novo ancora onde a tela está. */
  observe(state: ObserverState, nowMs: number): void {
    const current = settings(state);
    if (current !== this.settings) {
      this.anchorTick = Math.max(this.shown, state.tick);
      this.anchorAt = nowMs;
      this.settings = current;
    } else if (state.tick !== this.stateTick) {
      this.anchorTick = state.tick;
      this.anchorAt = nowMs;
    }
    this.stateTick = state.tick;
  }

  /** O tick a mostrar agora (fracionário, para interpolar trajetos); chamado a cada quadro. */
  at(state: ObserverState, nowMs: number, live: boolean): number {
    const elapsed = Math.max(0, nowMs - this.frameAt);
    this.frameAt = nowMs;
    const r = live ? rate(state) : 0;
    if (r > 0) {
      const target = this.anchorTick + Math.min(MAX_AHEAD, Math.max(0, nowMs - this.anchorAt) * r);
      const step = elapsed * r; // o que a tela andaria neste quadro no ritmo da escala
      const behind = target - (this.shown + step); // em ticks; negativo: a tela está adiantada
      if (behind > CATCH_UP) {
        this.shown = target;
      } else {
        // Corrige uma fração da diferença que depende só do tempo, não da taxa de quadros: estável
        // a 60 quadros por segundo e também numa aba em segundo plano, com um quadro por segundo.
        // Adiantada, a tela no máximo para; nunca volta.
        const share = 1 - Math.exp(-elapsed / SMOOTH_MS);
        const shown = this.shown + step + Math.max(-step, behind * share);
        this.shown = Math.min(shown, this.anchorTick + MAX_AHEAD);
      }
    }
    this.shown = Math.max(this.shown, state.tick);
    return this.shown;
  }
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
