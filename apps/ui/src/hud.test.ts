import type { ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { contractsText, loadView, needView } from "./panels/hud.ts";

describe("as barras do corpo (M21)", () => {
  it("a fome aparece como saciedade: cheia é boa, como a energia", () => {
    expect(needView("fome", 6)).toEqual({ label: "saciedade", value: 94 });
    expect(needView("fome", 100)).toEqual({ label: "saciedade", value: 0 });
    expect(needView("energia", 76)).toEqual({ label: "energia", value: 76 });
  });
});

describe("os contratos no painel (M21)", () => {
  it("os ajudantes que quem joga contratou, pelo quadro, com o nome da ficha", () => {
    const state = {
      tick: 0,
      day: 2,
      phase: "manha",
      clock: { mode: "continuous", scale: 72, paused: false },
      weather: {},
      entities: {
        board: { kind: "helper_board", attributes: { dita: "livre", ze_graudo: "com camps até o dia 5", nina: "com outro até o dia 3" } },
      },
      containers: {},
      motion: {},
      actions: {},
      needs: {},
      asleep: {},
      controllers: {},
      decisions: {},
      session: {
        cartridge_version: "0.1.0",
        tick_seconds: 60,
        affordances: [
          {
            action: "hire_helper",
            label: "Contratar ajudante",
            on: ["helper_board"],
            target: true,
            params: [{ name: "helper", label: "Ajudante", source: "any", choices: ["ze-graudo"], option_notes: { "ze-graudo": "Zé Graúdo, o carregador: carrega o dobro" } }],
          },
        ],
      },
    } as ObserverState;
    expect(contractsText(state, "camps")).toEqual(["Zé Graúdo até o dia 5"]);
  });
});

describe("a carga da mochila (M21)", () => {
  function carrying(attributes: Record<string, number>): ObserverState {
    return {
      tick: 0,
      day: 1,
      phase: "manha",
      clock: { mode: "continuous", scale: 72, paused: false },
      weather: {},
      entities: { camps: { kind: "avatar", position: { x: 1, y: 1 }, attributes } },
      containers: {},
      motion: {},
      actions: {},
      needs: {},
      asleep: {},
      controllers: {},
      decisions: {},
    };
  }

  it("o que carrega e o que aguenta, pelos atributos do avatar, em alerta perto do limite", () => {
    expect(loadView(carrying({ capacity: 20, weight: 12.5 }), "camps")).toEqual({ text: "carga 12,5 de 20", full: false });
    expect(loadView(carrying({ capacity: 20, weight: 18 }), "camps")).toEqual({ text: "carga 18 de 20", full: true });
    expect(loadView(carrying({ capacity: 20 }), "camps")).toEqual({ text: "carga 0 de 20", full: false });
  });

  it("sem capacidade, nada (a fazenda 1)", () => {
    expect(loadView(carrying({}), "camps")).toBeUndefined();
  });
});
