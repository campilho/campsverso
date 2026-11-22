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
/** As mãos e o modelo do dev que programa agora (ADR-0089), pelo último passo dele, enquanto o
 * passo vale; um passo do v1 não traz as mãos. */
export function handsNow(state: ObserverState, avatarId: string, tick: number): { readonly harness: string; readonly model: string | undefined } | undefined {
  const step = state.workshop?.steps?.[avatarId];
  if (step?.harness === undefined || age(state, tick, step.tick) > STEP_SECONDS) {
    return undefined;
  }
  return { harness: step.harness, model: step.model };
}

/** O robô mostra o resultado por 15 minutos do mundo e volta ao parado. */
export const RESULT_SECONDS = 15 * 60;
/** Um robô roda no máximo 60 s; "trabalhando" por mais de 2 horas do mundo é um que caiu. */
const WORKING_SECONDS = 2 * 3600;

// As do nosso harness e as do Claude Code (o workshop.step.v2, ADR-0089). O `Bash` não muda o
// monitor: pode ser ler, escrever ou testar.
const READING = new Set(["ver_arquivos", "ler", "buscar", "ver_mudancas", "Read", "Glob", "Grep"]);
const WRITING = new Set(["escrever", "editar", "Write", "Edit", "NotebookEdit"]);

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

// ---------------------------------------------------------------- acompanhar o dev (ADR-0089)

type Session = NonNullable<NonNullable<NonNullable<ObserverState["workshop"]>["sessions"]>[string]>;
type SessionStep = Session["steps"][number];

/** A sessão na oficina de um dev, em curso ou a última, como a projeção a guarda. */
export function sessionOf(state: ObserverState, avatarId: string): Session | undefined {
  return state.workshop?.sessions?.[avatarId];
}

/** O estado do pedido da sessão, pela ficha ("fazendo", "entregue"...), se a visão a traz. */
export function sessionTicketState(state: ObserverState, session: Session): string | undefined {
  const estado = state.entities[session.ticket_id]?.attributes.estado;
  return typeof estado === "string" ? estado : undefined;
}

/** A sessão em curso: sem o fim, com o pedido ainda em "fazendo" (a sessão fixa da rotina não
 * publica o fim) e com o último passo valendo (2 horas do mundo, como o monitor). */
export function activeSession(state: ObserverState, avatarId: string, tick: number): Session | undefined {
  const session = sessionOf(state, avatarId);
  if (session === undefined || session.finished !== undefined) {
    return undefined;
  }
  const estado = sessionTicketState(state, session);
  if (estado !== undefined && estado !== "fazendo") {
    return undefined;
  }
  const last = session.steps.at(-1)?.tick ?? session.started_tick;
  return age(state, tick, last) > STEP_SECONDS ? undefined : session;
}

/** O nome das mãos para quem lê: o do locale da prancheta; a sessão fixa da reserva, "rotina". */
export function handsName(harness: string | undefined, name: (id: string) => string): string {
  if (harness === undefined) {
    return "oficina";
  }
  return harness === "script" ? "rotina" : name(harness);
}

function basename(path: string): string {
  return path.split("/").at(-1) ?? path;
}

/** Um passo numa linha curta: a ferramenta e o arquivo, ou o que ele fez, até `limit` letras. */
export function stepShort(step: SessionStep, limit = 48): string {
  const tool = step.tool;
  const text = step.path !== undefined ? `${tool} ${basename(step.path)}` : step.summary.startsWith(`${tool}:`) ? step.summary : `${tool}: ${step.summary}`;
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
}

/** A linha sobre o dev que programa: "passo 23 · Edit hands_codex.py". */
export function sessionLine(state: ObserverState, avatarId: string, tick: number): string | undefined {
  const session = activeSession(state, avatarId, tick);
  const last = session?.steps.at(-1);
  if (session === undefined || last === undefined) {
    return undefined;
  }
  return `passo ${String(session.count)} · ${stepShort(last, 36)}`;
}
