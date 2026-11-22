/** Os retratos pequenos da conversa (as falas, a pilha do cabeçalho, as sugestões), desenhados uma
 * vez por avatar e guardados como imagem, para não abrir a folha a cada fala. Com o busto da folha
 * de retratos (`face`, ADR-0092), o recorte do rosto: 24 x 24 a partir de (8, 4), como no canvas do
 * Claude Design (briefing-tela-2.md, §2); sem ele, o mesmo recorte do sprite do `Portrait`. */
import type { ArtManifest } from "../art/manifest.ts";
import { faceCell, faceSheet } from "../panels/portrait.ts";

const SIZE = 48;
/** O rosto dentro do busto de 40 x 40. */
const FACE = 24;
const FACE_X = 8;
const FACE_Y = 4;

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
    const src = faceSheet(art, id);
    if (src === undefined) {
      return;
    }
    const image = new Image();
    image.onload = () => {
      if (this.art !== art) {
        return; // a arte mudou no meio do caminho
      }
      const where = faceCell(art, id, image);
      const canvas = document.createElement("canvas");
      canvas.width = SIZE;
      canvas.height = SIZE;
      const context = canvas.getContext("2d");
      if (where === undefined || context === null) {
        return;
      }
      // O busto tem a linha do piscar (`blinkDy`): dele sai só o rosto.
      const [sx, sy, size] = where.blinkDy === undefined ? [where.sx, where.sy, where.size] : [where.sx + FACE_X, where.sy + FACE_Y, FACE];
      context.imageSmoothingEnabled = false;
      context.drawImage(image, sx, sy, size, size, 0, 0, SIZE, SIZE);
      this.urls.set(id, canvas.toDataURL());
      this.version++;
      this.changed();
    };
    image.src = src;
  }
}
