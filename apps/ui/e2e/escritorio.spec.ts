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
  await expect(page.locator(".retro-chip", { hasText: "Camps" })).toContainText("você"); // o gerente é o Camps (ADR-0092)
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
  // O rastro do desenho (os caminhos que a tela começou): numa falha, a mensagem diz por que voltou.
  const trace = (id: string): Promise<unknown> =>
    page.evaluate((who) => (window as unknown as { campsverso: { motionTrace(id: string): unknown } }).campsverso.motionTrace(who), id);
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
  expect(ys.every((y, i) => i === 0 || y <= (ys[i - 1] ?? y) + 0.01), JSON.stringify({ ys, trace: await trace("gerente") })).toBe(true); // nunca volta
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
  // Quem programa e o modelo (ADR-0089): o dev-script não usa, mas a ficha guarda.
  await clipboard.getByRole("combobox", { name: "Quem programa" }).selectOption({ label: "Claude Code" });
  await clipboard.getByRole("combobox", { name: "Modelo" }).selectOption({ label: "Opus 5.5" });
  await page.screenshot({ path: `${SHOTS}/escritorio-prancheta.png` });
  await clipboard.getByRole("button", { name: "Pôr no quadro" }).click();
  await expect(clipboard).toBeHidden();
  // Enquanto o gerente vai ao quadro, a ficha fantasma fica em "A fazer"; depois, a de verdade.
  await expect(board.locator(".retro-ficha.fantasma")).toContainText("Ferramenta de busca");
  // A ficha quadrada é um botão só, com o número, o título e o tamanho no nome (ADR-0092).
  await expect(board.getByRole("button", { name: /^Pedido 1: Ferramenta de busca, tamanho pequeno/ })).toBeVisible({ timeout: 60_000 });
  await expect(board.locator(".retro-ficha.fantasma")).toHaveCount(0);

  // O dev trabalha sentado: com o pedido em "Fazendo", o desenho dele chega na cadeira da mesa.
  await expect(board.getByRole("tab", { name: "Fazendo, 1 pedido" })).toBeVisible({ timeout: 60_000 });
  const dev = (): Promise<{ x: number; y: number } | undefined> =>
    page.evaluate(() => {
      type Hook = { drawn(id: string): { x: number; y: number } | undefined };
      return (window as unknown as { campsverso: Hook }).campsverso.drawn("tiago");
    });
  await expect.poll(dev, { timeout: 20_000 }).toEqual({ x: 4, y: 5 }); // o cubículo de cima (ADR-0082)

  // A fala que interrompe (ADR-0080): o dev para o bloco de trabalho e responde ao gerente.
  const said = (): Promise<string[]> =>
    page.evaluate(() => (window as unknown as { campsverso: { said(id: string): string[] } }).campsverso.said("tiago"));
  // A conversa (docs/design/briefing-tela.md, §3.5): o @ abre as sugestões de quem está na sala, o
  // Enter escolhe, e a fala vai com a menção; a resposta do dev aparece no registro.
  const heardBefore = (await said()).length;
  const talk = page.locator(".retro-talk");
  const speech = talk.getByRole("textbox", { name: "Falar" });
  await speech.pressSequentially("@Ti");
  await expect(talk.getByRole("option", { name: /@Tiago/ })).toBeVisible();
  await speech.press("Enter");
  await expect(speech).toHaveValue("@Tiago ");
  await speech.pressSequentially("como vai a busca?");
  await speech.press("Enter");
  await expect(speech).toHaveValue("");
  const log = talk.getByRole("log");
  await expect(log.locator(".retro-say.mine")).toContainText("@Tiago como vai a busca?");
  await expect.poll(async () => (await said()).slice(heardBefore), { timeout: 20_000 }).toContain("Anotado.");
  await expect(log).toContainText("Anotado.");
  await expect(log).toContainText("Tiago pegou o pedido 1"); // a linha do quadro
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

  // A tela do dev (ADR-0089), o terminal de fósforo verde (ADR-0092): o monitorzinho do chip do
  // Tiago abre a tela dele, com a entrada, os passos como comandos e o fim; a conversa conta o
  // começo. Sem modelo, as mãos são a rotina.
  await page.getByRole("button", { name: "Ver a tela do Tiago" }).click();
  const devScreen = page.getByRole("dialog", { name: "Tela do Tiago" });
  await expect(devScreen).toBeVisible();
  await expect(devScreen).toContainText("Pedido #1 · Ferramenta de busca");
  await expect(devScreen).toContainText("Mãos: rotina");
  await expect(devScreen).toContainText("o pedido #1 foi entregue");
  await expect(devScreen.locator(".retro-term-entry")).not.toHaveCount(0);
  await expect(devScreen.locator(".retro-term-bar")).toContainText("TERMINOU");
  await page.screenshot({ path: `${SHOTS}/escritorio-tela-do-dev.png` });
  await devScreen.getByRole("button", { name: "Fechar" }).click();
  await expect(devScreen).toBeHidden();
  await expect(log).toContainText("Tiago começou a programar o pedido 1: rotina");

  // A ficha aberta, na prancheta em leitura, e o "ver o patch" (ADR-0080): sem modelo, a sessão fixa
  // do dev-script na oficina registra o pedido num arquivo, e o patch vai ao depósito de entregas.
  await board.getByRole("button", { name: /^Pedido 1: Ferramenta de busca/ }).click();
  const card = page.getByRole("dialog", { name: "Pedido #1" });
  await expect(card.locator(".retro-stamp")).toHaveText("ENTREGUE"); // o carimbo do estado
  await expect(card).toContainText("com Tiago");
  await expect(card).toContainText("Achar um arquivo do repositório pelo nome.");
  await expect(card).toContainText("Claude Code · Opus 5.5");
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
  expect(right.every((x, i) => i === 0 || x >= (right[i - 1] ?? x) - 0.01), JSON.stringify({ right, trace: await trace("gerente") })).toBe(true); // nunca volta
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

  // A luz da sala (ADR-0088): o menu do interruptor, na parede à direita da porta, acende a luz, e
  // a conversa conta quem acendeu. De dia a sala não muda; à noite, o interruptor manda.
  const lightSwitch = await tile(page, 10, 13);
  await page.mouse.click(lightSwitch.x, lightSwitch.y, { button: "right" });
  await page.getByRole("menu", { name: "Interruptor" }).getByRole("menuitem", { name: /Acender a luz/ }).click();
  await expect(page.locator(".retro-talk").getByRole("log")).toContainText("Camps acendeu a luz da sala", { timeout: 30_000 });

  // A pausa do gerente (ADR-0082): o menu da máquina de café, na copa, e o café no HUD dele.
  const machine = await tile(page, 13, 9);
  await page.mouse.click(machine.x, machine.y, { button: "right" });
  const menu = page.getByRole("menu");
  await menu.getByRole("menuitem", { name: /Tomar um café/ }).click();
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

test("a ficha aberta: a devolução de 1.000 caracteres chega inteira ao quadro e ao dev (ADR-0092)", async ({ page }) => {
  test.setTimeout(150_000);
  await page.goto("/?assumir=1");
  const board = page.locator(".retro-board");
  await expect(page.getByRole("button", { name: "Soltar o gerente" })).toBeEnabled({ timeout: 45_000 });
  const understood = page.getByRole("button", { name: "Entendi" });
  if (await understood.isVisible()) {
    await understood.click();
  }
  await page.getByRole("button", { name: "72×", exact: true }).click(); // o teste de antes deixou a 1×
  await page.getByRole("button", { name: "Escrever pedido" }).click();
  const clipboard = page.getByRole("dialog", { name: "Novo pedido" });
  await clipboard.getByRole("textbox", { name: "Título" }).fill("Contar os cafés do dia");
  await clipboard.getByRole("textbox", { name: "O que fazer" }).fill("Um contador na copa, que zera à meia-noite.");
  await clipboard.getByRole("radio", { name: "P, pequeno" }).check();
  await clipboard.getByRole("button", { name: "Pôr no quadro" }).click();
  // A tela do dev pelo computador da sala (briefing-tela-3.md, §1): o clique no monitor da mesa do
  // Tiago, o tile de cima da mesa, abre a tela, e não anda. Com o pedido em "Fazendo", um passo novo
  // entra e se digita, e os que já estavam não são redesenhados (§4).
  await expect(board.getByRole("tab", { name: "Fazendo, 1 pedido" })).toBeVisible({ timeout: 60_000 });
  const monitor = await tile(page, 4, 3);
  await page.mouse.move(monitor.x, monitor.y);
  await expect(page.locator(".retro-screen-hover")).toBeVisible();
  const standing = await page.evaluate(() => (window as unknown as { campsverso: { drawn(id: string): unknown } }).campsverso.drawn("gerente"));
  await page.mouse.click(monitor.x, monitor.y);
  const devScreen = page.getByRole("dialog", { name: "Tela do Tiago" });
  await expect(devScreen).toBeVisible();
  // O Tiago ainda anda até a mesa: até a sessão nova começar, a tela mostra a do pedido 1, e troca
  // sozinha quando ela começa.
  await expect(devScreen).toContainText("Pedido #2 · Contar os cafés do dia", { timeout: 30_000 });
  await devScreen.locator(".retro-term-entry").evaluateAll((nodes) => {
    for (const node of nodes) {
      node.setAttribute("data-velha", "1");
    }
  });
  const old = await devScreen.locator(".retro-term-entry[data-velha]").count();
  await expect(devScreen.locator(".retro-term-entry.entering").first()).toBeAttached({ timeout: 30_000 });
  expect(await devScreen.locator(".retro-term-entry[data-velha]").count()).toBe(old); // os antigos ficam
  // Com a tela aberta, o teclado é dela: o gerente não anda; o Esc fecha.
  await page.keyboard.press("ArrowUp");
  await page.waitForTimeout(300);
  expect(await page.evaluate(() => (window as unknown as { campsverso: { drawn(id: string): unknown } }).campsverso.drawn("gerente"))).toEqual(standing);
  await page.screenshot({ path: `${SHOTS}/escritorio-tela-do-dev-ao-vivo.png` });
  await page.keyboard.press("Escape");
  await expect(devScreen).toBeHidden();
  // O dev-script pega, trabalha e entrega; a ficha entregue abre com o "O que falta" no papel.
  const delivered = board.getByRole("tab", { name: "Entregue, 1 pedido" });
  await expect(delivered).toBeVisible({ timeout: 100_000 });
  await delivered.click();
  await board.getByRole("button", { name: /^Pedido 2: Contar os cafés do dia/ }).click();
  const card = page.getByRole("dialog", { name: "Pedido #2" });
  const missing = card.getByRole("textbox", { name: /O que falta/ });
  await expect(card).toContainText("faltam 1.000 de 1.000");
  const long = "Falta zerar o contador à meia-noite do mundo, e não à do computador. ".repeat(20).slice(0, 999) + ".";
  expect(long).toHaveLength(1000);
  await missing.fill(long);
  await expect(card).toContainText("faltam 0 de 1.000"); // o contador, nunca o corte escondido
  await page.screenshot({ path: `${SHOTS}/escritorio-ficha-aberta.png` });
  await card.getByRole("button", { name: "Devolver" }).click();
  await expect(card).toBeHidden();
  // O fato chega inteiro à conversa, e a ficha volta com o "devolvido" e o comentário inteiro.
  await expect(page.locator(".retro-talk").getByRole("log")).toContainText(`devolveu o pedido 2: ${long}`, { timeout: 30_000 });
  const returned = board.getByRole("button", { name: /^Pedido 2: Contar os cafés do dia, tamanho pequeno, devolvido/ });
  for (const tab of ["A fazer", "Fazendo"]) {
    await board.getByRole("tab", { name: new RegExp(`^${tab},`) }).click();
    if (await returned.isVisible()) {
      break;
    }
  }
  await returned.click();
  await expect(page.getByRole("dialog", { name: "Pedido #2" }).locator(".retro-returned")).toHaveText(`Devolvido: ${long}`);
});

test("o monitor maior: a sala na altura toda, o relógio de 7 segmentos e o pedido no quadro (ADR-0092)", async ({ page }) => {
  // As duas janelas do briefing-tela-2.md, §6, com a escala da sala de cada uma.
  for (const [width, height, scale] of [
    [1288, 720, 1.09],
    [1456, 816, 1.28],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.goto("/?view=player");
    const panel = page.locator(".retro-panel");
    await expect(panel).toBeVisible({ timeout: 45_000 });
    await expect(page.locator(".retro-bar")).toBeHidden(); // a barra de baixo foi para o painel do monitor
    // A sala escala pelo CSS; o canvas do Phaser continua em 1x.
    const canvas = page.locator(".retro-screen canvas").first();
    await expect.poll(async () => Math.round(((await canvas.boundingBox())?.width ?? 0) / 6.4), { timeout: 10_000 }).toBe(Math.round(scale * 100));
    expect(await canvas.evaluate((c: HTMLCanvasElement) => [c.width, c.height])).toEqual([640, 512]);
    // Nada passa da janela.
    expect(await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.scrollHeight])).toEqual([width, height]);
    // O relógio de 7 segmentos diz a hora do mundo para quem não vê o visor; as pessoas, o "?" e o
    // "Assumir" no painel; o "Escrever pedido" no cabeçalho do quadro.
    await expect(panel.getByRole("img", { name: /^\d{2}:\d{2}$/ })).toBeVisible();
    await expect(panel.locator(".retro-chip").first()).toBeVisible();
    await expect(panel.getByRole("button", { name: "Os comandos" })).toBeVisible();
    await expect(panel.getByRole("button", { name: /o gerente$/ })).toBeVisible();
    await expect(page.locator(".retro-board-head").getByRole("button", { name: "Escrever pedido" })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/escritorio-grande-${String(width)}.png` });
  }
});

test("as janelas no padrão da tela: o menu colado ao clique, os comandos e os créditos (ADR-0092)", async ({ page }) => {
  await page.goto("/?assumir=1");
  await expect(page.getByRole("button", { name: "Soltar o gerente" })).toBeEnabled({ timeout: 45_000 });
  const understood = page.getByRole("button", { name: "Entendi" });
  if (await understood.isVisible()) {
    await understood.click();
  }
  // O menu do sofá (briefing-tela-4.md, §2): colado ao clique, com o rabicho, um ícone por ação, o
  // foco na primeira linha pronta e o contorno da coisa clicada; ↓ anda, e o Esc fecha.
  const sofa = await tile(page, 16, 5);
  await page.mouse.click(sofa.x, sofa.y, { button: "right" });
  const menu = page.getByRole("menu", { name: "Sofá" });
  await expect(menu).toBeVisible();
  await expect(menu.getByRole("menuitem", { name: /Ver TV/ })).toBeFocused();
  await expect(menu.locator(".retro-ic:not(.empty)")).not.toHaveCount(0);
  const box = await menu.boundingBox();
  expect(box).not.toBeNull();
  const gap = box === null ? Infinity : Math.min(Math.abs(box.x - sofa.x), Math.abs(box.x + box.width - sofa.x));
  expect(gap).toBeLessThanOrEqual(16); // o rabicho de 13 px entre o clique e a janela
  await expect(page.locator(".retro-menu-target")).toBeVisible();
  await page.screenshot({ path: `${SHOTS}/escritorio-menu.png` });
  await page.keyboard.press("ArrowDown");
  await expect(menu.getByRole("menuitem", { name: /Jogar videogame/ })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(menu).toBeHidden();
  await expect(page.locator(".retro-menu-target")).toBeHidden();
  // Os comandos (§3): só o que vale no escritório; o P porque o sandbox pode pausar.
  await page.getByRole("button", { name: "Os comandos" }).click();
  const commands = page.getByRole("dialog", { name: "Comandos" });
  await expect(commands).toBeVisible();
  await expect(commands).not.toContainText("grama");
  await expect(commands).not.toContainText("rola o mapa");
  await expect(commands).toContainText("pausa e retoma o relógio");
  await page.screenshot({ path: `${SHOTS}/escritorio-comandos.png` });
  await commands.getByRole("button", { name: "Entendi" }).click();
  await expect(commands).toBeHidden();
  // Os créditos pelo Sobre (§4): um bloco só, de desenho próprio, as fontes e o "Voltar ao Sobre".
  await page.getByRole("button", { name: "Sobre o Campsverso" }).click();
  await page.getByRole("dialog", { name: "Sobre o Campsverso" }).getByRole("button", { name: "Créditos" }).click();
  const credits = page.getByRole("dialog", { name: "Créditos" });
  await expect(credits).toContainText("Quem fez o escritório");
  await expect(credits).toContainText("Toda a arte deste mundo é desenho próprio");
  await expect(credits.locator(".retro-credit:not(.retro-fonts)")).toHaveCount(1);
  await expect(credits).toContainText("VT323");
  await page.screenshot({ path: `${SHOTS}/escritorio-creditos.png` });
  await credits.getByRole("button", { name: "Voltar ao Sobre" }).click();
  await expect(page.getByRole("dialog", { name: "Sobre o Campsverso" })).toBeVisible();
});

test("no celular, a câmera segue o gerente num recorte da sala, e as abas trocam o painel (§4)", async ({ page }) => {
  await page.setViewportSize({ width: 402, height: 874 });
  await page.goto("/?view=player");
  await expect(page.locator(".retro-phone-tabs")).toBeVisible({ timeout: 45_000 });
  await expect(page.locator(".retro-bar")).toBeHidden(); // a barra de baixo vira a faixa, as abas e a barra de ação
  await expect(page.locator(".retro-strip")).toBeVisible();
  await expect(page.locator(".retro-actionbar")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(402); // nada passa da tela
  // A sala não cabe em 1x: o canvas é o recorte do monitor, e a câmera anda por ele.
  const canvas = page.locator(".retro-screen .phaser canvas").first();
  await expect.poll(() => canvas.evaluate((c: HTMLCanvasElement) => c.width), { timeout: 10_000 }).toBeLessThan(640);
  const seguir = page.getByRole("button", { name: "seguir", exact: true });
  await expect(seguir).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".retro-minimap")).toBeVisible();
  await page.getByRole("tab", { name: /^Pessoas/ }).click();
  await expect(page.locator(".retro-people-panel .retro-chip").first()).toBeVisible();
  await expect(page.locator(".retro-board")).toBeHidden();
  await page.screenshot({ path: `${SHOTS}/escritorio-celular.png` });
  await page.getByRole("button", { name: "sala", exact: true }).click();
  await expect(page.getByRole("button", { name: "sala", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".retro-follow-tag")).toBeHidden();
});
