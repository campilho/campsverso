// Fonte de pixel 5×7 para as placas da cena (maiúsculas, números e acentos
// do português). Desenhada em código, sem arquivo de fonte.

const G = {
  A: [14, 17, 17, 31, 17, 17, 17], B: [30, 17, 17, 30, 17, 17, 30], C: [14, 17, 16, 16, 16, 17, 14],
  D: [30, 17, 17, 17, 17, 17, 30], E: [31, 16, 16, 30, 16, 16, 31], F: [31, 16, 16, 30, 16, 16, 16],
  G: [14, 17, 16, 23, 17, 17, 15], H: [17, 17, 17, 31, 17, 17, 17], I: [14, 4, 4, 4, 4, 4, 14],
  J: [7, 2, 2, 2, 2, 18, 12], K: [17, 18, 20, 24, 20, 18, 17], L: [16, 16, 16, 16, 16, 16, 31],
  M: [17, 27, 21, 21, 17, 17, 17], N: [17, 17, 25, 21, 19, 17, 17], O: [14, 17, 17, 17, 17, 17, 14],
  P: [30, 17, 17, 30, 16, 16, 16], Q: [14, 17, 17, 17, 21, 18, 13], R: [30, 17, 17, 30, 20, 18, 17],
  S: [15, 16, 16, 14, 1, 1, 30], T: [31, 4, 4, 4, 4, 4, 4], U: [17, 17, 17, 17, 17, 17, 14],
  V: [17, 17, 17, 17, 17, 10, 4], W: [17, 17, 17, 21, 21, 21, 10], X: [17, 17, 10, 4, 10, 17, 17],
  Y: [17, 17, 10, 4, 4, 4, 4], Z: [31, 1, 2, 4, 8, 16, 31],
  0: [14, 17, 19, 21, 25, 17, 14], 1: [4, 12, 4, 4, 4, 4, 14], 2: [14, 17, 1, 2, 4, 8, 31],
  3: [31, 2, 4, 2, 1, 17, 14], 4: [2, 6, 10, 18, 31, 2, 2], 5: [31, 16, 30, 1, 1, 17, 14],
  6: [6, 8, 16, 30, 17, 17, 14], 7: [31, 1, 2, 4, 8, 8, 8], 8: [14, 17, 17, 14, 17, 17, 14],
  9: [14, 17, 17, 15, 1, 2, 12],
  ":": [0, 6, 6, 0, 6, 6, 0], ".": [0, 0, 0, 0, 0, 6, 6], ",": [0, 0, 0, 0, 6, 2, 4],
  "/": [1, 1, 2, 4, 8, 16, 16], "-": [0, 0, 0, 14, 0, 0, 0], "·": [0, 0, 0, 6, 6, 0, 0],
  ">": [16, 8, 4, 2, 4, 8, 16], "!": [4, 4, 4, 4, 4, 0, 4], "_": [0, 0, 0, 0, 0, 0, 31],
  "?": [14, 17, 1, 2, 4, 0, 4], "&": [12, 18, 20, 8, 21, 18, 13], " ": [0, 0, 0, 0, 0, 0, 0],
  "#": [10, 10, 31, 10, 31, 10, 10], "$": [4, 15, 20, 14, 5, 30, 4], "+": [0, 4, 4, 31, 4, 4, 0],
  "(": [2, 4, 8, 8, 8, 4, 2], ")": [8, 4, 2, 2, 2, 4, 8], "<": [1, 2, 4, 8, 4, 2, 1], "=": [0, 0, 31, 0, 31, 0, 0],
  "%": [24, 25, 2, 4, 8, 19, 3],
};
const ACENTO = { agudo: [2, 4], grave: [8, 4], til: [13, 22], circ: [4, 10] };
const COMPOSTOS = { "Á": ["A", "agudo"], "À": ["A", "grave"], "Ã": ["A", "til"], "Â": ["A", "circ"], "É": ["E", "agudo"],
  "Ê": ["E", "circ"], "Í": ["I", "agudo"], "Ó": ["O", "agudo"], "Ô": ["O", "circ"], "Õ": ["O", "til"], "Ú": ["U", "agudo"] };

export const ALTURA = 7, AVANCO = 6;
const larg = ch => (ch === " " ? 3 : ch === ":" || ch === "." || ch === "," || ch === "·" || ch === "!" ? 4 : AVANCO);

export function medeTexto(txt) {
  let w = 0;
  for (const ch of txt.toUpperCase()) w += larg(ch);
  return Math.max(0, w - 1);
}

// Desenha em (x, y) = canto de cima à esquerda do corpo das letras.
export function escreve(ctx, txt, x, y, cor, s = 1) {
  ctx.fillStyle = cor;
  let cx = Math.round(x);
  for (const ch0 of txt.toUpperCase()) {
    let ch = ch0, ac = null, ced = false;
    if (COMPOSTOS[ch]) [ch, ac] = COMPOSTOS[ch];
    if (ch === "Ç") { ch = "C"; ced = true; }
    const g = G[ch] || G["?"];
    const off = ch === ":" || ch === "." || ch === "," || ch === "·" || ch === "!" ? -1 : 0;
    for (let r = 0; r < 7; r++) for (let b = 0; b < 5; b++) if (g[r] & (16 >> b)) ctx.fillRect(cx + (b + off) * s, y + r * s, s, s);
    if (ac) { const a = ACENTO[ac]; for (let r = 0; r < 2; r++) for (let b = 0; b < 5; b++) if (a[r] & (16 >> b)) ctx.fillRect(cx + b * s, y + (r - 3) * s, s, s); }
    if (ced) { ctx.fillRect(cx + 2 * s, y + 7 * s, s, s); ctx.fillRect(cx + 1 * s, y + 8 * s, s, s); }
    cx += larg(ch0 === ch ? ch : ch0) * s;
  }
  return cx - x;
}

// Placa: fundo, borda de 1 px e texto centralizado.
export function placa(ctx, txt, cx, y, { fundo = "#1d1b26", texto = "#efe9dc", borda = null, pad = 3 } = {}) {
  const w = medeTexto(txt) + pad * 2, h = ALTURA + pad * 2 + (/[ÁÀÃÂÉÊÍÓÔÕÚ]/i.test(txt) ? 2 : 0);
  const x = Math.round(cx - w / 2);
  if (borda) { ctx.fillStyle = borda; ctx.fillRect(x - 1, y - 1, w + 2, h + 2); }
  ctx.fillStyle = fundo; ctx.fillRect(x, y, w, h);
  escreve(ctx, txt, x + pad, y + h - pad - ALTURA, texto);
  return { x, y, w, h };
}

// Fonte mínima 3 × 5, para etiquetas pequenas da cena (cartões, painéis).
const M = {
  A: "010101111101101", B: "110101110101110", C: "011100100100011", D: "110101101101110", E: "111100110100111",
  F: "111100110100100", G: "011100101101011", H: "101101111101101", I: "111010010010111", J: "001001001101010",
  K: "101101110101101", L: "100100100100111", M: "101111111101101", N: "110101101101101", O: "010101101101010",
  P: "110101110100100", Q: "010101101110011", R: "110101110101101", S: "011100010001110", T: "111010010010010",
  U: "101101101101111", V: "101101101101010", W: "101101111111101", X: "101101010101101", Y: "101101010010010",
  Z: "111001010100111", 0: "111101101101111", 1: "010110010010111", 2: "110001010100111", 3: "110001010001110",
  4: "101101111001001", 5: "111100110001110", 6: "011100111101111", 7: "111001010010010", 8: "111101111101111",
  9: "111101111001110", "#": "101111101111101", " ": "000000000000000", ".": "000000000000010", ":": "000010000010000",
  "-": "000000111000000", "/": "001001010100100", ">": "100010001010100", "!": "010010010000010", "?": "110001010000010",
  "·": "000000010000000", "%": "101001010100101", "+": "000010111010000", "_": "000000000000111",
};
const MACENTO = { "Ã": "A", "Á": "A", "É": "E", "Ê": "E", "Í": "I", "Ó": "O", "Õ": "O", "Ú": "U", "Ç": "C", "Â": "A", "Ô": "O" };
export function medeMini(txt) { return Math.max(0, String(txt).length * 4 - 1); }
export function escreveMini(ctx, txt, x, y, cor) {
  ctx.fillStyle = cor;
  let cx = Math.round(x);
  for (const c0 of String(txt).toUpperCase()) {
    const c = MACENTO[c0] || c0, g = M[c] || M["?"];
    for (let i = 0; i < 15; i++) if (g[i] === "1") ctx.fillRect(cx + (i % 3), y + Math.floor(i / 3), 1, 1);
    if (c0 === "Ã" || c0 === "Õ") { ctx.fillRect(cx, y - 2, 2, 1); ctx.fillRect(cx + 1, y - 2, 0, 0); ctx.fillRect(cx + 2, y - 3, 1, 1); }
    else if ("ÁÉÍÓÚ".includes(c0)) ctx.fillRect(cx + 1, y - 2, 1, 1);
    else if ("ÊÂÔ".includes(c0)) { ctx.fillRect(cx, y - 2, 1, 1); ctx.fillRect(cx + 2, y - 2, 1, 1); ctx.fillRect(cx + 1, y - 3, 1, 1); }
    cx += 4;
  }
  return cx - x;
}
