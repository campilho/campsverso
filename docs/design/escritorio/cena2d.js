// Camada visual 2D: o escritório em corte, como casa de bonecas, em pixel art.
// Resolução interna fixa de 640 × 360, ampliada em múltiplos inteiros de pixel
// do aparelho. Lê o quadro do motor e as posições da locomoção; não decide
// nada sobre quem está onde. Paleta limitada, contorno escuro e uma cor
// dominante por sala; luz pela hora (cones pontilhados, sol no chão, noite azul).

import { W, H, ANDARES, SALAS, SALA, retSala, ESCADA, MESAS, ESTANTE, TUBO, DEPLOY, SOFA, TV } from "./planta.js";
import { sprite, quadroNoTempo, visual, SW, SH, PE } from "./sprites.js";
import { escreve, placa, medeTexto, escreveMini, medeMini } from "./pixelfont.js";

const A1 = ANDARES[1], A0 = ANDARES[0];
const novoCanvas = (w, h) => Object.assign(document.createElement("canvas"), { width: w, height: h });
const rgb = a => `rgb(${a[0]},${a[1]},${a[2]})`;
function R(c, x, y, w, h, cor) { c.fillStyle = cor; c.fillRect(x, y, w, h); }
function caixa(c, x, y, w, h, cor, borda = "#1c1a26") { R(c, x, y, w, h, borda); R(c, x + 1, y + 1, w - 2, h - 2, cor); }

// Paleta (limitada) ------------------------------------------------------------
const P = {
  tinta: "#1c1a26", estrutura: "#363a48", laje: "#515565", lajeC: "#6b6f80", lajeE: "#2b2d38",
  madeira: "#b98a5a", madeiraC: "#d09c68", madeiraE: "#7a4d2d",
  khaki: "#d8cca8", khakiE: "#c3b58c", divisoria: "#c4b085", divisoriaE: "#a8956b", poste: "#6f6250",
  carpete: "#3d4a66", carpeteC: "#47557a",
  verde: "#cfe0d0", verdeE: "#b4cbb6",
  laranja: "#f0dbb6", laranjaE: "#e3c391", cafe: "#6b4426",
  cinzaAzul: "#cfd8dc", cinzaAzulE: "#aebcc2", aco: "#b6c0c9", acoE: "#8d97a3", acoEE: "#5a6370",
  srv: "#2c3a4f", srvE: "#223044", srvC: "#3a4b63",
  bege: "#d9cfb4", begeE: "#b8ad91", begeC: "#ebe3cc",
  vidro: "#9fc7d6", folha: "#4ea35a", folhaE: "#3f8a4b", vaso: "#b0613a",
  branco: "#f4f1ea", preto: "#20252c", tela: "#2a2f3a", lencol: "#ebe2cd", lencolE: "#cdbf9f", lencolEE: "#b5a684",
  sofa: "#2e6b6f", sofaE: "#22555a", sofaC: "#3d8186",
};

const LUMINARIAS = {
  dev: [[172, 50], [270, 50], [358, 50], [431, 34]], planejamento: [[566, 64]], portaria: [[108, 50]],
  cafe: [[214, 54], [300, 54], [392, 58]], servidores: [[478, 50], [574, 70]], escada: [],
};
const JANELAS = [];
const COLUNAS = [["a fazer", "A FAZER", "#ffe27a"], ["fazendo", "FAZENDO", "#9fd8ff"], ["revisão", "REVISÃO", "#dcc2ff"], ["publicado", "NO AR", "#b9f0a8"]];
const QUADRO = { x: 158, y: A1.teto + 12, w: 128, h: 64 };
const ESPEC = { x: 512, y: A1.teto + 14, w: 108, h: 58 };
const PAINEL_CI = { x: 520, y: A0.teto + 6, w: 96, h: 18 };
const ANDON = { x: 507, y: A0.teto + 36 };

// ------------------------------------------------------------ prédio (fundo e frente)
function montaPredio(cfg) {
  JANELAS.length = 0;
  const fundo = novoCanvas(W, H), frente = novoCanvas(W, H);
  const f = fundo.getContext("2d"), g = frente.getContext("2d");
  R(f, 0, 16, 640, 320, P.estrutura);
  // telhado: platibanda, caixa d'água, antena, parabólica, condensadoras, letreiro
  R(f, 0, 16, 640, 8, P.laje); R(f, 0, 16, 640, 1, P.lajeC); R(f, 0, 23, 640, 1, P.lajeE);
  caixa(f, 118, 3, 28, 13, "#6c7384"); R(f, 119, 4, 26, 2, "#8a91a2"); R(f, 124, 0, 16, 3, "#5a6070");
  R(f, 470, 4, 2, 12, "#5a6070"); R(f, 462, 1, 18, 3, "#7d8495"); R(f, 466, 0, 10, 1, "#9aa1b2");
  R(f, 532, 10, 3, 6, "#5a6070"); for (let i = 0; i < 9; i++) R(f, 524 + i, 9 - Math.round(Math.sin(i / 8 * Math.PI) * 5), 2, 2, "#b8bec8"); R(f, 531, 4, 4, 2, "#8d97a3");
  for (const x of [580, 606]) { caixa(f, x, 6, 22, 10, "#a9b0ba"); for (let k = 0; k < 3; k++) R(f, x + 3 + k * 6, 8, 4, 6, "#7d8590"); R(f, x + 2, 15, 18, 1, "#6b7280"); }
  R(f, 250, 13, 2, 3, P.lajeE); R(f, 290, 13, 2, 3, P.lajeE); caixa(f, 244, 1, 54, 13, "#0d1215");
  // lajes e base
  R(f, 0, 172, 640, 8, P.laje); R(f, 0, 172, 640, 1, P.lajeC); R(f, 0, 179, 640, 1, P.lajeE);
  R(f, 0, 328, 640, 6, P.laje); R(f, 0, 328, 640, 1, P.lajeC);
  // calçada e rua
  R(f, 0, 334, 640, 10, "#a7a6a1"); for (let x = 0; x < 640; x += 18) R(f, x, 334, 1, 10, "#8f8e89");
  R(f, 0, 344, 640, 2, "#7b7a76"); R(f, 0, 346, 640, 14, "#3a3c44");
  for (let x = 6; x < 640; x += 28) R(f, x, 353, 14, 1, "#cfc7a2");
  R(f, 176, 328, 6, 7, "#c0392b"); R(f, 175, 330, 8, 2, "#a5281c");
  R(f, 560, 331, 22, 2, "#7a5434"); R(f, 562, 333, 2, 3, "#3a3a3a"); R(f, 578, 333, 2, 3, "#3a3a3a");
  for (const s of SALAS) sala(f, g, s, cfg);
  return { fundo, frente };
}

function piso(f, x0, x1, a, padrao) {
  const y0 = a.chao, y1 = a.base;
  if (padrao === "carpete") {
    R(f, x0, y0, x1 - x0, y1 - y0, P.carpete);
    for (let y = y0; y < y1; y += 2) for (let x = x0 + (y % 4); x < x1; x += 6) R(f, x, y, 1, 1, P.carpeteC);
  } else if (padrao === "xadrez" || padrao === "ladrilho") {
    const [c1, c2] = padrao === "xadrez" ? ["#cdb999", "#b4a080"] : ["#9ca7ae", "#8c979e"];
    for (let y = y0; y < y1; y += 4) for (let x = x0; x < x1; x += 4) R(f, x, y, 4, 4, ((x - x0) / 4 + (y - y0) / 4) % 2 ? c1 : c2);
  } else if (padrao === "elevado") {
    R(f, x0, y0, x1 - x0, y1 - y0, "#6f7c8e");
    for (let x = x0; x < x1; x += 8) R(f, x, y0, 1, y1 - y0, "#5b6778");
    R(f, x0, y0 + 8, x1 - x0, 1, "#5b6778");
    for (let x = x0 + 4; x < x1; x += 16) R(f, x, y0 + 3, 2, 2, "#4a5566");
  } else if (padrao === "madeira") {
    for (let y = y0; y < y1; y += 2) R(f, x0, y, x1 - x0, 2, (y - y0) % 4 ? "#9a6b43" : "#a8794d");
    for (let y = y0; y < y1; y += 4) for (let x = x0 + ((y / 4) % 2) * 9; x < x1; x += 18) R(f, x, y, 1, 2, "#7f5534");
  }
  R(f, x0, y0, x1 - x0, 1, "rgba(0,0,0,.28)");
  R(f, x0, y1 - 1, x1 - x0, 1, "rgba(0,0,0,.35)");
}
function parede(f, x0, x1, a, cor, rodape, lambri) {
  R(f, x0, a.teto, x1 - x0, a.chao - a.teto, cor);
  R(f, x0, a.teto, x1 - x0, 3, "rgba(0,0,0,.22)");
  if (lambri) { R(f, x0, a.chao - 30, x1 - x0, 30, lambri); R(f, x0, a.chao - 31, x1 - x0, 1, "rgba(0,0,0,.18)"); R(f, x0, a.chao - 32, x1 - x0, 1, "rgba(255,255,255,.2)"); }
  R(f, x0, a.chao - 3, x1 - x0, 3, rodape);
}
function janela(f, sala, cx, w, y0, h) {
  const x0 = Math.round(cx - w / 2);
  JANELAS.push({ sala, x: x0, y: y0, w, h });
  R(f, x0 - 3, y0 - 3, w + 6, h + 6, P.tinta); R(f, x0 - 2, y0 - 2, w + 4, h + 4, "#e9e4d8");
  R(f, x0 - 4, y0 + h + 2, w + 8, 3, "#b9b2a2"); R(f, x0 - 4, y0 + h + 2, w + 8, 1, "#d8d1c2");
  f.clearRect(x0, y0, w, h);
  for (let x = x0 + Math.floor(w / 3); x < x0 + w - 2; x += Math.floor(w / 3)) R(f, x, y0, 2, h, "#e9e4d8");
  R(f, x0, y0 + Math.floor(h / 2), w, 2, "#e9e4d8");
}
function porta(f, x, a) { R(f, x, a.chao - 50, 4, 50, "#22242e"); }
function luminariaTeto(f, x, a, larga = false) {
  if (larga) { R(f, x - 9, a.teto, 1, 5, "#3a3a44"); R(f, x + 9, a.teto, 1, 5, "#3a3a44"); caixa(f, x - 12, a.teto + 5, 25, 4, "#d9dde3"); R(f, x - 10, a.teto + 9, 21, 1, "#f6f0c8"); return; }
  R(f, x, a.teto, 1, 7, "#3a3a44"); caixa(f, x - 5, a.teto + 7, 11, 4, "#2f3340"); R(f, x - 3, a.teto + 11, 7, 1, "#f6e7b0");
}
function planta(f, x, y, alta = false) {
  caixa(f, x, y - 9, 10, 9, P.vaso); R(f, x + 1, y - 8, 8, 1, "#c8774a");
  const h = alta ? 26 : 14;
  R(f, x + 4, y - 9 - h, 2, h, P.folhaE);
  for (let i = 0; i < (alta ? 6 : 3); i++) { const yy = y - 12 - i * 4; R(f, x + (i % 2 ? 6 : 0), yy, 4, 3, i % 2 ? P.folha : P.folhaE); R(f, x + (i % 2 ? 7 : 1), yy, 2, 1, "#6cc077"); }
}
function caneca(c, x, y, cor = P.branco) { R(c, x, y, 4, 4, P.tinta); R(c, x + 1, y + 1, 2, 3, cor); R(c, x + 4, y + 1, 1, 2, P.tinta); }
function cadeira(f, cx, pe, cor = "#7a4a33") {
  caixa(f, cx - 8, pe - 38, 16, 17, cor); R(f, cx - 6, pe - 37, 12, 1, "#9a6347"); R(f, cx - 1, pe - 21, 2, 6, "#262a35");
}
function relogioParede(f, x, y) { caixa(f, x, y, 13, 13, "#f7f3e8", "#3a3a44"); }

function sala(f, g, s, cfg) {
  const r = retSala(s.id), a = s.andar === -1 ? null : ANDARES[s.andar];
  const x0 = r.x, x1 = r.x + r.w;
  switch (s.id) {
    case "escada": {
      R(f, x0, r.y, r.w, r.h, "#bdb6a9"); R(f, x0, r.y, r.w, 3, "rgba(0,0,0,.2)");
      for (let y = r.y + 12; y < r.y + r.h; y += 24) R(f, x0, y, r.w, 1, "#aca596");
      R(f, 28, 166, 24, 6, "#8c8475"); R(f, 28, 166, 24, 1, "#a39b8b");
      R(f, 4, 312, 48, 16, "#8c8475"); R(f, 4, 312, 48, 1, "#a39b8b");
      const lance = (p, q) => {
        for (let i = 0; i <= 48; i++) { const t = i / 48; R(f, Math.round(p.x + (q.x - p.x) * t) - 4, Math.round(p.y + (q.y - p.y) * t) + 1, 9, 6, "#7d7566"); }
        for (let i = 0; i < 10; i++) { const t = (i + .5) / 10; R(f, Math.round(p.x + (q.x - p.x) * t) - 5, Math.round(p.y + (q.y - p.y) * t), 11, 2, "#a8a090"); }
      };
      lance(ESCADA.cima, ESCADA.meio); lance(ESCADA.meio, ESCADA.baixo);
      R(f, 4, 244, 14, 4, "#8c8475"); R(f, 4, 244, 14, 1, "#a39b8b");
      // trilho da plataforma (para o robô de rodas), listrado
      for (const [p, q] of [[ESCADA.cima, ESCADA.meio], [ESCADA.meio, ESCADA.baixo]]) for (let i = 0; i <= 40; i++) { const t = i / 40; R(f, Math.round(p.x + (q.x - p.x) * t) + 5, Math.round(p.y + (q.y - p.y) * t) + 7, 2, 1, i % 4 < 2 ? "#e9c46a" : "#3a3a3a"); }
      for (const [p, q] of [[ESCADA.cima, ESCADA.meio], [ESCADA.meio, ESCADA.baixo]]) for (let i = 0; i <= 30; i++) { const t = i / 30; R(g, Math.round(p.x + (q.x - p.x) * t), Math.round(p.y - 14 + (q.y - p.y) * t), 1, 1, "#5b4636"); }
      caixa(f, 8, 274, 20, 38, "#6b4a2e"); R(f, 11, 278, 14, 14, P.vidro); R(f, 11, 278, 14, 1, "#cfe6ee"); R(f, 23, 296, 2, 2, "#e0c070"); R(f, 6, 272, 24, 2, "#4a3322");
      caixa(f, 40, 292, 5, 10, "#c0392b"); R(f, 41, 290, 3, 2, P.tinta);
      for (const y of [40, 196]) { caixa(f, 22, y, 9, 5, "#2f3340"); R(f, 23, y + 5, 7, 1, "#f6e7b0"); }
      porta(f, 52, A1); porta(f, 52, A0);
      break;
    }
    case "dev": {
      parede(f, x0, x1, a, P.khaki, "#8f7b5e", null);
      for (let x = x0; x < x1; x += 4) for (let y = a.teto + 4; y < a.chao - 4; y += 6) if ((x + y) % 5 === 0) R(f, x, y, 1, 1, "rgba(120,100,60,.12)");
      piso(f, x0, x1, a, "carpete");
      janela(f, "dev", 84, 40, a.teto + 22, 38);
      janela(f, "dev", 334, 44, a.teto + 22, 38);
      // quadro de tickets (cortiça); os cartões entram na camada dinâmica
      const q = QUADRO;
      caixa(f, q.x, q.y, q.w, q.h, "#6b4a2e"); R(f, q.x + 2, q.y + 2, q.w - 4, q.h - 4, "#c39462");
      for (let i = 0; i < 40; i++) R(f, q.x + 3 + (i * 7) % (q.w - 6), q.y + 3 + (i * 5) % (q.h - 6), 1, 1, "#a87a4c");
      const cw = Math.floor((q.w - 4) / 4);
      COLUNAS.forEach(([, rot, cor], i) => {
        const cx = q.x + 2 + i * cw;
        R(f, cx + 1, q.y + 3, cw - 2, 7, "#2a2430"); escreveMini(f, rot, cx + Math.round((cw - medeMini(rot)) / 2), q.y + 4, cor);
        if (i) R(f, cx, q.y + 11, 1, q.h - 14, "#a87a4c");
      });
      placa(f, cfg.sprint || "SPRINT", q.x + q.w / 2, q.y - 9, { fundo: "#3a2f2a", texto: "#f4efe4", pad: 2 });
      relogioParede(f, 292, a.teto + 12);
      // pôster retrô
      caixa(f, 364, a.teto + 16, 30, 40, "#1c1a26"); R(f, 366, a.teto + 18, 26, 36, "#24324a");
      for (let i = 0; i < 5; i++) R(f, 366, a.teto + 44 + i * 2, 26, 1, ["#f2c230", "#f08a3a", "#e74c3c", "#c04fa8", "#5b5fc7"][i]);
      R(f, 373, a.teto + 23, 12, 9, "#cfc6ac"); R(f, 374, a.teto + 24, 10, 6, "#0b2414"); escreveMini(f, ">_", 375, a.teto + 25, "#39ff6a"); R(f, 376, a.teto + 32, 6, 2, "#b0a78e");
      escreveMini(f, "RUN", 373, a.teto + 37, "#f4efe4");
      // divisórias dos cubículos e cadeiras
      for (const m of MESAS) {
        const px = m.x - 29;
        R(f, px, a.pe - 46, 58, a.chao - (a.pe - 46), P.divisoria); R(f, px, a.pe - 46, 58, 2, P.divisoriaE); R(f, px, a.pe - 44, 58, 1, "#d8c79c");
        for (let y = a.pe - 40; y < a.chao; y += 3) for (let x = px + ((y / 3) % 2) * 2; x < px + 58; x += 4) R(f, x, y, 1, 1, "rgba(120,100,60,.18)");
        R(f, px, a.pe - 46, 2, a.chao - (a.pe - 46), P.poste); R(f, px + 57, a.pe - 46, 2, a.chao - (a.pe - 46), P.poste);
        caixa(f, m.x + 10, a.pe - 41, 12, 9, "#f6f1e3"); for (let k = 0; k < 3; k++) R(f, m.x + 12, a.pe - 39 + k * 2, 8, 1, "#9aa0ad");   // papelzinho preso
      }
      // estante com a doca do drone em cima
      const e = ESTANTE;
      caixa(f, e.x0, e.topo, e.x1 - e.x0, a.chao - e.topo, "#6b6f78");
      for (let i = 0; i < 4; i++) {
        const y = e.topo + 4 + i * 24; R(f, e.x0 + 1, y + 21, e.x1 - e.x0 - 2, 2, "#4a4e57");
        for (let x = e.x0 + 3, k = 0; x < e.x1 - 4; k++) {
          if ((k + i) % 4 === 3) { caixa(f, x, y + 9, 9, 12, "#b8894f"); R(f, x + 2, y + 12, 5, 3, P.branco); x += 10; continue; }
          const w = 3 + (k % 2), hgt = 15 + ((k + i) % 3) * 2;
          R(f, x, y + 21 - hgt, w, hgt, ["#c0392b", "#2f86d0", "#e9c46a", "#3a7d5c", "#7a5fd0", "#d8962c"][(k + i * 2) % 6]); R(f, x, y + 21 - hgt + 3, w, 1, "rgba(255,255,255,.35)");
          x += w + 1;
        }
      }
      caixa(f, e.x0 + 3, e.topo - 4, e.x1 - e.x0 - 6, 4, "#3a3f49"); R(f, e.x0 + 5, e.topo - 3, e.x1 - e.x0 - 10, 1, "#5ff2ff");
      // tubo pneumático e a estação do Mensageiro
      const t = TUBO, tx = t.x - 4;
      R(f, tx, a.teto, 8, 44, "#8d97a3"); R(f, tx + 1, a.teto, 2, 44, "#c3cbd4"); R(f, tx + 6, a.teto, 1, 44, "#5a6370");
      for (let y = a.teto + 10; y < a.teto + 44; y += 12) R(f, tx - 1, y, 10, 2, "#d6409f");
      caixa(f, t.x - 14, t.peitoril - 34, 28, 34, "#9aa3ae"); R(f, t.x - 13, t.peitoril - 33, 26, 2, "#c3cbd4");
      R(f, t.x - 10, t.peitoril - 28, 20, 28, "#1c2230"); R(f, t.x - 10, t.peitoril - 28, 20, 2, "#0f141c");
      R(f, tx, t.peitoril + 12, 8, a.chao - t.peitoril - 12, "#8d97a3"); R(f, tx + 1, t.peitoril + 12, 2, a.chao - t.peitoril - 12, "#c3cbd4");
      caixa(g, t.x - 15, t.peitoril, 30, 14, "#b7c0ca"); R(g, t.x - 14, t.peitoril + 1, 28, 1, "#dfe5ec");
      escreveMini(g, "CORREIO", t.x - 13, t.peitoril + 5, "#2a2f3a");
      planta(f, 58, a.chao + 6, true);
      for (const [x] of LUMINARIAS.dev) luminariaTeto(f, x, a, true);
      porta(f, 488, a);
      break;
    }
    case "planejamento": {
      parede(f, x0, x1, a, P.verde, "#6f8a74", P.verdeE);
      piso(f, x0, x1, a, "madeira");
      // quadro branco com a especificação atual
      const q = ESPEC;
      caixa(f, q.x, q.y, q.w, q.h, "#fbfbf7", "#6b7280"); R(f, q.x + 1, q.y + q.h - 2, q.w - 2, 1, "#d9dde3");
      escreveMini(f, "ESPECIFICAÇÃO ATUAL", q.x + 4, q.y + 4, "#566170");
      const tit = (cfg.espec || "").toUpperCase().slice(0, 25);
      escreveMini(f, tit, q.x + 4, q.y + 12, "#1f4e8c"); R(f, q.x + 4, q.y + 18, medeMini(tit), 1, "#1f4e8c");
      const cabe = (txt, n) => { txt = txt.toUpperCase(); if (txt.length <= n) return txt; const c = txt.slice(0, n + 1); const e = c.lastIndexOf(" "); return (e > 4 ? c.slice(0, e) : c.slice(0, n)); };
      (cfg.itens || []).slice(0, 5).forEach((it, i) => { R(f, q.x + 5, q.y + 24 + i * 6, 2, 2, "#c0392b"); escreveMini(f, cabe(it, 23), q.x + 9, q.y + 23 + i * 6, "#3a404c"); });
      R(f, q.x + 6, q.y + q.h, q.w - 12, 3, "#9aa1ab"); R(f, q.x + 20, q.y + q.h + 1, 6, 1, "#c0392b"); R(f, q.x + 30, q.y + q.h + 1, 6, 1, "#2f86d0");
      // vidro para o desenvolvimento
      R(f, x0, a.teto + 30, 6, a.chao - a.teto - 30, "rgba(160,215,230,.35)"); R(f, x0 + 2, a.teto + 36, 1, 24, "rgba(255,255,255,.55)");
      planta(f, 624, a.chao + 6, true);
      relogioParede(f, 498, a.teto + 10);
      for (const [x] of LUMINARIAS.planejamento) luminariaTeto(f, x, a, true);
      // cadeiras e mesa de reunião (na frente)
      for (const x of [536, 566, 596]) cadeira(f, x, a.pe, "#3d6b55");
      R(g, 512, a.pe - 21, 108, 4, P.tinta); R(g, 513, a.pe - 20, 106, 2, "#8a6d52"); R(g, 514, a.pe - 18, 104, 2, "#6e5640");
      R(g, 520, a.pe - 16, 3, 16, "#3b3f4b"); R(g, 609, a.pe - 16, 3, 16, "#3b3f4b");
      caneca(g, 540, a.pe - 25, "#2fa36b"); caixa(g, 576, a.pe - 24, 12, 3, "#f6f1e3"); R(g, 598, a.pe - 24, 9, 3, "#2a2f3a");
      break;
    }
    case "portaria": {
      parede(f, x0, x1, a, P.cinzaAzul, "#5f6d75", P.cinzaAzulE);
      piso(f, x0, x1, a, "ladrilho");
      janela(f, "portaria", 134, 26, a.teto + 22, 34);
      caixa(f, 62, a.teto + 22, 20, 16, "#6b4a2e"); for (let i = 0; i < 6; i++) { R(f, 65 + (i % 3) * 5, a.teto + 25 + Math.floor(i / 3) * 6, 1, 2, "#c9c9c9"); R(f, 65 + (i % 3) * 5, a.teto + 27 + Math.floor(i / 3) * 6, 2, 2, "#e0c070"); }
      relogioParede(f, 95, a.teto + 20);
      R(f, 64, a.pe - 18, 34, 3, "#7a5434"); R(f, 66, a.pe - 15, 2, 17, "#4e3522"); R(f, 94, a.pe - 15, 2, 17, "#4e3522");
      caixa(f, 66, a.pe - 42, 30, 24, "#cfc6ac"); R(f, 67, a.pe - 41, 28, 1, "#e6dfc8"); R(f, 93, a.pe - 40, 2, 21, "#b0a78e");
      R(f, 69, a.pe - 39, 22, 16, "#0a1a10"); R(f, 76, a.pe - 18, 12, 2, "#b0a78e");
      caixa(f, 150, a.pe - 14, 7, 14, "#3a4a5a"); R(f, 151, a.pe - 22, 1, 8, "#c0392b"); R(f, 154, a.pe - 20, 1, 6, "#2f86d0");
      for (const [x] of LUMINARIAS.portaria) luminariaTeto(f, x, a);
      R(g, 109, a.pe - 24, 46, 4, P.tinta); R(g, 110, a.pe - 23, 44, 2, "#7d8b93"); R(g, 111, a.pe - 21, 42, 23, "#46525a"); R(g, 111, a.pe - 21, 42, 1, "#5f6d75");
      R(g, 113, a.pe - 15, 38, 1, "#5f6d75"); R(g, 120, a.pe - 28, 9, 4, "#e9e4d8"); R(g, 121, a.pe - 27, 7, 1, "#9aa0ad");
      R(g, 146, a.pe - 34, 1, 10, "#3a3a44"); caixa(g, 142, a.pe - 38, 9, 5, "#c79a3a"); R(g, 143, a.pe - 34, 7, 1, "#f6e7b0");
      porta(f, 160, a);
      break;
    }
    case "cafe": {
      parede(f, x0, x1, a, P.laranja, "#9a7b54", P.laranjaE);
      for (let x = x0; x < x1; x += 6) R(f, x, a.chao - 30, 1, 27, "rgba(0,0,0,.06)");
      piso(f, x0, x1, a, "xadrez");
      janela(f, "cafe", 290, 40, a.teto + 20, 40);
      // bancada, espresso, moedor, prateleira
      R(f, 168, a.pe - 37, 58, 4, P.tinta); R(f, 169, a.pe - 36, 56, 2, "#7d6550"); R(f, 170, a.pe - 33, 54, 33, "#8a6d52"); R(f, 169, a.pe - 33, 1, 33, P.tinta); R(f, 224, a.pe - 33, 1, 33, P.tinta);
      for (const x of [172, 198]) { caixa(f, x, a.pe - 29, 24, 24, "#7a5f46"); R(f, x + 11, a.pe - 20, 2, 4, "#c9b18f"); }
      caixa(f, 174, a.pe - 56, 22, 19, "#b8bec8"); R(f, 175, a.pe - 55, 20, 2, "#d8dde6"); R(f, 178, a.pe - 50, 7, 5, "#2a2f3a"); R(f, 189, a.pe - 51, 3, 3, "#e74c3c");
      R(f, 179, a.pe - 45, 1, 4, "#5a6070"); R(f, 183, a.pe - 45, 1, 4, "#5a6070"); caneca(f, 179, a.pe - 41);
      caixa(f, 200, a.pe - 52, 8, 15, "#3a3a44"); R(f, 201, a.pe - 51, 6, 5, "#6b4426");
      caneca(f, 211, a.pe - 41, "#e9c46a"); caneca(f, 217, a.pe - 41, "#9fd8ff");
      R(f, 168, a.teto + 36, 58, 2, "#7a5f46"); for (let x = 181; x < 222; x += 8) caixa(f, x, a.teto + 28, 6, 8, ["#e9c46a", "#d04a78", "#2f86d0", "#21a184"][(x / 8 | 0) % 4]);
      planta(f, 168, a.teto + 28);
      // geladeira
      caixa(f, 230, a.pe - 56, 18, 56, "#e8ecef"); R(f, 231, a.pe - 55, 16, 1, "#ffffff"); R(f, 231, a.pe - 36, 16, 1, "#b8bec8");
      R(f, 243, a.pe - 50, 1, 10, "#9aa1ab"); R(f, 243, a.pe - 31, 1, 10, "#9aa1ab");
      R(f, 233, a.pe - 52, 3, 3, "#e74c3c"); R(f, 237, a.pe - 47, 3, 3, "#2f86d0"); R(f, 233, a.pe - 44, 4, 2, "#f2c230");
      // canto do videogame: pôster, estante de cartuchos, rack com a TV de tubo e o console
      caixa(f, 330, a.teto + 18, 26, 36, "#1c1a26"); R(f, 332, a.teto + 20, 22, 32, "#2b1d4f");
      for (let i = 0; i < 6; i++) R(f, 334 + (i % 3) * 7, a.teto + 24 + Math.floor(i / 3) * 6, 4, 3, ["#f2c230", "#e74c3c", "#39ff6a"][i % 3]);
      escreveMini(f, "HI", 337, a.teto + 38, "#f4efe4"); escreveMini(f, "SCORE", 333, a.teto + 44, "#f2c230");
      R(f, 414, a.teto + 30, 18, 2, "#7a5f46"); R(f, 414, a.teto + 46, 18, 2, "#7a5f46");
      for (let k = 0; k < 4; k++) { R(f, 415 + k * 4, a.teto + 22, 3, 8, ["#5b5fc7", "#c0392b", "#2fa36b", "#7d8590"][k]); R(f, 415 + k * 4, a.teto + 38, 3, 8, ["#e9c46a", "#7d8590", "#d04a78", "#2f86d0"][k]); }
      const tv = TV.x;
      caixa(f, tv - 26, a.pe - 26, 52, 26, "#5a4632"); R(f, tv - 24, a.pe - 24, 48, 1, "#7a6248"); R(f, tv - 24, a.pe - 14, 48, 1, "#3e3022");
      caixa(f, tv - 20, a.pe - 13, 16, 6, "#8d939c"); R(f, tv - 18, a.pe - 12, 6, 1, "#3a3f49"); R(f, tv - 8, a.pe - 11, 2, 2, "#e74c3c");     // console
      caixa(f, tv + 2, a.pe - 12, 9, 4, "#3a3f49");                                                                                              // controle extra
      caixa(f, tv - 22, a.pe - 60, 44, 34, "#3b3532"); R(f, tv - 21, a.pe - 59, 42, 2, "#57504c"); R(f, tv + 15, a.pe - 52, 4, 2, "#8d939c"); R(f, tv + 15, a.pe - 48, 4, 2, "#8d939c");
      R(f, tv - 6, a.pe - 66, 1, 6, "#2a2f3a"); R(f, tv + 5, a.pe - 66, 1, 6, "#2a2f3a"); R(f, tv - 8, a.pe - 67, 3, 1, "#2a2f3a"); R(f, tv + 5, a.pe - 67, 3, 1, "#2a2f3a");
      for (const [x] of LUMINARIAS.cafe) luminariaTeto(f, x, a);
      // mesa redonda alta e banquetas; sofá de costas para nós (na frente)
      R(g, 270, a.pe - 31, 50, 4, P.tinta); R(g, 271, a.pe - 30, 48, 2, "#8a6d52"); R(g, 293, a.pe - 27, 4, 26, "#3b3f4b"); R(g, 287, a.pe - 2, 16, 2, "#3b3f4b");
      caneca(g, 278, a.pe - 35); caneca(g, 305, a.pe - 35, "#e9c46a");
      for (const x of [258, 332]) { caixa(g, x - 6, a.pe - 18, 12, 3, "#c0392b"); R(g, x - 1, a.pe - 15, 2, 14, "#3b3f4b"); R(g, x - 4, a.pe - 1, 8, 1, "#3b3f4b"); }
      const sx = SOFA.x;
      caixa(g, sx - 40, a.pe - 26, 80, 22, P.sofa); R(g, sx - 39, a.pe - 25, 78, 2, P.sofaC); R(g, sx - 39, a.pe - 9, 78, 3, P.sofaE);
      R(g, sx - 1, a.pe - 24, 2, 14, P.sofaE);
      caixa(g, sx - 44, a.pe - 20, 8, 18, P.sofaE); caixa(g, sx + 36, a.pe - 20, 8, 18, P.sofaE);
      R(g, sx - 38, a.pe - 4, 3, 4, "#3a2a1e"); R(g, sx + 35, a.pe - 4, 3, 4, "#3a2a1e");
      porta(f, 436, a);
      break;
    }
    case "servidores": {
      parede(f, x0, x1, a, P.srv, "#1a2433", null);
      for (let x = x0 + 16; x < x1; x += 16) R(f, x, a.teto + 3, 1, a.chao - a.teto - 6, "rgba(0,0,0,.12)");
      piso(f, x0, x1, a, "elevado");
      // calha de cabos no teto
      R(f, 442, a.teto + 30, 192, 4, P.acoEE); R(f, 442, a.teto + 30, 192, 1, P.acoE);
      for (let x = 528; x < 620; x += 3) R(f, x, a.teto + 34, 1, 6 + (x % 4) * 2, ["#e74c3c", "#2f86d0", "#e9c46a", "#21a184"][x % 4]);
      // painel de status do CI (o texto entra na camada dinâmica) e o semáforo
      const pc = PAINEL_CI; caixa(f, pc.x, pc.y, pc.w, pc.h, "#0b0f14", "#5a6370"); R(f, pc.x + 30, pc.y + pc.h, 2, 6, "#5a6370"); R(f, pc.x + pc.w - 32, pc.y + pc.h, 2, 6, "#5a6370");
      caixa(f, ANDON.x - 4, ANDON.y - 2, 9, 26, "#1b1f27"); R(f, ANDON.x, ANDON.y + 24, 1, 6, "#5a6370");
      // tubo pneumático vindo de cima, até a caixa de correio
      R(f, TUBO.x - 4, a.teto, 8, 34, "#8d97a3"); R(f, TUBO.x - 3, a.teto, 2, 34, "#c3cbd4");
      caixa(f, TUBO.x - 10, a.teto + 34, 20, 14, "#9aa3ae"); R(f, TUBO.x - 7, a.teto + 38, 14, 6, "#1c2230");
      // racks (os LEDs piscam na camada dinâmica)
      for (const x of [524, 548, 572]) {
        caixa(f, x, a.teto + 44, 22, a.chao - a.teto - 44, P.preto); R(f, x + 1, a.teto + 45, 20, 1, "#3a424d");
        for (let y = a.teto + 48; y < a.chao - 6; y += 7) { R(f, x + 2, y, 18, 5, "#2d343e"); R(f, x + 2, y, 18, 1, "#3a434f"); }
      }
      // unidade de fita (os rolos giram com o CI)
      caixa(f, 598, a.teto + 44, 34, a.chao - a.teto - 44, "#c9cdd2"); R(f, 600, a.teto + 46, 30, 30, "#2a2f3a");
      R(f, 602, a.teto + 80, 26, 3, "#8d939c"); for (let i = 0; i < 4; i++) R(f, 603 + i * 6, a.teto + 88, 4, 2, "#5a6370");
      R(f, 600, a.teto + 96, 30, 1, "#a7adb5");
      // nobreak e extintor
      caixa(f, 444, a.pe - 24, 14, 24, "#2d343e"); R(f, 447, a.pe - 20, 3, 2, "#21a184");
      caixa(f, 462, a.pe - 13, 5, 11, "#c0392b"); R(f, 463, a.pe - 15, 3, 2, P.tinta);
      for (const [x] of LUMINARIAS.servidores) luminariaTeto(f, x, a, true);
      // console de publicação (na frente) com o botão vermelho
      const dx = DEPLOY.x;
      R(g, dx - 24, a.pe - 21, 50, 4, P.tinta); R(g, dx - 23, a.pe - 20, 48, 2, "#7d8590"); R(g, dx - 22, a.pe - 18, 46, 18, "#4a5260"); R(g, dx - 22, a.pe - 18, 46, 1, "#626b7a");
      for (let i = 0; i < 4; i++) R(g, dx - 18 + i * 6, a.pe - 13, 4, 1, "#2d343e");
      R(g, dx - 10, a.pe - 23, 16, 2, P.tinta); R(g, dx - 9, a.pe - 23, 14, 1, "#8a909c");          // teclado
      caixa(g, dx + 12, a.pe - 26, 12, 6, "#e9c46a"); R(g, dx + 13, a.pe - 24, 10, 1, "#1d1d1d");    // base do botão
      R(g, dx - 20, a.pe - 34, 1, 12, "#3a3a44"); caixa(g, dx - 24, a.pe - 37, 9, 4, "#2f3340");
      porta(f, 440, a);
      break;
    }
  }
}

// ------------------------------------------------------------ padrões de luz (pontilhado)
function padrao(ctx, cor, densa = false) {
  const c = novoCanvas(2, 2), x = c.getContext("2d");
  x.fillStyle = cor; x.fillRect(0, 0, 1, 1); x.fillRect(1, 1, 1, 1);
  if (densa) x.fillRect(1, 0, 1, 1);
  return ctx.createPattern(c, "repeat");
}

// Prédios da cidade, vistos pelas janelas (determinísticos).
const CIDADE = Array.from({ length: 70 }, (_, i) => ({ x: (i * 41 + (i % 3) * 7) % 660 - 10, w: 8 + (i * 13) % 14, h: 10 + (i * 29) % 30, j: i }));

// ------------------------------------------------------------ a cena
export class Cena2D {
  constructor(palco) {
    this.palco = palco;
    this.tipo = "2d";
    this.buf = novoCanvas(W, H);
    this.b = this.buf.getContext("2d");
    this.cfg = { sprint: "SPRINT", espec: "", itens: [], sigla: ">CV" };
    this.predio = montaPredio(this.cfg);
    this.tela = novoCanvas(W, H);
    this.tela.className = "cena-tela cena-2d";
    this.tela.setAttribute("aria-hidden", "true");
    palco.prepend(this.tela);
    this.t = this.tela.getContext("2d");
    this.cam = { x: W / 2, y: H / 2, k: 2, modo: "inteiro", alvoX: W / 2, alvoY: H / 2 };
    this.estrelas = Array.from({ length: 70 }, (_, i) => ({ x: (i * 97 + 13) % 640, y: (i * 53 + 7) % 120, f: (i * 31) % 100 }));
    this.pQuente = padrao(this.b, "rgba(255,214,140,.5)");
    this.pFrio = padrao(this.b, "rgba(225,240,255,.5)");
    this.pSol = padrao(this.b, "rgba(255,240,190,.55)");
    this.pAzul = padrao(this.b, "rgba(120,190,255,.55)");
    this.pVerde = padrao(this.b, "rgba(57,255,106,.45)");
    this.pCiano = padrao(this.b, "rgba(95,242,255,.55)", true);
    this.pLanterna = padrao(this.b, "rgba(255,246,200,.7)", true);
    this.pVermelho = padrao(this.b, "rgba(255,80,60,.5)");
    this.pAmbar = padrao(this.b, "rgba(255,190,70,.5)");
  }

  // Dados que mudam o desenho fixo: o nome do sprint, a especificação e a sigla.
  configura(cfg = {}) {
    this.cfg = { ...this.cfg, ...cfg };
    this.predio = montaPredio(this.cfg);
  }

  // Pontos clicáveis da cena além dos personagens (em px da cena).
  alvos() {
    return [
      { id: "quadro", x: QUADRO.x, y: QUADRO.y - 9, w: QUADRO.w, h: QUADRO.h + 9, rotulo: "Quadro de tickets do sprint" },
      { id: "espec", x: ESPEC.x, y: ESPEC.y, w: ESPEC.w, h: ESPEC.h, rotulo: "Quadro branco com a especificação atual" },
      { id: "painel-ci", x: PAINEL_CI.x, y: PAINEL_CI.y, w: PAINEL_CI.w, h: PAINEL_CI.h + 20, rotulo: "Painel do CI" },
      ...MESAS.map(m => ({ id: "mesa:" + m.id, mesa: m.id, x: m.x - 27, y: A1.pe - 40, w: 54, h: 40, rotulo: `Mesa ${m.id.slice(1)}` })),
    ];
  }

  medidas(m) {
    this.cam.modo = m.modo; this.cam.k = m.k; this.dpr = m.dpr;
    this.tela.width = Math.round(m.cssW * m.dpr); this.tela.height = Math.round(m.cssH * m.dpr);
    this.tela.style.width = m.cssW + "px"; this.tela.style.height = m.cssH + "px";
    if (m.modo === "inteiro") { this.cam.x = this.cam.alvoX = W / 2; this.cam.y = this.cam.alvoY = H / 2; }
  }
  segue(x, y, instantaneo = false) {
    if (this.cam.modo === "inteiro" || x == null) return;
    const vw = this.tela.width / this.cam.k, vh = this.tela.height / this.cam.k;
    this.cam.alvoX = Math.max(vw / 2, Math.min(W - vw / 2, x));
    this.cam.alvoY = Math.max(vh / 2, Math.min(H - vh / 2, y));
    if (instantaneo) { this.cam.x = this.cam.alvoX; this.cam.y = this.cam.alvoY; }
  }
  get origem() {
    const k = this.cam.k, vw = this.tela.width / k, vh = this.tela.height / k;
    return { x: Math.round((this.cam.x - vw / 2) * k) / k, y: Math.round((this.cam.y - vh / 2) * k) / k };
  }
  projeta(x, y, alt = 0) {
    const o = this.origem, s = this.cam.k / this.dpr;
    return { x: (x - o.x) * s, y: (y - alt - o.y) * s };
  }
  escala() { return this.cam.k / this.dpr; }
  retSala(id) {
    const r = retSala(id), a = this.projeta(r.x, r.y), s = this.escala();
    return { x: a.x, y: a.y, w: r.w * s, h: r.h * s };
  }
  visao() { const o = this.origem, k = this.cam.k; return { x: o.x, y: o.y, w: this.tela.width / k, h: this.tela.height / k }; }

  // ---------------------------------------------------------- quadro
  desenha(e) {
    const { q, pessoas, t } = e, b = this.b, parado = e.semMovimento;
    const sua = parado ? 1 : Math.min(1, (e.dt || 16) / 220);
    this.cam.x += (this.cam.alvoX - this.cam.x) * sua; this.cam.y += (this.cam.alvoY - this.cam.y) * sua;
    const alto = p => p.alt > .5 && visual(p.id).corpo !== "tubo";

    this.ceu(q.ceu, t, parado);
    b.drawImage(this.predio.fundo, 0, 0);
    for (const j of JANELAS) { b.fillStyle = "rgba(255,255,255,.16)"; for (let i = 0; i < j.h; i++) { const x = j.x + Math.round(j.w * .15) + Math.round((j.h - i) * .5); if (x < j.x + j.w - 2) b.fillRect(x, j.y + i, 3, 1); } }
    this.relogio(e.ms, 298, A1.teto + 18); this.relogio(e.ms, 101, A0.teto + 26); this.relogio(e.ms, 504, A1.teto + 16);
    this.cartoes(q);
    this.tv(q, t, parado);
    this.vapor(q, t, parado, pessoas);
    this.luzesAntes(q, t, pessoas, parado);
    this.pessoas(pessoas.filter(p => !alto(p)), t, parado);
    b.drawImage(this.predio.frente, 0, 0);
    this.mesas(q, pessoas, t, parado);
    this.pessoas(pessoas.filter(alto), t, parado);
    this.escuro(q);
    this.luzesDepois(q, t, pessoas, parado);
    this.placas(q);
    this.blit();
  }

  ceu(c, t, parado) {
    const b = this.b, gr = b.createLinearGradient(0, 0, 0, 300);
    gr.addColorStop(0, rgb(c.alto)); gr.addColorStop(1, rgb(c.horizonte));
    b.fillStyle = gr; b.fillRect(0, 0, W, H);
    if (c.estrelas > .05) for (const s of this.estrelas) {
      const pis = parado ? 1 : (Math.sin(t / 700 + s.f) + 1) / 2;
      b.fillStyle = `rgba(255,255,240,${(.35 + .65 * pis) * c.estrelas})`; b.fillRect(s.x, s.y, 1, 1);
    }
    if (c.sol != null) { const x = Math.round(40 + c.sol * 560), y = Math.round(40 - Math.sin(c.sol * Math.PI) * 34); b.fillStyle = "rgba(255,236,170,.35)"; b.fillRect(x - 6, y - 6, 13, 13); b.fillStyle = "#fff1b8"; b.fillRect(x - 4, y - 4, 9, 9); b.fillRect(x - 5, y - 3, 11, 7); }
    if (c.lua != null) { const x = Math.round(60 + c.lua * 520), y = 10; b.fillStyle = "#f2f0e2"; b.fillRect(x - 3, y - 3, 7, 7); b.fillRect(x - 4, y - 2, 9, 5); b.fillStyle = rgb(c.alto); b.fillRect(x, y - 3, 4, 5); }
    // a cidade, que só aparece pelas janelas
    const dia = c.dia, cor = `rgb(${Math.round(30 + dia * 110)},${Math.round(38 + dia * 118)},${Math.round(62 + dia * 118)})`;
    for (const base of [A1.teto + 56, A0.teto + 62]) {
      for (const p of CIDADE) {
        b.fillStyle = cor; b.fillRect(p.x, base - p.h, p.w, p.h + 4);
        if (dia < .5) for (let y = base - p.h + 2; y < base; y += 3) for (let x = p.x + 1; x < p.x + p.w - 1; x += 3) if (((x * 7 + y * 3 + p.j) % 5) === 0) { b.fillStyle = "rgba(255,214,120,.85)"; b.fillRect(x, y, 1, 1); }
        else if ((p.j % 4) === 0) { b.fillStyle = "rgba(255,255,255,.18)"; b.fillRect(p.x + 1, base - p.h + 1, 1, p.h - 2); }
      }
    }
  }

  relogio(ms, cx, cy) {
    if (ms == null) return;
    const b = this.b, sp = new Date(new Date(ms).toLocaleString("en-US", { timeZone: "America/Sao_Paulo" }));
    const ah = ((sp.getHours() % 12) + sp.getMinutes() / 60) / 12 * Math.PI * 2, am = sp.getMinutes() / 60 * Math.PI * 2;
    b.fillStyle = "#1c1a26";
    for (let i = 0; i <= 3; i++) b.fillRect(Math.round(cx + Math.sin(ah) * i), Math.round(cy - Math.cos(ah) * i), 1, 1);
    for (let i = 0; i <= 5; i++) b.fillRect(Math.round(cx + Math.sin(am) * i), Math.round(cy - Math.cos(am) * i), 1, 1);
    b.fillStyle = "#c0392b"; b.fillRect(cx, cy, 1, 1);
  }

  // Cartões do quadro de tickets, pelo estado de cada ticket no momento.
  cartoes(q) {
    if (!q.tickets) return;
    const b = this.b, Q = QUADRO, cw = Math.floor((Q.w - 4) / 4);
    COLUNAS.forEach(([est, , cor], i) => {
      const lista = Object.values(q.tickets).filter(t => t.estado === est).sort((a, z) => a.id - z.id);
      const cx = Q.x + 2 + i * cw;
      const mostra = lista.length > 5 ? lista.slice(0, 4) : lista;
      mostra.forEach((t, k) => {
        const x = cx + 4 + (k % 2), y = Q.y + 13 + k * 10;
        caixa(b, x, y, cw - 8, 9, cor, "#5a4632"); R(b, x + 1, y + 7, cw - 10, 1, "rgba(0,0,0,.12)");
        escreveMini(b, String(t.id), x + 4, y + 2, "#2a2430");
        R(b, x + cw - 13, y + 1, 2, 2, t.novo ? "#e74c3c" : "#c0392b");
      });
      if (lista.length > 5) escreveMini(b, `+${lista.length - 4}`, cx + 8, Q.y + 55, "#3a2f2a");
    });
  }

  // TV de tubo: desligada, ou com um joguinho de plataforma quando alguém joga.
  tv(q, t, parado) {
    const b = this.b, x = TV.x - 19, y = A0.pe - 56, w = 30, h = 26;
    if (!q.tv) { R(b, x, y, w, h, "#1a1f24"); R(b, x + 3, y + 2, 8, 1, "rgba(255,255,255,.12)"); R(b, x + 2, y + 3, 1, 6, "rgba(255,255,255,.08)"); return; }
    const k = parado ? 0 : t / 1000;
    R(b, x, y, w, h, "#2a5fb8"); R(b, x, y + 18, w, 8, "#3f8a4b"); R(b, x, y + 18, w, 1, "#6cc077");
    for (let i = 0; i < 4; i++) { const cx = Math.round(x + ((i * 11 - k * 9) % 36 + 36) % 36 - 4); R(b, Math.max(x, cx), y + 15, 5, 3, "#2f7a3b"); }
    const px = x + 8, py = y + 13 - Math.round(Math.abs(Math.sin(k * 3)) * 6);
    R(b, px, py, 3, 5, "#e74c3c"); R(b, px, py, 3, 1, "#f2c230");
    if (Math.floor(k * 2) % 2) R(b, x + 20, y + 7, 2, 2, "#f2c230");
    R(b, x + 2, y + 2, 10, 1, "#ffffff"); R(b, x + 3, y + 2, 1, 1, "#f2c230");
    for (let j = 0; j < h; j += 2) R(b, x, y + j, w, 1, "rgba(0,0,0,.18)");
  }

  vapor(q, t, parado, pessoas) {
    if (!pessoas.some(p => p.info && p.info.estado === "cafe")) return;
    const b = this.b;
    for (let i = 0; i < 4; i++) {
      const fase = parado ? i * .25 : ((t / 1400) + i * .25) % 1, y = Math.round(A0.pe - 58 - fase * 22), x = 181 + Math.round(Math.sin(fase * 6 + i) * 2);
      b.fillStyle = `rgba(255,255,255,${(.6 * (1 - fase)).toFixed(2)})`; b.fillRect(x, y, 2, 2);
    }
  }

  pessoas(lista, t, parado) {
    const b = this.b;
    for (const p of lista) {
      const inf = p.info || {}, v = visual(p.id);
      let est = p.andando ? (inf.leva ? "levando" : "andando") : inf.estado || "parado";
      if (!p.andando && inf.leva) est = "levando";
      const seed = p.id.length * 7 + p.id.charCodeAt(0);
      let f = parado && est !== "andando" ? 0 : quadroNoTempo(p.id, est, t, seed);
      if (!p.andando && est === "levando") f = 0;
      const fala = inf.fala && !p.andando && !parado ? Math.floor(t / 170) % 2 === 1 : false;
      const op = p.id === "vigia" && inf.lanterna && p.andando ? { lanternaAlta: true } : {};
      const spr = sprite(p.id, est, est === "cafe" && inf.fala ? (fala ? 1 : 0) : f, est !== "cafe" && est !== "trabalhando" && fala, op);
      const x = Math.round(p.x), y = Math.round(p.y), yv = Math.round(p.y - (p.alt || 0));
      b.globalAlpha = p.opacidade ?? 1;
      const naMesa = v.corpo === "pernas" && p.alt > 10;
      if (v.corpo === "drone") { b.fillStyle = `rgba(10,10,20,${p.alt > 40 ? .12 : .2})`; b.fillRect(x - 8, y, 17, 1); }
      else if (!naMesa && v.corpo !== "tubo") { b.fillStyle = "rgba(10,10,20,.28)"; b.fillRect(x - 10, y, 21, 2); b.fillRect(x - 7, y + 2, 15, 1); }
      if (v.corpo === "rodas" && p.x < 52 && p.andando) {           // plataforma do corrimão na escada
        R(b, x - 12, y, 24, 3, "#e9c46a"); R(b, x - 12, y + 3, 24, 1, "#8a6a1e"); R(b, x + 10, y - 16, 2, 16, "#8d97a3");
      }
      if (p.andando && p.dir < 0) { b.save(); b.translate(x + 20, yv - PE); b.scale(-1, 1); b.drawImage(spr, 0, 0); b.restore(); }
      else b.drawImage(spr, x - 20, yv - PE);
      b.globalAlpha = 1;
    }
  }

  // Mesas do desenvolvimento: quem tem dono ganha monitor; as vagas ficam cobertas.
  mesas(q, pessoas, t, parado) {
    const b = this.b, top = A1.pe - 20;
    for (const m of MESAS) {
      const info = q.mesas ? q.mesas[m.id] : { ocupada: m.id === "m1" };
      const x0 = m.x - 25, w = 50;
      // tampo e gaveteiro
      R(b, x0 - 1, top - 1, w + 2, 5, P.tinta);
      R(b, x0, top, w, 3, P.madeira); R(b, x0, top, w, 1, P.madeiraC);
      caixa(b, x0 + w - 17, top + 3, 15, 18, "#8e9399"); R(b, x0 + w - 16, top + 9, 13, 1, "#6b7077"); R(b, x0 + w - 16, top + 15, 13, 1, "#6b7077");
      R(b, x0 + w - 11, top + 6, 3, 1, "#d9dde3"); R(b, x0 + w - 11, top + 12, 3, 1, "#d9dde3"); R(b, x0 + w - 11, top + 18, 3, 1, "#d9dde3");
      R(b, x0 + 2, top + 3, 2, 18, "#5d6168"); R(b, x0 + 4, top + 3, w - 22, 11, P.madeiraE); R(b, x0 + 4, top + 13, w - 22, 1, "#5e3a21");
      if (!info.ocupada) { this.lencol(b, m, info, top); continue; }
      const dono = info.dono;
      if (dono === "revisor") {                                       // bandeja de papéis do PR e um terminal pequeno
        caixa(b, x0 + 2, top - 5, 14, 5, "#5a6370"); R(b, x0 + 3, top - 7, 12, 3, "#f6f3ea"); R(b, x0 + 4, top - 8, 10, 1, "#e6e1d2");
        caixa(b, x0 + w - 15, top - 13, 13, 13, P.bege); R(b, x0 + w - 13, top - 11, 9, 1, P.begeC); R(b, x0 + w - 14, top - 1, 11, 1, P.begeE);
      } else {                                                        // monitor de tubo, de costas, teclado e coisas da mesa
        caixa(b, x0 + 1, top - 15, 17, 14, P.bege); R(b, x0 + 2, top - 14, 15, 1, P.begeC); R(b, x0 + 4, top - 11, 11, 1, P.begeE); R(b, x0 + 4, top - 8, 11, 1, P.begeE);
        R(b, x0 + 5, top - 1, 9, 1, P.begeE);
        R(b, m.x - 6, top - 2, 14, 2, P.tinta); R(b, m.x - 5, top - 2, 12, 1, "#cfc6ac");
        if (dono === "camps") {
          caneca(b, m.x + 10, top - 4, "#c8423a");
          caixa(b, x0 + w - 13, top - 8, 12, 8, "#cfc6ac"); R(b, x0 + w - 11, top - 11, 8, 3, "#f6f3ea"); R(b, x0 + w - 12, top - 4, 10, 1, "#8a8070");   // impressora matricial
          caixa(b, x0 - 3, top - 5, 6, 5, "#2c3442"); R(b, x0 - 2, top - 5, 4, 1, "#b8c1cc");    // disquetes
        }
      }
    }
  }
  lencol(b, m, info, top) {
    const x0 = m.x - 25, w = 50;
    R(b, x0 - 3, top - 20, 26, 20, P.tinta);
    R(b, x0 - 2, top - 19, 24, 19, P.lencol); R(b, x0 + 14, top - 19, 6, 19, P.lencolE); R(b, x0 + 4, top - 17, 1, 15, P.lencolE);
    R(b, x0 - 4, top - 2, w + 8, 16, P.tinta);
    R(b, x0 - 3, top - 1, w + 6, 14, P.lencol);
    for (const dx of [6, 17, 31, 42]) R(b, x0 + dx, top + 1, 1, 11, P.lencolE);
    for (let i = 0; i < w + 6; i += 2) R(b, x0 - 3 + i, top + 13, 1, 1 + (i % 4 === 0 ? 1 : 0), P.lencolEE);
    R(b, x0 - 3, top - 1, w + 6, 1, "#f7f1e2");
    const txt = info.vaga && info.vaga.para ? "RESERVADA" : "VAGA", tw = medeMini(txt) + 6;
    caixa(b, m.x - Math.round(tw / 2), top + 3, tw, 9, "#fffdf6", "#5a4632");
    escreveMini(b, txt, m.x - Math.round(tw / 2) + 3, top + 5, info.vaga && info.vaga.para ? "#7a2f8a" : "#3a404c");
  }

  // Escuro por sala: noite azul; de dia, sem luz acesa, uma penumbra leve.
  escuro(q) {
    const b = this.b, dia = q.ceu.dia, noite = dia < .3;
    for (const s of SALAS) {
      const modo = q.luz[s.id] || "acesa", r = retSala(s.id);
      let a = 0;
      if (modo === "apagada") a = .8 - dia * .45;
      else if (modo === "penumbra") a = .1 + (1 - dia) * .5;
      else if (modo === "servidor") a = .66;
      else if (modo === "acesa") a = noite ? .3 : (1 - dia) * .2;
      if (s.id === "escada") a = Math.max(a, .12 + (1 - dia) * .55);
      if (a > .01) { b.fillStyle = modo === "servidor" ? `rgba(4,12,34,${a.toFixed(3)})` : `rgba(8,12,38,${a.toFixed(3)})`; b.fillRect(r.x, r.y, r.w, r.h); }
    }
    if (dia < .5) { b.fillStyle = `rgba(8,12,34,${((.5 - dia) * .9).toFixed(3)})`; b.fillRect(0, 328, W, 32); }
  }

  cone(x, yTopo, larguraTopo, yChao, larguraChao, pad, alfa) {
    const b = this.b;
    b.save(); b.globalAlpha = alfa;
    b.beginPath();
    b.moveTo(x - larguraTopo / 2, yTopo); b.lineTo(x + larguraTopo / 2, yTopo);
    b.lineTo(x + larguraChao / 2, yChao); b.lineTo(x - larguraChao / 2, yChao); b.closePath();
    b.fillStyle = pad; b.fill();
    b.restore();
  }
  poca(x, y, w, h, pad, alfa) {
    const b = this.b; b.save(); b.globalAlpha = alfa; b.fillStyle = pad;
    b.fillRect(Math.round(x - w / 2), y, Math.round(w), h); b.fillRect(Math.round(x - w / 2 + 4), y - 1, Math.round(w - 8), 1); b.fillRect(Math.round(x - w / 2 + 4), y + h, Math.round(w - 8), 1);
    b.restore();
  }

  luzesAntes(q, t, pessoas, parado) {
    const b = this.b, dia = q.ceu.dia, noite = dia < .3, A = { 1: A1, 0: A0 };
    if (q.ceu.sol != null && dia > .35) {
      const desvio = Math.round((.5 - q.ceu.sol) * 46);
      for (const j of JANELAS) {
        const a = A[SALA[j.sala].andar], alfa = (dia - .3) * .9;
        b.save(); b.fillStyle = this.pSol;
        b.beginPath(); b.moveTo(j.x, j.y + j.h + 5); b.lineTo(j.x + j.w, j.y + j.h + 5); b.lineTo(j.x + j.w + desvio, a.chao + 2); b.lineTo(j.x + desvio, a.chao + 2); b.closePath();
        b.globalAlpha = alfa * .2; b.fill();
        b.globalAlpha = alfa * .9; b.fillRect(j.x + desvio, a.chao + 3, j.w + 2, 9);
        b.restore();
      }
    }
    const intens = noite ? 1 : .45 + (1 - dia) * .5;
    for (const s of SALAS) {
      if (q.luz[s.id] !== "acesa" || dia > .85) continue;
      const a = A[s.andar]; if (!a) continue;
      const larga = s.id !== "portaria" && s.id !== "cafe";
      for (const [x, w] of LUMINARIAS[s.id] || []) this.cone(x, a.teto + (larga ? 10 : 12), larga ? 22 : 8, a.chao + 8, w, larga ? this.pFrio : this.pQuente, .45 * intens);
    }
    if (dia < .45) {
      const al = noite ? 1 : (.45 - dia) * 4;
      this.cone(26, 46, 6, A1.pe, 30, this.pQuente, .35 * al);
      this.cone(26, 202, 6, A0.pe - 40, 30, this.pQuente, .35 * al);
    }
  }

  luzesDepois(q, t, pessoas, parado) {
    const b = this.b, dia = q.ceu.dia, noite = dia < .3, A = { 1: A1, 0: A0 };
    const intens = noite ? 1 : .45 + (1 - dia) * .5;
    for (const s of SALAS) {
      if (q.luz[s.id] !== "acesa" || dia > .85) continue;
      const a = A[s.andar]; if (!a) continue;
      for (const [x, w] of LUMINARIAS[s.id] || []) this.poca(x, a.chao + 6, w * .85, 5, s.id === "cafe" || s.id === "portaria" ? this.pQuente : this.pFrio, .5 * intens);
    }
    // monitores: o rosto de quem trabalha pega a luz verde do fósforo
    for (const p of pessoas) {
      if (p.andando || !p.info || p.info.estado !== "trabalhando" || visual(p.id).corpo !== "humano" || p.sala !== "dev") continue;
      b.save(); b.globalAlpha = .4; b.fillStyle = this.pVerde; b.fillRect(Math.round(p.x) - 9, Math.round(p.y) - 49, 18, 16); b.restore();
    }
    // TV ligada: luz azul tremendo na frente
    if (q.tv) { b.save(); b.globalAlpha = parado ? .3 : .22 + Math.sin(t / 90) * .08; b.fillStyle = this.pAzul; b.fillRect(TV.x - 30, A0.pe - 62, 60, 44); b.restore(); }
    // servidores: LEDs, rolos de fita, painel do CI, semáforo, botão de publicar
    const ci = q.ci || {}, rodando = ci.estado === "rodando";
    for (const x of [524, 548, 572]) for (let i = 0, y = A0.teto + 49; y < A0.chao - 6; y += 7, i++) {
      const on = parado ? i % 3 !== 1 : Math.sin(t / (rodando ? 60 : 420) + i * 1.7 + x) > -.2;
      R(b, x + 17, y + 2, 2, 1, on ? (i % 5 === 0 ? "#ffb347" : "#45ff7a") : "#1d4a2a");
      if (i % 4 === 2) R(b, x + 14, y + 2, 1, 1, on ? "#7dd3ff" : "#1d3a4a");
    }
    const giro = parado || !rodando ? 0 : t / 300;
    for (const [cx, cy] of [[607, A0.teto + 61], [623, A0.teto + 61]]) {
      R(b, cx - 6, cy - 6, 12, 12, "#2a2f3a"); R(b, cx - 5, cy - 5, 10, 10, "#5a4632"); R(b, cx - 2, cy - 2, 4, 4, "#c9cdd2");
      for (let k = 0; k < 3; k++) { const a = giro + k * 2.1; R(b, Math.round(cx + Math.cos(a) * 3.5), Math.round(cy + Math.sin(a) * 3.5), 1, 1, "#e9edf2"); }
    }
    this.painelCI(q, t, parado);
    const pis = parado ? 1 : Math.floor(t / 400) % 2;
    const luz = { vermelho: ci.estado === "vermelho" && pis, amarelo: rodando && pis, verde: ci.estado === "verde" };
    [["vermelho", "#ff4a3d", "#4a1512"], ["amarelo", "#ffc23d", "#4a3a12"], ["verde", "#45ff7a", "#123a1d"]].forEach(([k, on, off], i) => {
      R(b, ANDON.x - 2, ANDON.y + i * 7, 5, 5, luz[k] ? on : off);
      if (luz[k]) { b.save(); b.globalAlpha = .45; b.fillStyle = k === "verde" ? this.pVerde : k === "amarelo" ? this.pAmbar : this.pVermelho; b.fillRect(ANDON.x - 9, ANDON.y + i * 7 - 6, 19, 17); b.restore(); }
    });
    const aperta = q.deploy && !q.deploy.no_ar;
    R(b, DEPLOY.x + 14, A0.pe - 30, 8, 4, aperta ? "#ff7a6a" : "#c0392b"); R(b, DEPLOY.x + 15, A0.pe - 31, 6, 1, aperta ? "#ffd0c8" : "#e05a4a");
    if (aperta) { b.save(); b.globalAlpha = .6; b.fillStyle = this.pVermelho; b.fillRect(DEPLOY.x + 6, A0.pe - 40, 24, 20); b.restore(); }
    R(b, DEPLOY.x - 23, A0.pe - 33, 7, 1, q.luz.servidores === "acesa" ? "#f6e7b0" : "#3a3a44");
    // CRT da portaria
    const cy = A0.pe - 39;
    b.save(); b.globalAlpha = noite ? .7 : .3; b.fillStyle = this.pVerde; b.fillRect(62, cy - 6, 38, 30); b.restore();
    R(b, 69, cy, 22, 16, "#0b2414"); escreve(b, this.cfg.sigla, 71, cy + 4, "#39ff6a");
    if (parado || Math.floor(t / 530) % 2) R(b, 88, cy + 10, 2, 1, "#39ff6a");
    for (let y = cy; y < cy + 16; y += 2) R(b, 69, y, 22, 1, "rgba(0,0,0,.25)");
    // robôs na recarga: LED âmbar pulsando
    for (const p of pessoas) {
      if (!p.info || p.info.estado !== "carregando") continue;
      const on = parado || Math.floor((t + p.id.length * 300) / 700) % 2;
      const yy = Math.round(p.y - (p.alt || 0)) - 4, xx = Math.round(p.x) + 13;
      R(b, xx, yy - 6, 5, 7, "#1c1a26"); R(b, xx + 1, yy - 5, 3, 5, "#2a2f3a"); R(b, xx + 1, yy - 1 - (on ? 3 : 1), 3, on ? 4 : 2, "#ffc23d"); R(b, xx + 2, yy - 7, 1, 1, "#1c1a26");
    }
    // drone lendo a estante: feixe ciano
    const d = pessoas.find(p => p.info && p.info.scan && !p.andando);
    if (d) {
      const ex = Math.round(d.x), ey = Math.round(d.y - d.alt) - 24, sw = parado ? 0 : Math.sin(t / 400) * 4;
      b.save(); b.globalAlpha = .7; b.fillStyle = this.pCiano;
      b.beginPath(); b.moveTo(ex - 2, ey); b.lineTo(ex + 2, ey); b.lineTo(ex + 14 + sw, A1.chao - 18); b.lineTo(ex - 14 + sw, A1.chao - 18); b.closePath(); b.fill(); b.restore();
    }
    if (dia < .45) {
      const al = noite ? 1 : (.45 - dia) * 4;
      this.cone(146, A0.pe - 33, 6, A0.pe - 24, 22, this.pQuente, .9 * al);
      this.poca(28, A0.pe + 2, 34, 4, this.pQuente, .5 * al);
      const v = pessoas.find(p => p.id === "vigia");
      if (v && v.info && v.info.lanterna && v.andando) {
        const dd = v.dir < 0 ? -1 : 1, hx = Math.round(v.x) + dd * 20, hy = Math.round(v.y) - 23, sw = parado ? 0 : Math.sin(t / 500) * 3;
        b.save(); b.globalAlpha = .85; b.fillStyle = this.pLanterna;
        b.beginPath(); b.moveTo(hx, hy - 1); b.lineTo(hx + dd * 46, hy - 10 + sw); b.lineTo(hx + dd * 46, hy + 20 + sw); b.lineTo(hx, hy + 2); b.closePath(); b.fill();
        b.restore();
        this.poca(hx + dd * 40, Math.round(v.y) - 1, 24, 3, this.pLanterna, .7);
      }
    }
    const neon = .55 + (1 - dia) * .45;
    b.save(); b.globalAlpha = .5 * neon; b.fillStyle = this.pVerde; b.fillRect(240, 0, 62, 16); b.restore();
    const sig = this.cfg.sigla, sw = medeTexto(sig);
    escreve(b, sig, 271 - Math.round((sw + 6) / 2), 4, `rgba(57,255,106,${neon.toFixed(2)})`);
    if (parado || Math.floor(t / 550) % 2) { b.fillStyle = `rgba(57,255,106,${neon.toFixed(2)})`; b.fillRect(271 + Math.round(sw / 2) - 2, 4, 4, 7); }
  }

  painelCI(q, t, parado) {
    const b = this.b, p = PAINEL_CI, ci = q.ci;
    R(b, p.x + 1, p.y + 1, p.w - 2, p.h - 2, "#0b0f14");
    let l1 = "CI", l2 = "SEM EXECUÇÃO HOJE", cor = "#8b97a6";
    if (ci) {
      if (ci.deploy) { l1 = `DEPLOY ${ci.deploy}`; l2 = "NO AR · SAÚDE OK"; cor = "#45ff7a"; }
      else {
        l1 = `CI · PR ${ci.pr}`;
        l2 = ci.estado === "rodando" ? "RODANDO" + ".".repeat(parado ? 3 : 1 + Math.floor(t / 400) % 3) : ci.estado === "verde" ? "VERDE" : "VERMELHO";
        cor = ci.estado === "rodando" ? "#ffc23d" : ci.estado === "verde" ? "#45ff7a" : "#ff5a50";
      }
    }
    escreveMini(b, l1, p.x + 4, p.y + 3, "#c8d0da");
    escreveMini(b, l2, p.x + 4, p.y + 10, cor);
    for (let y = p.y + 1; y < p.y + p.h - 1; y += 2) R(b, p.x + 1, y, p.w - 2, 1, "rgba(0,0,0,.25)");
  }

  placas(q) {
    const b = this.b, escuro = id => q.luz[id] === "apagada" || q.luz[id] === "servidor";
    const p = (txt, cx, y, id, op = {}) => { b.globalAlpha = escuro(id) ? .65 : 1; placa(b, txt, cx, y, op); b.globalAlpha = 1; };
    p("DESENVOLVIMENTO", 104, A1.teto + 3, "dev");
    p("PLANEJAMENTO", 566, A1.teto + 2, "planejamento", { fundo: "#1f3a2c", texto: "#e3f2e6" });
    p("PORTARIA", 90, A0.teto + 6, "portaria");
    p("CAFÉ E JOGOS", 224, A0.teto + 8, "cafe");
    p("SERVIDORES", 474, A0.teto + 10, "servidores", { fundo: "#0d1724", texto: "#9fd8ff" });
  }

  blit() {
    const k = this.cam.k, o = this.origem, t = this.t;
    t.imageSmoothingEnabled = false;
    t.fillStyle = "#0b0e12"; t.fillRect(0, 0, this.tela.width, this.tela.height);
    t.drawImage(this.buf, -Math.round(o.x * k), -Math.round(o.y * k), W * k, H * k);
  }

  desmonta() { this.tela.remove(); }
}
