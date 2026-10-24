/** A fila de ações do humano, na tela (ADR-0068). O kernel não muda: ele recebe uma proposta por
 * vez, e a tela manda a próxima quando a anterior termina.
 *
 * - Um passo com alvo longe do avatar ganha antes um `move {near}` até o lado dele.
 * - Uma recusa, ou uma ação que falha, esvazia a fila; quem joga é avisado.
 * - O shift com o clique enfileira; sem o shift, o passo novo substitui a fila. O Esc a esvazia.
 */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

import { approach, type Proposal, type Tile } from "./play.ts";

export interface Step {
  /** O que a fila mostra: "Plantar (milho) · plot-003". */
  readonly label: string;
  readonly proposal: Proposal;
  /** O alvo de que o avatar precisa estar ao lado; vazio quando não há (andar, comer, dormir). */
  readonly near?: string | Tile;
}

const SETTLED = new Set(["campsverso.action.completed.v1", "campsverso.action.rejected.v1", "campsverso.action.failed.v1"]);
const BROKEN = new Set(["campsverso.action.rejected.v1", "campsverso.action.failed.v1"]);

/** O avatar está livre para a próxima ação: nada em andamento e acordado. */
export function idle(state: ObserverState, avatarId: string): boolean {
  return state.actions[avatarId] === undefined && state.asleep[avatarId] !== true;
}

export class ActionQueue {
  private steps: Step[] = [];
  private inFlight = false;
  private walked = false;
  /** Muda a cada mudança da fila, para a tela redesenhar só quando precisa. */
  version = 0;

  get list(): readonly Step[] {
    return this.steps;
  }

  push(step: Step): void {
    this.steps.push(step);
    this.version++;
  }

  /** Esvazia a fila; devolve verdadeiro se havia o que esvaziar. */
  clear(): boolean {
    const had = this.steps.length > 0;
    this.steps = [];
    this.inFlight = false;
    this.walked = false;
    this.version++;
    return had;
  }

  /** A próxima proposta a mandar, ou nada: com uma em voo, a fila vazia ou o avatar ocupado. */
  next(state: ObserverState, avatarId: string): Proposal | undefined {
    const step = this.steps[0];
    if (this.inFlight || step === undefined || !idle(state, avatarId)) {
      return undefined;
    }
    this.inFlight = true;
    const walk = this.walked ? undefined : approach(state, avatarId, step.near);
    if (walk !== undefined) {
      this.walked = true; // depois de andar, a ação vai de qualquer jeito: o kernel decide
      return walk;
    }
    this.steps.shift();
    this.walked = false;
    this.version++;
    return step.proposal;
  }

  /** Os fatos do avatar que destravam a fila; devolve a mensagem quando uma recusa a esvaziou. */
  settle(event: EnvelopeV1, avatarId: string): string | undefined {
    const data = event.data as Record<string, unknown>;
    if (!SETTLED.has(event.type) || data.avatar_id !== avatarId) {
      return undefined;
    }
    const was = this.inFlight;
    this.inFlight = false;
    if (BROKEN.has(event.type) && was && this.clear()) {
      return "A fila foi esvaziada.";
    }
    return undefined;
  }
}
