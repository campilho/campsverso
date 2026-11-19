/** O que fica sobre a cabeça de um avatar: o que ele faz, o progresso e o que ele disse.
 *
 * Com a arte dos balões do escritório (o pedido de 18/nov, `bubbles` no manifesto), um balão
 * pequeno com o ícone da ação e o progresso num fio na base; a etiqueta escura com o nome, ao passar
 * o mouse ou para a ação sem ícone; e o balão de fala com a ponta, na fonte pixel. Sem essa arte (as
 * fazendas), o rótulo de texto, a barra e o balão de antes (ADR-0052, ADR-0078).
 */
import Phaser from "phaser";

import type { Bubbles } from "../art/manifest.ts";
import { drawBox, tint, wrapText } from "../art/textbox.ts";
import type { Label, Placement } from "../declutter.ts";
import type { Progress } from "../progress.ts";

const FONT = "ui-monospace, monospace";
const NO_WRAP = 1000;

function color(hex: string): number {
  return Number.parseInt(hex.replace("#", ""), 16);
}

/** As folhas dos balões já carregadas, os quadros e as caixas de texto, por cena. */
export class BubbleKit {
  readonly art: Bubbles;
  private readonly scene: Phaser.Scene;
  private readonly tinted = new Map<string, HTMLCanvasElement>();
  private serial = 0;

  constructor(scene: Phaser.Scene, art: Bubbles) {
    this.scene = scene;
    this.art = art;
  }

  /** As três folhas (os balões, os ícones e a fonte) chegaram. */
  ready(): boolean {
    const { textures } = this.scene;
    return textures.exists(this.art.sheet) && textures.exists(this.art.icons.sheet) && (this.art.font === undefined || textures.exists(this.art.font.sheet));
  }

  get sheet(): string {
    return this.art.sheet;
  }

  /** O quadro do balão de ação na folha dos balões, criado na primeira vez. */
  actionFrame(): string {
    const texture = this.scene.textures.get(this.art.sheet);
    if (!texture.has("acao")) {
      const [x, y, w, h] = this.art.action.rect;
      texture.add("acao", 0, x, y, w, h);
    }
    return "acao";
  }

  /** O quadro do ícone de uma ação (o sono é `sleep`), ou nada quando ela não tem ícone. */
  icon(action: string | undefined): number | undefined {
    const name = action === undefined ? undefined : this.art.icons.actions?.[action];
    const at = name === undefined ? undefined : this.art.icons.frames[name];
    return at === undefined ? undefined : at[1] * this.art.icons.columns + at[0];
  }

  /** Monta uma caixa (a etiqueta ou a fala) numa textura nova; devolve a chave e o bico. */
  box(kind: "label" | "speech", text: string): { key: string; origin: readonly [number, number]; width: number; height: number } | undefined {
    const frame = kind === "label" ? this.art.label : this.art.speech;
    const font = this.art.font;
    if (frame === undefined || font === undefined) {
      return undefined;
    }
    const { textures } = this.scene;
    const sheet = textures.get(this.art.sheet).getSourceImage() as CanvasImageSource;
    const lines = wrapText(font, text, frame.max_width ?? NO_WRAP, frame.lines);
    const { canvas, anchor } = drawBox(sheet, this.glyphs(frame.color), font, frame, lines);
    this.serial += 1;
    const key = `caixa-${String(this.serial)}`;
    const texture = textures.addCanvas(key, canvas);
    texture?.setFilter(Phaser.Textures.FilterMode.NEAREST);
    return { key, origin: [anchor[0] / canvas.width, anchor[1] / canvas.height], width: canvas.width, height: canvas.height };
  }

  /** Solta a textura de uma caixa que saiu da tela. */
  drop(key: string | undefined): void {
    if (key !== undefined && this.scene.textures.exists(key)) {
      this.scene.textures.remove(key);
    }
  }

  /** A folha da fonte tingida de uma cor, feita uma vez por cor. */
  private glyphs(hex: string): HTMLCanvasElement {
    let canvas = this.tinted.get(hex);
    if (canvas === undefined) {
      const source = this.scene.textures.get(this.art.font?.sheet ?? "").getSourceImage() as HTMLImageElement;
      canvas = tint(source, source.width, source.height, hex);
      this.tinted.set(hex, canvas);
    }
    return canvas;
  }
}

/** O que o avatar mostra sobre a cabeça neste quadro. */
export interface HeadInput {
  readonly kit: BubbleKit | undefined;
  /** O que a câmera mostra: nada sai da tela. */
  readonly view: Phaser.Geom.Rectangle;
  /** O meio da cabeça e a altura onde o rótulo pousa. */
  readonly x: number;
  readonly top: number;
  readonly progress: Progress | undefined;
  /** A ação de que sai o ícone (`sleep` no sono). */
  readonly action: string | undefined;
  /** Sentado à mesa, de costas: o balão vai para o lado da cabeça, para não cobrir o monitor. */
  readonly atDesk: boolean;
  readonly said: string | undefined;
  /** O texto da etiqueta com o mouse em cima: o nome e o que faz. */
  readonly hover: string | undefined;
}

/** Uma caixa de texto montada: a imagem, a textura e o texto dela. */
class Box {
  readonly image: Phaser.GameObjects.Image;
  private key: string | undefined;
  private text: string | undefined;

  constructor(scene: Phaser.Scene, depth: number) {
    this.image = scene.add.image(0, 0, "__DEFAULT").setDepth(depth).setVisible(false);
  }

  /** Mostra o texto (refaz a textura só quando ele muda); devolve falso se a arte não deu. */
  show(kit: BubbleKit, kind: "label" | "speech", text: string): boolean {
    if (text !== this.text || this.key === undefined) {
      const made = kit.box(kind, text);
      if (made === undefined) {
        return false;
      }
      this.image.setTexture(made.key).setOrigin(made.origin[0], made.origin[1]);
      kit.drop(this.key);
      this.key = made.key;
      this.text = text;
    }
    this.image.setVisible(true);
    return true;
  }

  hide(): void {
    this.image.setVisible(false);
  }

  destroy(kit: BubbleKit | undefined): void {
    kit?.drop(this.key);
    this.image.destroy();
  }
}

export class HeadView {
  private readonly scene: Phaser.Scene;
  // Sem a arte dos balões: o rótulo de texto, a barra e o balão de fala de antes.
  private readonly tag: Phaser.GameObjects.Text;
  private readonly bar: Phaser.GameObjects.Graphics;
  private readonly balloon: Phaser.GameObjects.Text;
  // Com a arte: o balão com o ícone e o fio, a etiqueta e a fala.
  private bubble: { readonly group: Phaser.GameObjects.Container; readonly icon: Phaser.GameObjects.Image; readonly thread: Phaser.GameObjects.Graphics } | undefined;
  private tip: Box | undefined;
  private speech: Box | undefined;
  private kit: BubbleKit | undefined;
  private viewTop = 0;
  /** O que o `declutter` vê: o balão (pelo ícone), a etiqueta ou o rótulo. */
  private headline: { readonly text: string; readonly object: Phaser.GameObjects.Components.Transform; readonly width: number; readonly height: number } | undefined;

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
    this.tag = scene.add
      .text(0, 0, "", { fontFamily: FONT, fontSize: "11px", color: "#ffe08a", fontStyle: "bold", backgroundColor: "rgba(20,20,20,0.8)", padding: { x: 4, y: 1 } })
      .setOrigin(0.5, 1)
      .setDepth(60)
      .setVisible(false);
    this.bar = scene.add.graphics().setDepth(60);
    this.balloon = scene.add
      .text(0, 0, "", { fontFamily: FONT, fontSize: "12px", color: "#1b1b1b", backgroundColor: "#fffdf5", padding: { x: 6, y: 4 }, wordWrap: { width: 190 } })
      .setOrigin(0.5, 1)
      .setDepth(62)
      .setVisible(false);
  }

  draw(input: HeadInput): void {
    this.viewTop = input.view.y;
    this.kit = input.kit;
    if (input.kit === undefined) {
      this.drawText(input);
    } else {
      this.drawArt(input, input.kit);
    }
  }

  /** As fazendas: o rótulo de texto, a barra e o balão de fala de texto (ADR-0052, ADR-0078). */
  private drawText({ view, x, top, progress, said }: HeadInput): void {
    this.hideArt();
    this.tag.setVisible(progress !== undefined).setText(progress?.label ?? "");
    const half = this.tag.width / 2 + 2;
    this.tag.setPosition(clampX(view, x, half), top - 3);
    this.headline = progress === undefined ? undefined : { text: this.tag.text, object: this.tag, width: this.tag.width, height: this.tag.height };
    this.drawBar(x, top, progress);
    this.balloon.setVisible(said !== undefined);
    if (said !== undefined) {
      if (this.balloon.text !== said) {
        this.balloon.setText(said);
      }
      const above = progress === undefined ? top - 2 : top - 22;
      const width = this.balloon.width / 2 + 2;
      this.balloon.setPosition(clampX(view, x, width), Math.max(view.y + this.balloon.height + 2, above));
    }
  }

  /** O escritório: o balão com o ícone, a etiqueta e a fala, na arte do Claude Design. */
  private drawArt(input: HeadInput, kit: BubbleKit): void {
    const { view, x, top, progress, said, hover } = input;
    this.tag.setVisible(false);
    this.balloon.setVisible(false);
    const icon = progress === undefined ? undefined : kit.icon(input.action);
    const tipText = hover ?? (progress !== undefined && icon === undefined ? progress.label : undefined);
    let above = top; // onde a fala pousa: acima do que estiver sobre a cabeça

    const showBubble = hover === undefined && icon !== undefined;
    const bubble = this.bubbleOf(kit);
    bubble.group.setVisible(showBubble);
    bubble.thread.clear();
    this.headline = undefined;
    if (showBubble) {
      const { action } = kit.art;
      const [dx, dy] = input.atDesk ? (action.at_desk ?? [0, 0]) : [0, 0];
      const [w, h] = [action.rect[2], action.rect[3]];
      bubble.group.setPosition(clampX(view, x + dx, w / 2 + 2), top - 1 + dy);
      bubble.icon.setFrame(icon);
      const fraction = progress?.fraction;
      if (fraction !== undefined) {
        const { x: px, y: py, width, height, track, fill } = action.progress;
        const [ax, ay] = action.anchor;
        bubble.thread.fillStyle(color(track), 1).fillRect(px - ax, py - ay, width, height);
        bubble.thread.fillStyle(color(fill), 1).fillRect(px - ax, py - ay, Math.round(width * fraction), height);
      }
      this.headline = { text: `icone:${String(icon)}`, object: bubble.group, width: w, height: h };
      above = bubble.group.y - h;
    }

    const tip = (this.tip ??= new Box(this.scene, 61));
    if (tipText !== undefined && tip.show(kit, "label", tipText)) {
      const image = tip.image;
      image.setPosition(clampX(view, x, image.width / 2 + 2), top - 3);
      this.headline = { text: tipText, object: image, width: image.width, height: image.height };
      above = image.y - image.height;
    } else {
      tip.hide();
    }
    // A ação sem ícone (e o mouse em cima de quem faz algo) guarda a barra embaixo da etiqueta.
    this.drawBar(x, top, showBubble ? undefined : progress);

    const speech = (this.speech ??= new Box(this.scene, 62));
    if (said !== undefined && speech.show(kit, "speech", said)) {
      const image = speech.image;
      const half = image.width / 2 + 2;
      const tipY = Math.max(view.y + image.height * image.originY + 2, above - 1);
      image.setPosition(clampX(view, x, half), tipY);
    } else {
      speech.hide();
    }
  }

  private bubbleOf(kit: BubbleKit): NonNullable<HeadView["bubble"]> {
    if (this.bubble === undefined) {
      const { action } = kit.art;
      const [ax, ay] = action.anchor;
      const [w, h] = [action.rect[2], action.rect[3]];
      const back = this.scene.add.image(0, 0, kit.sheet, kit.actionFrame()).setOrigin(ax / w, ay / h);
      const icon = this.scene.add.image(action.slot[0] - ax, action.slot[1] - ay, kit.art.icons.sheet, 0).setOrigin(0, 0);
      const thread = this.scene.add.graphics();
      const group = this.scene.add.container(0, 0, [back, icon, thread]).setDepth(60).setVisible(false);
      this.bubble = { group, icon, thread };
    }
    return this.bubble;
  }

  private drawBar(x: number, top: number, progress: Progress | undefined): void {
    this.bar.clear();
    if (progress?.fraction !== undefined) {
      const width = 32 - 4;
      this.bar.fillStyle(0x141414, 0.8).fillRect(x - width / 2 - 1, top - 1, width + 2, 6);
      this.bar.fillStyle(0x7bd88f, 1).fillRect(x - width / 2, top, width * progress.fraction, 4);
    }
  }

  /** A caixa do que vai sobre a cabeça, para o `declutter`. */
  label(id: string): Label | undefined {
    const line = this.headline;
    return line === undefined ? undefined : { id, text: line.text, x: line.object.x, y: line.object.y, width: line.width, height: line.height };
  }

  /** Põe o que vai sobre a cabeça onde o `declutter` mandou; quando sobe, a fala sobe junto. */
  place(at: Placement): void {
    const line = this.headline;
    if (line === undefined) {
      return;
    }
    const rise = at.y - line.object.y;
    line.object.setPosition(at.x, at.y);
    (line.object as unknown as Phaser.GameObjects.Components.Visible).setVisible(at.visible);
    for (const talk of [this.balloon, this.speech?.image]) {
      if (talk?.visible === true && rise < 0) {
        talk.setY(Math.max(this.viewTop + talk.height * talk.originY + 2, talk.y + rise));
      }
    }
  }

  hide(): void {
    this.tag.setVisible(false);
    this.balloon.setVisible(false);
    this.bar.clear();
    this.hideArt();
    this.headline = undefined;
  }

  destroy(): void {
    this.tag.destroy();
    this.bar.destroy();
    this.balloon.destroy();
    this.bubble?.group.destroy(true);
    this.tip?.destroy(this.kit);
    this.speech?.destroy(this.kit);
  }

  private hideArt(): void {
    this.bubble?.group.setVisible(false);
    this.bubble?.thread.clear();
    this.tip?.hide();
    this.speech?.hide();
  }
}

/** O x de uma caixa de meia-largura `half`, dentro do que a câmera mostra. */
function clampX(view: Phaser.Geom.Rectangle, x: number, half: number): number {
  return view.width > 0 ? Phaser.Math.Clamp(x, view.x + half, view.right - half) : x;
}
