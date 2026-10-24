/** O que os testes no navegador têm em comum: onde ficam as telas salvas e o centro de um tile. */
import type { Page } from "@playwright/test";

export const SHOTS = "test-results/telas";

/** O centro de um tile do mapa na tela. A tela diz onde, pela câmera (o mapa maior rola, ADR-0067);
 * sem o ajudante, a conta pelo tamanho do canvas do Phaser (32 px por tile, câmera parada). */
export async function tile(page: Page, x: number, y: number): Promise<{ x: number; y: number }> {
  const point = await page.evaluate(
    ([tx, ty]) => (window as unknown as { campsverso?: { tileCenter(x: number, y: number): { x: number; y: number } | undefined } }).campsverso?.tileCenter(tx, ty),
    [x, y] as const,
  );
  if (point !== undefined) {
    return point;
  }
  const canvas = page.locator(".phaser canvas");
  const box = await canvas.boundingBox();
  const size = await canvas.evaluate((c: HTMLCanvasElement) => ({ width: c.width, height: c.height }));
  if (box === null) {
    throw new Error("o canvas do Phaser não está na tela");
  }
  return {
    x: box.x + ((x + 0.5) * 32 * box.width) / size.width,
    y: box.y + ((y + 0.5) * 32 * box.height) / size.height,
  };
}

