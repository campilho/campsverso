/** O custo das mentes no painel do operador e na arena (ADR-0074): o gasto de hoje e o total de
 * cada controlador com modelo, e o último aviso da guarda de orçamento. Tudo vem do estado, que o
 * gateway projeta dos eventos `llm.call.completed` cobrados e dos `ops.budget.*`. */
import type { ObserverState } from "@campsverso/contracts";

/** Dólares em português, com casas de sobra para os centavos de uma chamada do Haiku. */
export function usd(value: number): string {
  const digits = value !== 0 && Math.abs(value) < 1 ? 3 : 2;
  return `US$ ${value.toFixed(digits).replace(".", ",")}`;
}

/** Uma linha por mente: o modelo, o gasto de hoje (zero se o último dia com chamadas foi outro), o
 * total, as chamadas e, quando houve, a parte do conselheiro. */
export function costLines(state: ObserverState): string[] {
  const minds = state.costs?.minds ?? {};
  const lines: string[] = [];
  for (const [id, mind] of Object.entries(minds).sort(([a], [b]) => a.localeCompare(b))) {
    if (mind === undefined) {
      continue;
    }
    const today = mind.day === state.day ? mind.day_usd : 0;
    const calls = `${String(mind.calls)} chamada${mind.calls === 1 ? "" : "s"}`;
    const advisor = mind.advisor_usd === undefined ? "" : ` (conselheiro ${usd(mind.advisor_usd)})`;
    lines.push(`${id} · ${mind.model ?? "?"}: hoje ${usd(today)}, total ${usd(mind.total_usd)}${advisor} · ${calls}`);
  }
  return lines;
}

/** O último aviso do orçamento, em uma linha; nada sem aviso. */
export function budgetLine(state: ObserverState): string | undefined {
  const budget = state.costs?.budget;
  if (budget === undefined) {
    return undefined;
  }
  const scope = budget.scope === "day" ? "o teto do dia" : "o teto total";
  const spent = `${usd(budget.spent_usd)} de ${usd(budget.limit_usd)}`;
  if (budget.exceeded) {
    return `Bateu ${scope} (${spent})${budget.paused === true ? ": o mundo pausou" : ""}.`;
  }
  return `${String(budget.threshold_pct ?? "?")}% d${scope} (${spent}).`;
}

/** O total de todas as mentes, para o cartão de cada corrida na arena; nada sem custo. */
export function totalCost(state: ObserverState): string | undefined {
  const minds = Object.values(state.costs?.minds ?? {});
  if (minds.length === 0) {
    return undefined;
  }
  return usd(minds.reduce((sum, mind) => sum + (mind?.total_usd ?? 0), 0));
}
