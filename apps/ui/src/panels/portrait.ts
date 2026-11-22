/** O retrato de um avatar (ADR-0053): no HUD e nos chips da tela retrô. Com o busto da folha de
 * retratos no manifesto (`face`, ADR-0092), desenha o busto inteiro, que pisca de vez em quando; sem
 * ele, um recorte da própria folha de sprites, ampliado. */
import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";

const SIZE = 56;
/** O piscar (briefing-tela-2.md, §2): a linha de baixo por 150 ms, a cada 4 a 7 s. */
const BLINK_MS = 150;
const BLINK_EVERY_MS: readonly [number, number] = [4000, 7000];

export interface FaceCell {
  readonly image: HTMLImageElement;
  readonly sx: number;
  readonly sy: number;
  readonly size: number;
  /** Quanto descer na folha para o quadro piscando; sem ele, não pisca. */
  readonly blinkDy?: number;
}

/** Onde fica o busto ou o recorte de um avatar na folha, depois que a imagem carregou. */
export function faceCell(art: ArtManifest, avatarId: string, image: HTMLImageElement): Omit<FaceCell, "image"> | undefined {
  const avatar = art.avatars?.[avatarId] ?? art.avatars?.["*"];
  if (avatar === undefined) {
    return undefined;
  }
  const face = avatar.face;
  const faces = face === undefined ? undefined : art.sheets?.[face.sheet];
  if (face !== undefined && faces !== undefined) {
    return { sx: face.column * faces.frame_width, sy: 0, size: faces.frame_width, blinkDy: faces.frame_height };
  }
  const crop = avatar.portrait;
  const sheet = art.sheets?.[avatar.sheet];
  if (crop === undefined || sheet === undefined) {
    return undefined;
  }
  const columns = Math.max(1, Math.floor(image.width / sheet.frame_width));
  return {
    sx: (crop.frame % columns) * sheet.frame_width + crop.x,
    sy: Math.floor(crop.frame / columns) * sheet.frame_height + crop.y,
    size: crop.size,
  };
}

/** A imagem da folha onde está o retrato do avatar: a dos retratos, ou a do sprite. */
export function faceSheet(art: ArtManifest, avatarId: string): string | undefined {
  const avatar = art.avatars?.[avatarId] ?? art.avatars?.["*"];
  if (avatar === undefined) {
    return undefined;
  }
  const faces = avatar.face === undefined ? undefined : art.sheets?.[avatar.face.sheet];
  if (faces !== undefined) {
    return faces.image;
  }
  return avatar.portrait === undefined ? undefined : art.sheets?.[avatar.sheet]?.image;
}

export class Portrait {
  readonly element: HTMLElement;
  private readonly canvas: HTMLCanvasElement;
  private readonly badge: HTMLElement;
  private readonly size: number;
  private cell: FaceCell | undefined;
  private blinkTimer: number | undefined;

  constructor(size = SIZE) {
    this.size = size;
    this.canvas = el("canvas", { className: "portrait-image" });
    this.canvas.width = size;
    this.canvas.height = size;
    this.badge = el("span", { className: "portrait-badge" });
    this.element = el("div", { className: "portrait" }, this.canvas, this.badge);
    this.element.hidden = true;
  }

  /** Desenha o retrato do manifesto; sem retrato na arte, fica escondido. */
  setArt(art: ArtManifest, avatarId: string): void {
    this.stopBlink();
    const src = faceSheet(art, avatarId);
    if (src === undefined) {
      this.element.hidden = true;
      return;
    }
    const image = new Image();
    image.onload = () => {
      const where = faceCell(art, avatarId, image);
      if (where === undefined) {
        this.element.hidden = true;
        return;
      }
      this.cell = { image, ...where };
      this.draw(false);
      this.element.hidden = false;
      this.scheduleBlink();
    };
    image.src = src;
  }

  /** O selo de estado: dormindo, ou a ação em andamento. */
  setBadge(text: string): void {
    if (this.badge.textContent !== text) {
      this.badge.textContent = text;
      this.badge.hidden = text === "";
    }
  }

  private draw(blinking: boolean): void {
    const cell = this.cell;
    const context = this.canvas.getContext("2d");
    if (cell === undefined || context === null) {
      return;
    }
    context.imageSmoothingEnabled = false;
    context.clearRect(0, 0, this.size, this.size);
    const sy = cell.sy + (blinking ? (cell.blinkDy ?? 0) : 0);
    context.drawImage(cell.image, cell.sx, sy, cell.size, cell.size, 0, 0, this.size, this.size);
  }

  /** O piscar é só de tela, num tempo diferente para cada retrato; parado com o movimento reduzido. */
  private scheduleBlink(): void {
    if (this.cell?.blinkDy === undefined || matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }
    const [low, high] = BLINK_EVERY_MS;
    this.blinkTimer = window.setTimeout(() => {
      this.draw(true);
      this.blinkTimer = window.setTimeout(() => {
        this.draw(false);
        this.scheduleBlink();
      }, BLINK_MS);
    }, low + Math.random() * (high - low));
  }

  private stopBlink(): void {
    if (this.blinkTimer !== undefined) {
      window.clearTimeout(this.blinkTimer);
      this.blinkTimer = undefined;
    }
  }
}
