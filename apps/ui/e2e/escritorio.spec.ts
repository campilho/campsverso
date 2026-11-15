/** O escritório no navegador (ADR-0078): o humano entra como o gerente, escreve um pedido no
 * quadro, fala com o dev e aceita o que ele entregou. */
import { expect, test } from "@playwright/test";

import { SHOTS } from "./tela.ts";

test("o gerente entra, escreve um pedido, fala com o dev e aceita a entrega", async ({ page }) => {
  await page.goto("/?assumir=1");
  const hud = page.locator(".hud");
  await expect(hud).toContainText("human/camps-browser", { timeout: 45_000 }); // o gerente é do humano
  const understood = page.getByRole("button", { name: "Entendi" });
  if (await understood.isVisible()) {
    await understood.click();
  }
  const office = page.locator("aside.office");
  await expect(office).toContainText("Quadro dos pedidos");

  await page.getByPlaceholder("Título").fill("Ferramenta de busca");
  await page.getByPlaceholder("O que fazer").fill("Achar um arquivo do repositório pelo nome.");
  await page.getByRole("button", { name: "Escrever no quadro" }).click();
  await expect(office).toContainText("#1 Ferramenta de busca (P)", { timeout: 60_000 });

  // O dev trabalha sentado: com o pedido em "Fazendo", o desenho dele chega na cadeira da mesa.
  await expect(office.locator(".fazendo")).toContainText("#1", { timeout: 60_000 });
  const camps = (): Promise<{ x: number; y: number } | undefined> =>
    page.evaluate(() => {
      type Hook = { drawn(id: string): { x: number; y: number } | undefined };
      return (window as unknown as { campsverso: Hook }).campsverso.drawn("camps");
    });
  await expect.poll(camps, { timeout: 20_000 }).toEqual({ x: 5, y: 7 });

  const speech = page.getByPlaceholder("Fale com o dev e aperte Enter");
  await speech.fill("Bom dia, Camps! Como vai a busca?");
  await speech.press("Enter");
  await expect(speech).toHaveValue("");

  // A 72×, os 15 minutos de trabalho do dev-script passam em uns 13 segundos.
  await expect(office.locator(".entregue")).toContainText("#1", { timeout: 60_000 });
  await page.screenshot({ path: `${SHOTS}/escritorio.png` });
  await office.getByRole("button", { name: "Aceitar" }).click();
  await expect(office.locator(".aceito")).toContainText("#1", { timeout: 30_000 });
});
