import type { Affordance, EnvelopeV1, ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { weatherText } from "./panels/hud.ts";
import { approach, menuFor, proposal, tileMenu } from "./play.ts";
import { ActionQueue } from "./queue.ts";

const AFFORDANCES: Affordance[] = [
  { action: "water", label: "Regar", on: ["plot"], target: true },
  { action: "dig", label: "Cavar um canteiro aqui", on: ["grass"], target: true },
  { action: "place", label: "Fincar aqui", on: ["grass"], target: true, params: [{ name: "item", label: "Item", choices: ["espantalho"], source: "inventory" }] },
  {
    action: "deposit",
    label: "Guardar no baú",
    on: ["chest"],
    target: true,
    params: [{ name: "item", label: "Item", choices: ["rabanete"], source: "inventory", entities: true }],
  },
  {
    action: "withdraw",
    label: "Pegar do baú",
    on: ["chest"],
    target: true,
    params: [{ name: "item", label: "Item", choices: ["rabanete"], source: "target", entities: true }],
  },
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
      "plot-001": { kind: "plot", position: { x: 20, y: 9 }, attributes: {} },
      chest: { kind: "chest", position: { x: 5, y: 5 }, attributes: {} },
      "spade-1": { kind: "spade", container_id: "camps", attributes: {} },
      "plow-1": { kind: "plow", container_id: "chest", attributes: {} },
    },
    containers: { camps: { rabanete: 2 }, chest: {} },
    motion: {},
    actions: {},
    needs: {},
    asleep: {},
    controllers: { camps: { type: "human", id: "human/camps-browser" } },
    decisions: {},
    ...overrides,
  };
}

function fact(type: string, avatarId = "camps"): EnvelopeV1 {
  return { type, data: { avatar_id: avatarId, action: "x" } } as unknown as EnvelopeV1;
}

describe("os menus do humano (ADR-0068)", () => {
  it("a grama vazia oferece andar, cavar e fincar o que ele tem, com o tile no alvo", () => {
    const tile = { x: 9, y: 2 };
    expect(tileMenu(state(), "camps", tile, "grass").map((e) => e.label)).toEqual(["Andar até aqui", "Cavar um canteiro aqui"]);
    const withScarecrow = state({ containers: { camps: { espantalho: 1 }, chest: {} } });
    const entries = tileMenu(withScarecrow, "camps", tile, "grass");
    expect(entries.map((e) => e.action)).toEqual(["move", "dig", "place"]);
    expect(entries.map((e) => proposal("camps", e, {}).params.target)).toEqual([tile, tile, tile]);
    expect(tileMenu(state(), "camps", tile, "river")).toEqual([]);
  });

  it("o baú oferece as ferramentas pelo id, do inventário ao guardar e do baú ao pegar", () => {
    const [deposit, withdraw] = menuFor(state(), "camps", "chest");
    expect(deposit?.params[0]?.options).toEqual(["rabanete", "spade-1"]);
    expect(withdraw?.params[0]?.options).toEqual(["plow-1"]);
  });

  it("o quadro de encomendas oferece os pedidos pelo nome, e a escolha leva o id (ADR-0069)", () => {
    const board: Affordance = {
      action: "accept_order",
      label: "Aceitar a encomenda",
      on: ["order_board"],
      target: true,
      params: [{ name: "order", label: "Pedido", source: "target", entities: true }],
    };
    const base = state();
    const withBoard = state({
      session: { ...base.session, cartridge_version: "0.1.0", tick_seconds: 60, affordances: [board] },
      entities: {
        ...base.entities,
        "order-board": { kind: "order_board", position: { x: 6, y: 4 }, attributes: {} },
        "order-012": { kind: "order", container_id: "order-board", display_name: "Dona Cida: 4 milho até dia 12 · 270", attributes: {} },
      },
    });
    const [accept] = menuFor(withBoard, "camps", "order-board");
    expect(accept?.params[0]?.options).toEqual(["order-012"]);
    expect(accept?.params[0]?.names).toEqual({ "order-012": "Dona Cida: 4 milho até dia 12 · 270" });
  });

  it("o HUD mostra o tempo em português e, com a previsão, o de amanhã", () => {
    expect(weatherText(state({ weather: { "1": "sun" } }))).toBe("clima: sol");
    expect(weatherText(state({ weather: { "1": "rain", "2": "storm" } }))).toBe("clima: chuva · amanhã: tempestade");
  });

  it("longe do alvo, o passo começa por andar até o lado dele; perto, não", () => {
    expect(approach(state(), "camps", "plot-001")?.params).toEqual({ near: "plot-001" });
    expect(approach(state(), "camps", { x: 9, y: 2 })?.params).toEqual({ near: { x: 9, y: 2 } });
    expect(approach(state(), "camps", "chest")).toBeUndefined();
    expect(approach(state(), "camps", undefined)).toBeUndefined();
  });
});

describe("a fila de ações (ADR-0068)", () => {
  const water = { label: "Regar · plot-001", proposal: { avatar_id: "camps", action: "water", params: { target: "plot-001" } }, near: "plot-001" };
  const deposit = { label: "Guardar no baú", proposal: { avatar_id: "camps", action: "deposit", params: { target: "chest" } }, near: "chest" };

  it("manda uma proposta por vez: anda até o lado, faz, e só então o passo seguinte", () => {
    const queue = new ActionQueue();
    queue.push(water);
    queue.push(deposit);
    expect(queue.next(state(), "camps")?.params).toEqual({ near: "plot-001" });
    expect(queue.next(state(), "camps")).toBeUndefined(); // em voo
    queue.settle(fact("campsverso.action.completed.v1"), "camps");
    const near = state({ entities: { ...state().entities, camps: { kind: "avatar", position: { x: 19, y: 9 }, attributes: {} } } });
    expect(queue.next(near, "camps")?.action).toBe("water");
    queue.settle(fact("campsverso.action.completed.v1"), "camps");
    expect(queue.next(near, "camps")?.params).toEqual({ near: "chest" });
    expect(queue.list.map((s) => s.label)).toEqual(["Guardar no baú"]);
  });

  it("não manda nada com o avatar ocupado ou dormindo", () => {
    const queue = new ActionQueue();
    queue.push(deposit);
    expect(queue.next(state({ asleep: { camps: true } }), "camps")).toBeUndefined();
    const busy = state({ actions: { camps: { action_id: "a-1", action: "dig", params: {}, end_tick: 20 } } });
    expect(queue.next(busy, "camps")).toBeUndefined();
    expect(queue.next(state(), "camps")?.action).toBe("deposit");
  });

  it("uma recusa esvazia a fila e avisa; o fato de outro avatar não conta", () => {
    const queue = new ActionQueue();
    queue.push(deposit);
    queue.push(water);
    queue.next(state(), "camps");
    expect(queue.settle(fact("campsverso.action.rejected.v1", "ana"), "camps")).toBeUndefined();
    expect(queue.settle(fact("campsverso.action.rejected.v1"), "camps")).toBe("A fila foi esvaziada.");
    expect(queue.list).toEqual([]);
  });
});
