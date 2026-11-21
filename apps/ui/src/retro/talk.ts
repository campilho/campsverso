/** A conversa da tela retrô (docs/design/briefing-tela.md, §3.5), em funções puras: as falas e as
 * linhas do sistema a partir da linha do tempo, quem está na conversa, as menções com `@` e as
 * sugestões. A menção só escolhe o `to` do `say`; quem decide se a fala vale é o kernel. */
import type { EnvelopeV1, EventLabel, ObserverState } from "@campsverso/contracts";

import { clockText } from "../simclock.ts";
import { describe } from "../timeline.ts";

const SPOKE = "campsverso.avatar.spoke.v1";
const ROBOT_CALLED = "campsverso.workshop.robot_called.v1";
// Os fatos que viram uma linha do sistema na conversa: o quadro, o PR, a convocação e os robôs.
const SYSTEM = /^campsverso\.office\.(ticket|staff)\.[a-z_]+\.v1$/;

/** Quem está na conversa: os avatares na sala, menos quem joga. */
export interface Person {
  readonly id: string;
  readonly name: string;
  readonly role: string;
  /** LLM, script ou você. */
  readonly controller: string;
}

const ROLE_ORDER = ["dev", "vigia", "gerente"];

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

/** As últimas `limit` linhas da conversa, da mais antiga para a mais nova. */
export function linesOf(
  timeline: readonly EnvelopeV1[],
  state: ObserverState,
  me: string,
  labels: readonly EventLabel[],
  limit = 80,
): TalkLine[] {
  const lines: TalkLine[] = [];
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
    } else if (event.type === ROBOT_CALLED) {
      const summary = typeof data.summary === "string" && data.summary !== "" ? `: ${data.summary}` : "";
      lines.push({ kind: "system", id: event.id, text: `${robotName(state, data.robot_id)} ${data.ok === true ? "passou" : "falhou"}${summary}`, time });
    } else if (SYSTEM.test(event.type)) {
      const text = describe(event, labels);
      if (text !== undefined) {
        const actor = nameOf(state, data.by ?? data.author);
        lines.push({ kind: "system", id: event.id, text: actor === undefined ? text : `${actor} ${text}`, time });
      }
    }
  }
  return lines.reverse();
}
