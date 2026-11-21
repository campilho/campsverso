/** Os retratos pequenos da conversa (as falas, a pilha do cabeçalho, as sugestões): o mesmo recorte
 * do `Portrait`, desenhado uma vez por avatar e guardado como imagem, para não abrir a folha de
 * sprites a cada fala. */
import type { ArtManifest } from "../art/manifest.ts";

const SIZE = 48;

export class FaceCache {
  private readonly urls = new Map<string, string>();
  private readonly pending = new Set<string>();
  private art: ArtManifest | undefined;
  private readonly changed: () => void;
  /** Muda a cada retrato pronto, para quem desenha saber que precisa redesenhar. */
  version = 0;

  constructor(changed: () => void) {
    this.changed = changed;
  }

  setArt(art: ArtManifest): void {
    this.art = art;
    this.urls.clear();
    this.pending.clear();
    this.version++;
    this.changed();
  }

  /** O retrato pronto, ou nada por enquanto (ele começa a carregar e avisa quando chegar). */
  url(id: string): string | undefined {
    const ready = this.urls.get(id);
    if (ready !== undefined || this.pending.has(id) || this.art === undefined) {
      return ready;
    }
    this.pending.add(id);
    this.load(this.art, id);
    return undefined;
  }

  private load(art: ArtManifest, id: string): void {
    const avatar = art.avatars?.[id] ?? art.avatars?.["*"];
    const crop = avatar?.portrait;
    const sheet = avatar === undefined ? undefined : art.sheets?.[avatar.sheet];
    if (crop === undefined || sheet === undefined) {
      return;
    }
    const image = new Image();
    image.onload = () => {
      if (this.art !== art) {
        return; // a arte mudou no meio do caminho
      }
      const canvas = document.createElement("canvas");
      canvas.width = SIZE;
      canvas.height = SIZE;
      const context = canvas.getContext("2d");
      if (context === null) {
        return;
      }
      const columns = Math.max(1, Math.floor(image.width / sheet.frame_width));
      const sx = (crop.frame % columns) * sheet.frame_width + crop.x;
      const sy = Math.floor(crop.frame / columns) * sheet.frame_height + crop.y;
      context.imageSmoothingEnabled = false;
      context.drawImage(image, sx, sy, crop.size, crop.size, 0, 0, SIZE, SIZE);
      this.urls.set(id, canvas.toDataURL());
      this.version++;
      this.changed();
    };
    image.src = sheet.image;
  }
}
