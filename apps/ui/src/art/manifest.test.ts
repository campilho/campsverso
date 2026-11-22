import { describe, expect, it } from "vitest";

import { loadArt } from "./load.ts";
import {
  animationFor,
  autotileMask,
  badgeOf,
  cardPlacements,
  carryAnimation,
  colorNumber,
  facedTile,
  facingOf,
  frameOf,
  inUseFrame,
  lightMode,
  roomLight,
  switchLit,
  lookOf,
  plaqueText,
  loopFrame,
  mergeManifests,
  minuteOfDay,
  rooted,
  seatAt,
  seatFacing,
  seatedAnimation,
  shadeOf,
  sitSpot,
  tileLook,
  timedTile,
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

  it("uma camada inclui outro JSON dela (o baloes.json gerado), e o art.json vale por cima", async () => {
    const files: Record<string, unknown> = {
      "/content/art/index.json": { layers: ["office"] },
      "/content/art/office/art.json": { version: 1, include: ["baloes.json"], bubbles: { icons: { actions: { work: "trabalhar" } } } },
      "/content/art/office/baloes.json": {
        sheets: { icones: { image: "icones.png", frame_width: 16, frame_height: 16 } },
        bubbles: { sheet: "baloes", icons: { sheet: "icones", columns: 8, frames: { trabalhar: [0, 0] } } },
      },
    };
    const get = (url: string): Promise<Response> =>
      Promise.resolve(url in files ? new Response(JSON.stringify(files[url])) : new Response("", { status: 404 }));
    const { manifest: art } = await loadArt(get);
    expect(art.sheets?.icones?.image).toBe("/content/art/office/icones.png");
    expect(art.bubbles?.icons).toEqual({ sheet: "icones", columns: 8, frames: { trabalhar: [0, 0] }, actions: { work: "trabalhar" } });
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

  it("o assento virado para a mesinha, livre e mais perto de quem vai almoçar (ADR-0082)", () => {
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
        copa_table: { sheet: "mesinha", frame: 0 },
      },
    };
    const things = {
      a: { kind: "copa_chair", position: { x: 12, y: 11 }, attributes: { virada: "direita" } },
      b: { kind: "copa_chair", position: { x: 14, y: 11 }, attributes: { virada: "esquerda" } },
      c: { kind: "copa_chair", position: { x: 16, y: 11 }, attributes: { virada: "direita" } },
      mesa: { kind: "copa_table", position: { x: 13, y: 11 } },
    };
    const table = { x: 13, y: 11 };
    expect(seatFacing(copa, things, table, { x: 10, y: 9 })).toEqual({ x: 12, y: 11 });
    expect(seatFacing(copa, things, table, { x: 15, y: 9 })).toEqual({ x: 14, y: 11 });
    expect(seatFacing(copa, things, table, { x: 10, y: 9 }, [{ x: 12, y: 11 }])).toEqual({ x: 14, y: 11 });
    expect(seatFacing(copa, things, table, { x: 10, y: 9 }, [{ x: 12, y: 11 }, { x: 14, y: 11 }])).toBeUndefined();
    // A cadeira c está virada para a direita, para a outra mesinha: não serve a esta.
    expect(seatFacing(copa, things, { x: 17, y: 11 }, { x: 10, y: 9 })).toEqual({ x: 16, y: 11 });
    expect(seatFacing(copa, things, { x: 18, y: 9 }, { x: 10, y: 9 })).toBeUndefined(); // o bebedouro não tem
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

describe("as animações e a noite do escritório (ADR-0082)", () => {
  const camps = {
    sheet: "camps",
    animations: { eat: { row: 21, frames: [0, 1, 2, 3], facings: ["left", "right"] as const } },
    sit_on: { tv: "sofa", videogame: "sofa" },
    carry: { marmita: { walk: "carry", idle: "carry_idle" } },
  };

  it("comer sentado só tem os lados: a linha sai da lista de direções da animação", () => {
    const eat = camps.animations.eat;
    expect(frameOf(eat, 8, "left", 1)).toBe(21 * 8 + 1);
    expect(frameOf(eat, 8, "right", 2)).toBe(22 * 8 + 2);
    expect(frameOf(eat, 8, "up", 0)).toBe(21 * 8); // sem a direção, a primeira
  });

  it("no tapete, logo acima ou abaixo do sofá, quem vê TV ou joga senta nele, na coluna dele", () => {
    const things = { sofa: { kind: "sofa", position: { x: 16, y: 5 } }, tv: { kind: "tv", position: { x: 16, y: 2 } } };
    for (const x of [15, 16, 17]) {
      expect(sitSpot(camps, "tv", things, { x, y: 4 })).toEqual({ x, y: 5 });
      expect(sitSpot(camps, "videogame", things, { x, y: 6 })).toEqual({ x, y: 5 });
    }
    expect(sitSpot(camps, "tv", things, { x: 14, y: 4 })).toBeUndefined(); // fora do sofá
    expect(sitSpot(camps, "tv", things, { x: 16, y: 3 })).toBeUndefined(); // longe demais
    expect(sitSpot(camps, "drink", things, { x: 16, y: 4 })).toBeUndefined(); // outra ação
    expect(sitSpot(undefined, "tv", things, { x: 16, y: 4 })).toBeUndefined();
  });

  it("a TV mostra o jogo ou o telejornal de quem está no sofá, em qualquer lugar da sala", () => {
    const tv = [
      { actions: ["videogame"], frames: [1, 2, 3], fps: 3, anywhere: true },
      { actions: ["tv"], frames: [4, 5, 6], fps: 1, anywhere: true },
    ];
    expect(inUseFrame(tv, [], 0, ["videogame"])).toBe(1);
    expect(inUseFrame(tv, [], 1.2, ["tv"])).toBe(5);
    expect(inUseFrame(tv, ["tv"], 0, [])).toBeUndefined(); // só vale quem faz, não quem está ao lado
    expect(inUseFrame(tv, [], 0, ["work"])).toBeUndefined(); // desligada
  });

  it("com a marmita na mão, anda e espera carregando; sem ela, nada muda", () => {
    expect(carryAnimation(camps, { carregando: "marmita" }, true)).toBe("carry");
    expect(carryAnimation(camps, { carregando: "marmita" }, false)).toBe("carry_idle");
    expect(carryAnimation(camps, { carregando: null }, true)).toBeUndefined();
    expect(carryAnimation(camps, {}, true)).toBeUndefined();
    expect(carryAnimation(camps, { carregando: "caixa" }, true)).toBeUndefined();
  });

  it("a luz segue a hora do mundo: dia, as luminárias das 18:00 às 21:00, e o escuro até amanhecer", () => {
    const lights = {
      schedule: [
        { from: "18:00", mode: "lamps" as const },
        { from: "06:00", mode: "day" as const },
        { from: "21:00", mode: "dark" as const },
      ],
      color: "#0b0f24",
      penumbra: 0.4,
      dark: 0.7,
    };
    expect(minuteOfDay("18:30")).toBe(18 * 60 + 30);
    expect(minuteOfDay("09:05:12")).toBe(9 * 60 + 5);
    expect(minuteOfDay("--:--")).toBeUndefined();
    expect(lightMode(lights, minuteOfDay("12:10"))).toBe("day");
    expect(lightMode(lights, minuteOfDay("18:00"))).toBe("lamps");
    expect(lightMode(lights, minuteOfDay("20:59"))).toBe("lamps");
    expect(lightMode(lights, minuteOfDay("21:00"))).toBe("dark");
    expect(lightMode(lights, minuteOfDay("03:00"))).toBe("dark"); // a madrugada é a noite da véspera
    expect(lightMode(undefined, 23 * 60)).toBe("day"); // a fazenda não tem
    expect(lightMode(lights, undefined)).toBe("day");
    // O interruptor do mundo (ADR-0088): de dia, nada muda; à noite, ele manda.
    expect(roomLight(lights, minuteOfDay("12:00"), false)).toBe("day");
    expect(roomLight(lights, minuteOfDay("22:00"), true)).toBe("lamps");
    expect(roomLight(lights, minuteOfDay("19:00"), false)).toBe("dark"); // apagaram antes das 21:00
    expect(roomLight(lights, minuteOfDay("22:00"), undefined)).toBe("dark"); // sem interruptor, a agenda
    const office = { interruptor: { kind: "light_switch", attributes: { acesa: true } }, quadro: { kind: "board", attributes: {} } };
    expect(switchLit(office)).toBe(true);
    expect(switchLit({ ...office, interruptor: { kind: "light_switch", attributes: { acesa: false } } })).toBe(false);
    expect(switchLit({ quadro: office.quadro })).toBeUndefined();
  });

  it("a janela vira a de noite e o relógio anda com a hora, nas duas metades do tile", () => {
    const tiles = { night: { "janela-meioA": "janela-noite-meioA" }, clock: "relogio" };
    expect(timedTile(tiles, "janela-meioA-t", true, 0)).toBe("janela-noite-meioA-t");
    expect(timedTile(tiles, "janela-meioA-b", false, 0)).toBe("janela-meioA-b");
    expect(timedTile(tiles, "relogio-10-t", false, 15 * 60 + 20)).toBe("relogio-3-t");
    expect(timedTile(tiles, "relogio-10-b", true, 0)).toBe("relogio-0-b");
    expect(timedTile(tiles, "relogio-10-b", true, undefined)).toBe("relogio-10-b");
    expect(timedTile(tiles, "quadro-meio-t", true, 0)).toBe("quadro-meio-t");
    expect(timedTile(undefined, "janela-meioA-t", true, 0)).toBe("janela-meioA-t");
  });

  it("as fichas do quadro vão na coluna do estado, na ordem do número, até quatro por coluna", () => {
    const cards = {
      sheet: "fichas",
      x: 64,
      y: 19,
      column_width: 32,
      first_inset: 6,
      inset: 3,
      columns: { a_fazer: 0, fazendo: 1, entregue: 2, aceito: 2 },
      state_frames: { aceito: 4 },
      size_frames: { P: 2, M: 1, G: 0 },
    };
    const ticket = (numero: number, estado: string, tamanho = "P") => ({ kind: "ticket", attributes: { numero, estado, tamanho } });
    const things = {
      t2: ticket(2, "a_fazer", "G"),
      t1: ticket(1, "a_fazer"),
      t3: ticket(3, "fazendo", "M"),
      t4: ticket(4, "aceito"),
      t5: ticket(5, "entregue"),
      mesa: { kind: "desk", position: { x: 4, y: 4 }, attributes: {} },
      t9: ticket(9, "cancelado"),
    };
    expect(cardPlacements(cards, things)).toEqual([
      { x: 70, y: 19, frame: 2 }, // o 1, a fazer, P
      { x: 82, y: 19, frame: 0 }, // o 2, a fazer, G
      { x: 99, y: 19, frame: 1 }, // o 3, fazendo, M
      { x: 131, y: 19, frame: 4 }, // o 4, aceito
      { x: 143, y: 19, frame: 2 }, // o 5, entregue, P
    ]);
    const many = Object.fromEntries([1, 2, 3, 4, 5, 6].map((n) => [`t${String(n)}`, ticket(n, "a_fazer")]));
    const shown = cardPlacements(cards, many);
    expect(shown).toHaveLength(4); // as quatro mais novas
    expect(shown[2]).toEqual({ x: 70, y: 31, frame: 2 }); // a terceira, embaixo da primeira
    expect(cardPlacements(undefined, things)).toEqual([]);
  });

  it("a ficha com PR ganha o selo do estado dele, e a fechada sem mesclar fica sem (ADR-0083)", () => {
    const pr = (pr_estado: string, pr_ci?: string) => ({ pr: 1, pr_estado, ...(pr_ci === undefined ? {} : { pr_ci }) });
    expect(badgeOf(pr("aberto"))).toBe("pr");
    expect(badgeOf(pr("aberto", "pending"))).toBe("pr");
    expect(badgeOf(pr("aberto", "success"))).toBe("ci_verde");
    expect(badgeOf(pr("aberto", "failure"))).toBe("ci_vermelho");
    expect(badgeOf(pr("mesclado", "success"))).toBe("mesclado");
    expect(badgeOf(pr("fechado"))).toBeUndefined();
    expect(badgeOf({})).toBeUndefined();
    const cards = {
      sheet: "fichas",
      x: 64,
      y: 19,
      column_width: 32,
      first_inset: 6,
      inset: 3,
      columns: { entregue: 2, aceito: 2 },
      frame: 3,
      badge: { sheet: "selos", at: [4, 4] as const, frames: { pr: 0, ci_verde: 1, ci_vermelho: 2, mesclado: 3 } },
    };
    const things = {
      t1: { kind: "ticket", attributes: { numero: 1, estado: "aceito", ...pr("mesclado", "success") } },
      t2: { kind: "ticket", attributes: { numero: 2, estado: "entregue", ...pr("aberto", "success") } },
      t3: { kind: "ticket", attributes: { numero: 3, estado: "entregue" } },
    };
    expect(cardPlacements(cards, things).map((c) => c.badge)).toEqual([3, 1, undefined]);
  });

  it("a placa escreve o commit curto e o dia dele numa linha", () => {
    expect(plaqueText({ commit: "4b7ab259633452ca529e0e1d9e0244476a96d2ae", date: "2026-11-21T01:38:37-03:00" })).toBe("4b7ab25 21/11");
    expect(plaqueText({ commit: "4b7ab259633452ca529e0e1d9e0244476a96d2ae", date: "" })).toBe("4b7ab25");
  });
});
