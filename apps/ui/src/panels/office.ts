/** O quadro dos pedidos e a conversa do gerente (ADR-0078).
 *
 * O humano entra no escritório como o gerente: escreve pedidos no quadro, fala com o dev, aceita ou
 * devolve o que foi entregue e sai pela porta. O quadro é desenhado dos pedidos que o mundo tem (as
 * entidades `ticket`); a tela não decide nada: cada botão vira uma proposta, e o kernel decide.
 *
 * O formulário e a caixa de fala são montados uma vez só: redesenhar o painel a cada mudança do
 * estado apagaria o que o gerente está escrevendo. Só o quadro se redesenha.
 */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

import { button, el } from "../dom.ts";
import { choicesOf } from "../locale.ts";
import { clockText } from "../simclock.ts";
import { DeliveryDialog } from "./delivery.ts";

/** Um dev e a convocação dele fora do expediente (a parte 5 do M25), dos atributos do avatar. */
export interface SummonView {
  readonly id: string;
  readonly name: string;
  readonly present: boolean;
  readonly summoned: boolean;
  readonly arrives: number | undefined;
  readonly until: number | undefined;
}

const SUMMONED = "campsverso.office.staff.summoned.v1";
const DISMISSED = "campsverso.office.staff.dismissed.v1";

function title(id: string): string {
  return id === "" ? "o dev" : id.charAt(0).toUpperCase() + id.slice(1);
}

/** Os devs, com a convocação de cada um. A tela do jogador não traz quem está fora da sala: a
 * convocação de um dev ausente vem dos fatos dela na linha do tempo, e, sem nenhum dev conhecido,
 * fica um "dev" sem id, que o kernel resolve para o único dev do elenco. */
export function summonsOf(state: ObserverState, timeline: readonly EnvelopeV1[] = []): SummonView[] {
  const found = new Map<string, SummonView>();
  for (const event of timeline) {
    if (event.type !== SUMMONED && event.type !== DISMISSED) {
      continue;
    }
    const data = event.data as { avatar_id?: unknown; arrives_tick?: unknown; until_tick?: unknown };
    if (typeof data.avatar_id !== "string") {
      continue;
    }
    const summoned = event.type === SUMMONED;
    found.set(data.avatar_id, {
      id: data.avatar_id,
      name: state.entities[data.avatar_id]?.display_name ?? title(data.avatar_id),
      present: false,
      summoned,
      arrives: summoned && typeof data.arrives_tick === "number" ? data.arrives_tick : undefined,
      until: summoned && typeof data.until_tick === "number" ? data.until_tick : undefined,
    });
  }
  for (const [id, entity] of Object.entries(state.entities)) {
    if (entity?.kind !== "avatar" || entity.attributes.papel !== "dev") {
      continue;
    }
    const a = entity.attributes;
    const tick = (key: string): number | undefined => {
      const value = a[key];
      return typeof value === "number" ? value : undefined;
    };
    found.set(id, {
      id,
      name: entity.display_name ?? title(id),
      present: entity.position !== undefined, // fora do escritório, o avatar não tem posição
      summoned: typeof a.convocado_por === "string",
      arrives: tick("convocado_chega"),
      until: tick("convocado_ate"),
    });
  }
  // Os devs do elenco que a visão não traz (fora da sala): do locale do cenário (ADR-0093).
  for (const [id, name] of choicesOf("assignee")) {
    if (!found.has(id)) {
      found.set(id, { id, name, present: false, summoned: false, arrives: undefined, until: undefined });
    }
  }
  if (found.size === 0) {
    found.set("", { id: "", name: title(""), present: false, summoned: false, arrives: undefined, until: undefined });
  }
  return [...found.values()].sort((x, y) => (x.id < y.id ? -1 : x.id > y.id ? 1 : 0));
}

/** A linha de um dev na convocação: a caminho, até quando, no expediente ou fora. */
export function summonLine(state: ObserverState, dev: SummonView): string {
  const at = (tick: number | undefined): string => (tick === undefined ? "--:--" : clockText(state, tick).slice(0, 5));
  if (dev.summoned && !dev.present) {
    return `${dev.name} está a caminho: chega às ${at(dev.arrives)}`;
  }
  if (dev.summoned) {
    return `${dev.name} convocado até as ${at(dev.until)}`;
  }
  return dev.present ? `${dev.name} está no escritório` : `${dev.name} está fora`;
}

export interface TicketView {
  readonly id: string;
  readonly number: number;
  readonly title: string;
  readonly description: string;
  readonly acceptance: string;
  readonly size: string;
  readonly state: string;
  readonly owner: string | undefined;
  /** Quem escreveu o pedido (o gerente). */
  readonly author: string | undefined;
  readonly comment: string | undefined;
  /** A chave do patch que o dev entregou da oficina (ADR-0080); sem ela, o trabalho foi simulado. */
  readonly patch: string | undefined;
  /** O PR do pedido no GitHub (ADR-0083), quando a entrega virou um. */
  readonly pr: PullRequestView | undefined;
  /** Quem programa e o modelo, quando o gerente escolheu na prancheta (ADR-0089). */
  readonly harness: string | undefined;
  readonly model: string | undefined;
  /** Para quem (ADR-0093, decisão 8): o dev a quem o pedido foi dado. */
  readonly assignee: string | undefined;
  /** O grupo de um "para todos": as fichas do mesmo pedido, uma por dev. */
  readonly group: string | undefined;
}

export interface PullRequestView {
  readonly number: number;
  readonly url: string;
  /** aberto, mesclado ou fechado */
  readonly state: string;
  /** pending, success ou failure */
  readonly ci: string;
}

const CI_TEXT: Readonly<Record<string, string>> = { pending: "CI rodando", success: "CI verde", failure: "CI vermelho" };
// Só o endereço de um PR no GitHub vira link (o contrato já o confere; aqui, de novo).
export const PR_URL = /^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/pull\/[0-9]+$/;

function pullRequestOf(a: Readonly<Record<string, unknown>>): PullRequestView | undefined {
  if (typeof a.pr !== "number") {
    return undefined;
  }
  return { number: a.pr, url: text(a.pr_url), state: text(a.pr_estado), ci: text(a.pr_ci) };
}

/** A linha do PR no cartão: o número (um link para o GitHub), o estado e o CI. */
export function pullRequestLine(pr: PullRequestView): string {
  const parts = [`PR #${String(pr.number)}`, pr.state];
  if (pr.state === "aberto" && pr.ci in CI_TEXT) {
    parts.push(CI_TEXT[pr.ci] ?? "");
  }
  return parts.join(" · ");
}

export const COLUMNS: readonly (readonly [string, string])[] = [
  ["a_fazer", "A fazer"],
  ["fazendo", "Fazendo"],
  ["entregue", "Entregue"],
  ["aceito", "Aceito"],
];
export const TITLE_MAX = 80;
export const DESCRIPTION_MAX = 1000;
export const ACCEPTANCE_MAX = 500;
export const SPEECH_MAX = 280;
/** A devolução (ADR-0092): o mesmo limite da descrição, o `comment_max` do cartucho. */
export const COMMENT_MAX = 1000;

/** Um mundo com quadro de pedidos: o escritório. */
export function isOffice(state: ObserverState): boolean {
  return Object.values(state.entities).some((entity) => entity?.kind === "board");
}

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

/** Um link que abre noutra aba, sem dar à página de lá acesso a esta. */
function link(label: string, url: string): HTMLAnchorElement {
  const anchor = el("a", {}, label);
  anchor.href = url;
  anchor.target = "_blank";
  anchor.rel = "noopener noreferrer";
  return anchor;
}

/** Os pedidos do quadro, na ordem em que foram escritos. */
export function ticketsOf(state: ObserverState): TicketView[] {
  const found: TicketView[] = [];
  for (const [id, entity] of Object.entries(state.entities)) {
    if (entity?.kind !== "ticket") {
      continue;
    }
    const a = entity.attributes;
    found.push({
      id,
      number: Number(a.numero ?? 0),
      title: text(a.titulo),
      description: text(a.descricao),
      acceptance: text(a.aceite),
      size: text(a.tamanho),
      state: text(a.estado),
      owner: typeof a.dono === "string" ? a.dono : undefined,
      author: typeof a.autor === "string" ? a.autor : undefined,
      comment: typeof a.comentario === "string" ? a.comentario : undefined,
      patch: typeof a.patch === "string" && a.patch !== "" ? a.patch : undefined,
      pr: pullRequestOf(a),
      harness: typeof a.maos === "string" && a.maos !== "" ? a.maos : undefined,
      model: typeof a.modelo === "string" && a.modelo !== "" ? a.modelo : undefined,
      assignee: typeof a.para === "string" && a.para !== "" ? a.para : undefined,
      group: typeof a.grupo === "string" && a.grupo !== "" ? a.grupo : undefined,
    });
  }
  return found.sort((a, b) => a.number - b.number);
}

export interface NewTicket {
  readonly title: string;
  readonly description: string;
  readonly acceptance: string;
  readonly size: string;
  /** Quem programa e o modelo (ADR-0089); sem eles, o padrão do mundo. */
  readonly harness?: string;
  readonly model?: string;
  /** Para quem e para todos (ADR-0093, decisão 8); sem eles, quem estiver livre. */
  readonly assignee?: string;
  readonly everyone?: boolean;
}

/** O sistema da volta, escolhido ao devolver (ADR-0093, decisão 12). */
export interface System {
  readonly harness: string;
  readonly model?: string;
}

export interface OfficeActions {
  write(ticket: NewTicket): void;
  accept(ticketId: string): void;
  giveBack(ticketId: string, comment: string, system?: System): void;
  speak(text: string): void;
  leave(): void;
  summon(devId: string): void;
  dismiss(devId: string): void;
}

export class OfficePanel {
  private readonly board = el("div", { className: "board" });
  private readonly summons = el("div", { className: "summons" });
  private readonly managerOnly: HTMLElement[] = [];
  private readonly hint = el("p", { className: "hint" });
  private shown = "";
  private readonly root: HTMLElement;
  private readonly actions: OfficeActions;
  private readonly delivery: DeliveryDialog;

  constructor(root: HTMLElement, actions: OfficeActions) {
    this.root = root;
    this.actions = actions;
    this.delivery = new DeliveryDialog(document.body);
    const say = el("input", { className: "speech" });
    say.maxLength = SPEECH_MAX;
    say.placeholder = "Fale com o dev e aperte Enter";
    say.setAttribute("aria-label", "Falar");
    const speak = (): void => {
      const value = say.value.trim();
      if (value !== "") {
        this.actions.speak(value);
        say.value = "";
      }
    };
    say.addEventListener("keydown", (event) => {
      event.stopPropagation(); // o teclado anda com o avatar: aqui ele escreve
      if (event.key === "Enter") {
        speak();
      }
    });
    const talk = el("div", { className: "card" }, el("h2", {}, "Falar"), el("div", { className: "row" }, say, button("Falar", speak)));

    const title = el("input");
    title.maxLength = TITLE_MAX;
    title.placeholder = "Título";
    const description = el("textarea");
    description.maxLength = DESCRIPTION_MAX;
    description.placeholder = "O que fazer";
    const acceptance = el("textarea");
    acceptance.maxLength = ACCEPTANCE_MAX;
    acceptance.placeholder = "Teste de aceite: quando está pronto";
    const size = el("select");
    for (const [value, label] of [["P", "P (pequeno)"], ["M", "M (médio)"], ["G", "G (grande)"]] as const) {
      const option = el("option", {}, label);
      option.value = value;
      size.append(option);
    }
    for (const field of [title, description, acceptance]) {
      field.addEventListener("keydown", (event) => { event.stopPropagation(); });
    }
    const write = (): void => {
      if (title.value.trim() === "") {
        title.focus();
        return;
      }
      this.actions.write({
        title: title.value.trim(),
        description: description.value.trim(),
        acceptance: acceptance.value.trim(),
        size: size.value,
      });
      title.value = description.value = acceptance.value = "";
    };
    const form = el(
      "div",
      { className: "card new-ticket" },
      el("h2", {}, "Novo pedido"),
      title,
      description,
      acceptance,
      el("div", { className: "row" }, size, button("Escrever no quadro", write)),
    );
    const leave = button("Sair do escritório", () => { this.actions.leave(); });
    const summon = el("div", { className: "card summon" }, el("h2", {}, "Convocação"), this.summons);
    this.managerOnly.push(talk, summon, form, leave);
    // Na tela retrô, o quadro e o novo pedido vão para a cortiça e a prancheta (`retro/`).
    const tickets = el("div", { className: "card tickets" }, el("h2", {}, "Quadro dos pedidos"), this.board);
    this.root.replaceChildren(tickets, talk, summon, form, leave, this.hint);
  }

  /** O "Ver o patch" de um pedido, no diálogo de sempre (a prancheta da tela retrô o usa também). */
  openPatch(heading: string, ref: string): void {
    void this.delivery.open(heading, ref);
  }

  /** `underway`: os pedidos a que o gerente já está indo (aceitar ou devolver, na fila ou fazendo). */
  render(
    state: ObserverState,
    manager: boolean,
    underway: ReadonlySet<string> = new Set(),
    timeline: readonly EnvelopeV1[] = [],
  ): void {
    for (const part of this.managerOnly) {
      part.hidden = !manager;
    }
    this.hint.hidden = manager;
    this.hint.textContent = "Entre no escritório como o gerente para escrever pedidos e falar com o dev.";
    const tickets = ticketsOf(state);
    const devs = summonsOf(state, timeline);
    const lines = devs.map((dev) => summonLine(state, dev));
    const key = JSON.stringify([manager, tickets, [...underway].sort(), devs, lines]);
    if (key === this.shown) {
      return;
    }
    this.shown = key;
    this.summons.replaceChildren(
      ...devs.map((dev, i) =>
        el(
          "div",
          { className: "row" },
          el("span", { className: "hint" }, lines[i] ?? ""),
          ...(dev.summoned
            ? [button(`Dispensar o ${dev.name}`, () => { this.actions.dismiss(dev.id); })]
            : dev.present
              ? []
              : [button(`Convocar ${dev.id === "" ? dev.name : `o ${dev.name}`}`, () => { this.actions.summon(dev.id); })]),
        ),
      ),
    );
    this.board.replaceChildren(
      ...COLUMNS.map(([id, label]) => {
        const mine = tickets.filter((t) => t.state === id);
        return el(
          "div",
          { className: `column ${id}` },
          el("h3", {}, `${label} · ${String(mine.length)}`),
          ...mine.map((ticket) => this.card(ticket, manager, state, underway.has(ticket.id))),
        );
      }),
    );
  }

  private card(ticket: TicketView, manager: boolean, state: ObserverState, underway: boolean): HTMLElement {
    const owner = ticket.owner === undefined ? "" : (state.entities[ticket.owner]?.display_name ?? ticket.owner);
    const details = el(
      "details",
      { className: "ticket" },
      el("summary", {}, `#${String(ticket.number)} ${ticket.title} (${ticket.size})`),
      ...(ticket.description === "" ? [] : [el("p", {}, ticket.description)]),
      ...(ticket.acceptance === "" ? [] : [el("p", { className: "acceptance" }, `Pronto quando: ${ticket.acceptance}`)]),
      ...(owner === "" ? [] : [el("p", { className: "hint" }, `com ${owner}`)]),
      ...(ticket.comment === undefined ? [] : [el("p", { className: "comment" }, `Devolvido: ${ticket.comment}`)]),
    );
    const pr = ticket.pr;
    if (pr !== undefined) {
      const line = pullRequestLine(pr);
      const label = PR_URL.test(pr.url) ? link(line, pr.url) : el("span", {}, line);
      details.append(el("p", { className: `pull-request ${pr.state}` }, label));
    }
    const ref = ticket.patch;
    if (ref !== undefined && (ticket.state === "entregue" || ticket.state === "aceito")) {
      const heading = `Pedido #${String(ticket.number)}: ${ticket.title}`;
      details.append(el("div", { className: "row" }, button("Ver o patch", () => { void this.delivery.open(heading, ref); })));
    }
    if (manager && ticket.state === "entregue" && underway) {
      details.open = true;
      details.append(el("p", { className: "hint underway" }, "O gerente está indo ao quadro."));
    } else if (manager && ticket.state === "entregue") {
      const comment = el("input");
      comment.placeholder = "O que falta (para devolver)";
      comment.maxLength = COMMENT_MAX;
      comment.addEventListener("keydown", (event) => { event.stopPropagation(); });
      details.open = true;
      details.append(
        el(
          "div",
          { className: "row" },
          // Com o PR aberto, aceitar é mesclar no GitHub (ADR-0083): o quadro não aceita.
          pr?.state === "aberto"
            ? el("span", { className: "hint" }, `Aceite mesclando o PR #${String(pr.number)}`)
            : button("Aceitar", () => { this.actions.accept(ticket.id); }),
          comment,
          button("Devolver", () => {
            if (comment.value.trim() === "") {
              comment.focus();
              return;
            }
            this.actions.giveBack(ticket.id, comment.value.trim());
          }),
        ),
      );
    }
    return details;
  }
}
