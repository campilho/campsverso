/** O andar sem pulo (ADR-0078, decisão 14): a tela quadro a quadro, um teste por mecanismo.
 *
 * Cada cena roda a tela a 60 quadros por segundo sobre um mundo de mentira, com o relógio ideal da
 * tela (o tick cresce no ritmo da escala). Um pulo é um deslocamento grande entre dois quadros.
 */
import type { ObserverMotion } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import type { ObserverState } from "@campsverso/contracts";

import { FOLLOW_TILES_PER_FRAME, MotionClock, pathFrom, positionAt, type Point } from "./motion.ts";
import { DisplayClock } from "./simclock.ts";

const FRAME_MS = 1000 / 60;

/** O que o estado mostra num instante: o tick da tela, o trajeto em curso e a posição do kernel. */
interface Moment {
  readonly tick: number;
  readonly motion?: ObserverMotion;
  readonly rest?: Point;
}

/** A tela quadro a quadro, de 0 a `untilMs`; `world` diz o estado em cada instante. */
function film(clock: MotionClock, untilMs: number, world: (ms: number) => Moment, id = "camps"): Point[] {
  const drawn: Point[] = [];
  for (let ms = 0; ms <= untilMs; ms += FRAME_MS) {
    const { tick, motion, rest } = world(ms);
    const at = clock.at(id, motion, rest, tick, ms);
    if (at !== undefined) {
      drawn.push(at);
    }
  }
  return drawn;
}

/** O maior deslocamento entre dois quadros seguidos, em tiles. */
function biggestStep(points: readonly Point[]): number {
  let biggest = 0;
  for (let i = 1; i < points.length; i++) {
    const a = points[i - 1];
    const b = points[i];
    if (a !== undefined && b !== undefined) {
      biggest = Math.max(biggest, Math.hypot(b.x - a.x, b.y - a.y));
    }
  }
  return biggest;
}

function line(fromX: number, toX: number, y = 0): ObserverMotion["path"] {
  return pathFrom({ x: fromX, y }, [{ x: toX, y }]);
}

function at(path: ObserverMotion["path"], index: number): Point {
  const point = path[index];
  if (point === undefined) {
    throw new Error(`o trajeto não tem o ponto ${String(index)}`);
  }
  return point;
}

/** Ticks por milissegundo real na fazenda (tick de 60 s) à escala dada. */
function rate(scale: number): number {
  return scale / 60 / 1000;
}

/** O script andando sem parar: vai e volta entre x=0 e x=30, cada trajeto num tick, com uma ação de
 * um tick entre um e outro (a colheita). No fim, um trajeto é interrompido no meio por outra ação: o
 * kernel o para onde ele está, e o trajeto some do estado. */
function busyScript(scale: number, trips: number): { world: (ms: number) => Moment; endMs: number; stop: Point } {
  const perMs = rate(scale);
  const legs: { motion: ObserverMotion; start: number }[] = [];
  for (let trip = 0; trip < trips; trip++) {
    const from = trip % 2 === 0 ? 0 : 30;
    const to = 30 - from;
    legs.push({ motion: { path: line(from, to), depart_tick: 10 + trip * 2, tiles_per_tick: 30, action_id: `andar-${String(trip)}` }, start: 10 + trip * 2 });
  }
  const last = trips % 2 === 0 ? 0 : 30;
  const cut: ObserverMotion = { path: line(last, last === 0 ? 30 : 0), depart_tick: 10 + trips * 2, tiles_per_tick: 30, action_id: "andar-cortado" };
  const cutTick = 10 + trips * 2;
  const stop = at(cut.path, 15);
  const world = (ms: number): Moment => {
    const tick = 10 + ms * perMs;
    if (tick >= cutTick + 0.5) {
      return { tick, rest: stop }; // interrompido no meio: o kernel o deixa onde estava
    }
    if (tick >= cutTick) {
      return { tick, motion: cut, rest: at(cut.path, cut.path.length - 1) };
    }
    const leg = legs.find((l) => tick >= l.start && tick < l.start + 1);
    if (leg !== undefined) {
      return { tick, motion: leg.motion, rest: at(leg.motion.path, leg.motion.path.length - 1) };
    }
    const done = [...legs].reverse().find((l) => tick >= l.start + 1);
    return { tick, rest: done === undefined ? { x: 0, y: 0 } : at(done.motion.path, done.motion.path.length - 1) };
  };
  const endMs = (cutTick + 0.5 - 10) / perMs + 3000; // e três segundos para a tela assentar
  return { world, endMs, stop };
}

describe("1. o desenho atrasado não salta para o destino", () => {
  it("a 72×, o script andando e o trajeto cortado no meio: nenhum quadro anda mais de um tile", () => {
    const { world, endMs, stop } = busyScript(72, 6);
    const drawn = film(new MotionClock(), endMs, world);
    expect(biggestStep(drawn)).toBeLessThanOrEqual(1);
    expect(drawn.at(-1)).toEqual(stop);
  });

  it("a 720×, o desenho anda com o kernel (uns 6 tiles por quadro) e nunca fica longe dele", () => {
    const { world, endMs, stop } = busyScript(720, 12);
    const clock = new MotionClock();
    let behind = 0;
    const drawn: Point[] = [];
    for (let ms = 0; ms <= endMs; ms += FRAME_MS) {
      const { tick, motion, rest } = world(ms);
      const point = clock.at("camps", motion, rest, tick, ms);
      const truth = motion === undefined ? rest : positionAt(motion, tick);
      if (point !== undefined && truth !== undefined) {
        drawn.push(point);
        behind = Math.max(behind, Math.hypot(truth.x - point.x, truth.y - point.y));
      }
    }
    const kernelPerFrame = 30 * rate(720) * FRAME_MS;
    expect(biggestStep(drawn)).toBeLessThanOrEqual(kernelPerFrame + 1);
    // O primeiro quadro de cada trecho parte da origem: dois quadros do kernel de folga. O teto
    // antigo, de 12 tiles por segundo, deixava o desenho dezenas de tiles para trás.
    expect(behind).toBeLessThanOrEqual(2 * kernelPerFrame + 1);
    expect(drawn.at(-1)).toEqual(stop);
  });
});

describe("2. dois trajetos que saem no mesmo tick", () => {
  it("o segundo substitui o primeiro, sem passar do destino nem saltar de volta", () => {
    const clock = new MotionClock();
    const perMs = rate(72);
    const first: ObserverMotion = { path: line(0, 20), depart_tick: 10, tiles_per_tick: 30, action_id: "a1" };
    const second: ObserverMotion = { path: line(0, 5), depart_tick: 10, tiles_per_tick: 30, action_id: "a2" };
    clock.observe("camps", first, 0); // o primeiro chegou pelo evento; o estado já mostra o segundo
    const drawn = film(clock, 3000, (ms) => {
      const tick = 10 + ms * perMs;
      return tick < 10 + 5 / 30 ? { tick, motion: second, rest: { x: 5, y: 0 } } : { tick, rest: { x: 5, y: 0 } };
    });
    expect(biggestStep(drawn)).toBeLessThanOrEqual(1);
    expect(Math.max(...drawn.map((p) => p.x))).toBeLessThanOrEqual(5);
    expect(drawn.at(-1)).toEqual({ x: 5, y: 0 });
  });
});

describe("3. a emenda para trás", () => {
  it("o desenho à frente do kernel volta pelo caminho, tile a tile, e chega", () => {
    const clock = new MotionClock();
    const perMs = rate(60); // um tick por segundo
    const go: ObserverMotion = { path: line(0, 10), depart_tick: 10, tiles_per_tick: 1, action_id: "ida" };
    // A tela anda 0,6 tick à frente do kernel. No tick 13,4 o kernel, que arredonda para baixo,
    // manda o avatar de volta a partir do tile 3: a origem nova fica atrás de onde ele aparece.
    const back: ObserverMotion = { path: line(3, 0), depart_tick: 13, tiles_per_tick: 1, action_id: "volta" };
    const drawn = film(clock, 9000, (ms) => {
      const kernel = 10 + ms * perMs;
      const shown = kernel + 0.6;
      if (kernel < 13.4) {
        return { tick: shown, motion: go, rest: { x: 10, y: 0 } };
      }
      return kernel < 16 ? { tick: shown, motion: back, rest: { x: 0, y: 0 } } : { tick: shown, rest: { x: 0, y: 0 } };
    });
    expect(biggestStep(drawn)).toBeLessThanOrEqual(0.5);
    expect(Math.max(...drawn.map((p) => p.x))).toBeLessThan(5);
    expect(drawn.at(-1)).toEqual({ x: 0, y: 0 });
  });
});

describe("4. o trajeto seguinte começa noutro tile", () => {
  it("terminado o desenho, o próximo trajeto parte de onde o avatar aparece, sem teleporte", () => {
    const clock = new MotionClock();
    const perMs = rate(72);
    const first: ObserverMotion = { path: line(0, 10), depart_tick: 10, tiles_per_tick: 30, action_id: "b1" };
    const next: ObserverMotion = { path: line(12, 20), depart_tick: 13, tiles_per_tick: 30, action_id: "b2" };
    const drawn = film(clock, 6000, (ms) => {
      const tick = 10 + ms * perMs;
      if (tick < 11) {
        return { tick, motion: first, rest: { x: 10, y: 0 } };
      }
      if (tick < 13) {
        return { tick, rest: { x: 10, y: 0 } };
      }
      if (tick < 14) {
        return { tick, motion: next, rest: { x: 20, y: 0 } };
      }
      return { tick, rest: { x: 20, y: 0 } };
    });
    expect(biggestStep(drawn)).toBeLessThanOrEqual(1);
    expect(drawn.at(-1)).toEqual({ x: 20, y: 0 });
  });
});

describe("5 e 6. o tempo da tela", () => {
  it("um quadro com o relógio um pouco atrás (duas fontes de tempo) não para nem volta o desenho", () => {
    const clock = new MotionClock();
    const walk: ObserverMotion = { path: line(0, 30), depart_tick: 10, tiles_per_tick: 1, action_id: "c1" };
    clock.at("camps", walk, { x: 30, y: 0 }, 10, 1000);
    const a = clock.at("camps", walk, { x: 30, y: 0 }, 12, 3000);
    const b = clock.at("camps", walk, { x: 30, y: 0 }, 12.1, 2999); // o quadro seguinte, numa fonte atrasada
    expect(a).toBeDefined();
    expect(b).toBeDefined();
    expect((b?.x ?? 0) >= (a?.x ?? 0)).toBe(true);
  });

  it("a aba que volta depois de muito tempo alcança o kernel em alguns quadros, sem passar dele", () => {
    const clock = new MotionClock();
    const walk: ObserverMotion = { path: line(0, 30), depart_tick: 10, tiles_per_tick: 1, action_id: "c2" };
    clock.at("camps", walk, { x: 30, y: 0 }, 10, 0);
    const drawn: Point[] = [];
    for (let ms = 60_000; ms <= 61_000; ms += FRAME_MS) {
      const tick = 25 + (ms - 60_000) / 1000; // um tick por segundo
      const point = clock.at("camps", walk, { x: 30, y: 0 }, tick, ms);
      expect(point?.x).toBeLessThanOrEqual(positionAt(walk, tick).x + 1e-9);
      if (point !== undefined) {
        drawn.push(point);
      }
    }
    expect(biggestStep(drawn)).toBeLessThanOrEqual(FOLLOW_TILES_PER_FRAME);
    expect(drawn.at(-1)?.x).toBeCloseTo(16, 0);
  });
});

describe("7. cada tela com o seu relógio de movimento", () => {
  it("dois relógios com o mesmo avatar não se emendam", () => {
    const a = new MotionClock();
    const b = new MotionClock();
    const left: ObserverMotion = { path: line(0, 4), depart_tick: 10, tiles_per_tick: 1, action_id: "d1" };
    const right: ObserverMotion = { path: line(20, 24), depart_tick: 10, tiles_per_tick: 1, action_id: "d1" };
    a.at("camps", left, { x: 4, y: 0 }, 10, 0);
    b.at("camps", right, { x: 24, y: 0 }, 10, 0);
    expect(a.at("camps", left, { x: 4, y: 0 }, 12, 2000)?.x).toBeLessThanOrEqual(4);
    expect(b.at("camps", right, { x: 24, y: 0 }, 12, 2000)?.x).toBeGreaterThanOrEqual(20);
  });
});

describe("a 1× o andar tem a velocidade do kernel", () => {
  it("30 tiles num tick de um minuto levam o minuto inteiro, sem correr e parar", () => {
    const clock = new MotionClock();
    const perMs = rate(1);
    const walk: ObserverMotion = { path: line(0, 30), depart_tick: 10, tiles_per_tick: 30, action_id: "e1" };
    const drawn = film(clock, 60_000, (ms) => ({ tick: 10 + ms * perMs, motion: walk, rest: { x: 30, y: 0 } }));
    const half = drawn[Math.floor(drawn.length / 2)];
    expect(half?.x).toBeGreaterThan(13);
    expect(half?.x).toBeLessThan(17);
    expect(biggestStep(drawn)).toBeLessThanOrEqual(0.05);
  });
});

describe("o relógio da tela a 1× não corre na frente do kernel", () => {
  it("a pulsação traz o tick que o kernel vai rodar; a tela mostra o que acabou de rodar, andando", () => {
    const state = {
      tick: 100,
      sim_time: "2026-11-16T09:40:00-03:00",
      session: { cartridge_version: "0.1.0", tick_seconds: 60, map: { id: "x", width: 3, height: 2 } },
      clock: { mode: "continuous", scale: 1, paused: false },
      pulse: { tick: 101, alive: true },
    } as unknown as ObserverState;
    const clock = new DisplayClock();
    clock.reset(state, 0);
    clock.observe(state, 0);
    expect(clock.at(state, 0, true)).toBeLessThan(100.01);
    expect(clock.at(state, 30_000, true)).toBeCloseTo(100.5, 1);
    expect(clock.at(state, 59_000, true)).toBeLessThan(101);
  });
});

describe("o trajeto perdido que termina em diagonal (a queda da aba no escritório, M23)", () => {
  it("de (6,7) a (5,5) sem o trajeto do kernel, o desenho anda um L e para no destino", () => {
    expect(pathFrom({ x: 6, y: 7 }, [{ x: 5, y: 5 }])).toEqual([
      { x: 6, y: 7 },
      { x: 5, y: 7 },
      { x: 5, y: 6 },
      { x: 5, y: 5 },
    ]);
    // O gerente parado em (6,7); o trajeto até (5,5) começa e acaba entre duas atualizações, e o
    // estado só mostra o lugar novo. Antes, a emenda andava em diagonal sem fim e a aba caía.
    const clock = new MotionClock();
    const drawn = film(clock, 2000, (ms) => ({ tick: 10 + ms * rate(72), rest: ms < 500 ? { x: 6, y: 7 } : { x: 5, y: 5 } }), "gerente");
    expect(biggestStep(drawn)).toBeLessThanOrEqual(1);
    expect(drawn.at(-1)).toEqual({ x: 5, y: 5 });
  });
});

describe("a seta a 1× com o tick de 250 ms (ADR-0081)", () => {
  it("o destino novo começa atrás do desenho, no mesmo caminho: o desenho espera, sem voltar", () => {
    const clock = new MotionClock();
    const perMs = rate(60); // um tick por segundo, um tile por tick
    const go: ObserverMotion = { path: line(0, 10), depart_tick: 10, tiles_per_tick: 1, action_id: "ida" };
    // A tela anda 0,4 tick à frente do kernel; no tick 13 o kernel troca o destino (a seta
    // segurada) e parte do tile 3, onde está; o trajeto novo chega um quarto de tick depois.
    const further: ObserverMotion = { path: line(3, 12), depart_tick: 13, tiles_per_tick: 1, action_id: "adiante" };
    const drawn = film(clock, 9000, (ms) => {
      const kernel = 10 + ms * perMs;
      const shown = kernel + 0.4;
      return kernel < 13.25 ? { tick: shown, motion: go, rest: { x: 10, y: 0 } } : { tick: shown, motion: further, rest: { x: 12, y: 0 } };
    });
    expect(drawn.every((p, i) => i === 0 || p.x >= (drawn[i - 1]?.x ?? 0) - 1e-9)).toBe(true);
    expect(drawn.at(-1)?.x ?? 0).toBeGreaterThan(8);
  });

  it("solta a seta: o desenho não passa da parada enquanto o kernel não responde", () => {
    const clock = new MotionClock();
    const perMs = rate(60);
    const go: ObserverMotion = { path: line(0, 10), depart_tick: 10, tiles_per_tick: 1, action_id: "ida" };
    const stop: ObserverMotion = { path: line(5, 5), depart_tick: 15, tiles_per_tick: 1, action_id: "parada" };
    const drawn: Point[] = [];
    for (let ms = 0; ms <= 9000; ms += FRAME_MS) {
      const kernel = 10 + ms * perMs;
      if (ms >= 4000 && ms < 4000 + FRAME_MS) {
        clock.limit("camps", { x: 5, y: 0 }, 1500); // soltou no tile 4: a parada vai no 5
      }
      // A parada chega 1,5 tick depois (o tick e a rede): o trajeto velho ainda está no estado.
      const motion = kernel < 15.5 ? go : stop;
      const point = clock.at("camps", motion, kernel < 15.5 ? { x: 10, y: 0 } : { x: 5, y: 0 }, kernel + 0.4, ms);
      if (point !== undefined) {
        drawn.push(point);
      }
    }
    expect(Math.max(...drawn.map((p) => p.x))).toBeLessThanOrEqual(5);
    expect(drawn.every((p, i) => i === 0 || p.x >= (drawn[i - 1]?.x ?? 0) - 1e-9)).toBe(true);
    expect(drawn.at(-1)).toEqual({ x: 5, y: 0 });
  });
});

describe("o relógio da tela a 72× com o tick de 250 ms (ADR-0081)", () => {
  it("anda liso entre os pulsos de um segundo, sem correr, parar e saltar", () => {
    // 288 ticks por segundo real; o pulso do kernel chega a cada segundo, sem outros eventos.
    const base = {
      sim_time: "2026-11-16T10:00:00-03:00",
      session: { cartridge_version: "0.4.0", tick_ms: 250, map: { id: "office", width: 20, height: 17 } },
      clock: { mode: "continuous", scale: 72, paused: false },
    };
    const at = (tick: number): ObserverState => ({ ...base, tick, pulse: { tick: tick + 1, alive: true } }) as unknown as ObserverState;
    const clock = new DisplayClock();
    clock.reset(at(10_000), 0);
    let previous = clock.at(at(10_000), 0, true);
    let biggest = 0;
    let smallest = Number.POSITIVE_INFINITY;
    for (let ms = 16; ms <= 10_000; ms += 16) {
      const state = at(10_000 + Math.floor(ms / 1000) * 288); // o pulso de cada segundo
      clock.observe(state, ms);
      const shown = clock.at(state, ms, true);
      if (ms > 2000) {
        biggest = Math.max(biggest, shown - previous);
        smallest = Math.min(smallest, shown - previous);
      }
      previous = shown;
    }
    // Um quadro de 16 ms a 72× anda uns 4,6 ticks; antes, a tela parava (0) e saltava (dezenas).
    expect(smallest).toBeGreaterThan(2);
    expect(biggest).toBeLessThan(10);
  });
});
