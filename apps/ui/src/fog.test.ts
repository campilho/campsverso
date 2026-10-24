import type { ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import cases from "../../../tests/fixtures/raio/casos.json";
import { FogMemory, visionRadius } from "./fog.ts";

function state(phase: string, entities: ObserverState["entities"], containers: ObserverState["containers"] = {}): ObserverState {
  return {
    tick: 0,
    day: 1,
    phase,
    clock: { mode: "continuous", scale: 72, paused: false },
    weather: {},
    entities,
    containers,
    motion: {},
    actions: {},
    needs: {},
    asleep: {},
    controllers: {},
    decisions: {},
    session: {
      cartridge_version: "0.1.0",
      tick_seconds: 60,
      perception: { radius: 3, by_phase: { noite: 1 }, lights: { lanterna: 2 }, landmarks: ["kiosk"] },
    },
  };
}

describe("a névoa (ADR-0068)", () => {
  it("o raio da hora segue a regra da percepção: a fase, ou a luz que o avatar carrega", () => {
    expect(visionRadius(state("amanhecer", {}), "camps")).toBe(3);
    expect(visionRadius(state("noite", {}), "camps")).toBe(1);
    expect(visionRadius(state("noite", {}, { camps: { lanterna: 1 } }), "camps")).toBe(2);
    const whole = { ...state("noite", {}), session: { cartridge_version: "0.1.0", tick_seconds: 60 } } as ObserverState;
    expect(visionRadius(whole, "camps")).toBeUndefined();
  });

  it("a conta bate com a da percepção: os mesmos casos do teste em Python", () => {
    for (const [n, c] of cases.cases.entries()) {
      const base = state(c.phase, {}, { camps: c.held });
      const perception = c.perception as NonNullable<NonNullable<ObserverState["session"]>["perception"]>;
      const session = { cartridge_version: "0.1.0", tick_seconds: 60, perception };
      expect(visionRadius({ ...base, session }, "camps") ?? null, `caso ${String(n)}`).toBe(c.expected);
    }
  });

  it("a borda da vista: os dois anéis de fora, com o tile logo além na direção de fora", () => {
    const fog = new FogMemory();
    fog.look(state("amanhecer", {}), { x: 10, y: 10 }, 4);
    expect(fog.edge(14, 10)).toEqual({ depth: 0, beyond: { x: 15, y: 10 } });
    expect(fog.edge(10, 7)).toEqual({ depth: 1, beyond: { x: 10, y: 5 } });
    expect(fog.edge(6, 6)).toEqual({ depth: 0, beyond: { x: 5, y: 5 } });
    expect(fog.edge(11, 10)).toBeUndefined(); // longe da borda
    expect(fog.edge(15, 10)).toBeUndefined(); // fora da vista
    fog.look(state("amanhecer", {}), { x: 10, y: 10 }, 2);
    expect(fog.edge(12, 10)).toBeUndefined(); // um raio pequeno não tem véu
  });

  it("o que saiu da vista fica congelado como foi visto, e o que nunca foi visto não aparece", () => {
    const fog = new FogMemory();
    const plot = { kind: "plot", position: { x: 2, y: 0 }, attributes: { crop: "milho", stage: "broto" } };
    const far = { kind: "plot", position: { x: 9, y: 0 }, attributes: {} };
    const kiosk = { kind: "kiosk", position: { x: 20, y: 0 }, attributes: {} };
    const before = state("amanhecer", { "plot-001": plot, "plot-009": far, kiosk });
    expect(fog.look(before, { x: 0, y: 0 }, 3)).toBe(true);
    expect(Object.keys(fog.entities(before, "camps")).sort()).toEqual(["kiosk", "plot-001"]);
    expect(fog.sight(9, 0)).toBe("unseen");
    // O avatar se afasta, e o canteiro amadurece longe da vista: a tela mostra o broto.
    const after = state("amanhecer", {
      "plot-001": { ...plot, attributes: { crop: "milho", stage: "madura" } },
      "plot-009": far,
      kiosk,
    });
    fog.look(after, { x: 10, y: 0 }, 3);
    expect(fog.sight(2, 0)).toBe("seen");
    const shown = fog.entities(after, "camps");
    expect(shown["plot-001"]?.attributes.stage).toBe("broto");
    expect(shown["plot-009"]).toBeDefined();
    // Volta, e o canteiro tinha virado grama: some da tela.
    const gone = state("amanhecer", { "plot-009": far, kiosk });
    fog.look(gone, { x: 1, y: 0 }, 3);
    expect(fog.entities(gone, "camps")["plot-001"]).toBeUndefined();
  });
});
