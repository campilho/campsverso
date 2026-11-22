/** Onde uma entidade está no meio de um trajeto: interpolação para desenhar, nunca regra (escopo §9).
 *
 * O desenho segue o tempo do trajeto que o kernel publicou (ADR-0078, decisão 14): a posição sai do
 * tick de saída, do passo e do relógio da tela. Quando o kernel corrige (um destino novo, uma
 * interrupção, uma reconexão), a tela não salta: anda pelo caminho até onde o kernel diz e o alcança
 * depressa. Só um lugar longe do caminho (entrar no mundo, uma reconexão) reposiciona o avatar de
 * uma vez. É só desenho: o kernel não espera nem adianta nada.
 *
 * Antes (ADR-0057) havia um teto de 12 tiles por segundo: acelerado, o desenho ficava para trás, o
 * atraso se acumulava de um trajeto para o outro, e o avatar saltava para o destino quando o trajeto
 * acabava (o pulo que o usuário viu). Agora o desenho anda na velocidade do kernel, que é a verdade.
 */
import type { ObserverMotion, Position } from "@campsverso/contracts";

export interface Point {
  readonly x: number;
  readonly y: number;
}

/** Em quanto tempo real a tela desfaz a maior parte de um atraso (constante de tempo, em ms). */
export const CATCH_MS = 200;
/** A menor velocidade com que a tela desfaz um atraso, em tiles por segundo real. */
export const CATCH_TILES_PER_SECOND = 4;
/** Fora do caminho, acima desta distância a tela reposiciona o avatar de uma vez, em vez de andar
 * até lá (entrar no mundo, uma reconexão longe). Pelo caminho, o atraso sempre se desfaz andando. */
export const SNAP_TILES = 16;
/** O quanto a tela acompanha o kernel num quadro, no máximo; o resto vira atraso, desfeito depressa.
 * A 720× o kernel anda uns 6 tiles por quadro; um salto do relógio da tela anda muito mais. */
export const FOLLOW_TILES_PER_FRAME = 8;
/** O maior intervalo entre dois quadros que conta para andar: a aba em segundo plano não acumula. */
export const MAX_FRAME_MS = 50;
/** Quantos começos de caminho a tela lembra por entidade, para explicar um desenho que voltou. */
export const TRACE_KEPT = 40;

/** Um caminho que a tela começou a desenhar: por quê, de onde o desenho estava e para onde. */
export interface MotionTrace {
  readonly ms: number;
  readonly tick: number | undefined;
  readonly key: string;
  /** "trajeto": um `motion` novo do kernel; "parada": o kernel pôs a entidade noutro lugar. */
  readonly why: "trajeto" | "parada";
  readonly drawn: Point | undefined;
  readonly origin: Point;
  readonly end: Point | undefined;
  /** O desenho já estava no caminho novo, à frente da origem (o atalho do vaivém, ADR-0081). */
  readonly ahead: number | undefined;
  /** Os pontos da emenda, de onde o desenho estava até a origem do caminho novo. */
  readonly prefix: readonly Point[];
}

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
 * retos em 4 direções. Um segmento torto (a emenda de um desenho que perdeu o trajeto, de (6,7) a
 * (5,5)) vira um L, primeiro em x, depois em y. Antes, um passo em diagonal passava da esquina e o
 * laço não acabava: a aba enchia a memória e caía (a partida do usuário no escritório, M23). */
export function pathFrom(origin: Position, waypoints: readonly Position[]): ObserverMotion["path"] {
  const path: ObserverMotion["path"] = [{ x: origin.x, y: origin.y }];
  for (const corner of waypoints) {
    let { x, y } = path[path.length - 1] ?? origin;
    while (x !== corner.x) {
      x += Math.sign(corner.x - x);
      path.push({ x, y });
    }
    while (y !== corner.y) {
      y += Math.sign(corner.y - y);
      path.push({ x, y });
    }
  }
  return path;
}

/** Posição contínua (em tiles) no tick dado; `tick` pode ser fracionário. */
export function positionAt(motion: ObserverMotion, tick: number): Point {
  return pointAt(motion.path, stepsAt(motion, tick));
}

/** A chave de um trajeto: a ação que o pôs em marcha. Dois trajetos que saem no mesmo tick (a
 * tecla segurada, cliques rápidos) são dois trajetos. Sem a ação (um estado antigo), a saída e o
 * destino. */
export function motionKey(motion: ObserverMotion): string {
  if (motion.action_id !== undefined) {
    return `ação ${motion.action_id}`;
  }
  const end = motion.path[motion.path.length - 1];
  return `${String(motion.depart_tick)} → ${String(end?.x)},${String(end?.y)}`;
}

function same(a: Point | undefined, b: Point | undefined): boolean {
  return a !== undefined && b !== undefined && a.x === b.x && a.y === b.y;
}

function distance(a: Point, b: Point): number {
  return Math.hypot(b.x - a.x, b.y - a.y);
}

/** Quantos tiles da origem o ponto `p` está, se ele fica no caminho depois da origem: no meio de um
 * trecho ou em cima de um tile; nada se ele não está no caminho. Os trechos são retos, de um tile,
 * em 4 direções. Em cima de um tile conta: a parada da seta solta prende o desenho exatamente no
 * tile, e o kernel, na virada do tile de trás, parte dele; sem contar, o desenho voltava ao tile de
 * trás e andava de novo (o vaivém do teste do navegador, ADR-0081). */
function along(path: readonly Position[], p: Point): number | undefined {
  for (let i = 0; i + 1 < path.length; i++) {
    const a = path[i];
    const b = path[i + 1];
    if (a === undefined || b === undefined) {
      continue;
    }
    const t = a.x === b.x ? (p.y - a.y) / (b.y - a.y) : (p.x - a.x) / (b.x - a.x);
    const onLine = a.x === b.x ? Math.abs(p.x - a.x) < 1e-9 : Math.abs(p.y - a.y) < 1e-9;
    if (onLine && t > 1e-9 && t < 1 + 1e-9) {
      return t > 1 - 1e-9 ? i + 1 : i + t;
    }
  }
  return undefined;
}

/** Uma linha de pontos medida pelo comprimento, para andar por ela com passos fracionários. */
class Route {
  readonly points: readonly Point[];
  private readonly lengths: readonly number[];

  constructor(points: readonly Point[]) {
    const kept: Point[] = [];
    for (const point of points) {
      if (!same(kept[kept.length - 1], point)) {
        kept.push({ x: point.x, y: point.y });
      }
    }
    this.points = kept.length > 0 ? kept : [{ x: 0, y: 0 }];
    const lengths = [0];
    for (let i = 1; i < this.points.length; i++) {
      const a = this.points[i - 1];
      const b = this.points[i];
      lengths.push((lengths[i - 1] ?? 0) + (a === undefined || b === undefined ? 0 : distance(a, b)));
    }
    this.lengths = lengths;
  }

  get length(): number {
    return this.lengths[this.lengths.length - 1] ?? 0;
  }

  get end(): Point {
    return this.points[this.points.length - 1] ?? { x: 0, y: 0 };
  }

  /** O ponto a `s` tiles do começo, pelo caminho. */
  at(s: number): Point {
    if (s <= 0) {
      return this.points[0] ?? { x: 0, y: 0 };
    }
    for (let i = 1; i < this.points.length; i++) {
      const until = this.lengths[i] ?? 0;
      if (s <= until) {
        const from = this.points[i - 1] ?? { x: 0, y: 0 };
        const to = this.points[i] ?? from;
        const start = this.lengths[i - 1] ?? 0;
        const t = until > start ? (s - start) / (until - start) : 1;
        return { x: from.x + (to.x - from.x) * t, y: from.y + (to.y - from.y) * t };
      }
    }
    return this.end;
  }

  /** O comprimento até o ponto `p` do caminho mais perto de `near`, ou nada se ele não está nele. */
  find(p: Point, near: number): number | undefined {
    let best: number | undefined;
    this.points.forEach((point, i) => {
      const at = this.lengths[i] ?? 0;
      if (same(point, p) && (best === undefined || Math.abs(at - near) < Math.abs(best - near))) {
        best = at;
      }
    });
    return best;
  }

  /** Os pontos do caminho de `from` a `to`, nessa ordem: para a frente ou para trás. */
  between(from: number, to: number): Point[] {
    const points = [this.at(from)];
    const forward = to >= from;
    const inside = this.points
      .map((point, i) => ({ point, at: this.lengths[i] ?? 0 }))
      .filter(({ at }) => (forward ? at > from && at < to : at < from && at > to));
    for (const { point } of forward ? inside : inside.reverse()) {
      points.push(point);
    }
    points.push(this.at(to));
    return points;
  }
}

/** Um caminho sendo desenhado: a emenda de onde o avatar aparecia, e o trajeto do kernel. */
interface Walker {
  readonly key: string;
  readonly route: Route;
  /** Onde o trajeto do kernel começa no caminho, em tiles. */
  readonly offset: number;
  /** O trajeto do kernel, que dá o tempo; sem ele, o desenho só alcança o fim do caminho. */
  readonly motion: ObserverMotion | undefined;
  /** Até onde o desenho já andou, em tiles; nunca volta. */
  steps: number;
  /** O último quadro, no relógio da página; nunca volta. */
  ms: number;
  /** Onde o kernel estava no quadro anterior, para saber quanto ele andou neste. */
  goal: number | undefined;
}

/** Lembra, para uma tela, onde cada avatar aparece e o caminho que o desenho está fazendo.
 *
 * Cada tela tem o seu (a página, cada miniatura da arena): numa memória só, as miniaturas, todas
 * com o avatar `camps`, emendavam o desenho de uma corrida no da outra. */
export class MotionClock {
  private readonly walkers = new Map<string, Walker>();
  private readonly paces = new Map<string, number>();
  private readonly drawnAt = new Map<string, Point>();
  private readonly limits = new Map<string, { readonly tile: Point; readonly forMs: number; untilMs?: number }>();
  private readonly traces = new Map<string, MotionTrace[]>();
  private tick: number | undefined;

  /** Os últimos caminhos que a tela começou para uma entidade, do mais antigo ao mais novo. */
  trace(id: string): readonly MotionTrace[] {
    return this.traces.get(id) ?? [];
  }

  /** Até onde o desenho pode ir pelo caminho de agora: o tile da parada que a seta solta mandou
   * (ADR-0081). Até o kernel responder, o trajeto velho segue no estado, e o relógio da tela o
   * desenhava além da parada; quando a parada chegava, o desenho voltava. Vale até chegar um
   * trajeto que termina ali, ou por `forMs` no relógio dos quadros. */
  limit(id: string, tile: Point, forMs: number): void {
    this.limits.set(id, { tile: { x: tile.x, y: tile.y }, forMs });
  }

  /** O ritmo do desenho de uma entidade, em tiles por segundo real. O teclado anda mais devagar
   * que o kernel, de propósito, para o desenho não alcançá-lo e parar (ADR-0057); `undefined`
   * volta a seguir o kernel. */
  pace(id: string, tilesPerSecond: number | undefined): void {
    if (tilesPerSecond === undefined) {
      this.paces.delete(id);
    } else {
      this.paces.set(id, tilesPerSecond);
    }
  }

  /** Onde a entidade apareceu no último quadro desenhado, sem andar nada. */
  drawn(id: string): Point | undefined {
    return this.drawnAt.get(id);
  }

  /** Um trajeto que chegou pelo evento `world.entity.moved`: começa a ser desenhado mesmo que o
   * estado nunca o mostre (começou e terminou entre duas atualizações, a 144× e a 720×). */
  observe(id: string, motion: ObserverMotion, nowMs: number): void {
    const key = motionKey(motion);
    if (this.walkers.get(id)?.key !== key) {
      this.begin(id, key, motion.path, motion, nowMs);
    }
  }

  /** Onde desenhar a entidade agora: no trajeto em curso, ou parada em `rest`, onde o kernel a pôs. */
  at(id: string, motion: ObserverMotion | undefined, rest: Point | undefined, tick: number, nowMs: number): Point | undefined {
    this.tick = tick;
    if (motion === undefined && rest === undefined) {
      this.forget(id); // saiu do mundo
      return undefined;
    }
    let walker = this.walkers.get(id);
    if (motion !== undefined) {
      const key = motionKey(motion);
      if (walker?.key !== key) {
        walker = this.begin(id, key, motion.path, motion, nowMs);
      }
    } else if (rest !== undefined && !same(walker?.route.end ?? this.drawnAt.get(id), rest)) {
      // O kernel pôs a entidade noutro lugar: um trajeto interrompido, outra ação, a reconexão.
      walker = this.drawnAt.has(id) ? this.begin(id, `parada ${String(rest.x)},${String(rest.y)}`, [rest], undefined, nowMs) : undefined;
    }
    if (walker === undefined) {
      return this.remember(id, rest);
    }
    let goal = Math.min(walker.route.length, walker.motion === undefined ? walker.route.length : walker.offset + stepsAt(walker.motion, tick));
    const limit = this.limits.get(id);
    if (limit !== undefined) {
      limit.untilMs ??= nowMs + limit.forMs;
    }
    if (limit?.untilMs !== undefined && nowMs > limit.untilMs) {
      this.limits.delete(id);
    } else if (limit !== undefined) {
      const at = walker.route.find(limit.tile, walker.steps);
      if (at !== undefined) {
        goal = Math.min(goal, at);
      }
    }
    const point = this.remember(id, this.advance(id, walker, goal, nowMs));
    if (motion === undefined && walker.steps >= walker.route.length) {
      this.walkers.delete(id); // chegou onde o kernel o pôs
    }
    return point;
  }

  private forget(id: string): void {
    this.walkers.delete(id);
    this.drawnAt.delete(id);
  }

  private remember(id: string, point: Point | undefined): Point | undefined {
    if (point === undefined) {
      this.drawnAt.delete(id);
    } else {
      this.drawnAt.set(id, point);
    }
    return point;
  }

  /** Anda o desenho para `goal`: no ritmo do kernel, e desfazendo depressa o que estiver atrasado. */
  private advance(id: string, walker: Walker, goal: number, nowMs: number): Point {
    const dt = Math.min(MAX_FRAME_MS, Math.max(0, nowMs - walker.ms));
    walker.ms = Math.max(walker.ms, nowMs);
    const walked = walker.goal === undefined ? 0 : Math.min(FOLLOW_TILES_PER_FRAME, Math.max(0, goal - walker.goal));
    walker.goal = goal;
    const lag = goal - walker.steps;
    if (lag > 0) {
      const pace = this.paces.get(id);
      if (pace !== undefined) {
        walker.steps += Math.min(lag, (pace * dt) / 1000);
      } else {
        const catchUp = Math.max(lag * (1 - Math.exp(-dt / CATCH_MS)), (CATCH_TILES_PER_SECOND * dt) / 1000);
        walker.steps += Math.min(lag, Math.max(walked, catchUp));
      }
    }
    return walker.route.at(walker.steps);
  }

  /** Começa a desenhar um caminho a partir de onde a entidade aparece agora: pelo caminho velho até
   * a origem do novo, para a frente ou para trás; perto, em linha reta; longe, de uma vez. */
  private begin(id: string, key: string, path: readonly Position[], motion: ObserverMotion | undefined, nowMs: number): Walker {
    const old = this.walkers.get(id);
    const drawn = old === undefined ? this.drawnAt.get(id) : old.route.at(old.steps);
    const origin = path[0] ?? drawn ?? { x: 0, y: 0 };
    const end = path[path.length - 1];
    const limit = this.limits.get(id);
    if (limit !== undefined && same(limit.tile, end)) {
      this.limits.delete(id); // a parada chegou
    }
    // O desenho já está no caminho novo, à frente da origem: o relógio da tela andou o trajeto
    // velho um pouco além do tick em que o kernel trocou de destino, ou o limite da parada o
    // prendeu no tile dela. O desenho espera o kernel passar por ele, em vez de voltar até a
    // origem e andar de novo (o vaivém a 1×, ADR-0081).
    const ahead = drawn === undefined || same(drawn, origin) ? undefined : along(path, drawn);
    if (drawn !== undefined && ahead !== undefined && motion !== undefined) {
      const walker: Walker = {
        key,
        route: new Route([drawn, ...path.slice(Math.floor(ahead) + 1)]),
        offset: -ahead,
        motion,
        steps: 0,
        ms: old?.ms ?? nowMs,
        goal: undefined,
      };
      this.walkers.set(id, walker);
      this.note(id, { ms: nowMs, tick: this.tick, key, why: "trajeto", drawn, origin, end, ahead, prefix: [] });
      return walker;
    }
    let prefix: Point[] = [];
    if (drawn !== undefined && !same(drawn, origin)) {
      const found = old?.route.find(origin, old.steps);
      if (old !== undefined && found !== undefined) {
        prefix = old.route.between(old.steps, found);
      } else if (distance(drawn, origin) <= SNAP_TILES) {
        prefix = [drawn, ...pathFrom({ x: Math.round(drawn.x), y: Math.round(drawn.y) }, [origin])];
      }
    }
    // O destino novo já está na emenda (soltar a seta logo depois): o desenho para ali, sem ir e voltar.
    const stop = prefix.findIndex((point, i) => i > 0 && same(point, end));
    const route = new Route(stop >= 0 ? prefix.slice(0, stop + 1) : [...prefix, ...path]);
    const walker: Walker = {
      key,
      route,
      offset: stop >= 0 ? route.length : new Route([...prefix, origin]).length,
      motion: stop >= 0 ? undefined : motion,
      steps: 0,
      ms: old?.ms ?? nowMs,
      goal: undefined,
    };
    this.walkers.set(id, walker);
    this.note(id, { ms: nowMs, tick: this.tick, key, why: motion === undefined ? "parada" : "trajeto", drawn, origin, end, ahead, prefix });
    return walker;
  }

  private note(id: string, entry: MotionTrace): void {
    const list = this.traces.get(id) ?? [];
    list.push(entry);
    list.splice(0, Math.max(0, list.length - TRACE_KEPT));
    this.traces.set(id, list);
  }
}
