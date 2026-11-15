// Motor de cena do escritório.
// Entra: o relógio (ms) e os dados de dados/*.json. Sai: um "quadro" — quem
// está em que lugar, fazendo o quê, com que balão, que luz, que céu, o quadro
// de tickets e o estado do CI. Não toca no DOM nem desenha nada.
// Nenhum balão é inventado: os do expediente são os eventos do JSON, com a
// origem deles; os de fora do expediente são a agenda e os números do dia, e
// dizem isso.
//
// Dia de demonstração: quando o JSON diz "demonstracao", o dia de exemplo é
// tocado no relógio de hoje (10:30 de hoje mostra as 10:30 do exemplo). A
// página avisa isso o tempo todo.

import { lugar, LUGARES, rota, salaEm, PORTA, SALAS, SALA, RONDA, ANDARES, MESAS } from "./planta.js";

export const FUSO = "America/Sao_Paulo";
const SEGURA = 8 * 60e3;      // um balão fica no ar até 8 min (relógio do dia) depois do evento
const ATIVO = 10 * 60e3;      // um robô "trabalha" até 10 min depois do próprio evento
const AVISO = 4 * 60e3;       // o Mensageiro fica fora do tubo 4 min
const CICLO = 6500;           // fora do expediente, cada fala dura 6,5 s

export const VELOCIDADES = {
  "1x":   { nome: "1×",     k: 1,   min: 0,   max: Infinity },
  "6x":   { nome: "6×",     k: 6,   min: 0,   max: Infinity },
  "60x":  { nome: "60×",    k: 60,  min: 0,   max: Infinity },
  maximo: { nome: "Máximo", k: 240, min: 900, max: 2600 },
};

// ------------------------------------------------------------ relógio de São Paulo
const fmt = new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, year: "numeric", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", second: "2-digit", weekday: "short", hourCycle: "h23" });
export function campos(ms) {
  const p = Object.fromEntries(fmt.formatToParts(new Date(ms)).map(x => [x.type, x.value]));
  const h = +p.hour % 24, m = +p.minute, s = +p.second;
  return { data: `${p.year}-${p.month}-${p.day}`, h, m, s, min: h * 60 + m + s / 60, dia: p.weekday.replace(".", "") };
}
const dois = n => String(n).padStart(2, "0");
export const hhmmss = ms => { const c = campos(ms); return `${dois(c.h)}:${dois(c.m)}:${dois(c.s)}`; };
export const hhmm = ms => hhmmss(ms).slice(0, 5);
export const diaMes = iso => `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;
export const semana = iso => new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC", weekday: "long" }).format(new Date(iso + "T12:00:00Z"));
export const semanaCurta = iso => semana(iso).replace("-feira", "");
export const msDe = (iso, hm) => Date.parse(`${iso}T${hm.length === 5 ? hm + ":00" : hm}-03:00`);
const minDe = hm => +hm.slice(0, 2) * 60 + +hm.slice(3, 5);
const somaDias = (iso, n) => new Date(Date.parse(iso + "T12:00:00Z") + n * 864e5).toISOString().slice(0, 10);
export function duracaoTexto(seg) {
  seg = Math.round(seg);
  const h = Math.floor(seg / 3600), m = Math.floor((seg % 3600) / 60), s = seg % 60;
  if (h) return m ? `${h} h ${m} min` : `${h} h`;
  return m ? (s ? `${m} min ${s} s` : `${m} min`) : `${s} s`;
}
export const numero = n => Number(n).toLocaleString("pt-BR");
export const dinheiro = v => "US$ " + Number(v).toFixed(2).replace(".", ",");

// ------------------------------------------------------------ céu da hora
const CEU = [
  [0,    "#0a0f2c", "#18214b", 1,   0],
  [300,  "#0c1236", "#3a2f66", 1,   0],
  [345,  "#1d2150", "#e0803f", .8,  .08],
  [390,  "#36437f", "#ef9546", .3,  .3],
  [430,  "#6c9fd8", "#f5c38a", 0,   .75],
  [480,  "#5aa0e8", "#bfe1f8", 0,   1],
  [990,  "#4e95e0", "#c3e2f7", 0,   1],
  [1050, "#5b7cc4", "#f1b06a", 0,   .8],
  [1110, "#383d82", "#de6d58", .2,  .4],
  [1170, "#151946", "#3a2f66", .8,  .08],
  [1260, "#0a0f2c", "#18214b", 1,   0],
  [1440, "#0a0f2c", "#18214b", 1,   0],
];
const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
export function ceu(min) {
  let i = 0;
  while (i < CEU.length - 2 && CEU[i + 1][0] <= min) i++;
  const a = CEU[i], b = CEU[i + 1], t = Math.max(0, Math.min(1, (min - a[0]) / (b[0] - a[0])));
  return {
    alto: mix(hex(a[1]), hex(b[1]), t), horizonte: mix(hex(a[2]), hex(b[2]), t),
    estrelas: a[3] + (b[3] - a[3]) * t, dia: a[4] + (b[4] - a[4]) * t, min,
    sol: min > 360 && min < 1110 ? (min - 360) / 750 : null,
    lua: min < 360 || min > 1110 ? ((min + 330) % 1440) / 690 : null,
  };
}

// ------------------------------------------------------------ o motor
export function criaMotor(equipeJson, dia) {
  const esc = equipeJson.escritorio, membros = equipeJson.equipe;
  const porId = Object.fromEntries(membros.map(p => [p.id, p]));
  const D = dia.data, DEMO = !!(dia.demonstracao || equipeJson.demonstracao);
  const eventos = dia.eventos.map((e, i) => ({ ...e, i, ms: Date.parse(e.t), ateMs: e.ate ? Date.parse(e.ate) : null }));
  const corrida = eventos;
  const INI = eventos[0].ms, FIM = eventos[eventos.length - 1].ms;
  const capitulos = (dia.capitulos || []).map(c => ({ ...c, ms: Date.parse(c.t) }));
  const ABRE = minDe(esc.expediente.abre), FECHA = minDe(esc.expediente.fecha), ALM = esc.expediente.almoco.map(minDe);
  const corpo = id => ((porId[id] || {}).visual || {}).corpo || "humano";
  const robo = id => (porId[id] || {}).tipo === "robo";
  const nomeDe = id => (porId[id] || { nome: id }).nome;
  const chegadaDe = Object.fromEntries(eventos.filter(e => e.tipo === "chegada").map(e => [e.quem, e.ms]));
  const saidaDe = Object.fromEntries(eventos.filter(e => e.tipo === "saida").map(e => [e.quem, e.ms]));
  const vagaDe = Object.fromEntries((equipeJson.vagas || []).map(v => [v.mesa, v]));

  function diaUtil(iso) {
    const d = new Date(iso + "T12:00:00Z").getUTCDay();
    return (esc.dias_uteis || [1, 2, 3, 4, 5]).includes(d) && !(esc.folgas || {})[iso];
  }
  function proximoExpediente(c) {
    let iso = c.data;
    if (diaUtil(iso) && c.min < ABRE) return iso;
    for (let i = 1; i < 30; i++) { iso = somaDias(c.data, i); if (diaUtil(iso)) return iso; }
    return null;
  }
  // No modo demonstração, o dia de exemplo toca no relógio de hoje.
  const noDia = ms => { const c = campos(ms); return msDe(D, "00:00") + (c.h * 3600 + c.m * 60 + c.s) * 1000 + (ms % 1000); };

  function periodo(ms, replay) {
    if (replay) return { nome: "replay", c: campos(ms), md: ms };
    const c = campos(ms);
    if (!diaUtil(c.data)) return { nome: "folga", c, md: null, motivo: (esc.folgas || {})[c.data] || semana(c.data) };
    let md;
    if (DEMO) md = noDia(ms);
    else if (c.data === D) md = ms;
    else return { nome: c.min >= ABRE && c.min < FECHA ? "sem-dados" : "fechado", c, md: null };
    if (md < INI || md > FIM) return { nome: "fechado", c, md };
    return { nome: c.min >= ALM[0] && c.min < ALM[1] ? "almoco" : "expediente", c, md };
  }

  // ---------------------------------------------------------- o dia até um momento
  function ate(md) {
    let n = 0;
    while (n < corrida.length && corrida[n].ms <= md) n++;
    return n;
  }
  function estadoDoDia(md) {
    const n = ate(md), vistos = corrida.slice(0, n);
    const ult = {}, local = {}, recarga = {};
    let aberto = false;
    const tickets = Object.fromEntries((dia.tickets || []).map(t => [t.id, { ...t }]));
    const prs = Object.fromEntries((dia.prs || []).map(p => [p.numero, { ...p, estado: p.estado ?? null, ci: null, rodadas: 0 }]));
    let ci = null, deploy = null, custo = 0, cafes = 0, ciVerde = 0, ciTotal = 0, rodadas = 0, entregues = 0, mesclados = 0, deploys = 0;
    for (const e of vistos) {
      ult[e.quem] = e;
      if (e.onde) { local[e.quem] = e; for (const x of e.com || []) local[x] = e; }
      else if (local[e.quem] && (local[e.quem].ateMs == null || e.ms >= local[e.quem].ateMs)) delete local[e.quem];   // voltou ao posto
      if (e.tipo === "abertura") aberto = true;
      if (e.tipo === "fechamento") aberto = false;
      if (e.tipo === "recarga") recarga[e.quem] = true;
      if (e.tipo === "acorda") recarga[e.quem] = false;
      if (e.custo_usd) custo += e.custo_usd;
      if (e.tipo === "cafe") cafes++;
      if (e.ticket != null) {
        const t = tickets[e.ticket] || (tickets[e.ticket] = { id: e.ticket, titulo: e.titulo || `Ticket ${e.ticket}`, estado: "a fazer", novo: true });
        if (e.titulo) t.titulo = e.titulo;
        const est = e.tipo === "ticket" ? e.estado : e.estado_ticket;
        if (est) t.estado = est;
      }
      if (e.pr != null) {
        const p = prs[e.pr] || (prs[e.pr] = { numero: e.pr, titulo: `PR ${e.pr}`, estado: "aberto", ci: null, rodadas: 0 });
        if (e.tipo === "pr" && e.estado) { p.estado = e.estado; if (e.estado === "mesclado") mesclados++; }
        if (e.tipo === "ci") { p.ci = e.ci; if (e.ci !== "rodando") { ciTotal++; if (e.ci === "verde") ciVerde++; } }
        if (e.resultado) { p.rodadas++; rodadas++; p.revisao = e.resultado; }
      }
      if (e.tipo === "ci") ci = { estado: e.ci, pr: e.pr, ms: e.ms };
      if (e.tipo === "deploy") {
        deploy = { versao: e.versao, ms: e.ms, no_ar: e.ci === "verde" };
        if (e.ci === "verde") { deploys++; ci = { estado: "verde", pr: null, ms: e.ms, deploy: e.versao }; }
        for (const id of e.tickets || []) if (tickets[id]) { if (tickets[id].estado !== "publicado") entregues++; tickets[id].estado = "publicado"; }
      }
    }
    return { n, vistos, ult, local, recarga, aberto, tickets, prs, ci, deploy,
      metricas: { custo, cafes, ciVerde, ciTotal, rodadas, entregues, mesclados, deploys } };
  }

  function presente(id, md) {
    const m = porId[id];
    if (chegadaDe[id] != null && md < chegadaDe[id]) return false;
    if (saidaDe[id] != null && md >= saidaDe[id]) return false;
    if (m.tipo === "humano" && m.id !== "vigia" && chegadaDe[id] == null) return false;
    return true;
  }
  // Mesa descoberta: o dono já trabalha aqui (chegou num dia anterior) ou já chegou hoje.
  function mesas(md, isoHoje) {
    const r = {};
    for (const m of MESAS) {
      const dono = membros.find(p => p.posto === m.id);
      let ocupada = false;
      if (dono) {
        if (md == null) ocupada = dono.desde <= isoHoje;
        else ocupada = dono.desde < D || chegadaDe[dono.id] == null || md >= chegadaDe[dono.id];
      }
      const vaga = vagaDe[m.id] || (dono && !ocupada ? { mesa: m.id, para: dono.nome, previsto: "hoje" } : null);
      r[m.id] = { ocupada, dono: dono ? dono.id : null, vaga };
    }
    return r;
  }

  function altDe(id, lug, carregando) {
    const c = corpo(id);
    if (c === "drone") return carregando || lug === "doca" ? LUGARES.doca.alt : lug === "estante" ? LUGARES.estante.alt : 30;
    if (c === "pernas") return /^m\d/.test(lug) ? 21 : 0;
    if (c === "tubo") return LUGARES.tubo.alt;
    if (lug === "sofa") return 6;
    return 0;
  }

  const balaoDe = (e, sala) => ({ chave: `e${e.i}`, sala, quem: e.quem, origem: e.origem, texto: e.texto, ms: e.ms, tipo: e.tipo });
  const fala = (quem, texto, origem, sala) => ({ chave: `${origem}:${quem}:${texto}`, sala, quem, origem, texto, ms: null });

  function luzes(modo) { const l = {}; for (const s of SALAS) l[s.id] = modo; return l; }

  // ---------------------------------------------------------- o quadro
  function quadro(ms, op = {}) {
    const per = periodo(ms, op.replay);
    const c = per.c, md = per.md;
    const q = { ms, md, per: per.nome, rotulo: "", replay: !!op.replay, demo: DEMO, min: c.min, ceu: ceu(c.min), pessoas: {}, baloes: [],
      luz: {}, estado: "", placa: null, fita: [], fitaRotulo: "No escritório agora", fitaNota: "", ativa: "portaria",
      tickets: null, ci: null, deploy: null, mesas: null, tv: false, metricas: null, pendencias: [], dia: null };
    const sug = op.sugestao;
    const ciclo = Math.floor(ms / CICLO);
    const isoHoje = c.data;
    const prox = proximoExpediente(c);
    const proxCurto = prox ? (prox === c.data ? `hoje, às ${esc.expediente.abre}` : `${semanaCurta(prox)}, ${diaMes(prox)}, às ${esc.expediente.abre}`) : "";

    if (per.nome === "fechado" && md != null) return fora(q, per, c, md, prox, proxCurto, ciclo, sug, estadoDoDia(md));
    // ---- no meio do dia (ao vivo ou replay)
    if (md != null) {
      const E = estadoDoDia(md);
      q.dia = E; q.tickets = E.tickets; q.ci = E.ci; q.metricas = E.metricas; q.mesas = mesas(md, isoHoje);
      q.deploy = E.deploy && md - E.deploy.ms < 3 * 60e3 ? E.deploy : null;
      const dentro = md >= INI && md <= FIM;
      // quem está onde
      const vagaIdx = {};
      for (const m of membros) {
        if (!presente(m.id, md)) continue;
        if (m.desde > D && !DEMO) continue;
        const R = robo(m.id), carregando = R && (!E.aberto || E.recarga[m.id]);
        const L = E.local[m.id];
        let lug = m.posto;
        if (L && L.onde && (L.ateMs == null || md < L.ateMs) && !carregando) lug = L.onde;
        let idx = 0;
        if (L && L.onde === lug) idx = L.quem === m.id ? 0 : (L.com || []).indexOf(m.id) + 1;
        else { idx = vagaIdx[lug] || 0; }
        vagaIdx[lug] = (vagaIdx[lug] || 0) + 1;
        const pos = lugar(lug, idx) || lugar(m.posto);
        const u = E.ult[m.id];
        let estado = "parado", situ = "parado";
        if (carregando) { estado = "carregando"; situ = "na recarga"; }
        else if (!R) {
          if (lug === "sofa") { estado = "jogando"; situ = "no sofá, jogando"; }
          else if (lug === "cafe") { estado = "cafe"; situ = "no café"; }
          else if (/^m\d/.test(lug) && E.aberto) { estado = "trabalhando"; situ = "na mesa"; }
          else if (lug === "planejamento") situ = "na reunião";
          else if (m.id === "vigia") situ = "na portaria";
        } else if (u && md - u.ms < (corpo(m.id) === "tubo" ? AVISO : ATIVO) && u.tipo !== "recarga") { estado = "trabalhando"; situ = "trabalhando"; }
        else if (corpo(m.id) === "tubo") situ = "no tubo";
        if (lug === "planejamento" && !carregando) { estado = R ? "parado" : "parado"; situ = "na reunião"; }
        q.pessoas[m.id] = { ...pos, alt: altDe(m.id, lug, carregando), estado, situ,
          leva: !!(L && L.tipo === "entrega" && L.quem === m.id && lug === L.onde && corpo(m.id) === "rodas"),
          scan: corpo(m.id) === "drone" && lug === "estante" && estado === "trabalhando" };
      }
      q.tv = Object.values(q.pessoas).some(p => p.estado === "jogando");
      // balões: o último evento de cada sala, se recente (ou o último de todos)
      const comTexto = E.vistos.filter(e => e.texto && q.pessoas[e.quem]);
      const ultimo = comTexto[comTexto.length - 1];
      const porSala = {};
      for (const e of comTexto) porSala[q.pessoas[e.quem].sala] = e;
      for (const [sala, e] of Object.entries(porSala)) {
        if (e === ultimo || md - e.ms < SEGURA) {
          q.baloes.push(balaoDe(e, sala));
          if (["humano", "agente"].includes(e.origem)) q.pessoas[e.quem].fala = true;
        }
      }
      q.ativa = ultimo && q.pessoas[ultimo.quem] ? q.pessoas[ultimo.quem].sala : "portaria";
      // luz
      const escuro = q.ceu.dia < .3;
      if (dentro && E.aberto) { q.luz = luzes("acesa"); }
      else { q.luz = luzes(escuro ? "apagada" : "penumbra"); q.luz.portaria = "acesa"; }
      q.luz.servidores = q.luz.servidores === "acesa" ? "acesa" : "servidor";
      q.pendencias = pendencias(E);
      q.fita = E.vistos.slice(-8).reverse().map(e => balaoDe(e, null));
      // rótulo e estado
      if (op.replay) {
        q.rotulo = "REPLAY";
        q.fitaRotulo = "No replay, até agora";
        q.estado = DEMO ? `Replay do dia de exemplo (${semana(D)}, ${diaMes(D)}). Não é ao vivo.` : `Replay de ${semana(D)}, ${diaMes(D)}. Não é ao vivo.`;
      } else {
        q.rotulo = per.nome === "almoco" ? "ALMOÇO" : "EXPEDIENTE";
        q.fitaRotulo = "Hoje, até agora";
        q.estado = per.nome === "almoco" ? "Hora do almoço. Os robôs seguem com o que estava na fila." : "Expediente. Cada um no seu lugar; quem fez algo há pouco tem balão.";
        if (DEMO) q.estado += " Dia de exemplo, no relógio de hoje.";
      }
      reacaoAoSite(q, sug, op.replay, true);
      return q;
    }
    return fora(q, per, c, md, prox, proxCurto, ciclo, sug, null);
  }

  // ---- fora do expediente (fechado, folga, sem dados)
  function fora(q, per, c, md, prox, proxCurto, ciclo, sug, E) {
    const folga = per.nome === "folga", noite = q.ceu.dia < .3;
    q.rotulo = folga ? "FOLGA" : per.nome === "sem-dados" ? "SEM DADOS" : "FECHADO";
    q.luz = luzes(noite ? "apagada" : "penumbra"); q.luz.portaria = "acesa"; q.luz.servidores = "servidor";
    if (!E) { q.mesas = mesas(null, c.data); }
    // quem fica: o Vigia e os robôs na recarga (nos postos)
    for (const m of membros) {
      if (m.id === "vigia") continue;
      if (m.tipo !== "robo") { if (E && presente(m.id, md)) { /* ainda não saiu */ } else continue; }
      if (E ? !presente(m.id, md) : m.desde > c.data) continue;
      const pos = lugar(m.posto);
      if (m.tipo !== "robo") { q.pessoas[m.id] = { ...pos, alt: 0, estado: "trabalhando", situ: "na mesa" }; continue; }
      q.pessoas[m.id] = { ...pos, alt: altDe(m.id, m.posto, true), estado: "carregando", situ: "na recarga" };
    }
    q.pessoas.vigia = { ...lugar("portaria"), alt: 0, estado: "parado", situ: "de plantão" };
    let naRonda = false;
    if (noite && !(sug != null && sug < 12e3)) {
      const fase = (q.ms / 1000) % 64;
      const parada = fase < 36 ? null : fase < 46 ? RONDA[0] : fase < 54 ? RONDA[1] : fase < 60 ? RONDA[2] : null;
      if (parada) { naRonda = true; Object.assign(q.pessoas.vigia, { sala: parada.sala, x: parada.x, y: ANDARES[SALA[parada.sala].andar].pe, situ: "de ronda" }); }
      q.pessoas.vigia.lanterna = true;
    }
    q.ativa = "portaria";
    const exemplo = DEMO ? "No dia de exemplo" : (E ? "Hoje" : "No último expediente");
    const numerosDoDia = (() => {
      const Ef = E || estadoDoDia(FIM);
      const m = Ef.metricas;
      return `${exemplo}: ${m.entregues} ${m.entregues === 1 ? "ticket entregue" : "tickets entregues"} e ${m.deploys} ${m.deploys === 1 ? "deploy" : "deploys"}.`;
    })();
    const antes = md != null && md < INI;
    let falas;
    if (folga) falas = [fala("vigia", `Hoje é ${per.motivo}: o escritório não abre.`, "agenda", "portaria"),
                        fala("vigia", `A equipe volta ${proxCurto}.`, "agenda", "portaria"),
                        fala("vigia", numerosDoDia, "numeros", "portaria")];
    else if (per.nome === "sem-dados") falas = [fala("vigia", `O registro de hoje ainda não chegou. O último é de ${diaMes(D)}.`, "agenda", "portaria")];
    else if (antes || (md == null && c.min < ABRE)) falas = [fala("vigia", `O escritório abre às ${esc.expediente.abre}.`, "agenda", "portaria"),
                        fala("vigia", "Os robôs ficam na recarga até a abertura.", "agenda", "portaria")];
    else falas = [fala("vigia", `Escritório fechado. Abre ${proxCurto}.`, "agenda", "portaria"),
                  fala("vigia", numerosDoDia, "numeros", "portaria")];
    const atual = falas[ciclo % falas.length];
    if (!naRonda) q.baloes.push(atual);
    q.fita = falas.map(f => ({ ...f, atual: f === atual }));
    q.fitaRotulo = "Na portaria";
    q.fitaNota = falas.some(f => f.origem === "numeros") ? (DEMO ? "Os números vêm do dia de exemplo." : "Os números vêm do registro do dia.") : "";
    q.estado = folga ? `Folga: ${per.motivo}. A equipe volta ${proxCurto}.` : per.nome === "sem-dados" ? "Dia útil, e o registro de hoje ainda não chegou." : `Escritório fechado. Abre ${proxCurto}.`;
    if (folga && prox) q.placa = `A equipe volta ${proxCurto}`;
    if (E) { q.dia = E; q.tickets = E.tickets; q.ci = E.ci; q.metricas = E.metricas; q.mesas = mesas(md, c.data); q.pendencias = pendencias(E); }
    else { const Ef = estadoDoDia(FIM); q.tickets = Ef.tickets; q.ci = Ef.ci; q.dia = null; }
    reacaoAoSite(q, sug, false, false);
    return q;
  }

  // O que está esperando alguém, tirado do estado do dia.
  function pendencias(E) {
    const r = [];
    for (const p of Object.values(E.prs)) {
      if (!p.estado || p.estado === "mesclado") continue;
      if (p.ci === "rodando") r.push({ tipo: "ci", texto: `aguardando o CI do PR #${p.numero}` });
      else if (p.ci === "vermelho") r.push({ tipo: "vermelho", texto: `CI vermelho no PR #${p.numero}` });
      else if (p.revisao === "mudancas") r.push({ tipo: "mudanca", texto: `PR #${p.numero} com pedido de mudança` });
      else if (p.revisao !== "aprovado") r.push({ tipo: "revisao", texto: `PR #${p.numero} esperando revisão` });
    }
    return r;
  }

  function reacaoAoSite(q, sug, replay, dentro) {
    if (sug == null || replay || sug > 12e3) return;
    if (dentro && q.pessoas.mensageiro) {
      q.baloes = q.baloes.filter(b => b.sala !== q.pessoas.mensageiro.sala);
      Object.assign(q.pessoas.mensageiro, { estado: "trabalhando", situ: "com um envelope" });
      q.baloes.push(fala("mensageiro", "Chegou um pedido pelo site. Fica na caixa de entrada até o Camps ler.", "visitante", q.pessoas.mensageiro.sala));
    } else {
      q.baloes = q.baloes.filter(b => b.sala !== "portaria");
      q.baloes.push(fala("vigia", "Chegou um pedido pelo site. Fica na caixa de entrada até a abertura.", "visitante", "portaria"));
    }
  }

  return { equipe: equipeJson, membros, porId, dia, D, DEMO, eventos, corrida, capitulos, INI, FIM, nomeDe, corpo, robo,
    periodo, proximoExpediente, estadoDoDia, quadro, diaUtil };
}

// ------------------------------------------------------------ replay
// Anda pelo dia evento a evento. O relógio mostra sempre o horário do evento;
// as velocidades encurtam as esperas, nunca mudam a ordem.
export class Replay {
  constructor(motor, vel = "maximo") {
    this.c = motor.corrida; this.INI = motor.INI; this.FIM = motor.FIM;
    this.i = 0; this.p = 0; this.vel = vel; this.pausado = false; this.parado = 0;
  }
  passo(i, vel = this.vel) {
    const a = this.c[i], b = this.c[i + 1];
    if (!b) return Infinity;
    const gap = b.ms - a.ms, v = VELOCIDADES[vel];
    return Math.max(v.min, Math.min(v.max, gap / v.k));
  }
  get fim() { return this.i >= this.c.length - 1; }
  avanca(dt) {
    if (this.pausado) return;
    if (this.fim) { this.parado += dt; return; }
    while (dt > 0 && !this.fim) {
      const d = this.passo(this.i), resta = (1 - this.p) * d;
      if (dt < resta) { this.p += dt / d; dt = 0; } else { dt -= resta; this.i++; this.p = 0; }
    }
  }
  ms() {
    const a = this.c[this.i], b = this.c[this.i + 1];
    return b ? a.ms + (b.ms - a.ms) * this.p : a.ms;
  }
  irPara(ms) {
    let i = 0;
    while (i < this.c.length - 1 && this.c[i + 1].ms <= ms) i++;
    const a = this.c[i], b = this.c[i + 1];
    this.i = i; this.p = b && b.ms > a.ms ? Math.max(0, Math.min(.999, (ms - a.ms) / (b.ms - a.ms))) : 0;
    this.parado = 0;
  }
  proximo() { if (!this.fim) { this.i++; this.p = 0; this.parado = 0; } }
  recomeca() { this.i = 0; this.p = 0; this.parado = 0; this.pausado = false; }
  duracao(vel) { let s = 0; for (let i = 0; i < this.c.length - 1; i++) s += this.passo(i, vel); return s; }
  progresso() { return (this.ms() - this.INI) / Math.max(1, this.FIM - this.INI); }
}

// ------------------------------------------------------------ locomoção
// Quem anda de um lugar para outro. Fica fora da cena para que a troca de
// camada visual não perca ninguém no meio do caminho.
export class Locomocao {
  constructor() { this.p = {}; this.vel = 62; }   // px da cena por segundo
  define(pessoas, instantaneo = false) {
    const ids = new Set([...Object.keys(this.p), ...Object.keys(pessoas)]);
    for (const id of ids) {
      const alvo = pessoas[id];
      let s = this.p[id];
      if (!alvo) {
        if (!s || s.saindo) continue;
        if (instantaneo) { delete this.p[id]; continue; }
        s.saindo = true; s.chave = "porta"; s.rota = rota(s, PORTA); s.info = { ...s.info, fala: false };
        continue;
      }
      const chave = `${alvo.sala}:${alvo.x}:${alvo.y}`;
      if (!s) {
        const nasce = instantaneo || alvo.estado === "carregando" || id === "mensageiro";
        s = this.p[id] = { id, x: nasce ? alvo.x : PORTA.x, y: nasce ? alvo.y : PORTA.y, dir: 1, rota: [],
          chave: null, opacidade: nasce ? 1 : 0, tempo: 0, alt: alvo.alt || 0 };
      }
      s.saindo = false; s.info = alvo;
      if (s.chave !== chave) {
        s.chave = chave;
        if (instantaneo) { s.x = alvo.x; s.y = alvo.y; s.rota = []; s.alt = alvo.alt || 0; }
        else s.rota = rota(s, alvo);
      }
    }
  }
  atualiza(dt) {
    for (const [id, s] of Object.entries(this.p)) {
      let passo = this.vel * dt / 1000;
      while (passo > 0 && s.rota.length) {
        const a = s.rota[0], dx = a.x - s.x, dy = a.y - s.y, d = Math.hypot(dx, dy);
        if (Math.abs(dx) > .01) s.dir = Math.sign(dx);
        if (d <= passo) { s.x = a.x; s.y = a.y; s.rota.shift(); passo -= d; }
        else { s.x += dx / d * passo; s.y += dy / d * passo; passo = 0; }
      }
      s.andando = s.rota.length > 0;
      // altura (drone, aranha na mesa): vai e volta suave; andando, o drone voa a 30 px
      const alvoAlt = s.andando ? ((s.info || {}).alt > 0 && s.info.alt < 30 ? 0 : (s.info || {}).alt > 0 ? 30 : 0) : (s.info || {}).alt || 0;
      const vAlt = 40 * dt / 1000;
      s.alt = Math.abs(alvoAlt - s.alt) <= vAlt ? alvoAlt : s.alt + Math.sign(alvoAlt - s.alt) * vAlt;
      s.tempo += dt;
      s.opacidade = s.saindo && s.rota.length < 2 ? Math.max(0, s.opacidade - dt / 500) : Math.min(1, s.opacidade + dt / 400);
      s.sala = salaEm(s.x, s.y);
      if (s.saindo && !s.andando) delete this.p[id];
    }
  }
  ordem() { return Object.values(this.p).sort((a, b) => (a.alt > 0) - (b.alt > 0) || a.y - b.y || a.x - b.x); }
}

export { SALA };
