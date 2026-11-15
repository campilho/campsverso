/** Os balões de fala (ADR-0078): o que cada avatar disse, por um tempo, sobre a cabeça dele.
 *
 * A fala chega pelo evento `campsverso.avatar.spoke.v1`, com o texto inteiro, que a linha do tempo
 * guarda. O balão mostra até `BALLOON_CHARS` caracteres, com "…" (a regra do protótipo do Claude
 * Design), e fica o tempo de ler: um pouco mais para um texto longo.
 */

export const BALLOON_CHARS = 90;
const MIN_MS = 3000;
const MS_PER_CHAR = 60;
const MAX_MS = 10_000;

/** O texto do balão: inteiro até o limite, cortado numa palavra com "…" depois dele. */
export function balloonText(text: string): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= BALLOON_CHARS) {
    return clean;
  }
  const cut = clean.slice(0, BALLOON_CHARS - 1);
  const space = cut.lastIndexOf(" ");
  return `${(space > BALLOON_CHARS / 2 ? cut.slice(0, space) : cut).trimEnd()}…`;
}

/** Quanto tempo real o balão fica: o tempo de ler. */
export function balloonMs(text: string): number {
  return Math.min(MAX_MS, MIN_MS + text.length * MS_PER_CHAR);
}

interface Spoken {
  readonly text: string;
  readonly until: number;
}

/** O balão de cada avatar agora: a última fala, até o tempo dela acabar. */
export class Balloons {
  private readonly spoken = new Map<string, Spoken>();

  hear(avatarId: string, text: string, nowMs: number): void {
    const shown = balloonText(text);
    this.spoken.set(avatarId, { text: shown, until: nowMs + balloonMs(shown) });
  }

  current(avatarId: string, nowMs: number): string | undefined {
    const found = this.spoken.get(avatarId);
    if (found === undefined) {
      return undefined;
    }
    if (nowMs >= found.until) {
      this.spoken.delete(avatarId);
      return undefined;
    }
    return found.text;
  }
}
