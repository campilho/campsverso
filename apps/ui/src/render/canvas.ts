/** O canvas de depuração: quadrados coloridos sobre o mapa do cartucho (escopo §6, M4).
 *
 * Desenha o estado; não decide nada. Trajetos são interpolados só para a tela (motion.ts).
 */
import type { ObserverState } from "@campsverso/contracts";

import { positionAt, type Point } from "../motion.ts";
import { progressOf } from "../progress.ts";
import { tileAt, type TileGrid } from "../tiled.ts";
import { entityColor, entityLabel, isNight, tileColor } from "./skin.ts";

export const TILE = 32;

export class MapCanvas {
  private grid: TileGrid | undefined;
  private readonly canvas: HTMLCanvasElement;
  private readonly context: CanvasRenderingContext2D;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const context = canvas.getContext("2d");
    if (context === null) {
      throw new Error("canvas 2D indisponível");
    }
    this.context = context;
  }

  setGrid(grid: TileGrid): void {
    this.grid = grid;
  }

  /** O tile sob um ponto da tela (coordenadas do evento do mouse), ou nada fora do mapa. */
  tileAt(clientX: number, clientY: number): { x: number; y: number } | undefined {
    const box = this.canvas.getBoundingClientRect();
    const x = Math.floor(((clientX - box.left) * this.canvas.width) / box.width / TILE);
    const y = Math.floor(((clientY - box.top) * this.canvas.height) / box.height / TILE);
    const inside = x >= 0 && y >= 0 && x * TILE < this.canvas.width && y * TILE < this.canvas.height;
    return inside ? { x, y } : undefined;
  }

  private resize(width: number, height: number): void {
    if (this.canvas.width !== width * TILE || this.canvas.height !== height * TILE) {
      this.canvas.width = width * TILE;
      this.canvas.height = height * TILE;
    }
  }

  draw(state: ObserverState, tick: number): void {
    const map = state.session?.map;
    const width = this.grid?.width ?? map?.width ?? 1;
    const height = this.grid?.height ?? map?.height ?? 1;
    this.resize(width, height);
    const ctx = this.context;
    ctx.fillStyle = "#111";
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    this.drawTerrain(width, height);
    this.drawThings(state);
    this.drawAvatars(state, tick);
    if (isNight(state.phase)) {
      ctx.fillStyle = "rgba(12, 18, 60, 0.38)";
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }

  private drawTerrain(width: number, height: number): void {
    const ctx = this.context;
    const grid = this.grid;
    if (grid === undefined) {
      return;
    }
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        ctx.fillStyle = tileColor(tileAt(grid, x, y));
        ctx.fillRect(x * TILE, y * TILE, TILE, TILE);
      }
    }
    ctx.strokeStyle = "rgba(0, 0, 0, 0.08)";
    ctx.lineWidth = 1;
    for (let x = 0; x <= width; x++) {
      ctx.beginPath();
      ctx.moveTo(x * TILE + 0.5, 0);
      ctx.lineTo(x * TILE + 0.5, height * TILE);
      ctx.stroke();
    }
    for (let y = 0; y <= height; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * TILE + 0.5);
      ctx.lineTo(width * TILE, y * TILE + 0.5);
      ctx.stroke();
    }
  }

  private drawThings(state: ObserverState): void {
    const ctx = this.context;
    for (const entity of Object.values(state.entities)) {
      if (entity === undefined || entity.position === undefined || entity.kind === "avatar") {
        continue;
      }
      const { x, y } = entity.position;
      const attributes = entity.attributes as Record<string, unknown>;
      ctx.fillStyle = entityColor(entity.kind, attributes);
      ctx.fillRect(x * TILE + 3, y * TILE + 3, TILE - 6, TILE - 6);
      ctx.strokeStyle = "rgba(0, 0, 0, 0.45)";
      ctx.strokeRect(x * TILE + 3.5, y * TILE + 3.5, TILE - 7, TILE - 7);
      if (attributes.watered_today === true) {
        ctx.fillStyle = "#4fc3f7";
        ctx.beginPath();
        ctx.arc(x * TILE + TILE - 7, y * TILE + 7, 3.5, 0, Math.PI * 2);
        ctx.fill();
      }
      this.label(entityLabel(entity.kind, attributes), x * TILE + TILE / 2, y * TILE + TILE / 2 + 3);
    }
  }

  private drawAvatars(state: ObserverState, tick: number): void {
    const ctx = this.context;
    for (const [id, entity] of Object.entries(state.entities)) {
      if (entity?.kind !== "avatar") {
        continue;
      }
      const motion = state.motion[id];
      const at: Point | undefined = motion === undefined ? entity.position : positionAt(motion, tick);
      if (at === undefined) {
        continue;
      }
      const cx = at.x * TILE + TILE / 2;
      const cy = at.y * TILE + TILE / 2;
      ctx.fillStyle = "#f5f5f5";
      ctx.strokeStyle = "#1b1b1b";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx, cy, TILE * 0.34, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.lineWidth = 1;
      this.label(id.slice(0, 1).toUpperCase(), cx, cy + 4, "#1b1b1b", "bold 12px");
      const progress = progressOf(state, id, tick);
      if (progress !== undefined) {
        this.tag(progress.label, cx, at.y * TILE - 8);
        if (progress.fraction !== undefined) {
          this.bar(progress.fraction, cx, at.y * TILE - 4);
        }
      }
    }
  }

  private label(text: string, x: number, y: number, color = "#fff", font = "9px"): void {
    if (text === "") {
      return;
    }
    const ctx = this.context;
    ctx.font = `${font} ui-monospace, monospace`;
    ctx.textAlign = "center";
    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
  }

  /** A barra de progresso da ação ou do sono (ADR-0052), logo abaixo do rótulo. */
  private bar(fraction: number, x: number, y: number): void {
    const ctx = this.context;
    const width = TILE - 4;
    ctx.fillStyle = "rgba(20, 20, 20, 0.8)";
    ctx.fillRect(x - width / 2 - 1, y - 1, width + 2, 6);
    ctx.fillStyle = "#7bd88f";
    ctx.fillRect(x - width / 2, y, width * fraction, 4);
  }

  private tag(text: string, x: number, y: number): void {
    const ctx = this.context;
    ctx.font = "bold 11px ui-monospace, monospace";
    const width = ctx.measureText(text).width + 8;
    ctx.fillStyle = "rgba(20, 20, 20, 0.8)";
    ctx.fillRect(x - width / 2, y - 13, width, 15);
    ctx.fillStyle = "#ffe08a";
    ctx.textAlign = "center";
    ctx.fillText(text, x, y - 2);
  }
}
