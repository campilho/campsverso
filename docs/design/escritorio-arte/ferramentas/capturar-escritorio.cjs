// Captura o escritório com a arte nova (ADR-0082) em dois momentos do mesmo mundo: a sala de dia
// com o dev digitando na mesa, e o dev almoçando na copa. Precisa de um sandbox do escritório no
// ar (make sandbox MUNDO=office-campsverso-demo, que roda a 72×) e do Playwright do apps/ui. Da
// raiz do repositório:
//   NODE_PATH=apps/ui/node_modules node docs/design/escritorio-arte/ferramentas/capturar-escritorio.cjs \
//     http://127.0.0.1:8765 docs/design/escritorio-arte/comparacao
// A página assume o gerente, escreve um pedido no quadro e espera o dev sentar e trabalhar; pausa,
// fotografa, retoma e espera o almoço passar das 12:10.
let pw;
try { pw = require('playwright'); } catch { pw = require('@playwright/test'); }
const { chromium } = pw;
const fs = require('fs'), path = require('path');

const drawn = (page, id) => page.evaluate((who) => window.campsverso?.drawn(who), id);
const hud = async (page) => ((await page.locator('.hud').textContent()) ?? '').replace(/\s+/g, ' ');
const until = async (what, test, ms = 240_000) => {
  const end = Date.now() + ms;
  for (;;) {
    if (await test().catch(() => false)) return;
    if (Date.now() > end) throw new Error(`esperando ${what}`);
    await new Promise((r) => setTimeout(r, 250));
  }
};
const clock = async (page) => {
  const match = /(\d\d):(\d\d)(?::\d\d)?/.exec(await hud(page));
  return match === null ? -1 : Number(match[1]) * 60 + Number(match[2]);
};

async function pause(page) {
  await page.keyboard.press('p');
  await until('a pausa', async () => (await hud(page)).includes('pausado'), 15_000);
  await page.waitForTimeout(1200); // o desenho assenta
}

async function resume(page) {
  await page.keyboard.press('p');
  await until('o relógio andando', async () => !(await hud(page)).includes('pausado'), 15_000);
}

async function clipAround(page, from, to) {
  const a = await page.evaluate(([x, y]) => window.campsverso.tileCenter(x, y), from);
  const b = await page.evaluate(([x, y]) => window.campsverso.tileCenter(x, y), to);
  return { x: a.x - 16, y: a.y - 16, width: b.x - a.x + 32, height: b.y - a.y + 32 };
}

(async () => {
  const [base, out] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  // O Chrome da máquina, como os testes da tela fora do CI (apps/ui/playwright.config.ts).
  const browser = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch());
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto(`${base}/?view=player&assumir=1`);
  await until('o gerente', async () => (await hud(page)).includes('human/'));
  const understood = page.getByRole('button', { name: 'Entendi' });
  if (await understood.isVisible()) await understood.click();
  // O gerente escreve um pedido; o dev pega, senta e trabalha.
  const office = page.locator('aside.office');
  for (let attempt = 0; !(await office.textContent())?.includes('#1') && attempt < 3; attempt++) {
    await page.getByPlaceholder('Título').fill('Ferramenta de busca');
    await page.getByPlaceholder('O que fazer').fill('Achar um arquivo do repositório pelo nome.');
    await page.getByRole('button', { name: 'Escrever no quadro' }).click();
    await page.waitForTimeout(3000);
  }
  await until('o dev trabalhando na mesa', async () => {
    const at = await drawn(page, 'camps');
    return at?.x === 4 && at?.y === 5 && (await hud(page)).includes('fazendo: work');
  });
  await page.waitForTimeout(800);
  await pause(page);
  await page.locator('canvas').first().screenshot({ path: path.join(out, 'sala-dia.png') });
  await page.screenshot({ path: path.join(out, 'mesa-dev.png'), clip: await clipAround(page, [1, 2], [11, 10]) });
  fs.writeFileSync(path.join(out, 'instante.txt'), `sala: ${await hud(page)}\n`);
  // O almoço: a geladeira, o micro-ondas, a mesinha da copa.
  await resume(page);
  await until('o almoço na copa', async () => (await clock(page)) >= 12 * 60 + 10 && (await hud(page)).includes('lunch'), 420_000);
  await page.waitForTimeout(600);
  await pause(page);
  await page.locator('canvas').first().screenshot({ path: path.join(out, 'sala-almoco.png') });
  await page.screenshot({ path: path.join(out, 'copa-almoco.png'), clip: await clipAround(page, [11, 8], [18, 12]) });
  fs.appendFileSync(path.join(out, 'instante.txt'), `almoço: ${await hud(page)}\n`);
  await browser.close();
  console.log('capturas em', out);
})().catch((error) => { console.error(error); process.exit(1); });
