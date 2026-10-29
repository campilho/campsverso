import type { ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { budgetLine, costLines, totalCost, usd } from "./costs.ts";

function state(day: number, costs?: ObserverState["costs"]): ObserverState {
  return {
    tick: (day - 1) * 1440,
    day,
    phase: "manha",
    clock: { mode: "continuous", scale: 72, paused: false },
    weather: {},
    entities: {},
    containers: {},
    motion: {},
    actions: {},
    needs: {},
    asleep: {},
    controllers: {},
    decisions: {},
    ...(costs === undefined ? {} : { costs }),
  };
}

const MINDS: NonNullable<ObserverState["costs"]>["minds"] = {
  "llm/camps": {
    avatar_id: "camps",
    model: "claude-haiku-5-5",
    day: 3,
    day_usd: 0.0214,
    total_usd: 0.0731,
    calls: 210,
    advisor_usd: 0.0166,
  },
};

describe("o custo das mentes (ADR-0074)", () => {
  it("dólares em português, com três casas abaixo de um dólar", () => {
    expect(usd(0.0214)).toBe("US$ 0,021");
    expect(usd(12.5)).toBe("US$ 12,50");
    expect(usd(0)).toBe("US$ 0,00");
  });

  it("hoje, o total, o conselheiro e as chamadas de cada mente", () => {
    expect(costLines(state(3, { minds: MINDS }))).toEqual([
      "llm/camps · claude-haiku-5-5: hoje US$ 0,021, total US$ 0,073 (conselheiro US$ 0,017) · 210 chamadas",
    ]);
    // O último dia com chamadas foi o 3: no dia 4, ainda sem chamada, hoje é zero.
    expect(costLines(state(4, { minds: MINDS }))[0]).toContain("hoje US$ 0,00, total US$ 0,073");
    expect(costLines(state(1))).toEqual([]);
  });

  it("o aviso do orçamento e o total da corrida", () => {
    const warned = { scope: "day", spent_usd: 0.48, limit_usd: 0.6, threshold_pct: 80, exceeded: false };
    expect(budgetLine(state(3, { minds: MINDS, budget: warned }))).toBe("80% do teto do dia (US$ 0,480 de US$ 0,600).");
    const hit = { scope: "total", spent_usd: 10, limit_usd: 10, exceeded: true, paused: true };
    expect(budgetLine(state(3, { budget: hit }))).toBe("Bateu o teto total (US$ 10,00 de US$ 10,00): o mundo pausou.");
    expect(budgetLine(state(3, { minds: MINDS }))).toBeUndefined();
    expect(totalCost(state(3, { minds: MINDS }))).toBe("US$ 0,073");
    expect(totalCost(state(3))).toBeUndefined();
  });
});
