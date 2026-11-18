import type { ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import type { WorkshopArt } from "./art/manifest.ts";
import { RESULT_SECONDS, STEP_SECONDS, stepLook, workshopFrame, workshopState } from "./workshop.ts";

// O escritório: o tick de 250 ms (ADR-0081); 4 ticks por segundo do mundo.
const TICKS_PER_SECOND = 4;

function state(workshop: ObserverState["workshop"]): ObserverState {
  return {
    tick: 1000,
    sim_time: "2026-11-16T09:00:00-03:00",
    day: 1,
    phase: "manha",
    session: { cartridge_version: "0.4.0", tick_ms: 250 },
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
    ...(workshop === undefined ? {} : { workshop }),
  };
}

const DESK: WorkshopArt = {
  of: "owner",
  frames: {
    lendo: { frames: [4] },
    escrevendo: { frames: [1, 2, 3], fps: 3 },
    verde: { frames: [5] },
    vermelho: { frames: [6] },
  },
};
const ROBOT: WorkshopArt = {
  of: "self",
  frames: { trabalhando: { frames: [4, 5, 6, 7], fps: 4 }, passou: { frames: [8, 9] }, falhou: { frames: [12, 13] } },
};
const BENCH: WorkshopArt = { of: "any", frames: { trabalhando: { frames: [1] } } };
const DONO = { dono: "camps" };

describe("o monitor da mesa do dev", () => {
  it("mostra o último passo: lendo, escrevendo, os testes verdes ou vermelhos", () => {
    expect(stepLook("ler", true)).toBe("lendo");
    expect(stepLook("buscar", true)).toBe("lendo");
    expect(stepLook("editar", true)).toBe("escrevendo");
    expect(stepLook("rodar_testes", true)).toBe("verde");
    expect(stepLook("rodar_testes", false)).toBe("vermelho");
    expect(stepLook("pronto", true)).toBeUndefined();
  });

  it("só quando o dono está nela, e por até 2 horas do mundo", () => {
    const s = state({ steps: { camps: { ticket_id: "pedido-001", tool: "rodar_testes", ok: false, tick: 1000 } } });
    expect(workshopState(DESK, "mesa", DONO, s, 1000, ["camps"])).toBe("vermelho");
    expect(workshopFrame(DESK, "vermelho", 0)).toBe(6);
    expect(workshopState(DESK, "mesa", DONO, s, 1000, ["gerente"])).toBeUndefined(); // o dev saiu
    expect(workshopState(DESK, "mesa-3", {}, s, 1000, ["camps"])).toBeUndefined(); // a mesa vazia
    const late = 1000 + STEP_SECONDS * TICKS_PER_SECOND + 1;
    expect(workshopState(DESK, "mesa", DONO, s, late, ["camps"])).toBeUndefined();
  });

  it("sem a oficina, fica o de sempre", () => {
    expect(workshopState(DESK, "mesa", DONO, state(undefined), 1000, ["camps"])).toBeUndefined();
    expect(workshopFrame(DESK, undefined, 0)).toBeUndefined();
  });
});

describe("o robô e a bancada", () => {
  it("o robô trabalha entre o começo e o fim da chamada, e a bancada liga o osciloscópio", () => {
    const s = state({ robots: { "robo-testador": { state: "working", avatar_id: "camps", tick: 990 } } });
    expect(workshopState(ROBOT, "robo-testador", {}, s, 1000, [])).toBe("trabalhando");
    expect(workshopFrame(ROBOT, "trabalhando", 0.5)).toBe(6);
    expect(workshopState(ROBOT, "robo-revisor", {}, s, 1000, [])).toBeUndefined(); // o outro, parado
    expect(workshopState(BENCH, "bancada", {}, s, 1000, [])).toBe("trabalhando");
  });

  it("o resultado fica 15 minutos do mundo e o robô volta ao parado", () => {
    const s = state({ robots: { "robo-testador": { state: "failed", avatar_id: "camps", tick: 1000 } } });
    expect(workshopState(ROBOT, "robo-testador", {}, s, 1000, [])).toBe("falhou");
    expect(workshopFrame(ROBOT, "falhou", 0)).toBe(12);
    const later = 1000 + RESULT_SECONDS * TICKS_PER_SECOND + 1;
    expect(workshopState(ROBOT, "robo-testador", {}, s, later, [])).toBeUndefined();
    expect(workshopState(BENCH, "bancada", {}, s, 1000, [])).toBeUndefined();
  });
});
