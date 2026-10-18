/** Onde uma entidade está no meio de um trajeto: interpolação para desenhar, nunca regra (escopo §9). */
import type { ObserverMotion, Position } from "@campsverso/contracts";

export interface Point {
  readonly x: number;
  readonly y: number;
}

/** Teto do desenho, em tiles por segundo real (ADR-0057).
 *
 * A 30 tiles por minuto simulado, o 72× daria 36 tiles por segundo na tela: um pulo. Acima do teto, a
 * tela fica para trás do kernel e o alcança em seguida, inclusive depois de o trajeto terminar. A 1× e a
 * 6× o teto nunca é atingido. É só desenho: o kernel não espera nem adianta nada.
 */
export const MAX_TILES_PER_SECOND = 12;

/** Quantos tiles do trajeto já foram andados no tick dado (fracionário), limitado ao fim. */
export function stepsAt(motion: ObserverMotion, tick: number): number {
  const last = motion.path.length - 1;
  return Math.min(last, Math.max(0, (tick - motion.depart_tick) * motion.tiles_per_tick));
}

/** O ponto do trajeto a `steps` tiles da origem. */
export function pointAt(path: readonly Position[], steps: number): Point {
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

/** Posição contínua (em tiles) no tick dado; `tick` pode ser fracionário. */
export function positionAt(motion: ObserverMotion, tick: number): Point {
  return pointAt(motion.path, stepsAt(motion, tick));
}

/** Quando o trajeto chega à tela, o kernel já o começou: a caminhada aparece um pouco adiantada.
 *
 * Para não pular tiles, a tela começa o desenho da origem no tick em que viu o trajeto e alcança o
 * tempo do kernel até a chegada, andando um pouco mais depressa. Na chegada, os dois coincidem.
 * É só desenho: o kernel não espera nem adianta nada (escopo §9).
 */
export function smoothedSteps(motion: ObserverMotion, tick: number, seenTick: number): number {
  const lag = Math.max(0, seenTick - motion.depart_tick);
  const arrival = motion.depart_tick + (motion.path.length - 1) / motion.tiles_per_tick;
  // Visto já na segunda metade (a página abriu no meio da caminhada): sem volta à origem.
  if (lag === 0 || tick >= arrival || lag > (arrival - motion.depart_tick) / 2) {
    return stepsAt(motion, tick);
  }
  const caught = Math.min(1, Math.max(0, (tick - seenTick) / (arrival - seenTick)));
  return stepsAt(motion, tick - lag * (1 - caught));
}

export function smoothedAt(motion: ObserverMotion, tick: number, seenTick: number): Point {
  return pointAt(motion.path, smoothedSteps(motion, tick, seenTick));
}

/** Até onde a tela já desenhou um trajeto, para respeitar o teto de velocidade. */
interface Walker {
  readonly key: string;
  readonly path: readonly Position[];
  steps: number;
  ms: number;
}

/** Lembra em que tick a tela viu cada trajeto pela primeira vez, e até onde já o desenhou. */
export class MotionClock {
  private readonly seen = new Map<string, number>();
  private readonly walkers = new Map<string, Walker>();

  /** Onde desenhar a entidade agora: no trajeto em curso ou parada em `rest`. Parada no fim de um
   * trajeto que a tela ainda não terminou de desenhar, ela termina a caminhada no ritmo do teto. */
  at(id: string, motion: ObserverMotion | undefined, rest: Point | undefined, tick: number, nowMs: number): Point | undefined {
    const walker = this.walkers.get(id);
    if (motion === undefined) {
      if (walker === undefined || rest === undefined) {
        return rest;
      }
      const last = walker.path.length - 1;
      const end = walker.path[last];
      if (end === undefined || walker.steps >= last || end.x !== rest.x || end.y !== rest.y) {
        this.walkers.delete(id);
        return rest;
      }
      walker.steps = Math.min(last, walker.steps + budget(walker, nowMs));
      walker.ms = nowMs;
      return pointAt(walker.path, walker.steps);
    }
    const key = `${id}@${String(motion.depart_tick)}`;
    const target = smoothedSteps(motion, tick, this.firstSeen(id, key, tick));
    if (walker !== undefined && walker.key === key) {
      walker.steps = Math.min(target, walker.steps + budget(walker, nowMs));
      walker.ms = nowMs;
      return pointAt(motion.path, walker.steps);
    }
    // Trajeto novo: o desenho parte da origem, mesmo que o kernel já esteja adiante.
    this.walkers.set(id, { key, path: motion.path, steps: 0, ms: nowMs });
    return pointAt(motion.path, 0);
  }

  private firstSeen(id: string, key: string, tick: number): number {
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
    return first;
  }
}

/** Quantos tiles a tela pode andar desde o último quadro, no teto. */
function budget(walker: Walker, nowMs: number): number {
  return (Math.max(0, nowMs - walker.ms) * MAX_TILES_PER_SECOND) / 1000;
}

/** Uma só memória para quem desenha e para quem acha o avatar sob o clique. */
export const motionClock = new MotionClock();
