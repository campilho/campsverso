/** O retrato do avatar no HUD (ADR-0053): um recorte da própria folha de sprites, ampliado. */
import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";

const SIZE = 56;

export class Portrait {
  readonly element: HTMLElement;
  private readonly canvas: HTMLCanvasElement;
  private readonly badge: HTMLElement;

  constructor() {
    this.canvas = el("canvas", { className: "portrait-image" });
    this.canvas.width = SIZE;
    this.canvas.height = SIZE;
    this.badge = el("span", { className: "portrait-badge" });
    this.element = el("div", { className: "portrait" }, this.canvas, this.badge);
    this.element.hidden = true;
  }

  /** Desenha o recorte do manifesto; sem retrato na arte, o HUD fica sem ele. */
  setArt(art: ArtManifest, avatarId: string): void {
    const avatar = art.avatars?.[avatarId] ?? art.avatars?.["*"];
    const crop = avatar?.portrait;
    const sheet = avatar === undefined ? undefined : art.sheets?.[avatar.sheet];
    if (crop === undefined || sheet === undefined) {
      this.element.hidden = true;
      return;
    }
    const image = new Image();
    image.onload = () => {
      const columns = Math.max(1, Math.floor(image.width / sheet.frame_width));
      const sx = (crop.frame % columns) * sheet.frame_width + crop.x;
      const sy = Math.floor(crop.frame / columns) * sheet.frame_height + crop.y;
      const context = this.canvas.getContext("2d");
      if (context === null) {
        return;
      }
      context.imageSmoothingEnabled = false;
      context.clearRect(0, 0, SIZE, SIZE);
      context.drawImage(image, sx, sy, crop.size, crop.size, 0, 0, SIZE, SIZE);
      this.element.hidden = false;
    };
    image.src = sheet.image;
  }

  /** O selo de estado: dormindo, ou a ação em andamento. */
  setBadge(text: string): void {
    if (this.badge.textContent !== text) {
      this.badge.textContent = text;
      this.badge.hidden = text === "";
    }
  }
}
