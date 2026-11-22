/** O quadro dos pedidos da tela retrô (docs/design/briefing-tela.md, §3.4): a moldura de madeira, o
 * cabeçalho, as quatro abas e as fichas na cortiça. Cada ficha é um botão que abre a prancheta em
 * leitura; a pílula do PR, ao lado dele, é o link para o GitHub. A ficha fantasma é o pedido que o
 * gerente está indo escrever, até o kernel o publicar. */
import type { ObserverState } from "@campsverso/contracts";

import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";
import { PR_URL, pullRequestLine, type TicketView } from "../panels/office.ts";
import { badgeOfPullRequest, boardSummary, nextTab, pinOf, tabsOf, whoLine, type Ghost } from "./tickets.ts";

const BADGE_SCALE = 3;

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
  private active = "a_fazer";
  private shown = "";
  private ghostsShown = 0;
  private art: ArtManifest | undefined;
  private last: BoardInput | undefined;

  constructor(open: (ticketId: string) => void) {
    this.open = open;
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
    const names = input.tickets.map((t) => whoLine(t, input.state));
    const key = JSON.stringify([this.active, input.tickets, input.ghosts, names]);
    if (key === this.shown) {
      return;
    }
    this.shown = key;
    this.summary.textContent = boardSummary(input.tickets);
    this.renderTabs(input.tickets);
    const mine = input.tickets
      .map((ticket, i) => ({ ticket, who: names[i] ?? "" }))
      .filter(({ ticket }) => ticket.state === this.active)
      .reverse(); // a mais nova em cima
    const ghosts = this.active === "a_fazer" ? input.ghosts.map((ghost) => this.ghost(ghost)) : [];
    const cards = mine.map(({ ticket, who }) => this.card(ticket, who));
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

  private card(ticket: TicketView, who: string): HTMLElement {
    const number = `#${String(ticket.number)}`;
    const open = el(
      "button",
      { className: "retro-ficha-open" },
      el("span", { className: "retro-ficha-top" }, el("span", {}, number), el("span", {}, ticket.size)),
      el("span", { className: "retro-ficha-title" }, ticket.title),
      who === "" ? undefined : el("span", { className: "retro-ficha-who" }, who),
    );
    open.type = "button";
    open.setAttribute("aria-haspopup", "dialog");
    open.addEventListener("click", () => { this.open(ticket.id); });
    const item = el("li", { className: `retro-ficha tam-${ticket.size}` }, el("i", { className: `retro-pin ${pinOf(ticket.number)}` }), open);
    const pr = ticket.pr;
    if (pr !== undefined) {
      item.append(pullRequestPill(pr, this.art));
    }
    return item;
  }

  private ghost(ghost: Ghost): HTMLElement {
    return el(
      "li",
      { className: `retro-ficha fantasma tam-${ghost.size}` },
      el(
        "div",
        { className: "retro-ficha-open" },
        el("span", { className: "retro-ficha-top" }, el("span", {}, "#…"), el("span", {}, ghost.size)),
        el("span", { className: "retro-ficha-title" }, ghost.title),
        el("span", { className: "retro-ficha-who" }, "o gerente está indo ao quadro"),
      ),
    );
  }
}

/** A pílula do PR: o selo da folha `selos` em 3x e o texto de `pullRequestLine`, como link quando o
 * endereço é de um PR no GitHub. Escura com o PR aberto, azul com ele mesclado. */
export function pullRequestPill(pr: TicketView["pr"] & object, art: ArtManifest | undefined): HTMLElement {
  const line = pullRequestLine(pr);
  const badge = badgeOfPullRequest(pr);
  const parts: HTMLElement[] = [];
  const spec = art?.cards?.badge;
  const sheet = spec === undefined ? undefined : art?.sheets?.[spec.sheet];
  const frame = badge === undefined ? undefined : spec?.frames[badge];
  if (sheet !== undefined && frame !== undefined) {
    const seal = el("span", { className: "retro-seal" });
    const size = 6 * BADGE_SCALE;
    seal.style.backgroundImage = `url(${sheet.image})`;
    seal.style.backgroundSize = `auto ${String(size)}px`;
    seal.style.backgroundPosition = `-${String(frame * size)}px 0`;
    parts.push(seal);
  }
  parts.push(el("span", {}, line));
  const className = `retro-pr ${pr.state}`;
  if (PR_URL.test(pr.url)) {
    const anchor = el("a", { className }, ...parts);
    anchor.href = pr.url;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    return anchor;
  }
  return el("span", { className }, ...parts);
}
