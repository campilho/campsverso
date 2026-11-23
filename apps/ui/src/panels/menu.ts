/** O menu do clique direito (ADR-0051): as ações do catálogo para a coisa clicada.
 *
 * Cada ação com parâmetros ganha os seus campos (uma lista de escolhas ou um número) e um botão.
 * O menu não esconde nada que o kernel aceitaria: só desabilita o que não tem o que escolher.
 *
 * No escritório (a tela retrô, `body.retro`; briefing-tela-4.md, §2), o menu é uma janelinha colada
 * ao clique, com o rabicho apontando para ele: a barra listrada com o título, um ícone por ação, o
 * porquê do que não vale agora, o teclado (↑ ↓, Enter, shift + Enter) e o rodapé. As fazendas
 * seguem com o menu de sempre.
 */
import type { ArtManifest } from "../art/manifest.ts";
import { button, el } from "../dom.ts";
import { localName } from "../locale.ts";
import { amount, type Contents, type MenuEntry, type MenuParam } from "../play.ts";
import { actionIcon } from "../retro/icons.ts";

/** `queued`: o shift no clique ou no Enter põe a ação na fila e deixa o menu aberto. */
export type Choose = (entry: MenuEntry, chosen: Record<string, string | number>, queued?: boolean) => void;

/** O que o menu desenha além das ações (M21): o interior do contêiner clicado, com os ícones dos
 * itens, e o retrato de uma escolha que é um avatar (o ajudante do quadro). */
export interface MenuExtras {
  readonly contents?: Contents;
  readonly icon?: (item: string) => string | undefined;
  readonly portrait?: (option: string) => HTMLElement | undefined;
  /** A arte, para os ícones das ações no menu do escritório. */
  readonly art?: ArtManifest;
  /** A tela do monitor, de onde o menu do escritório nunca sai (coordenadas da página). */
  readonly bounds?: { readonly left: number; readonly top: number; readonly right: number; readonly bottom: number };
  /** Chamado quando o menu fecha: quem abriu apaga o contorno da coisa clicada. */
  readonly onClose?: () => void;
}

/** O rabicho do menu do escritório, em px. */
export const TAIL = 13;

/** Onde o menu do escritório abre (briefing-tela-4.md, §2): à direita do clique, com o rabicho
 * apontando para ele; vira para a esquerda quando não cabe; sobe quando não cabe embaixo; nunca sai
 * da tela do monitor. `tail` é a altura do rabicho dentro do menu. */
export function placeMenu(
  click: { readonly x: number; readonly y: number },
  size: { readonly width: number; readonly height: number },
  bounds: { readonly left: number; readonly top: number; readonly right: number; readonly bottom: number },
): { readonly left: number; readonly top: number; readonly side: "right" | "left"; readonly tail: number } {
  const fitsRight = click.x + TAIL + size.width <= bounds.right - MARGIN;
  const side = fitsRight || click.x - TAIL - size.width < bounds.left + MARGIN ? "right" : "left";
  const rawLeft = side === "right" ? click.x + TAIL : click.x - TAIL - size.width;
  const left = Math.max(bounds.left + MARGIN, Math.min(rawLeft, bounds.right - MARGIN - size.width));
  const rawTop = click.y - 22; // o rabicho na altura da primeira linha
  const top = Math.max(bounds.top + MARGIN, Math.min(rawTop, bounds.bottom - MARGIN - size.height));
  const tail = Math.max(12, Math.min(click.y - top, size.height - 12));
  return { left, top, side, tail };
}

const CELLS = 100; // as casas do desenho de um contêiner: a capacidade, em partes iguais
const MARGIN = 8; // a distância mínima entre o menu e a borda da tela

/** O texto de uma escolha: o nome, quantas há e o preço (M21). A contagem diz de quem é ("você tem
 * 4", "há 4 no baú"): "rabanete ×4" parecia plantar quatro vezes (achado do usuário no mapa d). */
export function optionText(p: MenuParam, option: string): string {
  const name = p.names?.[option] ?? localName(option);
  const count = p.counts?.[option];
  const price = p.prices?.[option];
  const held = count === undefined ? undefined : p.countsOf === "there" ? `há ${String(count)}` : `você tem ${String(count)}`;
  return [name, held, price === undefined ? undefined : `${String(price)} moedas`].filter((part) => part !== undefined).join(" · ");
}

/** A cor de um item no desenho do contêiner, estável pelo nome. */
function tint(item: string): string {
  let hash = 0;
  for (const char of item) {
    hash = (hash * 31 + char.charCodeAt(0)) % 360;
  }
  return `hsl(${String(hash)} 45% 38%)`;
}

export class ActionMenu {
  private readonly root = el("div", { className: "action-menu" });
  private readonly dot = el("span", { className: "retro-menu-dot" });
  private onClose: (() => void) | undefined;
  private returnTo: HTMLElement | null = null;

  constructor(host: HTMLElement) {
    this.root.hidden = true;
    this.dot.hidden = true;
    host.append(this.root, this.dot);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        this.close();
      }
    });
    // No escritório, clicar fora fecha o menu.
    document.addEventListener(
      "pointerdown",
      (event) => {
        if (!this.root.hidden && this.root.classList.contains("retro-menu") && !this.root.contains(event.target as Node | null)) {
          this.close();
        }
      },
      { capture: true },
    );
  }

  get isOpen(): boolean {
    return !this.root.hidden;
  }

  close(): void {
    const wasOpen = !this.root.hidden;
    this.root.hidden = true;
    this.dot.hidden = true;
    this.root.replaceChildren();
    const done = this.onClose;
    this.onClose = undefined;
    done?.();
    if (wasOpen && this.root.classList.contains("retro-menu")) {
      this.returnTo?.focus();
    }
    this.returnTo = null;
  }

  open(x: number, y: number, title: string, entries: readonly MenuEntry[], choose: Choose, extras: MenuExtras = {}): void {
    this.close();
    if (document.body.classList.contains("retro")) {
      this.openRetro(x, y, title, entries, choose, extras);
      return;
    }
    this.root.className = "action-menu";
    this.root.removeAttribute("role");
    const rows = entries.map((entry) => this.row(entry, choose, extras));
    this.root.replaceChildren(
      el("div", { className: "menu-title" }, title),
      ...(extras.contents === undefined ? [] : [this.contents(extras.contents, extras.icon)]),
      ...(rows.length > 0 ? rows : [el("p", { className: "hint" }, "nenhuma ação aqui")]),
      button("Fechar", () => { this.close(); }),
    );
    this.root.style.left = `${String(Math.round(x))}px`;
    this.root.style.top = `${String(Math.round(y))}px`;
    this.root.hidden = false;
    // Perto da borda, o menu sobe e vai para a esquerda até caber na tela (M21).
    const box = this.root.getBoundingClientRect();
    const over = { x: box.right - innerWidth + MARGIN, y: box.bottom - innerHeight + MARGIN };
    if (over.x > 0) {
      this.root.style.left = `${String(Math.round(Math.max(scrollX + MARGIN, x - over.x)))}px`;
    }
    if (over.y > 0) {
      this.root.style.top = `${String(Math.round(Math.max(scrollY + MARGIN, y - over.y)))}px`;
    }
  }

  /** O menu do escritório (briefing-tela-4.md, §2): a janelinha colada ao clique. */
  private openRetro(x: number, y: number, title: string, entries: readonly MenuEntry[], choose: Choose, extras: MenuExtras): void {
    this.returnTo = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    this.onClose = extras.onClose;
    this.root.className = "action-menu retro-menu";
    this.root.setAttribute("role", "menu");
    const heading = el("h2", { className: "retro-window-title" }, title);
    heading.id = "retro-menu-title";
    this.root.setAttribute("aria-labelledby", heading.id);
    const close = el("button", { className: "retro-close" });
    close.type = "button";
    close.setAttribute("aria-label", "Fechar");
    close.addEventListener("click", () => { this.close(); });
    const items = entries.map((entry) => this.retroItem(entry, choose, extras));
    const empty = items.length === 0;
    const tail = el("span", { className: "retro-menu-tail" });
    this.root.replaceChildren(
      tail,
      el("div", { className: "retro-window-bar" }, close, heading),
      el(
        "div",
        { className: "retro-menu-body" },
        ...(extras.contents === undefined ? [] : [this.retroContents(extras.contents)]),
        ...(empty ? [el("p", { className: "retro-menu-empty" }, "Nada a fazer aqui.")] : items),
      ),
      ...(empty
        ? []
        : [el("div", { className: "retro-menu-foot" }, el("span", {}, el("b", {}, "shift"), " + clique põe na fila"), el("span", {}, el("b", {}, "Esc"), " fecha"))]),
    );
    this.root.classList.toggle("small", empty);
    // O teclado do menu: ↑ ↓ entre as linhas prontas; o resto não anda com o avatar.
    this.root.onkeydown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        return; // o documento fecha
      }
      event.stopPropagation();
      if (event.key !== "ArrowDown" && event.key !== "ArrowUp") {
        return;
      }
      event.preventDefault();
      const rows = [...this.root.querySelectorAll<HTMLElement>(".retro-menu-row:not([aria-disabled='true'])")];
      const at = rows.indexOf(document.activeElement as HTMLElement);
      const next = event.key === "ArrowDown" ? (at + 1) % rows.length : (at - 1 + rows.length) % rows.length;
      rows[next]?.focus();
    };
    this.root.style.left = "0px";
    this.root.style.top = "0px";
    this.root.hidden = false;
    const box = this.root.getBoundingClientRect();
    const view = extras.bounds ?? { left: scrollX, top: scrollY, right: scrollX + innerWidth, bottom: scrollY + innerHeight };
    const place = placeMenu({ x, y }, { width: box.width, height: box.height }, view);
    this.root.style.left = `${String(Math.round(place.left))}px`;
    this.root.style.top = `${String(Math.round(place.top))}px`;
    this.root.dataset.side = place.side;
    tail.style.top = `${String(Math.round(place.tail))}px`;
    this.dot.style.left = `${String(Math.round(x))}px`;
    this.dot.style.top = `${String(Math.round(y))}px`;
    this.dot.hidden = false;
    // Ao abrir, o foco vai para a primeira linha pronta.
    (this.root.querySelector<HTMLElement>(".retro-menu-row:not([aria-disabled='true'])") ?? close).focus();
  }

  /** Uma linha do menu do escritório: o botão de 44 px com o ícone, o rótulo e o detalhe; com o que
   * escolher, um bloco com os campos embaixo, recuados. */
  private retroItem(entry: MenuEntry, choose: Choose, extras: MenuExtras): HTMLElement {
    const inputs = new Map<string, HTMLInputElement | HTMLSelectElement>();
    const fields: HTMLElement[] = [];
    for (const p of entry.params) {
      const label = el("span", { className: "retro-menu-field-label" }, p.label);
      if (p.numeric) {
        const input = el("input", { className: "retro-menu-number" });
        input.type = "number";
        input.min = String(p.minimum ?? 1);
        input.value = String(p.initial ?? p.minimum ?? 1);
        input.setAttribute("aria-label", p.label);
        inputs.set(p.name, input);
        const step = (by: number): void => {
          input.value = String(Math.max(Number(input.min), Number(input.value) + by));
        };
        const minus = button("−", () => { step(-1); });
        const plus = button("+", () => { step(1); });
        minus.setAttribute("aria-label", `menos ${p.label}`);
        plus.setAttribute("aria-label", `mais ${p.label}`);
        fields.push(el("div", { className: "retro-menu-field" }, label, el("span", { className: "retro-menu-stepper" }, minus, input, plus)));
        continue;
      }
      const select = el("select", { className: "retro-menu-select" });
      select.setAttribute("aria-label", p.label);
      for (const option of p.options) {
        const node = el("option", {}, optionText(p, option));
        node.value = option;
        select.append(node);
      }
      select.disabled = p.options.length === 0;
      inputs.set(p.name, select);
      fields.push(el("div", { className: "retro-menu-field" }, label, select));
      if (Object.keys(p.notes ?? {}).length > 0 || extras.portrait !== undefined) {
        // A ficha da escolha: o retrato de 40 px e a nota, trocados com a escolha.
        const sheet = el("div", { className: "option-sheet retro-menu-sheet" });
        const show = (): void => {
          const picture = extras.portrait?.(select.value);
          const note = p.notes?.[select.value];
          sheet.replaceChildren(...(picture === undefined ? [] : [picture]), el("span", {}, note ?? ""));
          sheet.hidden = picture === undefined && note === undefined;
        };
        select.addEventListener("change", show);
        show();
        fields.push(sheet);
      }
    }
    const blocked = !entry.ready;
    const why = entry.blocked ?? "nada para escolher";
    const row = el(
      "button",
      { className: `retro-menu-row${blocked ? " blocked" : ""}` },
      actionIcon(extras.art, entry.action, 2),
      el(
        "span",
        { className: "retro-menu-text" },
        el("span", { className: "retro-menu-label" }, entry.label),
        blocked
          ? el("span", { className: "retro-menu-why" }, why)
          : entry.detail === undefined
            ? undefined
            : el("span", { className: "retro-menu-detail" }, entry.detail),
      ),
      el("span", { className: "retro-menu-enter" }, "↵"),
    );
    row.type = "button";
    row.setAttribute("role", "menuitem");
    if (blocked) {
      row.setAttribute("aria-disabled", "true");
    }
    const go = (queued: boolean): void => {
      if (blocked) {
        return;
      }
      const chosen: Record<string, string | number> = {};
      for (const p of entry.params) {
        const input = inputs.get(p.name);
        if (input !== undefined) {
          chosen[p.name] = p.numeric ? Number(input.value) : input.value;
        }
      }
      if (!queued) {
        this.close();
      }
      choose(entry, chosen, queued);
    };
    row.addEventListener("click", (event) => { go(event.shiftKey); });
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        go(event.shiftKey);
      }
    });
    if (fields.length === 0) {
      return row;
    }
    return el("div", { className: "retro-menu-block" }, row, el("div", { className: "retro-menu-fields" }, ...fields));
  }

  /** "Dentro" no menu do escritório: a régua de 12 células e a lista, com quanto cada coisa ocupa. */
  private retroContents(contents: Contents): HTMLElement {
    const ruler = el("div", { className: "retro-menu-ruler" });
    const per = contents.capacity / 12;
    let filled = 0;
    for (const item of contents.items) {
      const cells = item.weight > 0 ? Math.max(1, Math.round(item.weight / per)) : 0;
      for (let n = 0; n < cells && filled < 12; n++, filled++) {
        const cell = el("span", { className: "used", title: `${item.name} ×${String(item.qty)}` });
        cell.style.background = tint(item.item);
        ruler.append(cell);
      }
    }
    for (; filled < 12; filled++) {
      ruler.append(el("span"));
    }
    const list = el(
      "ul",
      { className: "retro-menu-contents-list" },
      ...contents.items.map((item) => {
        const swatch = el("span", { className: "swatch" });
        swatch.style.background = tint(item.item);
        return el("li", {}, swatch, el("span", {}, `${item.name} ×${String(item.qty)}`), el("span", { className: "retro-menu-takes" }, `ocupa ${amount(item.weight)}`));
      }),
    );
    return el(
      "div",
      { className: "retro-menu-contents" },
      el("div", { className: "retro-menu-contents-head" }, el("span", {}, "Dentro"), el("span", { className: "retro-menu-takes" }, `ocupa ${amount(contents.used)} de ${amount(contents.capacity)}`)),
      ruler,
      contents.items.length === 0 ? el("p", { className: "retro-menu-empty" }, "vazio") : list,
    );
  }

  /** O interior do contêiner (M21): uma grade com a capacidade em casas, cada item ocupando as
   * suas pelo peso, e a lista com o ícone, quantos e quanto pesa. */
  private contents(contents: Contents, icon?: (item: string) => string | undefined): HTMLElement {
    const grid = el("div", { className: "contents-grid" });
    const per = contents.capacity / CELLS;
    let filled = 0;
    for (const item of contents.items) {
      const cells = item.weight > 0 ? Math.max(1, Math.round(item.weight / per)) : 0;
      for (let n = 0; n < cells && filled < CELLS; n++, filled++) {
        const cell = el("span", { className: "cell used", title: `${item.name} ×${String(item.qty)}` });
        cell.style.background = tint(item.item);
        const url = n === 0 ? icon?.(item.item) : undefined;
        if (url !== undefined) {
          const image = el("img");
          image.src = url;
          image.alt = "";
          cell.append(image);
        }
        grid.append(cell);
      }
    }
    for (; filled < CELLS; filled++) {
      grid.append(el("span", { className: "cell" }));
    }
    const list = el(
      "ul",
      { className: "contents-list" },
      ...contents.items.map((item) => {
        const url = icon?.(item.item);
        const image = el("img");
        image.alt = "";
        if (url !== undefined) {
          image.src = url;
        }
        const swatch = el("span", { className: "swatch" });
        swatch.style.background = tint(item.item);
        return el("li", {}, swatch, url === undefined ? "" : image, `${item.name} ×${String(item.qty)} · ocupa ${amount(item.weight)}`);
      }),
    );
    const empty = contents.items.length === 0 ? el("p", { className: "hint" }, "vazio") : "";
    return el(
      "div",
      { className: "contents" },
      el("div", { className: "menu-detail" }, `ocupa ${amount(contents.used)} de ${amount(contents.capacity)}`),
      grid,
      list,
      empty,
    );
  }

  private row(entry: MenuEntry, choose: Choose, extras: MenuExtras): HTMLElement {
    const inputs = new Map<string, HTMLInputElement | HTMLSelectElement>();
    const sheets: HTMLElement[] = [];
    const fields = entry.params.map((p) => {
      if (p.numeric) {
        const input = el("input");
        input.type = "number";
        input.min = String(p.minimum ?? 1);
        input.value = String(p.initial ?? p.minimum ?? 1);
        inputs.set(p.name, input);
        return el("label", {}, `${p.label} `, input);
      }
      const select = el("select");
      for (const option of p.options) {
        const node = el("option", {}, optionText(p, option));
        node.value = option;
        select.append(node);
      }
      select.disabled = p.options.length === 0;
      inputs.set(p.name, select);
      if (Object.keys(p.notes ?? {}).length > 0 || extras.portrait !== undefined) {
        // A ficha da escolha (o ajudante): o retrato e a nota, trocados com a escolha.
        const sheet = el("div", { className: "option-sheet" });
        const show = (): void => {
          const picture = extras.portrait?.(select.value);
          const note = p.notes?.[select.value];
          sheet.replaceChildren(...(picture === undefined ? [] : [picture]), el("span", {}, note ?? ""));
          sheet.hidden = picture === undefined && note === undefined;
        };
        select.addEventListener("change", show);
        show();
        sheets.push(sheet);
      }
      return el("label", {}, `${p.label} `, select);
    });
    const go = button(
      entry.label,
      () => {
        const chosen: Record<string, string | number> = {};
        for (const p of entry.params) {
          const input = inputs.get(p.name);
          if (input !== undefined) {
            chosen[p.name] = p.numeric ? Number(input.value) : input.value;
          }
        }
        this.close();
        choose(entry, chosen);
      },
      entry.ready,
    );
    const why = entry.blocked ?? "nada para escolher";
    return el(
      "div",
      { className: "menu-row" },
      go,
      ...fields,
      !entry.ready && el("span", { className: "hint" }, why),
      entry.detail !== undefined && el("span", { className: "menu-detail" }, entry.detail),
      ...sheets,
    );
  }
}
