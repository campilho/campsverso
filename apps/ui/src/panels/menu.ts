/** O menu do clique direito (ADR-0051): as ações do catálogo para a coisa clicada.
 *
 * Cada ação com parâmetros ganha os seus campos (uma lista de escolhas ou um número) e um botão.
 * O menu não esconde nada que o kernel aceitaria: só desabilita o que não tem o que escolher.
 */
import { button, el } from "../dom.ts";
import type { Contents, MenuEntry, MenuParam } from "../play.ts";

export type Choose = (entry: MenuEntry, chosen: Record<string, string | number>) => void;

/** O que o menu desenha além das ações (M21): o interior do contêiner clicado, com os ícones dos
 * itens, e o retrato de uma escolha que é um avatar (o ajudante do quadro). */
export interface MenuExtras {
  readonly contents?: Contents;
  readonly icon?: (item: string) => string | undefined;
  readonly portrait?: (option: string) => HTMLElement | undefined;
}

const CELLS = 100; // as casas do desenho de um contêiner: a capacidade, em partes iguais
const MARGIN = 8; // a distância mínima entre o menu e a borda da tela

/** O texto de uma escolha: o nome, quantas há e o preço (M21). */
export function optionText(p: MenuParam, option: string): string {
  const name = p.names?.[option] ?? option.replace(/_/g, " ");
  const count = p.counts?.[option];
  const price = p.prices?.[option];
  return [`${name}${count === undefined ? "" : ` ×${String(count)}`}`, price === undefined ? undefined : `${String(price)} moedas`]
    .filter((part) => part !== undefined)
    .join(" · ");
}

/** A cor de um item no desenho do contêiner, estável pelo nome. */
function tint(item: string): string {
  let hash = 0;
  for (const char of item) {
    hash = (hash * 31 + char.charCodeAt(0)) % 360;
  }
  return `hsl(${String(hash)} 45% 38%)`;
}

/** Um número com no máximo uma casa, em português. */
function amount(value: number): string {
  return String(Math.round(value * 10) / 10).replace(".", ",");
}

export class ActionMenu {
  private readonly root = el("div", { className: "action-menu" });

  constructor(host: HTMLElement) {
    this.root.hidden = true;
    host.append(this.root);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        this.close();
      }
    });
  }

  close(): void {
    this.root.hidden = true;
    this.root.replaceChildren();
  }

  open(x: number, y: number, title: string, entries: readonly MenuEntry[], choose: Choose, extras: MenuExtras = {}): void {
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
