/** A oficina do dev na sala (ADR-0080): o monitor da mesa pelo último passo, o robô pela última
 * chamada e a bancada com o osciloscópio ligado enquanto um robô trabalha.
 *
 * O estado vem dos fatos da oficina, projetados pelo gateway (`state.workshop`). Aqui só se decide
 * o desenho: qual estado cada coisa mostra agora, e o quadro dele no manifesto (`WorkshopArt`).
 * Nada disso é regra do mundo.
 */
import type { ObserverState } from "@campsverso/contracts";

import { loopFrame, type WorkshopArt } from "./art/manifest.ts";
import { tickSeconds } from "./simclock.ts";

/** Um passo vale no monitor até 2 horas do mundo: a 72×, uma chamada lenta ao modelo passa de meia
 * hora entre dois passos; depois disso, a sessão acabou sem o `pronto` (o orçamento, uma queda). */
export const STEP_SECONDS = 2 * 3600;
/** O robô mostra o resultado por 15 minutos do mundo e volta ao parado. */
export const RESULT_SECONDS = 15 * 60;
/** Um robô roda no máximo 60 s; "trabalhando" por mais de 2 horas do mundo é um que caiu. */
const WORKING_SECONDS = 2 * 3600;

const READING = new Set(["ver_arquivos", "ler", "buscar", "ver_mudancas"]);
const WRITING = new Set(["escrever", "editar"]);

/** O que o monitor mostra por um passo: lendo, escrevendo, os testes verdes ou vermelhos; o
 * `pronto` (e o que não se conhece) não muda o monitor. */
export function stepLook(tool: string, ok: boolean): string | undefined {
  if (READING.has(tool)) {
    return "lendo";
  }
  if (WRITING.has(tool)) {
    return "escrevendo";
  }
  if (tool === "rodar_testes") {
    return ok ? "verde" : "vermelho";
  }
  return undefined;
}

const ROBOT_LOOK: Readonly<Record<string, string>> = { working: "trabalhando", passed: "passou", failed: "falhou" };

function age(state: ObserverState, tick: number, since: number): number {
  return Math.max(0, tick - since) * tickSeconds(state.session);
}

/** O estado da oficina de uma coisa agora, pelo `of` do manifesto; `users` são os avatares que a
 * usam (ao lado dela, fazendo alguma ação). */
export function workshopState(
  art: WorkshopArt | undefined,
  id: string,
  attributes: Readonly<Record<string, unknown>>,
  state: ObserverState,
  tick: number,
  users: readonly string[],
): string | undefined {
  const workshop = state.workshop;
  if (art === undefined || workshop === undefined) {
    return undefined;
  }
  if (art.of === "owner") {
    const owner = attributes.dono;
    const step = typeof owner === "string" && users.includes(owner) ? workshop.steps?.[owner] : undefined;
    return step === undefined || age(state, tick, step.tick) > STEP_SECONDS ? undefined : stepLook(step.tool, step.ok);
  }
  const robots = Object.entries(workshop.robots ?? {});
  if (art.of === "any") {
    const working = robots.some(([, r]) => r?.state === "working" && age(state, tick, r.tick) <= WORKING_SECONDS);
    return working ? "trabalhando" : undefined;
  }
  const robot = workshop.robots?.[id];
  if (robot === undefined) {
    return undefined;
  }
  const limit = robot.state === "working" ? WORKING_SECONDS : RESULT_SECONDS;
  return age(state, tick, robot.tick) > limit ? undefined : ROBOT_LOOK[robot.state];
}

/** O quadro do estado da oficina, ou nenhum (fica o de sempre). */
export function workshopFrame(art: WorkshopArt | undefined, look: string | undefined, seconds: number): number | undefined {
  return look === undefined ? undefined : loopFrame(art?.frames[look], seconds);
}
