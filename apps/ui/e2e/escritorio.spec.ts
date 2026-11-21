/** O escritório no navegador (ADR-0078): o humano entra como o gerente, escreve um pedido no
 * quadro, fala com o dev (que para e responde), vê o patch da entrega (ADR-0080), a aceita e toma
 * um café na copa; e o robô da bancada trabalha antes da entrega. */
import { expect, test } from "@playwright/test";

import { SHOTS, tile } from "./tela.ts";

test("o gerente entra, escreve um pedido, fala com o dev, vê o patch e aceita a entrega", async ({ page }) => {
  await page.goto("/?assumir=1");
  const hud = page.locator(".hud");
  await expect(hud).toContainText("human/camps-browser", { timeout: 45_000 }); // o gerente é do humano
  const understood = page.getByRole("button", { name: "Entendi" });
  if (await understood.isVisible()) {
    await understood.click();
  }
  await expect(page.locator(".retro-board")).toContainText("Quadro dos pedidos");

  // A moldura retrô (docs/design/briefing-tela.md): a luz com o rótulo, o gerente seu nos chips, o
  // comando de soltar e o Sobre, que abre e fecha.
  await expect(page.locator("body")).toHaveClass(/retro/);
  await expect(page.getByRole("img", { name: "online" })).toBeVisible();
  await expect(page.locator(".retro-chip", { hasText: "Gerente" })).toContainText("você");
  await expect(page.getByRole("button", { name: "Soltar o gerente" })).toBeEnabled();
  await page.getByRole("button", { name: "Sobre o Campsverso" }).click();
  const about = page.getByRole("dialog", { name: "Sobre o Campsverso" });
  await expect(about).toContainText("v0.4");
  await about.getByRole("button", { name: "Fechar" }).click();
  await expect(about).toBeHidden();

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
  expect(ys.every((y, i) => i === 0 || y <= (ys[i - 1] ?? y) + 0.01), JSON.stringify(ys)).toBe(true); // nunca volta
  expect(15 - (ys.at(-1) ?? 15)).toBeGreaterThanOrEqual(3); // um segundo a 4 tiles por segundo

  // A prancheta (docs/design/briefing-tela.md, §3.6): o "Escrever pedido" a abre com o foco no
  // título; escrever não anda com o gerente; o Esc fecha e guarda o rascunho.
  const board = page.locator(".retro-board");
  const write = page.getByRole("button", { name: "Escrever pedido" });
  await write.click();
  const clipboard = page.getByRole("dialog", { name: "Novo pedido" });
  await expect(clipboard).toBeVisible();
  const title = clipboard.getByRole("textbox", { name: "Título" });
  await expect(title).toBeFocused();
  const standing = await drawn("gerente");
  await title.pressSequentially("Ferramenta de busca");
  await page.waitForTimeout(300);
  expect(await drawn("gerente")).toEqual(standing); // as letras não andam com ele
  await page.keyboard.press("Escape");
  await expect(clipboard).toBeHidden();
  await write.click();
  await expect(title).toHaveValue("Ferramenta de busca"); // o rascunho ficou
  await clipboard.getByRole("textbox", { name: "O que fazer" }).fill("Achar um arquivo do repositório pelo nome.");
  await clipboard.getByRole("radio", { name: "P, pequeno" }).check();
  await clipboard.getByRole("button", { name: "Pôr no quadro" }).click();
  await expect(clipboard).toBeHidden();
  // Enquanto o gerente vai ao quadro, a ficha fantasma fica em "A fazer"; depois, a de verdade.
  await expect(board.locator(".retro-ficha.fantasma")).toContainText("Ferramenta de busca");
  await expect(board.getByRole("button", { name: /#1.*Ferramenta de busca/ })).toBeVisible({ timeout: 60_000 });
  await expect(board.locator(".retro-ficha.fantasma")).toHaveCount(0);

  // O dev trabalha sentado: com o pedido em "Fazendo", o desenho dele chega na cadeira da mesa.
  await expect(board.getByRole("tab", { name: "Fazendo, 1 pedido" })).toBeVisible({ timeout: 60_000 });
  const camps = (): Promise<{ x: number; y: number } | undefined> =>
    page.evaluate(() => {
      type Hook = { drawn(id: string): { x: number; y: number } | undefined };
      return (window as unknown as { campsverso: Hook }).campsverso.drawn("camps");
    });
  await expect.poll(camps, { timeout: 20_000 }).toEqual({ x: 4, y: 5 }); // o cubículo de cima (ADR-0082)

  // A fala que interrompe (ADR-0080): o dev para o bloco de trabalho e responde ao gerente.
  const said = (): Promise<string[]> =>
    page.evaluate(() => (window as unknown as { campsverso: { said(id: string): string[] } }).campsverso.said("camps"));
  // A conversa (docs/design/briefing-tela.md, §3.5): o @ abre as sugestões de quem está na sala, o
  // Enter escolhe, e a fala vai com a menção; a resposta do dev aparece no registro.
  const heardBefore = (await said()).length;
  const talk = page.locator(".retro-talk");
  const speech = talk.getByRole("textbox", { name: "Falar" });
  await speech.pressSequentially("@Ca");
  await expect(talk.getByRole("option", { name: /@Camps/ })).toBeVisible();
  await speech.press("Enter");
  await expect(speech).toHaveValue("@Camps ");
  await speech.pressSequentially("como vai a busca?");
  await speech.press("Enter");
  await expect(speech).toHaveValue("");
  const log = talk.getByRole("log");
  await expect(log.locator(".retro-say.mine")).toContainText("@Camps como vai a busca?");
  await expect.poll(async () => (await said()).slice(heardBefore), { timeout: 20_000 }).toContain("Anotado.");
  await expect(log).toContainText("Anotado.");
  await expect(log).toContainText("Camps pegou o pedido 1"); // a linha do quadro
  await talk.getByRole("button", { name: "Aumentar a conversa" }).click();
  await expect(page.locator(".retro-right")).toHaveClass(/talk-big/);
  await talk.getByRole("button", { name: "Diminuir a conversa" }).click();
  await expect(page.locator(".retro-right")).not.toHaveClass(/talk-big/);

  // O robô na bancada (o plano do M24, §4): antes de entregar, o dev-script chama o testador com os
  // testes da própria bancada (a `reserva` do registro), e a tela o mostra trabalhando e depois o
  // resultado. A 72×, os 15 minutos de trabalho do dev passam em uns 13 segundos.
  const look = (id: string): Promise<string | undefined> =>
    page.evaluate((who) => (window as unknown as { campsverso: { look(id: string): string | undefined } }).campsverso.look(who), id);
  await expect.poll(() => look("robo-testador"), { intervals: [100], timeout: 60_000 }).toBe("trabalhando");
  await expect.poll(() => look("robo-testador"), { timeout: 30_000 }).toBe("passou");
  await page.screenshot({ path: `${SHOTS}/escritorio-bancada.png` });
  const delivered = board.getByRole("tab", { name: "Entregue, 1 pedido" });
  await expect(delivered).toBeVisible({ timeout: 60_000 });
  await delivered.click();
  await page.screenshot({ path: `${SHOTS}/escritorio.png` });

  // A ficha aberta, na prancheta em leitura, e o "ver o patch" (ADR-0080): sem modelo, a sessão fixa
  // do dev-script na oficina registra o pedido num arquivo, e o patch vai ao depósito de entregas.
  await board.getByRole("button", { name: /#1.*Ferramenta de busca/ }).click();
  const card = page.getByRole("dialog", { name: "Ficha do pedido" });
  await expect(card).toContainText("ENTREGUE");
  await expect(card).toContainText("Achar um arquivo do repositório pelo nome.");
  await card.getByRole("button", { name: "Ver o patch" }).click();
  const patch = page.locator("dialog.delivery");
  await expect(patch).toContainText("docs/oficina/pedido-001.md", { timeout: 10_000 });
  await expect(patch.locator(".delivery-counts")).toContainText("1 arquivo(s)");
  await expect(patch.locator(".diff-add").filter({ hasText: "# Pedido 1: Ferramenta de busca" })).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/escritorio-patch.png` });
  await patch.getByRole("button", { name: "fechar" }).click();
  await expect(patch).toBeHidden();
  await card.getByRole("button", { name: "Aceitar" }).click();
  await expect(card).toBeHidden();
  await expect(board.getByRole("tab", { name: "Aceito, 1 pedido" })).toBeVisible({ timeout: 30_000 });

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

  // A pausa do gerente (ADR-0082): o menu da máquina de café, na copa, e o café no HUD dele.
  const machine = await tile(page, 13, 9);
  await page.mouse.click(machine.x, machine.y, { button: "right" });
  const menu = page.locator(".action-menu");
  await menu.getByRole("button", { name: "Tomar um café" }).click();
  await expect(hud).toContainText("fazendo: coffee", { timeout: 30_000 });
  await page.screenshot({ path: `${SHOTS}/escritorio-cafe.png` });

  // As mensagens do sistema (docs/design/briefing-tela.md, §3.9), pelo aviso que o supervisor manda
  // ao gateway: a espera avisa no canto e fecha no ×; a troca trava a tela, sem fechar no Esc; a
  // volta tira o modal e avisa.
  const notify = (data: Record<string, unknown>): Promise<unknown> => page.request.post("/aviso", { data });
  await notify({ kind: "espera", text: "Há uma versão nova: o escritório troca quando o dev terminar a sessão na oficina." });
  const toast = page.locator(".retro-toast");
  await expect(toast).toContainText("Versão nova na fila");
  await expect(page.getByRole("img", { name: "atualizando" })).toBeVisible();
  await toast.getByRole("button", { name: "Fechar o aviso" }).click();
  await expect(toast).toHaveCount(0);
  await notify({ kind: "troca", text: "O escritório vai trocar agora e volta em instantes.", commit: "a".repeat(40), pull_requests: [7] });
  const swap = page.getByRole("alertdialog", { name: "O Campsverso está se atualizando" });
  await expect(swap).toContainText("para a aaaaaaa, com o PR #7");
  await page.keyboard.press("Escape");
  await expect(swap).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/escritorio-troca.png` });
  await notify({ kind: "volta", text: "A versão aaaaaaa falhou ao subir, e o escritório voltou." });
  await expect(swap).toBeHidden();
  await expect(toast).toContainText("O escritório voltou");

  // A gaveta do operador (§3.8): a troca de visão navega, a gaveta entra cobrindo a coluna da
  // direita, e o "×" é o mesmo que "Jogador".
  await page.getByRole("button", { name: "Operador" }).click();
  await expect(page).toHaveURL(/view=operator/);
  const drawer = page.locator(".retro-drawer.open");
  await expect(drawer).toBeVisible({ timeout: 45_000 });
  await expect(drawer).toContainText("Linha do tempo");
  await expect(drawer).toContainText("sem supervisor");
  await page.waitForTimeout(500); // o fim do deslizar, para o print
  await page.screenshot({ path: `${SHOTS}/escritorio-operador.png` });
  await drawer.getByRole("button", { name: "Fechar o painel do operador" }).click();
  await expect(page).toHaveURL(/view=player/);
});
