/** O quadro de cortiça e a prancheta da tela retrô (docs/design/briefing-tela.md, §3.4 e §3.6), em
 * funções puras: as abas, o cabeçalho, as fichas fantasmas, o número de prévia, a linha de cada
 * ficha, o selo do PR e o rascunho. Nada aqui decide coisa do mundo: quem numera e quem aceita é o
 * kernel. */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

import { COLUMNS, pullRequestLine, type PullRequestView, type TicketView } from "../panels/office.ts";
import type { Step } from "../queue.ts";
import { clockText, tickSeconds } from "../simclock.ts";

export type Size = "P" | "M" | "G";

/** Os tamanhos, na ordem da prancheta, com o nome que a tela mostra. */
export const SIZES: readonly (readonly [Size, string])[] = [
  ["P", "pequeno"],
  ["M", "médio"],
  ["G", "grande"],
];

export function isSize(value: unknown): value is Size {
  return value === "P" || value === "M" || value === "G";
}

/** O cabeçalho do quadro: "15 pedidos · 1 PR aberto" (sem PR aberto, só os pedidos). */
export function boardSummary(tickets: readonly TicketView[]): string {
  const open = tickets.filter((t) => t.pr?.state === "aberto").length;
  const parts = [`${String(tickets.length)} ${tickets.length === 1 ? "pedido" : "pedidos"}`];
  if (open > 0) {
    parts.push(`${String(open)} PR ${open === 1 ? "aberto" : "abertos"}`);
  }
  return parts.join(" · ");
}

export interface Tab {
  readonly id: string;
  readonly label: string;
  readonly count: number;
}

/** As quatro abas, uma por coluna do quadro, com quantos pedidos cada uma tem. */
export function tabsOf(tickets: readonly TicketView[]): Tab[] {
  return COLUMNS.map(([id, label]) => ({ id, label, count: tickets.filter((t) => t.state === id).length }));
}

/** A aba para onde as setas levam: a próxima ou a anterior, dando a volta; Home e End, as pontas. */
export function nextTab(index: number, key: string, count: number): number | undefined {
  switch (key) {
    case "ArrowRight":
      return (index + 1) % count;
    case "ArrowLeft":
      return (index - 1 + count) % count;
    case "Home":
      return 0;
    case "End":
      return count - 1;
    default:
      return undefined;
  }
}

/** Uma ficha fantasma: o pedido que o gerente está indo escrever, antes de o kernel o publicar. */
export interface Ghost {
  readonly title: string;
  readonly size: string;
}

/** As fichas fantasmas, dos passos `write_ticket`: o que está sendo escrito agora e o que está na
 * fila, nesta ordem. */
export function ghostsOf(steps: readonly Step[], state: ObserverState, me: string): Ghost[] {
  const doing = state.actions[me];
  const params = [
    ...(doing?.action === "write_ticket" ? [doing.params as Record<string, unknown>] : []),
    ...steps.filter((step) => step.proposal.action === "write_ticket").map((step) => step.proposal.params),
  ];
  return params.map((p) => ({
    title: typeof p.title === "string" ? p.title : "",
    size: typeof p.size === "string" ? p.size : "M",
  }));
}

/** O número da próxima ficha, só como prévia na prancheta: quem numera é o kernel. */
export function nextNumber(tickets: readonly TicketView[]): number {
  return tickets.reduce((top, t) => Math.max(top, t.number), 0) + 1;
}

function nameOf(state: ObserverState, id: string): string {
  return state.entities[id]?.display_name ?? id.charAt(0).toUpperCase() + id.slice(1);
}

/** A linha de quem, na ficha: "com Camps" quando um dev a pegou; senão, de quem a escreveu. */
export function whoLine(ticket: TicketView, state: ObserverState): string {
  if (ticket.owner !== undefined) {
    return `com ${nameOf(state, ticket.owner)}`;
  }
  if (ticket.author === undefined) {
    return "";
  }
  return state.entities[ticket.author]?.attributes.papel === "gerente" ? "do gerente" : `de ${nameOf(state, ticket.author)}`;
}

/** O selo do PR na pílula: aberto (pelo CI) ou mesclado; fechado sem mesclar, nenhum. A mesma
 * regra do selo pendurado nas fichas da parede (`badgeOf`). */
export function badgeOfPullRequest(pr: PullRequestView | undefined): string | undefined {
  if (pr?.state === "mesclado") {
    return "mesclado";
  }
  if (pr?.state !== "aberto") {
    return undefined;
  }
  return pr.ci === "success" ? "ci_verde" : pr.ci === "failure" ? "ci_vermelho" : "pr";
}

/** O pino da ficha, alternando pelo número. */
export function pinOf(n: number): "vermelho" | "azul" {
  return n % 2 === 1 ? "vermelho" : "azul";
}

/** O contador do campo, só depois de 80% do limite: "812/1000". */
export function counterOf(length: number, max: number): string | undefined {
  return length > max * 0.8 ? `${String(length)}/${String(max)}` : undefined;
}

/** A ficha quadrada da cortiça (briefing-tela-2.md, §7): o número, o tamanho, o título e, embaixo,
 * só ícones. O resto (a descrição, o aceite, o PR por extenso, os botões) fica na ficha aberta. */
export interface SquareCard {
  readonly number: string;
  readonly size: string;
  readonly title: string;
  /** O que o leitor de tela diz da ficha, que é um botão só. */
  readonly label: string;
  /** O dono, cujo rosto vai embaixo. */
  readonly owner: string | undefined;
  /** O selo do PR (a folha `selos`) e o texto dele, no `title`. */
  readonly seal: string | undefined;
  readonly sealTitle: string | undefined;
  /** O pedido voltou do gerente e ainda não foi aceito: "devolvido", em letra de mão vermelha. */
  readonly returned: boolean;
}

export function squareOf(ticket: TicketView): SquareCard {
  const name = SIZES.find(([size]) => size === ticket.size)?.[1];
  const number = `#${String(ticket.number)}`;
  const returned = ticket.comment !== undefined && ticket.state !== "aceito";
  const parts = [`Pedido ${String(ticket.number)}: ${ticket.title}`, name === undefined ? undefined : `tamanho ${name}`, returned ? "devolvido" : undefined];
  return {
    number,
    size: ticket.size,
    title: ticket.title,
    label: parts.filter((part) => part !== undefined).join(", "),
    owner: ticket.owner,
    seal: badgeOfPullRequest(ticket.pr),
    sealTitle: ticket.pr === undefined ? undefined : pullRequestLine(ticket.pr),
    returned,
  };
}

const THOUSANDS = new Intl.NumberFormat("pt-BR");

/** O contador da devolução (ADR-0092), sempre à vista: "faltam 412 de 1.000". */
export function remainingOf(length: number, max: number): string {
  const left = Math.max(0, max - length);
  return `${left === 1 ? "falta" : "faltam"} ${THOUSANDS.format(left)} de ${THOUSANDS.format(max)}`;
}

/** "escrito no Dia 11 · 09:12", pelo fato de quando o pedido nasceu, se ele ainda está na linha do
 * tempo da tela; sem ele, nada (o pedido não guarda a hora em que foi escrito). */
export function writtenOf(state: ObserverState, timeline: readonly EnvelopeV1[], ticketId: string): string | undefined {
  const created = timeline.find(
    (event) => event.type === "campsverso.office.ticket.created.v1" && (event.data as { ticket_id?: unknown }).ticket_id === ticketId,
  );
  const tick = created?.tick;
  const hour = tick === undefined ? "--:--" : clockText(state, tick).slice(0, 5);
  if (tick === undefined || hour === "--:--") {
    return undefined;
  }
  // O dia do mundo de então: o de hoje menos as viradas de meia-noite entre os dois ticks.
  const since = (state.tick - tick) * tickSeconds(state.session);
  const today = secondsOfDay(state);
  const back = since <= today ? 0 : Math.ceil((since - today) / 86_400);
  return `escrito no Dia ${String(state.day - back)} · ${hour}`;
}

/** Quantos segundos do dia de hoje já passaram no tick do estado. */
function secondsOfDay(state: ObserverState): number {
  const [h = 0, m = 0, sec = 0] = clockText(state, state.tick).split(":").map(Number);
  return h * 3600 + m * 60 + sec;
}

/** O estado do pedido na etiqueta da ficha aberta, em caixa alta: "ENTREGUE". */
export function stateLabel(state: string): string {
  return (COLUMNS.find(([id]) => id === state)?.[1] ?? state).toUpperCase();
}

/** O rascunho da prancheta: fica quando ela fecha, e some quando a ficha de verdade nasce. */
export interface Draft {
  readonly title: string;
  readonly description: string;
  readonly acceptance: string;
  readonly size: Size;
  /** Quem programa e o modelo (ADR-0089); vazio é o padrão do escritório. */
  readonly harness: string;
  readonly model: string;
}

export const EMPTY_DRAFT: Draft = { title: "", description: "", acceptance: "", size: "M", harness: "", model: "" };

/** O rascunho guardado, conferido campo a campo: o que vier torto vira o rascunho vazio. */
export function parseDraft(raw: string | null): Draft {
  if (raw === null) {
    return EMPTY_DRAFT;
  }
  try {
    const value = JSON.parse(raw) as Record<string, unknown>;
    const str = (key: string): string => (typeof value[key] === "string" ? value[key] : "");
    return {
      title: str("title"),
      description: str("description"),
      acceptance: str("acceptance"),
      size: isSize(value.size) ? value.size : "M",
      harness: str("harness"),
      model: str("model"),
    };
  } catch {
    return EMPTY_DRAFT;
  }
}
