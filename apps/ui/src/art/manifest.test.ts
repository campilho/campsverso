import { describe, expect, it } from "vitest";

import { loadArt } from "./load.ts";
import {
  animationFor,
  colorNumber,
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
  avatars: { camps: { idle: "idle", asleep: "hurt", actions: { move: "walk", water: "watering", "*": "thrust" } } },
};

describe("manifesto de arte (ADR-0053)", () => {
  it("as camadas se juntam na ordem, e a de cima cobre a de baixo", () => {
    const art = mergeManifests([rooted(GENRE, "/content/art/farm"), rooted(SCENARIO, "/content/art/farm_camps")]);
    expect(art.tiles?.grass).toEqual({ color: "#00ff00" });
    expect(art.sheets?.crops?.image).toBe("/content/art/farm/crops.png");
    expect(art.visual_map).toBe("/content/art/farm_camps/map-visual.tmj");
    expect(art.kinds?.plot?.variants).toHaveLength(2);
  });

  it("a aparência sai da variante que bate, com as sobreposições por cima", () => {
    const broto = lookOf(GENRE, "plot", { crop: "batata", stage: "broto", watered_today: true });
    expect(broto).toMatchObject({ sheet: "crops", frame: 7, label: "batata", badges: ["#4fc3f7"] });
    expect(lookOf(GENRE, "plot", { crop: "rabanete", stage: "murcha" })).toMatchObject({ frame: 9, tint: "#7f7f6a", badges: [] });
    expect(lookOf(GENRE, "plot", { crop: null, stage: null })).toEqual({ color: "#5b3a1e", badges: [] });
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
    const art = await loadArt(get);
    expect(art.tiles?.grass?.color).toBe("#00ff00");
    expect(art.sheets?.crops?.image).toBe("/content/art/farm/crops.png");
    expect(await loadArt(() => Promise.resolve(new Response("", { status: 404 })))).toEqual({ version: 1 });
  });
});
