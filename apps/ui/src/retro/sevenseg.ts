/** O relógio de 7 segmentos (docs/design/briefing-tela-2.md, §1; ADR-0092): a hora do mundo num
 * visor de relógio digital dos anos 90, com os dígitos da folha `tela/relogio_7seg.png`. Cada
 * célula traz os segmentos acesos e os apagados; o visor põe o fundo escuro. Os dois pontos piscam a
 * cada segundo da parede, só no CSS: o mundo não sabe disso. */
import { el } from "../dom.ts";

/** As 14 células da folha, nesta ordem, de 12 x 20 cada. */
export const SEVENSEG_CELLS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "-", " ", ":", ":apagado"] as const;
export const SEVENSEG_CELL = { width: 12, height: 20 } as const;
/** Os dois pontos usam só as 4 primeiras colunas da célula. */
export const SEVENSEG_COLON_WIDTH = 4;

const UNKNOWN = ["-", "-", ":", "-", "-"] as const;

/** A hora em células: "10:59" vira ["1", "0", ":", "5", "9"]; sem hora conhecida, "--:--". */
export function clockCells(hour: string): readonly string[] {
  const match = /^(\d)(\d):(\d)(\d)/.exec(hour);
  if (match === null) {
    return UNKNOWN;
  }
  const [, h1 = "-", h2 = "-", m1 = "-", m2 = "-"] = match;
  return [h1, h2, ":", m1, m2];
}

/** O rótulo para quem não vê o visor: a hora, ou "hora desconhecida". */
export function clockLabel(hour: string): string {
  const cells = clockCells(hour);
  return cells === UNKNOWN ? "hora desconhecida" : cells.join("");
}

/** A célula de cada dígito na folha (o índice), que o CSS multiplica pela largura e pela escala. */
export function digitCells(hour: string): readonly number[] {
  return clockCells(hour)
    .filter((cell) => cell !== ":")
    .map((cell) => Math.max(0, SEVENSEG_CELLS.indexOf(cell as (typeof SEVENSEG_CELLS)[number])));
}

export class SevenSeg {
  readonly element: HTMLElement;
  private readonly digits: HTMLElement[];
  private shown = "";

  /** `scale` 2 na barra e no painel do monitor; 1 na faixa do celular. */
  constructor(scale: 1 | 2) {
    this.digits = [0, 1, 2, 3].map(() => el("span", { className: "retro-7seg-digit" }));
    const colon = el("span", { className: "retro-7seg-colon" });
    const [a, b, c, d] = this.digits;
    this.element = el("div", { className: `retro-7seg x${String(scale)}` }, a ?? "", b ?? "", colon, c ?? "", d ?? "");
    this.element.setAttribute("role", "img");
    this.element.style.setProperty("--seg", String(scale));
    this.set("");
  }

  /** Troca os dígitos e o rótulo só quando o minuto muda, nunca no piscar. */
  set(hour: string): void {
    const cells = clockCells(hour);
    const key = cells.join("");
    if (key === this.shown) {
      return;
    }
    this.shown = key;
    const indexes = digitCells(hour);
    this.digits.forEach((node, i) => {
      node.style.setProperty("--cell", String(indexes[i] ?? SEVENSEG_CELLS.indexOf(" ")));
    });
    this.element.setAttribute("aria-label", clockLabel(hour));
  }
}
