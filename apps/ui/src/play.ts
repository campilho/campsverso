/** Jogar pela tela (M5; ADR-0051): o que um clique propõe e o que o menu oferece.
 *
 * Tudo aqui é sugestão montada com o estado e o catálogo de ações do cartucho (`session.affordances`).
 * Quem decide é o kernel: uma proposta pode ser recusada, e a recusa aparece na tela.
 */
import type { Affordance, ObserverState } from "@campsverso/contracts";

export interface Proposal {
  readonly avatar_id: string;
  readonly action: string;
  readonly params: Record<string, unknown>;
}

export interface MenuParam {
  readonly name: string;
  readonly label: string;
  /** Escolhas que valem agora; vazio num parâmetro de escolha: não há o que escolher. */
  readonly options: readonly string[];
  readonly numeric: boolean;
  readonly minimum?: number;
  readonly initial?: number;
  /** O nome de cada escolha que é uma entidade (o pedido do quadro, ADR-0069). */
  readonly names?: Readonly<Record<string, string>>;
  /** O preço de cada escolha que tem preço: o de agora, que o alvo mostra, ou o de tabela (M21). */
  readonly prices?: Readonly<Record<string, number>>;
}

/** Um tile do mapa, no lugar de uma entidade (o menu da grama; ADR-0068). */
export interface Tile {
  readonly x: number;
  readonly y: number;
}

export interface MenuEntry {
  readonly action: string;
  readonly label: string;
  /** A entidade clicada, ou o tile vazio (no menu do terreno). */
  readonly target?: string | Tile;
  readonly params: readonly MenuParam[];
  /** Todo parâmetro de escolha tem ao menos uma opção. */
  readonly ready: boolean;
  /** O que a ação custa, a nota do cartucho (o horário) e se o alvo está aberto agora (M21). */
  readonly detail?: string;
}

/** O avatar está com um humano? Na v0.1, o único humano é quem está no browser. */
export function inControl(state: ObserverState, avatarId: string): boolean {
  return state.controllers[avatarId]?.type === "human";
}

function stock(state: ObserverState, containerId: string | undefined): Readonly<Record<string, number | undefined>> {
  return containerId === undefined ? {} : (state.containers[containerId] ?? {});
}

/** As entidades guardadas num contêiner (as ferramentas no inventário ou no baú), pelo id. */
function heldBy(state: ObserverState, containerId: string | undefined): string[] {
  return Object.entries(state.entities)
    .filter(([, e]) => containerId !== undefined && e?.container_id === containerId)
    .map(([id]) => id)
    .sort();
}

function param(state: ObserverState, avatarId: string, target: string | undefined, raw: NonNullable<Affordance["params"]>[number]): MenuParam {
  const choices = raw.choices ?? [];
  if (choices.length === 0 && raw.entities !== true) {
    return {
      name: raw.name,
      label: raw.label,
      options: [],
      numeric: true,
      ...(raw.minimum === undefined ? {} : { minimum: raw.minimum }),
      ...(raw.default === undefined ? {} : { initial: raw.default }),
    };
  }
  const from = raw.source === "inventory" ? avatarId : raw.source === "target" ? target : undefined;
  const have = stock(state, from);
  const shown = target === undefined ? undefined : state.entities[target]?.attributes;
  const today = raw.stock_attribute === undefined ? undefined : shown?.[raw.stock_attribute];
  const sold = typeof today === "string" ? new Set(today.split(",").map((c) => c.trim())) : undefined;
  const items = (from === undefined ? choices : choices.filter((c) => (have[c] ?? 0) > 0)).filter((c) => sold?.has(c) ?? true);
  const held = raw.entities === true ? heldBy(state, from) : [];
  const names = Object.fromEntries(
    held.flatMap((id) => {
      const shown = state.entities[id]?.display_name;
      return shown === undefined ? [] : [[id, shown]];
    }),
  );
  const prices: Record<string, number> = {};
  for (const item of items) {
    const now = raw.price_attribute === undefined ? undefined : shown?.[`${raw.price_attribute}${item}`];
    const price = typeof now === "number" ? now : raw.prices?.[item];
    if (price !== undefined) {
      prices[item] = price;
    }
  }
  return { name: raw.name, label: raw.label, options: [...items, ...held], numeric: false, names, prices };
}

/** A energia com no máximo uma casa, em português (1,5). */
function amount(value: number): string {
  return String(Math.round(value * 10) / 10).replace(".", ",");
}

/** A linha de baixo de uma ação no menu: o custo, a nota e se o alvo está aberto agora (M21). */
export function detailOf(state: ObserverState, affordance: Affordance, target: string | undefined): string | undefined {
  const parts: string[] = [];
  const cost = affordance.cost;
  if (cost !== undefined && cost.energy > 0) {
    parts.push(`${amount(cost.energy)} de energia`);
  }
  if (cost !== undefined && cost.minutes >= 2) {
    parts.push(`${String(cost.minutes)} min`);
  }
  const open = target === undefined ? undefined : state.entities[target]?.attributes.open;
  if (typeof open === "boolean") {
    parts.push(open ? "aberto agora" : "fechado agora");
  }
  if (affordance.note !== undefined) {
    parts.push(affordance.note);
  }
  return parts.length === 0 ? undefined : parts.join(" · ");
}

/** O menu de uma entidade, ou do próprio avatar (`self`), a partir do catálogo do cartucho. */
export function menuFor(state: ObserverState, avatarId: string, clicked: string): MenuEntry[] {
  const kind = clicked === "self" ? "self" : state.entities[clicked]?.kind;
  if (kind === undefined) {
    return [];
  }
  const target = clicked === "self" ? undefined : clicked;
  return (state.session?.affordances ?? [])
    .filter((a) => a.on.includes(kind))
    .map((a) => {
      const params = (a.params ?? []).map((p) => param(state, avatarId, target, p));
      const detail = detailOf(state, a, target);
      return {
        action: a.action,
        label: a.label,
        ...(a.target && target !== undefined ? { target } : {}),
        params,
        ready: params.every((p) => p.numeric || p.options.length > 0),
        ...(detail === undefined ? {} : { detail }),
      };
    });
}

/** O menu de um tile vazio: as ações declaradas para o terreno dele (`grass`), com o tile no
 * `target`, as que têm o que escolher; e, primeiro, andar até lá (ADR-0068). */
export function tileMenu(state: ObserverState, avatarId: string, tile: Tile, terrain: string): MenuEntry[] {
  const entries = (state.session?.affordances ?? [])
    .filter((a) => terrain !== "" && a.on.includes(terrain))
    .map((a) => {
      const params = (a.params ?? []).map((p) => param(state, avatarId, undefined, p));
      const detail = detailOf(state, a, undefined);
      return {
        action: a.action,
        label: a.label,
        ...(a.target ? { target: { x: tile.x, y: tile.y } } : {}),
        params,
        ready: params.every((p) => p.numeric || p.options.length > 0),
        ...(detail === undefined ? {} : { detail }),
      };
    })
    .filter((entry) => entry.ready);
  const walk: MenuEntry = { action: "move", label: "Andar até aqui", target: { x: tile.x, y: tile.y }, params: [], ready: true };
  return entries.length === 0 ? [] : [walk, ...entries];
}

/** O passo até o lado do alvo de uma ação, se o avatar estiver longe dele: `move {near}`. */
export function approach(state: ObserverState, avatarId: string, target: string | Tile | undefined): Proposal | undefined {
  const me = state.entities[avatarId]?.position;
  const spot = typeof target === "string" ? state.entities[target]?.position : target;
  if (me === undefined || spot === undefined || Math.max(Math.abs(me.x - spot.x), Math.abs(me.y - spot.y)) <= 1) {
    return undefined;
  }
  return { avatar_id: avatarId, action: "move", params: { near: typeof target === "string" ? target : { x: spot.x, y: spot.y } } };
}

export function proposal(avatarId: string, entry: MenuEntry, chosen: Readonly<Record<string, string | number>>): Proposal {
  return {
    avatar_id: avatarId,
    action: entry.action,
    params: { ...(entry.target === undefined ? {} : { target: entry.target }), ...chosen },
  };
}

/** A entidade desenhada no tile (não conta o que está dentro de um contêiner nem os avatares). */
export function thingAt(state: ObserverState, x: number, y: number): string | undefined {
  return Object.entries(state.entities)
    .filter(([, e]) => e !== undefined && e.kind !== "avatar" && e.position?.x === x && e.position.y === y)
    .map(([id]) => id)
    .sort()[0];
}

/** Clique esquerdo: andar até o tile, ou até perto da coisa que está nele. */
export function walkTo(state: ObserverState, avatarId: string, x: number, y: number): Proposal {
  const thing = thingAt(state, x, y);
  return {
    avatar_id: avatarId,
    action: "move",
    params: thing === undefined ? { target: { x, y } } : { near: thing },
  };
}
