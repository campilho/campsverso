/** O escritório na tela (ADR-0078): os balões de fala, o quadro dos pedidos e o relógio em tempo
 * real. */
import type { ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { deliveryUrl, diffLines, summaryOf, summaryRef } from "./panels/delivery.ts";
import { isOffice, pullRequestLine, ticketsOf } from "./panels/office.ts";
import { BALLOON_CHARS, Balloons, balloonMs, balloonText } from "./speech.ts";
import { clockText, realTime } from "./simclock.ts";

function state(overrides: Partial<ObserverState> = {}): ObserverState {
  return {
    tick: 16200,
    sim_time: "2026-11-16T09:00:00-03:00",
    day: 1,
    phase: "manha",
    session: { cartridge_version: "0.1.0", tick_seconds: 2, map: { id: "office_campsverso", width: 20, height: 17 } },
    clock: { mode: "continuous", scale: 1, paused: false },
    weather: {},
    entities: {},
    containers: {},
    motion: {},
    actions: {},
    needs: {},
    asleep: {},
    controllers: {},
    decisions: {},
    ...overrides,
  };
}

describe("o balão de fala", () => {
  it("mostra o texto curto inteiro e corta o longo numa palavra, com reticências", () => {
    expect(balloonText("  Bom   dia!  ")).toBe("Bom dia!");
    const long = "palavra ".repeat(30);
    const shown = balloonText(long);
    expect(shown.length).toBeLessThanOrEqual(BALLOON_CHARS);
    expect(shown.endsWith("palavra…")).toBe(true);
  });

  it("fica o tempo de ler e some", () => {
    const balloons = new Balloons();
    balloons.hear("gerente", "Bom dia, Camps!", 1000);
    expect(balloons.current("gerente", 1000)).toBe("Bom dia, Camps!");
    expect(balloons.current("gerente", 1000 + balloonMs("Bom dia, Camps!") - 1)).toBe("Bom dia, Camps!");
    expect(balloons.current("gerente", 1000 + balloonMs("Bom dia, Camps!"))).toBeUndefined();
    expect(balloons.current("camps", 1000)).toBeUndefined();
  });
});

describe("o quadro dos pedidos", () => {
  const office = state({
    entities: {
      quadro: { kind: "board", position: { x: 9, y: 2 }, attributes: {} },
      "pedido-002": {
        kind: "ticket",
        container_id: "quadro",
        attributes: { numero: 2, titulo: "Resumo", estado: "a_fazer", tamanho: "M", dono: null },
      },
      "pedido-001": {
        kind: "ticket",
        container_id: "quadro",
        attributes: { numero: 1, titulo: "Busca", estado: "entregue", tamanho: "P", dono: "camps", comentario: "Falta o teste.", patch: "office-x/pedido-001/abc-1.patch" },
      },
    },
  });

  it("é de um mundo com quadro, e lista os pedidos na ordem em que foram escritos", () => {
    expect(isOffice(office)).toBe(true);
    expect(isOffice(state())).toBe(false);
    const tickets = ticketsOf(office);
    expect(tickets.map((t) => t.number)).toEqual([1, 2]);
    expect(tickets[0]).toMatchObject({ title: "Busca", state: "entregue", owner: "camps", comment: "Falta o teste.", patch: "office-x/pedido-001/abc-1.patch" });
    expect(tickets[1]?.owner).toBeUndefined();
    expect(tickets[1]?.patch).toBeUndefined();
    expect(tickets[0]?.pr).toBeUndefined();
  });

  it("mostra o PR do pedido no GitHub, com o CI enquanto ele está aberto (ADR-0083)", () => {
    const url = "https://github.com/campilho/campsverso/pull/7";
    const withPr = state({
      entities: {
        "pedido-001": {
          kind: "ticket",
          attributes: { numero: 1, titulo: "Busca", estado: "entregue", pr: 7, pr_url: url, pr_estado: "aberto", pr_ci: "success" },
        },
      },
    });
    const pr = ticketsOf(withPr)[0]?.pr;
    expect(pr).toEqual({ number: 7, url, state: "aberto", ci: "success" });
    expect(pullRequestLine({ number: 7, url, state: "aberto", ci: "success" })).toBe("PR #7 · aberto · CI verde");
    expect(pullRequestLine({ number: 7, url, state: "aberto", ci: "pending" })).toBe("PR #7 · aberto · CI rodando");
    expect(pullRequestLine({ number: 7, url, state: "mesclado", ci: "success" })).toBe("PR #7 · mesclado");
  });
});

describe("o ver o patch (ADR-0080)", () => {
  it("lê cada linha do diff com o tipo dela", () => {
    const patch = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1,2 +1,2 @@\n def f():\n-    return 1\n+    return 2\n";
    expect(diffLines(patch).map((l) => l.kind)).toEqual(["file", "file", "file", "hunk", "context", "del", "add"]);
  });

  it("acha o resumo ao lado do patch e aceita só a forma esperada", () => {
    expect(summaryRef("office-x/pedido-001/abc-1.patch")).toBe("office-x/pedido-001/abc-1.json");
    expect(deliveryUrl("office-x/pedido-001/abc 1.patch")).toBe("/content/entregas/office-x/pedido-001/abc%201.patch");
    expect(summaryOf({ files: ["a.py", 3], added: 4, removed: 1, base: "abc" })).toEqual({ files: ["a.py"], added: 4, removed: 1, base: "abc" });
    expect(summaryOf(null)).toBeUndefined();
  });
});

describe("o relógio em tempo real", () => {
  it("mostra os segundos num tick menor que o minuto, e não na fazenda", () => {
    expect(realTime(state())).toBe(true);
    expect(clockText(state(), 16215)).toBe("09:00:30");
    const farm = state({ session: { cartridge_version: "0.1.0", tick_seconds: 60, map: { id: "farm_camps", width: 3, height: 2 } } });
    expect(realTime(farm)).toBe(false);
    expect(clockText(farm, 16201)).toBe("09:01");
  });
});
