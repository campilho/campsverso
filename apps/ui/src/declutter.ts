/** Os rótulos sobre as cabeças sem se encavalar (18/nov: "Jogando videogame game" no sofá e
 * "Almoçando Almoçando" na mesa da copa).
 *
 * Dois rótulos iguais que se tocam viram um só, entre os dois, na altura do mais alto. Rótulos
 * diferentes que se tocam se empilham: o da direita sobe até ficar acima. Função pura das caixas,
 * testável sem o Phaser; serve ao texto de hoje e ao balão com ícone que vem com a arte.
 */

/** Uma caixa com a origem no meio da borda de baixo, como os rótulos da tela. */
export interface Label {
  readonly id: string;
  readonly text: string;
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

export interface Placement {
  readonly x: number;
  readonly y: number;
  readonly visible: boolean;
}

/** O respiro entre duas caixas, em pixels. */
const GAP = 2;

interface Box {
  x: number;
  y: number;
  readonly width: number;
  readonly height: number;
}

function touches(a: Box, b: Box): boolean {
  const apart = (a.width + b.width) / 2 + GAP;
  return Math.abs(a.x - b.x) < apart && a.y - a.height < b.y + GAP && b.y - b.height < a.y + GAP;
}

/** Onde cada rótulo fica, pelo id; da esquerda para a direita, para não depender da ordem. */
export function declutter(labels: readonly Label[]): Map<string, Placement> {
  const sorted = [...labels].sort((a, b) => a.x - b.x || a.y - b.y || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  const groups: { readonly text: string; readonly members: Label[]; readonly box: Box }[] = [];
  for (const label of sorted) {
    const same = groups.find((g) => g.text === label.text && touches(g.box, label));
    if (same === undefined) {
      groups.push({ text: label.text, members: [label], box: { x: label.x, y: label.y, width: label.width, height: label.height } });
      continue;
    }
    same.members.push(label);
    same.box.x = same.members.reduce((sum, m) => sum + m.x, 0) / same.members.length;
    same.box.y = Math.min(same.box.y, label.y);
  }
  const placed: Box[] = [];
  for (const { box } of groups) {
    for (let tries = 0; tries <= placed.length; tries++) {
      const hit = placed.find((other) => touches(box, other));
      if (hit === undefined) {
        break;
      }
      box.y = hit.y - hit.height - GAP;
    }
    placed.push(box);
  }
  const result = new Map<string, Placement>();
  for (const { members, box } of groups) {
    members.forEach((member, i) => {
      result.set(member.id, { x: box.x, y: box.y, visible: i === 0 });
    });
  }
  return result;
}
