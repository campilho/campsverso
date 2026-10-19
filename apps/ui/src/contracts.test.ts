import { CONTRACT_TYPES, type Envelope } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

describe("contratos vistos pela UI", () => {
  it("conhecem a visibilidade de cada tipo", () => {
    expect(Object.keys(CONTRACT_TYPES)).toHaveLength(59);
    expect(CONTRACT_TYPES["campsverso.rules.effect_applied.v1"].visibility).toBe("internal");
    expect(CONTRACT_TYPES["campsverso.perception.updated.v1"].visibility).toBe("agent");
  });

  it("tipam o payload pelo tipo do evento", () => {
    const event: Envelope<"campsverso.world.clock.phase_changed.v1"> = {
      specversion: "1.0",
      id: "019a1b2c-3d4e-7f60-8a9b-0c1d2e3f4a5b",
      source: "/kernel/farm-camps-01",
      type: "campsverso.world.clock.phase_changed.v1",
      time: "2026-10-11T22:00:00Z",
      datacontenttype: "application/json",
      dataschema: "contracts://events/world/clock.phase_changed.v1",
      worldid: "farm-camps-01",
      cartridge: "farm_camps",
      seq: 1,
      provenance: "simulated",
      visibility: "world",
      data: { phase: "amanhecer", day: 2 },
    };
    expect(event.data.day).toBe(2);
  });
});
