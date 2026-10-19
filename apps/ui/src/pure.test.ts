import type { EnvelopeV1, ObserverMotion, ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { MAX_TILES_PER_SECOND, MotionClock, positionAt, smoothedAt } from "./motion.ts";
import { applyMergePatch } from "./patch.ts";
import { entityColor, tileColor } from "./render/skin.ts";
import { DisplayClock, MAX_AHEAD, clockText, isLive } from "./simclock.ts";
import { Store } from "./store.ts";
import { doingText } from "./panels/hud.ts";
import { matches, shortType, summarize } from "./timeline.ts";
import { parseTiledMap, tileAt } from "./tiled.ts";

function state(overrides: Partial<ObserverState> = {}): ObserverState {
  return {
    tick: 100,
    sim_time: "2026-10-10T07:40:00-03:00",
    day: 1,
    phase: "amanhecer",
    session: { cartridge_version: "0.1.0", tick_seconds: 60, map: { id: "farm_camps", width: 3, height: 2 } },
    clock: { mode: "continuous", scale: 72, paused: false },
    weather: { "1": "sun" },
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

function event(type: string, visibility: EnvelopeV1["visibility"], data: Record<string, unknown>): EnvelopeV1 {
  return {
    specversion: "1.0",
    id: "019a1b2c-3d4e-7f60-8a9b-0c1d2e3f4a5b",
    source: "/kernel/farm-camps-01",
    type,
    time: "2026-10-11T22:00:00Z",
    datacontenttype: "application/json",
    dataschema: "contracts://x",
    worldid: "farm-camps-01",
    cartridge: "farm_camps",
    seq: 1,
    tick: 7,
    provenance: "simulated",
    visibility,
    data,
  };
}

describe("merge patch (RFC 7386)", () => {
  it("troca, acrescenta e apaga chaves; arrays vêm inteiros", () => {
    const before = { clock: { paused: false, scale: 72 }, motion: { camps: { path: [1, 2] } }, tick: 1 };
    const patch = { clock: { paused: true }, motion: { camps: null }, tick: 2, day: 2 };
    expect(applyMergePatch(before, patch)).toEqual({ clock: { paused: true, scale: 72 }, motion: {}, tick: 2, day: 2 });
    expect(applyMergePatch({ a: [1, 2] }, { a: [3] })).toEqual({ a: [3] });
  });

  it("os eventos novos chegam a quem escuta mesmo com a linha do tempo cheia", () => {
    const store = new Store();
    store.applyWelcome({
      type: "campsverso.realtime.welcome.v1",
      worldid: "w",
      view: "player",
      avatar_id: "camps",
      commands: [],
      state: state(),
      events: Array.from({ length: 1000 }, () => event("campsverso.world.x.v1", "world", {})),
    });
    const heard: string[] = [];
    store.onEvents((events) => heard.push(...events.map((e) => e.type)));
    const rejected = event("campsverso.world.command.rejected.v1", "observer", { reason: "mode_not_allowed" });
    store.applyUpdate({ type: "campsverso.realtime.update.v1", patch: {}, events: [rejected] });
    expect(heard).toEqual(["campsverso.world.command.rejected.v1"]);
    expect(store.timeline).toHaveLength(1000);
  });

  it("a loja aplica o patch e conta os welcomes", () => {
    const store = new Store();
    store.applyWelcome({
      type: "campsverso.realtime.welcome.v1",
      worldid: "w",
      view: "player",
      avatar_id: "camps",
      commands: [],
      state: state(),
      events: [],
    });
    store.applyUpdate({ type: "campsverso.realtime.update.v1", patch: { clock: { paused: true } }, events: [] });
    expect(store.state?.clock.paused).toBe(true);
    expect(store.welcomes).toBe(1);
  });
});

describe("mapa Tiled", () => {
  it("lê o tipo de cada tile pela camada terrain", () => {
    const grid = parseTiledMap({
      width: 2,
      height: 1,
      layers: [{ name: "terrain", type: "tilelayer", data: [1, 4] }],
      tilesets: [{ firstgid: 1, tiles: [{ id: 0, type: "grass" }, { id: 3, type: "river" }] }],
    });
    expect([tileAt(grid, 0, 0), tileAt(grid, 1, 0)]).toEqual(["grass", "river"]);
    expect(tileColor("grass")).not.toBe(tileColor("river"));
    expect(tileColor("lava")).toMatch(/^hsl\(/); // tipo novo ganha cor estável
  });
});

describe("trajeto", () => {
  const motion: ObserverMotion = {
    path: [{ x: 1, y: 1 }, { x: 2, y: 1 }, { x: 2, y: 2 }],
    depart_tick: 10,
    tiles_per_tick: 2,
  };

  it("anda pelas esquinas na velocidade do evento e para no fim", () => {
    expect(positionAt(motion, 10)).toEqual({ x: 1, y: 1 });
    expect(positionAt(motion, 10.25)).toEqual({ x: 1.5, y: 1 });
    expect(positionAt(motion, 10.75)).toEqual({ x: 2, y: 1.5 });
    expect(positionAt(motion, 50)).toEqual({ x: 2, y: 2 });
  });
});

describe("relógio da tela", () => {
  const at72 = state(); // 72 s simulados por segundo: 1,2 tick por segundo
  const at720 = state({ clock: { mode: "continuous", scale: 720, paused: false } });

  /** Quadros a cada `every` ms de `from` até `to`; devolve todos os ticks mostrados. */
  function frames(clock: DisplayClock, s: ObserverState, from: number, to: number, live = true, every = 50): number[] {
    const shown: number[] = [];
    for (let now = from; now <= to; now += every) {
      shown.push(clock.at(s, now, live));
    }
    return shown;
  }

  const monotonic = (values: number[]): boolean => values.every((v, i) => i === 0 || v >= (values[i - 1] ?? v));

  it("anda na escala entre eventos, com teto", () => {
    const clock = new DisplayClock();
    clock.reset(at72, 0);
    expect(frames(clock, at72, 0, 10_000).at(-1)).toBeCloseTo(112, 1);
    expect(frames(clock, at72, 10_050, 200_000).at(-1)).toBeCloseTo(100 + MAX_AHEAD, 0);
  });

  it("evento atrasado: não volta nem trava, só desacelera até acertar", () => {
    const clock = new DisplayClock();
    clock.reset(at72, 0);
    const before = frames(clock, at72, 0, 5000); // 106
    const late = { ...at72, tick: 105 }; // aconteceu há quase 1 s
    clock.observe(late, 5000);
    const after = frames(clock, late, 5050, 9000);
    expect(monotonic([...before, ...after])).toBe(true);
    expect(after.every((v, i) => i === 0 || v > (after[i - 1] ?? 0))).toBe(true); // sempre andando
    expect(after.at(-1)).toBeCloseTo(105 + 4 * 1.2, 0);
  });

  it("trocar 720× por 72× não faz o relógio voltar nem saltar", () => {
    const clock = new DisplayClock();
    clock.reset(at720, 0);
    const fast = frames(clock, at720, 0, 5000); // 160
    clock.observe(at72, 5000); // escala nova, sem evento novo
    const slow = frames(clock, at72, 5050, 6000);
    expect(monotonic([...fast, ...slow])).toBe(true);
    expect((slow.at(-1) ?? 0) - (fast.at(-1) ?? 0)).toBeCloseTo(1.2, 1);
  });

  it("numa aba em segundo plano (um quadro por segundo) a 720× continua estável", () => {
    const clock = new DisplayClock();
    clock.reset(at720, 0);
    let s = at720;
    let shown: number[] = [];
    for (let second = 1; second <= 20; second++) {
      s = { ...s, tick: 100 + Math.floor(second * 12 - 1.5) }; // evento ~125 ms atrasado
      clock.observe(s, second * 1000);
      shown = [...shown, ...frames(clock, s, second * 1000, second * 1000 + 999, true, 1000)];
    }
    expect(monotonic(shown)).toBe(true);
    const gaps = shown.slice(1).map((v, i) => v - (shown[i] ?? v));
    expect(Math.min(...gaps.slice(3))).toBeGreaterThan(10); // sem paradas: anda uns 12 ticks por quadro
    expect(Math.abs((shown.at(-1) ?? 0) - (100 + 20 * 12))).toBeLessThan(3);
  });

  it("um passo com a pausa pula direto para o tick novo", () => {
    const clock = new DisplayClock();
    const paused = state({ clock: { mode: "continuous", scale: 72, paused: true } });
    clock.reset(paused, 0);
    const stepped = { ...paused, tick: 160 };
    clock.observe(stepped, 1000);
    expect(clock.at(stepped, 1000, true)).toBe(160);
  });

  it("para sem conexão, na pausa e no modo máximo", () => {
    const clock = new DisplayClock();
    clock.reset(at72, 0);
    expect(frames(clock, at72, 0, 10_000, false).at(-1)).toBe(100);
    const paused = state({ clock: { mode: "continuous", scale: 72, paused: true } });
    clock.observe(paused, 10_000);
    expect(frames(clock, paused, 10_000, 20_000).at(-1)).toBe(100);
    const max = state({ clock: { mode: "max", scale: 72, paused: false } });
    clock.observe(max, 20_000);
    expect(frames(clock, max, 20_000, 30_000).at(-1)).toBe(100);
  });

  it("o pulso do kernel ancora o relógio mesmo sem evento, e sem sinal ele para", () => {
    const clock = new DisplayClock();
    clock.reset(at72, 0);
    frames(clock, at72, 0, 2000); // ~102,4 pela estimativa
    const pulsed = { ...at72, pulse: { tick: 103, alive: true } };
    clock.observe(pulsed, 2000);
    expect(frames(clock, pulsed, 2050, 3000).at(-1)).toBeGreaterThan(103.5);
    const silent = { ...pulsed, pulse: { tick: 103, alive: false } };
    clock.observe(silent, 3000);
    const frozen = frames(clock, silent, 3050, 9000, isLive(silent, true));
    expect(frozen.at(-1)).toBe(frozen[0]);
  });

  it("um welcome novo recomeça, mesmo para trás", () => {
    const clock = new DisplayClock();
    clock.reset(at72, 0);
    frames(clock, at72, 0, 10_000);
    clock.reset(state({ tick: 3 }), 10_000);
    expect(clock.at(state({ tick: 3 }), 10_000, true)).toBe(3);
  });

  it("mostra a hora do mundo, no fuso do mundo", () => {
    expect(clockText(state(), 100)).toBe("07:40");
    expect(clockText(state(), 125.9)).toBe("08:05");
  });
});

describe("linha do tempo", () => {
  it("resume qualquer evento e filtra por visibilidade e tipo", () => {
    const rejected = event("campsverso.action.rejected.v1", "agent", { avatar_id: "camps", action: "sleep", reason: "not_tired", params: {} });
    expect(shortType(rejected.type)).toBe("action.rejected");
    expect(summarize(rejected)).toBe("avatar_id=camps · action=sleep · reason=not_tired");
    expect(matches(rejected, { visibilities: new Set(["world"]), text: "" })).toBe(false);
    expect(matches(rejected, { visibilities: new Set(["agent"]), text: "REJ" })).toBe(true);
  });

  it("a intenção declarada vem logo depois da ação (ADR-0059)", () => {
    const accepted = event("campsverso.action.accepted.v1", "world", {
      action_id: "act-1",
      avatar_id: "camps",
      action: "plant",
      params: { target: "plot-w-02" },
      applied_tick: 10,
      duration_ticks: 5,
      intent: "Plantar rabanete no plot-w-02.",
    });
    expect(summarize(accepted)).toBe("avatar_id=camps · action=plant · intent=Plantar rabanete no plot-w-02. · action_id=act-1");
    expect(doingText("plant")).toBe("fazendo: plant");
    expect(doingText("plant", "Plantar rabanete no plot-w-02.")).toBe("fazendo: plant · Plantar rabanete no plot-w-02.");
  });

  it("cor do canteiro vem do estágio", () => {
    expect(entityColor("plot", { stage: "madura" })).not.toBe(entityColor("plot", { stage: "semente" }));
  });
});

describe("caminhada que chega atrasada à tela", () => {
  // 6 tiles a 3 por tick: parte no tick 10 e chega no 12.
  const walk: ObserverMotion = {
    path: [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 2, y: 0 }, { x: 3, y: 0 }, { x: 4, y: 0 }, { x: 5, y: 0 }, { x: 6, y: 0 }],
    depart_tick: 10,
    tiles_per_tick: 3,
  };

  it("começa da origem quando foi vista no meio do primeiro tick, sem pular tiles", () => {
    expect(positionAt(walk, 10.8).x).toBeCloseTo(2.4); // o desenho cru pularia 2,4 tiles
    expect(smoothedAt(walk, 10.8, 10.8)).toEqual({ x: 0, y: 0 });
    const a = smoothedAt(walk, 11.2, 10.8).x;
    const b = smoothedAt(walk, 11.6, 10.8).x;
    expect(a).toBeGreaterThan(0);
    expect(b).toBeGreaterThan(a);
    expect(smoothedAt(walk, 12, 10.8)).toEqual({ x: 6, y: 0 }); // chega junto com o kernel
  });

  it("aberta já na segunda metade do caminho, segue o kernel sem voltar à origem", () => {
    expect(smoothedAt(walk, 11.5, 11.5)).toEqual(positionAt(walk, 11.5));
  });

  it("a memória guarda o tick em que cada trajeto foi visto", () => {
    const clock = new MotionClock();
    expect(clock.at("camps", walk, undefined, 10.5, 0)).toEqual({ x: 0, y: 0 });
    expect(clock.at("camps", walk, undefined, 12, 10_000)).toEqual({ x: 6, y: 0 });
    const next = { ...walk, depart_tick: 20 };
    expect(clock.at("camps", next, undefined, 20, 20_000)).toEqual({ x: 0, y: 0 });
  });

  it("um trajeto lento segue o kernel: o teto de velocidade não entra", () => {
    const clock = new MotionClock();
    expect(clock.at("camps", walk, undefined, 10, 0)).toEqual({ x: 0, y: 0 });
    expect(clock.at("camps", walk, undefined, 11, 100_000)).toEqual(positionAt(walk, 11));
  });
});

describe("teto de velocidade do desenho (ADR-0057)", () => {
  // 30 tiles num tick: a 72×, 36 tiles por segundo; a tela anda no máximo MAX_TILES_PER_SECOND.
  const dash: ObserverMotion = {
    path: [{ x: 0, y: 0 }, ...Array.from({ length: 30 }, (_, i) => ({ x: i + 1, y: 0 }))],
    depart_tick: 10,
    tiles_per_tick: 30,
  };

  it("fica para trás do kernel e alcança no ritmo do teto, mesmo depois de o trajeto acabar", () => {
    const clock = new MotionClock();
    expect(clock.at("camps", dash, undefined, 10, 0)).toEqual({ x: 0, y: 0 });
    // Meio segundo depois o kernel já chegou (tick 11); a tela andou 6 tiles.
    expect(clock.at("camps", dash, undefined, 11, 500)).toEqual({ x: MAX_TILES_PER_SECOND / 2, y: 0 });
    // O trajeto sumiu do estado (chegou): a tela termina a caminhada até o destino.
    expect(clock.at("camps", undefined, { x: 30, y: 0 }, 11.5, 1_000)).toEqual({ x: MAX_TILES_PER_SECOND, y: 0 });
    expect(clock.at("camps", undefined, { x: 30, y: 0 }, 13, 5_000)).toEqual({ x: 30, y: 0 });
    // Parada em outro lugar, que não é o fim do trajeto: vai direto.
    expect(clock.at("camps", undefined, { x: 2, y: 2 }, 14, 5_100)).toEqual({ x: 2, y: 2 });
  });
});
