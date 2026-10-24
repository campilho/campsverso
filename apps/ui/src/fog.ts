/** A névoa da visão do jogador (ADR-0068): a tela mostra o que o avatar enxerga agora, o desenho
 * congelado do que ele já viu e uma nuvem sobre o que nunca viu.
 *
 * O raio da hora segue a mesma regra da percepção (o da fase, ou o da luz que o avatar carrega), e
 * um teste confere que as duas contas batem. O que foi visto fica guardado aqui, enquanto a tela
 * está aberta: o humano vê o desenho de quando passou por lá, e não sabe se algo mudou. */
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
      if (remembered?.position !== undefined && this.sight(remembered.position.x, remembered.position.y) === "visible") {
        this.frozen.delete(id); // à vista de novo: vale o que existe agora
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

  sight(x: number, y: number): Sight {
    const at = this.center;
    if (at !== undefined && this.radius !== undefined && Math.max(Math.abs(x - at.x), Math.abs(y - at.y)) <= this.radius) {
      return "visible";
    }
    return this.seen.has(`${String(x)},${String(y)}`) ? "seen" : "unseen";
  }

  /** As entidades como o jogador as vê: as à vista como são, as construções sempre, e as fora da
   * vista como foram vistas por último (congeladas); o que nunca foi visto não aparece. */
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
      if (where !== undefined && this.sight(where.x, where.y) !== "visible" && !(id in shown && landmarks.has(entity.kind))) {
        shown[id] = entity; // inclusive o que já não existe: o jogador não sabe
      }
    }
    return shown;
  }
}
