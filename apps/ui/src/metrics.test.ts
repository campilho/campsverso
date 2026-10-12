import type { ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { metricTable } from "./metrics.ts";

const CATALOG = [
  { id: "colheitas", label: "Colheitas", kind: "count" as const, event: "campsverso.action.completed.v1", by: { field: "params.target", attribute: "group" } },
  { id: "moedas", label: "Moedas no fim do dia", kind: "item" as const, item: "moeda" },
  { id: "pico_fome", label: "Pico de fome", kind: "max_need" as const, need: "fome" },
  { id: "desmaios", label: "Desmaios", kind: "count" as const, event: "campsverso.avatar.fainted.v1" },
];

function state(metrics: ObserverState["metrics"]): ObserverState {
  return {
    tick: 0,
    day: 1,
    phase: "manha",
    session: { cartridge_version: "0.2.0", tick_seconds: 60, metrics: CATALOG },
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
    ...(metrics === undefined ? {} : { metrics }),
  };
}

describe("métricas do dia no painel (ADR-0054)", () => {
  it("hoje, ontem e a soma dos dias que houver", () => {
    const table = metricTable(
      state({
        "1": { colheitas: { oeste: 1 }, moedas: 100, pico_fome: 30 },
        "2": { colheitas: { oeste: 2, leste: 3 }, moedas: 80, pico_fome: 55.25, desmaios: 1 },
        "3": { moedas: 140, pico_fome: 41 },
      }),
    );
    expect(table?.weekLabel).toBe("3 dias");
    expect(table?.rows).toEqual([
      { id: "colheitas", label: "Colheitas", today: "0", yesterday: "leste 3 · oeste 2", week: "leste 3 · oeste 3" },
      { id: "moedas", label: "Moedas no fim do dia", today: "140", yesterday: "80", week: "+40" },
      { id: "pico_fome", label: "Pico de fome", today: "41", yesterday: "55,3", week: "55,3" },
      { id: "desmaios", label: "Desmaios", today: "0", yesterday: "1", week: "1" },
    ]);
  });

  it("no primeiro dia, ontem fica vazio; sem catálogo ou sem dados, não há tabela", () => {
    const first = metricTable(state({ "1": { moedas: 100 } }));
    expect(first?.weekLabel).toBe("1 dia");
    expect(first?.rows.find((r) => r.id === "moedas")).toMatchObject({ today: "100", yesterday: "–", week: "–" });
    expect(metricTable(state(undefined))).toBeUndefined();
  });

  it("só os 7 dias mais recentes entram na semana", () => {
    const metrics = Object.fromEntries(Array.from({ length: 8 }, (_, i) => [String(i + 1), { desmaios: 1 }]));
    const table = metricTable(state(metrics));
    expect(table?.weekLabel).toBe("7 dias");
    expect(table?.rows.find((r) => r.id === "desmaios")?.week).toBe("7");
  });
});
