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

  // A seta segurada anda no passo de tela, e soltar não faz o gerente voltar (ADR-0079): a 72×, o
  // teclado troca o destino a cada 200 ms, e o passo começado termina antes de o avatar virar.
  const drawn = (id: string): Promise<{ x: number; y: number } | undefined> =>
    page.evaluate((who) => {
      type Hook = { drawn(id: string): { x: number; y: number } | undefined };
      return (window as unknown as { campsverso: Hook }).campsverso.drawn(who);
    }, id);
  await expect.poll(() => drawn("gerente"), { timeout: 20_000 }).toEqual({ x: 9, y: 15 });
  const ys: number[] = [];
  await page.keyboard.down("ArrowUp");
  for (let i = 0; i < 30; i++) {
    if (i === 10) {
      await page.keyboard.up("ArrowUp");
    }
    await page.waitForTimeout(100);
    ys.push((await drawn("gerente"))?.y ?? Number.NaN);
  }
  expect(ys.every((y, i) => i === 0 || y <= (ys[i - 1] ?? y) + 0.01)).toBe(true); // nunca volta
  expect(15 - (ys.at(-1) ?? 15)).toBeGreaterThanOrEqual(3); // um segundo a 4 tiles por segundo

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
  await expect.poll(camps, { timeout: 20_000 }).toEqual({ x: 4, y: 5 }); // o cubículo de cima (ADR-0082)

  const speech = page.getByPlaceholder("Fale com o dev e aperte Enter");
  await speech.fill("Bom dia, Camps! Como vai a busca?");
  await speech.press("Enter");
  await expect(speech).toHaveValue("");

  // A 72×, os 15 minutos de trabalho do dev-script passam em uns 13 segundos.
  await expect(office.locator(".entregue")).toContainText("#1", { timeout: 60_000 });
  await page.screenshot({ path: `${SHOTS}/escritorio.png` });
  await office.getByRole("button", { name: "Aceitar" }).click();
  await expect(office.locator(".aceito")).toContainText("#1", { timeout: 30_000 });

  // A 1×, o andar responde como a 72× (ADR-0081): com o tick de 250 ms, o kernel aceita um comando
  // a cada quarto de segundo. Com o tick de 2 s, a seta solta passava até 8 tiles do ponto e
  // voltava, e o clique esperava até 2 s.
  await page.getByRole("button", { name: "1×", exact: true }).click();
  await expect(hud).toContainText(/(^|\D)1×/, { timeout: 10_000 });
  // O gerente aceitou ao lado do quadro, na linha 2: para a direita, a linha é livre até os
  // arquivos, na coluna 12 (a planta da arte nova, ADR-0082).
  const before = await drawn("gerente");
  expect(before).toBeDefined();
  const right: number[] = [];
  await page.keyboard.down("ArrowRight");
  for (let i = 0; i < 25; i++) {
    if (i === 10) {
      await page.keyboard.up("ArrowRight");
    }
    await page.waitForTimeout(100);
    right.push((await drawn("gerente"))?.x ?? Number.NaN);
  }
  expect(right.every((x, i) => i === 0 || x >= (right[i - 1] ?? x) - 0.01), JSON.stringify(right)).toBe(true); // nunca volta
  const released = right[9] ?? Number.NaN;
  const end = right.at(-1) ?? Number.NaN;
  expect(end - (before?.x ?? 0)).toBeGreaterThanOrEqual(3); // um segundo a 4 tiles por segundo
  // Soltou: para logo, sem voltar. A 1× ele ainda anda uns 2 tiles (meio segundo): a parada chega
  // ao kernel no tick seguinte, depois da rede. Com o tick de 2 s, passava até 8 tiles e voltava.
  expect(end - released, JSON.stringify(right)).toBeLessThanOrEqual(3.5);

  const here = await drawn("gerente");
  const goal = { x: Math.round(here?.x ?? 0) - 3, y: Math.round(here?.y ?? 0) };
  const at = await page.evaluate(
    ([x, y]) => (window as unknown as { campsverso: { tileCenter(x: number, y: number): { x: number; y: number } } }).campsverso.tileCenter(x, y),
    [goal.x, goal.y] as const,
  );
  const clicked = Date.now();
  await page.mouse.click(at.x, at.y);
  await expect.poll(async () => (await drawn("gerente"))?.x ?? 0, { intervals: [25], timeout: 3_000 }).toBeLessThan(end - 0.05);
  expect(Date.now() - clicked).toBeLessThan(800); // o clique anda logo (em geral, em 100 ms)
  await expect.poll(() => drawn("gerente"), { timeout: 5_000 }).toEqual(goal);
});
