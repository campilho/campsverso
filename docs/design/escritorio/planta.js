// Planta do escritório, em pixels da cena 2D (640 × 360).
// Fonte única do espaço: a cena desenha a partir dela e o motor usa os
// lugares e as rotas. Nada aqui é dado do dia; dados vêm só de dados/*.json.

export const W = 640, H = 360;

// Dois andares. "teto" e "base" limitam a sala; "pe" é a linha dos pés.
export const ANDARES = {
  1: { teto: 24, chao: 156, pe: 166, base: 172 },   // superior: desenvolvimento
  0: { teto: 180, chao: 312, pe: 322, base: 328 },  // térreo: portaria, café, servidores
};

export const SALAS = [
  { id: "escada",       nome: "Escada",          andar: -1, x0: 4,   x1: 52  },
  { id: "dev",          nome: "Desenvolvimento", andar: 1,  x0: 56,  x1: 488 },
  { id: "planejamento", nome: "Planejamento",    andar: 1,  x0: 492, x1: 636 },
  { id: "portaria",     nome: "Portaria",        andar: 0,  x0: 56,  x1: 160 },
  { id: "cafe",         nome: "Café e jogos",    andar: 0,  x0: 164, x1: 436 },
  { id: "servidores",   nome: "Servidores",      andar: 0,  x0: 440, x1: 636 },
];
export const SALA = Object.fromEntries(SALAS.map(s => [s.id, s]));

export function retSala(id) {
  const s = SALA[id];
  if (s.andar === -1) return { x: s.x0, y: ANDARES[1].teto, w: s.x1 - s.x0, h: ANDARES[0].base - ANDARES[1].teto };
  const a = ANDARES[s.andar];
  return { x: s.x0, y: a.teto, w: s.x1 - s.x0, h: a.base - a.teto };
}

// Paradas da câmera no celular (deslizar). As salas largas têm duas paradas.
export const PARADAS = [
  { id: "portaria",   sala: "portaria" },
  { id: "cafe",       sala: "cafe", x: 236, nome: "Café" },
  { id: "jogos",      sala: "cafe", x: 372, nome: "Café · sofá e videogame" },
  { id: "servidores", sala: "servidores" },
  { id: "mesas",      sala: "dev", x: 150, nome: "Desenvolvimento · mesas 1 a 3" },
  { id: "vagas",      sala: "dev", x: 380, nome: "Desenvolvimento · vagas e estante" },
  { id: "planejamento", sala: "planejamento" },
];

// Seis mesas no desenvolvimento. Quem chega ganha uma; as vazias ficam cobertas.
export const MESAS = [
  { id: "m1", x: 88 }, { id: "m2", x: 148 }, { id: "m3", x: 208 },
  { id: "m4", x: 268 }, { id: "m5", x: 328 }, { id: "m6", x: 388 },
];
export const MESA = Object.fromEntries(MESAS.map(m => [m.id, m]));

// Estante com a doca do drone em cima e o tubo pneumático do Mensageiro.
export const ESTANTE = { x0: 414, x1: 448, topo: 54 };        // topo em y absoluto
export const TUBO = { x: 470, peitoril: 98 };                   // borda de baixo da boca da estação, em y absoluto
export const DEPLOY = { x: 478 };                               // console de publicação, nos servidores
export const SOFA = { x: 392 };
export const TV = { x: 392 };

// Lugares com nome, para os eventos dizerem "onde". "vagas" separa quem
// divide o mesmo lugar. "alt" ergue o personagem (drone, aranha na mesa).
export const LUGARES = {
  ...Object.fromEntries(MESAS.map(m => [m.id, { sala: "dev", x: m.x }])),
  estante:      { sala: "dev", x: 431, alt: 44 },
  doca:         { sala: "dev", x: 431, alt: ANDARES[1].pe - (ESTANTE.topo - 4) },
  tubo:         { sala: "dev", x: TUBO.x, alt: ANDARES[1].pe - TUBO.peitoril - 3 },
  planejamento: { sala: "planejamento", x: 566, vagas: [0, -30, 30, -58, 56] },
  cafe:         { sala: "cafe", x: 232, vagas: [0, 28, -26, 54] },
  sofa:         { sala: "cafe", x: SOFA.x, vagas: [0, -16, 16] },
  portaria:     { sala: "portaria", x: 128 },
  deploy:       { sala: "servidores", x: DEPLOY.x },
  racks:        { sala: "servidores", x: 566 },
};

// Ronda do Vigia à noite: portaria → café → servidores → café → portaria.
export const RONDA = [{ sala: "cafe", x: 300 }, { sala: "servidores", x: 540 }, { sala: "cafe", x: 236 }];

export function lugar(nome, i = 0) {
  const l = LUGARES[nome];
  if (!l) return null;
  const a = ANDARES[SALA[l.sala].andar], dx = l.vagas ? l.vagas[i % l.vagas.length] : 0;
  return { sala: l.sala, x: l.x + dx, y: a.pe, alt: l.alt || 0, lugar: nome };
}

// Porta da rua (na escada, no térreo) e a escada em dois lances.
export const PORTA = { x: 18, y: ANDARES[0].pe };
const ESC_CIMA = { x: 44, y: ANDARES[1].pe }, ESC_MEIO = { x: 12, y: 244 }, ESC_BAIXO = { x: 44, y: ANDARES[0].pe };
export const ESCADA = { cima: ESC_CIMA, meio: ESC_MEIO, baixo: ESC_BAIXO };

export const andarDe = y => (y <= ANDARES[1].base ? 1 : y >= ANDARES[0].chao ? 0 : -1);

// Rota entre dois pontos: no mesmo andar, em linha reta; senão, pela escada
// (o robô de rodas vai na plataforma do corrimão; o drone voa por cima).
export function rota(de, para) {
  const a = andarDe(de.y), b = andarDe(para.y), fim = { x: para.x, y: para.y };
  if (a === b && a !== -1) return [fim];
  if (a === 1) return [ESC_CIMA, ESC_MEIO, ESC_BAIXO, fim];
  if (a === 0) return [ESC_BAIXO, ESC_MEIO, ESC_CIMA, fim];
  return b === 1 ? [ESC_MEIO, ESC_CIMA, fim] : [ESC_MEIO, ESC_BAIXO, fim];
}

export function salaEm(x, y) {
  if (x < 52) return "escada";
  const andar = y <= ANDARES[1].base ? 1 : 0;
  const s = SALAS.find(s => s.andar === andar && x >= s.x0 && x <= s.x1);
  return s ? s.id : null;
}
