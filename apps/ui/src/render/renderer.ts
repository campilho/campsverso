/** O que a tela espera de quem desenha o mundo: o canvas de depuração ou o Phaser (ADR-0053). */
import type { ObserverState } from "@campsverso/contracts";

import type { ArtManifest } from "../art/manifest.ts";
import type { TileGrid } from "../tiled.ts";

export interface WorldRenderer {
  /** O elemento que vai na página e recebe os cliques. */
  readonly element: HTMLElement;
  setGrid(grid: TileGrid): void;
  setArt(art: ArtManifest): void;
  /** Desenha o estado no tick mostrado (fracionário); a tela chama a cada quadro. */
  draw(state: ObserverState, tick: number): void;
  /** O tile sob um ponto da tela (coordenadas do evento do mouse), ou nada fora do mapa. */
  tileAt(clientX: number, clientY: number): { x: number; y: number } | undefined;
}

/** A conta comum: ponto da tela → tile, num canvas com `size` pixels por tile. */
export function tileUnder(canvas: HTMLCanvasElement, size: number, clientX: number, clientY: number): { x: number; y: number } | undefined {
  const box = canvas.getBoundingClientRect();
  if (box.width === 0 || box.height === 0) {
    return undefined;
  }
  const x = Math.floor(((clientX - box.left) * canvas.width) / box.width / size);
  const y = Math.floor(((clientY - box.top) * canvas.height) / box.height / size);
  const inside = x >= 0 && y >= 0 && x * size < canvas.width && y * size < canvas.height;
  return inside ? { x, y } : undefined;
}
