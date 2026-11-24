/** A prancheta da tela retrô (docs/design/briefing-tela.md, §3.6): o novo pedido e a ficha aberta,
 * num modal por cima de tudo, com a sala viva atrás.
 *
 * - **O novo pedido:** os campos de hoje, com os mesmos limites, em letra de mão. Fechar (Esc ou o
 *   botão) guarda o rascunho; "Pôr no quadro" chama a mesma ação de hoje (o gerente anda até o
 *   quadro), e o rascunho só some quando a ficha de verdade nasce.
 * - **A ficha aberta** (briefing-tela-2.md, §7; ADR-0092): o pedido em leitura, numa prancheta de
 *   660 px, com o carimbo do estado, o PR grampeado e o patch. Entregue e com o gerente, o "O que
 *   falta" em papel pautado, na tinta vermelha, com o contador (até 1.000, nunca cortado escondido),
 *   e o aceitar e o devolver na barra. As regras são as do cartão de hoje; só a forma muda.
 *
 * Nada aqui decide coisa do mundo: cada botão vira uma proposta, e o kernel decide. */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";
import { choiceName, choicesOf } from "../locale.ts";
import { ACCEPTANCE_MAX, COMMENT_MAX, DESCRIPTION_MAX, PR_URL, TITLE_MAX, ticketsOf, type NewTicket, type PullRequestView, type System, type TicketView } from "../panels/office.ts";
import { sealOf } from "./board.ts";
import type { FaceCache } from "./faces.ts";
import {
  EMPTY_DRAFT,
  badgeOfPullRequest,
  counterOf,
  nextNumber,
  parseDraft,
  remainingOf,
  stateLabel,
  writtenOf,
  type Draft,
} from "./tickets.ts";

const DRAFT_KEY = "campsverso.prancheta.v1";
const LINE = 28; // a entrelinha da pauta, em px

export interface ClipboardActions {
  write(ticket: NewTicket): void;
  accept(ticketId: string): void;
  giveBack(ticketId: string, comment: string, system?: System): void;
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
  /** Os fatos recentes: o "escrito no Dia 11 · 09:12" da ficha aberta. */
  readonly timeline: readonly EnvelopeV1[];
}

const CI_SHORT: Readonly<Record<string, string>> = { pending: "CI rodando", success: "CI verde", failure: "CI vermelho" };

/** "PR #11 · CI verde" no papel grampeado: aberto, o CI; senão, o estado. */
function stapleLine(pr: PullRequestView): string {
  const tail = pr.state === "aberto" ? (CI_SHORT[pr.ci] ?? "aberto") : pr.state;
  return `PR #${String(pr.number)} · ${tail}`;
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

/** Os devs do elenco, do locale do cenário (`choices.assignee`; ADR-0093): fora da sala, a visão do
 * jogador não os traz. */
export function devsOf(): (readonly [string, string])[] {
  return choicesOf("assignee");
}

/** O nome de um dev pelo locale; sem ele, pela visão, ou o id. */
function devName(state: ObserverState, id: string): string {
  return devsOf().find(([dev]) => dev === id)?.[1] ?? nameOf(state, id, "o dev");
}

/** "De Camps para o Kenji." / "para quem estiver livre." / "para todos os devs, uma ficha para cada." */
export function routeOf(from: string, to: string | undefined, everyone: boolean): (Node | string)[] {
  const head = ["De ", strong(from)];
  if (everyone) {
    return [...head, " para ", strong("todos os devs"), ", uma ficha para cada."];
  }
  return to === undefined ? [...head, " para quem estiver livre."] : [...head, " para ", strong(to), "."];
}

/** A cor da faixa (ADR-0093, decisão 11): a do dev, da arte; sem dev, a neutra do CSS. */
function paint(node: HTMLElement, art: ArtManifest | undefined, dev: string | undefined): void {
  const color = dev === undefined ? undefined : art?.avatars?.[dev]?.color;
  if (color === undefined) {
    node.style.removeProperty("--faixa");
  } else {
    node.style.setProperty("--faixa", color);
  }
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

/** Uma escolha da prancheta (ADR-0089): a primeira opção, vazia, é o padrão do dev. */
function picker(kind: string, chosen: string, labelId: string, onPick: (value: string) => void): HTMLSelectElement | undefined {
  const options = choicesOf(kind);
  if (options.length === 0) {
    return undefined; // um mundo sem a escolha
  }
  const select = el("select", { className: "retro-hand retro-pick" });
  select.setAttribute("aria-labelledby", labelId);
  fill(select, [["", "o padrão do dev"], ...options], chosen);
  select.addEventListener("change", () => { onPick(select.value); });
  return select;
}

function fill(select: HTMLSelectElement, options: readonly (readonly [string, string])[], chosen: string): void {
  select.replaceChildren(
    ...options.map(([value, name]) => {
      const option = el("option", {}, name);
      option.value = value;
      option.selected = value === chosen;
      return option;
    }),
  );
}

/** Os modelos que cabem em quem programa (ADR-0093, decisão 18): a lista do harness, ou todos. */
export function modelsFor(harness: string): (readonly [string, string])[] {
  const own = choicesOf(`models.${harness}`);
  return own.length > 0 ? own : choicesOf("models");
}

/** O seletor do modelo segue o de quem programa: sem harness, só o padrão do dev; com ele, o
 * padrão do harness (o primeiro da lista dele) e os modelos da língua dele. Devolve o modelo que
 * ficou escolhido, vazio quando o de antes não cabe no harness novo. */
export function syncModels(select: HTMLSelectElement, harness: string, chosen: string): string {
  if (harness === "") {
    fill(select, [["", "o padrão do dev"]], "");
    select.disabled = true;
    return "";
  }
  const models = modelsFor(harness);
  const kept = models.some(([id]) => id === chosen) ? chosen : "";
  fill(select, [["", `o padrão do ${choiceName("hands", harness)}`], ...models], kept);
  select.disabled = false;
  return kept;
}

/** "Claude Code · Opus 5.5" (ou o padrão do dev no que não foi escolhido). */
export function handsLine(harness: string | undefined, model: string | undefined): string | undefined {
  if (harness === undefined && model === undefined) {
    return undefined;
  }
  const who = harness === undefined ? "o padrão do dev" : choiceName("hands", harness);
  const which = model === undefined ? "o modelo padrão" : choiceName("models", model);
  return `${who} · ${which}`;
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
  private readonly comment = el("textarea", { className: "retro-hand retro-lined retro-missing" });
  private readonly commentCounter = el("span", { className: "retro-counter retro-remaining" });
  /** O sistema da volta escolhido na ficha aberta (ADR-0093, decisão 12). */
  private swap = { harness: "", model: "" };
  private readonly faces: FaceCache | undefined;

  constructor(parent: HTMLElement, actions: ClipboardActions, faces?: FaceCache) {
    this.actions = actions;
    this.faces = faces;
    this.element = el("dialog", { className: "retro-clipboard-dialog" });
    this.element.setAttribute("aria-modal", "true");
    // O teclado anda com o avatar: dentro da prancheta, ele escreve.
    this.element.addEventListener("keydown", (event) => { event.stopPropagation(); });
    this.element.addEventListener("close", () => {
      this.mode = undefined;
      this.shown = "";
      this.returnTo?.focus();
    });
    this.comment.maxLength = COMMENT_MAX;
    this.comment.placeholder = "O que o dev precisa refazer, para devolver";
    this.comment.setAttribute("aria-labelledby", "retro-missing-label");
    this.comment.setAttribute("aria-describedby", "retro-missing-count");
    this.commentCounter.id = "retro-missing-count";
    this.commentCounter.setAttribute("aria-live", "polite");
    this.comment.addEventListener("input", () => {
      grow(this.comment, 3, 8);
      this.countComment();
    });
    this.countComment();
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
    this.swap = { harness: "", model: "" };
    this.countComment();
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
    const written = writtenOf(ctx.state, ctx.timeline, ticket.id);
    const key = JSON.stringify([ticket, ctx.manager, underway, ctx.art === undefined, written, this.faces?.version]);
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

  /** "faltam 412 de 1.000", sempre à vista: o campo para no limite, nunca corta escondido. */
  private countComment(): void {
    this.commentCounter.textContent = remainingOf(this.comment.value.length, COMMENT_MAX);
  }

  /** A madeira, o prendedor, a caneta e o papel com a faixa da cor do dev (ADR-0093, decisão 11).
   * Lendo uma ficha, a prancheta é maior (660 px; a do novo pedido continua com 580). */
  private board(dev: string | undefined, paper: HTMLElement[], bar: HTMLElement[], reading = false): HTMLElement {
    const clip = el("img", { className: "retro-clip-clamp" });
    clip.src = "/tela/prendedor.png";
    clip.alt = "";
    const pen = el("img", { className: "retro-clip-pen" });
    pen.src = "/tela/caneta.png";
    pen.alt = "";
    const sheet = el("div", { className: "retro-paper" }, el("div", { className: "retro-paper-stripe" }), ...paper);
    paint(sheet, this.ctx?.art, dev);
    return el("div", { className: `retro-clipboard${reading ? " read" : ""}` }, clip, pen, sheet, el("div", { className: "retro-clip-bar" }, ...bar));
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

  /** Para quem (ADR-0093, decisão 8): um dev do elenco, ou quem estiver livre; e o "Para todos",
   * que põe uma ficha para cada dev e trava o "para quem". */
  private assignees(assignee: string, everyone: boolean, onPick: (assignee: string, everyone: boolean) => void): HTMLElement | undefined {
    const devs = devsOf();
    if (devs.length === 0) {
      return undefined; // um mundo sem a lista dos devs
    }
    const select = el("select", { className: "retro-hand retro-pick" });
    select.setAttribute("aria-labelledby", "retro-assignee-label");
    fill(select, [["", "quem estiver livre"], ...devs], assignee);
    select.disabled = everyone;
    const all = el("input");
    all.type = "checkbox";
    all.checked = everyone;
    all.className = "retro-everyone-box";
    const pick = (): void => {
      select.disabled = all.checked;
      onPick(all.checked ? "" : select.value, all.checked);
    };
    select.addEventListener("change", pick);
    all.addEventListener("change", pick);
    return el(
      "div",
      { className: "retro-field retro-hands retro-assign" },
      el("div", {}, label("Para quem", "retro-assignee-label"), select),
      el("label", { className: "retro-everyone" }, all, el("span", {}, "Para todos")),
    );
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
    let harness = this.draft.harness;
    let model = this.draft.model;
    let assignee = this.draft.assignee;
    let everyone = this.draft.everyone;
    const routeLine = el("p", { className: "retro-paper-route" });
    const assign = this.assignees(assignee, everyone, (to, all) => {
      assignee = to;
      everyone = all;
      sync();
    });
    // Quem programa e o modelo (ADR-0089; ADR-0093, decisão 18): o kernel confere o par; sem
    // escolha, o padrão do dev. O modelo segue o harness.
    const models = picker("models", model, "retro-model-label", (value) => { model = value; sync(); });
    const hands = picker("hands", harness, "retro-hands-label", (value) => {
      harness = value;
      if (models !== undefined) {
        model = syncModels(models, harness, model);
      }
      sync();
    });
    if (models !== undefined) {
      model = syncModels(models, harness, model);
    }
    const paper = (): HTMLElement | null => this.element.querySelector(".retro-paper");
    const sync = (): void => {
      this.draft = { title: title.value, description: description.value, acceptance: acceptance.value, size: "M", harness, model, assignee, everyone };
      saveDraft(this.draft);
      const node = paper();
      if (node !== null) {
        paint(node, ctx.art, assignee === "" ? undefined : assignee);
      }
      routeLine.replaceChildren(
        ...routeOf(manager, assignee === "" ? undefined : devName(state, assignee), everyone),
        " A ficha entra no quadro em ",
        strong("A fazer"),
        ".",
      );
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
      // O tamanho saiu da tela (ADR-0093, decisão 11): o contrato pede um, e vai o "M".
      this.actions.write({
        title: title.value.trim(),
        description: description.value.trim(),
        acceptance: acceptance.value.trim(),
        size: "M",
        ...(harness === "" ? {} : { harness }),
        ...(model === "" ? {} : { model }),
        ...(everyone ? { everyone: true } : assignee === "" ? {} : { assignee }),
      });
      this.sent = JSON.stringify(this.draft);
      this.close();
    });
    const tickets = ticketsOf(state);
    const content = this.board(
      assignee === "" ? undefined : assignee,
      [
        this.header("Novo pedido", `#${String(nextNumber(tickets))}`, el("span", { className: "retro-paper-when" }, ctx.when)),
        routeLine,
        el("div", { className: "retro-field" }, el("div", { className: "retro-field-top" }, label("Título", "retro-title-label"), counters[0]), title),
        el("div", { className: "retro-field" }, el("div", { className: "retro-field-top" }, label("O que fazer", "retro-description-label"), counters[1]), description),
        el(
          "div",
          { className: "retro-field" },
          el("div", { className: "retro-field-top" }, label("Teste de aceite", "retro-acceptance-label", "como você vê que ficou pronto"), counters[2]),
          acceptance,
        ),
        ...(assign === undefined ? [] : [assign]),
        ...(hands === undefined || models === undefined
          ? []
          : [
              el(
                "div",
                { className: "retro-field retro-hands" },
                el("div", {}, label("Quem programa", "retro-hands-label"), hands),
                el("div", {}, label("Modelo", "retro-model-label"), models),
              ),
            ]),
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
    // O cabeçalho: "Pedido #11", o carimbo do estado e, se a tela sabe, quando foi escrito.
    const title = el("h2", { className: "retro-paper-title" }, `Pedido ${number}`);
    title.id = "retro-clip-title";
    this.element.setAttribute("aria-labelledby", title.id);
    const written = writtenOf(state, ctx.timeline, ticket.id);
    const head = el(
      "header",
      { className: "retro-paper-head" },
      el("div", {}, el("div", { className: "retro-paper-kicker" }, "Campsverso · ficha de pedido"), title),
      el(
        "div",
        { className: "retro-paper-number" },
        el("span", { className: `retro-stamp ${ticket.state}` }, stateLabel(ticket.state)),
        written === undefined ? undefined : el("span", { className: "retro-paper-when" }, written),
      ),
    );
    // De quem para quem e, à direita, com quem está.
    const owner = ticket.owner;
    const to = ticket.assignee === undefined ? undefined : devName(state, ticket.assignee);
    const route_ = el("div", { className: "retro-paper-route" }, el("p", {}, ...routeOf(from, to, ticket.group !== undefined)));
    if (owner !== undefined) {
      const face = this.faces?.url(owner);
      const pill = el("span", { className: "retro-with" });
      if (face !== undefined) {
        const picture = el("img", { className: "retro-with-face" });
        picture.src = face;
        picture.alt = "";
        pill.append(picture);
      }
      pill.append(`com ${nameOf(state, owner, "o dev")}`);
      route_.append(pill);
    }
    const paper: HTMLElement[] = [
      head,
      route_,
      el("div", { className: "retro-field" }, label("Título"), text(ticket.title, "retro-rule")),
      el("div", { className: "retro-field" }, label("O que fazer"), text(ticket.description, "retro-lined")),
      el("div", { className: "retro-field" }, label("Teste de aceite", undefined, "como você vê que ficou pronto"), text(ticket.acceptance, "retro-lined")),
    ];
    const chosen = handsLine(ticket.harness, ticket.model);
    if (chosen !== undefined) {
      paper.push(el("div", { className: "retro-field" }, label("Quem programa"), text(chosen, "retro-rule")));
    }
    if (ticket.comment !== undefined) {
      paper.push(el("p", { className: "retro-hand retro-returned" }, `Devolvido: ${ticket.comment}`));
    }
    // O PR e o patch num recorte grampeado no papel.
    const staple = this.staple(ticket, number, ctx.art);
    if (staple !== undefined) {
      paper.push(staple);
    }
    const bar: HTMLElement[] = [this.closeButton(), el("span", { className: "retro-clip-spacer" })];
    if (ctx.manager && ticket.state === "entregue" && underway) {
      bar.push(el("span", { className: "retro-clip-note" }, "O gerente está indo ao quadro."));
    } else if (ctx.manager && ticket.state === "entregue") {
      // A devolução maior (ADR-0092): o "O que falta" no papel, do tamanho do pedido. A volta pode
      // trocar quem programa (ADR-0093, decisão 12): sem escolha, o sistema de antes.
      paper.push(
        el(
          "div",
          { className: "retro-field retro-giveback" },
          el("div", { className: "retro-field-top" }, label("O que falta", "retro-missing-label", "para devolver"), this.commentCounter),
          this.comment,
        ),
      );
      const swap = this.swapper();
      if (swap !== undefined) {
        paper.push(swap.node);
      }
      const pr = ticket.pr;
      const give = el("button", { className: "retro-button retro-give" }, "Devolver");
      give.type = "button";
      give.addEventListener("click", () => {
        const comment = this.comment.value.trim();
        if (comment === "") {
          this.comment.focus();
          return;
        }
        this.actions.giveBack(ticket.id, comment, swap?.system());
        this.close();
      });
      bar.push(give);
      // Com o PR aberto, aceitar é mesclar no GitHub (ADR-0083): o quadro não aceita.
      if (pr?.state === "aberto") {
        bar.push(el("span", { className: "retro-clip-note retro-clip-merge" }, "Aceite mesclando o PR no GitHub: o quadro só acompanha."));
      } else {
        const accept = el("button", { className: "retro-take retro-put retro-accept" }, "Aceitar");
        accept.type = "button";
        accept.addEventListener("click", () => {
          this.actions.accept(ticket.id);
          this.close();
        });
        bar.push(accept);
      }
    }
    const scroll = this.element.querySelector(".retro-paper")?.scrollTop ?? 0;
    this.element.replaceChildren(this.board(ticket.assignee ?? owner, paper, bar, true));
    const sheet = this.element.querySelector(".retro-paper");
    if (sheet !== null) {
      sheet.scrollTop = scroll; // o mundo andou; o papel fica onde o gerente lia
    }
    grow(this.comment, 3, 8);
    // O desenho novo não tira o foco de quem escrevia o que falta.
    if (focused === this.comment) {
      this.comment.focus();
    } else if (this.element.open && !this.element.contains(focused)) {
      this.element.querySelector<HTMLElement>(".retro-clip-close")?.focus();
    }
  }

  /** Quem programa a volta (ADR-0093, decisão 12): o harness e o modelo, como na prancheta; vazio,
   * o sistema de antes. Guarda a escolha entre um desenho e outro, como o "O que falta". */
  private swapper(): { node: HTMLElement; system: () => System | undefined } | undefined {
    const hands = choicesOf("hands");
    if (hands.length === 0) {
      return undefined;
    }
    const harness = el("select", { className: "retro-hand retro-pick" });
    harness.setAttribute("aria-labelledby", "retro-swap-label");
    fill(harness, [["", "o mesmo de antes"], ...hands], this.swap.harness);
    const model = el("select", { className: "retro-hand retro-pick" });
    model.setAttribute("aria-labelledby", "retro-swap-model-label");
    this.swap.model = harness.value === "" ? "" : syncModels(model, harness.value, this.swap.model);
    if (harness.value === "") {
      fill(model, [["", "o de antes"]], "");
      model.disabled = true;
    }
    harness.addEventListener("change", () => {
      this.swap.harness = harness.value;
      this.swap.model = harness.value === "" ? "" : syncModels(model, harness.value, this.swap.model);
      if (harness.value === "") {
        fill(model, [["", "o de antes"]], "");
        model.disabled = true;
      }
    });
    model.addEventListener("change", () => { this.swap.model = model.value; });
    const node = el(
      "div",
      { className: "retro-field retro-hands" },
      el("div", {}, label("Quem programa a volta", "retro-swap-label"), harness),
      el("div", {}, label("Modelo", "retro-swap-model-label"), model),
    );
    const system = (): System | undefined =>
      this.swap.harness === "" ? undefined : { harness: this.swap.harness, ...(this.swap.model === "" ? {} : { model: this.swap.model }) };
    return { node, system };
  }

  /** O recorte grampeado: o selo do PR em 4x, o link para o GitHub e o "Ver o patch". */
  private staple(ticket: TicketView, number: string, art: ArtManifest | undefined): HTMLElement | undefined {
    const pr = ticket.pr;
    const ref = ticket.patch;
    const patch = ref !== undefined && (ticket.state === "entregue" || ticket.state === "aceito");
    if (pr === undefined && !patch) {
      return undefined;
    }
    const parts: HTMLElement[] = [];
    if (pr !== undefined) {
      const badge = badgeOfPullRequest(pr);
      const seal = badge === undefined ? undefined : sealOf(badge, art, 4);
      if (seal !== undefined) {
        parts.push(seal);
      }
      const line = stapleLine(pr);
      if (PR_URL.test(pr.url)) {
        const link = el("a", { className: "retro-staple-link" }, line);
        link.href = pr.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        parts.push(link, el("span", { className: "retro-staple-where" }, "no GitHub"));
      } else {
        parts.push(el("span", { className: "retro-staple-link" }, line));
      }
    }
    parts.push(el("span", { className: "retro-clip-spacer" }));
    if (patch) {
      const see = el("button", { className: "retro-button" }, "Ver o patch");
      see.type = "button";
      see.addEventListener("click", () => { this.actions.patch(`Pedido ${number}: ${ticket.title}`, ref); });
      parts.push(see);
    }
    return el("div", { className: "retro-staple" }, ...parts);
  }
}
