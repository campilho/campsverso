/** O renderer Phaser (M6; ADR-0053): o mesmo estado do canvas de depuração, com a arte dos cartuchos.
 *
 * Desenha; não decide nada (escopo §9). A aparência de cada coisa vem do manifesto de arte; o que
 * ele não conhece vira um quadrado de cor estável. O Phaser só desenha: os cliques ficam com a
 * página (main.ts), que pergunta `tileAt`.
 */
import type { ObserverState } from "@campsverso/contracts";
import Phaser from "phaser";

import { lightLevels } from "../art/light.ts";
import {
  EMPTY,
  animationFor,
  autotileMask,
  cardPlacements,
  carryAnimation,
  colorNumber,
  facingOf,
  frameOf,
  inUseFrame,
  lightMode,
  lookOf,
  loopFrame,
  minuteOfDay,
  seasonSheet,
  seasonTint,
  seatAt,
  seatedAnimation,
  shadeOf,
  sitSpot,
  tileLook,
  timedTile,
  visualMapFor,
  weatherEffect,
  type ArtManifest,
  type AvatarArt,
  type Facing,
  type LightMode,
  type Resolved,
} from "../art/manifest.ts";
import { declutter, type Label, type Placement } from "../declutter.ts";
import { BubbleKit, HeadView } from "./bubbles.ts";
import { el } from "../dom.ts";
import { FogMemory, FogStore, lightHeld, serverCenter, visionRadius, type Sight } from "../fog.ts";
import { MotionClock, type Point } from "../motion.ts";
import { Balloons } from "../speech.ts";
import { overHead } from "../progress.ts";
import { clockText } from "../simclock.ts";
import { tileAt, type TileGrid } from "../tiled.ts";
import { workshopFrame, workshopState } from "../workshop.ts";
import { tileUnder, type WorldRenderer } from "./renderer.ts";

const TILE = 32;
const DROPS = 140;
const CLOUD_COLOR = 0xdde2e8; // a névoa sobre o que nunca foi visto
const SEEN_COLOR = 0x6f7782; // o cinza sobre o que já foi visto
const SEEN_ALPHA = 0.5;
const HAZE = [0.5, 0.22]; // o véu do anel de fora da vista e o do seguinte, em fração da névoa
const LIGHT_RINGS = 20; // anéis da luz à noite, do mais largo ao mais estreito (sem degraus à vista)
const FONT = "ui-monospace, monospace";
/** Quantos pixels o balão desce para quem está sentado de lado, com a cabeça mais baixa. */
const SEATED_DROP = 10;
const FOG_SAVE_MS = 1000; // a lembrança da névoa vai ao navegador no máximo uma vez por segundo
// Um mapa visual por endereço: as variantes do mapa (ADR-0070) têm cada uma o seu.
const mapKey = (url: string): string => `visual-map:${url}`;
// A tela mostra no máximo 32 × 18 tiles; um mapa maior (a Morada do Sol, ADR-0067) rola com a câmera.
const VIEW = { width: 32, height: 18 };
const DRAG = 6; // pixels de arrasto antes de virar arrastar, e não clique
const FEET = 2; // os pés do LPC ficam um pouco acima da borda do quadro
/** Por quanto tempo, depois do último quadro em que o desenho se mexeu, o avatar continua com a
 * animação de andar: entre dois passos do teclado ele não pisca para o parado. */
const WALK_HOLD_MS = 120;

interface Frame {
  readonly state: ObserverState;
  readonly tick: number;
}

/** A cama em que o avatar dorme, como está desenhada: o centro e o topo da imagem. */
interface Bed {
  readonly cx: number;
  readonly top: number;
  readonly y: number;
}

/** Profundidade pela linha do chão: quem está mais embaixo na tela fica na frente. */
function depthAt(y: number): number {
  return 10 + y;
}

/** Quantos quadros cabem numa linha da folha. */
function columnsOf(scene: Phaser.Scene, sheet: string): number {
  const width = scene.textures.getFrame(sheet, 0).width;
  return Math.max(1, Math.floor(scene.textures.get(sheet).getSourceImage().width / width));
}

/** Uma entidade parada no mapa: um quadro da arte, ou um quadrado de cor com rótulo. */
class ThingView {
  private readonly box: Phaser.GameObjects.Rectangle;
  private readonly image: Phaser.GameObjects.Image;
  /** O quadro por cima de quem está no tile (o encosto da cadeira). */
  private readonly front: Phaser.GameObjects.Image;
  private readonly label: Phaser.GameObjects.Text;
  private readonly badge: Phaser.GameObjects.Arc;
  private readonly mark: Phaser.GameObjects.Arc;

  constructor(scene: Phaser.Scene) {
    this.box = scene.add.rectangle(0, 0, TILE - 6, TILE - 6, 0xffffff).setStrokeStyle(1, 0x000000, 0.45);
    this.image = scene.add.image(0, 0, "__DEFAULT").setVisible(false).setOrigin(0.5, 1);
    this.front = scene.add.image(0, 0, "__DEFAULT").setVisible(false).setOrigin(0.5, 1);
    this.label = scene.add.text(0, 0, "", { fontFamily: FONT, fontSize: "9px", color: "#ffffff" }).setOrigin(0.5);
    this.badge = scene.add.circle(0, 0, 3.5, 0x4fc3f7).setVisible(false).setStrokeStyle(1, 0x0b3d5c);
    this.mark = scene.add.circle(0, 0, 3.5, 0xe0a33a).setVisible(false).setStrokeStyle(1, 0x4a2e0c);
  }

  /** `frame` troca o quadro do manifesto: a tela da mesa em uso. */
  show(scene: Phaser.Scene, look: Resolved, x: number, y: number, frame?: number): void {
    const cx = x * TILE + TILE / 2;
    const cy = y * TILE + TILE / 2;
    const depth = depthAt(y);
    const sheet = look.sheet !== undefined && scene.textures.exists(look.sheet) ? look.sheet : undefined;
    // Sem quadro, o quadrado de cor é a coisa; com quadro, só o chão (`ground`) vai por baixo dele.
    const fill = sheet === undefined ? look.color : look.ground;
    this.box.setVisible(fill !== undefined).setPosition(cx, cy).setDepth(depth - 0.05);
    if (fill !== undefined) {
      this.box.setFillStyle(colorNumber(fill));
    }
    // O pé do quadro no meio da borda de baixo do tile, andado de `dx` e `dy` (o bloco do banheiro).
    const footX = cx + (look.dx ?? 0);
    const footY = (y + 1) * TILE + (look.dy ?? 0);
    this.image.setVisible(sheet !== undefined).setPosition(footX, footY).setDepth(depth);
    if (sheet !== undefined) {
      this.image.setTexture(sheet, frame ?? look.frame ?? 0).setScale(look.scale ?? 1);
      if (look.tint === undefined) {
        this.image.clearTint();
      } else {
        this.image.setTint(colorNumber(look.tint));
      }
    }
    // O avatar no tile fica em depthAt(y) + 0.5: o encosto vem logo por cima dele.
    const front = sheet === undefined ? undefined : look.front;
    this.front.setVisible(front !== undefined).setPosition(footX, footY).setDepth(depth + 0.6);
    if (sheet !== undefined && front !== undefined) {
      this.front.setTexture(sheet, front).setScale(look.scale ?? 1);
    }
    this.label.setText(sheet === undefined ? (look.label ?? "") : "").setPosition(cx, cy + 1).setDepth(depth + 0.1);
    const [badge] = look.badges;
    this.badge.setVisible(badge !== undefined).setPosition(x * TILE + TILE - 6, y * TILE + TILE - 6).setDepth(depth + 0.2);
    if (badge !== undefined) {
      this.badge.setFillStyle(colorNumber(badge));
    }
    const [mark] = look.marks ?? [];
    this.mark.setVisible(mark !== undefined).setPosition(x * TILE + 6, y * TILE + TILE - 6).setDepth(depth + 0.2);
    if (mark !== undefined) {
      this.mark.setFillStyle(colorNumber(mark));
    }
  }

  destroy(): void {
    for (const object of [this.box, this.image, this.front, this.label, this.badge, this.mark]) {
      object.destroy();
    }
  }
}

/** Um avatar: o sprite animado (ou um círculo, sem arte) e o que vai sobre a cabeça (`HeadView`). */
class AvatarView {
  private readonly body: Phaser.GameObjects.Arc;
  private readonly initial: Phaser.GameObjects.Text;
  private readonly sprite: Phaser.GameObjects.Sprite;
  private readonly head: HeadView;
  private facing: Facing = "down";
  private last: Point | undefined;
  private walked = 0;
  private animation: string | undefined;
  private since = 0;
  private movedAt = Number.NEGATIVE_INFINITY;

  constructor(scene: Phaser.Scene, id: string) {
    this.body = scene.add.circle(0, 0, TILE * 0.34, 0xf5f5f5).setStrokeStyle(2, 0x1b1b1b);
    this.initial = scene.add
      .text(0, 0, id.slice(0, 1).toUpperCase(), { fontFamily: FONT, fontSize: "12px", color: "#1b1b1b", fontStyle: "bold" })
      .setOrigin(0.5);
    this.sprite = scene.add.sprite(0, 0, "__DEFAULT").setOrigin(0.5, 1).setVisible(false);
    // O rótulo da ação, a barra e o balão de fala (ADR-0052, ADR-0078), ou os balões do escritório.
    this.head = new HeadView(scene);
  }

  show(
    scene: Phaser.Scene,
    look: Resolved,
    art: AvatarArt | undefined,
    frame: Frame,
    id: string,
    at: Point,
    time: number,
    bed?: Bed,
    said?: string,
    seat?: Facing,
    kit?: BubbleKit,
    pointer?: Point,
  ): void {
    const { state, tick } = frame;
    const action = state.actions[id];
    const asleep = state.asleep[id] === true;
    if (action !== undefined && art?.hidden?.includes(action.action) === true) {
      this.hide(); // atrás da porta do banheiro (ADR-0080)
      return;
    }
    const moved = this.last === undefined ? { x: 0, y: 0 } : { x: at.x - this.last.x, y: at.y - this.last.y };
    const step = Math.hypot(moved.x, moved.y);
    this.walked += step;
    this.last = at;
    if (step > 1e-4) {
      this.movedAt = time;
    }
    // O desenho que anda, anda com a animação de andar: a 72× a ação do kernel acaba antes de o
    // desenho chegar, e o avatar deslizava parado até o destino (achado do usuário no escritório).
    const doing = !asleep && time - this.movedAt < WALK_HOLD_MS ? "move" : action?.action;
    // Ver TV e jogar (ADR-0082): de pé no tapete, logo acima ou abaixo do sofá, o avatar aparece
    // sentado nele, na coluna dele, de costas para a tela e com o encosto por cima.
    const sofa = doing === "move" || asleep ? undefined : sitSpot(art, action?.action, state.entities, at);
    const spot = sofa ?? at;
    const cx = spot.x * TILE + TILE / 2;
    const depth = depthAt(spot.y) + 0.5;
    const target = action?.params.target;
    const thing = typeof target === "string" ? state.entities[target]?.position : undefined;
    // Parado num assento, senta olhando para o lado dele, qualquer que seja a ação (ADR-0078).
    const seated = seat !== undefined && !asleep && doing !== "move" ? seatedAnimation(art, action?.action) : undefined;
    this.facing =
      sofa !== undefined
        ? "up"
        : seated !== undefined && seat !== undefined
          ? seat
          : doing === "move" || thing === undefined
            ? facingOf(moved.x, moved.y, this.facing)
            : facingOf(thing.x - at.x, thing.y - at.y, this.facing);

    // Com a marmita na mão (o atributo `carregando`), anda e espera carregando; as ações têm as suas.
    const attributes = state.entities[id]?.attributes;
    const carried =
      sofa !== undefined || seated !== undefined || asleep
        ? undefined
        : doing === "move"
          ? carryAnimation(art, attributes, true)
          : doing === undefined
            ? carryAnimation(art, attributes, false)
            : undefined;
    const name = seated ?? carried ?? animationFor(art, doing, asleep);
    const animation = name === undefined ? undefined : art?.animations?.[name];
    const sheet = art !== undefined && scene.textures.exists(art.sheet) ? art.sheet : undefined;
    if (name !== this.animation) {
      this.animation = name;
      this.since = time;
    }
    const inBed = asleep && bed !== undefined && sheet !== undefined ? art?.in_bed : undefined;
    const drawn = sheet !== undefined && (animation !== undefined || inBed !== undefined);
    this.body.setVisible(!drawn).setPosition(cx, spot.y * TILE + TILE / 2).setDepth(depth);
    this.body.setFillStyle(colorNumber(look.color ?? "#f5f5f5"));
    this.initial.setVisible(!drawn).setPosition(cx, spot.y * TILE + TILE / 2 + 1).setDepth(depth + 0.01);
    this.sprite.setVisible(drawn);
    if (inBed !== undefined && bed !== undefined && sheet !== undefined) {
      // Na cama: só a cabeça no travesseiro; a coberta é a da própria cama.
      const { x, y, width, height, scale, dy } = inBed;
      this.sprite
        .setTexture(sheet, inBed.frame)
        .setOrigin(0, 0)
        .setScale(scale)
        .setCrop(x, y, width, height)
        .setPosition(bed.cx - (width * scale) / 2 - x * scale, bed.top + dy - y * scale)
        .setDepth(depthAt(bed.y) + 0.6);
    } else {
      this.sprite
        .setCrop()
        .setOrigin(0.5, 1)
        .setScale(1)
        .setPosition(cx, (spot.y + 1) * TILE + (art?.feet ?? FEET))
        .setDepth(depth);
    }
    if (inBed === undefined && sheet !== undefined && animation !== undefined) {
      // O relógio acelerado acelera as ações; pausado, tudo para.
      const pace = state.clock.paused === true ? 0 : Math.min(3, Math.max(0.5, (state.clock.scale ?? 72) / 72));
      const step =
        animation.per_tile === undefined
          ? ((time - this.since) / 1000) * (animation.fps ?? 6) * pace
          : this.walked * animation.per_tile;
      this.sprite.setTexture(sheet, frameOf(animation, columnsOf(scene, sheet), this.facing, step));
    }

    const progress = overHead(state, id, tick);
    const above = inBed !== undefined && bed !== undefined ? { cx: bed.cx, top: bed.top - 2 } : undefined;
    // O mouse em cima de quem está na sala: a etiqueta com o nome e o que ele faz (18/nov).
    const shape = drawn ? this.sprite : this.body;
    const hovered = pointer !== undefined && kit !== undefined && shape.getBounds().contains(pointer.x, pointer.y);
    const who = state.entities[id]?.display_name ?? id;
    // Sentado de lado (a cadeira da copa), a cabeça fica mais baixa: o balão desce junto.
    const sideways = seated !== undefined && sofa === undefined && this.facing !== "up";
    // Perto da borda, o que vai sobre a cabeça fica inteiro dentro do que a câmera mostra (achado do
    // usuário no mapa d: "Cavar um canteiro aqui" saía do mapa).
    this.head.draw({
      kit,
      view: scene.cameras.main.worldView,
      x: above?.cx ?? cx,
      top: (above?.top ?? (drawn ? (spot.y + 1) * TILE - (art?.label_above ?? 50) : spot.y * TILE - 4)) + (kit !== undefined && sideways ? SEATED_DROP : 0),
      progress,
      action: asleep ? "sleep" : action?.action,
      atDesk: seated !== undefined && sofa === undefined && this.facing === "up",
      said,
      hover: hovered ? (progress === undefined ? who : `${who} – ${progress.label}`) : undefined,
    });
  }

  /** A caixa do que vai sobre a cabeça, quando há, para o `declutter`. */
  label(id: string): Label | undefined {
    return this.head.label(id);
  }

  /** Põe o que vai sobre a cabeça onde o `declutter` mandou; quando sobe, a fala sobe junto. */
  place(at: Placement): void {
    this.head.place(at);
  }

  /** Some da tela sem sair do mundo; o próximo `show` o desenha de novo. */
  private hide(): void {
    for (const object of [this.body, this.initial, this.sprite]) {
      object.setVisible(false);
    }
    this.head.hide();
  }

  destroy(): void {
    for (const object of [this.body, this.initial, this.sprite]) {
      object.destroy();
    }
    this.head.destroy();
  }
}

class WorldScene extends Phaser.Scene {
  grid: TileGrid | undefined;
  art: ArtManifest = EMPTY;
  frame: Frame | undefined;
  terrainDirty = true;
  created = false; // a cena já rodou o create (a câmera existe)
  private terrain!: Phaser.GameObjects.Graphics;
  private shade!: Phaser.GameObjects.Rectangle;
  private rain!: Phaser.GameObjects.Graphics;
  private fogLayer!: Phaser.GameObjects.Graphics;
  private light!: Phaser.GameObjects.Graphics;
  /** A névoa da visão do jogador (ADR-0068): ligada, a tela mostra o que o avatar vê. */
  fogOn = false;
  private fog = new FogMemory();
  private fogDrawn = false;
  private fogless = false; // sem raio de visão na sessão (o escritório): sem névoa nenhuma
  private fogStore: FogStore | undefined; // a lembrança no navegador, na visão do jogador
  private fogLoaded = false;
  private fogSavedAt = 0;
  private fogTick = 0;
  private visual: Phaser.Tilemaps.Tilemap | undefined;
  private mapId: string | undefined; // o id do mapa do `session.started`, que escolhe o mapa visual
  private visualUrl: string | undefined; // o endereço do mapa visual desenhado agora
  private ground: Phaser.Tilemaps.TilemapLayer | Phaser.Tilemaps.TilemapGPULayer | undefined;
  private tinted: string | undefined;
  private season: string | undefined; // a estação já desenhada nas folhas do mapa visual
  private readonly things = new Map<string, ThingView>();
  /** O estado da oficina que cada coisa mostrou no último quadro (para os testes no navegador). */
  readonly looks = new Map<string, string>();
  /** As peças sobre os tiles (a divisória, ADR-0082), refeitas quando o terreno muda. */
  private props: Phaser.GameObjects.Image[] = [];
  private readonly avatars = new Map<string, AvatarView>();
  private readonly seen = new Map<string, Point>(); // onde cada avatar aparece agora, em tiles
  /** O que fazem os que estão sentados, pelo tile à frente do assento: a mesa em uso. */
  private readonly using = new Map<string, string[]>();
  /** Quem está ao lado de cada tile, fazendo alguma ação: o dono da mesa, para o monitor dela
   * mostrar o último passo dele na oficina (ADR-0080). */
  private readonly users = new Map<string, string[]>();
  /** O que fazem todos os avatares agora: a TV mostra o jogo de quem joga no sofá (ADR-0082). */
  private doing: string[] = [];
  /** Os balões do escritório, quando a arte os traz e as folhas já chegaram. */
  private kit: BubbleKit | undefined;
  /** A luz da noite (ADR-0082): uma imagem do tamanho do mapa, por cima das coisas e dos avatares,
   * refeita só quando o modo da hora ou a lanterna mudam. */
  private night: Phaser.GameObjects.Image | undefined;
  private nightTexture: Phaser.Textures.CanvasTexture | undefined;
  private nightKey = "";
  /** Os tiles da decoração que mudam com a hora (a janela, o relógio), como estão no mapa visual. */
  private decor: { layer: Phaser.Tilemaps.TilemapLayer; gids: Map<string, number>; tiles: { x: number; y: number; name: string }[] } | undefined;
  private decorKey = "";
  /** As fichas penduradas no quadro dos pedidos, pelo estado de cada pedido (ADR-0082). */
  private cards: Phaser.GameObjects.Image[] = [];
  /** O caminho que o desenho de cada avatar faz nesta tela (ADR-0078). */
  readonly motion = new MotionClock();
  /** O que cada avatar disse por último, enquanto o balão dura (ADR-0078). */
  readonly balloons = new Balloons();
  /** Quem a câmera segue; parar de seguir é arrastar, voltar é o botão. */
  follow: string | undefined;
  following = true;
  whole = false; // o mapa inteiro na tela, com zoom

  constructor() {
    super({ key: "world" });
  }

  create(): void {
    this.terrain = this.add.graphics().setDepth(0);
    // A noite e a chuva são da tela, não do mundo: não rolam com a câmera.
    this.shade = this.add.rectangle(0, 0, 1, 1, 0x0c123c, 0).setOrigin(0.5).setDepth(80).setScrollFactor(0);
    this.rain = this.add.graphics().setDepth(81).setScrollFactor(0);
    this.fogLayer = this.add.graphics().setDepth(70); // a névoa rola com o mapa, abaixo da noite
    // A luz em volta do avatar à noite (ADR-0068): por cima da sombra, somando cor, e rola com o mapa.
    this.light = this.add.graphics().setDepth(80.5).setBlendMode(Phaser.BlendModes.ADD);
    this.created = true;
    this.loadArt();
  }

  /** Carrega as folhas e o mapa visual do manifesto que ainda não estão na memória. */
  loadArt(): void {
    if (!this.created) {
      return;
    }
    let pending = false;
    for (const [name, sheet] of Object.entries(this.art.sheets ?? {})) {
      if (!this.textures.exists(name)) {
        this.load.spritesheet(name, sheet.image, { frameWidth: sheet.frame_width, frameHeight: sheet.frame_height });
        pending = true;
      }
    }
    const url = visualMapFor(this.art, this.mapId);
    if (url !== undefined && !this.cache.tilemap.exists(mapKey(url))) {
      this.load.tilemapTiledJSON(mapKey(url), url);
      pending = true;
    }
    if (pending) {
      this.load.once("complete", () => {
        this.terrainDirty = true;
      });
      this.load.start();
    }
  }

  override update(time: number): void {
    const width = this.scale.width;
    const height = this.scale.height;
    if (this.terrainDirty) {
      this.drawTerrain();
      this.drawProps();
      this.terrainDirty = false;
    }
    const frame = this.frame;
    if (frame === undefined) {
      return;
    }
    const { state } = frame;
    const mapId = state.session?.map?.id;
    if (mapId !== this.mapId) {
      this.mapId = mapId; // uma variante do mapa: o mapa visual dela (ADR-0070)
      this.loadArt();
      this.terrainDirty = true;
    }
    this.drawAvatars(frame, time);
    this.drawThings(this.fogged(state), time, frame);
    // A hora do mundo acende as luminárias, apaga a sala, troca a janela e anda o relógio (ADR-0082).
    const minute = minuteOfDay(clockText(state, frame.tick));
    const mode = lightMode(this.art.lights, minute);
    this.drawNight(mode);
    this.drawDecor(mode, minute);
    this.drawCards(state);
    this.aim();
    this.tint(state.season);
    // Com zoom, o que não rola encolhe em volta do centro: o retângulo cresce na mesma conta.
    const zoom = this.cameras.main.zoom;
    this.shade
      .setPosition(width / 2, height / 2)
      .setSize(width / zoom, height / zoom)
      .setFillStyle(0x0c123c, shadeOf(this.art, state.phase));
    this.drawLight(state);
    this.drawRain(weatherEffect(this.art, state.weather[String(state.day)]) === "rain", time, width, height);
  }

  /** A luz em volta do avatar seguido, quando escurece (ADR-0068): o raio da hora da percepção,
   * fria sem luz nenhuma e quente com a lanterna. Só num mundo cuja percepção tem raio. */
  private drawLight(state: ObserverState): void {
    this.light.clear();
    const id = this.follow;
    const at = id === undefined ? undefined : this.seen.get(id);
    const radius = id === undefined ? undefined : visionRadius(state, id);
    const shade = shadeOf(this.art, state.phase);
    if (at === undefined || radius === undefined || shade === 0) {
      return;
    }
    const lantern = lightHeld(state, id ?? "");
    const color = lantern ? 0xffb347 : 0x9fb4ff;
    const step = (lantern ? 0.065 : 0.025) * shade; // mais escuro, mais contraste
    const outer = (radius + 0.5) * TILE;
    const cx = at.x * TILE + TILE / 2;
    const cy = at.y * TILE + TILE / 2;
    for (let ring = 0; ring < LIGHT_RINGS; ring++) {
      this.light.fillStyle(color, step).fillCircle(cx, cy, outer * (1 - ring / LIGHT_RINGS));
    }
  }

  /** A luz da noite do escritório (ADR-0082): os níveis de `lightLevels` pintados com a cor da
   * sombra numa imagem do tamanho do mapa. De dia, nada; refeita só quando muda. */
  private drawNight(mode: LightMode): void {
    const lights = this.art.lights;
    const grid = this.grid;
    if (lights === undefined || grid === undefined || mode === "day") {
      this.night?.setVisible(false);
      this.nightKey = "day";
      return;
    }
    const width = grid.width * TILE;
    const height = grid.height * TILE;
    const holder = lights.lantern?.avatar;
    const at = holder === undefined || !this.avatars.has(holder) ? undefined : this.seen.get(holder);
    const lantern =
      mode === "dark" && at !== undefined
        ? { x: Math.round(at.x * TILE + TILE / 2), y: Math.round(at.y * TILE + TILE / 2 - (lights.lantern?.lift ?? 8)) }
        : undefined;
    const key = `${mode}|${String(lantern?.x)}|${String(lantern?.y)}|${String(width)}x${String(height)}`;
    if (key === this.nightKey && this.night !== undefined) {
      return;
    }
    const levels = lightLevels(lights, mode, width, height, lantern);
    if (levels === undefined) {
      return;
    }
    if (this.nightTexture === undefined || this.nightTexture.width !== width || this.nightTexture.height !== height) {
      this.night?.destroy();
      this.nightTexture?.destroy();
      const texture = this.textures.createCanvas(`night-light-${String(width)}x${String(height)}`, width, height);
      if (texture === null) {
        return;
      }
      this.nightTexture = texture;
      this.night = this.add.image(0, 0, texture.key).setOrigin(0, 0).setDepth(50);
    }
    const context = this.nightTexture.getContext();
    const image = context.createImageData(width, height);
    const pixels = new Uint32Array(image.data.buffer); // RGBA na ordem da memória: A no byte de cima
    const color = colorNumber(lights.color);
    const rgb = ((color & 0xff) << 16) | (color & 0xff00) | ((color >> 16) & 0xff);
    const paint = [0, lights.penumbra, lights.dark].map((alpha) => ((Math.round(alpha * 255) << 24) | rgb) >>> 0);
    for (let i = 0; i < levels.length; i++) {
      pixels[i] = paint[levels[i] ?? 0] ?? 0;
    }
    context.putImageData(image, 0, 0);
    this.nightTexture.refresh();
    this.night?.setVisible(true);
    this.nightKey = key;
  }

  /** A janela de noite e o relógio na hora do mundo (ADR-0082), trocando os tiles da camada de
   * decoração do mapa visual; só quando a hora ou a noite mudam. */
  private drawDecor(mode: LightMode, minute: number | undefined): void {
    const decor = this.decor;
    const tiles = this.art.time_tiles;
    const night = mode !== "day";
    const key = `${String(night)}|${String(minute === undefined ? undefined : Math.floor(minute / 60))}`;
    if (decor === undefined || tiles === undefined || key === this.decorKey) {
      return;
    }
    for (const tile of decor.tiles) {
      const gid = decor.gids.get(timedTile(tiles, tile.name, night, minute));
      if (gid !== undefined) {
        decor.layer.putTileAt(gid, tile.x, tile.y);
      }
    }
    this.decorKey = key;
  }

  /** Os tiles da camada `decor` que mudam com a hora, lidos do mapa visual recém-montado: o nome de
   * cada tile vem do tipo dele no tileset (o mapa do Tiled que o cache guarda). */
  private findDecor(map: Phaser.Tilemaps.Tilemap, key: string): void {
    this.decor = undefined;
    this.decorKey = "";
    const tiles = this.art.time_tiles;
    const layer = map.getLayer("decor")?.tilemapLayer;
    const raw = (this.cache.tilemap.get(key) as { data?: unknown } | undefined)?.data as
      | { tilesets?: { firstgid: number; tiles?: { id: number; type?: string }[] }[] }
      | undefined;
    if (tiles === undefined || !(layer instanceof Phaser.Tilemaps.TilemapLayer) || raw === undefined) {
      return;
    }
    const gids = new Map<string, number>();
    const names = new Map<number, string>();
    for (const tileset of raw.tilesets ?? []) {
      for (const tile of tileset.tiles ?? []) {
        if (tile.type !== undefined) {
          gids.set(tile.type, tileset.firstgid + tile.id);
          names.set(tileset.firstgid + tile.id, tile.type);
        }
      }
    }
    const timed: { x: number; y: number; name: string }[] = [];
    layer.forEachTile((tile) => {
      const name = names.get(tile.index);
      // Muda com a hora: de noite (a janela) ou de uma hora para a outra (o relógio).
      if (name !== undefined && [timedTile(tiles, name, true, 0), timedTile(tiles, name, true, 60)].some((other) => other !== name)) {
        timed.push({ x: tile.x, y: tile.y, name });
      }
    });
    this.decor = timed.length === 0 ? undefined : { layer, gids, tiles: timed };
  }

  /** As fichas no quadro dos pedidos (ADR-0082): uma por pedido, na coluna do estado dele. */
  private drawCards(state: ObserverState): void {
    const cards = this.art.cards;
    const placed = cards === undefined || !this.textures.exists(cards.sheet) ? [] : cardPlacements(cards, state.entities);
    while (this.cards.length > placed.length) {
      this.cards.pop()?.destroy();
    }
    placed.forEach((card, i) => {
      const image = this.cards[i] ?? this.add.image(0, 0, cards?.sheet ?? "__DEFAULT").setOrigin(0, 0).setDepth(1);
      this.cards[i] = image;
      image.setTexture(cards?.sheet ?? "__DEFAULT", card.frame).setPosition(card.x, card.y);
    });
  }

  /** As peças sobre os tiles de um tipo (ADR-0082): a divisória dos cubículos, com a profundidade
   * da linha dela, como as coisas, para cobrir o pé de quem passa atrás. */
  private drawProps(): void {
    for (const image of this.props) {
      image.destroy();
    }
    this.props = [];
    const grid = this.grid;
    const props = this.art.tile_props;
    if (grid === undefined || props === undefined) {
      return;
    }
    const typeAt = (x: number, y: number): string =>
      x < 0 || y < 0 || x >= grid.width || y >= grid.height ? "" : tileAt(grid, x, y);
    for (let y = 0; y < grid.height; y++) {
      for (let x = 0; x < grid.width; x++) {
        const prop = props[typeAt(x, y)];
        if (prop === undefined || !this.textures.exists(prop.sheet)) {
          continue;
        }
        const frame = prop.autotile === "mask4" ? autotileMask(typeAt, x, y) : (prop.frame ?? 0);
        const image = this.add.image(x * TILE + TILE / 2, (y + 1) * TILE, prop.sheet, frame);
        this.props.push(image.setOrigin(0.5, 1).setDepth(depthAt(y)));
      }
    }
  }

  /** O mapa visual do cartucho, quando há; senão, uma cor por tipo de tile do mapa lógico. */
  private drawTerrain(): void {
    this.terrain.clear();
    const url = visualMapFor(this.art, this.mapId);
    if (this.visual !== undefined && this.visualUrl !== url) {
      this.visual.destroy(); // outro mapa: as camadas do anterior saem
      this.visual = undefined;
      this.decor = undefined;
      this.ground = undefined;
    }
    if (this.visual === undefined && url !== undefined && this.cache.tilemap.exists(mapKey(url))) {
      const map = this.make.tilemap({ key: mapKey(url) });
      const tilesets = map.tilesets
        .map((tileset) => (this.textures.exists(tileset.name) ? map.addTilesetImage(tileset.name, tileset.name) : null))
        .filter((tileset): tileset is Phaser.Tilemaps.Tileset => tileset !== null);
      if (tilesets.length === map.tilesets.length) {
        map.layers.forEach((layer, index) => {
          const created = map.createLayer(layer.name, tilesets, 0, 0).setDepth(index * 0.01);
          if (index === 0) {
            this.ground = created;
          }
        });
        this.visual = map;
        this.visualUrl = url;
        this.findDecor(map, mapKey(url));
        this.tinted = undefined; // a camada nova ainda não tem o tom da estação
        this.season = undefined;
      } else {
        map.destroy();
      }
    }
    const grid = this.grid;
    if (this.visual !== undefined || grid === undefined) {
      return;
    }
    for (let y = 0; y < grid.height; y++) {
      for (let x = 0; x < grid.width; x++) {
        const look = tileLook(this.art, tileAt(grid, x, y));
        this.terrain.fillStyle(colorNumber(look.color ?? "#000000"), 1).fillRect(x * TILE, y * TILE, TILE, TILE);
      }
    }
  }

  /** As entidades como o jogador as vê, com a névoa ligada; senão, todas. Redesenha a névoa
   * quando o recorte visível muda. */
  private fogged(state: ObserverState): ObserverState["entities"] {
    const id = this.follow;
    const at = id === undefined ? undefined : this.seen.get(id);
    const radius = id === undefined ? undefined : visionRadius(state, id);
    this.fogless = id !== undefined && radius === undefined; // o avatar vê o mundo inteiro
    if (!this.fogOn || id === undefined || at === undefined || radius === undefined) {
      if (this.fogDrawn) {
        this.fogLayer.clear();
        this.fogDrawn = false;
      }
      return state.entities;
    }
    if (this.fogStore !== undefined && !this.fogLoaded) {
      this.fog = this.fogStore.load(state.tick) ?? this.fog;
      this.fogLoaded = true;
      this.fogDrawn = false;
    }
    const tile = { x: Math.round(at.x), y: Math.round(at.y) };
    this.fogTick = state.tick;
    if (this.fog.look(state, tile, radius, serverCenter(state, id) ?? tile) || !this.fogDrawn) {
      this.drawFog();
      if (performance.now() - this.fogSavedAt > FOG_SAVE_MS) {
        this.saveFog();
      }
    }
    return this.fog.entities(state, id);
  }

  /** Guarda a lembrança da névoa no navegador, na visão do jogador. */
  rememberFog(store: FogStore): void {
    this.fogStore = store;
    this.fogLoaded = false;
  }

  saveFog(): void {
    if (this.fogStore !== undefined && this.fogLoaded) {
      this.fogStore.save(this.fog, this.fogTick);
      this.fogSavedAt = performance.now();
    }
  }

  /** A nuvem sobre o que nunca foi visto e o cinza sobre o que já foi, tile a tile. */
  private drawFog(): void {
    const grid = this.grid;
    if (grid === undefined) {
      return;
    }
    this.fogLayer.clear();
    for (let y = 0; y < grid.height; y++) {
      for (let x = 0; x < grid.width; x++) {
        const sight = this.fog.sight(x, y);
        if (sight === "visible") {
          this.drawHaze(x, y, grid);
          continue;
        }
        if (sight === "seen") {
          this.fogLayer.fillStyle(SEEN_COLOR, SEEN_ALPHA).fillRect(x * TILE, y * TILE, TILE, TILE);
          continue;
        }
        // Nuvem: um véu claro e, a cada poucos tiles, um tufo grande que passa por cima dos
        // vizinhos, em lugares que não se repetem em grade.
        const hash = (x * 73856093) ^ (y * 19349663);
        const puff = (Math.abs(hash) % 7) / 100;
        this.fogLayer.fillStyle(CLOUD_COLOR, 0.9 + puff).fillRect(x * TILE, y * TILE, TILE, TILE);
        if (Math.abs(hash) % 3 === 0) {
          const dx = (Math.abs(hash >> 3) % 24) - 4;
          const dy = (Math.abs(hash >> 7) % 24) - 4;
          this.fogLayer.fillStyle(0xf5f7f9, 0.22).fillCircle(x * TILE + dx, y * TILE + dy, 22);
        }
      }
    }
    this.fogDrawn = true;
  }

  /** O véu nos dois anéis de fora da vista, na cor do que está além (a nuvem ou o cinza do já
   * visto): a passagem à névoa fica gradual, e nada além do raio aparece. */
  private drawHaze(x: number, y: number, grid: TileGrid): void {
    const edge = this.fog.edge(x, y);
    const { beyond } = edge ?? { beyond: { x: -1, y: -1 } };
    if (edge === undefined || beyond.x < 0 || beyond.y < 0 || beyond.x >= grid.width || beyond.y >= grid.height) {
      return; // longe da borda, ou a borda é a do mapa
    }
    const cloud = this.fog.sight(beyond.x, beyond.y) === "unseen";
    const alpha = HAZE[edge.depth] ?? 0;
    this.fogLayer
      .fillStyle(cloud ? CLOUD_COLOR : SEEN_COLOR, (cloud ? 1 : SEEN_ALPHA) * alpha)
      .fillRect(x * TILE, y * TILE, TILE, TILE);
  }

  /** O que o jogador enxerga num tile, com a névoa ligada; sem névoa, nada. Num mundo sem raio
   * de visão (o escritório, que se vê inteiro), não há névoa: antes, tudo ficava "nunca visto", e o
   * clique direito só andava, sem o menu das pausas (ADR-0082). */
  sightAt(x: number, y: number): Sight | undefined {
    if (!this.fogOn || this.fogless) {
      return undefined;
    }
    return this.fog.sight(x, y);
  }


  /** Esquece o que foi visto: outra sessão, ou o operador desligou e ligou a névoa. */
  resetFog(): void {
    this.fog = new FogMemory();
    this.fogDrawn = false;
  }

  private drawThings(entities: ObserverState["entities"], time: number, frame: Frame): void {
    const seen = new Set<string>();
    for (const [id, entity] of Object.entries(entities)) {
      if (entity?.position === undefined || entity.kind === "avatar") {
        continue;
      }
      seen.add(id);
      let view = this.things.get(id);
      if (view === undefined) {
        view = new ThingView(this);
        this.things.set(id, view);
      }
      const { x, y } = entity.position;
      const kind = this.art.kinds?.[entity.kind];
      // Quem está ao lado de qualquer tile da coisa a usa (o bloco do banheiro tem 4 de largura).
      const users: string[] = [];
      const who: string[] = [];
      for (let dx = 0; dx < (kind?.width ?? 1); dx++) {
        users.push(...(this.using.get(`${String(x + dx)},${String(y)}`) ?? []));
        who.push(...(this.users.get(`${String(x + dx)},${String(y)}`) ?? []));
      }
      const seconds = time / 1000;
      const shop = workshopState(kind?.workshop, id, entity.attributes, frame.state, frame.tick, who);
      if (shop === undefined) {
        this.looks.delete(id);
      } else {
        this.looks.set(id, shop);
      }
      const busy =
        workshopFrame(kind?.workshop, shop, seconds) ??
        inUseFrame(kind?.in_use, users, seconds, this.doing) ??
        loopFrame(kind?.loop, seconds);
      view.show(this, lookOf(this.art, entity.kind, entity.attributes), x, y, busy);
    }
    for (const [id, view] of this.things) {
      if (!seen.has(id)) {
        view.destroy();
        this.things.delete(id);
        this.looks.delete(id);
      }
    }
  }

  /** Os balões da arte, prontos para desenhar, ou nada (as fazendas, ou as folhas a caminho). */
  private bubbleKit(): BubbleKit | undefined {
    const art = this.art.bubbles;
    if (art === undefined) {
      return undefined;
    }
    if (this.kit?.art !== art) {
      this.kit = new BubbleKit(this, art);
    }
    return this.kit.ready() ? this.kit : undefined;
  }

  private drawAvatars(frame: Frame, time: number): void {
    const { state, tick } = frame;
    const kit = this.bubbleKit();
    const mouse = this.input.activePointer;
    const pointer = this.input.isOver ? this.cameras.main.getWorldPoint(mouse.x, mouse.y) : undefined;
    const seen = new Set<string>();
    this.using.clear();
    this.users.clear();
    this.doing = [];
    for (const [id, entity] of Object.entries(state.entities)) {
      if (entity?.kind !== "avatar") {
        continue;
      }
      const motion = state.motion[id];
      // O relógio da página, o mesmo de quem observa os trajetos pelo evento (main.ts).
      const at: Point | undefined = this.motion.at(id, motion, entity.position, tick, performance.now());
      if (at === undefined) {
        continue;
      }
      seen.add(id);
      this.seen.set(id, at);
      let view = this.avatars.get(id);
      if (view === undefined) {
        view = new AvatarView(this, id);
        this.avatars.set(id, view);
      }
      const art = this.art.avatars?.[id] ?? this.art.avatars?.["*"];
      const said = this.balloons.current(id, performance.now());
      const seat = seatAt(this.art, state.entities, at);
      const doing = state.actions[id]?.action;
      if (doing !== undefined) {
        this.doing.push(doing);
        // Quem faz uma ação usa o que está ao lado dele: a mesa diante da cadeira, a máquina de
        // café, o micro-ondas no balcão, a porta do banheiro (ADR-0082).
        const [ax, ay] = [Math.round(at.x), Math.round(at.y)];
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const key = `${String(ax + dx)},${String(ay + dy)}`;
            this.using.set(key, [...(this.using.get(key) ?? []), doing]);
            this.users.set(key, [...(this.users.get(key) ?? []), id]);
          }
        }
      }
      view.show(this, lookOf(this.art, "avatar", entity.attributes), art, frame, id, at, time, this.bedOf(state, id), said, seat, kit, pointer);
    }
    for (const [id, view] of this.avatars) {
      if (!seen.has(id)) {
        view.destroy();
        this.avatars.delete(id);
      }
    }
    // Dois rótulos que se tocam, no sofá ou na mesa da copa, viram um só ou se empilham (18/nov).
    const labels = [...this.avatars].flatMap(([id, view]) => view.label(id) ?? []);
    for (const [id, placement] of declutter(labels)) {
      this.avatars.get(id)?.place(placement);
    }
  }

  /** A câmera: o mapa inteiro com zoom, ou seguindo o avatar, dentro dos limites do mapa. */
  private aim(): void {
    const grid = this.grid;
    if (grid === undefined) {
      return;
    }
    const cam = this.cameras.main;
    const width = grid.width * TILE;
    const height = grid.height * TILE;
    if (this.whole) {
      cam.removeBounds();
      cam.setZoom(Math.min(1, cam.width / width, cam.height / height));
      cam.centerOn(width / 2, height / 2);
      return;
    }
    cam.setZoom(1);
    cam.setBounds(0, 0, width, height);
    const at = this.follow === undefined ? undefined : this.seen.get(this.follow);
    if (this.following && at !== undefined) {
      cam.centerOn(at.x * TILE + TILE / 2, at.y * TILE + TILE / 2);
    }
  }

  /** O chão no tom da estação e as folhas da estação no mapa visual (ADR-0067); só muda quando
   * a estação muda. */
  private tint(season: string | undefined): void {
    if (this.visual !== undefined && season !== this.season) {
      for (const tileset of this.visual.tilesets) {
        const sheet = seasonSheet(this.art, season, tileset.name);
        if (this.textures.exists(sheet)) {
          tileset.setImage(this.textures.get(sheet));
        }
      }
      this.season = season;
    }
    const color = seasonTint(this.art, season);
    if (this.ground === undefined || color === this.tinted) {
      return;
    }
    if (this.ground instanceof Phaser.Tilemaps.TilemapLayer) {
      this.ground.setTint(colorNumber(color)); // a camada de GPU não tinge: fica sem o tom
    }
    this.tinted = color;
  }

  /** A cama do sono em andamento, onde está desenhada (o avatar dorme ao lado dela no mundo). */
  private bedOf(state: ObserverState, id: string): Bed | undefined {
    const bedId = state.sleep?.[id]?.bed_id;
    const bed = bedId === undefined ? undefined : state.entities[bedId];
    if (bed?.position === undefined) {
      return undefined;
    }
    const look = lookOf(this.art, bed.kind, bed.attributes);
    const height =
      look.sheet !== undefined && this.textures.exists(look.sheet)
        ? this.textures.getFrame(look.sheet, look.frame ?? 0).height * (look.scale ?? 1)
        : TILE;
    const bottom = (bed.position.y + 1) * TILE;
    return { cx: bed.position.x * TILE + TILE / 2, top: bottom - height, y: bed.position.y };
  }

  /** Gotas caindo em diagonal; a posição sai do tempo da tela, não do mundo (é só enfeite). */
  private drawRain(raining: boolean, time: number, width: number, height: number): void {
    this.rain.clear();
    if (!raining) {
      return;
    }
    this.rain.lineStyle(1, 0xaed6ff, 0.55);
    for (let i = 0; i < DROPS; i++) {
      const x = (i * 97 + time * 0.05) % (width + 40);
      const y = (i * 53 + time * 0.45) % (height + 40);
      this.rain.lineBetween(x - 20, y - 20, x - 23, y - 12);
    }
  }
}

/** WebGL quando a máquina tem; senão, o Canvas (o Phaser no modo AUTO aborta se o WebGL falhar depois
 * de parecer disponível, como num Chromium sem GPU). */
/** O armazenamento do navegador, quando há; numa aba que o bloqueia, nenhum. */
function browserStorage(): Storage | undefined {
  try {
    return localStorage;
  } catch {
    return undefined;
  }
}

function rendererType(): number {
  const probe = document.createElement("canvas");
  const gl = probe.getContext("webgl2") ?? probe.getContext("webgl");
  return gl === null ? Phaser.CANVAS : Phaser.WEBGL;
}

export class PhaserRenderer implements WorldRenderer {
  readonly element: HTMLElement;
  private readonly scene = new WorldScene();
  readonly motion = this.scene.motion;

  speak(avatarId: string, text: string): void {
    this.scene.balloons.hear(avatarId, text, performance.now());
  }
  private readonly game: Phaser.Game;
  private size = { width: 32, height: 18 };
  private grid = { width: 32, height: 18 };
  private savesOnHide = false;
  private drag: { x: number; y: number; moved: boolean } | undefined;
  private swallowClick = false;
  private readonly followButton: HTMLButtonElement;
  private readonly wholeButton: HTMLButtonElement;
  private readonly fogButton: HTMLButtonElement;
  private fogMode: "always" | "toggle" | "off" = "off";

  constructor() {
    this.followButton = el("button", { className: "map-button" }, "Seguir o avatar");
    this.wholeButton = el("button", { className: "map-button" }, "Mapa inteiro");
    this.fogButton = el("button", { className: "map-button" }, "Ver como o avatar");
    this.element = el(
      "div",
      { className: "phaser" },
      el("div", { className: "map-buttons" }, this.fogButton, this.followButton, this.wholeButton),
    );
    this.listen();
    this.game = new Phaser.Game({
      type: rendererType(),
      parent: this.element,
      width: this.size.width * TILE,
      height: this.size.height * TILE,
      pixelArt: true,
      backgroundColor: "#111111",
      banner: false,
      input: false,
      audio: { noAudio: true },
      scale: { mode: Phaser.Scale.NONE },
      scene: this.scene,
    });
  }

  setGrid(grid: TileGrid): void {
    this.scene.grid = grid;
    this.scene.terrainDirty = true;
    this.grid = { width: grid.width, height: grid.height };
    // O canvas tem no máximo o tamanho da tela; o resto do mapa a câmera mostra (ADR-0067).
    const width = Math.min(grid.width, VIEW.width);
    const height = Math.min(grid.height, VIEW.height);
    if (width !== this.size.width || height !== this.size.height) {
      this.size = { width, height };
      this.game.scale.resize(width * TILE, height * TILE);
    }
    this.buttons();
  }

  /** Quem a câmera segue, num mapa maior que a tela. */
  follow(entityId: string): void {
    this.scene.follow = entityId;
  }

  recenter(): void {
    this.scene.following = true;
    this.scene.whole = false;
    this.buttons();
  }

  private big(): boolean {
    return this.grid.width > VIEW.width || this.grid.height > VIEW.height;
  }

  /** A lembrança da névoa no navegador, por mundo e avatar; guardada também ao sair da página. */
  rememberFog(key: string): void {
    this.scene.rememberFog(new FogStore(key, browserStorage()));
    if (!this.savesOnHide) {
      this.savesOnHide = true;
      addEventListener("pagehide", () => {
        this.scene.saveFog();
      });
    }
  }

  /** A névoa (ADR-0068): sempre na visão do jogador; o operador liga e desliga. */
  setFog(mode: "always" | "toggle"): void {
    this.fogMode = mode;
    this.scene.fogOn = mode === "always";
    this.buttons();
  }

  private buttons(): void {
    this.fogButton.hidden = this.fogMode !== "toggle" || this.fogButton.hidden;
    this.fogButton.textContent = this.scene.fogOn ? "Ver tudo" : "Ver como o avatar";
    const big = this.big();
    this.followButton.hidden = !big || (this.scene.following && !this.scene.whole);
    this.wholeButton.hidden = !big || this.scene.whole;
  }

  /** Arrastar com o botão esquerdo rola o mapa; o clique que termina um arrasto não conta. */
  private listen(): void {
    const stop = (event: Event): void => {
      event.stopPropagation(); // o botão não é um clique no mapa
    };
    this.followButton.addEventListener("click", (event) => {
      stop(event);
      this.recenter();
    });
    this.wholeButton.addEventListener("click", (event) => {
      stop(event);
      this.scene.whole = true;
      this.buttons();
    });
    this.fogButton.addEventListener("click", (event) => {
      stop(event);
      this.scene.fogOn = !this.scene.fogOn;
      this.scene.resetFog(); // o operador vê de novo pelos olhos do avatar, do zero
      this.buttons();
    });
    this.fogButton.addEventListener("contextmenu", stop);
    this.followButton.addEventListener("contextmenu", stop);
    this.wholeButton.addEventListener("contextmenu", stop);
    this.element.addEventListener("pointerdown", (event) => {
      const onCanvas = event.target instanceof HTMLCanvasElement;
      this.drag = event.button === 0 && onCanvas && this.big() ? { x: event.clientX, y: event.clientY, moved: false } : undefined;
    });
    window.addEventListener("pointermove", (event) => {
      const drag = this.drag;
      if (drag === undefined) {
        return;
      }
      const dx = event.clientX - drag.x;
      const dy = event.clientY - drag.y;
      if (!drag.moved && Math.hypot(dx, dy) < DRAG) {
        return;
      }
      drag.moved = true;
      const canvas = this.game.canvas;
      const box = canvas.getBoundingClientRect();
      const cam = this.scene.cameras.main;
      const scale = box.width === 0 ? 1 : canvas.width / box.width;
      this.scene.whole = false;
      this.scene.following = false;
      cam.setZoom(1);
      cam.scrollX -= (dx * scale) / cam.zoom;
      cam.scrollY -= (dy * scale) / cam.zoom;
      drag.x = event.clientX;
      drag.y = event.clientY;
      this.buttons();
    });
    window.addEventListener("pointerup", () => {
      this.swallowClick = this.drag?.moved === true;
      this.drag = undefined;
    });
    this.element.addEventListener(
      "click",
      (event) => {
        if (this.swallowClick) {
          event.stopImmediatePropagation();
          this.swallowClick = false;
        }
      },
      { capture: true },
    );
  }

  setArt(art: ArtManifest): void {
    this.scene.art = art;
    this.scene.terrainDirty = true;
    this.scene.loadArt(); // antes do create, quem carrega é o próprio create
  }

  draw(state: ObserverState, tick: number): void {
    this.scene.frame = { state, tick };
    // Sem raio (as fazendas 1 e 2), não há névoa: o botão do operador não aparece.
    const follow = this.scene.follow;
    const radius = follow === undefined ? undefined : visionRadius(state, follow);
    const toggle = this.fogMode === "toggle" && radius !== undefined;
    if (this.fogButton.hidden === toggle) {
      this.fogButton.hidden = !toggle;
    }
  }

  sight(x: number, y: number): Sight | undefined {
    return this.scene.sightAt(x, y);
  }

  workshopLook(entityId: string): string | undefined {
    return this.scene.looks.get(entityId);
  }

  clientOf(x: number, y: number): { x: number; y: number } | undefined {
    if (!this.scene.created) {
      return undefined;
    }
    const canvas = this.game.canvas;
    const box = canvas.getBoundingClientRect();
    const cam = this.scene.cameras.main;
    // Do mundo ao pixel do canvas (o inverso de getWorldPoint), e dele à tela.
    const px = (x * TILE + TILE / 2 - cam.worldView.x) * cam.zoom;
    const py = (y * TILE + TILE / 2 - cam.worldView.y) * cam.zoom;
    return { x: box.left + (px * box.width) / canvas.width, y: box.top + (py * box.height) / canvas.height };
  }

  tileAt(clientX: number, clientY: number): { x: number; y: number } | undefined {
    if (!this.scene.created) {
      return tileUnder(this.game.canvas, TILE, clientX, clientY); // antes da cena, sem câmera
    }
    const camera = this.scene.cameras.main;
    const canvas = this.game.canvas;
    const box = canvas.getBoundingClientRect();
    if (box.width === 0 || box.height === 0) {
      return undefined;
    }
    // Do ponto da tela ao pixel do canvas, e dele ao mundo pela câmera (rolagem e zoom).
    const point = camera.getWorldPoint(
      ((clientX - box.left) * canvas.width) / box.width,
      ((clientY - box.top) * canvas.height) / box.height,
    );
    const x = Math.floor(point.x / TILE);
    const y = Math.floor(point.y / TILE);
    const inside = x >= 0 && y >= 0 && x < this.grid.width && y < this.grid.height;
    return inside ? { x, y } : undefined;
  }
}
