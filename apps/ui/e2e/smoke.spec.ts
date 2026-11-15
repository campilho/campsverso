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

/** Na página: o maior deslocamento do Camps entre dois quadros desenhados, durante `ms`. */
function sampleSteps(ms: number): Promise<{ biggest: number; moved: number }> {
  type Hook = { drawn(id: string): { x: number; y: number } | undefined };
  const hook = (window as unknown as { campsverso: Hook }).campsverso;
  return new Promise((resolve) => {
    let first: { x: number; y: number } | undefined;
    let last: { x: number; y: number } | undefined;
    let biggest = 0;
    const start = performance.now();
    const frame = (): void => {
      const point = hook.drawn("camps");
      if (point !== undefined) {
        if (last !== undefined) {
          biggest = Math.max(biggest, Math.hypot(point.x - last.x, point.y - last.y));
        }
        first ??= point;
        last = point;
      }
      if (performance.now() - start < ms) {
        requestAnimationFrame(frame);
      } else {
        const moved = first === undefined || last === undefined ? 0 : Math.hypot(last.x - first.x, last.y - first.y);
        resolve({ biggest, moved });
      }
    };
    requestAnimationFrame(frame);
  });
}

test("o Camps anda sem pulo, a 72× e a 1× (ADR-0078)", async ({ page }) => {
  await page.goto("/?view=operator");
  const hud = page.locator(".hud");
  await expect(hud).toContainText("ao vivo", { timeout: 30_000 });
  await page.waitForTimeout(2_000);
  await page.getByRole("button", { name: "Assumir Camps" }).click();
  await expect(page.getByRole("button", { name: "Devolver ao script" })).toBeVisible();
  const understood = page.locator(".commands").getByRole("button", { name: "Entendi" });
  if (await understood.isVisible()) {
    await understood.click();
  }
  await expect(hud).toContainText("parado", { timeout: 45_000 });

  // A 72×, 30 tiles por minuto simulado viram 36 tiles por segundo: uns 0,6 tile por quadro.
  await page.getByRole("button", { name: "72×", exact: true }).click();
  const far = await tile(page, 15, 12);
  const fast = page.evaluate(sampleSteps, 3_000);
  await page.mouse.click(far.x, far.y);
  const at72 = await fast;
  expect(at72.moved).toBeGreaterThan(3);
  expect(at72.biggest).toBeLessThanOrEqual(1);
  await expect(hud).toContainText("parado", { timeout: 20_000 });

  // A 1×, meio tile por segundo: a caminhada leva o minuto do tick, sem correr e parar.
  await page.getByRole("button", { name: "1×", exact: true }).click();
  const near = await tile(page, 5, 12);
  await page.mouse.click(near.x, near.y);
  await expect(hud).toContainText("fazendo: move", { timeout: 75_000 });
  const at1 = await page.evaluate(sampleSteps, 4_000);
  expect(at1.moved).toBeGreaterThan(0.5);
  expect(at1.moved).toBeLessThan(4);
  expect(at1.biggest).toBeLessThanOrEqual(0.2);

  await page.getByRole("button", { name: "72×", exact: true }).click();
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
