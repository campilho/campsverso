/** O quadro dos pedidos e a conversa do gerente (ADR-0078).
 *
 * O humano entra no escritório como o gerente: escreve pedidos no quadro, fala com o dev, aceita ou
 * devolve o que foi entregue e sai pela porta. O quadro é desenhado dos pedidos que o mundo tem (as
 * entidades `ticket`); a tela não decide nada: cada botão vira uma proposta, e o kernel decide.
 *
 * O formulário e a caixa de fala são montados uma vez só: redesenhar o painel a cada mudança do
 * estado apagaria o que o gerente está escrevendo. Só o quadro se redesenha.
 */
import type { ObserverState } from "@campsverso/contracts";

import { button, el } from "../dom.ts";

export interface TicketView {
  readonly id: string;
  readonly number: number;
  readonly title: string;
  readonly description: string;
  readonly acceptance: string;
  readonly size: string;
  readonly state: string;
  readonly owner: string | undefined;
  readonly comment: string | undefined;
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

/** Um mundo com quadro de pedidos: o escritório. */
export function isOffice(state: ObserverState): boolean {
  return Object.values(state.entities).some((entity) => entity?.kind === "board");
}

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
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
      comment: typeof a.comentario === "string" ? a.comentario : undefined,
    });
  }
  return found.sort((a, b) => a.number - b.number);
}

export interface NewTicket {
  readonly title: string;
  readonly description: string;
  readonly acceptance: string;
  readonly size: string;
}

export interface OfficeActions {
  write(ticket: NewTicket): void;
  accept(ticketId: string): void;
  giveBack(ticketId: string, comment: string): void;
  speak(text: string): void;
  leave(): void;
}

export class OfficePanel {
  private readonly board = el("div", { className: "board" });
  private readonly managerOnly: HTMLElement[] = [];
  private readonly hint = el("p", { className: "hint" });
  private shown = "";
  private readonly root: HTMLElement;
  private readonly actions: OfficeActions;

  constructor(root: HTMLElement, actions: OfficeActions) {
    this.root = root;
    this.actions = actions;
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
    this.managerOnly.push(talk, form, leave);
    this.root.replaceChildren(el("div", { className: "card" }, el("h2", {}, "Quadro dos pedidos"), this.board), talk, form, leave, this.hint);
  }

  render(state: ObserverState, manager: boolean): void {
    for (const part of this.managerOnly) {
      part.hidden = !manager;
    }
    this.hint.hidden = manager;
    this.hint.textContent = "Entre no escritório como o gerente para escrever pedidos e falar com o dev.";
    const tickets = ticketsOf(state);
    const key = JSON.stringify([manager, tickets]);
    if (key === this.shown) {
      return;
    }
    this.shown = key;
    this.board.replaceChildren(
      ...COLUMNS.map(([id, label]) => {
        const mine = tickets.filter((t) => t.state === id);
        return el(
          "div",
          { className: `column ${id}` },
          el("h3", {}, `${label} · ${String(mine.length)}`),
          ...mine.map((ticket) => this.card(ticket, manager, state)),
        );
      }),
    );
  }

  private card(ticket: TicketView, manager: boolean, state: ObserverState): HTMLElement {
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
    if (manager && ticket.state === "entregue") {
      const comment = el("input");
      comment.placeholder = "O que falta (para devolver)";
      comment.maxLength = SPEECH_MAX;
      comment.addEventListener("keydown", (event) => { event.stopPropagation(); });
      details.open = true;
      details.append(
        el(
          "div",
          { className: "row" },
          button("Aceitar", () => { this.actions.accept(ticket.id); }),
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
