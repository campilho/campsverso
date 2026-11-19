/** As caixas de texto da sala (o pedido de arte de 18/nov): a fonte pixel do Claude Design e as
 * molduras em nove fatias (a etiqueta escura e o balão de fala).
 *
 * A medida e a quebra das linhas são funções puras da fonte, testáveis sem o navegador; o desenho
 * monta cada caixa num canvas 2D, pixel a pixel, para sair igual no WebGL e no Canvas e com as
 * cores exatas da paleta.
 */
import type { BitmapFont, TextFrame } from "./manifest.ts";

/** Os caracteres que a fonte não tem e o que vai no lugar. */
const STAND_INS: Readonly<Record<string, string>> = {
  "—": "–",
  "‘": "'",
  "’": "'",
  "“": '"',
  "”": '"',
  "«": '"',
  "»": '"',
  "\u00a0": " ",
  "·": "-",
};

/** O índice do glifo de um caractere: o próprio, o substituto, a letra sem o acento ou o "?". */
export function glyphIndex(font: BitmapFont, char: string): number {
  const direct = font.glyphs.indexOf(char);
  if (direct >= 0) {
    return direct;
  }
  const stand = STAND_INS[char];
  if (stand !== undefined && font.glyphs.includes(stand)) {
    return font.glyphs.indexOf(stand);
  }
  const bare = char.normalize("NFD").replace(/[̀-ͯ]/g, "");
  if (bare !== "" && bare !== char && font.glyphs.includes(bare)) {
    return font.glyphs.indexOf(bare);
  }
  return Math.max(0, font.glyphs.indexOf("?"));
}

/** A largura do texto em pixels, com o respiro entre as letras. */
export function textWidth(font: BitmapFont, text: string): number {
  const chars = Array.from(text);
  const glyphs = chars.reduce((sum, char) => sum + (font.widths[glyphIndex(font, char)] ?? 0), 0);
  return glyphs + Math.max(0, chars.length - 1) * font.spacing;
}

/** Corta uma palavra comprida demais para uma linha. */
function split(font: BitmapFont, word: string, width: number): string[] {
  const pieces: string[] = [];
  let piece = "";
  for (const char of word) {
    if (piece !== "" && textWidth(font, piece + char) > width) {
      pieces.push(piece);
      piece = "";
    }
    piece += char;
  }
  return piece === "" ? pieces : [...pieces, piece];
}

/** Quebra o texto em linhas de até `width` pixels, no máximo `lines`; o que sobra vira "…". */
export function wrapText(font: BitmapFont, text: string, width: number, lines: number): string[] {
  const words = text.trim().split(/\s+/).filter((w) => w !== "").flatMap((w) => split(font, w, width));
  const out: string[] = [];
  let line = "";
  for (const word of words) {
    const next = line === "" ? word : `${line} ${word}`;
    if (line !== "" && textWidth(font, next) > width) {
      out.push(line);
      line = word;
    } else {
      line = next;
    }
  }
  if (line !== "") {
    out.push(line);
  }
  if (out.length <= lines) {
    return out;
  }
  const kept = out.slice(0, lines);
  let last = kept[lines - 1] ?? "";
  while (last !== "" && textWidth(font, `${last}…`) > width) {
    last = Array.from(last).slice(0, -1).join("").trimEnd();
  }
  kept[lines - 1] = `${last}…`;
  return kept;
}

export interface BoxSize {
  readonly width: number;
  readonly height: number;
}

/** O tamanho da moldura com as linhas dentro (sem a ponta): nunca menor que as nove fatias. */
export function boxSize(font: BitmapFont, frame: TextFrame, lines: readonly string[]): BoxSize {
  const [mx, my] = frame.margin;
  const text = Math.max(0, ...lines.map((l) => textWidth(font, l)));
  const height = lines.length === 0 ? 0 : (lines.length - 1) * frame.line + font.cell[1];
  return {
    width: Math.max(2 * frame.slice, text + 2 * mx),
    height: Math.max(2 * frame.slice, height + 2 * my),
  };
}

/** O lugar de cada glifo na folha da fonte: [x, y, largura, altura]. */
export function glyphRect(font: BitmapFont, index: number): readonly [number, number, number, number] {
  const [cw, ch] = font.cell;
  return [(index % font.columns) * cw, Math.floor(index / font.columns) * ch, font.widths[index] ?? 0, ch];
}

/** A folha da fonte tingida de uma cor: o branco vira a cor, a transparência fica. */
export function tint(source: CanvasImageSource, width: number, height: number, color: string): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (context !== null) {
    context.imageSmoothingEnabled = false;
    context.drawImage(source, 0, 0);
    context.globalCompositeOperation = "source-in";
    context.fillStyle = color;
    context.fillRect(0, 0, width, height);
  }
  return canvas;
}

/** Desenha a moldura em nove fatias, as linhas e, no balão de fala, a ponta embaixo, no meio.
 * Devolve o canvas e onde fica o bico (a âncora), em pixels do canvas. */
export function drawBox(
  sheet: CanvasImageSource,
  glyphs: CanvasImageSource,
  font: BitmapFont,
  frame: TextFrame,
  lines: readonly string[],
): { readonly canvas: HTMLCanvasElement; readonly anchor: readonly [number, number] } {
  const size = boxSize(font, frame, lines);
  const tail = frame.tail;
  const extra = tail === undefined ? 0 : tail.rect[3] - tail.rise;
  const canvas = document.createElement("canvas");
  canvas.width = size.width;
  canvas.height = size.height + extra;
  const context = canvas.getContext("2d");
  const center = Math.floor(size.width / 2);
  if (context === null) {
    return { canvas, anchor: [center, canvas.height] };
  }
  context.imageSmoothingEnabled = false;
  const [fx, fy, fw, fh] = frame.rect;
  const s = frame.slice;
  const cols: readonly [number, number, number, number][] = [
    [fx, s, 0, s],
    [fx + s, fw - 2 * s, s, size.width - 2 * s],
    [fx + fw - s, s, size.width - s, s],
  ];
  const rows: readonly [number, number, number, number][] = [
    [fy, s, 0, s],
    [fy + s, fh - 2 * s, s, size.height - 2 * s],
    [fy + fh - s, s, size.height - s, s],
  ];
  for (const [sy, sh, dy, dh] of rows) {
    for (const [sx, sw, dx, dw] of cols) {
      if (dw > 0 && dh > 0) {
        context.drawImage(sheet, sx, sy, sw, sh, dx, dy, dw, dh);
      }
    }
  }
  let anchor: readonly [number, number] = [center, size.height];
  if (tail !== undefined) {
    const [tx, ty, tw, th] = tail.rect;
    const left = center - Math.floor(tw / 2);
    const top = size.height - tail.rise;
    context.drawImage(sheet, tx, ty, tw, th, left, top, tw, th);
    anchor = [left + tail.tip[0], top + tail.tip[1]];
  }
  const [mx, my] = frame.margin;
  lines.forEach((line, row) => {
    let x = mx;
    const y = my + row * frame.line;
    for (const char of line) {
      const [gx, gy, gw, gh] = glyphRect(font, glyphIndex(font, char));
      if (gw > 0) {
        context.drawImage(glyphs, gx, gy, gw, gh, x, y, gw, gh);
      }
      x += gw + font.spacing;
    }
  });
  return { canvas, anchor };
}
