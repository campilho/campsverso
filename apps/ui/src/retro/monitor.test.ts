/** O monitor maior (docs/design/briefing-tela-2.md, §1 e §6; ADR-0092): a hora em células do relógio
 * de 7 segmentos e a escala da sala por tamanho de janela, pela tabela do briefing. */
import { describe, expect, it } from "vitest";

import { roomLayout } from "./layout.ts";
import { clockCells, clockLabel, digitCells, SEVENSEG_CELLS } from "./sevenseg.ts";

describe("o relógio de 7 segmentos", () => {
  it("a hora vira células, com os dois pontos no meio", () => {
    expect(clockCells("10:59")).toEqual(["1", "0", ":", "5", "9"]);
    expect(clockCells("07:05:42")).toEqual(["0", "7", ":", "0", "5"]); // os segundos ficam de fora
    expect(clockLabel("10:59")).toBe("10:59");
  });

  it("sem hora conhecida, --:--", () => {
    expect(clockCells("")).toEqual(["-", "-", ":", "-", "-"]);
    expect(clockCells("?")).toEqual(["-", "-", ":", "-", "-"]);
    expect(clockLabel("")).toBe("hora desconhecida");
  });

  it("cada dígito aponta a sua célula da folha", () => {
    expect(SEVENSEG_CELLS).toHaveLength(14);
    expect(digitCells("10:59")).toEqual([1, 0, 5, 9]);
    expect(digitCells("")).toEqual([10, 10, 10, 10]); // o "-", só o segmento do meio
  });
});

describe("a escala da sala no monitor maior", () => {
  // A tabela do §6: a janela, a escala, o monitor e a coluna da direita.
  it.each([
    [1288, 720, 1.09, 742, 522],
    [1456, 816, 1.28, 861, 570],
    [1728, 980, 1.6, 1066, 638],
  ])("em %i x %i, a sala em %fx", (width, height, scale, monitor, right) => {
    const layout = roomLayout(width, height);
    expect(layout.scale).toBeCloseTo(scale, 2);
    expect(Math.abs(layout.monitor - monitor)).toBeLessThan(1.5);
    expect(Math.abs(layout.right - right)).toBeLessThan(1.5);
  });

  it("numa janela larga e baixa, manda a altura; numa estreita, a coluna da direita fica com 400 px", () => {
    expect(roomLayout(2400, 816).scale).toBeCloseTo(roomLayout(1456, 816).scale, 5);
    const narrow = roomLayout(1180, 1200);
    expect(narrow.right).toBeCloseTo(400, 5);
  });

  it("numa janela muito baixa, a sala não encolhe além de 0,75x", () => {
    expect(roomLayout(1440, 400).scale).toBe(0.75);
  });
});
