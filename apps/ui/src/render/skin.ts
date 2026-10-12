/** Aparência do canvas de depuração: cor de cada tipo de tile e de entidade (ADR-0050).
 *
 * O estado é genérico; quem desenha escolhe a aparência. Tipos que o canvas não conhece ganham uma
 * cor estável derivada do nome, para que um cartucho novo apareça sem mudar a UI.
 */

const TILES: Readonly<Record<string, string>> = {
  grass: "#6dab4f",
  path: "#c9a26b",
  tree: "#2f6b34",
  river: "#3b7dd8",
  wall: "#7a5c46",
  door: "#a8743d",
  soil: "#8a5a35",
  floor: "#d9c3a0",
  entrance: "#b08d57",
};

const KINDS: Readonly<Record<string, string>> = {
  avatar: "#f2f2f2",
  bed: "#c0392b",
  chest: "#8e5b2a",
  kiosk: "#e67e22",
  sell_box: "#d4ac0d",
  table: "#a0785a",
  well: "#5d6d7e",
  door: "#6e4b2a",
  plot: "#5b3a1e",
};

/** Cor do canteiro pelo estágio da planta (atributos do cartucho farm). */
const STAGES: Readonly<Record<string, string>> = {
  semente: "#7d5a3c",
  broto: "#9bc46a",
  crescendo: "#5fa83a",
  madura: "#e8c02e",
  murcha: "#7f7f6a",
};

function hashColor(name: string): string {
  let hash = 0;
  for (const char of name) {
    hash = (hash * 31 + char.charCodeAt(0)) % 360;
  }
  return `hsl(${String(hash)} 45% 55%)`;
}

export function tileColor(type: string): string {
  return TILES[type] ?? (type === "" ? "#000000" : hashColor(type));
}

export function entityColor(kind: string, attributes: Readonly<Record<string, unknown>>): string {
  const stage = attributes.stage;
  if (kind === "plot" && typeof stage === "string") {
    return STAGES[stage] ?? hashColor(stage);
  }
  return KINDS[kind] ?? hashColor(kind);
}

/** Rótulo curto para desenhar dentro do tile. */
export function entityLabel(kind: string, attributes: Readonly<Record<string, unknown>>): string {
  if (kind === "plot") {
    const crop = attributes.crop;
    return typeof crop === "string" ? crop.slice(0, 3) : "";
  }
  return kind.replace(/_/g, " ").slice(0, 5);
}

/** Fases da noite do cartucho farm: a tela escurece um pouco. */
const NIGHT = new Set(["noite", "madrugada"]);

export function isNight(phase: string): boolean {
  return NIGHT.has(phase);
}
