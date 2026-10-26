/** A Morada do Sol na tela (ADR-0068): a névoa na visão do jogador e o menu da grama do humano.
 * O sandbox começa com o relógio parado, então o script não age antes do humano assumir. */
import { expect, test, type Page } from "@playwright/test";

import { SHOTS, tile } from "./tela.ts";

type Hooks = { campsverso?: { sight(x: number, y: number): string | undefined } };

async function sight(page: Page, x: number, y: number): Promise<string | undefined> {
  return page.evaluate(([tx, ty]) => (window as unknown as Hooks).campsverso?.sight(tx, ty), [x, y] as const);
}

test("o jogador vê só o que o Camps vê: em volta dele, sim; o outro lado do mapa, nunca", async ({ page }) => {
  await page.goto("/?view=player");
  await expect(page.locator(".hud")).toContainText("pausado", { timeout: 30_000 });
  await expect.poll(() => sight(page, 6, 16), { timeout: 15_000 }).toBe("visible");
  expect(await sight(page, 60, 38)).toBe("unseen");
  await page.screenshot({ path: `${SHOTS}/morada-nevoa.png` });
});

test("o humano cava pela grama: o Camps anda até o lado do tile e o canteiro aparece", async ({ page }) => {
  await page.goto("/?view=operator");
  const hud = page.locator(".hud");
  await expect(hud).toContainText("pausado", { timeout: 30_000 });
  await page.waitForTimeout(2_000); // o mapa e a arte chegam depois da primeira foto
  await page.getByRole("button", { name: "Assumir Camps" }).click();
  const commands = page.locator(".commands");
  await expect(commands).toBeVisible(); // a primeira vez: os comandos na tela
  await commands.getByRole("button", { name: "Entendi" }).click();
  await expect(commands).toBeHidden();

  const grass = await tile(page, 4, 21);
  await page.mouse.click(grass.x, grass.y, { button: "right" });
  const menu = page.locator(".action-menu");
  await expect(menu).toContainText("Andar até aqui");
  await menu.getByRole("button", { name: "Cavar um canteiro aqui" }).click();
  await expect(page.locator(".queue")).toContainText("Cavar um canteiro aqui · (4, 21)");

  await page.getByRole("button", { name: "Retomar" }).click();
  const timeline = page.locator("ol.timeline");
  await expect(timeline).toContainText("um canteiro novo: plot-001 em (4, 21)", { timeout: 60_000 });
  await expect(timeline).toContainText("camps cavou um canteiro em (4, 21)");
  await page.screenshot({ path: `${SHOTS}/morada-cavou.png` });
});
