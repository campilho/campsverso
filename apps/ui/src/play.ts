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
}

export interface MenuEntry {
  readonly action: string;
  readonly label: string;
  readonly target?: string;
  readonly params: readonly MenuParam[];
  /** Todo parâmetro de escolha tem ao menos uma opção. */
  readonly ready: boolean;
}

/** O avatar está com um humano? Na v0.1, o único humano é quem está no browser. */
export function inControl(state: ObserverState, avatarId: string): boolean {
  return state.controllers[avatarId]?.type === "human";
}

function stock(state: ObserverState, containerId: string | undefined): Readonly<Record<string, number | undefined>> {
  return containerId === undefined ? {} : (state.containers[containerId] ?? {});
}

function param(state: ObserverState, avatarId: string, target: string | undefined, raw: NonNullable<Affordance["params"]>[number]): MenuParam {
  const choices = raw.choices ?? [];
  if (choices.length === 0) {
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
  const options = from === undefined ? choices : choices.filter((c) => (have[c] ?? 0) > 0);
  return { name: raw.name, label: raw.label, options, numeric: false };
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
      return {
        action: a.action,
        label: a.label,
        ...(a.target && target !== undefined ? { target } : {}),
        params,
        ready: params.every((p) => p.numeric || p.options.length > 0),
      };
    });
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
