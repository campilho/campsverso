import { CONTRACT_TYPES, type Envelope } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

describe("contratos vistos pela UI", () => {
  it("conhecem a visibilidade de cada tipo", () => {
    // 78 eventos e 11 comandos: a fala, o relógio que alcança o real e o pedido do escritório
    // chegaram no M23 (ADR-0078); os avisos do orçamento na v2, os tetos mudados e o comando deles,
    // no M24 (ADR-0080), a sessão com o tick em milissegundos (ADR-0081), o passo na oficina e o
    // robô da bancada, que começa e termina.
    expect(Object.keys(CONTRACT_TYPES)).toHaveLength(89);
    expect(CONTRACT_TYPES["campsverso.workshop.robot_called.v1"].visibility).toBe("observer");
    expect(CONTRACT_TYPES["campsverso.avatar.spoke.v1"].visibility).toBe("world");
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
