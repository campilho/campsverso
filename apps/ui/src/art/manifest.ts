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
  /** Um ponto de cor no canto de baixo à direita (o canteiro regado). */
  readonly badge?: string;
  /** Um ponto de cor no canto de baixo à esquerda (o canteiro adubado, à espera do plantio). */
  readonly mark?: string;
  /** Escala do quadro (a cama LPC tem 2 tiles de largura; a casa da fazenda, só 3). */
  readonly scale?: number;
  /** Cor do chão por baixo do quadro: o canteiro cavado na grama da Boa Vista continua de terra
   * com a planta em cima (na fazenda 1, a terra vem do mapa). */
  readonly ground?: string;
  /** Um quadro da mesma folha desenhado por cima de quem está no tile: o encosto da cadeira de
   * escritório, na frente de quem senta de costas (a arte da fase 1). */
  readonly front?: number;
  /** Quanto o quadro anda, em pixels, a partir do pé no meio do tile: o bloco do banheiro, de 4
   * tiles, começa no tile da coisa (ADR-0082). */
  readonly dx?: number;
  readonly dy?: number;
  /** Um assento (a cadeira do escritório, ADR-0078): quem para em cima dele senta, olhando para
   * este lado. Numa variante, o lado vem do atributo (a cadeira de lado da copa, ADR-0082). */
  readonly seat?: Facing;
}

/** Uma coisa que se mexe sempre: a TV com o jogo, as bolhas do bebedouro (ADR-0082). */
export interface Loop {
  readonly frames: readonly number[];
  readonly fps?: number;
}

/** Uma peça desenhada sobre cada tile de um tipo do mapa lógico, com a profundidade da linha dele:
 * a divisória dos cubículos, que cobre o pé de quem passa atrás dela (ADR-0082). Com `autotile:
 * "mask4"`, o quadro é a máscara dos vizinhos do mesmo tipo (norte 1, leste 2, sul 4, oeste 8). */
export interface TileProp {
  readonly sheet: string;
  readonly frame?: number;
  readonly autotile?: "mask4";
}

/** Uma coisa que se mexe enquanto alguém sentado de frente para ela faz uma das ações: a tela da
 * mesa rolando código enquanto o dev trabalha. */
export interface InUse {
  readonly actions: readonly string[];
  readonly frames: readonly number[];
  readonly fps?: number;
  /** Em uso por quem faz a ação em qualquer lugar do mundo, e não só de frente para ela: a TV, que
   * mostra o telejornal ou o jogo de quem está no sofá (ADR-0082). */
  readonly anywhere?: boolean;
}

/** Os quadros pela oficina do dev (ADR-0080), com os estados que `workshop.ts` dá:
 * - `owner`: o último passo do dono da coisa (o atributo `dono`) enquanto ele a usa, a mesa do
 *   dev: `lendo`, `escrevendo`, `verde` e `vermelho`;
 * - `self`: a última chamada da própria coisa, o robô: `trabalhando`, `passou` e `falhou`;
 * - `any`: algum robô trabalhando, a bancada: `trabalhando`.
 * Sem estado, vale o que a coisa mostraria sem a oficina (`in_use`, `loop` ou o quadro). */
export interface WorkshopArt {
  readonly of: "owner" | "self" | "any";
  readonly frames: Readonly<Record<string, Loop>>;
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
  /** Os quadros de quando está em uso (`InUse`); uma lista quando cada ação mostra outros (a TV: o
   * telejornal ou o jogo). Vale a primeira em uso. */
  readonly in_use?: InUse | readonly InUse[];
  /** Os quadros que se repetem sempre (`Loop`). */
  readonly loop?: Loop;
  /** Os quadros pela oficina do dev (`WorkshopArt`), à frente de `in_use` e de `loop`. */
  readonly workshop?: WorkshopArt;
  /** Quantos tiles a coisa ocupa para a direita, a partir do tile dela: quem está ao lado de
   * qualquer um deles a usa (o bloco do banheiro, de 4 tiles). */
  readonly width?: number;
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
  /** As direções que a folha tem, na ordem das linhas a partir de `row`, quando não são as quatro:
   * comer sentado só de lado (`["left", "right"]`). As outras direções usam a primeira. */
  readonly facings?: readonly Facing[];
}

export interface AvatarArt {
  readonly sheet: string;
  readonly animations?: Readonly<Record<string, Animation>>;
  /** Ação → animação; `*` vale para as que não estão na lista. */
  readonly actions?: Readonly<Record<string, string>>;
  readonly idle?: string;
  readonly asleep?: string;
  /** A animação de quem está parado num assento, qualquer que seja a ação (trabalhar, esperar,
   * falar): o Camps senta na cadeira da mesa e o vigia na dele. */
  readonly seated?: string;
  /** Sentado, a animação de algumas ações no lugar da de sentado: digitar enquanto trabalha. */
  readonly seated_actions?: Readonly<Record<string, string>>;
  /** Quantos pixels o pé fica acima da borda de baixo do quadro (o LPC, 2; a fase 1, 0). */
  readonly feet?: number;
  /** A que altura do pé, em pixels, fica o rótulo da ação: acima da cabeça de quem senta encostado
   * na mesa (padrão 50, o do personagem LPC). */
  readonly label_above?: number;
  /** As ações em que o avatar não aparece: atrás da porta do banheiro (ADR-0080). */
  readonly hidden?: readonly string[];
  /** As ações feitas sentado numa coisa ao lado, pelo tipo dela: ver TV e jogar no sofá. O avatar
   * fica no tile logo acima ou logo abaixo da coisa, e a tela o desenha nela, na coluna dele,
   * olhando para cima (ADR-0082). */
  readonly sit_on?: Readonly<Record<string, string>>;
  /** O que o avatar carrega, pelo valor do atributo `carregando`: as animações de andar e de ficar
   * parado com a coisa na mão (a marmita, entre a geladeira e o lixo). */
  readonly carry?: Readonly<Record<string, { readonly walk: string; readonly idle: string }>>;
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
  /** As peças desenhadas sobre os tiles de um tipo, pelo nome do tipo (`TileProp`). */
  readonly tile_props?: Readonly<Record<string, TileProp>>;
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
  /** O mapa visual de cada variante do mapa (ADR-0070), pelo id que vem no `session.started`. */
  readonly visual_maps?: Readonly<Record<string, string>>;
  readonly avatars?: Readonly<Record<string, AvatarArt>>;
  /** O ícone de cada item no inventário do HUD (ADR-0068): um quadro de uma folha. */
  readonly items?: Readonly<Record<string, Look>>;
  /** Os créditos da arte desta camada (CSV), mostrados na tela. */
  readonly credits?: string;
  /** A luz do escritório pela hora do relógio do mundo (`Lights`, ADR-0082). */
  readonly lights?: Lights;
  /** Os tiles do mapa visual que mudam com a hora: a janela de noite e o relógio (`TimeTiles`). */
  readonly time_tiles?: TimeTiles;
  /** As fichas do quadro dos pedidos, penduradas pelo estado de cada pedido (`Cards`). */
  readonly cards?: Cards;
  /** Outros arquivos JSON da mesma camada, juntados antes deste (o `baloes.json` gerado pelo
   * `make arte-escritorio`); o que este diz vale por cima. */
  readonly include?: readonly string[];
  /** O que vai sobre a cabeça, na arte do escritório (`Bubbles`; o pedido de arte de 18/nov). */
  readonly bubbles?: Bubbles;
}

/** Uma fonte pixel numa folha: cada glifo numa célula, alinhado à esquerda, com a sua largura. */
export interface BitmapFont {
  readonly sheet: string;
  /** A célula de cada glifo, em pixels: [largura, altura]. */
  readonly cell: readonly [number, number];
  readonly columns: number;
  /** O respiro entre as letras, em pixels. */
  readonly spacing: number;
  /** Os caracteres na ordem da folha, e a largura de cada um. */
  readonly glyphs: string;
  readonly widths: readonly number[];
}

/** Uma moldura em nove fatias, esticada no tamanho do texto: a etiqueta ou o balão de fala. */
export interface TextFrame {
  /** A peça na folha dos balões: [x, y, largura, altura]. */
  readonly rect: readonly [number, number, number, number];
  /** O lado de cada uma das nove fatias. */
  readonly slice: number;
  /** A cor do texto (a fonte é tingida). */
  readonly color: string;
  /** Da borda ao texto: [x, y]. */
  readonly margin: readonly [number, number];
  /** A distância entre as linhas e o máximo delas. */
  readonly line: number;
  readonly lines: number;
  /** A largura máxima do texto, em pixels: mais que isso quebra a linha. */
  readonly max_width?: number;
  /** A ponta embaixo, no meio: a peça, quantos pixels ela sobe sobre a moldura e o bico (a âncora). */
  readonly tail?: {
    readonly rect: readonly [number, number, number, number];
    readonly rise: number;
    readonly tip: readonly [number, number];
  };
}

/** O balão com o ícone da ação, o progresso num fio na base, a etiqueta, a fala e a fonte. */
export interface Bubbles {
  readonly sheet: string;
  readonly action: {
    readonly rect: readonly [number, number, number, number];
    /** O bico da ponta, no quadro do balão: o ponto que fica sobre a cabeça. */
    readonly anchor: readonly [number, number];
    /** Onde o ícone pousa, no quadro do balão. */
    readonly slot: readonly [number, number];
    readonly progress: {
      readonly x: number;
      readonly y: number;
      readonly width: number;
      readonly height: number;
      readonly track: string;
      readonly fill: string;
    };
    /** Sentado à mesa, de costas: o balão vai para o lado da cabeça, para não cobrir o monitor. */
    readonly at_desk?: readonly [number, number];
  };
  readonly icons: {
    readonly sheet: string;
    readonly columns: number;
    /** Cada ícone pelo nome: [coluna, linha]. */
    readonly frames: Readonly<Record<string, readonly [number, number]>>;
    /** O ícone de cada ação (o sono é `sleep`); a ação sem ícone vai na etiqueta. */
    readonly actions?: Readonly<Record<string, string>>;
  };
  readonly label?: TextFrame;
  readonly speech?: TextFrame;
  readonly font?: BitmapFont;
}

export type LightMode = "day" | "lamps" | "dark";

/** A luz da noite: com as luminárias acesas, poças de luz e penumbra fora delas; depois, o escuro,
 * com a lanterna do vigia. A janela fica sempre acesa, e o corredor, na penumbra. As poças têm a
 * borda em xadrez, como a prévia; a sombra é uma cor por cima, imitando a troca da paleta. */
export interface Lights {
  /** O que vale a partir de cada hora ("HH:MM"): `day`, `lamps` ou `dark`. */
  readonly schedule: readonly { readonly from: string; readonly mode: LightMode }[];
  readonly color: string;
  /** Quanto escurecer fora das poças (0 a 1), com as luminárias e no escuro. */
  readonly penumbra: number;
  readonly dark: number;
  /** Os centros das luminárias, em tiles (o meio do tile é .5). */
  readonly lamps?: readonly (readonly [number, number])[];
  /** O raio das poças e a largura da borda em xadrez, em pixels. */
  readonly lamp_radius?: number;
  readonly lamp_border?: number;
  /** Os retângulos sempre acesos, em pixels do mapa: a janela. */
  readonly lit?: readonly { readonly x: number; readonly y: number; readonly w: number; readonly h: number }[];
  /** Os retângulos que nunca passam da penumbra, nem no escuro: o corredor, com a luz fraca do
   * prédio, e as faces da parede de baixo e do banheiro que dão para ele (18/nov: o corredor
   * sempre aceso puxava o olho para fora da sala). A lanterna acende por cima. */
  readonly dim?: readonly { readonly x: number; readonly y: number; readonly w: number; readonly h: number }[];
  /** A lanterna: quem a leva no escuro e os raios dos anéis em pixels (aceso, xadrez, penumbra,
   * xadrez), a partir de `lift` pixels acima do meio do tile (a mão). */
  readonly lantern?: { readonly avatar: string; readonly radii: readonly number[]; readonly lift?: number };
}

/** Os tiles da camada de decoração que mudam com a hora, pelo nome do tile no tileset sem o `-t` ou
 * o `-b` da metade: fora do dia, cada nome de `night` vira o dele (a janela com a cidade acesa); o
 * relógio (`clock-H`) mostra a hora do mundo, com H de 0 a 11. */
export interface TimeTiles {
  readonly night?: Readonly<Record<string, string>>;
  readonly clock?: string;
}

/** As fichas do quadro: a folha, o canto da primeira coluna (em pixels), a largura de cada coluna,
 * a coluna de cada estado do pedido e o quadro de cada ficha, pelo estado (`state_frames`, que
 * vale primeiro) ou pelo tamanho. Cabem quatro fichas por coluna. */
export interface Cards {
  readonly sheet: string;
  readonly x: number;
  readonly y: number;
  readonly column_width: number;
  /** Quantos pixels a ficha entra na coluna: na primeira, que tem a moldura, mais. */
  readonly first_inset: number;
  readonly inset: number;
  readonly columns: Readonly<Record<string, number>>;
  readonly state_frames?: Readonly<Record<string, number>>;
  readonly size_frames?: Readonly<Record<string, number>>;
  readonly frame?: number;
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
  const variants = Object.fromEntries(
    Object.entries(manifest.visual_maps ?? {}).map(([id, path]) => [id, `${root}/${path}`]),
  );
  return {
    ...manifest,
    ...(manifest.sheets === undefined ? {} : { sheets }),
    ...(manifest.visual_map === undefined ? {} : { visual_map: `${root}/${manifest.visual_map}` }),
    ...(manifest.visual_maps === undefined ? {} : { visual_maps: variants }),
    ...(manifest.credits === undefined ? {} : { credits: `${root}/${manifest.credits}` }),
  };
}

/** O mapa visual do mapa com este id: o da variante, quando há (ADR-0070); senão, o do cenário. */
export function visualMapFor(manifest: ArtManifest, mapId: string | undefined): string | undefined {
  return (mapId === undefined ? undefined : manifest.visual_maps?.[mapId]) ?? manifest.visual_map;
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
  readonly marks?: readonly string[];
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
  const marks: string[] = [];
  for (const overlay of overlays ?? []) {
    if (matches(overlay.when, attributes)) {
      const { badge, mark, ...others } = overlay.look;
      if (badge !== undefined) {
        badges.push(badge);
      }
      if (mark !== undefined) {
        marks.push(mark);
      }
      look = { ...look, ...others };
    }
  }
  const label = fill(look.label, attributes);
  return { ...look, ...(label === undefined ? {} : { label }), badges, ...(marks.length === 0 ? {} : { marks }) };
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

/** A animação de quem está sentado: a da ação, quando o manifesto tem (digitar ao trabalhar); senão,
 * a de sentado. */
export function seatedAnimation(art: AvatarArt | undefined, action: string | undefined): string | undefined {
  return (action === undefined ? undefined : art?.seated_actions?.[action]) ?? art?.seated;
}

const AHEAD: Readonly<Record<Facing, readonly [number, number]>> = { up: [0, -1], left: [-1, 0], down: [0, 1], right: [1, 0] };

/** O tile à frente de quem está em `at`, olhando para `facing`: o que a pessoa sentada usa. */
export function facedTile(at: { readonly x: number; readonly y: number }, facing: Facing): { x: number; y: number } {
  const [dx, dy] = AHEAD[facing];
  return { x: at.x + dx, y: at.y + dy };
}

/** O quadro de uma coisa em uso, quando alguém de frente para ela (`actions`) ou, com `anywhere`,
 * em qualquer lugar (`everywhere`) faz uma das ações dela; fora disso, nenhum (fica o quadro de
 * sempre). Numa lista, vale a primeira em uso. */
export function inUseFrame(
  inUse: InUse | readonly InUse[] | undefined,
  actions: readonly string[],
  seconds: number,
  everywhere: readonly string[] = [],
): number | undefined {
  const entries: readonly InUse[] = inUse === undefined ? [] : "actions" in inUse ? [inUse] : inUse;
  for (const entry of entries) {
    const doing = entry.anywhere === true ? everywhere : actions;
    if (entry.frames.length > 0 && doing.some((action) => entry.actions.includes(action))) {
      const index = Math.floor(Math.max(0, seconds) * (entry.fps ?? 4)) % entry.frames.length;
      return entry.frames[index];
    }
  }
  return undefined;
}

/** Onde desenhar quem faz uma ação sentado numa coisa (`sit_on`): no tile da coisa, na coluna do
 * avatar, quando ele está logo acima ou logo abaixo dela e a até um tile de lado (o sofá de três
 * lugares fica no do meio); senão, nada. */
export function sitSpot(
  art: AvatarArt | undefined,
  action: string | undefined,
  things: Readonly<Record<string, Placed | undefined>>,
  at: { readonly x: number; readonly y: number },
): { x: number; y: number } | undefined {
  const kind = action === undefined ? undefined : art?.sit_on?.[action];
  if (kind === undefined) {
    return undefined;
  }
  const x = Math.round(at.x);
  const y = Math.round(at.y);
  for (const thing of Object.values(things)) {
    const spot = thing?.position;
    if (thing?.kind === kind && spot !== undefined && Math.abs(spot.y - y) === 1 && Math.abs(spot.x - x) <= 1) {
      return { x, y: spot.y };
    }
  }
  return undefined;
}

/** A animação de quem carrega alguma coisa (`carry`, pelo atributo `carregando`), andando ou parado;
 * sem carga, nenhuma. */
export function carryAnimation(
  art: AvatarArt | undefined,
  attributes: Readonly<Record<string, unknown>> | undefined,
  moving: boolean,
): string | undefined {
  const load = attributes?.["carregando"];
  const carried = typeof load === "string" ? art?.carry?.[load] : undefined;
  return carried === undefined ? undefined : moving ? carried.walk : carried.idle;
}

function minutesOf(hhmm: string): number {
  return Number(hhmm.slice(0, 2)) * 60 + Number(hhmm.slice(3, 5));
}

/** A hora do relógio da tela (`18:30` ou `18:30:05`, a hora local do mundo) em minutos do dia; sem
 * hora (`--:--`), nada. */
export function minuteOfDay(clock: string | undefined): number | undefined {
  const match = clock === undefined ? null : /^(\d{2}):(\d{2})/.exec(clock);
  return match === null ? undefined : Number(match[1]) * 60 + Number(match[2]);
}

/** A luz de agora: a última entrada da agenda cuja hora já passou; antes da primeira, a última da
 * véspera (a madrugada continua escura). Sem agenda ou sem hora, dia. */
export function lightMode(lights: Lights | undefined, minute: number | undefined): LightMode {
  if (lights === undefined || minute === undefined || lights.schedule.length === 0) {
    return "day";
  }
  const sorted = [...lights.schedule].sort((a, b) => minutesOf(a.from) - minutesOf(b.from));
  let mode = sorted[sorted.length - 1]?.mode ?? "day";
  for (const entry of sorted) {
    if (minutesOf(entry.from) <= minute) {
      mode = entry.mode;
    }
  }
  return mode;
}

/** O tile que a camada de decoração mostra no lugar de `name` agora: o relógio na hora do mundo
 * (`relogio-3-t` às 15:20) e, fora do dia, a janela de noite; o próprio nome nos outros. */
export function timedTile(tiles: TimeTiles | undefined, name: string, night: boolean, minute: number | undefined): string {
  const match = /^(.*)-([tb])$/.exec(name);
  const base = match?.[1];
  const half = match?.[2];
  if (tiles === undefined || base === undefined || half === undefined) {
    return name;
  }
  const clock = tiles.clock;
  if (clock !== undefined && minute !== undefined && base.startsWith(`${clock}-`) && /^\d+$/.test(base.slice(clock.length + 1))) {
    return `${clock}-${String(Math.floor(minute / 60) % 12)}-${half}`;
  }
  const dark = night ? tiles.night?.[base] : undefined;
  return dark === undefined ? name : `${dark}-${half}`;
}

/** Onde pendurar cada ficha no quadro (o canto de cima à esquerda, em pixels) e com que quadro: na
 * coluna do estado do pedido, na ordem do número, até quatro por coluna, as mais novas (a segunda
 * 12 px à direita da primeira, a terceira 12 px abaixo). Pedido de estado sem coluna não aparece. */
export function cardPlacements(
  cards: Cards | undefined,
  things: Readonly<Record<string, Placed | undefined>>,
): { x: number; y: number; frame: number }[] {
  if (cards === undefined) {
    return [];
  }
  const byColumn = new Map<number, { number: number; frame: number }[]>();
  for (const thing of Object.values(things)) {
    if (thing?.kind !== "ticket") {
      continue;
    }
    const attributes = thing.attributes ?? {};
    const column = cards.columns[String(attributes["estado"])];
    if (column === undefined) {
      continue;
    }
    const frame =
      cards.state_frames?.[String(attributes["estado"])] ?? cards.size_frames?.[String(attributes["tamanho"])] ?? cards.frame ?? 0;
    const list = byColumn.get(column) ?? [];
    list.push({ number: Number(attributes["numero"] ?? 0), frame });
    byColumn.set(column, list);
  }
  const placed: { x: number; y: number; frame: number }[] = [];
  for (const [column, list] of [...byColumn.entries()].sort((a, b) => a[0] - b[0])) {
    const left = cards.x + column * cards.column_width + (column === 0 ? cards.first_inset : cards.inset);
    list
      .sort((a, b) => a.number - b.number)
      .slice(-4)
      .forEach((card, i) => {
        placed.push({ x: left + (i % 2) * 12, y: cards.y + Math.floor(i / 2) * 12, frame: card.frame });
      });
  }
  return placed;
}

/** O quadro de uma coisa que se mexe sempre (`Loop`); sem laço, nenhum. */
export function loopFrame(loop: Loop | undefined, seconds: number): number | undefined {
  if (loop === undefined || loop.frames.length === 0) {
    return undefined;
  }
  return loop.frames[Math.floor(Math.max(0, seconds) * (loop.fps ?? 2)) % loop.frames.length];
}

/** A máscara dos vizinhos do mesmo tipo de um tile (norte 1, leste 2, sul 4, oeste 8): o quadro
 * do autotile da divisória (ADR-0082). */
export function autotileMask(typeAt: (x: number, y: number) => string, x: number, y: number): number {
  const type = typeAt(x, y);
  return (
    (typeAt(x, y - 1) === type ? 1 : 0) |
    (typeAt(x + 1, y) === type ? 2 : 0) |
    (typeAt(x, y + 1) === type ? 4 : 0) |
    (typeAt(x - 1, y) === type ? 8 : 0)
  );
}

/** Uma coisa no mundo, do jeito que o assento precisa dela: o tipo, o lugar e os atributos (o lado
 * da cadeira da copa vem de um). */
export interface Placed {
  readonly kind: string;
  readonly position?: { readonly x: number; readonly y: number } | undefined;
  readonly attributes?: Readonly<Record<string, unknown>> | undefined;
}

/** O lado para onde olha quem está parado num assento, ou nada fora de um. Só vale em cima do
 * tile do assento: no meio de um passo, ninguém senta. */
export function seatAt(
  manifest: ArtManifest,
  things: Readonly<Record<string, Placed | undefined>>,
  at: { readonly x: number; readonly y: number },
): Facing | undefined {
  const x = Math.round(at.x);
  const y = Math.round(at.y);
  if (Math.abs(at.x - x) > 1e-6 || Math.abs(at.y - y) > 1e-6) {
    return undefined;
  }
  for (const thing of Object.values(things)) {
    if (thing?.position?.x !== x || thing.position.y !== y || manifest.kinds?.[thing.kind] === undefined) {
      continue;
    }
    const seat = lookOf(manifest, thing.kind, thing.attributes ?? {}).seat;
    if (seat !== undefined) {
      return seat;
    }
  }
  return undefined;
}

/** O assento virado para a coisa em `spot` (a cadeira da mesinha da copa, a da mesa), fora dos
 * tiles `taken` e o mais perto de `from`; nada quando a coisa não tem um. Quem escolhe uma pausa
 * na coisa pelo menu senta nele antes, como a rotina do dev (ADR-0082). */
export function seatFacing(
  manifest: ArtManifest,
  things: Readonly<Record<string, Placed | undefined>>,
  spot: { readonly x: number; readonly y: number },
  from: { readonly x: number; readonly y: number },
  taken: readonly { readonly x: number; readonly y: number }[] = [],
): { x: number; y: number } | undefined {
  const seats: { x: number; y: number }[] = [];
  for (const thing of Object.values(things)) {
    const at = thing?.position;
    if (thing === undefined || at === undefined || manifest.kinds?.[thing.kind] === undefined) {
      continue;
    }
    const facing = lookOf(manifest, thing.kind, thing.attributes ?? {}).seat;
    const faced = facing === undefined ? undefined : facedTile(at, facing);
    if (faced?.x !== spot.x || faced.y !== spot.y) {
      continue;
    }
    if (!taken.some((t) => t.x === at.x && t.y === at.y)) {
      seats.push({ x: at.x, y: at.y });
    }
  }
  const distance = (t: { x: number; y: number }): number => Math.abs(t.x - from.x) + Math.abs(t.y - from.y);
  return seats.sort((a, b) => distance(a) - distance(b) || a.y - b.y || a.x - b.x)[0];
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
  const facings = animation.facings;
  const offset = facings === undefined ? ROW_OF[facing] : Math.max(0, facings.indexOf(facing));
  const row = animation.row + (animation.single === true ? 0 : offset);
  const cycle = animation.frames;
  const index = ((Math.floor(step) % cycle.length) + cycle.length) % cycle.length;
  return row * columns + (cycle[index] ?? 0);
}
