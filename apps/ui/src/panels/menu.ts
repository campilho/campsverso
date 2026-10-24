/** O menu do clique direito (ADR-0051): as ações do catálogo para a coisa clicada.
 *
 * Cada ação com parâmetros ganha os seus campos (uma lista de escolhas ou um número) e um botão.
 * O menu não esconde nada que o kernel aceitaria: só desabilita o que não tem o que escolher.
 */
import { button, el } from "../dom.ts";
import type { MenuEntry } from "../play.ts";

export type Choose = (entry: MenuEntry, chosen: Record<string, string | number>) => void;

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

  open(x: number, y: number, title: string, entries: readonly MenuEntry[], choose: Choose): void {
    const rows = entries.map((entry) => this.row(entry, choose));
    this.root.replaceChildren(
      el("div", { className: "menu-title" }, title),
      ...(rows.length > 0 ? rows : [el("p", { className: "hint" }, "nenhuma ação aqui")]),
      button("Fechar", () => { this.close(); }),
    );
    this.root.style.left = `${String(Math.round(x))}px`;
    this.root.style.top = `${String(Math.round(y))}px`;
    this.root.hidden = false;
  }

  private row(entry: MenuEntry, choose: Choose): HTMLElement {
    const inputs = new Map<string, HTMLInputElement | HTMLSelectElement>();
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
        const node = el("option", {}, p.names?.[option] ?? option.replace(/_/g, " "));
        node.value = option;
        select.append(node);
      }
      select.disabled = p.options.length === 0;
      inputs.set(p.name, select);
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
    return el(
      "div",
      { className: "menu-row" },
      go,
      ...fields,
      !entry.ready && el("span", { className: "hint" }, "nada para escolher"),
    );
  }
}
