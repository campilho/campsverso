import { describe, expect, it } from "vitest";

import { DARK, LIT, PENUMBRA, lightLevels } from "./light.ts";
import type { Lights } from "./manifest.ts";

const LIGHTS: Lights = {
  schedule: [],
  color: "#0b0f24",
  penumbra: 0.4,
  dark: 0.7,
  lamps: [[2.5, 2.5]],
  lamp_radius: 30,
  lamp_border: 6,
  lit: [{ x: 0, y: 150, w: 200, h: 10 }],
  lantern: { avatar: "vigia", radii: [10, 14, 18, 22] },
};
const W = 200;
const H = 160;
const at = (levels: Uint8Array | undefined, x: number, y: number): number | undefined => levels?.[y * W + x];

describe("a luz da noite do escritório (ADR-0082)", () => {
  it("de dia, nada a pintar", () => {
    expect(lightLevels(LIGHTS, "day", W, H)).toBeUndefined();
    expect(lightLevels(undefined, "lamps", W, H)).toBeUndefined();
  });

  it("com as luminárias, poças acesas com a borda em xadrez e penumbra fora delas", () => {
    const levels = lightLevels(LIGHTS, "lamps", W, H);
    expect(at(levels, 80, 80)).toBe(LIT); // o centro da luminária
    expect(at(levels, 80 + 29, 80)).toBe(LIT);
    expect([at(levels, 80 + 32, 80), at(levels, 80 + 33, 80)].sort()).toEqual([LIT, PENUMBRA]); // a borda
    expect(at(levels, 80 + 40, 80)).toBe(PENUMBRA);
    expect(at(levels, 5, 5)).toBe(PENUMBRA);
    expect(at(levels, 5, 155)).toBe(LIT); // o corredor, sempre aceso
  });

  it("a luz é achatada na vertical, como na prévia", () => {
    const levels = lightLevels(LIGHTS, "lamps", W, H);
    expect([at(levels, 80 + 32, 80), at(levels, 80 + 32, 81)].sort()).toEqual([LIT, PENUMBRA]); // na borda
    expect(at(levels, 80, 80 + 32)).toBe(PENUMBRA); // 32 × 1,15 já passa da borda
  });

  it("no escuro, só a lanterna acende, em anéis do aceso ao escuro", () => {
    const levels = lightLevels(LIGHTS, "dark", W, H, { x: 100, y: 60 });
    expect(at(levels, 100, 60)).toBe(LIT);
    expect([at(levels, 112, 60), at(levels, 113, 60)].sort()).toEqual([LIT, PENUMBRA]);
    expect(at(levels, 116, 60)).toBe(PENUMBRA);
    expect([at(levels, 120, 60), at(levels, 121, 60)].sort()).toEqual([PENUMBRA, DARK]);
    expect(at(levels, 130, 60)).toBe(DARK);
    expect(at(levels, 80, 80)).toBe(DARK); // a luminária apagada
    expect(at(levels, 5, 155)).toBe(LIT);
    const nobody = lightLevels(LIGHTS, "dark", W, H);
    expect(at(nobody, 100, 60)).toBe(DARK); // sem o vigia, a sala toda escura
  });
});
