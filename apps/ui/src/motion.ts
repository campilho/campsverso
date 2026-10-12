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

/** Quando o trajeto chega à tela, o kernel já o começou: a caminhada aparece um pouco adiantada.
 *
 * Para não pular tiles, a tela começa o desenho da origem no tick em que viu o trajeto e alcança o
 * tempo do kernel até a chegada, andando um pouco mais depressa. Na chegada, os dois coincidem.
 * É só desenho: o kernel não espera nem adianta nada (escopo §9).
 */
export function smoothedAt(motion: ObserverMotion, tick: number, seenTick: number): Point {
  const lag = Math.max(0, seenTick - motion.depart_tick);
  const arrival = motion.depart_tick + (motion.path.length - 1) / motion.tiles_per_tick;
  // Visto já na segunda metade (a página abriu no meio da caminhada): sem volta à origem.
  if (lag === 0 || tick >= arrival || lag > (arrival - motion.depart_tick) / 2) {
    return positionAt(motion, tick);
  }
  const caught = Math.min(1, Math.max(0, (tick - seenTick) / (arrival - seenTick)));
  return positionAt(motion, tick - lag * (1 - caught));
}

/** Lembra em que tick a tela viu cada trajeto pela primeira vez (por entidade e partida). */
export class MotionClock {
  private readonly seen = new Map<string, number>();

  at(id: string, motion: ObserverMotion, tick: number): Point {
    const key = `${id}@${String(motion.depart_tick)}`;
    let first = this.seen.get(key);
    if (first === undefined) {
      first = tick;
      this.seen.set(key, first);
      for (const old of this.seen.keys()) {
        if (old.startsWith(`${id}@`) && old !== key) {
          this.seen.delete(old);
        }
      }
    }
    return smoothedAt(motion, tick, first);
  }
}

/** Uma só memória para quem desenha e para quem acha o avatar sob o clique. */
export const motionClock = new MotionClock();
