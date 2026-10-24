/** Linha do tempo: um resumo legível de qualquer evento, sem conhecer o cartucho (ADR-0050), e o
 * rótulo que o cartucho declara para ele, quando há (ADR-0068). */
import type { EnvelopeV1, EventLabel } from "@campsverso/contracts";

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

// `intent` logo depois da ação: é o que o LLM disse que pretendia (ADR-0059).
const FIRST = ["avatar_id", "entity_id", "action", "intent", "reason", "item", "qty", "plot_id", "rule", "phase", "need", "value"];

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

/** O valor num caminho com ponto (`params.crop`), ou nada. */
function pick(data: unknown, path: string): unknown {
  let value = data;
  for (const key of path.split(".")) {
    if (typeof value !== "object" || value === null || !(key in value)) {
      return undefined;
    }
    value = (value as Record<string, unknown>)[key];
  }
  return value;
}

/** O texto de um rótulo com os campos do evento, ou nada se faltar algum; `semente_batata` vira
 * `semente batata`. */
function fill(text: string, data: unknown): string | undefined {
  const paths = [...text.matchAll(/\{([a-z0-9_.]+)\}/g)].map((m) => m[1] ?? "");
  const values = new Map(paths.map((path) => [path, scalar(pick(data, path))]));
  if ([...values.values()].some((value) => value === undefined)) {
    return undefined;
  }
  return text.replace(/\{([a-z0-9_.]+)\}/g, (_, path: string) => (values.get(path) ?? "").replace(/_/g, " "));
}

/** O rótulo do cartucho para o evento: o mais específico que bate e tem todos os campos; no
 * empate, o primeiro declarado. Sem nenhum, `undefined`, e a tela mostra o tipo cru. */
export function describe(event: EnvelopeV1, labels: readonly EventLabel[]): string | undefined {
  const candidates = labels
    .map((label, order) => ({ label, order, weight: Object.keys(label.where ?? {}).length }))
    .filter(({ label }) => label.event === event.type && Object.entries(label.where ?? {}).every(([path, want]) => pick(event.data, path) === want))
    .sort((a, b) => b.weight - a.weight || a.order - b.order);
  for (const { label } of candidates) {
    const text = fill(label.text, event.data);
    if (text !== undefined) {
      return text;
    }
  }
  return undefined;
}

export function matches(event: EnvelopeV1, filter: TimelineFilter): boolean {
  if (!filter.visibilities.has(event.visibility)) {
    return false;
  }
  const text = filter.text.trim().toLowerCase();
  return text === "" || shortType(event.type).toLowerCase().includes(text);
}
