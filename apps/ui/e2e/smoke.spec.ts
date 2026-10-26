/** Fumaça da tela (ADR-0053): o Phaser desenha, os cliques chegam ao kernel, a arte tem créditos. */
import { expect, test } from "@playwright/test";

import { SHOTS, tile } from "./tela.ts";

test("o operador vê o mapa desenhado, assume o Camps, anda e devolve", async ({ page }) => {
  await page.goto("/?view=operator");
  const hud = page.locator(".hud");
  await expect(hud).toContainText("ao vivo", { timeout: 30_000 });
  await expect(page.locator(".phaser canvas")).toBeVisible();
  await page.waitForTimeout(2_000); // a arte carrega depois da primeira foto do mundo
  await page.screenshot({ path: `${SHOTS}/operador.png` });

  await page.getByRole("button", { name: "Assumir Camps" }).click();
  await expect(page.getByRole("button", { name: "Devolver ao script" })).toBeVisible();
  await page.locator(".commands").getByRole("button", { name: "Entendi" }).click(); // a primeira vez (ADR-0068)
  await expect(hud).toContainText("parado", { timeout: 45_000 }); // o que o script deixou em andamento termina

  // Com o relógio pausado, cada passo é um tick: a caminhada (1 minuto, a 30 tiles por minuto,
  // ADR-0057) fica visível entre um passo e outro, em vez de passar em menos de um segundo a 72×.
  await page.getByRole("button", { name: "Pausar" }).click();
  await expect(page.getByRole("button", { name: "Retomar" })).toBeVisible();
  const target = await tile(page, 15, 12);
  await page.mouse.click(target.x, target.y);
  await page.getByRole("button", { name: "+1", exact: true }).click();
  await expect(hud).toContainText("fazendo: move", { timeout: 10_000 });
  await page.screenshot({ path: `${SHOTS}/andando.png` });
  await page.getByRole("button", { name: "+1", exact: true }).click();
  await expect(hud).toContainText("parado", { timeout: 10_000 });
  await page.getByRole("button", { name: "Retomar" }).click();

  await page.getByRole("button", { name: "Devolver ao script" }).click();
  await expect(page.getByRole("button", { name: "Assumir Camps" })).toBeVisible();
});

test("o jogador vê o retrato do Camps e os créditos da arte", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".portrait")).toBeVisible({ timeout: 30_000 });
  await page.getByRole("link", { name: "créditos" }).click();
  const credits = page.locator("dialog.credits");
  await expect(credits).toContainText("bluecarrot16");
  await expect(credits).toContainText("Daniel Eddeland");
  await page.screenshot({ path: `${SHOTS}/creditos.png` });
  await credits.getByRole("button", { name: "fechar" }).click();
  await expect(credits).toBeHidden();
});

test("o canvas de depuração continua em ?render=debug", async ({ page }) => {
  await page.goto("/?render=debug");
  await expect(page.locator(".hud")).toContainText("ao vivo", { timeout: 30_000 });
  await expect(page.locator("section.world > canvas")).toBeVisible();
  await expect(page.locator(".phaser")).toHaveCount(0);
});
