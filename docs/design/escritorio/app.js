// O escritório: liga os dados ao motor de cena, o motor à cena 2D e a cena à
// página. Tudo o que aparece sai de dados/equipe.json e dados/dia-demo.json;
// aqui não há número escrito à mão.

import { criaMotor, Replay, Locomocao, VELOCIDADES, campos, hhmm, hhmmss, diaMes, semana, semanaCurta, msDe, duracaoTexto, numero, dinheiro } from "./motor.js";
import { Cena2D } from "./cena2d.js";
import { W, H, SALA, SALAS, retSala, PARADAS, MESA } from "./planta.js";
import { sprite, registraVisuais, visual } from "./sprites.js";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const cor = id => `var(--c-${id}, #888)`;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const reduz = matchMedia("(prefers-reduced-motion: reduce)");
const grosso = matchMedia("(pointer: coarse)");
const URLP = new URLSearchParams(location.search);
const DADOS = URLP.get("dados") || "dados";

const ORIGEM = { humano: "humano", agente: "frase do agente", ferramenta: "ferramenta", ci: "esteira de CI", mundo: "de fora", interno: "interno",
  agenda: "agenda", numeros: "números do dia", visitante: "reação do site" };
const ORIGEM_CURTA = { humano: "humano", agente: "agente", ferramenta: "ferramenta", ci: "ci", mundo: "mundo", interno: "interno", agenda: "agenda", numeros: "números", visitante: "site" };
const ONDE = { dev: "no desenvolvimento", planejamento: "no planejamento", portaria: "na portaria", cafe: "no café", servidores: "nos servidores", escada: "na escada" };
const DESC = {
  EXPEDIENTE: "Cada um no seu lugar. Quem fez algo há pouco tem balão.",
  "ALMOÇO": "O Camps no sofá; os robôs seguem com a fila.",
  FECHADO: "Robôs na recarga. Só o Vigia, na portaria.",
  FOLGA: "Dia sem expediente. Só o Vigia e os robôs na recarga.",
  "SEM DADOS": "Dia útil, e o registro de hoje ainda não chegou.",
  REPLAY: "Não é ao vivo. O relógio mostra o horário de cada evento.",
};
const CABECA = { humano: 56, pernas: 34, rodas: 46, drone: 36, tubo: 24 };
const ICONE = {
  play: '<svg class="icone" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2.5v11l9-5.5z" fill="currentColor"/></svg>',
  pausa: '<svg class="icone" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2.5h3v11H4zM9 2.5h3v11H9z" fill="currentColor"/></svg>',
  rever: '<svg class="icone" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8a5 5 0 1 0 1.5-3.6M3 2.5v2.8h2.8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  fechar: '<svg class="icone" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  alerta: '<svg class="icone" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.8 15 14H1z" fill="currentColor"/><path d="M8 6v4M8 11.6v.4" stroke="#0f1318" stroke-width="1.8" stroke-linecap="round"/></svg>',
};
const COLS = [["a fazer", "A fazer", "#ffe27a"], ["fazendo", "Fazendo", "#9fd8ff"], ["revisão", "Revisão", "#dcc2ff"], ["publicado", "No ar", "#b9f0a8"]];

const S = { M: null, loc: new Locomocao(), cena: null, c2d: null, replay: null, sim: null, sug: null,
  ficha: null, aba: null, volta: null, seguir: true, salaFoco: "portaria", parada: null, pausaSeguir: 0,
  med: null, saltar: true, ult: 0, q: null, assin: {}, anunciado: 0 };
const palco = $("#palco"), camada = $("#camada"), moldura = $("#moldura"), registro = $("#registro"), lista = $("#registro-lista"), hud = $("#hud");
const CORTE = 90;

// ------------------------------------------------------------ relógio
const agoraMs = () => (S.sim ? S.sim.base + (performance.now() - S.sim.desde) : Date.now());

// ------------------------------------------------------------ medidas do palco
function medidas() {
  const dpr = clamp(window.devicePixelRatio || 1, 1, 3);
  const larg = moldura.clientWidth;
  if (larg >= 720) {
    let k = Math.max(1, Math.floor(larg * dpr / W));
    if (k * W / dpr < larg * .8) k = larg * dpr / W;
    return { modo: "inteiro", k, dpr, cssW: Math.round(W * k / dpr), cssH: Math.round(H * k / dpr) };
  }
  const k = Math.max(2, Math.round(larg * dpr / 200));
  const cssH = Math.round(Math.min(innerHeight * .62, 170 * k / dpr));
  return { modo: "sala", k, dpr, cssW: larg, cssH };
}
function aplicaMedidas() {
  S.med = medidas();
  palco.style.width = S.med.cssW + "px"; palco.style.height = S.med.cssH + "px";
  S.c2d.medidas(S.med);
  for (const it of BAL.values()) it.medir = true;
  $("#sala-atual").hidden = S.med.modo === "inteiro";
  posicionaBotoesMinimapa();
  ajustaRegistro();
}
function ajustaRegistro() {
  const lado = getComputedStyle($(".estudio-grade")).gridTemplateColumns.split(" ").length > 1;
  registro.style.height = lado ? (S.med.cssH + hud.offsetHeight + 8) + "px" : "";
}

// ------------------------------------------------------------ carga
async function carrega() {
  const [eq, dia] = await Promise.all([
    fetch(`${DADOS}/equipe.json`).then(r => { if (!r.ok) throw new Error("equipe.json " + r.status); return r.json(); }),
    fetch(`${DADOS}/dia-demo.json`).then(r => { if (!r.ok) throw new Error("dia-demo.json " + r.status); return r.json(); }),
  ]);
  registraVisuais(eq.equipe);
  for (const m of eq.equipe) document.documentElement.style.setProperty(`--c-${m.id}`, m.visual.cor);
  S.M = criaMotor(eq, dia);
  S.c2d = new Cena2D(palco); S.cena = S.c2d;
  S.c2d.configura({ sprint: dia.sprint.nome.toUpperCase(), espec: dia.sprint.spec.titulo, itens: dia.sprint.spec.itens, sigla: eq.escritorio.sigla });
  const e = eq.escritorio;
  $("#sigla").textContent = e.sigla; $("#nome-escritorio").textContent = e.nome;
  document.title = `${e.nome} · protótipo`;
  $("#selo-demo").hidden = !S.M.DEMO;
  $("#proto-dados").textContent = S.M.DEMO ? `dia de demonstração (${semana(dia.data)}, ${diaMes(dia.data)}), tocado no relógio de hoje.` : `dados de ${semana(dia.data)}, ${diaMes(dia.data)}.`;
  montaSprint(); montaReplay(); criaBotoes(); criaAlvos(); montaMinimapa();
  aplicaMedidas();
  parametros();
  requestAnimationFrame(laco);
}

function parametros() {
  const sim = URLP.get("sim");
  if (sim) simula(sim);
  if (URLP.get("tema")) tema(URLP.get("tema") === "escuro" ? "dark" : URLP.get("tema") === "claro" ? "light" : URLP.get("tema"));
  if (URLP.has("replay")) {
    abreReplay(URLP.get("vel") || "maximo", false);
    if (URLP.get("em")) S.replay.irPara(msDe(S.M.D, URLP.get("em")));
    if (URLP.has("pausa")) S.replay.pausado = true;
  }
  if (URLP.get("ficha") && (S.M.porId[URLP.get("ficha")] || URLP.get("ficha").startsWith("mesa:"))) setTimeout(() => abreFicha(URLP.get("ficha"), URLP.get("aba")), 60);
}

// ------------------------------------------------------------ laço
function laco(t) {
  requestAnimationFrame(laco);
  if (document.hidden) return;
  const passou = t - S.ult;
  if (grosso.matches && passou < 1000 / 31) return;
  S.ult = t;
  const dt = clamp(passou, 0, 100);
  if (S.replay) S.replay.avanca(dt);
  const ms = S.replay ? S.replay.ms() : agoraMs();
  const q = S.M.quadro(ms, { replay: !!S.replay, sugestao: S.sug != null ? t - S.sug : null });
  S.q = q;
  const salto = S.saltar || reduz.matches;
  S.loc.define(q.pessoas, salto);
  S.loc.atualiza(salto ? 0 : dt);
  camera(q, salto);
  S.saltar = false;
  S.cena.desenha({ q, pessoas: S.loc.ordem(), t, ms, dt, semMovimento: reduz.matches });
  atualizaCamada(q);
  textos(q, ms, t);
  if (S.med.modo !== "inteiro") desenhaMinimapa(q);
}
document.addEventListener("visibilitychange", () => { S.ult = performance.now(); });

// ------------------------------------------------------------ câmera (celular)
function camera(q, salto) {
  if (S.med.modo === "inteiro") return;
  if (!S.seguir && performance.now() > S.pausaSeguir) S.seguir = true;
  let sala, x = null;
  if (S.seguir) {
    sala = q.ativa || "portaria";
    const b = q.baloes.find(b => b.sala === sala), p = b && S.loc.p[b.quem];
    if (p) x = p.x;
  } else {
    const par = PARADAS.find(p => p.id === S.parada) || PARADAS[0];
    sala = par.sala; x = par.x ?? null;
  }
  const nome = S.seguir ? SALA[sala].nome : (PARADAS.find(p => p.id === S.parada) || {}).nome || SALA[sala].nome;
  if (nome !== S.salaCamNome) { S.salaCamNome = nome; $("#sala-nome").textContent = nome; }
  S.salaCam = sala;
  $("#btn-seguir").hidden = S.seguir;
  const r = retSala(sala);
  if (x == null) x = r.x + r.w / 2;
  if (!arrasto) S.cena.segue(x, r.y + r.h / 2 + 2, salto);
}
function paradaAtual() {
  if (S.parada && !S.seguir) return PARADAS.findIndex(p => p.id === S.parada);
  const cx = S.c2d.cam.x;
  let melhor = 0, d = Infinity;
  PARADAS.forEach((p, i) => { if (p.sala !== S.salaCam) return; const r = retSala(p.sala), x = p.x ?? r.x + r.w / 2; if (Math.abs(x - cx) < d) { d = Math.abs(x - cx); melhor = i; } });
  return melhor;
}
function irSala(delta) {
  const i = paradaAtual(), n = PARADAS.length;
  S.parada = PARADAS[(i + delta + n) % n].id;
  S.seguir = false; S.pausaSeguir = performance.now() + 25e3;
}
function vaiSala(id) { S.parada = (PARADAS.find(p => p.sala === id) || PARADAS[0]).id; S.seguir = false; S.pausaSeguir = performance.now() + 25e3; }
let arrasto = null;
palco.addEventListener("pointerdown", e => {
  if (S.med.modo === "inteiro") return;
  arrasto = { x: e.clientX, y: e.clientY, cam: S.c2d.cam.x, ativo: false, id: e.pointerId };
});
palco.addEventListener("pointermove", e => {
  if (!arrasto || e.pointerId !== arrasto.id) return;
  const dx = e.clientX - arrasto.x, dy = e.clientY - arrasto.y;
  if (!arrasto.ativo && Math.abs(dx) > 12 && Math.abs(dx) > Math.abs(dy)) { arrasto.ativo = true; palco.setPointerCapture(e.pointerId); }
  if (arrasto.ativo) { S.c2d.cam.alvoX = S.c2d.cam.x = arrasto.cam - dx / S.c2d.escala(); }
});
const soltar = e => {
  if (!arrasto) return;
  const dx = e.clientX - arrasto.x, ativo = arrasto.ativo;
  arrasto = null;
  if (ativo && Math.abs(dx) > 40) irSala(dx < 0 ? 1 : -1);
};
palco.addEventListener("pointerup", soltar);
palco.addEventListener("pointercancel", () => { arrasto = null; });
$("#sala-ant").addEventListener("click", () => irSala(-1));
$("#sala-prox").addEventListener("click", () => irSala(1));
$("#btn-seguir").addEventListener("click", () => { S.seguir = true; S.parada = null; });

// ------------------------------------------------------------ minimapa
const mini = $("#minimapa-canvas"), miniCaixa = $("#minimapa");
const Y0 = 16, Y1 = 334;
function miniEscala() {
  const w = mini.width, h = mini.height, s = Math.min(w / W, h / (Y1 - Y0));
  return { s, ox: (w - W * s) / 2, oy: (h - (Y1 - Y0) * s) / 2 };
}
function montaMinimapa() {
  for (const sl of SALAS) {
    if (sl.id === "escada") continue;
    const b = document.createElement("button");
    b.type = "button"; b.dataset.sala = sl.id; b.setAttribute("aria-label", `Ver ${sl.nome}`);
    b.addEventListener("click", () => vaiSala(sl.id));
    miniCaixa.append(b);
  }
}
function posicionaBotoesMinimapa() {
  const r = miniCaixa.getBoundingClientRect(), dpr = clamp(devicePixelRatio || 1, 1, 3);
  if (!r.width) return;
  mini.width = Math.round(r.width * dpr); mini.height = Math.round(r.height * dpr);
  const { s, ox, oy } = miniEscala();
  for (const b of $$("button", miniCaixa)) {
    const q = retSala(b.dataset.sala);
    Object.assign(b.style, { left: (ox + q.x * s) / dpr + "px", top: (oy + (q.y - Y0) * s) / dpr + "px", width: q.w * s / dpr + "px", height: q.h * s / dpr + "px" });
  }
}
function desenhaMinimapa(q) {
  const c = mini.getContext("2d"), { s, ox, oy } = miniEscala();
  c.fillStyle = "#0b0e12"; c.fillRect(0, 0, mini.width, mini.height);
  const comBalao = new Set(q.baloes.map(b => b.sala));
  for (const sl of SALAS) {
    if (sl.id === "escada") continue;
    const r = retSala(sl.id), x = ox + r.x * s, y = oy + (r.y - Y0) * s, w = r.w * s, h = r.h * s;
    const l = q.luz[sl.id];
    c.fillStyle = l === "acesa" ? "#e9dcc0" : l === "penumbra" ? "#7a8292" : l === "servidor" ? "#1d3350" : "#262b36";
    c.fillRect(x + 1, y + 1, w - 2, h - 2);
    if (comBalao.has(sl.id)) { c.strokeStyle = "#39ff6a"; c.lineWidth = 2; c.strokeRect(x + 2, y + 2, w - 4, h - 4); }
  }
  const v = S.c2d.visao();
  c.strokeStyle = "#ffffff"; c.lineWidth = 2; c.strokeRect(ox + v.x * s + 1, oy + (v.y - Y0) * s + 1, v.w * s - 2, v.h * s - 2);
  for (const p of Object.values(S.loc.p)) {
    c.fillStyle = (visual(p.id) || {}).cor || "#fff";
    const x = ox + p.x * s, y = oy + (p.y - (p.alt || 0) - Y0 - 12) * s;
    c.beginPath(); c.arc(x, y, Math.max(2.5, s * 5), 0, Math.PI * 2); c.fill();
  }
}

// ------------------------------------------------------------ personagens, alvos e balões (HTML sobre a cena)
const BOT = {}, BAL = new Map();
function criaBotoes() {
  for (const p of S.M.membros) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "pers"; b.dataset.id = p.id; b.hidden = true;
    b.innerHTML = `<span class="tag">${esc(p.nome)}</span>`;
    b.addEventListener("click", () => abreFicha(p.id, null, b));
    camada.append(b); BOT[p.id] = b;
  }
}
const ALVOS = [];
function criaAlvos() {
  for (const a of S.c2d.alvos()) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "alvo"; b.setAttribute("aria-label", a.rotulo); b.hidden = true;
    b.addEventListener("click", () => {
      if (a.id === "quadro") abreFicha("camps", "sprint", b);
      else if (a.id === "espec") abreFicha("camps", "sprint", b);
      else if (a.id === "painel-ci") abreFicha("integrador", "ci", b);
      else if (a.mesa) abreFicha("mesa:" + a.mesa, null, b);
    });
    camada.prepend(b); ALVOS.push({ ...a, el: b });
  }
}
function atualizaCamada(q) {
  const pw = S.med.cssW, ph = S.med.cssH;
  for (const a of ALVOS) {
    let ok = true;
    if (a.mesa) { const m = q.mesas && q.mesas[a.mesa]; ok = !!m && !m.ocupada; if (ok) a.el.setAttribute("aria-label", `Mesa ${a.mesa.slice(1)}, ${m.vaga && m.vaga.para ? "reservada" : "vaga"}. Abrir.`); }
    if (a.id === "quadro" && q.tickets) a.el.setAttribute("aria-label", `Quadro de tickets: ${COLS.map(([k, n]) => `${n.toLowerCase()} ${Object.values(q.tickets).filter(t => t.estado === k).length}`).join(", ")}. Abrir o sprint.`);
    const p0 = S.cena.projeta(a.x, a.y), p1 = S.cena.projeta(a.x + a.w, a.y + a.h);
    const fora = !ok || p1.x < 0 || p0.x > pw || p1.y < 0 || p0.y > ph;
    if (a.el.hidden !== fora) a.el.hidden = fora;
    if (!fora) { a.el.style.transform = `translate(${p0.x.toFixed(1)}px, ${p0.y.toFixed(1)}px)`; a.el.style.width = (p1.x - p0.x).toFixed(1) + "px"; a.el.style.height = (p1.y - p0.y).toFixed(1) + "px"; }
  }
  for (const p of S.M.membros) {
    const b = BOT[p.id], s = S.loc.p[p.id];
    if (!s) { if (!b.hidden) b.hidden = true; continue; }
    const v = visual(p.id), alt = s.alt || 0, alto = CABECA[v.corpo] || 56;
    const pe = S.cena.projeta(s.x, s.y, alt), cab = S.cena.projeta(s.x, s.y, alt + alto);
    const h = Math.max(24, pe.y - cab.y), w = Math.max(24, v.corpo === "humano" ? h * .48 : h * 1.05);
    const fora = pe.x < -w || pe.x > pw + w || cab.y > ph || pe.y < 0;
    if (b.hidden !== fora) b.hidden = fora;
    if (fora) continue;
    b.style.transform = `translate(${(pe.x - w / 2).toFixed(1)}px, ${cab.y.toFixed(1)}px)`;
    b.style.width = w.toFixed(1) + "px"; b.style.height = h.toFixed(1) + "px";
    const inf = s.info || {}, onde = s.andando ? "andando" : ONDE[s.sala] || "no escritório";
    const rot = `${p.nome}, ${onde}${inf.situ && !s.andando ? `, ${inf.situ}` : ""}. Abrir a ficha.`;
    if (b.getAttribute("aria-label") !== rot) b.setAttribute("aria-label", rot);
  }
  const vivos = new Set();
  for (const bl of q.baloes) {
    const s = S.loc.p[bl.quem];
    if (!s || s.andando || s.sala !== bl.sala || (s.opacidade ?? 1) < .9) continue;
    const r = S.cena.retSala(bl.sala);
    const visW = Math.min(r.x + r.w, pw) - Math.max(r.x, 0), visH = Math.min(r.y + r.h, ph) - Math.max(r.y, 0);
    if (visW < Math.min(r.w * .6, 150) || visH < Math.min(r.h * .6, 120)) continue;
    let it = BAL.get(bl.chave);
    if (!it) { it = { el: criaBalao(bl), medir: true }; camada.append(it.el); BAL.set(bl.chave, it); }
    vivos.add(bl.chave);
    const v = visual(bl.quem), cab = S.cena.projeta(s.x, s.y, (s.alt || 0) + (CABECA[v.corpo] || 56));
    const x0 = Math.max(r.x + 4, 4), x1 = Math.min(r.x + r.w - 4, pw - 4), topo = Math.max(r.y + 4, 4);
    const disp = Math.round(cab.y - 12 - topo);
    const maxW = Math.round(clamp(x1 - x0, 110, 290));
    if (it.medir || it.maxW !== maxW || Math.abs((it.disp ?? 0) - disp) > 10) {
      it.el.classList.remove("sem-pe");
      it.el.style.setProperty("--max", maxW + "px");
      it.el.style.setProperty("--linhas", 8);
      it.w = it.el.offsetWidth; it.h = it.el.offsetHeight;
      if (it.h > disp && it.el.querySelector(".balao-pe")) { it.el.classList.add("sem-pe"); it.w = it.el.offsetWidth; it.h = it.el.offsetHeight; }
      if (it.h > disp && disp > 40) {
        const linhas = clamp(Math.floor((disp - (it.h - it.el.querySelector(".balao-txt").offsetHeight) - 4) / 18), 1, 8);
        it.el.style.setProperty("--linhas", linhas);
        it.h = it.el.offsetHeight;
      }
      it.medir = false; it.maxW = maxW; it.disp = disp;
    }
    const left = clamp(cab.x - it.w / 2, x0, Math.max(x0, x1 - it.w));
    const top = Math.max(topo, cab.y - 12 - it.h);
    it.el.style.transform = `translate(${left.toFixed(1)}px, ${top.toFixed(1)}px)`;
    it.el.style.setProperty("--rabo", clamp(cab.x - left, 14, it.w - 14).toFixed(1) + "px");
  }
  for (const [k, it] of BAL) if (!vivos.has(k)) { it.el.remove(); BAL.delete(k); }
  placaFolga(q);
}
function criaBalao(b) {
  const el = document.createElement("div");
  el.className = `balao o-${b.origem}`;
  el.style.setProperty("--cor", cor(b.quem));
  el.setAttribute("aria-hidden", "true");
  const pe = b.origem === "numeros" ? "montado com os números do dia" : b.origem === "visitante" ? "reação do site ao seu pedido" : "";
  el.innerHTML = `<div class="balao-cab"><span class="ponto"></span>${esc(S.M.nomeDe(b.quem))}<span class="origem">· ${esc(ORIGEM[b.origem] || b.origem)}</span></div>`
    + `<p class="balao-txt">${esc(corta(b.texto))}</p>`
    + (pe ? `<span class="balao-pe">${pe}</span>` : "");
  return el;
}
function corta(txt, n = CORTE) {
  txt = String(txt);
  if (txt.length <= n) return txt;
  let c = txt.slice(0, n);
  const esp = c.lastIndexOf(" ");
  if (esp > n - 24) c = c.slice(0, esp);
  return c.replace(/[\s,;:.\-–—]+$/, "") + "…";
}
let placaEl = null;
function placaFolga(q) {
  if (!q.placa) { if (placaEl) { placaEl.remove(); placaEl = null; } return; }
  if (!placaEl) { placaEl = document.createElement("div"); placaEl.className = "placa-folga"; placaEl.setAttribute("role", "note"); camada.append(placaEl); }
  if (placaEl.dataset.t !== q.placa) { placaEl.innerHTML = `<small>FOLGA · AVISO DA PORTARIA</small>${esc(q.placa.toLowerCase())}`; placaEl.dataset.t = q.placa; }
  const r = S.cena.retSala("cafe"), w = placaEl.offsetWidth;
  placaEl.hidden = !(r.x + r.w > 0 && r.x < S.med.cssW);
  placaEl.style.transform = `translate(${(r.x + r.w * .4 - w / 2).toFixed(1)}px, ${(r.y + r.h * .22).toFixed(1)}px)`;
}

// ------------------------------------------------------------ textos da página
function muda(chave, valor, fn) { if (S.assin[chave] !== valor) { S.assin[chave] = valor; fn(valor); } }
function textos(q, ms, t) {
  const c = campos(ms);
  muda("dia", `${c.dia} ${diaMes(c.data)}`, v => { $("#hora-dia").textContent = v; });
  muda("hora", S.replay ? hhmmss(ms) : hhmm(ms), v => { $("#hora-hhmm").textContent = v; });
  muda("fuso", S.replay ? "Horário do dia de exemplo" : S.sim ? "São Paulo · simulado" : "Horário de São Paulo", v => { $("#hora-fuso").textContent = v; });
  muda("estado", q.estado, v => { $("#estado").textContent = v; });
  muda("chip", q.rotulo, v => { $("#chip").textContent = v; $("#chip").dataset.p = v; $("#periodo-desc").textContent = DESC[v] || ""; });
  palco.classList.toggle("em-replay", !!S.replay);
  painel(q, ms, t);
  hudRender(q, ms);
  kanban(q);
  if (S.replay) textosReplay(ms);
  if (S.ficha && S.aba === "hoje") muda("agora", agoraDe(S.ficha, q), v => { const el = $("#agora-txt"); if (el) el.innerHTML = v; });
}

// ------------------------------------------------------------ painel do operador: métricas, custo e eventos
const MAX_REG = 80;
function painel(q, ms, t) {
  const M = S.M, m = q.metricas || (q.dia ? q.dia.metricas : null);
  const lim = M.dia.limites || {};
  muda("sub", S.replay ? "replay" : q.dia ? (M.DEMO ? "hoje · dia de exemplo" : "hoje") : "fora do expediente", v => { $("#registro-sub").textContent = v; });
  const linha = (rot, val, cls = "") => `<span>${rot}</span><b${cls ? ` class="${cls}"` : ""}>${val}</b>`;
  const html = m ? [
    linha("tickets entregues", numero(m.entregues)),
    linha("PRs mesclados", numero(m.mesclados)),
    linha("CI verde", m.ciTotal ? `${m.ciVerde} de ${m.ciTotal}` : "—", m.ciTotal && m.ciVerde === m.ciTotal ? "verde" : ""),
    linha("rodadas de revisão", numero(m.rodadas)),
    linha("deploys", numero(m.deploys)),
    `<span>cafés do Camps</span><b>${m.cafes}${lim.cafes ? ` de ${lim.cafes}` : ""}${lim.cafes ? `<span class="xicaras" aria-hidden="true">${Array.from({ length: lim.cafes }, (_, i) => `<i class="${i < m.cafes ? "cheia" : ""}"></i>`).join("")}</span>` : ""}</b>`,
  ].join("") : `<span>Sem expediente agora.</span><b></b>`;
  muda("metricas", html, v => { $("#metricas").innerHTML = v; });
  const custo = m ? m.custo : null;
  const cHtml = custo != null ? `<div class="linha"><span>custo de modelo hoje</span><span><b>${dinheiro(custo)}</b>${lim.custo_usd ? ` de ${dinheiro(lim.custo_usd).replace("US$ ", "")}` : ""}</span></div>`
    + (lim.custo_usd ? `<div class="barra" role="img" aria-label="${dinheiro(custo)} de ${dinheiro(lim.custo_usd)}"><i class="${custo / lim.custo_usd > .8 ? "alto" : ""}" style="width:${Math.min(100, 100 * custo / lim.custo_usd).toFixed(1)}%"></i></div>` : "") : "";
  muda("custo", cHtml, v => { $("#custo").innerHTML = v; $("#custo").hidden = !v; });
  // eventos
  const doDia = !!q.dia && q.md != null && q.per !== "fechado";
  let itens, chave;
  if (doDia) {
    const n = q.dia.n;
    itens = M.corrida.slice(Math.max(0, n - MAX_REG), n).reverse().map((e, i) => ({ ...e, chave: "e" + e.i, atual: i === 0 }));
    chave = "g" + n + (S.replay ? "r" : "");
  } else { itens = q.fita; chave = q.fitaRotulo + itens.map(e => e.chave + (e.atual ? "*" : "")).join("|"); }
  muda("registro", chave, () => {
    $("#eventos-sub").textContent = S.replay ? (S.replay.fim ? "fim do replay" : "até agora") : q.fitaRotulo.toLowerCase();
    lista.innerHTML = itens.map(itemRegistro).join("") || `<li class="ev ev-sem-hora"><div class="ev-linha"><span class="ev-txt">Nada acontecendo agora.</span></div></li>`;
    $("#registro-nota").textContent = q.fitaNota || (doDia ? (S.replay ? "Clique num evento para levar a linha do tempo até ele." : "O mais recente em cima.") : "");
    if (S.replay && itens[0] && itens[0].ms && t - S.anunciado > 4000 && S.replay.vel !== "maximo") {
      const e = itens[0]; S.anunciado = t;
      $("#anuncio").textContent = `${hhmm(e.ms)}, ${M.nomeDe(e.quem)}: ${e.texto}`;
    }
  });
}
function itemRegistro(e) {
  const tag = ORIGEM_CURTA[e.origem] || e.origem;
  const corpo = `${e.ms ? `<time>${hhmm(e.ms)}</time>` : ""}<span class="ev-cab"><span class="ev-tag">${esc(tag)}</span><span class="ev-quem"><span class="ponto" style="--cor:${cor(e.quem)}"></span>${esc(S.M.nomeDe(e.quem))}</span></span>`
    + `<span class="ev-txt">${esc(e.texto)}</span>`;
  const cls = `ev o-${e.origem}${e.atual ? " atual" : ""}${e.ms ? "" : " ev-sem-hora"}`;
  return S.replay && e.ms
    ? `<li class="${cls}"><button type="button" class="ev-linha" data-ms="${e.ms}" aria-label="Ir para ${hhmm(e.ms)}: ${esc(S.M.nomeDe(e.quem))}, ${esc(tag)}. ${esc(e.texto)}">${corpo}</button></li>`
    : `<li class="${cls}"><div class="ev-linha">${corpo}</div></li>`;
}
lista.addEventListener("click", e => { const b = e.target.closest("[data-ms]"); if (b && S.replay) irPara(+b.dataset.ms); });

// ------------------------------------------------------------ barra de status (só dado do JSON)
function emQuanto(ms, alvo) {
  let min = Math.max(0, Math.round((alvo - ms) / 60000));
  const d = Math.floor(min / 1440); min -= d * 1440; const h = Math.floor(min / 60); min -= h * 60;
  return d ? `em ${d} d ${h} h` : h ? (min ? `em ${h} h ${min} min` : `em ${h} h`) : `em ${min} min`;
}
function hudRender(q, ms) {
  const M = S.M, d = M.dia, it = [];
  const item = (rot, val, cls = "") => `<span${cls ? ` class="${cls}"` : ""}>${rot ? `<span class="rot">${rot}</span>` : ""}<b>${val}</b></span>`;
  if (q.dia && q.per !== "fechado") {
    const pend = q.pendencias || [];
    if (pend.length) it.push(`<span class="alerta">${ICONE.alerta} <b>${esc(pend[0].texto)}</b>${pend.length > 1 ? ` <span class="rot">+${pend.length - 1}</span>` : ""}</span>`);
    else it.push(item("", "nada pendente", "ok"));
    const cap = M.capitulos.filter(c => c.ms <= q.md).pop();
    if (cap) it.push(item("momento", esc(cap.titulo)));
    it.push(item(esc(d.sprint.nome.toLowerCase()), `dia ${d.dia_numero}`));
  } else {
    const c = campos(ms), prox = M.proximoExpediente(c), abre = M.equipe.escritorio.expediente.abre;
    if (prox) it.push(item("próximo expediente", `${prox === c.data ? "hoje" : `${esc(semanaCurta(prox))}, ${diaMes(prox)}`}, às ${esc(abre)} · ${emQuanto(ms, msDe(prox, abre))}`, "fosforo"));
    const E = q.dia || M.estadoDoDia(M.FIM);
    it.push(item(M.DEMO ? "dia de exemplo" : "último dia", `${E.metricas.entregues} tickets · ${E.metricas.deploys} deploys`));
  }
  muda("hud", it.join(""), v => { hud.innerHTML = v; ajustaRegistro(); });
}

// ------------------------------------------------------------ sprint (cartão abaixo da cena)
function montaSprint() {
  const d = S.M.dia;
  $("#sprint-rotulo").textContent = `${d.sprint.nome} · dia ${d.dia_numero}`;
  $("#sprint-titulo").textContent = d.sprint.objetivo;
  $("#btn-espec").addEventListener("click", e => abreFicha("camps", "sprint", e.currentTarget));
}
function kanban(q) {
  const tk = q.tickets || {};
  const html = COLS.map(([k, n, c]) => {
    const ts = Object.values(tk).filter(t => t.estado === k).sort((a, b) => a.id - b.id);
    return `<section style="--kc:${c}"><h3>${n}<span>${ts.length}</span></h3><ul>${ts.map(t => `<li><b>#${t.id}</b>${esc(t.titulo)}${t.novo ? '<span class="novo">novo</span>' : ""}</li>`).join("") || '<li class="vazio" style="background:none;box-shadow:none;padding:0">—</li>'}</ul></section>`;
  }).join("");
  muda("kanban", html, v => { $("#kanban").innerHTML = v; });
  const m = q.metricas;
  muda("smeta", m ? `${m.entregues} entregues hoje · ${m.mesclados} PRs mesclados · até ${hhmm(q.md)}` : "Fora do expediente: o quadro como ficou no fim do dia.", v => { $("#sprint-meta").textContent = v; });
}

// ------------------------------------------------------------ replay
function montaReplay() {
  const M = S.M, r = new Replay(M);
  $("#velocidades").innerHTML = Object.entries(VELOCIDADES).map(([k, v]) =>
    `<button type="button" data-vel="${k}" aria-pressed="false">${v.nome}<small>${duracaoTexto(r.duracao(k) / 1000)}</small></button>`).join("");
  $("#capitulos").innerHTML = M.capitulos.map((c, i) => `<li><button type="button" data-i="${i}"><span class="ponto" style="--cor:#fff"></span>${hhmm(c.ms)} · ${esc(c.titulo)}</button></li>`).join("");
  $("#cap-select").innerHTML = M.capitulos.map((c, i) => `<option value="${i}">${hhmm(c.ms)} · ${esc(c.titulo)}</option>`).join("");
  $("#marcas").innerHTML = M.capitulos.map(c => `<i style="left:${(100 * (c.ms - M.INI) / (M.FIM - M.INI)).toFixed(2)}%"></i>`).join("");
  $("#replay-quando").innerHTML = `<b>${M.DEMO ? "Dia de exemplo" : "Dia"}: ${semana(M.D)}, ${diaMes(M.D)}, das ${hhmm(M.INI)} às ${hhmm(M.FIM)}.</b> <span class="longo">Não é ao vivo: o relógio mostra o horário de cada evento.</span>`;
  $("#velocidades").addEventListener("click", e => { const b = e.target.closest("[data-vel]"); if (b && S.replay) { S.replay.vel = b.dataset.vel; marcaVel(); } });
  $("#capitulos").addEventListener("click", e => { const b = e.target.closest("[data-i]"); if (b) irPara(M.capitulos[+b.dataset.i].ms); });
  $("#cap-select").addEventListener("change", e => irPara(M.capitulos[+e.target.value].ms));
  $("#trilha").addEventListener("input", e => irPara(M.INI + (M.FIM - M.INI) * e.target.value / 1000));
  $("#btn-play").addEventListener("click", () => {
    if (!S.replay) return;
    if (S.replay.fim) { S.replay.recomeca(); S.saltar = true; } else S.replay.pausado = !S.replay.pausado;
  });
  $("#btn-prox").addEventListener("click", () => { if (S.replay) { S.replay.proximo(); S.saltar = true; } });
  $("#btn-replay").addEventListener("click", () => abreReplay());
  $("#btn-sair").addEventListener("click", saiReplay);
}
function abreReplay(vel = "maximo", rolar = true) {
  if (S.replay) { S.replay.recomeca(); S.saltar = true; return; }
  S.replay = new Replay(S.M, VELOCIDADES[vel] ? vel : "maximo");
  $("#faixa-replay").hidden = false;
  const b = $("#btn-replay"); b.setAttribute("aria-pressed", "true"); $(".rotulo-replay", b).textContent = "Recomeçar o replay";
  marcaVel(); S.saltar = true; S.seguir = true;
  if (rolar) window.scrollTo({ top: 0, behavior: reduz.matches ? "auto" : "smooth" });
  $("#btn-play").focus({ preventScroll: true });
}
function saiReplay() {
  S.replay = null;
  $("#faixa-replay").hidden = true;
  const b = $("#btn-replay"); b.setAttribute("aria-pressed", "false"); $(".rotulo-replay", b).textContent = "Replay do dia";
  S.saltar = true;
  b.focus({ preventScroll: true });
}
function irPara(ms) { if (!S.replay) return; S.replay.irPara(ms); S.saltar = true; }
function marcaVel() { $$("[data-vel]").forEach(b => b.setAttribute("aria-pressed", String(!!S.replay && b.dataset.vel === S.replay.vel))); }
function textosReplay(ms) {
  const r = S.replay, M = S.M;
  muda("rhora", hhmmss(ms), v => { $("#replay-hora").textContent = v; $("#trilha").setAttribute("aria-valuetext", v); });
  const tr = $("#trilha");
  if (document.activeElement !== tr) tr.value = Math.round(1000 * clamp(r.progresso(), 0, 1));
  const estado = r.fim ? "rever" : r.pausado ? "play" : "pausa";
  muda("play", estado, v => { const b = $("#btn-play"); b.innerHTML = ICONE[v]; b.setAttribute("aria-label", v === "rever" ? "Rever do começo" : v === "play" ? "Continuar" : "Pausar"); });
  const atual = M.capitulos.filter(c => c.ms <= ms).length - 1;
  muda("cap", atual, v => {
    $$("#capitulos button").forEach((b, i) => b.setAttribute("aria-current", String(i === v)));
    if (v >= 0) $("#cap-select").value = String(v);
  });
}

// ------------------------------------------------------------ ficha
const ficha = $("#ficha");
const ABA_PROPRIA = { camps: ["sprint", "Sprint"], revisor: ["revisoes", "Revisões"], integrador: ["ci", "CI e deploys"],
  pesquisador: ["pesquisas", "Pesquisas"], mensageiro: ["avisos", "Avisos"], vigia: ["plantao", "Plantão"] };

function abreFicha(id, aba, origem, focoAba = false) {
  const vaga = id.startsWith("mesa:");
  const p = vaga ? null : S.M.porId[id];
  const abas = vaga ? [["vaga", "A mesa"]] : [["hoje", "Hoje"], ABA_PROPRIA[id], ["perfil", "Perfil"]].filter(Boolean);
  if (!abas.some(a => a[0] === aba)) aba = abas[0][0];
  if (S.ficha && S.ficha !== id && BOT[S.ficha]) BOT[S.ficha].classList.remove("aberta");
  if (!ficha.open || S.ficha !== id) S.volta = origem || document.activeElement;
  S.ficha = id; S.aba = aba; S.assin.agora = null;
  ficha.style.setProperty("--cor", vaga ? "#b5a684" : cor(id));
  const mesa = vaga ? id.slice(5) : null;
  const titulo = vaga ? `Mesa ${mesa.slice(1)}` : esc(p.nome);
  const sub = vaga ? "Esperando um novo membro da equipe" : esc(p.papel);
  const situ = vaga ? `<span class="situ em_breve">vaga</span>` : `<span class="situ">${p.tipo === "robo" ? "robô" : "humano"}</span>`;
  ficha.innerHTML = `
    <div class="ficha-topo">
      <canvas class="ficha-retrato" width="40" height="44" aria-hidden="true"></canvas>
      <div><h2 id="ficha-nome" tabindex="-1">${titulo} ${situ}</h2><p>${sub}</p></div>
      <button class="fechar" type="button" aria-label="Fechar a ficha">${ICONE.fechar}</button>
    </div>
    <div class="abas" role="tablist" aria-label="Seções da ficha">${abas.map(([k, n]) =>
      `<button role="tab" type="button" id="aba-${k}" data-aba="${k}" aria-controls="ficha-corpo" aria-selected="${k === aba}" tabindex="${k === aba ? 0 : -1}">${n}</button>`).join("")}</div>
    <div class="ficha-corpo" id="ficha-corpo" role="tabpanel" aria-labelledby="aba-${aba}" tabindex="0">${vaga ? corpoVaga(mesa) : corpoFicha(p, aba)}</div>`;
  const rc = $(".ficha-retrato", ficha).getContext("2d");
  rc.imageSmoothingEnabled = false;
  if (!vaga) {
    const v = visual(id), est = v.corpo === "tubo" ? "trabalhando" : "parado";
    const oy = { humano: 0, pernas: 18, rodas: 8, drone: 18, tubo: 26 }[v.corpo] || 0;
    rc.drawImage(sprite(id, est, v.corpo === "tubo" ? 0 : 0), 0, oy, 40, 44, 0, 0, 40, 44);
  } else { rc.fillStyle = "#ebe2cd"; rc.fillRect(6, 14, 28, 20); rc.fillStyle = "#cdbf9f"; rc.fillRect(18, 14, 6, 20); rc.fillStyle = "#b5a684"; rc.fillRect(4, 34, 32, 3); }
  $(".fechar", ficha).addEventListener("click", fechaFicha);
  const tabs = $$("[role=tab]", ficha);
  tabs.forEach((b, i) => {
    b.addEventListener("click", () => abreFicha(id, b.dataset.aba, null, true));
    b.addEventListener("keydown", e => {
      const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (d) { e.preventDefault(); abreFicha(id, tabs[(i + d + tabs.length) % tabs.length].dataset.aba, null, true); }
    });
  });
  const pedir = $("[data-acao=ticket]", ficha);
  if (pedir) pedir.addEventListener("click", () => { fechaFicha(); $("#ticket-titulo").focus(); $("#sugira").scrollIntoView({ behavior: reduz.matches ? "auto" : "smooth", block: "center" }); });
  if (!ficha.open) {
    if (S.med.modo === "inteiro") { document.body.classList.add("com-ficha"); ficha.show(); aplicaMedidas(); }
    else ficha.showModal();
  }
  if (BOT[id]) BOT[id].classList.add("aberta");
  if (focoAba) $(`#aba-${aba}`, ficha).focus(); else $("#ficha-nome", ficha).focus();
  if (aba === "hoje" && S.q) { const el = $("#agora-txt"); if (el) el.innerHTML = agoraDe(id, S.q); }
}
function fechaFicha() { if (ficha.open) ficha.close(); }
ficha.addEventListener("close", () => {
  if (document.body.classList.contains("com-ficha")) { document.body.classList.remove("com-ficha"); aplicaMedidas(); }
  if (S.ficha && BOT[S.ficha]) BOT[S.ficha].classList.remove("aberta");
  S.ficha = null;
  const v = S.volta; S.volta = null;
  if (v && document.contains(v)) requestAnimationFrame(() => requestAnimationFrame(() => { if (!v.hidden) v.focus({ preventScroll: true }); }));
});
ficha.addEventListener("keydown", e => { if (e.key === "Escape" && !ficha.matches(":modal")) { e.preventDefault(); fechaFicha(); } });
ficha.addEventListener("click", e => { if (e.target === ficha && ficha.matches(":modal")) fechaFicha(); });

function agoraDe(id, q) {
  const s = S.loc.p[id];
  if (!s) {
    const prox = S.M.proximoExpediente(campos(q.ms));
    return `Fora do escritório.${prox ? ` Volta ${esc(semanaCurta(prox))}, ${diaMes(prox)}, às ${esc(S.M.equipe.escritorio.expediente.abre)}.` : ""}`;
  }
  if (s.andando) return "Andando pelo escritório.";
  const b = q.baloes.find(b => b.quem === id);
  const onde = ONDE[s.sala] || "no escritório";
  const quando = q.replay ? ` <span class="nota">(replay, ${hhmm(q.ms)})</span>` : "";
  const Onde = onde[0].toUpperCase() + onde.slice(1);
  const aspas = b && (b.origem === "agente" || b.origem === "humano");
  if (b) return `${esc(Onde)}: <span class="o-${b.origem}" style="${b.origem === "agente" ? "font-style:italic" : ""}">${aspas ? "“" : ""}${esc(b.texto)}${aspas ? "”" : ""}</span>${quando}`;
  return `${esc(Onde)}, ${esc((s.info || {}).situ || "parado")}.${quando}`;
}

function fitaDe(evs) {
  return `<ol class="fita">${evs.map(e => `<li><time>${hhmm(e.ms)}</time><span class="t o-${e.origem}">${esc(e.texto)}</span></li>`).join("")
    || `<li><span></span><span class="t">Nada registrado até agora.</span></li>`}</ol>`;
}
function corpoVaga(mesa) {
  const info = S.q && S.q.mesas ? S.q.mesas[mesa] : null, v = info && info.vaga;
  const dono = S.M.membros.find(p => p.posto === mesa);
  return `<div class="agora"><p class="rotulo">Coberta, esperando alguém</p><p>${v && v.para ? `Reservada para: <b>${esc(v.para)}</b>${v.previsto ? `, previsto para ${esc(v.previsto)}` : ""}.` : "Sem ninguém previsto ainda."}</p></div>
    ${dono ? `<p class="costura"><b>${esc(dono.nome)}</b> ocupa esta mesa quando chega.</p>` : ""}
    <p class="nota" style="margin:0">Quando um novo agente entra na equipe (um item novo em <span class="mono">equipe.json</span>, com um <span class="mono">posto</span> numa mesa livre), o lençol sai e o robô chega pela porta. Robôs de pernas, rodas, drone ou tubo ganham o desenho do corpo na cor que vier no JSON.</p>`;
}
function corpoFicha(p, aba) {
  const id = p.id, M = S.M, d = M.dia, q = S.q, ate = q && q.md != null ? q.md : M.FIM;
  const meus = M.eventos.filter(e => e.quem === id && e.ms <= ate);
  const porTras = `<p class="costura"><b>Por trás:</b> ${esc(p.por_tras)}</p>`;
  switch (aba) {
    case "hoje":
      return `<div class="agora"><p class="rotulo">Agora</p><p id="agora-txt">—</p></div><p style="margin:0">${esc(p.faz)}</p>
        <h3>${M.DEMO ? "No dia de exemplo" : "Hoje"} <span class="nota">· ${meus.length} registros até ${hhmm(ate)}</span></h3>${fitaDe(meus)}`;
    case "perfil":
      return `<ul class="lista">
          <li><b>Papel:</b> ${esc(p.papel)}</li>
          <li><b>Corpo:</b> ${esc({ humano: "humano", pernas: "robô de quatro pernas", rodas: "robô de uma roda", drone: "drone", tubo: "robô do tubo pneumático" }[p.visual.corpo] || p.visual.corpo)}</li>
          <li><b>Modelo:</b> ${p.modelo ? esc(p.modelo) : "nenhum (é gente)"}</li>
          <li><b>Ferramentas:</b> ${p.ferramentas.map(esc).join(", ")}</li>
          <li><b>Na equipe desde:</b> ${diaMes(p.desde)}${p.posto ? ` · posto: <span class="mono">${esc(p.posto)}</span>` : ""}</li>
        </ul>${porTras}${M.DEMO ? `<p class="nota" style="margin:0">Equipe de demonstração: o modelo e as ferramentas são exemplos.</p>` : ""}`;
    case "sprint": {
      const tk = (q && q.tickets) || {};
      return `<div class="agora"><p class="rotulo">Especificação atual</p><p><b>${esc(d.sprint.spec.titulo)}</b></p>
          <ul class="lista" style="margin-top:6px">${d.sprint.spec.itens.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>
        ${COLS.map(([k, n]) => { const ts = Object.values(tk).filter(t => t.estado === k).sort((a, b) => a.id - b.id);
          return `<h3>${n} <span class="nota">· ${ts.length}</span></h3><ul class="lista">${ts.map(t => `<li><b class="mono">#${t.id}</b> ${esc(t.titulo)}</li>`).join("") || '<li class="nota">—</li>'}</ul>`; }).join("")}
        <p class="nota" style="margin:0">Estado em ${hhmm(ate)}${M.DEMO ? ", no dia de exemplo" : ""}.</p>
        <button class="btn btn-acao" type="button" data-acao="ticket" style="justify-self:start">Abrir um ticket</button>`;
    }
    case "revisoes": {
      const E = M.estadoDoDia(ate);
      const prs = Object.values(E.prs).filter(x => x.estado);
      return `<ul class="pr-lista">${prs.map(x => {
          const rev = M.eventos.filter(e => e.pr === x.numero && e.resultado && e.ms <= ate);
          return `<li><b>PR #${x.numero}</b> · ${esc(x.titulo)}<br>
            ${rev.map(e => `<span class="rod ${e.resultado}">${e.rodada}ª · ${e.resultado === "aprovado" ? "aprovado" : "pediu mudança"}</span>`).join("") || '<span class="nota">sem revisão ainda</span>'}
            ${x.estado === "mesclado" ? '<span class="rod mesclado">mesclado</span>' : ""}</li>`; }).join("") || '<li class="nota">Nenhum PR aberto.</li>'}</ul>
        <h3>O que ele fez <span class="nota">· ${E.metricas.rodadas} ${E.metricas.rodadas === 1 ? "rodada" : "rodadas"} de revisão</span></h3>${fitaDe(meus.filter(e => e.tipo === "revisao"))}`;
    }
    case "ci": {
      const runs = M.eventos.filter(e => (e.tipo === "ci" || e.tipo === "deploy") && e.ms <= ate);
      const m = M.estadoDoDia(ate).metricas;
      return `<div class="numeros"><div><b>${m.ciTotal ? `${m.ciVerde}/${m.ciTotal}` : "—"}</b><span>execuções verdes</span></div><div><b>${m.deploys}</b><span>deploys</span></div></div>
        <ol class="fita">${runs.map(e => `<li><time>${hhmm(e.ms)}</time><span class="t o-${e.origem}">${e.ci ? `<span class="rod ${e.ci}">${e.ci}</span> ` : ""}${esc(e.texto)}</span></li>`).join("") || '<li><span></span><span class="t">Nenhuma execução até agora.</span></li>'}</ol>`;
    }
    case "pesquisas":
      return `<p class="nota" style="margin:0">Buscas, leituras e o que ele levou para alguém.</p>${fitaDe(meus.filter(e => ["busca", "leitura", "entrega", "nota"].includes(e.tipo)))}`;
    case "avisos":
      return `<p class="nota" style="margin:0">Cada vez que o Mensageiro sai do tubo com um envelope.</p>${fitaDe(meus)}`;
    case "plantao": {
      const e = M.equipe.escritorio;
      return `<ul class="lista"><li><b>Abre:</b> ${esc(e.expediente.abre)} · <b>fecha:</b> ${esc(e.expediente.fecha)}</li>
          <li><b>Almoço:</b> ${esc(e.expediente.almoco.join(" às "))}</li>
          <li><b>De noite:</b> ronda de lanterna pela portaria, café e servidores.</li></ul>
        <h3>Dias sem expediente</h3><ul class="lista">${Object.entries(e.folgas || {}).map(([x, m]) => `<li>${diaMes(x)}: ${esc(m)}</li>`).join("")}<li>Sábados e domingos</li></ul>`;
    }
  }
  return "";
}

// ------------------------------------------------------------ abrir um ticket (protótipo: nada é enviado)
const form = $("#form-ticket");
$("#ticket-desc").addEventListener("input", e => { $("#ticket-conta").textContent = `${numero(e.target.value.length)} / ${numero(1000)}`; });
form.addEventListener("submit", e => {
  e.preventDefault();
  const r = $("#resposta"), txt = $("#ticket-titulo").value.trim();
  r.hidden = false; r.classList.remove("erro");
  if ($("#site").value) { r.textContent = "Recebido."; return; }
  if (!txt) { r.classList.add("erro"); r.textContent = "Escreva um título antes de enviar."; $("#ticket-titulo").focus(); return; }
  if (S.replay) { r.textContent = "Protótipo: nada foi enviado. Você está no replay; volte ao vivo para ver o escritório reagir."; return; }
  S.sug = performance.now(); S.seguir = true;
  r.textContent = "Protótipo: nada foi enviado. No site de verdade, o Mensageiro recebe e deixa na caixa de entrada do Camps. Repare no escritório.";
  $("#palco").scrollIntoView({ behavior: reduz.matches ? "auto" : "smooth", block: "center" });
});

// ------------------------------------------------------------ simulação de horário (só no protótipo)
function simula(v) {
  const D = S.M.D;
  if (v === "agora") S.sim = null;
  else if (v === "folga") { let iso = D; for (let i = 1; i < 8; i++) { const x = new Date(Date.parse(D + "T12:00:00Z") + i * 864e5).toISOString().slice(0, 10); if (!S.M.diaUtil(x)) { iso = x; break; } } S.sim = { base: msDe(iso, "14:00"), desde: performance.now() }; }
  else S.sim = { base: msDe(D, v), desde: performance.now() };
  if (S.replay) saiReplay();
  S.saltar = true; S.seguir = true;
  $$("[data-sim]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.sim === v)));
}
$$("[data-sim]").forEach(b => b.addEventListener("click", () => simula(b.dataset.sim)));

// ------------------------------------------------------------ tema
function tema(v) {
  if (v === "light" || v === "dark") document.documentElement.dataset.theme = v; else delete document.documentElement.dataset.theme;
  $$("[data-tema]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.tema === (v === "light" || v === "dark" ? v : "auto"))));
}
$$("[data-tema]").forEach(b => b.addEventListener("click", () => tema(b.dataset.tema)));

// ------------------------------------------------------------ início
let espera;
window.addEventListener("resize", () => { clearTimeout(espera); espera = setTimeout(aplicaMedidas, 80); });
carrega().catch(err => {
  console.error(err);
  $("#estado").textContent = "Não consegui ler os dados do escritório (dados/equipe.json e dados/dia-demo.json).";
});

window.__escritorio = S;
