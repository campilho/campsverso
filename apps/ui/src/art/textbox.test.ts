import { describe, expect, it } from "vitest";

import type { BitmapFont, TextFrame } from "./manifest.ts";
import { boxSize, glyphIndex, glyphRect, textWidth, wrapText } from "./textbox.ts";

// Uma fonte pequena, no formato da do Claude Design: célula de 8 × 12, 4 colunas, 1 px entre letras.
const FONT: BitmapFont = {
  sheet: "fonte",
  cell: [8, 12],
  columns: 4,
  spacing: 1,
  glyphs: " abcdeno?'…",
  widths: [3, 5, 5, 4, 5, 4, 5, 5, 4, 1, 5],
};
const LABEL: TextFrame = { rect: [48, 0, 24, 24], slice: 8, color: "#f4ead0", margin: [4, 2], line: 11, lines: 1 };

describe("as caixas de texto da sala (o pedido de arte de 18/nov)", () => {
  it("cada caractere acha o seu glifo, um substituto, a letra sem acento ou o ponto de interrogação", () => {
    expect(glyphIndex(FONT, "b")).toBe(2);
    expect(glyphIndex(FONT, "’")).toBe(FONT.glyphs.indexOf("'"));
    expect(glyphIndex({ ...FONT, glyphs: " abcdeno?-…" }, "·")).toBe(9); // o ponto do meio vira hífen
    expect(glyphIndex(FONT, "ã")).toBe(FONT.glyphs.indexOf("a"));
    expect(glyphIndex(FONT, "z")).toBe(FONT.glyphs.indexOf("?"));
  });

  it("a largura soma os glifos e o respiro entre eles; o glifo sai da sua célula", () => {
    expect(textWidth(FONT, "ab")).toBe(5 + 1 + 5);
    expect(textWidth(FONT, "")).toBe(0);
    expect(glyphRect(FONT, 5)).toEqual([8, 12, 4, 12]); // a 6ª célula: coluna 1, linha 1
  });

  it("quebra nas palavras, corta a palavra longa demais e põe reticências no que não cabe", () => {
    expect(wrapText(FONT, "abc abc", 40, 3)).toEqual(["abc abc"]); // 31 px de glifos + 6 respiros = 37
    expect(wrapText(FONT, "abc abc abc", 40, 3)).toEqual(["abc abc", "abc"]);
    expect(wrapText(FONT, "aaaaaaaa", 20, 3)).toEqual(["aaa", "aaa", "aa"]); // 3 letras = 17 px
    const cut = wrapText(FONT, "abc abc abc abc abc", 40, 2);
    expect(cut).toHaveLength(2);
    expect(cut[1]?.endsWith("…")).toBe(true);
    expect(textWidth(FONT, cut[1] ?? "")).toBeLessThanOrEqual(40);
  });

  it("a moldura cerca o texto com a margem, e nunca é menor que as nove fatias", () => {
    expect(boxSize(FONT, LABEL, ["abc abc"])).toEqual({ width: 37 + 8, height: 12 + 4 });
    expect(boxSize(FONT, LABEL, ["a"])).toEqual({ width: 16, height: 16 });
    expect(boxSize(FONT, { ...LABEL, lines: 3 }, ["abc", "abc"])).toEqual({ width: 24, height: 11 + 12 + 4 });
  });
});
