/** A névoa da visão do jogador (ADR-0068): a tela mostra o que o avatar enxerga agora, o desenho
 * congelado do que ele já viu e uma nuvem sobre o que nunca viu.
 *
 * O raio da hora segue a mesma regra da percepção (o da fase, ou o da luz que o avatar carrega), e
 * um teste confere que as duas contas batem. O que foi visto fica guardado aqui, e no navegador
 * (por mundo e avatar, `FogStore`), para sobreviver a fechar e abrir a tela: o humano vê o desenho
 * de quando passou por lá, e não sabe se algo mudou.
 *
 * A tela mede a vista pela posição desenhada do avatar, que anda suave; o servidor manda as coisas
 * pela posição dele no mundo, que pode estar um pulso atrás. Na borda da vista, as duas contas
 * podem discordar por um tile ou dois. Por isso a lembrança de uma coisa só se apaga quando ela
 * está bem dentro da vista (`MARGIN` tiles longe da borda) e o servidor não a mandou: aí ela não
 * existe mais. Na borda, a lembrança fica. */
import type { ObserverEntity, ObserverState } from "@campsverso/contracts";

/** O raio que o avatar enxerga agora; `undefined` é o mapa inteiro (sem névoa). */
export function visionRadius(state: ObserverState, avatarId: string): number | undefined {
  const perception = state.session?.perception;
  if (perception === undefined || perception.radius === null) {
    return undefined;
  }
  const radius = perception.by_phase?.[state.phase] ?? perception.radius;
  const held = state.containers[avatarId] ?? {};
  const lights = Object.entries(perception.lights ?? {})
    .filter(([item]) => (held[item] ?? 0) > 0)
    .map(([, value]) => value ?? 0);
  return Math.max(radius, ...lights);
}

/** O avatar carrega uma luz (a lanterna): a tela desenha a luz quente em volta dele à noite. */
export function lightHeld(state: ObserverState, avatarId: string): boolean {
  const held = state.containers[avatarId] ?? {};
  return Object.keys(state.session?.perception?.lights ?? {}).some((item) => (held[item] ?? 0) > 0);
}

export type Sight = "visible" | "seen" | "unseen";

/** Quantos tiles da borda da vista a tela e o servidor podem discordar. */
export const MARGIN = 2;

/** O que a névoa guarda entre uma tela e outra: o tick em que foi guardada, os tiles vistos e o
 * retrato das coisas fora da vista. */
export interface FogSnapshot {
  tick: number;
  seen: string[];
  frozen: Record<string, ObserverEntity>;
}

export class FogMemory {
  private readonly seen = new Set<string>();
  private readonly frozen = new Map<string, ObserverEntity>();
  private center: { x: number; y: number } | undefined;
  private radius: number | undefined;

  /** Atualiza o que está à vista a partir do avatar em `at` (o tile em que ele aparece agora).
   * Devolve verdadeiro quando o recorte visível mudou (para redesenhar a névoa). */
  look(state: ObserverState, at: { x: number; y: number }, radius: number): boolean {
    const changed = this.center?.x !== at.x || this.center.y !== at.y || this.radius !== radius;
    this.center = { x: at.x, y: at.y };
    this.radius = radius;
    for (let y = at.y - radius; y <= at.y + radius; y++) {
      for (let x = at.x - radius; x <= at.x + radius; x++) {
        this.seen.add(`${String(x)},${String(y)}`);
      }
    }
    for (const id of [...this.frozen.keys()]) {
      const remembered = this.frozen.get(id);
      if (remembered?.position !== undefined && this.deep(remembered.position.x, remembered.position.y)) {
        this.frozen.delete(id); // bem à vista de novo: vale o que existe agora
      }
    }
    for (const [id, entity] of Object.entries(state.entities)) {
      if (entity?.position !== undefined && this.sight(entity.position.x, entity.position.y) === "visible") {
        this.frozen.set(id, entity); // o retrato de agora, para quando sair da vista
      }
    }
    return changed;
  }

  /** A borda da vista, para a passagem à névoa ser gradual sem mostrar nada além do raio: num tile
   * à vista nos dois anéis de fora, quantos tiles faltam até a borda (0 é o anel de fora) e o tile
   * logo além dela, na direção de fora; nada nos outros, nem num raio menor que 3. */
  edge(x: number, y: number): { depth: number; beyond: { x: number; y: number } } | undefined {
    const at = this.center;
    const radius = this.radius;
    if (at === undefined || radius === undefined || radius < 3) {
      return undefined;
    }
    const dx = x - at.x;
    const dy = y - at.y;
    const depth = radius - Math.max(Math.abs(dx), Math.abs(dy));
    if (depth < 0 || depth > 1) {
      return undefined;
    }
    const sx = Math.abs(dx) >= Math.abs(dy) ? Math.sign(dx) : 0;
    const sy = Math.abs(dy) >= Math.abs(dx) ? Math.sign(dy) : 0;
    return { depth, beyond: { x: x + sx * (depth + 1), y: y + sy * (depth + 1) } };
  }

  /** Bem dentro da vista, onde a tela e o servidor concordam sobre o que existe. */
  private deep(x: number, y: number): boolean {
    const at = this.center;
    const radius = this.radius;
    return at !== undefined && radius !== undefined && Math.max(Math.abs(x - at.x), Math.abs(y - at.y)) <= radius - MARGIN;
  }

  sight(x: number, y: number): Sight {
    const at = this.center;
    if (at !== undefined && this.radius !== undefined && Math.max(Math.abs(x - at.x), Math.abs(y - at.y)) <= this.radius) {
      return "visible";
    }
    return this.seen.has(`${String(x)},${String(y)}`) ? "seen" : "unseen";
  }

  /** As entidades como o jogador as vê: as à vista como são, as construções sempre, e as fora da
   * vista como foram vistas por último (congeladas); o que nunca foi visto não aparece. Na borda da
   * vista, o que o servidor ainda não mandou aparece como foi visto. */
  entities(state: ObserverState, avatarId: string): Record<string, ObserverEntity> {
    const landmarks = new Set(state.session?.perception?.landmarks ?? []);
    const shown: Record<string, ObserverEntity> = {};
    for (const [id, entity] of Object.entries(state.entities)) {
      if (entity === undefined) {
        continue;
      }
      const where = entity.position;
      if (id === avatarId || where === undefined || landmarks.has(entity.kind) || this.sight(where.x, where.y) === "visible") {
        shown[id] = entity;
      }
    }
    for (const [id, entity] of this.frozen) {
      const where = entity.position;
      if (where !== undefined && !(id in shown) && !this.deep(where.x, where.y)) {
        shown[id] = entity; // inclusive o que já não existe: o jogador não sabe
      }
    }
    return shown;
  }

  /** A lembrança para guardar no navegador, com o tick do mundo. */
  snapshot(tick: number): FogSnapshot {
    return { tick, seen: [...this.seen], frozen: Object.fromEntries(this.frozen) };
  }

  /** A lembrança guardada, de volta. */
  static restore(snapshot: FogSnapshot): FogMemory {
    const fog = new FogMemory();
    for (const key of snapshot.seen) {
      fog.seen.add(key);
    }
    for (const [id, entity] of Object.entries(snapshot.frozen)) {
      fog.frozen.set(id, entity);
    }
    return fog;
  }
}

/** A lembrança no navegador, por mundo e avatar. Uma lembrança de um tick depois do de agora é de
 * outro jogo no mesmo mundo (um sandbox novo, que recomeça no tick 0) e é esquecida; o sandbox que
 * retoma continua de onde parou. Sem armazenamento (aba privada, bloqueio), a névoa só não volta. */
export class FogStore {
  private readonly key: string;
  private readonly storage: Pick<Storage, "getItem" | "setItem" | "removeItem"> | undefined;

  constructor(key: string, storage: Pick<Storage, "getItem" | "setItem" | "removeItem"> | undefined) {
    this.key = key;
    this.storage = storage;
  }

  load(tick: number): FogMemory | undefined {
    try {
      const raw = this.storage?.getItem(this.key);
      if (raw === null || raw === undefined) {
        return undefined;
      }
      const snapshot = JSON.parse(raw) as FogSnapshot;
      if (snapshot.tick > tick) {
        this.storage?.removeItem(this.key);
        return undefined;
      }
      return FogMemory.restore(snapshot);
    } catch {
      return undefined;
    }
  }

  save(fog: FogMemory, tick: number): void {
    try {
      this.storage?.setItem(this.key, JSON.stringify(fog.snapshot(tick)));
    } catch {
      // cheio ou bloqueado: a lembrança fica só nesta tela
    }
  }
}

/** A chave da lembrança de um avatar num mundo. */
export function fogKey(worldid: string, avatarId: string): string {
  return `campsverso.fog.${worldid}.${avatarId}`;
}
