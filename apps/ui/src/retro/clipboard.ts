/** A prancheta da tela retrô (docs/design/briefing-tela.md, §3.6): o novo pedido e a ficha aberta,
 * num modal por cima de tudo, com a sala viva atrás.
 *
 * - **O novo pedido:** os campos de hoje, com os mesmos limites, em letra de mão. Fechar (Esc ou o
 *   botão) guarda o rascunho; "Pôr no quadro" chama a mesma ação de hoje (o gerente anda até o
 *   quadro), e o rascunho só some quando a ficha de verdade nasce.
 * - **A ficha aberta:** o pedido em leitura, com o PR, o patch e, entregue e com o gerente, o aceitar
 *   e o devolver. As regras são as do cartão de hoje; só a forma muda.
 *
 * Nada aqui decide coisa do mundo: cada botão vira uma proposta, e o kernel decide. */
import type { ObserverState } from "@campsverso/contracts";

import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";
import { ACCEPTANCE_MAX, DESCRIPTION_MAX, SPEECH_MAX, TITLE_MAX, ticketsOf, type NewTicket, type TicketView } from "../panels/office.ts";
import { pullRequestPill } from "./board.ts";
import { EMPTY_DRAFT, SIZES, counterOf, isSize, nextNumber, parseDraft, stateLabel, type Draft, type Size } from "./tickets.ts";

const DRAFT_KEY = "campsverso.prancheta.v1";
const LINE = 28; // a entrelinha da pauta, em px

export interface ClipboardActions {
  write(ticket: NewTicket): void;
  accept(ticketId: string): void;
  giveBack(ticketId: string, comment: string): void;
  patch(heading: string, ref: string): void;
}

/** O que a prancheta precisa do mundo para abrir e para se manter em dia. */
export interface ClipboardContext {
  readonly state: ObserverState;
  readonly me: string;
  /** O gerente está com quem joga, e a conexão está aberta. */
  readonly manager: boolean;
  /** Os pedidos a que o gerente já está indo (aceitar ou devolver). */
  readonly underway: ReadonlySet<string>;
  /** A hora do mundo agora: "Dia 13 · 10:59". */
  readonly when: string;
  readonly art: ArtManifest | undefined;
}

type Mode = { readonly kind: "new" } | { readonly kind: "read"; readonly ticketId: string };

function loadDraft(): Draft {
  try {
    return parseDraft(sessionStorage.getItem(DRAFT_KEY));
  } catch {
    return EMPTY_DRAFT; // sem acesso ao armazenamento, o rascunho fica só na página
  }
}

function saveDraft(draft: Draft): void {
  try {
    if (JSON.stringify(draft) === JSON.stringify(EMPTY_DRAFT)) {
      sessionStorage.removeItem(DRAFT_KEY);
    } else {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
    }
  } catch {
    // sem armazenamento, o rascunho vive enquanto a página viver
  }
}

function nameOf(state: ObserverState, id: string | undefined, fallback: string): string {
  return id === undefined ? fallback : (state.entities[id]?.display_name ?? id.charAt(0).toUpperCase() + id.slice(1));
}

/** O dev do elenco que a visão conhece; fora da sala, a visão do jogador não o traz. */
function devOf(state: ObserverState): string | undefined {
  return Object.entries(state.entities).find(([, e]) => e?.kind === "avatar" && e.attributes.papel === "dev")?.[0];
}

/** "De Gerente para Camps, o dev." (ou "para o dev", sem o dev na visão). */
function route(state: ObserverState, from: string, to: string | undefined): (Node | string)[] {
  const head = ["De ", strong(from)];
  return to === undefined ? [...head, " para o dev."] : [...head, " para ", strong(nameOf(state, to, "o dev")), ", o dev."];
}

/** A `textarea` pautada cresce de `min` a `max` linhas, e depois rola. */
function grow(area: HTMLTextAreaElement, min: number, max: number): void {
  area.style.height = "0px";
  area.style.height = `${String(Math.min(Math.max(area.scrollHeight, min * LINE), max * LINE))}px`;
}

function label(text: string, id?: string, extra?: string): HTMLElement {
  const node = el("div", { className: "retro-field-label" }, text, extra === undefined ? undefined : el("span", {}, ` · ${extra}`));
  if (id !== undefined) {
    node.id = id;
  }
  return node;
}

function strong(text: string): HTMLElement {
  return el("b", {}, text);
}

export class Clipboard {
  readonly element: HTMLDialogElement;
  private readonly actions: ClipboardActions;
  private mode: Mode | undefined;
  private draft: Draft = loadDraft();
  /** O rascunho como foi para o quadro: some quando nasce a ficha com o mesmo título. */
  private sent: string | undefined;
  private returnTo: HTMLElement | null = null;
  private shown = "";
  private ctx: ClipboardContext | undefined;
  /** O "O que falta" da ficha aberta: o mesmo campo entre um desenho e outro, para não perder o que
   * o gerente escreve enquanto o mundo anda. */
  private readonly comment = el("input", { className: "retro-missing" });

  constructor(parent: HTMLElement, actions: ClipboardActions) {
    this.actions = actions;
    this.element = el("dialog", { className: "retro-clipboard-dialog" });
    this.element.setAttribute("aria-modal", "true");
    // O teclado anda com o avatar: dentro da prancheta, ele escreve.
    this.element.addEventListener("keydown", (event) => { event.stopPropagation(); });
    this.element.addEventListener("close", () => {
      this.mode = undefined;
      this.shown = "";
      this.returnTo?.focus();
    });
    this.comment.maxLength = SPEECH_MAX;
    this.comment.placeholder = "O que falta (para devolver)";
    this.comment.setAttribute("aria-label", "O que falta");
    parent.append(this.element);
  }

  get isOpen(): boolean {
    return this.element.open;
  }

  /** O "Escrever pedido": só com o gerente; o foco vai ao título. */
  openNew(ctx: ClipboardContext): void {
    if (!ctx.manager) {
      return;
    }
    this.ctx = ctx;
    this.begin({ kind: "new" });
    const title = this.renderNew(ctx);
    this.element.showModal();
    for (const area of this.element.querySelectorAll<HTMLTextAreaElement>("textarea")) {
      area.dispatchEvent(new Event("input"));
    }
    title.focus();
  }

  /** Um clique numa ficha do quadro: a prancheta em leitura. */
  openTicket(ticketId: string, ctx: ClipboardContext): void {
    if (!ticketsOf(ctx.state).some((t) => t.id === ticketId)) {
      return;
    }
    this.begin({ kind: "read", ticketId });
    this.comment.value = "";
    this.update(ctx);
    this.element.showModal();
    this.element.querySelector<HTMLElement>(".retro-clip-close")?.focus();
  }

  /** A cada quadro: soltar o gerente, ou uma queda, fecham o novo pedido (o rascunho fica); a ficha
   * aberta acompanha o pedido. */
  update(ctx: ClipboardContext): void {
    this.ctx = ctx;
    const mode = this.mode;
    if (mode === undefined) {
      return;
    }
    if (mode.kind === "new") {
      if (!ctx.manager) {
        this.close();
      }
      return;
    }
    const ticket = ticketsOf(ctx.state).find((t) => t.id === mode.ticketId);
    if (ticket === undefined) {
      this.close();
      return;
    }
    const underway = ctx.underway.has(ticket.id);
    const key = JSON.stringify([ticket, ctx.manager, underway, ctx.art === undefined]);
    if (key !== this.shown) {
      this.shown = key;
      this.renderRead(ticket, ctx, underway);
    }
  }

  close(): void {
    if (this.element.open) {
      this.element.close();
    }
  }

  /** A ficha nasceu no quadro: o rascunho que foi para lá some, se ninguém o mudou depois. */
  created(title: string): void {
    if (this.sent === undefined || (JSON.parse(this.sent) as Draft).title !== title) {
      return;
    }
    if (JSON.stringify(this.draft) === this.sent) {
      this.draft = EMPTY_DRAFT;
      saveDraft(this.draft);
      if (this.mode?.kind === "new" && this.ctx !== undefined) {
        this.renderNew(this.ctx).focus(); // reaberta com o pedido que já foi: a folha limpa
      }
    }
    this.sent = undefined;
  }

  private begin(mode: Mode): void {
    if (!this.element.open) {
      this.returnTo = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    }
    this.mode = mode;
    this.shown = "";
  }

  /** A madeira, o prendedor, a caneta e o papel com a faixa da cor do tamanho. */
  private board(size: string, paper: HTMLElement[], bar: HTMLElement[]): HTMLElement {
    const clip = el("img", { className: "retro-clip-clamp" });
    clip.src = "/tela/prendedor.png";
    clip.alt = "";
    const pen = el("img", { className: "retro-clip-pen" });
    pen.src = "/tela/caneta.png";
    pen.alt = "";
    return el(
      "div",
      { className: "retro-clipboard" },
      clip,
      pen,
      el("div", { className: `retro-paper tam-${size}` }, el("div", { className: "retro-paper-stripe" }), ...paper),
      el("div", { className: "retro-clip-bar" }, ...bar),
    );
  }

  private header(heading: string, number: string, right: HTMLElement): HTMLElement {
    const title = el("h2", { className: "retro-paper-title" }, heading);
    title.id = "retro-clip-title";
    this.element.setAttribute("aria-labelledby", title.id);
    return el(
      "header",
      { className: "retro-paper-head" },
      el("div", {}, el("div", { className: "retro-paper-kicker" }, "Campsverso · ficha de pedido"), title),
      el("div", { className: "retro-paper-number" }, el("span", { className: "retro-paper-no" }, `Nº ${number}`), right),
    );
  }

  private closeButton(): HTMLButtonElement {
    const node = el("button", { className: "retro-button retro-clip-close" }, "Fechar");
    node.type = "button";
    node.addEventListener("click", () => { this.close(); });
    return node;
  }

  /** Os três quadrados do tamanho, com o "X" no escolhido. Em leitura, desabilitados. */
  private sizes(chosen: Size, onPick: ((size: Size) => void) | undefined): HTMLElement {
    const group = el("div", { className: "retro-sizes" });
    group.setAttribute("role", "radiogroup");
    group.setAttribute("aria-labelledby", "retro-size-label");
    const boxes: [HTMLInputElement, HTMLElement, HTMLElement][] = [];
    const refresh = (): void => {
      for (const [input, box, item] of boxes) {
        box.textContent = input.checked ? "X" : "";
        item.classList.toggle("on", input.checked);
      }
    };
    for (const [size, name] of SIZES) {
      const input = el("input");
      input.type = "radio";
      input.name = "retro-tamanho";
      input.value = size;
      input.checked = size === chosen;
      input.disabled = onPick === undefined;
      input.setAttribute("aria-label", `${size}, ${name}`);
      input.addEventListener("change", () => {
        refresh();
        if (input.checked) {
          onPick?.(size);
        }
      });
      const box = el("span", { className: "retro-size-box" });
      const item = el("label", { className: `retro-size tam-${size}` }, input, box, el("b", {}, size), el("span", { className: "retro-size-name" }, name));
      boxes.push([input, box, item]);
      group.append(item);
    }
    refresh();
    return group;
  }

  private renderNew(ctx: ClipboardContext): HTMLInputElement {
    const state = ctx.state;
    const manager = nameOf(state, ctx.me, "Gerente");
    const title = el("input", { className: "retro-hand retro-rule" });
    title.maxLength = TITLE_MAX;
    title.value = this.draft.title;
    title.placeholder = "Um título curto";
    title.setAttribute("aria-labelledby", "retro-title-label");
    const description = el("textarea", { className: "retro-hand retro-lined" });
    description.maxLength = DESCRIPTION_MAX;
    description.value = this.draft.description;
    description.placeholder = "O que o dev precisa fazer";
    description.setAttribute("aria-labelledby", "retro-description-label");
    const acceptance = el("textarea", { className: "retro-hand retro-lined" });
    acceptance.maxLength = ACCEPTANCE_MAX;
    acceptance.value = this.draft.acceptance;
    acceptance.placeholder = "Como você vê que ficou pronto";
    acceptance.setAttribute("aria-labelledby", "retro-acceptance-label");
    const counters = [el("span", { className: "retro-counter" }), el("span", { className: "retro-counter" }), el("span", { className: "retro-counter" })];
    const missing = el("span", { className: "retro-clip-missing" }, "Falta o título");
    const put = el("button", { className: "retro-take retro-put" }, el("i", { className: "retro-pin vermelho" }), "Pôr no quadro");
    put.type = "button";
    let size = this.draft.size;
    const sizes = this.sizes(size, (picked) => { size = picked; sync(); });
    const paper = (): HTMLElement | null => this.element.querySelector(".retro-paper");
    const sync = (): void => {
      this.draft = { title: title.value, description: description.value, acceptance: acceptance.value, size };
      saveDraft(this.draft);
      const node = paper();
      if (node !== null) {
        node.className = `retro-paper tam-${size}`;
      }
      [[title.value.length, TITLE_MAX], [description.value.length, DESCRIPTION_MAX], [acceptance.value.length, ACCEPTANCE_MAX]].forEach(([length = 0, max = 0], i) => {
        const counter = counters[i];
        if (counter !== undefined) {
          counter.textContent = counterOf(length, max) ?? "";
        }
      });
      const empty = title.value.trim() === "";
      put.disabled = empty;
      missing.hidden = !empty;
    };
    title.addEventListener("input", sync);
    title.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        description.focus();
      }
    });
    description.addEventListener("input", () => { grow(description, 3, 6); sync(); });
    acceptance.addEventListener("input", () => { grow(acceptance, 2, 4); sync(); });
    put.addEventListener("click", () => {
      if (title.value.trim() === "") {
        title.focus();
        return;
      }
      this.actions.write({
        title: title.value.trim(),
        description: description.value.trim(),
        acceptance: acceptance.value.trim(),
        size,
      });
      this.sent = JSON.stringify(this.draft);
      this.close();
    });
    const tickets = ticketsOf(state);
    const content = this.board(
      size,
      [
        this.header("Novo pedido", `#${String(nextNumber(tickets))}`, el("span", { className: "retro-paper-when" }, ctx.when)),
        el("p", { className: "retro-paper-route" }, ...route(state, manager, devOf(state)), " A ficha entra no quadro em ", strong("A fazer"), "."),
        el("div", { className: "retro-field" }, el("div", { className: "retro-field-top" }, label("Título", "retro-title-label"), counters[0]), title),
        el("div", { className: "retro-field" }, el("div", { className: "retro-field-top" }, label("O que fazer", "retro-description-label"), counters[1]), description),
        el(
          "div",
          { className: "retro-field" },
          el("div", { className: "retro-field-top" }, label("Teste de aceite", "retro-acceptance-label", "como você vê que ficou pronto"), counters[2]),
          acceptance,
        ),
        el("div", { className: "retro-field" }, label("Tamanho", "retro-size-label"), sizes),
        el("div", { className: "retro-signature" }, el("span", { className: "retro-hand" }, manager), el("span", {}, "Assinatura")),
      ],
      [this.closeButton(), el("span", { className: "retro-clip-spacer" }), missing, put],
    );
    this.element.replaceChildren(content);
    sync();
    return title;
  }

  private renderRead(ticket: TicketView, ctx: ClipboardContext, underway: boolean): void {
    const state = ctx.state;
    const focused = document.activeElement;
    const number = `#${String(ticket.number)}`;
    const text = (value: string, className: string): HTMLElement =>
      el("div", { className: `retro-hand ${className}${value === "" ? " empty" : ""}` }, value === "" ? "—" : value);
    const from = nameOf(state, ticket.author, "Gerente");
    const routeLine = el("p", { className: "retro-paper-route" }, ...route(state, from, ticket.owner ?? devOf(state)));
    if (ticket.owner !== undefined) {
      routeLine.append(" Está com ", strong(nameOf(state, ticket.owner, "o dev")), ".");
    }
    const paper: HTMLElement[] = [
      this.header("Ficha do pedido", number, el("span", { className: `retro-paper-state ${ticket.state}` }, stateLabel(ticket.state))),
      routeLine,
      el("div", { className: "retro-field" }, label("Título"), text(ticket.title, "retro-rule")),
      el("div", { className: "retro-field" }, label("O que fazer"), text(ticket.description, "retro-lined")),
      el("div", { className: "retro-field" }, label("Teste de aceite", undefined, "como você vê que ficou pronto"), text(ticket.acceptance, "retro-lined")),
      el("div", { className: "retro-field" }, label("Tamanho", "retro-size-label"), this.sizes(isSize(ticket.size) ? ticket.size : "M", undefined)),
    ];
    if (ticket.comment !== undefined) {
      paper.push(el("p", { className: "retro-hand retro-returned" }, `Devolvido: ${ticket.comment}`));
    }
    const extras: HTMLElement[] = [];
    if (ticket.pr !== undefined) {
      extras.push(pullRequestPill(ticket.pr, ctx.art));
    }
    const ref = ticket.patch;
    if (ref !== undefined && (ticket.state === "entregue" || ticket.state === "aceito")) {
      const see = el("button", { className: "retro-button" }, "Ver o patch");
      see.type = "button";
      see.addEventListener("click", () => { this.actions.patch(`Pedido ${number}: ${ticket.title}`, ref); });
      extras.push(see);
    }
    if (extras.length > 0) {
      paper.push(el("div", { className: "retro-paper-extras" }, ...extras));
    }
    const bar: HTMLElement[] = [this.closeButton(), el("span", { className: "retro-clip-spacer" })];
    if (ctx.manager && ticket.state === "entregue" && underway) {
      bar.push(el("span", { className: "retro-clip-note" }, "O gerente está indo ao quadro."));
    } else if (ctx.manager && ticket.state === "entregue") {
      const pr = ticket.pr;
      const give = el("button", { className: "retro-button" }, "Devolver");
      give.type = "button";
      give.addEventListener("click", () => {
        const comment = this.comment.value.trim();
        if (comment === "") {
          this.comment.focus();
          return;
        }
        this.actions.giveBack(ticket.id, comment);
        this.close();
      });
      bar.push(this.comment, give);
      // Com o PR aberto, aceitar é mesclar no GitHub (ADR-0083): o quadro não aceita.
      if (pr?.state === "aberto") {
        bar.push(el("span", { className: "retro-clip-note" }, `Aceite mesclando o PR #${String(pr.number)}`));
      } else {
        const accept = el("button", { className: "retro-take retro-put" }, "Aceitar");
        accept.type = "button";
        accept.addEventListener("click", () => {
          this.actions.accept(ticket.id);
          this.close();
        });
        bar.push(accept);
      }
    }
    this.element.replaceChildren(this.board(ticket.size, paper, bar));
    // O desenho novo não tira o foco de quem escrevia o que falta.
    if (focused === this.comment) {
      this.comment.focus();
    } else if (this.element.open && !this.element.contains(focused)) {
      this.element.querySelector<HTMLElement>(".retro-clip-close")?.focus();
    }
  }
}
