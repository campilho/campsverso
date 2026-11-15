/** O escritório na tela (ADR-0078): os balões de fala, o quadro dos pedidos e o relógio em tempo
 * real. */
import type { ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { isOffice, ticketsOf } from "./panels/office.ts";
import { BALLOON_CHARS, Balloons, balloonMs, balloonText } from "./speech.ts";
import { clockText, realTime } from "./simclock.ts";

function state(overrides: Partial<ObserverState> = {}): ObserverState {
  return {
    tick: 16200,
    sim_time: "2026-11-16T09:00:00-03:00",
    day: 1,
    phase: "manha",
    session: { cartridge_version: "0.1.0", tick_seconds: 2, map: { id: "office_campsverso", width: 20, height: 17 } },
    clock: { mode: "continuous", scale: 1, paused: false },
    weather: {},
    entities: {},
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

describe("o balão de fala", () => {
  it("mostra o texto curto inteiro e corta o longo numa palavra, com reticências", () => {
    expect(balloonText("  Bom   dia!  ")).toBe("Bom dia!");
    const long = "palavra ".repeat(30);
    const shown = balloonText(long);
    expect(shown.length).toBeLessThanOrEqual(BALLOON_CHARS);
    expect(shown.endsWith("palavra…")).toBe(true);
  });

  it("fica o tempo de ler e some", () => {
    const balloons = new Balloons();
    balloons.hear("gerente", "Bom dia, Camps!", 1000);
    expect(balloons.current("gerente", 1000)).toBe("Bom dia, Camps!");
    expect(balloons.current("gerente", 1000 + balloonMs("Bom dia, Camps!") - 1)).toBe("Bom dia, Camps!");
    expect(balloons.current("gerente", 1000 + balloonMs("Bom dia, Camps!"))).toBeUndefined();
    expect(balloons.current("camps", 1000)).toBeUndefined();
  });
});

describe("o quadro dos pedidos", () => {
  const office = state({
    entities: {
      quadro: { kind: "board", position: { x: 9, y: 2 }, attributes: {} },
      "pedido-002": {
        kind: "ticket",
        container_id: "quadro",
        attributes: { numero: 2, titulo: "Resumo", estado: "a_fazer", tamanho: "M", dono: null },
      },
      "pedido-001": {
        kind: "ticket",
        container_id: "quadro",
        attributes: { numero: 1, titulo: "Busca", estado: "fazendo", tamanho: "P", dono: "camps", comentario: "Falta o teste." },
      },
    },
  });

  it("é de um mundo com quadro, e lista os pedidos na ordem em que foram escritos", () => {
    expect(isOffice(office)).toBe(true);
    expect(isOffice(state())).toBe(false);
    const tickets = ticketsOf(office);
    expect(tickets.map((t) => t.number)).toEqual([1, 2]);
    expect(tickets[0]).toMatchObject({ title: "Busca", state: "fazendo", owner: "camps", comment: "Falta o teste." });
    expect(tickets[1]?.owner).toBeUndefined();
  });
});

describe("o relógio em tempo real", () => {
  it("mostra os segundos num tick menor que o minuto, e não na fazenda", () => {
    expect(realTime(state())).toBe(true);
    expect(clockText(state(), 16215)).toBe("09:00:30");
    const farm = state({ session: { cartridge_version: "0.1.0", tick_seconds: 60, map: { id: "farm_camps", width: 3, height: 2 } } });
    expect(realTime(farm)).toBe(false);
    expect(clockText(farm, 16201)).toBe("09:01");
  });
});
