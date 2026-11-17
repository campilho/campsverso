/** O "ver o patch" do gerente (ADR-0080): o que o dev entregou da oficina, antes de aceitar.
 *
 * O pedido entregue guarda a chave do patch no depósito de entregas (`patch`, no atributo do
 * pedido). O gateway serve o patch e o resumo dele, só para ler (`/content/entregas/<chave>`), e o
 * diálogo mostra os arquivos, as linhas a mais e a menos, e o diff com cada linha na sua cor. A
 * tela não decide nada: quem aceita ou devolve é o botão do quadro, e o kernel.
 */
import { button, el } from "../dom.ts";

export type DiffKind = "file" | "hunk" | "add" | "del" | "context";

export interface DiffLine {
  readonly kind: DiffKind;
  readonly text: string;
}

export interface DeliverySummary {
  readonly files: readonly string[];
  readonly added: number;
  readonly removed: number;
  readonly base?: string;
}

/** As linhas de um diff do git, cada uma com o tipo dela. */
export function diffLines(patch: string): DiffLine[] {
  return patch
    .replace(/\n$/, "")
    .split("\n")
    .map((text): DiffLine => {
      if (text.startsWith("diff --git") || text.startsWith("+++ ") || text.startsWith("--- ")) {
        return { kind: "file", text };
      }
      if (text.startsWith("@@")) {
        return { kind: "hunk", text };
      }
      if (text.startsWith("+")) {
        return { kind: "add", text };
      }
      if (text.startsWith("-")) {
        return { kind: "del", text };
      }
      return { kind: "context", text };
    });
}

/** O resumo da entrega (o `.json` ao lado do patch), ou nada se ele não tem a forma esperada. */
export function summaryOf(raw: unknown): DeliverySummary | undefined {
  if (typeof raw !== "object" || raw === null) {
    return undefined;
  }
  const r = raw as Record<string, unknown>;
  const files = Array.isArray(r.files) ? r.files.filter((f): f is string => typeof f === "string") : [];
  const added = typeof r.added === "number" ? r.added : 0;
  const removed = typeof r.removed === "number" ? r.removed : 0;
  return { files, added, removed, ...(typeof r.base === "string" ? { base: r.base } : {}) };
}

/** A chave do resumo, ao lado da do patch. */
export function summaryRef(ref: string): string {
  return ref.replace(/\.patch$/, ".json");
}

export function deliveryUrl(ref: string): string {
  return `/content/entregas/${ref.split("/").map(encodeURIComponent).join("/")}`;
}

export class DeliveryDialog {
  readonly element: HTMLDialogElement;
  private readonly title = el("h2", {});
  private readonly body = el("div", { className: "delivery-body" });

  constructor(parent: HTMLElement) {
    this.element = el(
      "dialog",
      { className: "delivery" },
      el("header", {}, this.title, button("fechar", () => { this.element.close(); })),
      this.body,
    );
    parent.append(this.element);
  }

  async open(heading: string, ref: string): Promise<void> {
    this.title.textContent = heading;
    this.element.showModal();
    this.body.replaceChildren(el("p", {}, "carregando…"));
    const [patch, summary] = await Promise.all([
      fetch(deliveryUrl(ref)).then((r) => (r.ok ? r.text() : undefined)),
      fetch(deliveryUrl(summaryRef(ref))).then((r) => (r.ok ? r.json() : undefined) as Promise<unknown>),
    ]);
    if (patch === undefined) {
      this.body.replaceChildren(el("p", {}, "O patch não está no depósito de entregas deste mundo."));
      return;
    }
    const facts = summaryOf(summary);
    const head = facts === undefined
      ? []
      : [
          el("p", { className: "delivery-counts" }, `${String(facts.files.length)} arquivo(s), +${String(facts.added)} −${String(facts.removed)}`),
          el("ul", { className: "delivery-files" }, ...facts.files.map((file) => el("li", {}, file))),
        ];
    const pre = el("pre", { className: "diff" });
    pre.append(...diffLines(patch).map((line) => el("span", { className: `diff-${line.kind}` }, `${line.text}\n`)));
    this.body.replaceChildren(...head, pre);
  }
}
