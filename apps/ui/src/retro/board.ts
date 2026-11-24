/** O quadro dos pedidos da tela retrô (docs/design/briefing-tela.md, §3.4): a moldura de madeira, o
 * cabeçalho, as quatro abas e as fichas na cortiça. Desde a ADR-0092 (briefing-tela-2.md, §7), as
 * fichas são quadradas: o número, o tamanho, o título e, embaixo, só ícones (o rosto do dono, o selo
 * do PR, "devolvido"). A ficha inteira é um botão que abre a ficha aberta, onde fica o resto, com o
 * link do PR. A ficha fantasma é o pedido que o gerente está indo escrever, até o kernel o publicar. */
import type { ObserverState } from "@campsverso/contracts";

import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";
import { choicesOf } from "../locale.ts";
import type { TicketView } from "../panels/office.ts";
import type { FaceCache } from "./faces.ts";
import { boardSummary, nextTab, pinOf, squareOf, tabsOf, type Ghost } from "./tickets.ts";

export interface BoardInput {
  readonly state: ObserverState;
  readonly tickets: readonly TicketView[];
  readonly ghosts: readonly Ghost[];
}

export class RetroBoard {
  readonly element: HTMLElement;
  private readonly summary = el("span", { className: "retro-board-summary" });
  /** O "Escrever pedido" do monitor maior (briefing-tela-2.md, §6): a moldura o põe aqui. */
  readonly writeSlot = el("div", { className: "retro-board-write" });
  private readonly tablist = el("div", { className: "retro-tabs" });
  private readonly panel = el("div", { className: "retro-cork" });
  private readonly cards = el("ul", { className: "retro-cards" });
  private readonly open: (ticketId: string) => void;
  private readonly faces: FaceCache;
  private active = "a_fazer";
  private shown = "";
  private ghostsShown = 0;
  private art: ArtManifest | undefined;
  private last: BoardInput | undefined;

  constructor(open: (ticketId: string) => void, faces: FaceCache) {
    this.open = open;
    this.faces = faces;
    this.tablist.setAttribute("role", "tablist");
    this.tablist.setAttribute("aria-label", "As colunas do quadro");
    this.panel.setAttribute("role", "tabpanel");
    this.panel.id = "retro-board-panel";
    this.panel.tabIndex = 0;
    this.panel.append(this.cards);
    this.element = el(
      "section",
      { className: "retro-board" },
      el("header", { className: "retro-board-head" }, el("h2", {}, "Quadro dos pedidos"), this.summary, this.writeSlot),
      this.tablist,
      this.panel,
    );
    this.element.setAttribute("aria-label", "Quadro dos pedidos");
  }

  setArt(art: ArtManifest): void {
    this.art = art;
    this.shown = "";
    if (this.last !== undefined) {
      this.render(this.last);
    }
  }

  /** A aba ativa só se guarda na tela. */
  select(tab: string): void {
    if (tab !== this.active) {
      this.active = tab;
      this.shown = "";
      if (this.last !== undefined) {
        this.render(this.last);
      }
    }
  }

  render(input: BoardInput): void {
    this.last = input;
    // Uma ficha fantasma nova leva o quadro para "A fazer", onde ela aparece.
    if (input.ghosts.length > this.ghostsShown) {
      this.active = "a_fazer";
    }
    this.ghostsShown = input.ghosts.length;
    const key = JSON.stringify([this.active, input.tickets, input.ghosts, this.faces.version]);
    if (key === this.shown) {
      return;
    }
    this.shown = key;
    this.summary.textContent = boardSummary(input.tickets);
    this.renderTabs(input.tickets);
    const mine = input.tickets.filter((ticket) => ticket.state === this.active).reverse(); // a mais nova em cima
    const ghosts = this.active === "a_fazer" ? input.ghosts.map((ghost) => this.ghost(ghost)) : [];
    const cards = mine.map((ticket) => this.card(ticket));
    this.cards.replaceChildren(...ghosts, ...cards);
    if (ghosts.length === 0 && cards.length === 0) {
      this.cards.append(el("li", { className: "retro-cards-empty" }, "Nenhum pedido aqui."));
    }
  }

  private renderTabs(tickets: readonly TicketView[]): void {
    const tabs = tabsOf(tickets);
    const focused = this.tablist.contains(document.activeElement);
    const buttons = tabs.map((tab, index) => {
      const selected = tab.id === this.active;
      const node = el("button", { className: "retro-tab" }, el("span", {}, tab.label), el("span", { className: "retro-tab-count" }, String(tab.count)));
      node.type = "button";
      node.id = `retro-tab-${tab.id}`;
      node.setAttribute("role", "tab");
      node.setAttribute("aria-label", `${tab.label}, ${String(tab.count)} ${tab.count === 1 ? "pedido" : "pedidos"}`);
      node.setAttribute("aria-selected", selected ? "true" : "false");
      node.setAttribute("aria-controls", this.panel.id);
      node.tabIndex = selected ? 0 : -1;
      node.addEventListener("click", () => { this.select(tab.id); });
      node.addEventListener("keydown", (event) => {
        const to = nextTab(index, event.key, tabs.length);
        if (to === undefined) {
          return;
        }
        event.preventDefault();
        event.stopPropagation(); // as setas aqui trocam a aba, não andam com o avatar
        const target = tabs[to];
        if (target !== undefined) {
          this.select(target.id);
          document.getElementById(`retro-tab-${target.id}`)?.focus();
        }
      });
      return node;
    });
    this.tablist.replaceChildren(...buttons);
    this.panel.setAttribute("aria-labelledby", `retro-tab-${this.active}`);
    if (focused) {
      document.getElementById(`retro-tab-${this.active}`)?.focus();
    }
  }

  /** A faixa na cor do dev (ADR-0093, decisão 11): da arte; sem dev, a neutra do CSS. */
  private paint(node: HTMLElement, dev: string | undefined): HTMLElement {
    const color = dev === undefined ? undefined : this.art?.avatars?.[dev]?.color;
    if (color !== undefined) {
      node.style.setProperty("--faixa", color);
    }
    return node;
  }

  private card(ticket: TicketView): HTMLElement {
    const square = squareOf(ticket, (id) => choicesOf("assignee").find(([dev]) => dev === id)?.[1] ?? id);
    const icons: HTMLElement[] = [];
    const face = square.owner === undefined ? undefined : this.faces.url(square.owner);
    if (face !== undefined) {
      const picture = el("img", { className: "retro-ficha-face" });
      picture.src = face;
      picture.alt = "";
      icons.push(picture);
    }
    const seal = square.seal === undefined ? undefined : sealOf(square.seal, this.art, 3);
    if (seal !== undefined) {
      seal.title = square.sealTitle ?? "";
      icons.push(seal);
    }
    if (square.returned) {
      icons.push(el("span", { className: "retro-hand retro-ficha-returned" }, "devolvido"));
    }
    const open = el(
      "button",
      { className: "retro-ficha-open" },
      el("span", { className: "retro-ficha-top" }, el("span", { className: "retro-ficha-no" }, square.number)),
      el("span", { className: "retro-ficha-title" }, square.title),
      el("span", { className: "retro-ficha-icons" }, ...icons),
    );
    open.type = "button";
    open.setAttribute("aria-haspopup", "dialog");
    open.setAttribute("aria-label", square.label);
    open.addEventListener("click", () => { this.open(ticket.id); });
    return this.paint(el("li", { className: "retro-ficha" }, el("i", { className: `retro-pin ${pinOf(ticket.number)}` }), open), square.dev);
  }

  private ghost(ghost: Ghost): HTMLElement {
    const card = el(
      "li",
      { className: "retro-ficha fantasma", title: "o gerente está indo ao quadro" },
      el(
        "div",
        { className: "retro-ficha-open" },
        el("span", { className: "retro-ficha-top" }, el("span", { className: "retro-ficha-no" }, "#…")),
        el("span", { className: "retro-ficha-title" }, ghost.title),
      ),
    );
    return this.paint(card, ghost.dev);
  }
}

/** O selo do PR, da folha `selos` (6 x 6), na escala dada: 3x na ficha quadrada, 4x na aberta. */
export function sealOf(badge: string, art: ArtManifest | undefined, scale: number): HTMLElement | undefined {
  const spec = art?.cards?.badge;
  const sheet = spec === undefined ? undefined : art?.sheets?.[spec.sheet];
  const frame = spec?.frames[badge];
  if (sheet === undefined || frame === undefined) {
    return undefined;
  }
  const size = 6 * scale;
  const seal = el("span", { className: "retro-seal" });
  seal.style.width = `${String(size)}px`;
  seal.style.height = `${String(size)}px`;
  seal.style.backgroundImage = `url(${sheet.image})`;
  seal.style.backgroundSize = `auto ${String(size)}px`;
  seal.style.backgroundPosition = `-${String(frame * size)}px 0`;
  return seal;
}
