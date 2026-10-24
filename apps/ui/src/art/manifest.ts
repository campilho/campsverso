/** O manifesto de arte dos cartuchos (ADR-0053): como desenhar cada tile, cada `kind` e o avatar.
 *
 * Cada camada (do gênero ao cenário) traz o seu `art.json`; a tela junta na ordem do índice, e a
 * camada de cima cobre a de baixo. O renderer não sabe o que é uma fazenda: ele só procura aqui.
 * O que o manifesto não conhece ganha uma cor estável derivada do nome.
 */

export type Scalar = string | number | boolean | null;

/** Uma imagem em quadros iguais. O caminho é relativo à camada no arquivo e absoluto depois de lido. */
export interface SheetDef {
  readonly image: string;
  readonly frame_width: number;
  readonly frame_height: number;
}

/** A aparência de uma coisa: um quadro de uma folha, ou uma cor (a arte provisória). */
export interface Look {
  readonly color?: string;
  /** Texto curto desenhado por cima; `{atributo}` vira o valor do atributo. */
  readonly label?: string;
  readonly sheet?: string;
  readonly frame?: number;
  /** Cor que tinge o quadro (a planta murcha é a madura escurecida). */
  readonly tint?: string;
  /** Um ponto de cor no canto (o canteiro regado). */
  readonly badge?: string;
  /** Escala do quadro (a cama LPC tem 2 tiles de largura; a casa da fazenda, só 3). */
  readonly scale?: number;
  /** Cor do chão por baixo do quadro: o canteiro cavado na grama da Boa Vista continua de terra
   * com a planta em cima (na fazenda 1, a terra vem do mapa). */
  readonly ground?: string;
}

export interface Variant {
  readonly when: Readonly<Record<string, Scalar>>;
  readonly look: Look;
}

export interface KindArt extends Look {
  /** A primeira variante cujos atributos batem cobre a aparência base. */
  readonly variants?: readonly Variant[];
  /** Todas as que batem se somam por cima (badges, rótulos). */
  readonly overlays?: readonly Variant[];
}

export interface Animation {
  /** Primeira linha: uma por direção, na ordem `up`, `left`, `down`, `right` (padrão LPC). */
  readonly row: number;
  /** A sequência de colunas que se repete. */
  readonly frames: readonly number[];
  /** Quadros por segundo de tela; ações mais rápidas no relógio acelerado. */
  readonly fps?: number;
  /** Quadros por tile andado: o passo acompanha o deslocamento, sem patinar. */
  readonly per_tile?: number;
  /** Uma só direção (o `hurt` do LPC, deitado). */
  readonly single?: boolean;
}

export interface AvatarArt {
  readonly sheet: string;
  readonly animations?: Readonly<Record<string, Animation>>;
  /** Ação → animação; `*` vale para as que não estão na lista. */
  readonly actions?: Readonly<Record<string, string>>;
  readonly idle?: string;
  readonly asleep?: string;
  /** Um recorte de um quadro da folha, para o HUD. */
  readonly portrait?: { readonly frame: number; readonly x: number; readonly y: number; readonly size: number };
  /** Dormindo numa cama: só a cabeça (um recorte de um quadro) no travesseiro, `dy` abaixo do topo da cama. */
  readonly in_bed?: {
    readonly frame: number;
    readonly x: number;
    readonly y: number;
    readonly width: number;
    readonly height: number;
    readonly scale: number;
    readonly dy: number;
  };
}

export interface ArtManifest {
  readonly version: 1;
  readonly tile_size?: number;
  readonly sheets?: Readonly<Record<string, SheetDef>>;
  readonly tiles?: Readonly<Record<string, Look>>;
  readonly kinds?: Readonly<Record<string, KindArt>>;
  /** Quanto escurecer em cada fase do dia (0 a 1). */
  readonly phases?: Readonly<Record<string, { readonly shade: number }>>;
  /** Em cada estação do ano acelerado (ADR-0067): a cor que tinge o chão e as folhas que trocam
   * as do mapa visual (as árvores de outono, por exemplo), pelo nome do tileset. */
  readonly seasons?: Readonly<
    Record<string, { readonly tint?: string; readonly tilesets?: Readonly<Record<string, string>> }>
  >;
  /** Efeito de cada condição do clima. */
  readonly weather?: Readonly<Record<string, { readonly effect: "rain" }>>;
  /** O mapa visual (Tiled), desenhado no lugar das cores dos tiles. */
  readonly visual_map?: string;
  readonly avatars?: Readonly<Record<string, AvatarArt>>;
  /** Os créditos da arte desta camada (CSV), mostrados na tela. */
  readonly credits?: string;
}

export const EMPTY: ArtManifest = { version: 1 };

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function deepMerge(base: unknown, over: unknown): unknown {
  if (!isObject(base) || !isObject(over)) {
    return over === undefined ? base : over;
  }
  const result: Record<string, unknown> = { ...base };
  for (const [key, value] of Object.entries(over)) {
    result[key] = deepMerge(base[key], value);
  }
  return result;
}

/** Os caminhos de uma camada viram endereços do gateway (`/content/art/<camada>/...`). */
export function rooted(manifest: ArtManifest, root: string): ArtManifest {
  const sheets = Object.fromEntries(
    Object.entries(manifest.sheets ?? {}).map(([name, sheet]) => [name, { ...sheet, image: `${root}/${sheet.image}` }]),
  );
  return {
    ...manifest,
    ...(manifest.sheets === undefined ? {} : { sheets }),
    ...(manifest.visual_map === undefined ? {} : { visual_map: `${root}/${manifest.visual_map}` }),
    ...(manifest.credits === undefined ? {} : { credits: `${root}/${manifest.credits}` }),
  };
}

/** Junta as camadas na ordem: a de cima cobre a de baixo; listas são trocadas, não somadas. */
export function mergeManifests(layers: readonly ArtManifest[]): ArtManifest {
  return layers.reduce<ArtManifest>((all, layer) => deepMerge(all, layer) as ArtManifest, EMPTY);
}

function matches(when: Readonly<Record<string, Scalar>>, attributes: Readonly<Record<string, unknown>>): boolean {
  return Object.entries(when).every(([key, value]) => (attributes[key] ?? null) === value);
}

function fill(label: string | undefined, attributes: Readonly<Record<string, unknown>>): string | undefined {
  return label?.replace(/\{(\w+)\}/g, (_, key: string) => {
    const value = attributes[key];
    return typeof value === "string" || typeof value === "number" ? String(value) : "";
  });
}

export function hashColor(name: string): string {
  let hash = 0;
  for (const char of name) {
    hash = (hash * 31 + char.charCodeAt(0)) % 360;
  }
  return `hsl(${String(hash)} 45% 55%)`;
}

export interface Resolved extends Look {
  readonly badges: readonly string[];
}

/** A aparência de uma entidade agora: base, variante que bate e sobreposições. */
export function lookOf(manifest: ArtManifest, kind: string, attributes: Readonly<Record<string, unknown>>): Resolved {
  const art = manifest.kinds?.[kind];
  if (art === undefined) {
    return { color: hashColor(kind), label: kind.replace(/_/g, " ").slice(0, 5), badges: [] };
  }
  const { variants, overlays, ...base } = art;
  const variant = variants?.find((v) => matches(v.when, attributes));
  let look: Look = variant === undefined ? base : { ...base, ...variant.look };
  const badges: string[] = [];
  for (const overlay of overlays ?? []) {
    if (matches(overlay.when, attributes)) {
      const { badge, ...others } = overlay.look;
      if (badge !== undefined) {
        badges.push(badge);
      }
      look = { ...look, ...others };
    }
  }
  const label = fill(look.label, attributes);
  return { ...look, ...(label === undefined ? {} : { label }), badges };
}

export function tileLook(manifest: ArtManifest, type: string): Look {
  return manifest.tiles?.[type] ?? { color: type === "" ? "#000000" : hashColor(type) };
}

/** O tom do chão na estação; branco (sem tingir) fora de um ano declarado. */
export function seasonTint(manifest: ArtManifest, season: string | undefined): string {
  return season === undefined ? "#ffffff" : (manifest.seasons?.[season]?.tint ?? "#ffffff");
}

/** A folha que desenha o tileset na estação; o próprio nome do tileset fora de uma troca. */
export function seasonSheet(manifest: ArtManifest, season: string | undefined, tileset: string): string {
  return season === undefined ? tileset : (manifest.seasons?.[season]?.tilesets?.[tileset] ?? tileset);
}

export function shadeOf(manifest: ArtManifest, phase: string): number {
  return Math.min(1, Math.max(0, manifest.phases?.[phase]?.shade ?? 0));
}

export function weatherEffect(manifest: ArtManifest, condition: string | undefined): "rain" | undefined {
  return condition === undefined ? undefined : manifest.weather?.[condition]?.effect;
}

/** Qual animação do avatar mostrar: dormindo, numa ação, ou parado. */
export function animationFor(art: AvatarArt | undefined, action: string | undefined, asleep: boolean): string | undefined {
  if (art === undefined) {
    return undefined;
  }
  if (asleep) {
    return art.asleep;
  }
  if (action === undefined) {
    return art.idle;
  }
  return art.actions?.[action] ?? art.actions?.["*"] ?? art.idle;
}

/** `#rrggbb` ou `hsl(h s% l%)` como número 0xRRGGBB, que é como o Phaser recebe cores. */
export function colorNumber(css: string): number {
  const hex = /^#([0-9a-f]{6})$/i.exec(css);
  if (hex?.[1] !== undefined) {
    return Number.parseInt(hex[1], 16);
  }
  const hsl = /^hsl\((\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)%\s+(\d+(?:\.\d+)?)%\)$/.exec(css);
  if (hsl === null) {
    return 0xff00ff; // cor que chama atenção: o manifesto tem um erro
  }
  const h = Number(hsl[1]) / 360;
  const s = Number(hsl[2]) / 100;
  const l = Number(hsl[3]) / 100;
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const channel = (t: number): number => {
    const k = ((t % 1) + 1) % 1;
    const v = k < 1 / 6 ? p + (q - p) * 6 * k : k < 1 / 2 ? q : k < 2 / 3 ? p + (q - p) * (2 / 3 - k) * 6 : p;
    return Math.round(v * 255);
  };
  return (channel(h + 1 / 3) << 16) | (channel(h) << 8) | channel(h - 1 / 3);
}

export type Facing = "up" | "left" | "down" | "right";

const ROW_OF: Readonly<Record<Facing, number>> = { up: 0, left: 1, down: 2, right: 3 };

/** Para onde olha quem se move (dx, dy em tiles); parado, continua olhando para onde olhava. */
export function facingOf(dx: number, dy: number, previous: Facing): Facing {
  if (Math.abs(dx) < 1e-6 && Math.abs(dy) < 1e-6) {
    return previous;
  }
  if (Math.abs(dx) >= Math.abs(dy)) {
    return dx > 0 ? "right" : "left";
  }
  return dy > 0 ? "down" : "up";
}

/** O quadro da folha num passo da animação (`step` cresce com o tempo ou com o caminho andado). */
export function frameOf(animation: Animation, columns: number, facing: Facing, step: number): number {
  const row = animation.row + (animation.single === true ? 0 : ROW_OF[facing]);
  const cycle = animation.frames;
  const index = ((Math.floor(step) % cycle.length) + cycle.length) % cycle.length;
  return row * columns + (cycle[index] ?? 0);
}
