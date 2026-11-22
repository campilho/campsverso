/** O minimapa do celular (docs/design/briefing-tela.md, §4): no canto do monitor, a sala inteira em
 * miniatura, com as pessoas e o retângulo do que a câmera mostra. Desenhado da grade lógica e das
 * cores dos tiles do manifesto, sem abrir o mapa visual. */
import type { ObserverState } from "@campsverso/contracts";

import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";
import { tileAt, type TileGrid } from "../tiled.ts";

const CELL = 4;

export interface ViewRect {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

export class Minimap {
  readonly element: HTMLCanvasElement;
  private shown = "";

  constructor() {
    this.element = el("canvas", { className: "retro-minimap" });
    this.element.setAttribute("aria-hidden", "true"); // o retrato da sala, para os olhos; a sala já se lê
  }

  draw(grid: TileGrid | undefined, art: ArtManifest | undefined, state: ObserverState, me: string, view: ViewRect | undefined): void {
    if (grid === undefined) {
      return;
    }
    const people = Object.entries(state.entities)
      .filter(([, e]) => e?.kind === "avatar" && e.position !== undefined)
      .map(([id, e]) => [id, e?.position?.x ?? 0, e?.position?.y ?? 0] as const);
    const key = JSON.stringify([grid.width, grid.height, art === undefined, people, view === undefined ? [] : [view.x, view.y, view.width, view.height].map((n) => Math.round(n * 4))]);
    if (key === this.shown) {
      return;
    }
    this.shown = key;
    const canvas = this.element;
    canvas.width = grid.width * CELL;
    canvas.height = grid.height * CELL;
    const context = canvas.getContext("2d");
    if (context === null) {
      return;
    }
    for (let y = 0; y < grid.height; y++) {
      for (let x = 0; x < grid.width; x++) {
        context.fillStyle = art?.tiles?.[tileAt(grid, x, y)]?.color ?? "#26222f";
        context.fillRect(x * CELL, y * CELL, CELL, CELL);
      }
    }
    for (const [id, x, y] of people) {
      context.fillStyle = id === me ? "#f2c94c" : "#f6f2e8";
      context.fillRect(x * CELL, y * CELL, CELL, CELL);
    }
    if (view !== undefined) {
      context.strokeStyle = "#f2c94c";
      context.lineWidth = 2;
      context.strokeRect(view.x * CELL + 1, view.y * CELL + 1, Math.max(2, view.width * CELL - 2), Math.max(2, view.height * CELL - 2));
    }
  }
}
