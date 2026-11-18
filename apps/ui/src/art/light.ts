/** A luz da noite do escritório (ADR-0082), pixel a pixel: o nível de cada pixel do mapa, 0 aceso, 1
 * penumbra e 2 escuro. A tela pinta os níveis com uma cor por cima; a prévia do Claude Design troca
 * as cores da paleta, e as bordas em xadrez das poças e da lanterna são as mesmas.
 *
 * Função pura do manifesto, do modo da hora e de onde está a lanterna: testável sem o Phaser.
 */
import type { LightMode, Lights } from "./manifest.ts";

const TILE = 32;
/** A luz é um pouco achatada na vertical, como na prévia: a sala vista de cima e de frente. */
const SQUASH = 1.15;

export const LIT = 0;
export const PENUMBRA = 1;
export const DARK = 2;

/** Os níveis de luz de um mapa de `width` × `height` pixels, linha a linha; de dia, nenhum (tudo
 * aceso). `lantern` é o centro da lanterna em pixels, quando quem a leva está no mapa. */
export function lightLevels(
  lights: Lights | undefined,
  mode: LightMode,
  width: number,
  height: number,
  lantern?: { readonly x: number; readonly y: number },
): Uint8Array | undefined {
  if (lights === undefined || mode === "day" || width <= 0 || height <= 0) {
    return undefined;
  }
  const levels = new Uint8Array(width * height);
  if (mode === "lamps") {
    levels.fill(PENUMBRA);
    const radius = lights.lamp_radius ?? 72;
    const border = lights.lamp_border ?? 14;
    for (const [tx, ty] of lights.lamps ?? []) {
      pool(levels, width, height, tx * TILE, ty * TILE, radius + border, (d, checker) =>
        d < radius ? LIT : d < radius + border ? (checker ? PENUMBRA : LIT) : undefined,
      );
    }
  } else {
    levels.fill(DARK);
    const radii = lights.lantern?.radii ?? [];
    const [r0, r1, r2, r3] = [radii[0] ?? 0, radii[1] ?? 0, radii[2] ?? 0, radii[3] ?? 0];
    if (lantern !== undefined && r3 > 0) {
      pool(levels, width, height, lantern.x, lantern.y, r3, (d, checker) =>
        d < r0
          ? LIT
          : d < r1
            ? checker
              ? PENUMBRA
              : LIT
            : d < r2
              ? PENUMBRA
              : d < r3
                ? checker
                  ? DARK
                  : PENUMBRA
                : undefined,
      );
    }
  }
  for (const rect of lights.dim ?? []) {
    eachPixel(rect, width, height, (i) => {
      if ((levels[i] ?? DARK) > PENUMBRA) {
        levels[i] = PENUMBRA;
      }
    });
  }
  for (const rect of lights.lit ?? []) {
    eachPixel(rect, width, height, (i) => {
      levels[i] = LIT;
    });
  }
  return levels;
}

/** Cada pixel de um retângulo, dentro do mapa, pelo índice na linha a linha. */
function eachPixel(
  rect: { readonly x: number; readonly y: number; readonly w: number; readonly h: number },
  width: number,
  height: number,
  visit: (index: number) => void,
): void {
  const x0 = Math.max(0, Math.floor(rect.x));
  const x1 = Math.min(width, Math.ceil(rect.x + rect.w));
  for (let y = Math.max(0, Math.floor(rect.y)); y < Math.min(height, Math.ceil(rect.y + rect.h)); y++) {
    for (let x = x0; x < x1; x++) {
      visit(y * width + x);
    }
  }
}

/** Acende em volta de (cx, cy), até `reach` pixels (o resto do mapa nem é olhado): `level` dá o
 * nível pela distância e pelo xadrez do pixel, ou nada fora do alcance; vale o mais aceso de tudo o
 * que ilumina o pixel. */
function pool(
  levels: Uint8Array,
  width: number,
  height: number,
  cx: number,
  cy: number,
  reach: number,
  level: (distance: number, checker: boolean) => number | undefined,
): void {
  const x0 = Math.max(0, Math.floor(cx - reach));
  const x1 = Math.min(width, Math.ceil(cx + reach));
  const y0 = Math.max(0, Math.floor(cy - reach / SQUASH));
  const y1 = Math.min(height, Math.ceil(cy + reach / SQUASH));
  for (let y = y0; y < y1; y++) {
    const dy = (y - cy) * SQUASH;
    for (let x = x0; x < x1; x++) {
      const value = level(Math.hypot(x - cx, dy), ((x + y) & 1) === 1);
      const i = y * width + x;
      if (value !== undefined && value < (levels[i] ?? DARK)) {
        levels[i] = value;
      }
    }
  }
}
