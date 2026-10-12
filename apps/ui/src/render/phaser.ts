/** O renderer Phaser (M6; ADR-0053): o mesmo estado do canvas de depuração, com a arte dos cartuchos.
 *
 * Desenha; não decide nada (escopo §9). A aparência de cada coisa vem do manifesto de arte; o que
 * ele não conhece vira um quadrado de cor estável. O Phaser só desenha: os cliques ficam com a
 * página (main.ts), que pergunta `tileAt`.
 */
import type { ObserverState } from "@campsverso/contracts";
import Phaser from "phaser";

import { EMPTY, colorNumber, lookOf, shadeOf, tileLook, weatherEffect, type ArtManifest, type Resolved } from "../art/manifest.ts";
import { el } from "../dom.ts";
import { positionAt, type Point } from "../motion.ts";
import { progressOf } from "../progress.ts";
import { tileAt, type TileGrid } from "../tiled.ts";
import { tileUnder, type WorldRenderer } from "./renderer.ts";

const TILE = 32;
const DROPS = 140;
const FONT = "ui-monospace, monospace";

interface Frame {
  readonly state: ObserverState;
  readonly tick: number;
}

/** Uma entidade parada no mapa: um quadro da arte, ou um quadrado de cor com rótulo. */
class ThingView {
  private readonly box: Phaser.GameObjects.Rectangle;
  private readonly image: Phaser.GameObjects.Image;
  private readonly label: Phaser.GameObjects.Text;
  private readonly badge: Phaser.GameObjects.Arc;

  constructor(scene: Phaser.Scene) {
    this.box = scene.add.rectangle(0, 0, TILE - 6, TILE - 6, 0xffffff).setStrokeStyle(1, 0x000000, 0.45).setDepth(10);
    this.image = scene.add.image(0, 0, "__DEFAULT").setVisible(false).setDepth(10);
    this.label = scene.add.text(0, 0, "", { fontFamily: FONT, fontSize: "9px", color: "#ffffff" }).setOrigin(0.5).setDepth(11);
    this.badge = scene.add.circle(0, 0, 3.5, 0x4fc3f7).setVisible(false).setDepth(11);
  }

  show(scene: Phaser.Scene, look: Resolved, x: number, y: number): void {
    const cx = x * TILE + TILE / 2;
    const cy = y * TILE + TILE / 2;
    const sheet = look.sheet !== undefined && scene.textures.exists(look.sheet) ? look.sheet : undefined;
    const sprite = sheet !== undefined;
    this.box.setVisible(!sprite).setPosition(cx, cy).setFillStyle(colorNumber(look.color ?? "#ff00ff"));
    this.image.setVisible(sprite).setPosition(cx, cy);
    if (sheet !== undefined) {
      this.image.setTexture(sheet, look.frame ?? 0);
      if (look.tint === undefined) {
        this.image.clearTint();
      } else {
        this.image.setTint(colorNumber(look.tint));
      }
    }
    this.label.setText(sprite ? "" : (look.label ?? "")).setPosition(cx, cy + 1);
    const [badge] = look.badges;
    this.badge.setVisible(badge !== undefined).setPosition(x * TILE + TILE - 7, y * TILE + 7);
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

/** Um avatar: o corpo, o rótulo da ação e a barra de progresso (ADR-0052). */
class AvatarView {
  private readonly body: Phaser.GameObjects.Arc;
  private readonly initial: Phaser.GameObjects.Text;
  private readonly tag: Phaser.GameObjects.Text;
  private readonly bar: Phaser.GameObjects.Graphics;

  constructor(scene: Phaser.Scene, id: string) {
    this.body = scene.add.circle(0, 0, TILE * 0.34, 0xf5f5f5).setStrokeStyle(2, 0x1b1b1b).setDepth(20);
    this.initial = scene.add
      .text(0, 0, id.slice(0, 1).toUpperCase(), { fontFamily: FONT, fontSize: "12px", color: "#1b1b1b", fontStyle: "bold" })
      .setOrigin(0.5)
      .setDepth(21);
    this.tag = scene.add
      .text(0, 0, "", { fontFamily: FONT, fontSize: "11px", color: "#ffe08a", fontStyle: "bold", backgroundColor: "rgba(20,20,20,0.8)", padding: { x: 4, y: 1 } })
      .setOrigin(0.5, 1)
      .setDepth(30);
    this.bar = scene.add.graphics().setDepth(30);
  }

  show(look: Resolved, at: Point, progress: ReturnType<typeof progressOf>): void {
    const cx = at.x * TILE + TILE / 2;
    const cy = at.y * TILE + TILE / 2;
    this.body.setPosition(cx, cy).setFillStyle(colorNumber(look.color ?? "#f5f5f5"));
    this.initial.setPosition(cx, cy + 1);
    this.tag.setVisible(progress !== undefined).setText(progress?.label ?? "").setPosition(cx, at.y * TILE - 6);
    this.bar.clear();
    if (progress?.fraction !== undefined) {
      const width = TILE - 4;
      const top = at.y * TILE - 4;
      this.bar.fillStyle(0x141414, 0.8).fillRect(cx - width / 2 - 1, top - 1, width + 2, 6);
      this.bar.fillStyle(0x7bd88f, 1).fillRect(cx - width / 2, top, width * progress.fraction, 4);
    }
  }

  destroy(): void {
    for (const object of [this.body, this.initial, this.tag, this.bar]) {
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
  private readonly things = new Map<string, ThingView>();
  private readonly avatars = new Map<string, AvatarView>();

  constructor() {
    super({ key: "world" });
  }

  create(): void {
    this.terrain = this.add.graphics().setDepth(0);
    this.shade = this.add.rectangle(0, 0, 1, 1, 0x0c123c, 0).setOrigin(0).setDepth(40);
    this.rain = this.add.graphics().setDepth(41);
    this.created = true;
    this.loadSheets();
  }

  /** Carrega as folhas do manifesto que ainda não estão na memória (depois do `create`). */
  loadSheets(): void {
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
    const { state, tick } = frame;
    this.drawThings(state);
    this.drawAvatars(state, tick);
    this.shade.setSize(width, height).setFillStyle(0x0c123c, shadeOf(this.art, state.phase));
    this.drawRain(weatherEffect(this.art, state.weather[String(state.day)]) === "rain", time, width, height);
  }

  private drawTerrain(): void {
    const grid = this.grid;
    this.terrain.clear();
    if (grid === undefined) {
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

  private drawAvatars(state: ObserverState, tick: number): void {
    const seen = new Set<string>();
    for (const [id, entity] of Object.entries(state.entities)) {
      if (entity?.kind !== "avatar") {
        continue;
      }
      const motion = state.motion[id];
      const at: Point | undefined = motion === undefined ? entity.position : positionAt(motion, tick);
      if (at === undefined) {
        continue;
      }
      seen.add(id);
      let view = this.avatars.get(id);
      if (view === undefined) {
        view = new AvatarView(this, id);
        this.avatars.set(id, view);
      }
      view.show(lookOf(this.art, "avatar", entity.attributes), at, progressOf(state, id, tick));
    }
    for (const [id, view] of this.avatars) {
      if (!seen.has(id)) {
        view.destroy();
        this.avatars.delete(id);
      }
    }
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

export class PhaserRenderer implements WorldRenderer {
  readonly element: HTMLElement;
  private readonly scene = new WorldScene();
  private readonly game: Phaser.Game;
  private size = { width: 32, height: 18 };

  constructor() {
    this.element = el("div", { className: "phaser" });
    this.game = new Phaser.Game({
      type: Phaser.AUTO,
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
    this.scene.loadSheets(); // antes do create, quem carrega é o próprio create
  }

  draw(state: ObserverState, tick: number): void {
    this.scene.frame = { state, tick };
  }

  tileAt(clientX: number, clientY: number): { x: number; y: number } | undefined {
    return tileUnder(this.game.canvas, TILE, clientX, clientY);
  }
}
