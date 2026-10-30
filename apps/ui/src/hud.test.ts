import { describe, expect, it } from "vitest";

import { needView } from "./panels/hud.ts";

describe("as barras do corpo (M21)", () => {
  it("a fome aparece como saciedade: cheia é boa, como a energia", () => {
    expect(needView("fome", 6)).toEqual({ label: "saciedade", value: 94 });
    expect(needView("fome", 100)).toEqual({ label: "saciedade", value: 0 });
    expect(needView("energia", 76)).toEqual({ label: "energia", value: 76 });
  });
});
