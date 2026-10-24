/** A visão arena (ADR-0068): as corridas de uma rodada lado a lado, a velocidade de todas, e o clique
 * que abre uma na visão do operador, no modo de assistir (só leitura). */
import { expect, test } from "@playwright/test";

import { SHOTS } from "./tela.ts";

test("a arena mostra as duas corridas, acelera e abre uma", async ({ page }) => {
  await page.goto("/?view=arena");
  const cards = page.locator(".arena-card");
  await expect(cards).toHaveCount(2, { timeout: 30_000 });
  await expect(page.locator(".arena")).toContainText("gravada");
  await expect(page.locator(".arena")).toContainText("ao vivo");
  await expect(cards.first()).toContainText("Dia 1", { timeout: 15_000 });
  await page.getByRole("button", { name: "1 dia a cada 10 s" }).click();
  await page.waitForTimeout(3_000);
  await page.screenshot({ path: `${SHOTS}/arena.png` });

  await cards.filter({ hasText: "script-gravada" }).click();
  await expect(page).toHaveURL(/view=operator&run=script-gravada/);
  await expect(page.locator(".control")).toContainText("Assistindo à corrida script-gravada", { timeout: 15_000 });
  await expect(page.getByRole("button", { name: "Assumir o Camps" })).toHaveCount(0);
  await expect(page.locator(".hud")).toContainText("Dia 1", { timeout: 15_000 });
});
