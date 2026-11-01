import type { ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import cases from "../../../tests/fixtures/raio/casos.json";
import { FogMemory, FogStore, fogKey, serverCenter, visionRadius } from "./fog.ts";
import { pathFrom } from "./motion.ts";

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

describe("a lembrança da névoa (M21)", () => {
  it("na borda da vista, o que o servidor ainda não mandou continua lembrado", () => {
    // A tela já desenha o avatar um tile adiante; o servidor ainda o vê no tile de antes, e não
    // manda o canteiro que, para a tela, ainda está à vista na borda (a 3 tiles, no raio 3).
    const fog = new FogMemory();
    const plot = { kind: "plot", position: { x: 2, y: 0 }, attributes: { crop: "rabanete" } };
    fog.look(state("amanhecer", { "plot-001": plot }), { x: 0, y: 0 }, 3);
    const lagging = state("amanhecer", {});
    fog.look(lagging, { x: -1, y: 0 }, 3);
    expect(fog.sight(2, 0)).toBe("visible");
    expect(fog.entities(lagging, "camps")["plot-001"]).toEqual(plot);
    // Ao sair da vista, ele continua lá, como foi visto.
    fog.look(lagging, { x: -6, y: 0 }, 3);
    expect(fog.entities(lagging, "camps")["plot-001"]).toEqual(plot);
    // Bem dentro da vista, sem o servidor o mandar, ele não existe mais: some.
    fog.look(lagging, { x: 1, y: 0 }, 3);
    expect(fog.entities(lagging, "camps")["plot-001"]).toBeUndefined();
  });

  it("numa caminhada, o que a tela vê e o servidor ainda não mediu continua lembrado", () => {
    // Achado do usuário no mapa d: andando, a tela desenha o avatar longe de onde o servidor mediu
    // a vista. O canteiro do caminho, bem dentro da vista da tela, não foi mandado porque estava
    // fora da do servidor; a lembrança dele não pode se apagar.
    const fog = new FogMemory();
    const plot = { kind: "plot", position: { x: 10, y: 0 }, attributes: { crop: "couve" } };
    fog.look(state("noite", { "plot-010": plot }), { x: 10, y: 0 }, 3);
    const walking = state("noite", {});
    fog.look(walking, { x: 10, y: 1 }, 3, { x: 0, y: 0 }); // o servidor mediu do tile (0, 0)
    expect(fog.entities(walking, "camps")["plot-010"]).toEqual(plot);
    fog.look(walking, { x: 10, y: 9 }, 3, { x: 10, y: 9 }); // passou e saiu da vista
    expect(fog.entities(walking, "camps")["plot-010"]).toEqual(plot);
    // As duas contas no mesmo tile, e o canteiro bem à vista sem ter vindo: ele não existe mais.
    fog.look(walking, { x: 10, y: 1 }, 3, { x: 10, y: 1 });
    expect(fog.entities(walking, "camps")["plot-010"]).toBeUndefined();
  });

  it("o servidor mede a vista do tile do trajeto no tick do pulso, como o gateway", () => {
    const base = state("amanhecer", { camps: { kind: "avatar", position: { x: 20, y: 0 }, attributes: {} } });
    expect(serverCenter(base, "camps")).toEqual({ x: 20, y: 0 });
    const path = pathFrom({ x: 0, y: 0 }, [{ x: 20, y: 0 }]);
    const walking = { ...base, tick: 1, motion: { camps: { path, depart_tick: 1, tiles_per_tick: 1 } } };
    expect(serverCenter(walking, "camps")).toEqual({ x: 0, y: 0 }); // o tick do último evento
    expect(serverCenter({ ...walking, pulse: { tick: 11, alive: true } }, "camps")).toEqual({ x: 10, y: 0 });
    expect(serverCenter({ ...walking, pulse: { tick: 90, alive: true } }, "camps")).toEqual({ x: 20, y: 0 });
  });

  it("guardada no navegador, volta na tela nova; a de outro jogo no mesmo mundo é esquecida", () => {
    const items = new Map<string, string>();
    const storage = {
      getItem: (key: string) => items.get(key) ?? null,
      setItem: (key: string, value: string) => void items.set(key, value),
      removeItem: (key: string) => void items.delete(key),
    };
    const key = fogKey("farm-morada-do-sol-04", "camps");
    const fog = new FogMemory();
    const plot = { kind: "plot", position: { x: 2, y: 0 }, attributes: {} };
    fog.look(state("amanhecer", { "plot-001": plot }), { x: 0, y: 0 }, 3);
    fog.look(state("amanhecer", {}), { x: 10, y: 0 }, 3);
    new FogStore(key, storage).save(fog, 500);
    expect(key).toBe("campsverso.fog.farm-morada-do-sol-04.camps");

    const back = new FogStore(key, storage).load(520); // o sandbox retomou depois
    expect(back?.sight(2, 0)).toBe("seen");
    expect(back?.sight(30, 0)).toBe("unseen");
    expect(back?.entities(state("amanhecer", {}), "camps")["plot-001"]).toEqual(plot);
    expect(new FogStore(key, storage).load(10)).toBeUndefined(); // um jogo novo, do tick 0
    expect(items.has(key)).toBe(false);
    expect(new FogStore(key, undefined).load(10)).toBeUndefined(); // sem armazenamento
  });
});
