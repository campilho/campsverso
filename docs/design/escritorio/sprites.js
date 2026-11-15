// A equipe em pixel art, 40 × 56, desenhada em código.
// Humanos (Camps, Vigia) seguem o desenho do estúdio do CampsCast; os robôs
// retrô têm quatro corpos: pernas (aranha com lupa), rodas (monociclo com
// formulário contínuo), drone (quadricóptero com disquete) e tubo (o
// Mensageiro, no tubo pneumático). A aparência vem de equipe.json ("visual"):
// quem chegar com um desses corpos e uma cor já ganha sprite.

export const SW = 40, SH = 56, PE = 53;      // PE: linha dos pés dentro do sprite

const VISUAIS = {};
const PADRAO = {
  humano: { pele: "#d9a37a", cabelo: "#2b1d16", estilo: "curto", calca: "#2d3446", sapato: "#1f2029", acessorio: null, passo: 150 },
  pernas: { passo: 210 },
  rodas:  { passo: 160 },
  drone:  { passo: 180 },
  tubo:   { passo: 220 },
};
export function registraVisuais(equipe) {
  for (const m of equipe) VISUAIS[m.id] = { ...PADRAO[m.visual.corpo] || {}, ...m.visual };
}
export const visual = id => VISUAIS[id] || { corpo: "humano", cor: "#888888", ...PADRAO.humano };

// Estados e número de quadros por corpo. Estado que o corpo não tem cai no "parado".
const QUADROS = {
  humano: { parado: 2, trabalhando: 4, andando: 4, cafe: 3, jogando: 2 },
  pernas: { parado: 2, trabalhando: 4, andando: 4, carregando: 1 },
  rodas:  { parado: 2, trabalhando: 4, andando: 4, levando: 4, carregando: 1 },
  drone:  { parado: 4, trabalhando: 4, andando: 4, carregando: 1 },
  tubo:   { parado: 2, trabalhando: 4, carregando: 1 },
};
export function estadoDo(id, estado) {
  const q = QUADROS[visual(id).corpo] || QUADROS.humano;
  if (q[estado]) return estado;
  if (estado === "levando" && q.andando) return "andando";
  return "parado";
}
export const estadosDo = id => Object.keys(QUADROS[visual(id).corpo] || QUADROS.humano);
export const quadrosDe = (id, estado) => (QUADROS[visual(id).corpo] || QUADROS.humano)[estadoDo(id, estado)] || 1;

const CONTORNO = "#17151f", OLHO = "#1b1b2a", BOCA = "#6b2f2f", BRANCO = "#ffffff";

// ------------------------------------------------------------ cores
const hx = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const rgb = a => "#" + a.map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("");
export const escurece = (h, f) => rgb(hx(h).map(v => v * (1 - f)));
export const clareia = (h, f) => rgb(hx(h).map(v => v + (255 - v) * f));
const mistura = (a, b, t) => rgb(hx(a).map((v, i) => v + (hx(b)[i] - v) * t));

// ------------------------------------------------------------ grade
function grade() { return Array.from({ length: SH }, () => Array(SW).fill(null)); }
function P(g, x, y, c) { if (c && x >= 0 && x < SW && y >= 0 && y < SH) g[y][x] = c; }
function R(g, x, y, w, h, c) { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) P(g, x + i, y + j, c); }
function apaga(g, x, y) { if (x >= 0 && x < SW && y >= 0 && y < SH) g[y][x] = null; }
function L(g, x0, y0, x1, y1, c, grosso = 1) {      // linha com espessura
  const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0), 1);
  for (let i = 0; i <= n; i++) { const x = Math.round(x0 + (x1 - x0) * i / n), y = Math.round(y0 + (y1 - y0) * i / n); R(g, x, y, grosso, grosso, c); }
}
function disco(g, cx, cy, r, c) { for (let y = -r; y <= r; y++) for (let x = -r; x <= r; x++) if (x * x + y * y <= r * r + r * .6) P(g, Math.round(cx + x), Math.round(cy + y), c); }

// ================================================================ humanos
function cabeloTras(g, d, u) {
  const c = escurece(d.cabelo, .18);
  if (d.estilo === "longo") { R(g, 9, 7 + u, 22, 22, c); R(g, 10, 29 + u, 20, 1, c); }
  if (d.estilo === "cacheado") R(g, 9, 6 + u, 22, 10, c);
}
function pernas(g, d, estado, f) {
  const c = d.calca, ce = escurece(c, .3), s = d.sapato, sc = clareia(s, .15), se = escurece(s, .35);
  const perna = (x, y1, sx) => { R(g, x, 41, 6, y1 - 41 + 1, c); R(g, x + 5, 41, 1, y1 - 41 + 1, ce); R(g, sx, y1 + 1, 7, 3, s); R(g, sx + 1, y1 + 1, 3, 1, sc); R(g, sx, y1 + 3, 7, 1, se); };
  if (estado === "andando" && (f === 0 || f === 2)) {
    const esq = f === 0;
    perna(13, esq ? 50 : 47, esq ? 11 : 12);
    perna(21, esq ? 47 : 50, esq ? 21 : 22);
  } else { perna(13, 50, 12); perna(21, 50, 21); }
  R(g, 13, 41, 14, 3, c);
  for (let y = 44; y <= 50; y++) { apaga(g, 19, y); apaga(g, 20, y); }
}
function tronco(g, d, u) {
  const c = d.cor, ce = escurece(c, .22), cc = clareia(c, .22);
  R(g, 12, 23 + u, 16, 18, c);
  R(g, 25, 23 + u, 3, 18, ce); R(g, 12, 24 + u, 1, 16, cc);
  apaga(g, 12, 23 + u); apaga(g, 27, 23 + u);
  if (d.barba) {                                      // camiseta: gola redonda e estampa >_
    R(g, 17, 23 + u, 6, 1, escurece(d.pele, .1)); R(g, 16, 23 + u, 1, 1, cc); R(g, 23, 23 + u, 1, 1, cc);
    const t = "#f4efe4"; P(g, 16, 29 + u, t); P(g, 17, 30 + u, t); P(g, 16, 31 + u, t); R(g, 19, 31 + u, 4, 1, t);
  } else {
    R(g, 18, 23 + u, 4, 1, d.pele); R(g, 19, 24 + u, 2, 1, escurece(d.pele, .1)); P(g, 17, 23 + u, cc); P(g, 22, 23 + u, cc);
    P(g, 19, 28 + u, ce); P(g, 19, 32 + u, ce);
  }
  R(g, 12, 40 + u, 16, 1, escurece(d.calca, .25));
}
function braco(g, d, lado, pose, u, f = 0) {
  const c = d.cor, ce = escurece(c, .3), pe = d.pele, pee = escurece(d.pele, .18);
  const x = lado < 0 ? 8 : 28, borda = lado < 0 ? x : x + 3;
  const manga = d.barba ? 6 : 13;                     // camiseta: manga curta, antebraço de pele
  switch (pose) {
    case "baixo": case "frente": case "tras": {
      const dy = pose === "frente" ? -1 : 0, dx = pose === "frente" ? -lado : pose === "tras" ? lado : 0;
      R(g, x + dx, 24 + u + dy, 4, 13, pe); R(g, borda + dx, 24 + u + dy, 1, 13, pee);
      R(g, x + dx, 24 + u + dy, 4, manga, c); R(g, borda + dx, 24 + u + dy, 1, manga, ce);
      R(g, x + dx, 37 + u + dy, 4, 3, pe); P(g, borda + dx, 39 + u + dy, pee);
      break;
    }
    case "teclado": {
      const up = f ? -1 : 0;
      R(g, x, 24 + u, 4, 7, d.barba ? pe : c); R(g, x, 24 + u, 4, Math.min(manga, 7), c); R(g, borda, 24 + u, 1, 7, ce);
      const fx = lado < 0 ? 11 : 22;
      R(g, fx, 31 + u + up, 7, 3, d.barba ? pe : c); R(g, fx, 33 + u + up, 7, 1, d.barba ? pee : ce);
      R(g, lado < 0 ? 17 : 20, 31 + u + up, 3, 3, pe);
      break;
    }
    case "peito": {
      const up = f ? -1 : 0;
      R(g, x, 24 + u, 4, 6, d.barba ? pe : c); R(g, x, 24 + u, 4, Math.min(manga, 6), c); R(g, borda, 24 + u, 1, 6, ce);
      const fx = lado < 0 ? 11 : 22;
      R(g, fx, 30 + u + up, 7, 3, d.barba ? pe : c); R(g, fx, 32 + u + up, 7, 1, d.barba ? pee : ce);
      R(g, lado < 0 ? 16 : 21, 29 + u + up, 3, 4, pe);
      break;
    }
    case "alto": {
      R(g, x, 21 + u, 4, 9, d.barba ? pe : c); R(g, x, 25 + u, 4, 5, c); R(g, borda, 21 + u, 1, 9, ce);
      R(g, lado < 0 ? x + 1 : x - 1, 17 + u, 4, 4, pe);
      break;
    }
    case "estendido": {
      R(g, x, 24 + u, 4, 6, c); R(g, borda, 24 + u, 1, 6, ce);
      R(g, lado < 0 ? 5 : 31, 30 + u, 5, 3, c);
      R(g, lado < 0 ? 3 : 34, 30 + u, 3, 3, pe);
      break;
    }
  }
}
function cabeca(g, d, u, { olhos = "abertos", boca = "fechada", vira = 0 } = {}) {
  const pe = d.pele, pee = escurece(d.pele, .16), pec = clareia(d.pele, .14);
  R(g, 17, 21 + u, 6, 2, pee);
  R(g, 11, 4 + u, 18, 17, pe);
  R(g, 27, 6 + u, 2, 13, pee); R(g, 12, 20 + u, 16, 1, pee);
  R(g, 12, 6 + u, 1, 6, pec);
  for (const [x, y] of [[11, 4], [12, 4], [11, 5], [27, 4], [28, 4], [28, 5], [11, 20], [28, 20], [11, 19], [28, 19]]) apaga(g, x, y + u);
  R(g, 10, 11 + u, 1, 4, pe); R(g, 29, 11 + u, 1, 4, pee); P(g, 10, 12 + u, pee);
  const v = vira;
  const sb = escurece(d.cabelo, .1);
  R(g, 14 + v, 10 + u, 4, 1, sb); R(g, 22 + v, 10 + u, 4, 1, sb);
  if (olhos === "fechados") { R(g, 14 + v, 14 + u, 3, 1, OLHO); R(g, 22 + v, 14 + u, 3, 1, OLHO); }
  else { R(g, 15 + v, 12 + u, 2, 3, OLHO); R(g, 23 + v, 12 + u, 2, 3, OLHO); P(g, 15 + v, 12 + u, BRANCO); P(g, 23 + v, 12 + u, BRANCO); }
  R(g, 19 + v, 15 + u, 2, 2, pee);
  const bochecha = mistura(pe, "#e0636b", .3);
  R(g, 13 + v, 16 + u, 2, 1, bochecha); R(g, 25 + v, 16 + u, 2, 1, bochecha);
  if (d.barba) { barba(g, d, u, boca); return; }
  if (boca === "aberta") { R(g, 18 + v, 18 + u, 4, 2, BOCA); R(g, 19 + v, 19 + u, 2, 1, "#c45a5a"); }
  else if (boca === "meia") R(g, 18 + v, 18 + u, 4, 1, BOCA);
  else if (boca === "sorriso") { P(g, 17 + v, 17 + u, BOCA); R(g, 18 + v, 18 + u, 4, 1, BOCA); P(g, 22 + v, 17 + u, BOCA); }
  else R(g, 18 + v, 18 + u, 4, 1, mistura(pe, BOCA, .6));
}
function barba(g, d, u, boca) {          // barba cheia do Camps
  const b = d.barba, bc = clareia(b, .18), be = escurece(b, .25);
  R(g, 11, 12 + u, 2, 8, b); R(g, 27, 12 + u, 2, 8, b);         // costeletas
  R(g, 12, 17 + u, 16, 4, b); R(g, 13, 21 + u, 14, 1, b); R(g, 15, 22 + u, 10, 1, b); R(g, 17, 23 + u, 6, 1, be);
  R(g, 14, 16 + u, 4, 1, b); R(g, 22, 16 + u, 4, 1, b); R(g, 16, 17 + u, 8, 1, be);   // bigode
  P(g, 13, 19 + u, bc); P(g, 25, 18 + u, bc); P(g, 20, 21 + u, bc); P(g, 16, 20 + u, bc);
  if (boca === "aberta") { R(g, 18, 18 + u, 4, 2, "#3a1212"); R(g, 19, 19 + u, 2, 1, "#a8484a"); }
  else if (boca === "sorriso") { R(g, 17, 18 + u, 6, 1, "#3a1d14"); P(g, 18, 19 + u, "#f4efe4"); P(g, 21, 19 + u, "#f4efe4"); }
  else R(g, 18, 18 + u, 4, 1, "#3a1d14");
}
function cabeloFrente(g, d, u) {
  const c = d.cabelo, cc = clareia(c, .25), ce = escurece(c, .2);
  const topo = () => { R(g, 14, 2 + u, 12, 1, c); R(g, 12, 3 + u, 16, 1, c); R(g, 11, 4 + u, 18, 3, c); R(g, 15, 3 + u, 4, 1, cc); R(g, 13, 4 + u, 3, 1, cc); };
  switch (d.estilo) {
    case "curto": topo(); R(g, 11, 7 + u, 3, 4, c); R(g, 26, 7 + u, 3, 4, c); R(g, 14, 7 + u, 5, 1, c); R(g, 24, 5 + u, 4, 2, ce); break;
    case "raspado": R(g, 13, 3 + u, 14, 1, c); R(g, 11, 4 + u, 18, 2, c); R(g, 11, 6 + u, 1, 4, c); R(g, 28, 6 + u, 1, 4, c); break;
    case "bagunca":                                   // despenteado, com tufos
      topo(); R(g, 11, 7 + u, 3, 4, c); R(g, 26, 7 + u, 3, 4, c); R(g, 14, 7 + u, 8, 1, c); R(g, 15, 8 + u, 3, 1, c); R(g, 22, 7 + u, 2, 1, ce);
      R(g, 17, 0 + u, 3, 2, c); P(g, 13, 1 + u, c); P(g, 22, 1 + u, c); R(g, 23, 1 + u, 2, 1, c); P(g, 10, 4 + u, c); P(g, 29, 5 + u, c); P(g, 26, 2 + u, c);
      P(g, 18, 0 + u, cc); P(g, 16, 3 + u, cc); P(g, 21, 3 + u, cc); P(g, 24, 4 + u, cc); P(g, 12, 5 + u, cc); R(g, 25, 5 + u, 3, 1, ce);
      break;
    case "longo": topo(); R(g, 10, 7 + u, 3, 16, c); R(g, 27, 7 + u, 3, 16, c); R(g, 13, 7 + u, 6, 1, c); break;
    default: topo();
  }
}
function bone(g, d, estado, u) {                  // boné e lanterna do Vigia
  const k = "#2b3545", kc = "#3d4a5e";
  R(g, 13, 1 + u, 14, 1, k); R(g, 11, 2 + u, 18, 5, k); R(g, 14, 2 + u, 6, 1, kc); R(g, 11, 7 + u, 22, 2, escurece(k, .25)); R(g, 29, 7 + u, 4, 1, kc);
  R(g, 18, 3 + u, 4, 3, "#e9c46a"); P(g, 19, 4 + u, "#b38b2a");
  if (estado === "cafe") return;
  if (estado === "andando" || d.lanternaAlta) { R(g, 34, 29 + u, 5, 3, "#8a929e"); R(g, 34, 29 + u, 5, 1, "#a8b0bc"); R(g, 39, 29 + u, 1, 3, "#fff2b0"); }
  else { R(g, 29, 37 + u, 3, 6, "#8a929e"); R(g, 29, 37 + u, 1, 6, "#5c636e"); R(g, 29, 43 + u, 3, 1, "#fff2b0"); }
}
// De costas, no sofá, jogando videogame. O sofá (na frente) cobre da cintura para baixo.
function costas(g, d, f) {
  const u = f ? 1 : 0, c = d.cor, ce = escurece(c, .22), pe = d.pele, pee = escurece(pe, .18), h = d.cabelo, hc = clareia(h, .22), he = escurece(h, .2);
  R(g, 12, 24 + u, 16, 20, c); R(g, 25, 24 + u, 3, 20, ce); R(g, 18, 26 + u, 2, 16, ce);
  apaga(g, 12, 24 + u); apaga(g, 27, 24 + u);
  R(g, 8, 26 + u, 5, 7, c); R(g, 27, 26 + u, 5, 7, c);                 // ombros e braços para a frente
  R(g, 8, 33 + u, 4, 3, pee); R(g, 28, 33 + u, 4, 3, pee);
  R(g, 17, 21 + u, 6, 3, pee);
  R(g, 11, 4 + u, 18, 17, h); R(g, 12, 3 + u, 16, 1, h); R(g, 14, 2 + u, 12, 1, h);
  for (const [x, y] of [[11, 4], [28, 4], [11, 20], [28, 20]]) apaga(g, x, y + u);
  R(g, 10, 11 + u, 1, 4, pe); R(g, 29, 11 + u, 1, 4, pee);
  if (d.barba) { R(g, 11, 15 + u, 1, 5, d.barba); R(g, 28, 15 + u, 1, 5, d.barba); }
  R(g, 17, 0 + u, 3, 2, h); P(g, 13, 1 + u, h); P(g, 23, 1 + u, h); P(g, 26, 2 + u, h);
  P(g, 18, 0 + u, hc); P(g, 15, 5 + u, hc); P(g, 22, 6 + u, hc); P(g, 19, 10 + u, hc); R(g, 13, 12 + u, 3, 1, he); R(g, 24, 9 + u, 3, 1, he); R(g, 17, 16 + u, 5, 1, he);
}

function montaHumano(d, estado, f, abre) {
  const g = grade();
  if (estado === "jogando") { costas(g, d, f); return g; }
  const andando = estado === "andando";
  const u = (estado === "parado" && f === 1) || (andando && (f === 1 || f === 3)) ? 1 : 0;
  cabeloTras(g, d, u);
  pernas(g, d, estado, f);
  tronco(g, d, u);
  let esq = "baixo", dir = "baixo";
  if (andando) { esq = f === 0 ? "frente" : f === 2 ? "tras" : "baixo"; dir = f === 0 ? "tras" : f === 2 ? "frente" : "baixo"; }
  if (estado === "trabalhando") { esq = "teclado"; dir = "teclado"; }
  if (d.acessorio === "bone" && (andando || d.lanternaAlta) && estado !== "cafe") dir = "estendido";
  if (estado === "cafe") dir = f === 2 ? "alto" : "peito";
  braco(g, d, -1, esq, u, estado === "trabalhando" ? f % 2 : 0);
  braco(g, d, 1, dir, u, estado === "trabalhando" ? (f + 1) % 2 : 0);
  const piscando = estado === "parado" && f === 1;
  let boca = "fechada";
  if (abre) boca = "aberta"; else if (estado === "cafe") boca = f === 1 ? "aberta" : "sorriso";
  cabeca(g, d, u, { olhos: piscando ? "fechados" : "abertos", boca });
  cabeloFrente(g, d, u);
  if (d.acessorio === "bone") bone(g, d, estado, u);
  if (estado === "cafe") {
    if (f === 2) { R(g, 22, 17 + u, 5, 6, "#f4f1ea"); R(g, 27, 18 + u, 1, 3, "#f4f1ea"); R(g, 22, 17 + u, 5, 1, "#6b4426"); }
    else {
      R(g, 17, 28 + u, 5, 6, "#f4f1ea"); R(g, 16, 29 + u, 1, 3, "#f4f1ea"); R(g, 17, 28 + u, 5, 1, "#6b4426"); R(g, 18, 31 + u, 3, 1, d.cor);
      P(g, 18, 26 + u - (f ? 1 : 0), "#d8dde6"); P(g, 20, 25 + u, "#d8dde6"); P(g, 19, 24 + u - (f ? 1 : 0), "#d8dde6");
    }
  }
  return g;
}

// ================================================================ robôs
const MET = { corpo: "#dde1e7", sombra: "#a7afba", escuro: "#4f5866", junta: "#3b424d", visor: "#1b2230", olho: "#6ff4ff", olhoApagado: "#1f4b55", magenta: "#d6409f" };

// Revisor: aranha de quatro pernas, com lupa.
function montaPernas(d, estado, f) {
  const g = grade(), c = d.cor, carrega = estado === "carregando", anda = estado === "andando", trab = estado === "trabalhando";
  const u = carrega ? 4 : anda ? (f % 2) : (estado === "parado" && f === 1 ? 1 : 0);
  const y0 = 29 + u;
  // pernas (atrás do corpo)
  const pe = MET.escuro, pc = "#7f8896";
  const sobe = (k) => (anda && ((f === 0 && (k === 0 || k === 3)) || (f === 2 && (k === 1 || k === 2))) ? 2 : 0);
  const pernasDef = carrega
    ? [[10, y0 + 7, 3, y0 + 5, 1], [12, y0 + 10, 7, y0 + 9, 6], [29, y0 + 7, 36, y0 + 5, 38], [27, y0 + 10, 32, y0 + 9, 33]]
    : [[10, y0 + 7, 4, y0 + 2, 2], [12, y0 + 10, 8, y0 + 7, 8], [29, y0 + 7, 35, y0 + 2, 37], [27, y0 + 10, 31, y0 + 7, 31]];
  pernasDef.forEach(([hx_, hy, kx, ky, fx], k) => {
    const s = sobe(k), fy = 52 - s;
    L(g, hx_, hy, kx, ky - s, pc, 2); L(g, kx, ky - s, fx, fy, pc, 2);
    R(g, kx, ky - s, 2, 2, pe); R(g, fx - 1, fy + 0, 3, 2, MET.junta);
  });
  // corpo em cúpula
  R(g, 13, y0, 14, 1, MET.corpo); R(g, 11, y0 + 1, 18, 1, MET.corpo); R(g, 10, y0 + 2, 20, 9, MET.corpo); R(g, 11, y0 + 11, 18, 1, MET.corpo); R(g, 13, y0 + 12, 14, 1, MET.sombra);
  R(g, 25, y0 + 2, 5, 9, MET.sombra); R(g, 12, y0 + 2, 2, 3, "#f4f6f9");
  R(g, 10, y0 + 8, 20, 2, c); R(g, 10, y0 + 9, 20, 1, escurece(c, .25));
  // visor e olhos
  R(g, 13, y0 + 3, 14, 4, MET.visor);
  const olho = carrega ? MET.olhoApagado : MET.olho, pisca = estado === "parado" && f === 1;
  const ox = trab ? [0, -1, -2, -1][f] : 0;
  if (pisca) { R(g, 15 + ox, y0 + 5, 3, 1, olho); R(g, 22 + ox, y0 + 5, 3, 1, olho); }
  else { R(g, 15 + ox, y0 + 4, 3, 2, olho); R(g, 22 + ox, y0 + 4, 3, 2, olho); if (!carrega) { P(g, 15 + ox, y0 + 4, BRANCO); P(g, 22 + ox, y0 + 4, BRANCO); } }
  // antena
  R(g, 20, y0 - 4, 1, 4, MET.escuro); R(g, 19, y0 - 6, 3, 2, carrega ? escurece(c, .4) : c);
  // braço e lupa
  const mx = trab ? [0, -4, -8, -4][f] : 0, my = trab ? [0, 1, 0, 1][f] : carrega ? 6 : 2;
  const hx2 = 31 + mx, hy2 = y0 - 1 + my;
  L(g, 28, y0 + 5, hx2, hy2 + 2, MET.escuro, 2);
  const cx = hx2 + 2, cy = hy2 - 4;
  disco(g, cx, cy, 4, "#c9a43a"); disco(g, cx, cy, 3, "#cfeeff"); P(g, cx - 1, cy - 1, BRANCO); P(g, cx - 2, cy - 1, BRANCO); P(g, cx - 1, cy - 2, BRANCO);
  R(g, hx2, hy2, 2, 3, "#7a4a2a");
  return g;
}

// Integrador: monociclo com tela de LEDs, leva o formulário contínuo.
function montaRodas(d, estado, f) {
  const g = grade(), c = d.cor, carrega = estado === "carregando", leva = estado === "levando", anda = estado === "andando" || leva, trab = estado === "trabalhando";
  const u = anda ? (f % 2) : 0;
  // roda
  const cx = 20, cy = 46;
  disco(g, cx, cy, 7, "#262a33"); disco(g, cx, cy, 4, "#7a8390"); disco(g, cx, cy, 1, MET.corpo);
  const ang = (anda ? f : 0) * Math.PI / 4;
  for (const a of [ang, ang + Math.PI / 2]) L(g, Math.round(cx - Math.cos(a) * 4), Math.round(cy - Math.sin(a) * 4), Math.round(cx + Math.cos(a) * 4), Math.round(cy + Math.sin(a) * 4), "#3a404b");
  P(g, cx, cy, MET.corpo); R(g, 14, 52, 13, 1, "#1a1d24");
  // garfo
  R(g, 14, 35 + u, 2, 11 - u, MET.escuro); R(g, 24, 35 + u, 2, 11 - u, MET.escuro); R(g, 14, 45, 12, 2, MET.junta);
  // corpo
  const y = 15 + u;
  R(g, 11, y, 18, 1, MET.corpo); R(g, 10, y + 1, 20, 20, MET.corpo); R(g, 11, y + 21, 18, 1, MET.sombra);
  R(g, 26, y + 1, 4, 20, MET.sombra); R(g, 11, y + 1, 13, 1, "#f4f6f9");
  R(g, 10, y + 16, 20, 2, c); R(g, 10, y + 17, 20, 1, escurece(c, .25));
  for (let i = 0; i < 3; i++) R(g, 13 + i * 3, y + 19, 2, 1, MET.escuro);
  // tela com LEDs (o rosto)
  R(g, 12, y + 4, 16, 8, MET.escuro); R(g, 13, y + 5, 14, 6, "#0c1a12");
  const verde = carrega ? "#16351f" : clareia(c, .35), vermelho = carrega ? "#3a1416" : "#ff5a50";
  for (let i = 0; i < 4; i++) {
    const aceso = carrega ? false : trab ? i === f : !(estado === "parado" && f === 1 && i === 3);
    R(g, 14 + i * 3, y + 7, 2, 2, aceso ? verde : escurece(c, .55));
  }
  R(g, 14 + 12, y + 7, 1, 2, carrega ? vermelho : (trab && f % 2) || estado === "parado" ? vermelho : "#5a1e1e");
  // tampa e farol
  R(g, 13, y - 3, 14, 3, MET.sombra); R(g, 13, y - 3, 14, 1, MET.corpo);
  R(g, 19, y - 6, 3, 3, carrega ? "#1f4b55" : trab && f % 2 ? "#ffffff" : "#7dd3ff");
  R(g, 8, y + 6, 2, 4, d.cor2 || MET.magenta); R(g, 30, y + 6, 2, 4, d.cor2 || MET.magenta);   // orelhas
  // braços
  if (leva) {
    const py = 27 + u;
    R(g, 7, py, 26, 12, "#f6f3ea");
    for (let j = 0; j < 12; j += 2) R(g, 9, py + j, 22, 1, j % 4 ? "#d7ecd6" : "#f6f3ea");
    for (let j = 1; j < 12; j += 2) { P(g, 8, py + j, "#b9bec6"); P(g, 31, py + j, "#b9bec6"); }
    R(g, 7, py + 11, 26, 1, "#d9d4c4"); R(g, 9, py - 2, 22, 2, "#f6f3ea"); R(g, 9, py - 2, 22, 1, "#e6e1d2");
    R(g, 4, py + 3, 4, 3, MET.escuro); R(g, 32, py + 3, 4, 3, MET.escuro);
  } else {
    const ay = y + 10 + (trab ? [0, 1, 0, -1][f] : 0);
    R(g, 6, ay, 4, 3, MET.escuro); R(g, 6, ay + 3, 3, 6, MET.sombra); R(g, 5, ay + 9, 4, 2, MET.junta);
    R(g, 30, ay, 4, 3, MET.escuro); R(g, 31, ay + 3, 3, 6, MET.sombra); R(g, 31, ay + 9, 4, 2, MET.junta);
  }
  return g;
}

// Pesquisador: quadricóptero com um disquete preso na garra.
function montaDrone(d, estado, f) {
  const g = grade(), c = d.cor, carrega = estado === "carregando", trab = estado === "trabalhando";
  const oy = carrega ? 12 : 0, u = carrega ? 0 : (f >> 1) % 2;
  const y = 22 + oy + u;
  // braços e rotores
  R(g, 5, y + 5, 30, 2, MET.escuro);
  R(g, 3, y + 3, 5, 3, MET.junta); R(g, 32, y + 3, 5, 3, MET.junta);
  R(g, 1, y + 6, 10, 1, "#8d96a3"); R(g, 29, y + 6, 10, 1, "#8d96a3");        // aro de proteção
  const pa = "#eef1f5";
  if (carrega) { R(g, 0, y + 2, 11, 1, "#9aa3af"); R(g, 29, y + 2, 11, 1, "#9aa3af"); }
  else if (f % 2 === 0) { R(g, 0, y + 2, 11, 1, pa); R(g, 29, y + 2, 11, 1, pa); }
  else { R(g, 3, y + 2, 5, 1, pa); R(g, 32, y + 2, 5, 1, pa); P(g, 0, y + 2, "#c3cad3"); P(g, 10, y + 2, "#c3cad3"); P(g, 29, y + 2, "#c3cad3"); P(g, 39, y + 2, "#c3cad3"); }
  // corpo
  R(g, 15, y + 3, 10, 1, MET.corpo); R(g, 14, y + 4, 12, 1, MET.corpo); R(g, 13, y + 5, 14, 7, MET.corpo); R(g, 14, y + 12, 12, 1, MET.sombra);
  R(g, 23, y + 5, 4, 7, MET.sombra); R(g, 14, y + 5, 2, 2, "#f4f6f9");
  R(g, 13, y + 10, 14, 1, c);
  R(g, 19, y + 2, 2, 1, carrega ? "#5a2846" : MET.magenta);
  R(g, 15, y + 6, 10, 3, MET.visor);
  const olho = carrega ? MET.olhoApagado : trab ? "#ffffff" : MET.olho;
  const pisca = estado === "parado" && f === 1 && false;
  if (!pisca) { R(g, 16, y + 7, 2, 1, olho); R(g, 22, y + 7, 2, 1, olho); }
  if (carrega) { R(g, 12, 52, 16, 1, MET.escuro); R(g, 14, y + 13, 1, 52 - (y + 13), MET.escuro); R(g, 25, y + 13, 1, 52 - (y + 13), MET.escuro); return g; }
  // garra e disquete
  R(g, 19, y + 13, 2, 4, MET.escuro); R(g, 16, y + 17, 8, 1, MET.escuro); R(g, 16, y + 18, 1, 2, MET.escuro); R(g, 23, y + 18, 1, 2, MET.escuro);
  const fy = y + 19;
  R(g, 14, fy, 12, Math.min(12, 53 - fy), "#2c3442"); R(g, 16, fy, 7, 4, "#b8c1cc"); R(g, 20, fy + 1, 2, 2, "#2c3442");
  R(g, 15, fy + 5, 10, Math.min(6, 52 - fy - 5), "#f3efe2"); R(g, 16, fy + 7, 8, 1, "#c0392b"); R(g, 16, fy + 9, 6, 1, "#9aa1ab");
  return g;
}

// Mensageiro: cabeça redonda que sai do tubo pneumático com um envelope.
function montaTubo(d, estado, f) {
  const g = grade(), c = d.cor, trab = estado === "trabalhando", carrega = estado === "carregando";
  const u = trab ? [0, -1, 0, -1][f] : 9;
  const y = 34 + u;
  R(g, 15, y - 4, 1, 4, MET.escuro); R(g, 14, y - 6, 3, 2, carrega ? escurece(c, .45) : c);
  R(g, 15, y, 10, 1, MET.corpo); R(g, 13, y + 1, 14, 1, MET.corpo); R(g, 12, y + 2, 16, 9, MET.corpo); R(g, 13, y + 11, 14, 1, MET.sombra); R(g, 15, y + 12, 10, 1, MET.sombra);
  R(g, 24, y + 2, 4, 9, MET.sombra); R(g, 13, y + 2, 2, 3, "#ffffff");
  R(g, 10, y + 4, 2, 5, c); R(g, 28, y + 4, 2, 5, c); R(g, 9, y + 5, 1, 3, escurece(c, .3)); R(g, 30, y + 5, 1, 3, escurece(c, .3));
  R(g, 14, y + 4, 12, 4, MET.visor);
  const olho = carrega ? MET.olhoApagado : MET.olho;
  if (trab && f % 2) { P(g, 16, y + 6, olho); P(g, 17, y + 5, olho); P(g, 18, y + 6, olho); P(g, 22, y + 6, olho); P(g, 23, y + 5, olho); P(g, 24, y + 6, olho); }
  else if (estado === "parado" && f === 1) { R(g, 16, y + 6, 3, 1, olho); R(g, 22, y + 6, 3, 1, olho); }
  else { R(g, 16, y + 5, 3, 2, olho); R(g, 22, y + 5, 3, 2, olho); }
  R(g, 14, y + 13, 12, 53 - y - 13, MET.sombra); R(g, 14, y + 13, 12, 1, MET.escuro);
  if (trab) {                                                  // envelope erguido
    const ey = y - 2 + (f % 2), ex = 27;
    R(g, 26, y + 8, 3, 2, MET.escuro); R(g, 28, ey + 7, 2, 3, MET.escuro);
    R(g, ex, ey, 12, 8, "#f6e7a8"); L(g, ex, ey, ex + 5, ey + 4, "#c9a85a"); L(g, ex + 11, ey, ex + 6, ey + 4, "#c9a85a");
    R(g, ex + 5, ey + 4, 2, 2, "#d0392b");
  }
  return g;
}

// ------------------------------------------------------------ montagem e cache
function contorna(g, cor) {
  const out = g.map(r => r.slice());
  for (let y = 0; y < SH; y++) for (let x = 0; x < SW; x++) {
    if (g[y][x]) continue;
    const viz = (g[y - 1] && g[y - 1][x]) || (g[y + 1] && g[y + 1][x]) || g[y][x - 1] || g[y][x + 1];
    if (viz) out[y][x] = cor;
  }
  return out;
}

const cache = new Map();
// op.lanternaAlta: Vigia de ronda, com a lanterna para a frente.
export function sprite(id, estado = "parado", f = 0, abre = false, op = {}) {
  estado = estadoDo(id, estado);
  const n = quadrosDe(id, estado);
  f = ((f % n) + n) % n;
  const k = `${id}|${estado}|${f}|${abre ? 1 : 0}|${op.lanternaAlta ? 1 : 0}`;
  if (cache.has(k)) return cache.get(k);
  const d = { ...visual(id), ...op };
  const g0 = d.corpo === "pernas" ? montaPernas(d, estado, f)
    : d.corpo === "rodas" ? montaRodas(d, estado, f)
    : d.corpo === "drone" ? montaDrone(d, estado, f)
    : d.corpo === "tubo" ? montaTubo(d, estado, f)
    : montaHumano(d, estado, f, abre);
  const g = contorna(g0, CONTORNO);
  const cv = typeof OffscreenCanvas !== "undefined" ? new OffscreenCanvas(SW, SH) : Object.assign(document.createElement("canvas"), { width: SW, height: SH });
  const ctx = cv.getContext("2d");
  for (let y = 0; y < SH; y++) for (let x = 0; x < SW; x++) if (g[y][x]) { ctx.fillStyle = g[y][x]; ctx.fillRect(x, y, 1, 1); }
  cache.set(k, cv);
  return cv;
}

// Quadro da animação a partir do tempo (ms) — cada um tem seu ritmo.
export function quadroNoTempo(id, estado, t, semente = 0) {
  const v = visual(id);
  estado = estadoDo(id, estado);
  if (estado === "carregando") return 0;
  if (v.corpo === "drone" && estado !== "trabalhando") return Math.floor(t / 60) % 2 + (Math.floor((t + semente * 97) / 700) % 2) * 2;   // hélice + flutuação
  if (estado === "andando" || estado === "levando") return Math.floor(t / (v.corpo === "rodas" ? 100 : v.corpo === "pernas" ? 120 : 140)) % 4;
  if (estado === "trabalhando") return Math.floor((t + semente * 97) / (v.passo || 200)) % 4;
  if (estado === "cafe") { const c = Math.floor((t + semente * 331) / 900) % 6; return c === 5 ? 2 : 0; }
  if (estado === "jogando") return Math.floor((t + semente * 51) / 380) % 2;
  if (estado === "parado") return ((t + semente * 613) % 3400) < 160 ? 1 : 0;
  return 0;
}
