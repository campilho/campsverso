import type { EnvelopeV1, EventLabel } from "@campsverso/contracts";
import { describe as suite, expect, it } from "vitest";

import { describe } from "./timeline.ts";

const LABELS: EventLabel[] = [
  { event: "campsverso.action.completed.v1", where: { action: "deposit" }, text: "{avatar_id} guardou {params.qty} {params.item} no {params.target}" },
  { event: "campsverso.action.completed.v1", where: { action: "deposit" }, text: "{avatar_id} guardou {params.item} no {params.target}" },
  { event: "campsverso.action.completed.v1", text: "{avatar_id} terminou: {action}" },
  { event: "campsverso.world.item.created.v1", where: { reason: "harvest" }, text: "{container_id} colheu {qty} {item}" },
  { event: "campsverso.world.entity.spawned.v1", text: "um canteiro novo em {position}" },
];

function event(type: string, data: Record<string, unknown>): EnvelopeV1 {
  return { type, data } as unknown as EnvelopeV1;
}

suite("os rótulos da linha do tempo (ADR-0068)", () => {
  it("o mais específico que bate vale, com os campos do evento", () => {
    const deposit = event("campsverso.action.completed.v1", { avatar_id: "camps", action: "deposit", params: { target: "chest", item: "semente_batata", qty: 3 } });
    expect(describe(deposit, LABELS)).toBe("camps guardou 3 semente batata no chest");
    const harvest = event("campsverso.world.item.created.v1", { item: "milho", qty: 1, container_id: "camps", reason: "harvest" });
    expect(describe(harvest, LABELS)).toBe("camps colheu 1 milho");
    expect(describe(event("campsverso.world.entity.spawned.v1", { position: { x: 3, y: 4 } }), LABELS)).toBe("um canteiro novo em (3, 4)");
  });

  it("um campo que falta passa ao rótulo seguinte; sem nenhum, o tipo cru fica com a tela", () => {
    const tool = event("campsverso.action.completed.v1", { avatar_id: "camps", action: "deposit", params: { target: "chest", item: "plow-1" } });
    expect(describe(tool, LABELS)).toBe("camps guardou plow-1 no chest");
    const water = event("campsverso.action.completed.v1", { avatar_id: "camps", action: "water", params: { target: "plot-001" } });
    expect(describe(water, LABELS)).toBe("camps terminou: water");
    const sold = event("campsverso.world.item.created.v1", { item: "moeda", qty: 25, container_id: "camps", reason: "payment" });
    expect(describe(sold, LABELS)).toBeUndefined();
    expect(describe(water, [])).toBeUndefined();
  });
});
