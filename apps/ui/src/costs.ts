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

/** O último aviso do orçamento, em uma linha; nada sem aviso. No escritório (ADR-0080), o teto do
 * dia ou do total desliga a mente, sem pausar o mundo, e o de um pedido faz a mente largá-lo. */
export function budgetLine(state: ObserverState): string | undefined {
  const budget = state.costs?.budget;
  if (budget === undefined) {
    return undefined;
  }
  const ticket = budget.scope === "ticket";
  const scope = ticket ? `o teto do ${budget.ticket_id ?? "pedido"}` : budget.scope === "day" ? "o teto do dia" : "o teto total";
  const spent = `${usd(budget.spent_usd)} de ${usd(budget.limit_usd)}`;
  if (budget.exceeded) {
    const effect = budget.paused === true ? ": o mundo pausou" : ticket ? ": a mente larga o pedido" : budget.paused === false ? ": a mente desligou" : "";
    return `Bateu ${scope} (${spent})${effect}.`;
  }
  return `${String(budget.threshold_pct ?? "?")}% d${scope} (${spent}).`;
}

/** O sinal de vida da guarda (ADR-0080), em uma linha: o gasto do dia e o total contra os tetos, o
 * teto por pedido, o que está estourado e se a guarda ficou sem sinal; nada sem sinal nenhum. */
export function guardLine(state: ObserverState): string | undefined {
  const guard = state.costs?.guard;
  if (guard === undefined) {
    return undefined;
  }
  const { limits } = guard;
  const parts = [
    `dia ${usd(guard.spent_day_usd ?? 0)} de ${usd(limits.usd_per_sim_day)}`,
    ...(limits.usd_per_ticket === undefined ? [] : [`pedido até ${usd(limits.usd_per_ticket)}`]),
    `total ${usd(guard.spent_total_usd)} de ${usd(limits.usd_total)}`,
  ];
  const over = guard.exceeded.length === 0 ? "" : ` · estourado: ${guard.exceeded.join(", ")}`;
  return `Guarda${guard.alive ? "" : " sem sinal"}: ${parts.join(" · ")}${over}.`;
}

/** O total de todas as mentes, para o cartão de cada corrida na arena; nada sem custo. */
export function totalCost(state: ObserverState): string | undefined {
  const minds = Object.values(state.costs?.minds ?? {});
  if (minds.length === 0) {
    return undefined;
  }
  return usd(minds.reduce((sum, mind) => sum + (mind?.total_usd ?? 0), 0));
}
