// As capturas da arte nova do escritório (ADR-0082) com o Playwright sem janela, num sandbox do
// escritório no ar. Da raiz do repositório:
//   node docs/design/escritorio-arte/ferramentas/capturar-arte-nova.cjs <dia|noite|sofa> <url> <pasta>
// - dia: num mundo que começa às 08:59 (MUNDO=office-campsverso-demo), o gerente entra e escreve três
//   pedidos (P, M e G); às 09:50, a sala e o quadro com as fichas; às 12:10, a copa no almoço;
// - noite: num mundo que começa perto das 18:00, a sala com as luminárias e, das 21:00 em diante,
//   dez fotos do escuro com o vigia na ronda (escolha a melhor);
// - sofa: só na captura, a página recebe um patch com o gerente no tapete jogando videogame (o
//   kernel ainda não tinha a ação), para ver o sofá e a TV com o jogo.
const path = require("node:path");
const { chromium } = require(require.resolve("@playwright/test", { paths: [path.resolve("apps/ui")] }));

const [mode, base, out] = process.argv.slice(2);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const hms = (t) => [Math.floor(t / 3600), Math.floor(t / 60) % 60, t % 60].map((n) => String(n).padStart(2, "0")).join(":");

async function clock(page) {
  const match = /(\d{2}):(\d{2})(?::(\d{2}))?/.exec(await page.locator(".hud").first().innerText());
  return match === null ? -1 : Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3] ?? 0);
}

async function until(page, hhmmss) {
  const [h, m, s = 0] = hhmmss.split(":").map(Number);
  while ((await clock(page)) < h * 3600 + m * 60 + s) {
    await wait(250);
  }
}

/** O mapa inteiro, ou um recorte dele em pixels do mapa (20 tiles de 32 px de largura). */
async function shot(page, name, clip) {
  const understood = page.getByRole("button", { name: "Entendi" });
  if (await understood.isVisible()) {
    await understood.click(); // a ajuda dos comandos, por cima do mapa
    await wait(300);
  }
  const canvas = page.locator("canvas").first();
  const file = path.join(out, `${name}.png`);
  if (clip === undefined) {
    await canvas.screenshot({ path: file });
  } else {
    const box = await canvas.boundingBox();
    const scale = box.width / 640;
    const area = { x: box.x + clip.x * scale, y: box.y + clip.y * scale, width: clip.w * scale, height: clip.h * scale };
    await page.screenshot({ path: file, clip: area });
  }
  console.log(name, hms(await clock(page)));
}

async function operator(browser, inject) {
  const page = await browser.newPage({ viewport: { width: 1300, height: 900 }, deviceScaleFactor: 2 });
  if (inject !== undefined) {
    await page.routeWebSocket(/\/ws/, (ws) => {
      const server = ws.connectToServer();
      let sent = false;
      server.onMessage((message) => {
        ws.send(message);
        if (!sent && String(message).includes("realtime.welcome")) {
          sent = true;
          setTimeout(() => ws.send(JSON.stringify(inject)), 1500);
        }
      });
      ws.onMessage((message) => server.send(message));
    });
  }
  await page.goto(`${base}/?view=operator`);
  await page.locator("canvas").first().waitFor();
  await wait(2500);
  return page;
}

const T = 32;

(async () => {
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  if (mode === "noite") {
    const page = await operator(browser);
    if ((await clock(page)) < 20 * 3600 + 30 * 60) {
      await shot(page, "sala-luminarias");
    }
    await until(page, "21:00:20");
    for (let i = 1; i <= 10; i++) {
      await shot(page, `noite-${String(i)}`);
      await wait(900);
    }
  } else if (mode === "sofa") {
    const page = await operator(browser, {
      type: "campsverso.realtime.update.v1",
      patch: {
        entities: { gerente: { kind: "avatar", position: { x: 16, y: 6 }, display_name: "Gerente", attributes: { papel: "gerente" } } },
        actions: { gerente: { action_id: "captura-sofa", action: "videogame", params: {}, end_tick: 999999999 } },
      },
      events: [],
    });
    await wait(2500);
    await shot(page, "sofa-jogando", { x: 13 * T, y: T, w: 7 * T, h: 6 * T });
  } else {
    const page = await operator(browser);
    const player = await browser.newPage({ viewport: { width: 1300, height: 900 } });
    await player.goto(`${base}/?assumir=1`);
    await player.locator(".hud").waitFor();
    await wait(3000);
    const understood = player.getByRole("button", { name: "Entendi" });
    if (await understood.isVisible()) {
      await understood.click();
    }
    const office = player.locator("aside.office");
    for (const [title, size] of [["Busca de arquivos", "P"], ["Relatório do dia", "M"], ["Painel de métricas", "G"]]) {
      await player.getByPlaceholder("Título").fill(title);
      await player.getByPlaceholder("O que fazer").fill(`${title}: o que o gerente pediu.`);
      await office.locator("select").first().selectOption(size);
      await player.getByRole("button", { name: "Escrever no quadro" }).click();
      await wait(2500);
    }
    await until(page, "09:50:00");
    await shot(page, "sala-dia");
    await shot(page, "quadro-fichas", { x: T, y: 0, w: 5 * T, h: 2 * T });
    await until(page, "12:10:00");
    await shot(page, "sala-almoco");
    await shot(page, "copa-almoco", { x: 11 * T, y: 8 * T, w: 9 * T, h: 5 * T });
  }
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
