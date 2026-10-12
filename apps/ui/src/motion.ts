/** Onde uma entidade está no meio de um trajeto: interpolação para desenhar, nunca regra (escopo §9). */
import type { ObserverMotion, Position } from "@campsverso/contracts";

export interface Point {
  readonly x: number;
  readonly y: number;
}

/** Posição contínua (em tiles) no tick dado; `tick` pode ser fracionário. */
export function positionAt(motion: ObserverMotion, tick: number): Point {
  const path: readonly Position[] = motion.path;
  const steps = Math.max(0, (tick - motion.depart_tick) * motion.tiles_per_tick);
  const last = path.length - 1;
  if (steps >= last) {
    const end = path[last] ?? { x: 0, y: 0 };
    return { x: end.x, y: end.y };
  }
  const index = Math.floor(steps);
  const from = path[index] ?? { x: 0, y: 0 };
  const to = path[index + 1] ?? from;
  const t = steps - index;
  return { x: from.x + (to.x - from.x) * t, y: from.y + (to.y - from.y) * t };
}
