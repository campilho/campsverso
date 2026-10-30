import type { Affordance, ObserverEntity, ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { contentsOf, inControl, menuFor, proposal, thingAt, walkTo } from "./play.ts";

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

describe("o menu mostra o que vale agora (M21)", () => {
  const plotAffordances: Affordance[] = [
    {
      action: "plant",
      label: "Plantar",
      on: ["plot"],
      target: true,
      requires: [{ attribute: "crop", values: [null], hint: "o canteiro já tem planta" }],
      params: [{ name: "crop", label: "Cultura", choices: ["rabanete", "batata", "milho"], source: "any", held_prefix: "semente_" }],
    },
    { action: "harvest", label: "Colher", on: ["plot"], target: true, requires: [{ attribute: "stage", values: ["madura"], hint: "ainda não está madura" }] },
    {
      action: "fertilize",
      label: "Adubar",
      on: ["plot"],
      target: true,
      requires: [
        { item: "adubo", hint: "sem adubo no inventário" },
        { attribute: "crop", values: [null], hint: "só se aduba o canteiro vazio" },
      ],
    },
    {
      action: "sell",
      label: "Vender na feira",
      on: ["fair_stall"],
      target: true,
      note: "feira a cada 7 dias; a próxima é no dia {target.proxima_feira}",
      params: [{ name: "item", label: "Colheita", choices: ["rabanete", "batata"], source: "inventory", price_attribute: "preco_" }],
    },
    {
      action: "hire_helper",
      label: "Contratar ajudante",
      on: ["helper_board"],
      target: true,
      params: [
        {
          name: "helper",
          label: "Ajudante",
          choices: ["dita", "ze-graudo"],
          source: "any",
          price_attribute: "diaria_",
          option_notes: { dita: "Dita, a plantadeira: planta rápido", "ze-graudo": "Zé Graúdo, o carregador: carrega o dobro" },
        },
      ],
    },
  ];
  const base = state();
  const at = (plot: Record<string, unknown>, inventory: Record<string, number>): ObserverState => ({
    ...base,
    session: { cartridge_version: "0.1.0", tick_seconds: 60, affordances: plotAffordances, items: { rabanete: { weight: 1 }, adubo: { weight: 1 } } },
    entities: {
      ...base.entities,
      "plot-e-01": { kind: "plot", position: { x: 24, y: 9 }, attributes: plot as ObserverEntity["attributes"] },
      feira: { kind: "fair_stall", position: { x: 5, y: 5 }, attributes: { open: false, proxima_feira: 14, preco_rabanete: 31 } },
      board: { kind: "helper_board", position: { x: 6, y: 6 }, attributes: { diaria_dita: 40, diaria_ze_graudo: 45 } },
    },
    containers: { camps: inventory, chest: { rabanete: 5, adubo: 2 } },
  });

  it("plantar mostra só a semente que se tem, com quantas; o canteiro ocupado desabilita", () => {
    const empty = at({ crop: null, stage: null }, { semente_rabanete: 4, semente_milho: 1, rabanete: 8 });
    const [plant, harvest, fertilize] = menuFor(empty, "camps", "plot-e-01");
    expect(plant?.params[0]?.options).toEqual(["rabanete", "milho"]);
    expect(plant?.params[0]?.counts).toEqual({ rabanete: 4, milho: 1 });
    expect(plant?.ready).toBe(true);
    expect([harvest?.ready, harvest?.blocked]).toEqual([false, "ainda não está madura"]);
    expect([fertilize?.ready, fertilize?.blocked]).toEqual([false, "sem adubo no inventário"]);
    expect(fertilize?.detail).toBe("você tem 0 adubo");
    const ripe = at({ crop: "rabanete", stage: "madura" }, { adubo: 3 });
    const [busy, picked, again] = menuFor(ripe, "camps", "plot-e-01");
    expect([busy?.ready, busy?.blocked]).toEqual([false, "o canteiro já tem planta"]);
    expect(picked?.ready).toBe(true);
    expect([again?.blocked, again?.detail]).toEqual(["só se aduba o canteiro vazio", "você tem 3 adubo"]);
  });

  it("vender mostra quantas se tem e o preço de agora; a nota cita o alvo", () => {
    const [sell] = menuFor(at({}, { rabanete: 8 }), "camps", "feira");
    expect(sell?.params[0]?.counts).toEqual({ rabanete: 8 });
    expect(sell?.params[0]?.prices).toEqual({ rabanete: 31 });
    expect(sell?.detail).toBe("fechado agora · feira a cada 7 dias; a próxima é no dia 14");
  });

  it("contratar mostra a diária de agora (com o id em snake_case) e a ficha de cada ajudante", () => {
    const [hire] = menuFor(at({}, {}), "camps", "board");
    expect(hire?.params[0]?.prices).toEqual({ dita: 40, "ze-graudo": 45 });
    expect(hire?.params[0]?.notes?.["ze-graudo"]).toBe("Zé Graúdo, o carregador: carrega o dobro");
    expect(hire?.params[0]?.names).toEqual({ dita: "Dita", "ze-graudo": "Zé Graúdo" }); // o nome, pela ficha
  });

  it("o interior do baú: cada item, quantos e quanto ocupa da capacidade", () => {
    const base = at({}, {});
    const storage: Affordance = { action: "withdraw", label: "Pegar do baú", on: ["chest"], target: true };
    const chest = {
      ...base,
      session: { ...base.session, cartridge_version: "0.1.0", tick_seconds: 60, affordances: [...plotAffordances, storage] },
      entities: {
        ...base.entities,
        chest: { kind: "chest", position: { x: 6, y: 5 }, attributes: { capacity: 100, weight: 7 } },
        orders: { kind: "order_board", position: { x: 9, y: 5 }, attributes: { capacity: 100, weight: 0 } },
      },
    };
    expect(contentsOf(chest, "chest")).toEqual({
      items: [
        { item: "adubo", name: "adubo", qty: 2, weight: 2 },
        { item: "rabanete", name: "rabanete", qty: 5, weight: 5 },
      ],
      used: 7,
      capacity: 100,
    });
    expect(contentsOf(chest, "feira")).toBeUndefined(); // sem capacidade, sem desenho
    expect(contentsOf(chest, "orders")).toBeUndefined(); // o quadro guarda pedidos, não coisas
  });
});
