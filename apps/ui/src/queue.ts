/** A fila de ações do humano, na tela (ADR-0068). O kernel não muda: ele recebe uma proposta por
 * vez, e a tela manda a próxima quando a anterior termina.
 *
 * - Um passo com alvo longe do avatar ganha antes um `move {near}` até o lado dele; com um assento
 *   virado para o alvo, um `move {target}` até o assento (ADR-0082).
 * - Uma recusa, ou uma ação que falha, esvazia a fila; quem joga é avisado.
 * - O shift com o clique enfileira; sem o shift, o passo novo substitui a fila, e a tela avisa
 *   quantos passos foram trocados (ADR-0092). O Esc a esvazia.
 * - Um passo do quadro (escrever, aceitar ou devolver uma ficha) não espera o lazer acabar: ele
 *   interrompe a TV e o videogame no sofá, que o kernel cancela (`interrupt: cancel`; ADR-0092).
 */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

import { approach, type Proposal, type Tile } from "./play.ts";

export interface Step {
  /** O que a fila mostra: "Plantar (milho) · plot-003". */
  readonly label: string;
  readonly proposal: Proposal;
  /** O alvo de que o avatar precisa estar ao lado; vazio quando não há (andar, comer, dormir). */
  readonly near?: string | Tile;
  /** O assento virado para o alvo, onde sentar antes da ação, no lugar do lado qualquer do `near`
   * (a cadeira da mesinha da copa; ADR-0082). */
  readonly seat?: Tile;
}

const SETTLED = new Set(["campsverso.action.completed.v1", "campsverso.action.rejected.v1", "campsverso.action.failed.v1"]);
const BROKEN = new Set(["campsverso.action.rejected.v1", "campsverso.action.failed.v1"]);

/** O avatar está livre para a próxima ação: nada em andamento e acordado. */
export function idle(state: ObserverState, avatarId: string): boolean {
  return state.actions[avatarId] === undefined && state.asleep[avatarId] !== true;
}

/** O lazer no sofá, que o kernel cancela quando chega outra ação (`interrupt: cancel`). */
export const LEISURE: readonly string[] = ["tv", "videogame"];
/** Os passos do quadro, que não esperam o lazer acabar: escrever, pegar, aceitar ou devolver uma
 * ficha (o plano das telas, fase 6). */
export const BOARD_STEPS: readonly string[] = ["write_ticket", "take_ticket", "accept_ticket", "return_ticket"];

/** O avatar pode começar o passo: livre, ou no lazer que um passo do quadro interrompe. */
export function readyFor(step: Step, state: ObserverState, avatarId: string): boolean {
  if (idle(state, avatarId)) {
    return true;
  }
  const doing = state.actions[avatarId]?.action;
  return state.asleep[avatarId] !== true && doing !== undefined && LEISURE.includes(doing) && BOARD_STEPS.includes(step.proposal.action);
}

/** O aviso de quando um clique troca a fila: "a fila de 3 passos foi trocada". */
export function replacedText(count: number): string {
  return `a fila de ${String(count)} ${count === 1 ? "passo" : "passos"} foi trocada`;
}

export class ActionQueue {
  private steps: Step[] = [];
  private inFlight = false;
  /** A ação da proposta em voo: o cancelamento de outra (o lazer que ela interrompeu) não conta. */
  private flying: string | undefined;
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
    this.flying = undefined;
    this.walked = false;
    this.version++;
    return had;
  }

  /** A próxima proposta a mandar, ou nada: com uma em voo, a fila vazia ou o avatar ocupado. */
  next(state: ObserverState, avatarId: string): Proposal | undefined {
    const step = this.steps[0];
    if (this.inFlight || step === undefined || !readyFor(step, state, avatarId)) {
      return undefined;
    }
    this.inFlight = true;
    const walk = this.walked ? undefined : sitDown(state, avatarId, step.seat) ?? approach(state, avatarId, step.near);
    if (walk !== undefined) {
      this.walked = true; // depois de andar, a ação vai de qualquer jeito: o kernel decide
      this.flying = walk.action;
      return walk;
    }
    this.steps.shift();
    this.walked = false;
    this.flying = step.proposal.action;
    this.version++;
    return step.proposal;
  }

  /** Os fatos do avatar que destravam a fila; devolve a mensagem quando uma recusa a esvaziou. */
  settle(event: EnvelopeV1, avatarId: string): string | undefined {
    const data = event.data as Record<string, unknown>;
    if (!SETTLED.has(event.type) || data.avatar_id !== avatarId) {
      return undefined;
    }
    // O lazer que a proposta em voo interrompeu falha como "cancelled": não é a proposta da fila.
    if (event.type === "campsverso.action.failed.v1" && data.reason === "cancelled" && this.inFlight && data.action !== this.flying) {
      return undefined;
    }
    const was = this.inFlight;
    this.inFlight = false;
    this.flying = undefined;
    if (BROKEN.has(event.type) && was && this.clear()) {
      return "A fila foi esvaziada.";
    }
    return undefined;
  }
}

/** Os alvos (como os pedidos do quadro) de uma destas ações que já estão a caminho: na fila ou em
 * andamento. Um segundo clique no mesmo botão não entra, e o quadro mostra que o gerente está indo
 * (18/nov: dois cliques em aceitar saíam juntos, e o segundo era recusado). */
export function pendingTargets(
  steps: readonly Step[],
  state: ObserverState,
  avatarId: string,
  actions: readonly string[],
): Set<string> {
  const doing = state.actions[avatarId];
  const proposals = [
    ...steps.map((step) => step.proposal),
    ...(doing === undefined ? [] : [{ action: doing.action, params: doing.params as Record<string, unknown> }]),
  ];
  return new Set(
    proposals
      .filter((p) => actions.includes(p.action))
      .map((p) => p.params.target)
      .filter((target): target is string => typeof target === "string"),
  );
}

/** O passo até o assento, se o avatar não estiver nele. */
function sitDown(state: ObserverState, avatarId: string, seat: Tile | undefined): Proposal | undefined {
  const me = state.entities[avatarId]?.position;
  if (seat === undefined || me === undefined || (me.x === seat.x && me.y === seat.y)) {
    return undefined;
  }
  return { avatar_id: avatarId, action: "move", params: { target: { x: seat.x, y: seat.y } } };
}
