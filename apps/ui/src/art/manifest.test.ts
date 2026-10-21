import { describe, expect, it } from "vitest";

import { loadArt } from "./load.ts";
import {
  animationFor,
  colorNumber,
  facingOf,
  frameOf,
  lookOf,
  mergeManifests,
  rooted,
  shadeOf,
  tileLook,
  weatherEffect,
  type ArtManifest,
} from "./manifest.ts";

const GENRE: ArtManifest = {
  version: 1,
  sheets: { crops: { image: "crops.png", frame_width: 32, frame_height: 32 } },
  tiles: { grass: { color: "#6dab4f" } },
  kinds: {
    plot: {
      color: "#5b3a1e",
      variants: [
        { when: { crop: "batata", stage: "broto" }, look: { sheet: "crops", frame: 7, label: "{crop}" } },
        { when: { stage: "murcha" }, look: { sheet: "crops", frame: 9, tint: "#7f7f6a" } },
      ],
      overlays: [{ when: { watered_today: true }, look: { badge: "#4fc3f7" } }],
    },
  },
  phases: { noite: { shade: 0.38 } },
  weather: { rain: { effect: "rain" } },
};

const SCENARIO: ArtManifest = {
  version: 1,
  tiles: { grass: { color: "#00ff00" } },
  visual_map: "map-visual.tmj",
  credits: "CREDITS.csv",
  avatars: {
    camps: {
      sheet: "camps",
      animations: {
        walk: { row: 4, frames: [1, 2, 3, 4, 5, 6, 7, 8], per_tile: 4 },
        lying: { row: 12, frames: [5], single: true },
      },
      idle: "idle",
      asleep: "hurt",
      actions: { move: "walk", water: "watering", "*": "thrust" },
    },
  },
};

describe("manifesto de arte (ADR-0053)", () => {
  it("as camadas se juntam na ordem, e a de cima cobre a de baixo", () => {
    const art = mergeManifests([rooted(GENRE, "/content/art/farm"), rooted(SCENARIO, "/content/art/farm_camps")]);
    expect(art.tiles?.grass).toEqual({ color: "#00ff00" });
    expect(art.sheets?.crops?.image).toBe("/content/art/farm/crops.png");
    expect(art.visual_map).toBe("/content/art/farm_camps/map-visual.tmj");
    expect(art.credits).toBe("/content/art/farm_camps/CREDITS.csv");
    expect(art.kinds?.plot?.variants).toHaveLength(2);
  });

  it("a aparência sai da variante que bate, com as sobreposições por cima", () => {
    const broto = lookOf(GENRE, "plot", { crop: "batata", stage: "broto", watered_today: true });
    expect(broto).toMatchObject({ sheet: "crops", frame: 7, label: "batata", badges: ["#4fc3f7"] });
    expect(lookOf(GENRE, "plot", { crop: "rabanete", stage: "murcha" })).toMatchObject({ frame: 9, tint: "#7f7f6a", badges: [] });
    expect(lookOf(GENRE, "plot", { crop: null, stage: null })).toEqual({ color: "#5b3a1e", badges: [] });
  });

  it("o chão de uma camada de cima fica por baixo da variante (o canteiro da Boa Vista)", () => {
    const boavista = mergeManifests([
      rooted(GENRE, "/content/art/farm"),
      rooted({ version: 1, kinds: { plot: { ground: "#8a5a35" } } }, "/content/art/farm_boavista"),
    ]);
    expect(boavista.kinds?.plot?.variants).toHaveLength(2);
    expect(lookOf(boavista, "plot", { crop: "batata", stage: "broto" })).toMatchObject({ sheet: "crops", frame: 7, ground: "#8a5a35" });
    expect(lookOf(GENRE, "plot", { crop: "batata", stage: "broto" }).ground).toBeUndefined();
  });

  it("o que o manifesto não conhece ganha cor estável e nome curto", () => {
    expect(lookOf(GENRE, "scarecrow", {})).toEqual(lookOf(GENRE, "scarecrow", {}));
    expect(lookOf(GENRE, "scarecrow", {}).label).toBe("scare");
    expect(tileLook(GENRE, "lava").color).toMatch(/^hsl\(/);
    expect(tileLook(GENRE, "").color).toBe("#000000");
  });

  it("noite, chuva e animação do avatar vêm do manifesto", () => {
    expect(shadeOf(GENRE, "noite")).toBe(0.38);
    expect(shadeOf(GENRE, "meio_dia")).toBe(0);
    expect(weatherEffect(GENRE, "rain")).toBe("rain");
    expect(weatherEffect(GENRE, "sun")).toBeUndefined();
    const camps = SCENARIO.avatars?.camps;
    expect(animationFor(camps, "water", false)).toBe("watering");
    expect(animationFor(camps, "plant", false)).toBe("thrust");
    expect(animationFor(camps, undefined, false)).toBe("idle");
    expect(animationFor(camps, "sleep", true)).toBe("hurt");
  });

  it("o avatar olha para onde anda, e o quadro sai da linha da direção", () => {
    expect(facingOf(1, 0.2, "down")).toBe("right");
    expect(facingOf(0, -1, "down")).toBe("up");
    expect(facingOf(0, 0, "left")).toBe("left");
    const walk = SCENARIO.avatars?.camps?.animations?.walk;
    const lying = SCENARIO.avatars?.camps?.animations?.lying;
    if (walk === undefined || lying === undefined) {
      throw new Error("sem animações no exemplo");
    }
    expect(frameOf(walk, 9, "down", 0)).toBe(6 * 9 + 1); // linha 4 + down (2)
    expect(frameOf(walk, 9, "right", 9.5)).toBe(7 * 9 + 2); // volta ao começo do ciclo
    expect(frameOf(lying, 9, "left", 3)).toBe(12 * 9 + 5); // uma direção só
  });

  it("cores do CSS viram números do Phaser", () => {
    expect(colorNumber("#6dab4f")).toBe(0x6dab4f);
    expect(colorNumber("hsl(0 100% 50%)")).toBe(0xff0000);
    expect(colorNumber("hsl(120 100% 25%)")).toBe(0x008000);
    expect(colorNumber("azul")).toBe(0xff00ff);
  });

  it("o carregador lê o índice e cada camada; sem gateway, fica vazio", async () => {
    const files: Record<string, unknown> = {
      "/content/art/index.json": { layers: ["farm", "farm_camps"] },
      "/content/art/farm/art.json": GENRE,
      "/content/art/farm_camps/art.json": SCENARIO,
    };
    const get = (url: string): Promise<Response> =>
      Promise.resolve(url in files ? new Response(JSON.stringify(files[url])) : new Response("", { status: 404 }));
    const { manifest: art, credits } = await loadArt(get);
    expect(art.tiles?.grass?.color).toBe("#00ff00");
    expect(art.sheets?.crops?.image).toBe("/content/art/farm/crops.png");
    expect(credits).toEqual([{ layer: "farm_camps", url: "/content/art/farm_camps/CREDITS.csv" }]);
    const empty = await loadArt(() => Promise.resolve(new Response("", { status: 404 })));
    expect(empty).toEqual({ manifest: { version: 1 }, credits: [] });
  });
});

describe("créditos da arte (ADR-0053)", () => {
  it("o CSV dos créditos aceita vírgulas e aspas dentro dos campos", async () => {
    const { parseCsv } = await import("../panels/credits.ts");
    const csv = 'file,authors,urls\ncamps.png,"bluecarrot16, ElizaWy","https://a, https://b"\r\nterrain.png,"Sharm ""Lanea""",\n';
    expect(parseCsv(csv)).toEqual([
      ["file", "authors", "urls"],
      ["camps.png", "bluecarrot16, ElizaWy", "https://a, https://b"],
      ["terrain.png", 'Sharm "Lanea"', ""],
    ]);
  });
});
