/** O retrato dos chips e da conversa (ADR-0092; briefing-tela-2.md, §2): o busto da folha de
 * retratos, pela coluna de cada um, e a volta ao recorte do sprite sem ele. */
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

import type { ArtManifest } from "../art/manifest.ts";
import { faceCell, faceSheet } from "./portrait.ts";

const OFFICE = JSON.parse(
  readFileSync(new URL("../../../../cartridges/office_campsverso/art/art.json", import.meta.url), "utf-8"),
) as ArtManifest;
const SHEET = { width: 512, height: 1856 } as HTMLImageElement; // 8 colunas de 64 px

describe("o retrato pelo busto da folha de retratos", () => {
  it("o Tiago, o Camps de blazer e o vigia: a coluna de cada um, com a linha do piscar", () => {
    expect(faceSheet(OFFICE, "tiago")).toBe("retratos.png");
    expect(faceCell(OFFICE, "tiago", SHEET)).toEqual({ sx: 4 * 40, sy: 0, size: 40, blinkDy: 40 });
    expect(faceCell(OFFICE, "gerente", SHEET)).toEqual({ sx: 1 * 40, sy: 0, size: 40, blinkDy: 40 });
    expect(faceCell(OFFICE, "vigia", SHEET)).toEqual({ sx: 3 * 40, sy: 0, size: 40, blinkDy: 40 });
  });

  it("sem o busto, o recorte do quadro do sprite, sem piscar", () => {
    const art: ArtManifest = {
      sheets: { camps: { image: "camps.png", frame_width: 64, frame_height: 64 } },
      avatars: { camps: { sheet: "camps", portrait: { frame: 48, x: 16, y: 14, size: 32 } } },
    } as unknown as ArtManifest;
    expect(faceSheet(art, "camps")).toBe("camps.png");
    // O quadro 48 numa folha de 8 colunas: a coluna 0 da linha 6.
    expect(faceCell(art, "camps", SHEET)).toEqual({ sx: 16, sy: 6 * 64 + 14, size: 32 });
  });

  it("um avatar sem retrato nenhum fica sem", () => {
    const art = { sheets: {}, avatars: { robo: { sheet: "robo" } } } as unknown as ArtManifest;
    expect(faceSheet(art, "robo")).toBeUndefined();
    expect(faceCell(art, "robo", SHEET)).toBeUndefined();
  });
});
