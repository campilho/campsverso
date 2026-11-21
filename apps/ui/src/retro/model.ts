/** O que a tela retrô do escritório mostra, em funções puras (docs/design/briefing-tela.md): a luz
 * da barra de cima, a hora e o dia e os chips das pessoas. A moldura só desenha o que estas funções
 * dizem; nada aqui decide coisa do mundo. */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

import type { Banner } from "../banner.ts";
import { summonLine, summonsOf, type SummonView } from "../panels/office.ts";
import { actionLabel } from "../progress.ts";
import { tickSeconds } from "../simclock.ts";
import type { Status } from "../store.ts";
import { RESULT_SECONDS } from "../workshop.ts";

/** A luz da barra de cima: verde, âmbar ou vermelha, sempre com o rótulo (nunca só a cor). */
export interface Light {
  readonly color: "verde" | "ambar" | "vermelha";
  readonly label: string;
}

export function lightOf(status: Status, alive: boolean, banner: Banner | undefined): Light {
  if (status !== "open" || !alive) {
    return { color: "vermelha", label: "sem conexão" };
  }
  if (banner?.kind === "troca" || banner?.kind === "espera") {
    return { color: "ambar", label: "atualizando" };
  }
  return { color: "verde", label: "online" };
}

/** O relógio da barra de baixo: a hora, o dia com a fase e o ritmo, só quando não for 1×. */
export interface ClockView {
  readonly hour: string;
  readonly day: string;
  readonly pace: string | undefined;
}

const PHASES: Readonly<Record<string, string>> = { manha: "manhã", tarde: "tarde", noite: "noite", almoco: "almoço" };

export function clockView(state: ObserverState, shown: string): ClockView {
  const phase = ` · ${PHASES[state.phase] ?? state.phase}`;
  const scale = state.clock.scale;
  return {
    hour: shown.slice(0, 5),
    day: `Dia ${String(state.day)}${phase}`,
    pace: scale === undefined || scale === 1 ? undefined : `${String(scale)}×`,
  };
}

/** Um chip da barra de baixo: um avatar do elenco ou um robô da bancada. */
export interface Chip {
  readonly id: string;
  readonly name: string;
  readonly tag: "LLM" | "script" | "robô" | "você";
  /** A ação ("work") ou o nome do ícone na folha `icones` ("fora", "vigiar", "dormir"). */
  readonly icon: string | undefined;
  /** Só a ação curta: o texto inteiro vai no `title`. */
  readonly line: string;
  readonly title: string;
  /** Fora da sala (sem posição): a borda tracejada. */
  readonly away: boolean;
  readonly robot: boolean;
}

const ROBOT_LINE: Readonly<Record<string, string>> = {
  working: "trabalhando",
  passed: "passou",
  failed: "falhou",
};
const ROBOT_WORKING_SECONDS = 2 * 3600;

/** O estado de um robô pela última chamada dele na oficina (a regra de `workshop.ts`): trabalhando,
 * passou ou falhou, enquanto vale; depois, parado. */
export function robotLine(state: ObserverState, id: string, tick: number): string {
  const robot = state.workshop?.robots?.[id];
  if (robot === undefined) {
    return "parado";
  }
  const age = Math.max(0, tick - robot.tick) * tickSeconds(state.session);
  const limit = robot.state === "working" ? ROBOT_WORKING_SECONDS : RESULT_SECONDS;
  return age > limit ? "parado" : (ROBOT_LINE[robot.state] ?? "parado");
}

/** A ação curta, em minúsculas: "Jogando videogame" vira "jogando videogame". */
export function shortAction(state: ObserverState, action: string): string {
  const label = actionLabel(state, action);
  return label.charAt(0).toLowerCase() + label.slice(1);
}

/** A linha curta da convocação: "fora", "a caminho · 20:10", "convocado até 22:00". */
export function summonShort(state: ObserverState, dev: SummonView): string {
  const line = summonLine(state, dev);
  const time = /(\d{2}:\d{2})$/.exec(line)?.[1];
  if (dev.summoned && !dev.present) {
    return time === undefined ? "a caminho" : `a caminho · ${time}`;
  }
  if (dev.summoned) {
    return time === undefined ? "convocado" : `convocado até ${time}`;
  }
  return dev.present ? "" : "fora";
}

const CAST_ORDER = ["dev", "vigia", "gerente"];

/** Os chips, nesta ordem: o elenco (o dev, o vigia, o gerente) e os robôs da bancada. A linha do
 * tempo traz a convocação do dev que a visão do jogador não vê (fora da sala). */
export function chipsOf(state: ObserverState, me: string, tick: number, timeline: readonly EnvelopeV1[] = []): Chip[] {
  const chips: Chip[] = [];
  const summons = new Map(summonsOf(state, timeline).map((dev) => [dev.id, dev]));
  const avatars = Object.entries(state.entities)
    .filter(([, e]) => e?.kind === "avatar")
    .map(([id, e]) => ({ id, entity: e }));
  // O dev fora da sala não vem na visão do jogador: a convocação dele, sim.
  for (const dev of summons.values()) {
    if (dev.id !== "" && !avatars.some((a) => a.id === dev.id)) {
      avatars.push({ id: dev.id, entity: undefined });
    }
  }
  if (!avatars.some((a) => a.id === me)) {
    avatars.push({ id: me, entity: undefined }); // o gerente fora do escritório
  }
  const role = (id: string): string => {
    const papel = state.entities[id]?.attributes.papel;
    return typeof papel === "string" ? papel : id === me ? "gerente" : "dev";
  };
  avatars.sort((x, y) => CAST_ORDER.indexOf(role(x.id)) - CAST_ORDER.indexOf(role(y.id)) || (x.id < y.id ? -1 : 1));
  for (const { id, entity } of avatars) {
    const away = entity?.position === undefined;
    const controller = state.controllers[id];
    const tag: Chip["tag"] = id === me && controller?.type === "human" ? "você" : controller?.type === "llm" ? "LLM" : "script";
    // O vigia parado no ponto da ronda (o `wait` do script) está vigiando, não esperando.
    const doing = role(id) === "vigia" && state.actions[id]?.action === "wait" ? undefined : state.actions[id];
    const asleep = state.asleep[id] === true;
    let icon: string | undefined;
    let line: string;
    let title: string;
    if (away) {
      const dev = summons.get(id);
      line = dev === undefined ? "fora" : summonShort(state, dev) || "fora";
      icon = "fora";
      title = line;
    } else if (asleep) {
      icon = "dormir";
      line = "dormindo";
      title = line;
    } else if (doing !== undefined) {
      icon = doing.action;
      line = shortAction(state, doing.action);
      title = doing.intent === undefined ? line : `${line} · ${doing.intent}`;
    } else if (role(id) === "vigia") {
      icon = "vigiar";
      line = "vigiando";
      title = line;
    } else {
      line = id === me && tag === "você" ? "no escritório" : "parado";
      title = line;
    }
    const name = entity?.display_name ?? summons.get(id)?.name ?? (id.charAt(0).toUpperCase() + id.slice(1));
    chips.push({ id, name, tag, icon, line, title, away, robot: false });
  }
  const robots = Object.entries(state.entities)
    .filter(([, e]) => e?.kind === "robot")
    .sort(([a], [b]) => (a < b ? -1 : 1));
  for (const [id, entity] of robots) {
    const line = robotLine(state, id, tick);
    chips.push({
      id,
      name: entity?.display_name ?? id,
      tag: "robô",
      icon: line === "trabalhando" ? "work" : undefined,
      line,
      title: line,
      away: false,
      robot: true,
    });
  }
  return chips;
}
