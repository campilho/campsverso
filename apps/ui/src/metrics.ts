/** As métricas do dia no painel do operador (ADR-0054): hoje, ontem e os últimos 7 dias.
 *
 * O catálogo vem do cartucho (`session.metrics`), e os valores, da projeção comum. Aqui só se junta
 * e se formata: somas para contagens, o pico para necessidades, a variação para itens.
 */
import type { ObserverState } from "@campsverso/contracts";

type Value = number | Readonly<Record<string, number | undefined>>;

export interface MetricRow {
  readonly id: string;
  readonly label: string;
  readonly today: string;
  readonly yesterday: string;
  readonly week: string;
}

export interface MetricTable {
  /** "7 dias", ou quantos houver até lá. */
  readonly weekLabel: string;
  readonly rows: readonly MetricRow[];
}

function add(a: Value | undefined, b: Value | undefined): Value | undefined {
  if (a === undefined) {
    return b;
  }
  if (b === undefined) {
    return a;
  }
  if (typeof a === "number" && typeof b === "number") {
    return a + b;
  }
  const sum: Record<string, number> = {};
  for (const part of [a, b]) {
    for (const [group, n] of Object.entries(typeof part === "number" ? { total: part } : part)) {
      sum[group] = (sum[group] ?? 0) + (n ?? 0);
    }
  }
  return sum;
}

function show(value: Value | undefined, decimals = 0): string {
  if (value === undefined) {
    return "–";
  }
  if (typeof value === "number") {
    return value.toLocaleString("pt-BR", { maximumFractionDigits: decimals });
  }
  const groups = Object.entries(value).sort(([a], [b]) => a.localeCompare(b));
  return groups.length === 0 ? "–" : groups.map(([group, n]) => `${group} ${String(n ?? 0)}`).join(" · ");
}

export function metricTable(state: ObserverState): MetricTable | undefined {
  const catalog = state.session?.metrics ?? [];
  const days = Object.keys(state.metrics ?? {}).map(Number);
  if (catalog.length === 0 || days.length === 0) {
    return undefined;
  }
  const today = Math.max(...days);
  const week = Array.from({ length: 7 }, (_, i) => today - 6 + i).filter((d) => days.includes(d));
  const at = (day: number, id: string): Value | undefined => state.metrics?.[String(day)]?.[id];
  const rows = catalog.map((metric): MetricRow => {
    const id = metric.id;
    if (metric.kind === "count") {
      // Dia sem nenhum evento contado (ou somado, com `field`) vale zero.
      const total = week.reduce<Value | undefined>((sum, d) => add(sum, at(d, id)), undefined);
      const yesterday = days.includes(today - 1) ? (at(today - 1, id) ?? 0) : undefined;
      return { id, label: metric.label, today: show(at(today, id) ?? 0), yesterday: show(yesterday), week: show(total ?? 0) };
    }
    if (metric.kind === "max_need") {
      const peaks = week.map((d) => at(d, id)).filter((v): v is number => typeof v === "number");
      return { id, label: metric.label, today: show(at(today, id), 1), yesterday: show(at(today - 1, id), 1), week: show(peaks.length > 0 ? Math.max(...peaks) : undefined, 1) };
    }
    // item: o valor do fim do dia; na semana, quanto mudou desde o fim do primeiro dia
    const first = week[0] === undefined ? undefined : at(week[0], id);
    const last = at(today, id);
    const change = typeof first === "number" && typeof last === "number" && week.length > 1 ? last - first : undefined;
    return {
      id,
      label: metric.label,
      today: show(last),
      yesterday: show(at(today - 1, id)),
      week: change === undefined ? "–" : `${change >= 0 ? "+" : ""}${show(change)}`,
    };
  });
  return { weekLabel: week.length === 7 ? "7 dias" : `${String(week.length)} ${week.length === 1 ? "dia" : "dias"}`, rows };
}
