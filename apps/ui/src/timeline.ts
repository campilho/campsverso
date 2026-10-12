/** Linha do tempo: um resumo legível de qualquer evento, sem conhecer o cartucho (ADR-0050). */
import type { EnvelopeV1 } from "@campsverso/contracts";

export type Visibility = EnvelopeV1["visibility"];

export interface TimelineFilter {
  readonly visibilities: ReadonlySet<Visibility>;
  /** Trecho do tipo, sem diferenciar maiúsculas; vazio deixa passar tudo. */
  readonly text: string;
}

/** `campsverso.world.entity.moved.v1` vira `world.entity.moved`. */
export function shortType(type: string): string {
  return type.replace(/^campsverso\./, "").replace(/\.v\d+$/, "");
}

const FIRST = ["avatar_id", "entity_id", "action", "reason", "item", "qty", "plot_id", "rule", "phase", "need", "value"];

function scalar(value: unknown): string | undefined {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(1);
  }
  if (typeof value === "boolean") {
    return String(value);
  }
  if (typeof value === "object" && value !== null && "x" in value && "y" in value) {
    const { x, y } = value;
    return `(${String(x)}, ${String(y)})`;
  }
  return undefined;
}

/** Até `limit` campos `chave=valor` do payload, os mais informativos primeiro. */
export function summarize(event: EnvelopeV1, limit = 4): string {
  const data = event.data as Record<string, unknown>;
  const keys = [...FIRST.filter((k) => k in data), ...Object.keys(data).filter((k) => !FIRST.includes(k))];
  const parts: string[] = [];
  for (const key of keys) {
    const text = scalar(data[key]);
    if (text !== undefined) {
      parts.push(`${key}=${text}`);
    }
    if (parts.length === limit) {
      break;
    }
  }
  return parts.join(" · ");
}

export function matches(event: EnvelopeV1, filter: TimelineFilter): boolean {
  if (!filter.visibilities.has(event.visibility)) {
    return false;
  }
  const text = filter.text.trim().toLowerCase();
  return text === "" || shortType(event.type).toLowerCase().includes(text);
}
