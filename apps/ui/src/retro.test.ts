/** A tela retrô do escritório (docs/design/briefing-tela.md): a luz, o relógio e os chips das
 * pessoas, em funções puras. */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import type { Banner } from "./banner.ts";
import { chipsOf, clockView, lightOf, robotLine, summonShort } from "./retro/model.ts";
import { summonsOf } from "./panels/office.ts";

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

const swap: Banner = { text: "Trocando de versão…", tone: "info", kind: "troca" };

describe("a luz da barra de cima", () => {
  it("é verde online, âmbar na troca e na espera, vermelha sem conexão, sempre com o rótulo", () => {
    expect(lightOf("open", true, undefined)).toEqual({ color: "verde", label: "online" });
    expect(lightOf("open", true, swap)).toEqual({ color: "ambar", label: "atualizando" });
    expect(lightOf("open", true, { ...swap, kind: "espera" }).color).toBe("ambar");
    expect(lightOf("open", true, { ...swap, kind: "fresh" }).color).toBe("verde");
    expect(lightOf("closed", true, swap)).toEqual({ color: "vermelha", label: "sem conexão" });
    expect(lightOf("connecting", true, undefined).color).toBe("vermelha");
    expect(lightOf("open", false, undefined).color).toBe("vermelha"); // o mundo parou de pulsar
  });
});

describe("o relógio da barra de baixo", () => {
  it("diz a hora, o dia com a fase e o ritmo só quando não é 1×", () => {
    expect(clockView(state(), "09:00:12")).toEqual({ hour: "09:00", day: "Dia 1 · manhã", pace: undefined });
    const fast = state({ day: 3, phase: "tarde", clock: { mode: "continuous", scale: 72, paused: false } });
    expect(clockView(fast, "15:30:00")).toEqual({ hour: "15:30", day: "Dia 3 · tarde", pace: "72×" });
  });
});

describe("os chips das pessoas", () => {
  const out = { kind: "avatar", display_name: "Camps", attributes: { papel: "dev" } }; // fora: sem posição
  const camps = { ...out, position: { x: 4, y: 6 } };
  const vigia = { kind: "avatar", display_name: "Vigia", position: { x: 2, y: 14 }, attributes: { papel: "vigia" } };
  const gerente = { kind: "avatar", display_name: "Gerente", position: { x: 9, y: 14 }, attributes: { papel: "gerente" } };
  const testador = { kind: "robot", display_name: "Testador", position: { x: 15, y: 4 }, attributes: {} };
  const briefing = { kind: "robot", display_name: "Briefing", position: { x: 16, y: 4 }, attributes: {} };

  it("vêm nesta ordem: o dev, o vigia, o gerente e os robôs, com a etiqueta de quem controla", () => {
    const office = state({
      entities: { testador, gerente, vigia, camps, briefing },
      controllers: {
        camps: { type: "llm" },
        vigia: { type: "script" },
        gerente: { type: "human" },
      } as unknown as ObserverState["controllers"],
    });
    const chips = chipsOf(office, "gerente", office.tick);
    expect(chips.map((c) => [c.id, c.tag])).toEqual([
      ["camps", "LLM"],
      ["vigia", "script"],
      ["gerente", "você"],
      ["briefing", "robô"],
      ["testador", "robô"],
    ]);
    expect(chips.find((c) => c.id === "vigia")).toMatchObject({ icon: "vigiar", line: "vigiando", away: false });
    const looking = state({ ...office, actions: { vigia: { action: "wait" } } as unknown as ObserverState["actions"] });
    expect(chipsOf(looking, "gerente", office.tick).find((c) => c.id === "vigia")?.line).toBe("vigiando"); // olhando a sala
    expect(chips.find((c) => c.id === "gerente")?.line).toBe("no escritório");
    expect(chips.filter((c) => c.robot).map((c) => c.line)).toEqual(["parado", "parado"]);
  });

  it("o gerente com o script não é você, e a ação curta vai na linha, a intenção no title", () => {
    const office = state({
      entities: { camps, gerente },
      controllers: { gerente: { type: "script" } } as unknown as ObserverState["controllers"],
      actions: { camps: { action: "work", intent: "o pedido 3" } } as unknown as ObserverState["actions"],
    });
    const chips = chipsOf(office, "gerente", office.tick);
    expect(chips.find((c) => c.id === "gerente")).toMatchObject({ tag: "script", line: "parado" });
    const dev = chips.find((c) => c.id === "camps");
    expect(dev?.icon).toBe("work");
    expect(dev?.title).toBe(`${dev?.line ?? ""} · o pedido 3`);
    expect(dev?.line.charAt(0)).toBe(dev?.line.charAt(0).toLowerCase());
  });

  it("quem dorme mostra dormindo, e quem está fora tem a borda tracejada", () => {
    const office = state({
      entities: { camps: out, gerente },
      asleep: { gerente: true },
    });
    const chips = chipsOf(office, "gerente", office.tick);
    expect(chips.find((c) => c.id === "camps")).toMatchObject({ away: true, icon: "fora", line: "fora" });
    expect(chips.find((c) => c.id === "gerente")).toMatchObject({ icon: "dormir", line: "dormindo" });
  });

  it("o dev fora da visão do jogador vem da convocação na linha do tempo, e o gerente fora também aparece", () => {
    const empty = state({ entities: {} });
    expect(chipsOf(empty, "gerente", empty.tick).map((c) => [c.id, c.away])).toEqual([["gerente", true]]);
    const event = {
      type: "campsverso.office.staff.summoned.v1",
      data: { avatar_id: "camps", by: "gerente", origin: "botao", arrives_tick: 16260, until_tick: 16800 },
    } as unknown as EnvelopeV1;
    const chips = chipsOf(empty, "gerente", empty.tick, [event]);
    expect(chips.map((c) => c.id)).toEqual(["camps", "gerente"]);
    expect(chips[0]).toMatchObject({ name: "Camps", away: true, line: "a caminho · 09:02" });
  });

  it("a linha curta da convocação: a caminho, convocado até uma hora, fora", () => {
    const summon = { convocado_por: "gerente", convocado_chega: 16260, convocado_ate: 16200 + 6 * 60 * 30 };
    const coming = state({ entities: { camps: { ...out, attributes: { papel: "dev", ...summon } } } });
    const [dev] = summonsOf(coming);
    expect(dev && summonShort(coming, dev)).toBe("a caminho · 09:02");
    const there = state({ entities: { camps: { ...camps, attributes: { papel: "dev", ...summon } } } });
    const [present] = summonsOf(there);
    expect(present && summonShort(there, present)).toBe("convocado até 15:00");
    const away = state({ entities: { camps: out } });
    const [gone] = summonsOf(away);
    expect(gone && summonShort(away, gone)).toBe("fora");
  });
});

describe("o robô da bancada", () => {
  it("trabalha, passa ou falha pela última chamada, e volta a parado depois", () => {
    const robots = (robot: { state: "working" | "passed" | "failed"; tick: number }): ObserverState =>
      state({ workshop: { robots: { testador: { ...robot, avatar_id: "camps" } } } });
    expect(robotLine(state(), "testador", 16200)).toBe("parado");
    expect(robotLine(robots({ state: "working", tick: 16100 }), "testador", 16200)).toBe("trabalhando");
    expect(robotLine(robots({ state: "passed", tick: 16190 }), "testador", 16200)).toBe("passou");
    expect(robotLine(robots({ state: "failed", tick: 16190 }), "testador", 16200)).toBe("falhou");
    expect(robotLine(robots({ state: "passed", tick: 10000 }), "testador", 16200)).toBe("parado");
    expect(robotLine(robots({ state: "working", tick: 0 }), "testador", 16200)).toBe("parado"); // passou das duas horas
  });
});
