/** Os créditos da arte (ADR-0053): o `CREDITS.csv` de cada camada, numa janela sobre a tela. */
import { button, el } from "../dom.ts";

/** CSV simples (RFC 4180): aspas em volta de campos com vírgula, aspas dobradas dentro deles. */
export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text.charAt(i);
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') {
        field += '"';
        i++;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n" || char === "\r") {
      if (char === "\r" && text[i + 1] === "\n") {
        i++;
      }
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field !== "" || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows.filter((r) => r.some((cell) => cell !== ""));
}

export class CreditsDialog {
  readonly element: HTMLDialogElement;
  private readonly body: HTMLElement;

  constructor(parent: HTMLElement) {
    this.body = el("div", { className: "credits-body" });
    this.element = el(
      "dialog",
      { className: "credits" },
      el("header", {}, el("h2", {}, "Créditos da arte"), button("fechar", () => { this.element.close(); })),
      el("p", {}, "Pixel art do Liberated Pixel Cup (LPC) e de quem a estendeu. Cada autor está listado abaixo, com a licença de cada peça."),
      this.body,
    );
    parent.append(this.element);
  }

  async open(credits: readonly { readonly layer: string; readonly url: string }[]): Promise<void> {
    this.element.showModal();
    this.body.replaceChildren(el("p", {}, "carregando…"));
    const sections: HTMLElement[] = [];
    for (const { layer, url } of credits) {
      const response = await fetch(url);
      const [header, ...rows] = response.ok ? parseCsv(await response.text()) : [];
      if (header === undefined) {
        continue;
      }
      const link = (text: string): Node[] =>
        text.split(/,\s*/).filter(Boolean).flatMap((href, i) => {
          const a = el("a", {}, href);
          a.href = href;
          a.target = "_blank";
          a.rel = "noreferrer";
          return i === 0 ? [a] : [el("br"), a];
        });
      const column = (name: string): number => header.indexOf(name);
      sections.push(
        el(
          "section",
          {},
          el("h3", {}, layer),
          ...rows.map((row) =>
            el(
              "article",
              {},
              el("strong", {}, `${row[column("file")] ?? ""} · ${row[column("source")] ?? ""}`),
              el("p", {}, row[column("authors")] ?? ""),
              el("p", { className: "license" }, row[column("licenses")] ?? ""),
              el("p", { className: "urls" }, ...link(row[column("urls")] ?? "")),
            ),
          ),
        ),
      );
    }
    sections.push(fontsCredits());
    this.body.replaceChildren(...sections);
  }
}

/** As fontes da tela do escritório, que vêm junto com a UI (docs/design/briefing-tela.md). */
export const FONTS = [
  { name: "Pixelify Sans", authors: "Stefie Justprince" },
  { name: "Inter", authors: "Rasmus Andersson" },
  { name: "JetBrains Mono", authors: "JetBrains" },
  { name: "Patrick Hand", authors: "Patrick Wagesreiter" },
  { name: "VT323", authors: "Peter Hull" }, // a tela do dev, o terminal de fósforo verde (ADR-0092)
] as const;

function fontsCredits(): HTMLElement {
  return el(
    "section",
    {},
    el("h3", {}, "fontes da tela"),
    ...FONTS.map((font) =>
      el(
        "article",
        {},
        el("strong", {}, font.name),
        el("p", {}, font.authors),
        el("p", { className: "license" }, "SIL Open Font License 1.1"),
      ),
    ),
  );
}
