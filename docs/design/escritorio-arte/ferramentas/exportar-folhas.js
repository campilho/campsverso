// Abre a página da arte num navegador sem tela e salva as folhas, os metadados e,
// se pedido, os quadros da prévia (window.folhas, window.metadados, window.quadroPrevia).
// Da raiz do repositório, com o Playwright do apps/ui:
//   NODE_PATH=apps/ui/node_modules node docs/design/escritorio-arte/ferramentas/exportar-folhas.js \
//     docs/design/escritorio-arte/escritorio-arte.html /tmp/arte [quadros; -1 = o ciclo inteiro]
let pw;
try { pw = require('playwright'); } catch { pw = require('@playwright/test'); }
const { chromium } = pw;
const fs = require('fs'), path = require('path');
(async () => {
  const [html, out, nFrames] = process.argv.slice(2);
  fs.mkdirSync(path.join(out, 'folhas'), { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage();
  const erros = []; p.on('pageerror', e => erros.push(String(e))); p.on('console', m => { if (m.type() === 'error') erros.push(m.text()); });
  await p.goto('file://' + path.resolve(html)); await p.waitForTimeout(300);
  if (erros.length) { console.error(erros.join('\n')); process.exit(1); }
  const folhas = await p.evaluate(() => window.folhas());
  for (const [n, d] of Object.entries(folhas)) fs.writeFileSync(path.join(out, 'folhas', n + '.png'), Buffer.from(d.split(',')[1], 'base64'));
  const meta = await p.evaluate(() => window.metadados());
  fs.writeFileSync(path.join(out, 'folhas', 'metadados.json'), JSON.stringify(meta, null, 2));
  console.log('folhas:', Object.keys(folhas).length, '· cores usadas:', meta.coresUsadas.length);
  const n = nFrames ? +nFrames : 0;
  if (n) {
    fs.mkdirSync(path.join(out, 'quadros'), { recursive: true });
    const ciclo = await p.evaluate(() => window.cicloPrevia());
    const total = n < 0 ? ciclo : n;
    for (const noite of [false, true]) for (let i = 0; i < (noite ? 1 : total); i++) {
      const d = await p.evaluate(([i, noite]) => window.quadroPrevia(i, { noite }), [i, noite]);
      fs.writeFileSync(path.join(out, 'quadros', (noite ? 'noite_' : 'dia_') + String(i).padStart(4, '0') + '.png'), Buffer.from(d.split(',')[1], 'base64'));
    }
    console.log('quadros da prévia:', total, '(ciclo', ciclo + ')');
  }
  await b.close();
})();
