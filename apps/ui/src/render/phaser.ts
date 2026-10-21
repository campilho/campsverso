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
  shadeOf,
  tileLook,
  weatherEffect,
  type ArtManifest,
  type AvatarArt,
  type Facing,
  type Resolved,
} from "../art/manifest.ts";
import { el } from "../dom.ts";
import { motionClock, type Point } from "../motion.ts";
import { progressOf } from "../progress.ts";
import { tileAt, type TileGrid } from "../tiled.ts";
import { tileUnder, type WorldRenderer } from "./renderer.ts";

const TILE = 32;
const DROPS = 140;
const FONT = "ui-monospace, monospace";
const MAP_KEY = "visual-map";
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
  private created = false;
  private terrain!: Phaser.GameObjects.Graphics;
  private shade!: Phaser.GameObjects.Rectangle;
  private rain!: Phaser.GameObjects.Graphics;
  private visual: Phaser.Tilemaps.Tilemap | undefined;
  private readonly things = new Map<string, ThingView>();
  private readonly avatars = new Map<string, AvatarView>();

  constructor() {
    super({ key: "world" });
  }

  create(): void {
    this.terrain = this.add.graphics().setDepth(0);
    this.shade = this.add.rectangle(0, 0, 1, 1, 0x0c123c, 0).setOrigin(0).setDepth(80);
    this.rain = this.add.graphics().setDepth(81);
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
    if (this.art.visual_map !== undefined && !this.cache.tilemap.exists(MAP_KEY)) {
      this.load.tilemapTiledJSON(MAP_KEY, this.art.visual_map);
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
    this.drawThings(state);
    this.drawAvatars(frame, time);
    this.shade.setSize(width, height).setFillStyle(0x0c123c, shadeOf(this.art, state.phase));
    this.drawRain(weatherEffect(this.art, state.weather[String(state.day)]) === "rain", time, width, height);
  }

  /** O mapa visual do cartucho, quando há; senão, uma cor por tipo de tile do mapa lógico. */
  private drawTerrain(): void {
    this.terrain.clear();
    if (this.visual === undefined && this.cache.tilemap.exists(MAP_KEY)) {
      const map = this.make.tilemap({ key: MAP_KEY });
      const tilesets = map.tilesets
        .map((tileset) => (this.textures.exists(tileset.name) ? map.addTilesetImage(tileset.name, tileset.name) : null))
        .filter((tileset): tileset is Phaser.Tilemaps.Tileset => tileset !== null);
      if (tilesets.length === map.tilesets.length) {
        map.layers.forEach((layer, index) => {
          map.createLayer(layer.name, tilesets, 0, 0).setDepth(index * 0.01);
        });
        this.visual = map;
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

  private drawThings(state: ObserverState): void {
    const seen = new Set<string>();
    for (const [id, entity] of Object.entries(state.entities)) {
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

  constructor() {
    this.element = el("div", { className: "phaser" });
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
    if (grid.width !== this.size.width || grid.height !== this.size.height) {
      this.size = { width: grid.width, height: grid.height };
      this.game.scale.resize(grid.width * TILE, grid.height * TILE);
    }
  }

  setArt(art: ArtManifest): void {
    this.scene.art = art;
    this.scene.terrainDirty = true;
    this.scene.loadArt(); // antes do create, quem carrega é o próprio create
  }

  draw(state: ObserverState, tick: number): void {
    this.scene.frame = { state, tick };
  }

  tileAt(clientX: number, clientY: number): { x: number; y: number } | undefined {
    return tileUnder(this.game.canvas, TILE, clientX, clientY);
  }
}
