import type { ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { setLocale } from "./locale.ts";
import { busyText, overHead, progressOf } from "./progress.ts";

function state(overrides: Partial<ObserverState> = {}): ObserverState {
  return {
    tick: 100,
    sim_time: "2026-03-02T08:00:00-03:00",
    day: 1,
    phase: "manha",
    session: {
      cartridge_version: "0.2.0",
      tick_seconds: 60,
      affordances: [{ action: "plant", label: "Plantar", on: ["plot"], target: true }],
    },
    clock: { mode: "continuous", scale: 72, paused: false },
    weather: {},
    entities: { camps: { kind: "avatar", display_name: "Camps", position: { x: 4, y: 4 }, attributes: {} } },
    containers: {},
    motion: {},
    actions: {},
    needs: {},
    asleep: {},
    controllers: {},
    decisions: {},
    ...overrides,
  };
}

const planting = {
  camps: { action_id: "act-1", action: "plant", params: { target: "plot-e-01" }, applied_tick: 100, end_tick: 105, interrupt: "never" as const },
};

describe("barra de progresso e ocupado (ADR-0052)", () => {
  it("a barra anda do início ao fim previsto da ação, com o rótulo do catálogo", () => {
    const s = state({ actions: planting });
    expect(progressOf(s, "camps", 100)).toEqual({ label: "Plantar", fraction: 0 });
    expect(progressOf(s, "camps", 102.5)).toEqual({ label: "Plantar", fraction: 0.5 });
    expect(progressOf(s, "camps", 109)).toEqual({ label: "Plantar", fraction: 1 });
    expect(progressOf(state(), "camps", 100)).toBeUndefined();
  });

  it("sem o início (arquivo antigo), só o rótulo", () => {
    const old = { camps: { action_id: "act-1", action: "water", params: {}, end_tick: 105 } };
    expect(progressOf(state({ actions: old }), "camps", 101)).toEqual({ label: "water" });
    const walking = { camps: { action_id: "act-2", action: "move", params: {}, applied_tick: 100, end_tick: 104 } };
    expect(progressOf(state({ actions: walking }), "camps", 101)).toEqual({ label: "Andando", fraction: 0.25 });
  });

  it("sobre a cabeça, nada de andar, esperar nem falar; o retrato continua dizendo (18/nov)", () => {
    for (const action of ["move", "wait", "say"]) {
      const s = state({ actions: { camps: { action_id: "act-3", action, params: {}, applied_tick: 100, end_tick: 104 } } });
      expect(overHead(s, "camps", 101)).toBeUndefined();
      expect(progressOf(s, "camps", 101)).toBeDefined();
    }
    const planting = { camps: { action_id: "act-4", action: "plant", params: {}, applied_tick: 100, end_tick: 104 } };
    expect(overHead(state({ actions: planting }), "camps", 102)).toEqual({ label: "Plantar", fraction: 0.5 });
    const asleep = state({ asleep: { camps: true }, actions: { camps: { action_id: "act-5", action: "wait", params: {}, end_tick: 104 } } });
    expect(overHead(asleep, "camps", 101)?.label).toBe("Zz");
  });

  it("o arquivo da língua diz o que se faz, antes do rótulo do menu (ADR-0082)", () => {
    const playing = {
      gerente: { action_id: "act-3", action: "videogame", params: {}, applied_tick: 100, end_tick: 104, interrupt: "cancel" as const },
    };
    const office = state({
      session: { cartridge_version: "0.1.0", tick_seconds: 1, affordances: [{ action: "videogame", label: "Jogar videogame", on: ["sofa"], target: false }] },
      entities: { gerente: { kind: "avatar", display_name: "Gerente", position: { x: 4, y: 4 }, attributes: {} } },
      actions: playing,
    });
    expect(progressOf(office, "gerente", 100)?.label).toBe("Jogar videogame");
    setLocale([{ actions: { videogame: "Jogando videogame" } }]);
    try {
      expect(progressOf(office, "gerente", 102)).toEqual({ label: "Jogando videogame", fraction: 0.5 });
      expect(busyText(office, "gerente", 101)).toContain("ocupado: jogando videogame");
    } finally {
      setLocale([]);
    }
  });

  it("o sono tem barra até a hora de acordar", () => {
    const s = state({ asleep: { camps: true }, sleep: { camps: { since_tick: 100, wake_at_tick: 140 } } });
    expect(progressOf(s, "camps", 110)).toEqual({ label: "Zz", fraction: 0.25 });
    expect(busyText(s, "camps", 110)).toBe("Camps está dormindo; acorda às 08:40.");
  });

  it("a recusa busy diz o que ocupa e quanto falta", () => {
    expect(busyText(state({ actions: planting }), "camps", 101.5)).toBe("Camps está ocupado: plantar, faltam 4 min.");
    expect(busyText(state({ actions: planting }), "camps", 104.9)).toBe("Camps está ocupado: plantar, faltam 1 min.");
  });
});
