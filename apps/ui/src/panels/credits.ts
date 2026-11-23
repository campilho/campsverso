/** Os créditos da arte (ADR-0053): o `CREDITS.csv` de cada camada, numa janela sobre a tela.
 *
 * No escritório (briefing-tela-4.md, §4), uma janela retrô: um bloco por grupo de autores, com as
 * licenças em selos e as peças como fichinhas, a frase de abertura tirada dos dados (o escritório é
 * todo desenho próprio; a fazenda vem do LPC) e as fontes da tela. As fazendas seguem com a lista. */
import { button, el } from "../dom.ts";
import { retroWindow } from "../retro/about.ts";

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

/** As fontes da tela do escritório, que vêm junto com a UI (docs/design/briefing-tela.md), todas
 * na SIL Open Font License 1.1: as que o `main.ts` importa. */
export const FONTS = [
  { name: "Pixelify Sans", authors: "Stefie Justprince", use: "os títulos e os botões" },
  { name: "Inter", authors: "Rasmus Andersson", use: "o texto" },
  { name: "JetBrains Mono", authors: "JetBrains", use: "os números, os ids e as teclas" },
  { name: "Patrick Hand", authors: "Patrick Wagesreiter", use: "a letra de mão da prancheta" },
  { name: "VT323", authors: "Peter Hull", use: "a tela do dev" }, // o terminal de fósforo verde (ADR-0092)
] as const;

/** Uma linha de um `CREDITS.csv`, com a camada de onde veio. */
export interface CreditRow {
  readonly layer: string;
  readonly file: string;
  readonly source: string;
  readonly authors: string;
  readonly licenses: string;
  readonly urls: string;
  readonly notes: string;
}

/** As linhas de um `CREDITS.csv`, pelo cabeçalho. */
export function creditRows(layer: string, text: string): CreditRow[] {
  const [header, ...rows] = parseCsv(text);
  if (header === undefined) {
    return [];
  }
  const at = (row: readonly string[], name: string): string => row[header.indexOf(name)] ?? "";
  return rows.map((row) => ({
    layer,
    file: at(row, "file"),
    source: at(row, "source"),
    authors: at(row, "authors"),
    licenses: at(row, "licenses"),
    urls: at(row, "urls"),
    notes: at(row, "notes"),
  }));
}

/** Uma peça num bloco: o arquivo e a nota dela. */
export interface CreditPiece {
  readonly file: string;
  readonly note: string;
}

/** Um bloco dos créditos: um grupo de autores com as mesmas licenças, e as peças dele. */
export interface CreditBlock {
  readonly authors: string;
  readonly licenses: readonly string[];
  readonly urls: readonly string[];
  readonly source: string;
  readonly pieces: readonly CreditPiece[];
}

function split(text: string): string[] {
  return text
    .split(/\s*,\s*/)
    .map((part) => part.trim())
    .filter((part) => part !== "");
}

/** A camada para onde uma linha "ver ..." remete: "ver cartridges/office/art/CREDITS.csv" ou "ver os
 * créditos do gênero farm". */
export function referredLayer(authors: string): string | undefined {
  if (!authors.startsWith("ver ")) {
    return undefined;
  }
  return /cartridges\/([a-z0-9_]+)\/art/.exec(authors)?.[1] ?? /gênero ([a-z0-9_]+)/.exec(authors)?.[1];
}

/** Os blocos: as linhas de todas as camadas com os mesmos autores e licenças juntas; uma linha que
 * remete a outro arquivo (o mapa visual) entra como uma peça no bloco das peças que ela monta. */
export function creditBlocks(rows: readonly CreditRow[]): CreditBlock[] {
  const blocks = new Map<string, { authors: string; licenses: string[]; urls: Set<string>; sources: Map<string, number>; pieces: CreditPiece[]; layers: Set<string> }>();
  const later: CreditRow[] = [];
  for (const row of rows) {
    if (referredLayer(row.authors) !== undefined) {
      later.push(row);
      continue;
    }
    const licenses = split(row.licenses);
    const key = `${row.authors}|${licenses.join(",")}`;
    const block = blocks.get(key) ?? { authors: row.authors, licenses, urls: new Set<string>(), sources: new Map<string, number>(), pieces: [], layers: new Set<string>() };
    block.sources.set(row.source, (block.sources.get(row.source) ?? 0) + 1);
    for (const url of split(row.urls)) {
      block.urls.add(url);
    }
    if (!block.pieces.some((piece) => piece.file === row.file)) {
      block.pieces.push({ file: row.file, note: row.notes });
    }
    block.layers.add(row.layer);
    blocks.set(key, block);
  }
  for (const row of later) {
    const layer = referredLayer(row.authors);
    const home = [...blocks.values()].find((block) => layer !== undefined && block.layers.has(layer));
    if (home !== undefined) {
      home.pieces.push({ file: row.file, note: row.source });
      continue;
    }
    blocks.set(`${row.authors}|${row.licenses}`, {
      authors: row.authors,
      licenses: split(row.licenses),
      urls: new Set(split(row.urls)),
      sources: new Map([[row.source, 1]]),
      pieces: [{ file: row.file, note: row.source }],
      layers: new Set([row.layer]),
    });
  }
  // A origem do bloco: a mais comum das linhas dele (no escritório, "desenho próprio").
  return [...blocks.values()].map((block) => ({
    authors: block.authors,
    licenses: block.licenses,
    urls: [...block.urls],
    source: [...block.sources.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? "",
    pieces: block.pieces,
  }));
}

/** A frase de abertura, dos dados: sem nada do opengameart, desenho próprio; senão, o LPC. */
export function openingOf(rows: readonly CreditRow[]): string {
  const lpc = rows.some((row) => row.urls.includes("opengameart"));
  return lpc
    ? "A arte vem do Liberated Pixel Cup (LPC) e de quem a estendeu; o que faltava foi desenhado no mesmo estilo. Cada bloco junta as peças de um mesmo grupo de autores, com as licenças."
    : "Toda a arte deste mundo é desenho próprio do Campsverso, feito em código. As fontes vêm junto com a tela.";
}

/** A cor do selo de uma licença: MIT verde, CC-BY-SA amarelo, GPL laranja, CC0 cinza, OFL azul. */
export function licenseKind(license: string): "mit" | "ccbysa" | "gpl" | "cc0" | "ofl" | "outra" {
  const text = license.toUpperCase();
  if (text.startsWith("MIT")) {
    return "mit";
  }
  if (text.startsWith("CC0")) {
    return "cc0";
  }
  if (text.startsWith("CC-BY")) {
    return "ccbysa";
  }
  if (text.startsWith("GPL")) {
    return "gpl";
  }
  return text.startsWith("OFL") || text.includes("OPEN FONT") ? "ofl" : "outra";
}

function seal(license: string): HTMLElement {
  return el("span", { className: `retro-license ${licenseKind(license)}` }, license);
}

/** Os créditos do escritório (briefing-tela-4.md, §4): a janela retrô, com "Voltar ao Sobre". */
export class RetroCredits {
  readonly element: HTMLDialogElement;
  private readonly back: () => void;

  constructor(parent: HTMLElement, back: () => void) {
    this.back = back;
    this.element = el("dialog", { className: "retro-dialog retro-credits-dialog" });
    this.element.setAttribute("aria-modal", "true");
    this.element.addEventListener("keydown", (event) => { event.stopPropagation(); });
    parent.append(this.element);
  }

  async open(credits: readonly { readonly layer: string; readonly url: string }[], world: string): Promise<void> {
    const rows: CreditRow[] = [];
    for (const { layer, url } of credits) {
      try {
        const response = await fetch(url);
        if (response.ok) {
          rows.push(...creditRows(layer, await response.text()));
        }
      } catch {
        // uma camada sem créditos não impede as outras
      }
    }
    const blocks = creditBlocks(rows);
    const pieces = blocks.reduce((sum, block) => sum + block.pieces.length, 0);
    const licenses = [...new Set(blocks.flatMap((block) => block.licenses.map((license) => license.split(" ")[0] ?? license)))];
    const icon = el("img", { className: "retro-credits-icon" });
    icon.src = "/tela/icone.png";
    icon.alt = "";
    const pill = (text: string): HTMLElement => el("span", { className: "retro-pill" }, text);
    const header = el(
      "header",
      { className: "retro-credits-head" },
      icon,
      el(
        "div",
        {},
        el("h3", {}, `Quem fez ${world}`),
        el("p", {}, openingOf(rows)),
        el(
          "div",
          { className: "retro-pills" },
          pill(`${String(pieces)} ${pieces === 1 ? "peça" : "peças"}`),
          pill(`${String(blocks.length)} ${blocks.length === 1 ? "grupo" : "grupos"} de autores`),
          pill(`${licenses.join(" · ")} ${licenses.length === 1 ? "arte" : "licenças"}`),
          pill("OFL 1.1 fontes"),
        ),
      ),
    );
    const list = blocks.map((block) => {
      const urls = block.urls.map((url) => {
        const a = el("a", {}, url.replace(/^https?:\/\//, ""));
        a.href = url;
        a.target = "_blank";
        a.rel = "noreferrer";
        return a;
      });
      const chips = block.pieces.map((piece) => el("span", { className: "retro-file", title: piece.note }, piece.file));
      const notes = block.pieces.filter((piece) => piece.note !== "");
      return el(
        "article",
        { className: "retro-credit" },
        el("div", { className: "retro-credit-head" }, el("b", {}, block.authors), el("span", { className: "retro-seals" }, ...block.licenses.map(seal))),
        el("p", { className: "retro-credit-source" }, block.source, ...(urls.length === 0 ? [] : [" · ", ...urls.flatMap((a, i) => (i === 0 ? [a] : [", ", a]))])),
        el("div", { className: "retro-files" }, ...chips),
        ...(notes.length === 0
          ? []
          : [el("details", {}, el("summary", {}, "o que cada peça é"), el("ul", {}, ...notes.map((piece) => el("li", {}, el("code", {}, piece.file), ` · ${piece.note}`))))]),
      );
    });
    const fonts = el(
      "section",
      { className: "retro-credit retro-fonts" },
      el("div", { className: "retro-credit-head" }, el("b", {}, "As fontes da tela"), el("span", { className: "retro-seals" }, seal("OFL 1.1"))),
      el(
        "div",
        { className: "retro-fonts-grid" },
        ...FONTS.map((font) => el("div", {}, el("div", {}, el("b", {}, font.name), ` · ${font.authors}`), el("div", { className: "retro-font-use" }, font.use))),
      ),
    );
    const backButton = el("button", { className: "retro-button" }, "Voltar ao Sobre");
    backButton.type = "button";
    backButton.addEventListener("click", () => {
      this.element.close();
      this.back();
    });
    const close = el("button", { className: "retro-button primary" }, "Fechar");
    close.type = "button";
    close.addEventListener("click", () => { this.element.close(); });
    const window = retroWindow(
      "Créditos",
      () => { this.element.close(); },
      header,
      el("div", { className: "retro-credits-list" }, ...list, fonts),
      el("div", { className: "retro-credits-foot" }, el("span", {}, "dos arquivos ", el("code", {}, "CREDITS.csv"), " de cada camada"), backButton, close),
    );
    window.classList.add("retro-credits-window");
    this.element.replaceChildren(window);
    this.element.setAttribute("aria-labelledby", window.getAttribute("aria-labelledby") ?? "");
    if (!this.element.open) {
      this.element.showModal();
    }
    close.focus();
  }
}

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
