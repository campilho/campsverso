/** O monitor maior (docs/design/briefing-tela-2.md, §6; ADR-0092): a partir de 1180 px de largura, a
 * barra de baixo sai e a sala escala para a altura toda. O canvas do Phaser continua em 1x (640 x
 * 512); o CSS o amplia pela escala que esta conta dá, a maior que cabe nas duas medidas. */

/** Abaixo disso, o iPad e o celular, nada muda. */
export const BIG = "(min-width: 1180px)";

export const ROOM = { width: 640, height: 512 } as const;

/** A barra de cima, o espaço entre as peças e a margem da página. */
const TOP = 44;
const GAP = 8;
const PAGE = 8;
/** O que o monitor tem além da tela: a borda, o topo, a moldura, o espaço e o painel (102 px na
 * altura) e as bordas dos lados (44 px na largura). */
const MONITOR_HEIGHT = 102;
const MONITOR_WIDTH = 44;
/** A coluna da direita, o quadro e a conversa, nunca fica com menos que isso. */
const RIGHT_MIN = 400;
/** Numa janela muito baixa, a sala não encolhe além disso: a página rola. */
const SMALLEST = 0.75;

export interface Layout {
  /** A escala da sala, fracionária. */
  readonly scale: number;
  /** A largura do monitor, a tela mais as bordas. */
  readonly monitor: number;
  /** O que sobra para o quadro e a conversa. */
  readonly right: number;
}

export function roomLayout(width: number, height: number): Layout {
  const column = height - TOP - GAP - PAGE;
  const byHeight = (column - MONITOR_HEIGHT) / ROOM.height;
  const byWidth = (width - 2 * PAGE - GAP - RIGHT_MIN - MONITOR_WIDTH) / ROOM.width;
  const scale = Math.max(SMALLEST, Math.min(byHeight, byWidth));
  const monitor = ROOM.width * scale + MONITOR_WIDTH;
  return { scale, monitor, right: width - 2 * PAGE - GAP - monitor };
}
