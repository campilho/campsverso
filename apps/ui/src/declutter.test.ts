import { describe, expect, it } from "vitest";

import { declutter, type Label } from "./declutter.ts";

const label = (id: string, text: string, x: number, y = 100, width = 120, height = 16): Label => ({ id, text, x, y, width, height });

describe("os rótulos sobre as cabeças sem se encavalar (18/nov)", () => {
  it("dois iguais lado a lado viram um só, entre os dois", () => {
    const placed = declutter([label("gerente", "Jogando videogame", 560), label("camps", "Jogando videogame", 528)]);
    expect(placed.get("camps")).toEqual({ x: 544, y: 100, visible: true });
    expect(placed.get("gerente")).toEqual({ x: 544, y: 100, visible: false });
  });

  it("na altura do mais alto dos dois", () => {
    const placed = declutter([label("camps", "Almoçando", 400, 360), label("gerente", "Almoçando", 464, 356)]);
    expect(placed.get("camps")).toEqual({ x: 432, y: 356, visible: true });
  });

  it("diferentes que se tocam se empilham: o da direita sobe", () => {
    const placed = declutter([label("camps", "Almoçando", 400, 100, 70), label("gerente", "Tomando um café", 440, 100, 100)]);
    expect(placed.get("camps")).toEqual({ x: 400, y: 100, visible: true });
    expect(placed.get("gerente")).toEqual({ x: 440, y: 82, visible: true });
  });

  it("longe um do outro, ninguém se mexe", () => {
    const placed = declutter([label("camps", "Trabalhando", 100), label("vigia", "Trabalhando", 400)]);
    expect(placed.get("camps")).toEqual({ x: 100, y: 100, visible: true });
    expect(placed.get("vigia")).toEqual({ x: 400, y: 100, visible: true });
  });

  it("três: o par igual vira um, e o diferente sobe acima dele", () => {
    const placed = declutter([
      label("a", "Almoçando", 400, 100, 70),
      label("b", "Almoçando", 432, 100, 70),
      label("c", "Jogando fora", 470, 100, 80),
    ]);
    expect(placed.get("a")).toEqual({ x: 416, y: 100, visible: true });
    expect(placed.get("b")?.visible).toBe(false);
    expect(placed.get("c")).toEqual({ x: 470, y: 82, visible: true });
  });
});
