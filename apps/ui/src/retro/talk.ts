/** A conversa da tela retrô (docs/design/briefing-tela.md, §3.5), em funções puras: as falas e as
 * linhas do sistema a partir da linha do tempo, quem está na conversa, as menções com `@` e as
 * sugestões. A menção só escolhe o `to` do `say`; quem decide se a fala vale é o kernel. */
import type { EnvelopeV1, EventLabel, ObserverState } from "@campsverso/contracts";

import { choiceName } from "../locale.ts";
import { ticketsOf } from "../panels/office.ts";
import { clockText } from "../simclock.ts";
import { describe } from "../timeline.ts";
import { handsName } from "../workshop.ts";

const SPOKE = "campsverso.avatar.spoke.v1";
const ROBOT_CALLED = "campsverso.workshop.robot_called.v1";
// Os marcos da sessão do dev na oficina (ADR-0089): o começo, os testes e o fim, e não cada passo.
const STEP = "campsverso.workshop.step.v2";
const FINISHED = "campsverso.workshop.session_finished.v1";
const TESTS = /pytest|\btests?\b/i;
// Os fatos que viram uma linha do sistema na conversa: o quadro, o PR, a convocação e os robôs.
// Os fatos do quadro, da convocação e da luz, em qualquer versão: o `ticket.returned.v2` (ADR-0092)
// entra como o v1 dos dias antigos.
const SYSTEM = /^campsverso\.office\.(ticket|staff|light)\.[a-z_]+\.v\d+$/;
const LIGHT = "campsverso.office.light.switched.v1";

/** Quem está na conversa: os avatares na sala, menos quem joga. */
export interface Person {
  readonly id: string;
  readonly name: string;
  readonly role: string;
  /** LLM, script ou você. */
  readonly controller: string;
}

const ROLE_ORDER = ["dev", "vigia", "gerente"];


const STAFF = /^campsverso\.office\.staff\.[a-z_]+\.v\d+$/;

/** A convocação com o nome do dev (ADR-0093: com dois devs, "o dev" não diz qual): "dispensou o
 * Kenji"; e a dispensa pelo próprio dev, que foi para casa depois de combinar na conversa. */
function staffLine(state: ObserverState, event: EnvelopeV1, text: string | undefined): string | undefined {
  if (text === undefined || !STAFF.test(event.type)) {
    return text;
  }
  const data = event.data as { avatar_id?: unknown; by?: unknown };
  const dev = typeof data.avatar_id === "string" ? nameOf(state, data.avatar_id) : undefined;
  if (dev === undefined) {
    return text;
  }
  if (event.type.endsWith(".dismissed.v1") && data.by === data.avatar_id) {
    return "foi para casa";
  }
  return text.replace(/\bdo dev\b/g, `do ${dev}`).replace(/\bo dev\b/g, `o ${dev}`);
}
export function peopleOf(state: ObserverState, me: string): Person[] {
  return Object.entries(state.entities)
    .filter(([id, e]) => id !== me && e?.kind === "avatar" && e.position !== undefined)
    .map(([id, e]) => {
      const papel = e?.attributes.papel;
      const type = state.controllers[id]?.type;
      return {
        id,
        name: e?.display_name ?? id.charAt(0).toUpperCase() + id.slice(1),
        role: typeof papel === "string" ? papel : "",
        controller: type === "llm" ? "LLM" : type === "human" ? "humano" : "script",
      };
    })
    .sort((a, b) => rank(a.role) - rank(b.role) || (a.id < b.id ? -1 : 1));
}

function rank(role: string): number {
  const i = ROLE_ORDER.indexOf(role);
  return i === -1 ? ROLE_ORDER.length : i;
}

/** O nome na frase: o dev pelo nome ("o Camps"), os outros pelo papel ("o vigia"). */
function inLine(person: Person): string {
  return `o ${person.role === "dev" || person.role === "" ? person.name : person.name.toLowerCase()}`;
}

/** "o Camps e o vigia", "o Camps", ou ninguém. */
export function peopleLine(people: readonly Person[]): string {
  const names = people.map(inLine);
  if (names.length === 0) {
    return "ninguém na sala";
  }
  const last = names.pop() ?? "";
  return names.length === 0 ? last : `${names.join(", ")} e ${last}`;
}

/** O papel e o controle na sugestão: "o dev · LLM". */
export function personTag(person: Person): string {
  return `${person.role === "" ? "na sala" : `o ${person.role}`} · ${person.controller}`;
}

const MENTION = /@([\p{L}\p{N}_-]+)/gu;

function same(a: string, b: string): boolean {
  return a.localeCompare(b, "pt-BR", { sensitivity: "base" }) === 0;
}

/** A primeira menção de quem está na conversa vira o `to` da fala; quem joga não está na lista. */
export function mentionTarget(text: string, people: readonly Person[]): string | undefined {
  for (const match of text.matchAll(MENTION)) {
    const word = match[1] ?? "";
    const found = people.find((p) => same(p.name, word) || same(p.id, word));
    if (found !== undefined) {
      return found.id;
    }
  }
  return undefined;
}

/** O pedaço depois do `@` que se está escrevendo agora, no fim do texto; sem `@` no fim, nada. */
export function mentionQuery(text: string): string | undefined {
  const match = /(?:^|\s)@([\p{L}\p{N}_-]*)$/u.exec(text);
  return match?.[1];
}

function fold(text: string): string {
  return text.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

/** As sugestões: quem está na conversa, pelo começo do nome. */
export function suggestionsOf(query: string, people: readonly Person[]): Person[] {
  const want = fold(query);
  return people.filter((p) => fold(p.name).startsWith(want) || fold(p.id).startsWith(want));
}

/** Troca o `@pedaço` do fim pela menção inteira, com um espaço depois. */
export function completeMention(text: string, person: Person): string {
  return text.replace(/@([\p{L}\p{N}_-]*)$/u, `@${person.name} `);
}

/** O texto em pedaços, com as menções separadas, para a fala as mostrar como pílulas. */
export function splitMentions(text: string): { readonly text: string; readonly mention: boolean }[] {
  const parts: { text: string; mention: boolean }[] = [];
  let at = 0;
  for (const match of text.matchAll(MENTION)) {
    const start = match.index;
    if (start > at) {
      parts.push({ text: text.slice(at, start), mention: false });
    }
    parts.push({ text: match[0], mention: true });
    at = start + match[0].length;
  }
  if (at < text.length) {
    parts.push({ text: text.slice(at), mention: false });
  }
  return parts;
}

/** Uma linha do registro: uma fala, ou um fato do quadro, do PR ou da bancada. */
export type TalkLine =
  | { readonly kind: "speech"; readonly id: string; readonly who: string; readonly name: string; readonly text: string; readonly mine: boolean; readonly time: string }
  | { readonly kind: "system"; readonly id: string; readonly text: string; readonly time: string };

function nameOf(state: ObserverState, id: unknown): string | undefined {
  if (typeof id !== "string") {
    return undefined;
  }
  return state.entities[id]?.display_name ?? id.charAt(0).toUpperCase() + id.slice(1);
}

/** O robô pelo nome em minúsculas: "o testador". */
function robotName(state: ObserverState, id: unknown): string {
  const name = nameOf(state, id) ?? "robô";
  return `o ${name.toLowerCase()}`;
}

/** O número do pedido pela ficha, ou pelo id ("pedido-002" é o 2). */
function ticketNumber(state: ObserverState, ticketId: unknown): string {
  const ticket = ticketsOf(state).find((t) => t.id === ticketId);
  if (ticket !== undefined) {
    return String(ticket.number);
  }
  const digits = /(\d+)$/.exec(String(ticketId))?.[1];
  return digits === undefined ? String(ticketId) : String(Number(digits));
}

/** Os passos que abrem uma sessão: o primeiro de um pedido, para cada dev, na ordem dos fatos. */
function sessionStarts(timeline: readonly EnvelopeV1[]): Set<string> {
  const open = new Map<string, unknown>();
  const starts = new Set<string>();
  for (const event of timeline) {
    const data = event.data as Record<string, unknown>;
    if (typeof data.avatar_id !== "string") {
      continue;
    }
    if (event.type === STEP && open.get(data.avatar_id) !== data.ticket_id) {
      starts.add(event.id);
      open.set(data.avatar_id, data.ticket_id);
    } else if (event.type === FINISHED) {
      open.delete(data.avatar_id);
    }
  }
  return starts;
}

function money(value: unknown): string | undefined {
  return typeof value === "number" ? `US$ ${value.toFixed(2).replace(".", ",")}` : undefined;
}

/** A linha de um passo que vira marco: o primeiro da sessão e os testes; os outros, nenhuma. */
function stepLine(state: ObserverState, data: Record<string, unknown>, first: boolean): string | undefined {
  const who = nameOf(state, data.avatar_id) ?? "O dev";
  if (first) {
    const hands = handsName(typeof data.harness === "string" ? data.harness : undefined, (id) => choiceName("hands", id));
    const model = typeof data.model === "string" ? ` (${choiceName("models", data.model)})` : "";
    return `${who} começou a programar o pedido ${ticketNumber(state, data.ticket_id)}: ${hands}${model}`;
  }
  const summary = typeof data.summary === "string" ? data.summary : "";
  if (data.tool === "rodar_testes") {
    return `${who} rodou os testes: ${summary.split(": ").slice(1).join(": ") || (data.ok === true ? "passaram" : "falharam")}`;
  }
  if (data.tool === "Bash" && TESTS.test(summary)) {
    return `${who} rodou os testes: ${data.ok === true ? "passaram" : "falharam"}`;
  }
  return undefined;
}

/** O fim da sessão: o motivo, as voltas, o custo e o tempo. */
function finishedLine(state: ObserverState, data: Record<string, unknown>): string {
  const who = nameOf(state, data.avatar_id) ?? "O dev";
  const parts = [String(data.reason), `${String(data.turns)} voltas`];
  const cost = money(data.cost_usd);
  if (cost !== undefined) {
    parts.push(cost);
  }
  if (typeof data.duration_ms === "number") {
    parts.push(`${(data.duration_ms / 60000).toFixed(1).replace(".", ",")} min`);
  }
  return `${who} terminou a sessão do pedido ${ticketNumber(state, data.ticket_id)}: ${parts.join(", ")}`;
}

/** As últimas `limit` linhas da conversa, da mais antiga para a mais nova. */
export function linesOf(
  timeline: readonly EnvelopeV1[],
  state: ObserverState,
  me: string,
  labels: readonly EventLabel[],
  limit = 80,
): TalkLine[] {
  const lines: TalkLine[] = [];
  const starts = sessionStarts(timeline);
  for (let i = timeline.length - 1; i >= 0 && lines.length < limit; i--) {
    const event = timeline[i];
    if (event === undefined) {
      continue;
    }
    const data = event.data as Record<string, unknown>;
    const time = typeof event.tick === "number" ? clockText(state, event.tick).slice(0, 5) : "";
    if (event.type === SPOKE && typeof data.avatar_id === "string" && typeof data.text === "string") {
      lines.push({
        kind: "speech",
        id: event.id,
        who: data.avatar_id,
        name: nameOf(state, data.avatar_id) ?? data.avatar_id,
        text: data.text,
        mine: data.avatar_id === me,
        time,
      });
    } else if (event.type === STEP) {
      const text = stepLine(state, data, starts.has(event.id));
      if (text !== undefined) {
        lines.push({ kind: "system", id: event.id, text, time });
      }
    } else if (event.type === FINISHED) {
      lines.push({ kind: "system", id: event.id, text: finishedLine(state, data), time });
    } else if (event.type === ROBOT_CALLED) {
      // "chamando o robô ...: saída 0" não diz nada a quem lê; o resumo do testador, sim.
      const said = typeof data.summary === "string" && !data.summary.startsWith("chamando o robô") ? data.summary : "";
      const summary = said !== "" ? `: ${said}` : "";
      lines.push({ kind: "system", id: event.id, text: `${robotName(state, data.robot_id)} ${data.ok === true ? "passou" : "falhou"}${summary}`, time });
    } else if (SYSTEM.test(event.type)) {
      const text = staffLine(state, event, describe(event, labels));
      if (text !== undefined) {
        // A luz que o temporizador do prédio acende ou apaga não tem quem (ADR-0088).
        const actor = nameOf(state, data.by ?? data.author) ?? (event.type === LIGHT ? "O temporizador" : undefined);
        lines.push({ kind: "system", id: event.id, text: actor === undefined ? text : `${actor} ${text}`, time });
      }
    }
  }
  return lines.reverse();
}
