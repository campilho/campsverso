/** As janelas no padrão da tela retrô (docs/design/briefing-tela-4.md, §2 a §4; ADR-0092): onde o
 * menu abre, os comandos de cada mundo e os blocos dos créditos. */
import { describe, expect, it } from "vitest";

import { creditBlocks, creditRows, licenseKind, openingOf, referredLayer } from "./credits.ts";
import { commandsFor } from "./help.ts";
import { TAIL, placeMenu } from "./menu.ts";

describe("o menu abre colado ao clique, sem sair do monitor", () => {
  const screen = { left: 0, top: 0, right: 800, bottom: 600 };
  const size = { width: 300, height: 170 };

  it("à direita do clique, com o rabicho na altura dele", () => {
    const at = placeMenu({ x: 100, y: 200 }, size, screen);
    expect(at).toEqual({ left: 100 + TAIL, top: 178, side: "right", tail: 22 });
  });

  it("vira para a esquerda quando não cabe à direita", () => {
    const at = placeMenu({ x: 700, y: 200 }, size, screen);
    expect(at.side).toBe("left");
    expect(at.left).toBe(700 - TAIL - 300);
  });

  it("sobe quando não cabe embaixo, e o rabicho continua apontando para o clique", () => {
    const at = placeMenu({ x: 100, y: 580 }, size, screen);
    expect(at.top).toBe(600 - 8 - 170);
    expect(at.top + at.tail).toBeLessThanOrEqual(600 - 8); // o rabicho dentro do menu
    expect(at.tail).toBe(170 - 12);
  });
});

describe("os comandos que valem neste mundo e nesta tela", () => {
  it("no escritório: sem arrastar e sem espaço, e o P só no sandbox", () => {
    const office = commandsFor({ farm: false, scrolls: false, pausable: false });
    expect(office.mouse.map((m) => [m.gesture, m.shift])).toEqual([
      ["clique", false],
      ["direito", false],
      ["clique", true],
    ]);
    expect(office.mouse[1]?.text).not.toContain("grama");
    expect(office.keys.map((k) => k.keys.join(" "))).toEqual(["setas", "E", "Esc", "?"]);
    expect(commandsFor({ farm: false, scrolls: false, pausable: true }).keys.map((k) => k.keys.join(" "))).toEqual(["setas", "E", "Esc", "P", "?"]);
  });

  it("na fazenda, com o mapa maior que a tela: a grama, arrastar e o espaço", () => {
    const farm = commandsFor({ farm: true, scrolls: true, pausable: true });
    expect(farm.mouse[1]?.text).toContain("da grama");
    expect(farm.mouse.at(-1)).toEqual({ gesture: "arrastar", shift: false, text: "rola o mapa" });
    expect(farm.keys.map((k) => k.keys.join(" "))).toEqual(["setas", "E", "Esc", "espaço", "P", "?"]);
  });
});

describe("os créditos por grupo de autores", () => {
  const header = "file,source,authors,licenses,urls,notes";
  const office = creditRows(
    "office",
    [
      header,
      "terreno.png,montado por make arte-escritorio,Fernando Campilho e Claude,MIT,https://github.com/campilho/campsverso,o carpete",
      "mesa_dev.png,desenho próprio do Campsverso,Fernando Campilho e Claude,MIT,https://github.com/campilho/campsverso,a mesa",
      "cadeira.png,desenho próprio do Campsverso,Fernando Campilho e Claude,MIT,https://github.com/campilho/campsverso,a cadeira",
    ].join("\n"),
  );
  const scenario = creditRows(
    "office_campsverso",
    [header, "map-visual.tmj,gerado por make mapa-visual,ver cartridges/office/art/CREDITS.csv,MIT,https://github.com/campilho/campsverso,"].join("\n"),
  );

  it("no escritório, um bloco só: o mapa visual entra como peça do bloco que ele monta", () => {
    const blocks = creditBlocks([...office, ...scenario]);
    expect(blocks).toHaveLength(1);
    expect(blocks[0]?.authors).toBe("Fernando Campilho e Claude");
    expect(blocks[0]?.licenses).toEqual(["MIT"]);
    expect(blocks[0]?.pieces.map((p) => p.file)).toEqual(["terreno.png", "mesa_dev.png", "cadeira.png", "map-visual.tmj"]);
    expect(blocks[0]?.source).toBe("desenho próprio do Campsverso"); // a origem mais comum
    expect(openingOf([...office, ...scenario])).toMatch(/^Toda a arte deste mundo é desenho próprio/);
  });

  it("na fazenda, um bloco por autores e licenças, e a frase do LPC", () => {
    const farm = creditRows(
      "farm",
      [
        header,
        'terrain.png,LPC,Daniel Eddeland (daneeklu),"CC-BY-SA 3.0, GPL 3.0",https://opengameart.org/content/lpc-farming,a terra',
        'objects.png,LPC,Daniel Eddeland (daneeklu),"CC-BY-SA 3.0, GPL 3.0",https://opengameart.org/content/lpc-farming,os objetos',
        "camps.png,LPC,ElizaWy,CC0,https://opengameart.org/content/lpc-hair,o cabelo",
        'map-visual.tmj,gerado,ver os créditos do gênero farm,"CC-BY-SA 3.0, GPL 3.0",,',
      ].join("\n"),
    );
    const blocks = creditBlocks(farm);
    expect(blocks.map((b) => [b.authors, b.licenses, b.pieces.length])).toEqual([
      ["Daniel Eddeland (daneeklu)", ["CC-BY-SA 3.0", "GPL 3.0"], 3],
      ["ElizaWy", ["CC0"], 1],
    ]);
    expect(openingOf(farm)).toMatch(/Liberated Pixel Cup/);
  });

  it("lê a camada para onde a linha remete e a cor de cada licença", () => {
    expect(referredLayer("ver cartridges/office/art/CREDITS.csv")).toBe("office");
    expect(referredLayer("ver os créditos do gênero farm")).toBe("farm");
    expect(referredLayer("Fernando Campilho e Claude")).toBeUndefined();
    expect(["MIT", "CC-BY-SA 3.0", "GPL 3.0+", "CC0", "OFL 1.1", "OGA-BY 3.0"].map(licenseKind)).toEqual(["mit", "ccbysa", "gpl", "cc0", "ofl", "outra"]);
  });
});
