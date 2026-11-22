/** O que a tela espera de quem desenha o mundo: o canvas de depuração ou o Phaser (ADR-0053). */
import type { ObserverState } from "@campsverso/contracts";

import type { ArtManifest } from "../art/manifest.ts";
import type { Sight } from "../fog.ts";
import type { MotionClock } from "../motion.ts";
import type { TileGrid } from "../tiled.ts";

export interface WorldRenderer {
  /** O elemento que vai na página e recebe os cliques. */
  readonly element: HTMLElement;
  /** Onde cada avatar aparece nesta tela, e o caminho que o desenho faz (ADR-0078): cada tela tem o seu. */
  readonly motion: MotionClock;
  setGrid(grid: TileGrid): void;
  setArt(art: ArtManifest): void;
  /** Desenha o estado no tick mostrado (fracionário); a tela chama a cada quadro. */
  draw(state: ObserverState, tick: number): void;
  /** Um avatar falou (ADR-0078): o balão sobre a cabeça dele; o canvas de depuração não desenha. */
  speak?(avatarId: string, text: string): void;
  /** Quem a câmera segue, num mapa maior que a tela (ADR-0067); o canvas de depuração não segue. */
  follow?(entityId: string): void;
  /** Volta a seguir quem a câmera segue, depois de arrastar o mapa (a tecla espaço; ADR-0068). */
  recenter?(): void;
  /** O tamanho da vista em pixels, menor que a sala (o celular da tela retrô: a câmera segue em 1x,
   * num recorte); sem tamanho, a vista volta ao tamanho do mapa. */
  setView?(size: { readonly width: number; readonly height: number } | undefined): void;
  /** A sala inteira na vista, com zoom ("sala"), ou a câmera seguindo ("seguir"). */
  setWhole?(whole: boolean): void;
  /** O que a câmera mostra agora, em tiles, para o minimapa. */
  viewRect?(): { readonly x: number; readonly y: number; readonly width: number; readonly height: number } | undefined;
  /** A névoa da visão do jogador (ADR-0068): sempre, ou com o botão do operador. */
  setFog?(mode: "always" | "toggle"): void;
  /** Guarda a lembrança da névoa no navegador, com esta chave (por mundo e avatar). */
  rememberFog?(key: string): void;
  /** O que o jogador enxerga num tile com a névoa ligada; para os testes no navegador. */
  sight?(x: number, y: number): Sight | undefined;
  /** O estado da oficina que uma coisa mostrou no último quadro ("trabalhando", "passou"...), ou
   * nada; para os testes no navegador (o robô na bancada, ADR-0080). */
  workshopLook?(entityId: string): string | undefined;
  /** A versão que o escritório vivo roda, para a placa da parede (ADR-0083); nada sem supervisor. */
  setBuild?(build: { readonly commit: string; readonly date: string } | undefined): void;
  /** O centro de um tile em coordenadas da tela, pela câmera; para os testes no navegador. */
  clientOf?(x: number, y: number): { x: number; y: number } | undefined;
  /** O tile sob um ponto da tela (coordenadas do evento do mouse), ou nada fora do mapa. */
  tileAt(clientX: number, clientY: number): { x: number; y: number } | undefined;
}

/** A conta comum: ponto da tela → tile, num canvas com `size` pixels por tile. */
export function tileUnder(canvas: HTMLCanvasElement, size: number, clientX: number, clientY: number): { x: number; y: number } | undefined {
  const box = canvas.getBoundingClientRect();
  if (box.width === 0 || box.height === 0) {
    return undefined;
  }
  const x = Math.floor(((clientX - box.left) * canvas.width) / box.width / size);
  const y = Math.floor(((clientY - box.top) * canvas.height) / box.height / size);
  const inside = x >= 0 && y >= 0 && x * size < canvas.width && y * size < canvas.height;
  return inside ? { x, y } : undefined;
}
