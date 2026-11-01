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

/** O trajeto tile a tile a partir das esquinas, como a projeção o refaz (`path_from`): segmentos
 * retos em 4 direções. */
export function pathFrom(origin: Position, waypoints: readonly Position[]): ObserverMotion["path"] {
  const path: ObserverMotion["path"] = [{ x: origin.x, y: origin.y }];
  for (const corner of waypoints) {
    let { x, y } = path[path.length - 1] ?? origin;
    const dx = Math.sign(corner.x - x);
    const dy = Math.sign(corner.y - y);
    while (x !== corner.x || y !== corner.y) {
      x += dx;
      y += dy;
      path.push({ x, y });
    }
  }
  return path;
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

/** Até onde a tela já desenhou um trajeto, para respeitar o teto de velocidade. O desenho pode
 * começar por uma emenda (`offset` pontos antes do trajeto do kernel): de onde o avatar aparecia
 * até a origem do trajeto novo. */
interface Walker {
  readonly key: string;
  readonly path: readonly Point[];
  readonly offset: number;
  steps: number;
  ms: number;
}

function same(a: Point | undefined, b: Point | undefined): boolean {
  return a !== undefined && b !== undefined && a.x === b.x && a.y === b.y;
}

/** Lembra em que tick a tela viu cada trajeto pela primeira vez, e até onde já o desenhou.
 *
 * Um trajeto novo no meio de outro (um destino novo, o teclado) não salta: o desenho segue do
 * ponto em que o avatar aparecia, pelo resto do trajeto velho até a origem do novo. Se o novo
 * termina nesse caminho (parar logo depois de soltar a tecla), o desenho para ali, sem ir e voltar.
 * E um trajeto que começou e terminou entre duas atualizações da tela (a 144× e a 720×) chega pelo
 * evento (`observe`): sem ele, o avatar aparecia já no destino (achados do usuário no mapa d). */
export class MotionClock {
  private readonly seen = new Map<string, number>();
  private readonly walkers = new Map<string, Walker>();
  private readonly paces = new Map<string, number>();

  /** O ritmo do desenho de uma entidade, em tiles por segundo real (o teclado anda mais devagar
   * que o teto, para o desenho não alcançar o kernel e parar); `undefined` volta ao teto. */
  pace(id: string, tilesPerSecond: number | undefined): void {
    if (tilesPerSecond === undefined) {
      this.paces.delete(id);
    } else {
      this.paces.set(id, tilesPerSecond);
    }
  }

  /** Um trajeto que chegou pelo evento `world.entity.moved`: começa a ser desenhado mesmo que o
   * estado nunca o mostre. */
  observe(id: string, motion: ObserverMotion, nowMs: number): void {
    const key = `${id}@${String(motion.depart_tick)}`;
    if (this.walkers.get(id)?.key !== key) {
      this.start(id, key, motion.path, nowMs);
    }
  }

  /** Onde desenhar a entidade agora: no trajeto em curso ou parada em `rest`. Parada no fim de um
   * trajeto que a tela ainda não terminou de desenhar, ela termina a caminhada no ritmo do teto. */
  at(id: string, motion: ObserverMotion | undefined, rest: Point | undefined, tick: number, nowMs: number): Point | undefined {
    const walker = this.walkers.get(id);
    if (motion === undefined) {
      if (walker === undefined || rest === undefined) {
        return rest;
      }
      const last = walker.path.length - 1;
      if (walker.steps >= last || !same(walker.path[last], rest)) {
        this.walkers.delete(id);
        return rest;
      }
      walker.steps = Math.min(last, walker.steps + this.budget(id, walker, nowMs));
      walker.ms = nowMs;
      return pointAt(walker.path, walker.steps);
    }
    const key = `${id}@${String(motion.depart_tick)}`;
    const target = smoothedSteps(motion, tick, this.firstSeen(id, key, tick));
    const current = walker?.key === key ? walker : this.start(id, key, motion.path, nowMs);
    const ahead = Math.min(current.path.length - 1, target + current.offset, current.steps + this.budget(id, current, nowMs));
    current.steps = Math.max(current.steps, ahead); // o desenho nunca volta
    current.ms = nowMs;
    return pointAt(current.path, current.steps);
  }

  /** Começa o desenho de um trajeto: de onde o avatar aparece agora, sem saltar, se o desenho do
   * anterior ainda não terminou. Terminado, o avatar estava onde o kernel o pôs: o trajeto novo
   * parte da origem dele. */
  private start(id: string, key: string, path: readonly Position[], nowMs: number): Walker {
    const old = this.walkers.get(id);
    const origin = path[0];
    let prefix: Point[] = [];
    if (old !== undefined && origin !== undefined && old.steps < old.path.length - 1) {
      const drawn = pointAt(old.path, old.steps);
      if (!same(drawn, origin)) {
        const from = Math.floor(old.steps);
        const reached = old.path.findIndex((p, i) => i > from && same(p, origin));
        prefix = [drawn, ...(reached > from ? old.path.slice(from + 1, reached) : [])];
      }
    }
    const end = path[path.length - 1];
    const stop = prefix.findIndex((p) => same(p, end));
    const walker: Walker =
      stop >= 0
        ? { key, path: prefix.slice(0, stop + 1), offset: stop, steps: 0, ms: nowMs }
        : { key, path: [...prefix, ...path], offset: prefix.length, steps: 0, ms: nowMs };
    this.walkers.set(id, walker);
    return walker;
  }

  /** Quantos tiles a tela pode andar desde o último quadro, no ritmo da entidade. */
  private budget(id: string, walker: Walker, nowMs: number): number {
    return (Math.max(0, nowMs - walker.ms) * (this.paces.get(id) ?? MAX_TILES_PER_SECOND)) / 1000;
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

/** Uma só memória para quem desenha e para quem acha o avatar sob o clique. */
export const motionClock = new MotionClock();
