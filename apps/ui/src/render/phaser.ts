/** O renderer Phaser (M6; ADR-0053): o mesmo estado do canvas de depuração, com a arte dos cartuchos.
 *
 * Desenha; não decide nada (escopo §9). A aparência de cada coisa vem do manifesto de arte; o que
 * ele não conhece vira um quadrado de cor estável. O Phaser só desenha: os cliques ficam com a
 * página (main.ts), que pergunta `tileAt`.
 */
import type { ObserverState } from "@campsverso/contracts";
import Phaser from "phaser";

import {
  EMPTY,
  animationFor,
  colorNumber,
  facingOf,
  frameOf,
  lookOf,
  seasonSheet,
  seasonTint,
  shadeOf,
  tileLook,
  visualMapFor,
  weatherEffect,
  type ArtManifest,
  type AvatarArt,
  type Facing,
  type Resolved,
} from "../art/manifest.ts";
import { el } from "../dom.ts";
import { FogMemory, FogStore, lightHeld, visionRadius, type Sight } from "../fog.ts";
import { motionClock, type Point } from "../motion.ts";
import { progressOf } from "../progress.ts";
import { tileAt, type TileGrid } from "../tiled.ts";
import { tileUnder, type WorldRenderer } from "./renderer.ts";

const TILE = 32;
const DROPS = 140;
const CLOUD_COLOR = 0xdde2e8; // a névoa sobre o que nunca foi visto
const SEEN_COLOR = 0x6f7782; // o cinza sobre o que já foi visto
const SEEN_ALPHA = 0.5;
const HAZE = [0.5, 0.22]; // o véu do anel de fora da vista e o do seguinte, em fração da névoa
const LIGHT_RINGS = 20; // anéis da luz à noite, do mais largo ao mais estreito (sem degraus à vista)
const FONT = "ui-monospace, monospace";
const FOG_SAVE_MS = 1000; // a lembrança da névoa vai ao navegador no máximo uma vez por segundo
// Um mapa visual por endereço: as variantes do mapa (ADR-0070) têm cada uma o seu.
const mapKey = (url: string): string => `visual-map:${url}`;
// A tela mostra no máximo 32 × 18 tiles; um mapa maior (a Morada do Sol, ADR-0067) rola com a câmera.
const VIEW = { width: 32, height: 18 };
const DRAG = 6; // pixels de arrasto antes de virar arrastar, e não clique
const FEET = 2; // os pés do LPC ficam um pouco acima da borda do quadro

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
  private readonly label: Phaser.GameObjects.Text;
  private readonly badge: Phaser.GameObjects.Arc;

  constructor(scene: Phaser.Scene) {
    this.box = scene.add.rectangle(0, 0, TILE - 6, TILE - 6, 0xffffff).setStrokeStyle(1, 0x000000, 0.45);
    this.image = scene.add.image(0, 0, "__DEFAULT").setVisible(false).setOrigin(0.5, 1);
    this.label = scene.add.text(0, 0, "", { fontFamily: FONT, fontSize: "9px", color: "#ffffff" }).setOrigin(0.5);
    this.badge = scene.add.circle(0, 0, 3.5, 0x4fc3f7).setVisible(false).setStrokeStyle(1, 0x0b3d5c);
  }

  show(scene: Phaser.Scene, look: Resolved, x: number, y: number): void {
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
    this.image.setVisible(sheet !== undefined).setPosition(cx, (y + 1) * TILE).setDepth(depth);
    if (sheet !== undefined) {
      this.image.setTexture(sheet, look.frame ?? 0).setScale(look.scale ?? 1);
      if (look.tint === undefined) {
        this.image.clearTint();
      } else {
        this.image.setTint(colorNumber(look.tint));
      }
    }
    this.label.setText(sheet === undefined ? (look.label ?? "") : "").setPosition(cx, cy + 1).setDepth(depth + 0.1);
    const [badge] = look.badges;
    this.badge.setVisible(badge !== undefined).setPosition(x * TILE + TILE - 6, y * TILE + TILE - 6).setDepth(depth + 0.2);
    if (badge !== undefined) {
      this.badge.setFillStyle(colorNumber(badge));
    }
  }

  destroy(): void {
    for (const object of [this.box, this.image, this.label, this.badge]) {
      object.destroy();
    }
  }
}

/** Um avatar: o sprite animado (ou um círculo, sem arte), o rótulo da ação e a barra de progresso. */
class AvatarView {
  private readonly body: Phaser.GameObjects.Arc;
  private readonly initial: Phaser.GameObjects.Text;
  private readonly sprite: Phaser.GameObjects.Sprite;
  private readonly tag: Phaser.GameObjects.Text;
  private readonly bar: Phaser.GameObjects.Graphics;
  private facing: Facing = "down";
  private last: Point | undefined;
  private walked = 0;
  private animation: string | undefined;
  private since = 0;

  constructor(scene: Phaser.Scene, id: string) {
    this.body = scene.add.circle(0, 0, TILE * 0.34, 0xf5f5f5).setStrokeStyle(2, 0x1b1b1b);
    this.initial = scene.add
      .text(0, 0, id.slice(0, 1).toUpperCase(), { fontFamily: FONT, fontSize: "12px", color: "#1b1b1b", fontStyle: "bold" })
      .setOrigin(0.5);
    this.sprite = scene.add.sprite(0, 0, "__DEFAULT").setOrigin(0.5, 1).setVisible(false);
    this.tag = scene.add
      .text(0, 0, "", { fontFamily: FONT, fontSize: "11px", color: "#ffe08a", fontStyle: "bold", backgroundColor: "rgba(20,20,20,0.8)", padding: { x: 4, y: 1 } })
      .setOrigin(0.5, 1)
      .setDepth(60);
    this.bar = scene.add.graphics().setDepth(60);
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
  ): void {
    const { state, tick } = frame;
    const cx = at.x * TILE + TILE / 2;
    const depth = depthAt(at.y) + 0.5;
    const action = state.actions[id];
    const asleep = state.asleep[id] === true;
    const moved = this.last === undefined ? { x: 0, y: 0 } : { x: at.x - this.last.x, y: at.y - this.last.y };
    this.walked += Math.hypot(moved.x, moved.y);
    this.last = at;
    const target = action?.params.target;
    const thing = typeof target === "string" ? state.entities[target]?.position : undefined;
    this.facing =
      action?.action === "move" || thing === undefined
        ? facingOf(moved.x, moved.y, this.facing)
        : facingOf(thing.x - at.x, thing.y - at.y, this.facing);

    const name = animationFor(art, action?.action, asleep);
    const animation = name === undefined ? undefined : art?.animations?.[name];
    const sheet = art !== undefined && scene.textures.exists(art.sheet) ? art.sheet : undefined;
    if (name !== this.animation) {
      this.animation = name;
      this.since = time;
    }
    const inBed = asleep && bed !== undefined && sheet !== undefined ? art?.in_bed : undefined;
    const drawn = sheet !== undefined && (animation !== undefined || inBed !== undefined);
    this.body.setVisible(!drawn).setPosition(cx, at.y * TILE + TILE / 2).setDepth(depth);
    this.body.setFillStyle(colorNumber(look.color ?? "#f5f5f5"));
    this.initial.setVisible(!drawn).setPosition(cx, at.y * TILE + TILE / 2 + 1).setDepth(depth + 0.01);
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
      this.sprite.setCrop().setOrigin(0.5, 1).setScale(1).setPosition(cx, (at.y + 1) * TILE + FEET).setDepth(depth);
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

    const progress = progressOf(state, id, tick);
    const above = inBed !== undefined && bed !== undefined ? { cx: bed.cx, top: bed.top - 2 } : undefined;
    const tx = above?.cx ?? cx;
    const top = above?.top ?? (drawn ? (at.y + 1) * TILE - 50 : at.y * TILE - 4);
    this.tag.setVisible(progress !== undefined).setText(progress?.label ?? "").setPosition(tx, top - 3);
    this.bar.clear();
    if (progress?.fraction !== undefined) {
      const width = TILE - 4;
      this.bar.fillStyle(0x141414, 0.8).fillRect(tx - width / 2 - 1, top - 1, width + 2, 6);
      this.bar.fillStyle(0x7bd88f, 1).fillRect(tx - width / 2, top, width * progress.fraction, 4);
    }
  }

  destroy(): void {
    for (const object of [this.body, this.initial, this.sprite, this.tag, this.bar]) {
      object.destroy();
    }
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
  private readonly avatars = new Map<string, AvatarView>();
  private readonly seen = new Map<string, Point>(); // onde cada avatar aparece agora, em tiles
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
    this.drawThings(this.fogged(state));
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

  /** O mapa visual do cartucho, quando há; senão, uma cor por tipo de tile do mapa lógico. */
  private drawTerrain(): void {
    this.terrain.clear();
    const url = visualMapFor(this.art, this.mapId);
    if (this.visual !== undefined && this.visualUrl !== url) {
      this.visual.destroy(); // outro mapa: as camadas do anterior saem
      this.visual = undefined;
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
    if (this.fog.look(state, tile, radius) || !this.fogDrawn) {
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

  /** O que o jogador enxerga num tile, com a névoa ligada; sem névoa, nada. */
  sightAt(x: number, y: number): Sight | undefined {
    return this.fogOn ? this.fog.sight(x, y) : undefined;
  }

  /** Esquece o que foi visto: outra sessão, ou o operador desligou e ligou a névoa. */
  resetFog(): void {
    this.fog = new FogMemory();
    this.fogDrawn = false;
  }

  private drawThings(entities: ObserverState["entities"]): void {
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
      view.show(this, lookOf(this.art, entity.kind, entity.attributes), entity.position.x, entity.position.y);
    }
    for (const [id, view] of this.things) {
      if (!seen.has(id)) {
        view.destroy();
        this.things.delete(id);
      }
    }
  }

  private drawAvatars(frame: Frame, time: number): void {
    const { state, tick } = frame;
    const seen = new Set<string>();
    for (const [id, entity] of Object.entries(state.entities)) {
      if (entity?.kind !== "avatar") {
        continue;
      }
      const motion = state.motion[id];
      const at: Point | undefined = motionClock.at(id, motion, entity.position, tick, time);
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
      view.show(this, lookOf(this.art, "avatar", entity.attributes), art, frame, id, at, time, this.bedOf(state, id));
    }
    for (const [id, view] of this.avatars) {
      if (!seen.has(id)) {
        view.destroy();
        this.avatars.delete(id);
      }
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
