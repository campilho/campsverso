import type { Affordance, ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { inControl, menuFor, proposal, thingAt, walkTo } from "./play.ts";

const AFFORDANCES: Affordance[] = [
  { action: "plant", label: "Plantar", on: ["plot"], target: true, params: [{ name: "crop", label: "Cultura", choices: ["rabanete", "batata"], source: "any" }] },
  { action: "water", label: "Regar", on: ["plot"], target: true },
  {
    action: "withdraw",
    label: "Pegar do baú",
    on: ["chest"],
    target: true,
    params: [
      { name: "item", label: "Item", choices: ["rabanete", "batata"], source: "target" },
      { name: "qty", label: "Quantidade", source: "any", minimum: 1, default: 1 },
    ],
  },
  { action: "eat", label: "Comer", on: ["self"], target: false, params: [{ name: "item", label: "Comida", choices: ["rabanete", "batata"], source: "inventory" }] },
];

function state(overrides: Partial<ObserverState> = {}): ObserverState {
  return {
    tick: 10,
    day: 1,
    phase: "amanhecer",
    session: { cartridge_version: "0.1.0", tick_seconds: 60, affordances: AFFORDANCES },
    clock: { mode: "continuous", scale: 72, paused: false },
    weather: {},
    entities: {
      camps: { kind: "avatar", position: { x: 4, y: 4 }, attributes: {} },
      "plot-e-01": { kind: "plot", position: { x: 24, y: 9 }, attributes: {} },
      chest: { kind: "chest", position: { x: 6, y: 5 }, attributes: {} },
    },
    containers: { camps: { moeda: 100 }, chest: { rabanete: 5 } },
    motion: {},
    actions: {},
    needs: {},
    asleep: {},
    controllers: { camps: { type: "human", id: "human/camps-browser" } },
    decisions: {},
    ...overrides,
  };
}

describe("jogar pela tela (ADR-0051)", () => {
  it("o menu de cada coisa vem do catálogo, com o alvo preenchido", () => {
    const plot = menuFor(state(), "camps", "plot-e-01");
    expect(plot.map((e) => e.label)).toEqual(["Plantar", "Regar"]);
    const [plant] = plot;
    if (plant === undefined) {
      throw new Error("sem Plantar no menu");
    }
    expect(proposal("camps", plant, { crop: "batata" })).toEqual({
      avatar_id: "camps",
      action: "plant",
      params: { target: "plot-e-01", crop: "batata" },
    });
  });

  it("as escolhas valem pelo inventário ou pelo alvo; sem escolha, a ação fica desabilitada", () => {
    const [withdraw] = menuFor(state(), "camps", "chest");
    expect(withdraw?.params[0]?.options).toEqual(["rabanete"]); // só o que o baú guarda
    expect(withdraw?.params[1]).toMatchObject({ numeric: true, minimum: 1, initial: 1 });
    const [eat] = menuFor(state(), "camps", "self");
    expect(eat?.target).toBeUndefined();
    expect(eat?.ready).toBe(false); // o Camps não tem comida
    const fed = state({ containers: { camps: { batata: 1 } } });
    expect(menuFor(fed, "camps", "self")[0]?.params[0]?.options).toEqual(["batata"]);
  });

  it("clique esquerdo anda até o tile, ou até perto da coisa que está nele", () => {
    expect(walkTo(state(), "camps", 10, 10).params).toEqual({ target: { x: 10, y: 10 } });
    expect(walkTo(state(), "camps", 6, 5).params).toEqual({ near: "chest" });
    expect(thingAt(state(), 4, 4)).toBeUndefined(); // o avatar não é "coisa"
  });

  it("só joga quem tem a posse", () => {
    expect(inControl(state(), "camps")).toBe(true);
    expect(inControl(state({ controllers: { camps: { type: "script", id: "script/farmer-v1" } } }), "camps")).toBe(false);
  });
});

describe("o menu diz o custo, o horário e o preço (M21)", () => {
  const kioskAffordances: Affordance[] = [
    {
      action: "buy",
      label: "Comprar",
      on: ["kiosk"],
      target: true,
      cost: { energy: 0, minutes: 2 },
      note: "aberto das 08:00 às 18:00",
      params: [
        {
          name: "item",
          label: "Item",
          choices: ["semente_rabanete", "semente_milho", "semente_tomate", "adubo"],
          source: "any",
          prices: { semente_rabanete: 10, semente_milho: 20, semente_tomate: 30, adubo: 15 },
          price_attribute: "preco_",
          stock_attribute: "estoque_hoje",
        },
      ],
    },
    { action: "dig", label: "Cavar um canteiro aqui", on: ["self"], target: false, cost: { energy: 8, minutes: 15 } },
    { action: "sleep", label: "Dormir aqui", on: ["self"], target: false, cost: { energy: 0, minutes: 1 } },
    { action: "water", label: "Regar", on: ["plot"], target: true, cost: { energy: 0.5, minutes: 2 } },
  ];
  const kiosk = {
    kind: "kiosk",
    position: { x: 5, y: 4 },
    attributes: { open: false, estoque_hoje: "semente_rabanete, semente_milho, adubo", preco_semente_rabanete: 11, preco_semente_milho: null },
  };
  const at = state({
    session: { cartridge_version: "0.1.0", tick_seconds: 60, affordances: kioskAffordances },
    entities: { ...state().entities, kiosk },
  });

  it("no quiosque: o horário, fechado agora, o preço de agora e só o que há hoje", () => {
    const [buy] = menuFor(at, "camps", "kiosk");
    expect(buy?.detail).toBe("2 min · fechado agora · aberto das 08:00 às 18:00");
    expect(buy?.params[0]?.options).toEqual(["semente_rabanete", "semente_milho", "adubo"]); // o tomate não está no estoque
    // O rabanete com o preço de agora; o milho sem preço de agora fica com o de tabela, como o adubo.
    expect(buy?.params[0]?.prices).toEqual({ semente_rabanete: 11, semente_milho: 20, adubo: 15 });
  });

  it("cada ação diz a energia e o tempo; o que não custa nada não diz", () => {
    const own = menuFor(at, "camps", "self");
    expect(own.map((e) => e.detail)).toEqual(["8 de energia · 15 min", undefined]);
    expect(menuFor(at, "camps", "plot-e-01")[0]?.detail).toBe("0,5 de energia · 2 min");
  });
});
