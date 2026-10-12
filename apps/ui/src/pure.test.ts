import type { EnvelopeV1, ObserverMotion, ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { positionAt } from "./motion.ts";
import { applyMergePatch } from "./patch.ts";
import { entityColor, tileColor } from "./render/skin.ts";
import { MAX_AHEAD, clockText, estimateTick } from "./simclock.ts";
import { Store } from "./store.ts";
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

  it("a loja aplica o patch e só reinicia a estimativa quando o tick muda", () => {
    const store = new Store();
    store.applyWelcome(
      { type: "campsverso.realtime.welcome.v1", worldid: "w", view: "player", avatar_id: "camps", commands: [], state: state(), events: [] },
      1000,
    );
    store.applyUpdate({ type: "campsverso.realtime.update.v1", patch: { clock: { paused: true } }, events: [] }, 2000);
    expect(store.state?.clock.paused).toBe(true);
    expect(store.receivedAtMs).toBe(1000);
    store.applyUpdate({ type: "campsverso.realtime.update.v1", patch: { tick: 101 }, events: [] }, 3000);
    expect(store.receivedAtMs).toBe(3000);
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

describe("relógio estimado", () => {
  it("avança pela escala só no contínuo sem pausa, com teto", () => {
    expect(estimateTick(state(), 0, 10_000)).toBeCloseTo(100 + (10 * 72) / 60);
    expect(estimateTick(state({ clock: { mode: "continuous", scale: 72, paused: true } }), 0, 10_000)).toBe(100);
    expect(estimateTick(state({ clock: { mode: "max", scale: 72, paused: false } }), 0, 10_000)).toBe(100);
    expect(estimateTick(state(), 0, 10_000_000)).toBe(100 + MAX_AHEAD);
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

  it("cor do canteiro vem do estágio", () => {
    expect(entityColor("plot", { stage: "madura" })).not.toBe(entityColor("plot", { stage: "semente" }));
  });
});
