import { describe, expect, it } from "vitest";

import { loadArt } from "./load.ts";
import {
  animationFor,
  autotileMask,
  colorNumber,
  facedTile,
  facingOf,
  frameOf,
  inUseFrame,
  lookOf,
  loopFrame,
  mergeManifests,
  rooted,
  seatAt,
  seatedAnimation,
  shadeOf,
  tileLook,
  visualMapFor,
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

  it("cada variante do mapa tem o seu mapa visual, pelo id do mapa (ADR-0070)", () => {
    const morada: ArtManifest = {
      version: 1,
      visual_map: "map-visual.tmj",
      visual_maps: { "farm_morada_do_sol-b": "map-visual-b.tmj" },
    };
    const art = mergeManifests([rooted(GENRE, "/content/art/farm"), rooted(morada, "/content/art/farm_morada_do_sol")]);
    expect(visualMapFor(art, "farm_morada_do_sol-b")).toBe("/content/art/farm_morada_do_sol/map-visual-b.tmj");
    expect(visualMapFor(art, "farm_morada_do_sol")).toBe("/content/art/farm_morada_do_sol/map-visual.tmj");
    expect(visualMapFor(art, undefined)).toBe("/content/art/farm_morada_do_sol/map-visual.tmj");
  });

  it("a aparência sai da variante que bate, com as sobreposições por cima", () => {
    const broto = lookOf(GENRE, "plot", { crop: "batata", stage: "broto", watered_today: true });
    expect(broto).toMatchObject({ sheet: "crops", frame: 7, label: "batata", badges: ["#4fc3f7"] });
    expect(lookOf(GENRE, "plot", { crop: "rabanete", stage: "murcha" })).toMatchObject({ frame: 9, tint: "#7f7f6a", badges: [] });
    expect(lookOf(GENRE, "plot", { crop: null, stage: null })).toEqual({ color: "#5b3a1e", badges: [] });
  });

  it("o canteiro adubado ganha a marca no outro canto, separada da gota da rega", () => {
    const art = { version: 1 as const, kinds: { plot: { overlays: [
      { when: { watered_today: true }, look: { badge: "#4fc3f7" } },
      { when: { adubado: true }, look: { mark: "#e0a33a" } },
    ] } } };
    expect(lookOf(art, "plot", { adubado: true })).toMatchObject({ badges: [], marks: ["#e0a33a"] });
    expect(lookOf(art, "plot", { adubado: true, watered_today: true })).toMatchObject({ badges: ["#4fc3f7"], marks: ["#e0a33a"] });
    expect(lookOf(art, "plot", { adubado: false }).marks).toBeUndefined();
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
    expect(empty).toEqual({ manifest: { version: 1 }, credits: [], layers: [] });
  });

});

describe("a arte da fase 1 do escritório", () => {
  it("sentado, a ação pode ter animação própria: digitar ao trabalhar", () => {
    const art = { sheet: "camps", seated: "sit", seated_actions: { work: "type" } };
    expect(seatedAnimation(art, "work")).toBe("type");
    expect(seatedAnimation(art, "wait")).toBe("sit");
    expect(seatedAnimation(art, undefined)).toBe("sit");
    expect(seatedAnimation({ sheet: "camps", seated: "sit" }, "work")).toBe("sit"); // a LPC
  });

  it("a mesa em uso: alguém sentado de frente para ela faz uma das ações dela", () => {
    expect(facedTile({ x: 5, y: 7 }, "up")).toEqual({ x: 5, y: 6 });
    expect(facedTile({ x: 5, y: 7 }, "left")).toEqual({ x: 4, y: 7 });
    const screen = { actions: ["work"], frames: [1, 2, 3], fps: 2 };
    expect(inUseFrame(screen, ["work"], 0)).toBe(1);
    expect(inUseFrame(screen, ["work"], 0.6)).toBe(2);
    expect(inUseFrame(screen, ["wait", "work"], 1.6)).toBe(1); // o ciclo recomeça
    expect(inUseFrame(screen, ["wait"], 1)).toBeUndefined(); // sentado, mas sem trabalhar
    expect(inUseFrame(undefined, ["work"], 1)).toBeUndefined(); // a LPC não tem
  });

  it("o encosto da cadeira vem com a aparência", () => {
    const art: ArtManifest = { version: 1, kinds: { chair: { sheet: "cadeira", frame: 0, front: 1, seat: "up" } } };
    expect(lookOf(art, "chair", {}).front).toBe(1);
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

describe("o assento (ADR-0078)", () => {
  const office: ArtManifest = { version: 1, kinds: { chair: { sheet: "objects", frame: 3, seat: "up" }, desk: { sheet: "objects", frame: 0 } } };
  const things = {
    cadeira: { kind: "chair", position: { x: 5, y: 7 } },
    mesa: { kind: "desk", position: { x: 5, y: 6 } },
    pedido: { kind: "ticket" },
  };

  it("só quem está em cima do tile do assento senta, olhando para o lado dele", () => {
    expect(seatAt(office, things, { x: 5, y: 7 })).toBe("up");
    expect(seatAt(office, things, { x: 5, y: 6 })).toBeUndefined(); // a mesa não é assento
    expect(seatAt(office, things, { x: 5, y: 7.4 })).toBeUndefined(); // no meio de um passo
    expect(seatAt({ version: 1 }, things, { x: 5, y: 7 })).toBeUndefined(); // a fazenda não tem
  });

  it("a cadeira de lado da copa senta virado para a mesinha, pelo atributo (ADR-0082)", () => {
    const copa: ArtManifest = {
      version: 1,
      kinds: {
        copa_chair: {
          sheet: "cadeira_lado",
          variants: [
            { when: { virada: "direita" }, look: { frame: 0, seat: "right" } },
            { when: { virada: "esquerda" }, look: { frame: 1, seat: "left" } },
          ],
        },
      },
    };
    const chairs = {
      a: { kind: "copa_chair", position: { x: 12, y: 11 }, attributes: { virada: "direita" } },
      b: { kind: "copa_chair", position: { x: 14, y: 11 }, attributes: { virada: "esquerda" } },
    };
    expect(seatAt(copa, chairs, { x: 12, y: 11 })).toBe("right");
    expect(seatAt(copa, chairs, { x: 14, y: 11 })).toBe("left");
    expect(lookOf(copa, "copa_chair", { virada: "esquerda" }).frame).toBe(1);
  });
});

describe("a arte nova do escritório (ADR-0082)", () => {
  it("a TV e o bebedouro se mexem sempre, no laço deles", () => {
    expect(loopFrame({ frames: [1, 2], fps: 2 }, 0)).toBe(1);
    expect(loopFrame({ frames: [1, 2], fps: 2 }, 0.6)).toBe(2);
    expect(loopFrame({ frames: [1, 2], fps: 2 }, 1.1)).toBe(1);
    expect(loopFrame(undefined, 3)).toBeUndefined();
  });

  it("a divisória escolhe o quadro pela máscara dos vizinhos", () => {
    // Uma fileira de cubículos: a linha de cima e as colunas 0 e 2 descendo.
    const rows = ["PPP", "P.P", "P.P"];
    const typeAt = (x: number, y: number): string => rows[y]?.[x] ?? "";
    expect(autotileMask(typeAt, 0, 0)).toBe(2 | 4); // canto: leste e sul
    expect(autotileMask(typeAt, 1, 0)).toBe(2 | 8); // reta leste-oeste
    expect(autotileMask(typeAt, 2, 0)).toBe(4 | 8); // canto: sul e oeste
    expect(autotileMask(typeAt, 0, 2)).toBe(1); // a ponta de baixo
  });
});
