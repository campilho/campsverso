/** Os ícones dos itens no inventário do HUD (ADR-0068): o quadro do manifesto (`items`), recortado
 * da folha uma vez e guardado como imagem. Enquanto a folha carrega, o item fica só com o texto. */
import { EMPTY, type ArtManifest } from "./manifest.ts";

export class ItemIcons {
  private art: ArtManifest = EMPTY;
  private readonly urls = new Map<string, string>();
  private readonly images = new Map<string, HTMLImageElement>();
  private readonly loaded: () => void;

  /** `loaded` avisa a tela quando uma folha termina de carregar: com o relógio parado, o HUD não
   * se redesenharia sozinho. */
  constructor(loaded: () => void = () => undefined) {
    this.loaded = loaded;
  }

  /** Troca o manifesto e já pede as folhas dos ícones. */
  setArt(art: ArtManifest): void {
    this.art = art;
    this.urls.clear();
    for (const look of Object.values(art.items ?? {})) {
      const sheet = look.sheet === undefined ? undefined : art.sheets?.[look.sheet];
      if (sheet !== undefined) {
        this.image(sheet.image);
      }
    }
  }

  private image(src: string): HTMLImageElement {
    let image = this.images.get(src);
    if (image === undefined) {
      image = new Image();
      image.onload = () => {
        this.loaded();
      };
      image.src = src;
      this.images.set(src, image);
    }
    return image;
  }

  /** O endereço da imagem do ícone, ou nada (sem ícone no manifesto, ou a folha ainda carregando). */
  url(item: string): string | undefined {
    const known = this.urls.get(item);
    if (known !== undefined) {
      return known;
    }
    const look = this.art.items?.[item];
    const sheet = look?.sheet === undefined ? undefined : this.art.sheets?.[look.sheet];
    if (look === undefined || sheet === undefined) {
      return undefined;
    }
    const image = this.image(sheet.image);
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    if (!image.complete || image.naturalWidth === 0 || context === null) {
      return undefined;
    }
    canvas.width = sheet.frame_width;
    canvas.height = sheet.frame_height;
    const columns = Math.max(1, Math.floor(image.naturalWidth / sheet.frame_width));
    const frame = look.frame ?? 0;
    const sx = (frame % columns) * sheet.frame_width;
    const sy = Math.floor(frame / columns) * sheet.frame_height;
    context.drawImage(image, sx, sy, sheet.frame_width, sheet.frame_height, 0, 0, sheet.frame_width, sheet.frame_height);
    const url = canvas.toDataURL();
    this.urls.set(item, url);
    return url;
  }
}
