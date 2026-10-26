/** HUD das duas visões: relógio, clima, avatar, necessidades, inventário (escopo §6) e os outros
 * avatares à vista, com a ordem e o que estão fazendo (os ajudantes, ADR-0072). */
import type { ObserverState } from "@campsverso/contracts";

import { el } from "../dom.ts";
import { clockText } from "../simclock.ts";
import type { Status } from "../store.ts";

const STATUS: Record<Status, string> = { connecting: "conectando…", open: "ao vivo", closed: "sem conexão" };

const MONTHS = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const SEASONS: Readonly<Record<string, string>> = { verao: "verão" };
const WEATHER: Readonly<Record<string, string>> = { sun: "sol", rain: "chuva", storm: "tempestade", drought: "seca" };

/** O tempo de hoje e, quando a previsão já saiu, o de amanhã (ADR-0069). */
export function weatherText(state: ObserverState): string {
  const name = (condition: string | undefined): string => (condition === undefined ? "?" : (WEATHER[condition] ?? condition));
  const today = name(state.weather[String(state.day)]);
  const tomorrow = state.weather[String(state.day + 1)];
  return tomorrow === undefined ? `clima: ${today}` : `clima: ${today} · amanhã: ${name(tomorrow)}`;
}

/** A data e a estação do ano acelerado (ADR-0067), "15 de nov · primavera"; vazio sem ano. */
export function yearText(state: ObserverState): string {
  if (state.date === undefined) {
    return "";
  }
  const [, month, day] = state.date.split("-").map(Number);
  const season = state.season === undefined ? "" : ` · ${SEASONS[state.season] ?? state.season}`;
  return ` · ${String(day)} de ${MONTHS[(month ?? 1) - 1] ?? ""}${season}`;
}

function clockBadge(state: ObserverState): string {
  const { mode, scale, paused } = state.clock;
  const pace = mode === "max" ? "máximo" : `${String(scale ?? "?")}×`;
  return paused === true ? `${pace} · pausado` : pace;
}

function needBar(name: string, value: number): HTMLElement {
  const bar = el("div", { className: "bar" }, el("span", { style: `width: ${String(Math.round(value))}%` }));
  return el("div", { className: "need" }, el("label", {}, name), bar, el("b", {}, value.toFixed(0)));
}

/** "fazendo: plant" e, quando o controlador declarou, a intenção: o que o LLM pretende (ADR-0059). */
export function doingText(action: string, intent?: string): string {
  return intent === undefined ? `fazendo: ${action}` : `fazendo: ${action} · ${intent}`;
}

/** O ícone de um item do inventário (um endereço de imagem), ou nada: o item fica só com o texto. */
export type IconOf = (item: string) => string | undefined;

function itemChip(item: string, qty: number, icon?: IconOf): HTMLElement {
  const url = icon?.(item);
  const chip = el("span", { className: "item" }, `${item} ×${String(qty)}`);
  if (url !== undefined) {
    const image = el("img", { className: "item-icon" });
    image.src = url;
    image.alt = "";
    chip.prepend(image);
  }
  return chip;
}

/** Os outros avatares na tela: o nome, a ordem que receberam (quando têm) e o que fazem agora. */
export function othersText(state: ObserverState, avatarId: string): string[] {
  return Object.entries(state.entities)
    .filter(([id, e]) => id !== avatarId && e?.kind === "avatar" && e.position !== undefined)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([id, e]) => {
      const order = e?.attributes["ordem"];
      const action = state.actions[id];
      const doing = action === undefined ? "parado" : doingText(action.action, action.intent);
      return `${e?.display_name ?? id}${typeof order === "string" ? ` · ${order}` : ""} · ${doing}`;
    });
}

export function renderHud(
  root: HTMLElement,
  state: ObserverState,
  tick: number,
  avatarId: string,
  status: Status,
  portrait?: HTMLElement,
  icon?: IconOf,
): void {
  const avatar = state.entities[avatarId];
  const controller = state.controllers[avatarId];
  const action = state.actions[avatarId];
  const needs = Object.entries(state.needs[avatarId] ?? {})
    .filter((entry): entry is [string, number] => entry[1] !== undefined)
    .sort(([a], [b]) => a.localeCompare(b));
  const items = Object.entries(state.containers[avatarId] ?? {}).sort(([a], [b]) => a.localeCompare(b));
  const held = Object.entries(state.entities)
    .filter(([, e]) => e?.container_id === avatarId)
    .map(([id, e]) => {
      const attributes = Object.entries(e?.attributes ?? {}).map(([k, v]) => `${k} ${String(v)}`);
      return `${id}${attributes.length > 0 ? ` (${attributes.join(", ")})` : ""}`;
    });
  // Cada coisa tem o seu lugar fixo na grade (style.css): o texto muda, a posição não.
  root.replaceChildren(
    portrait ?? el("div", { className: "portrait" }),
    el(
      "div",
      { className: "hud-clock" },
      el("strong", { className: "hud-time" }, `Dia ${String(state.day)} · ${clockText(state, tick)}${yearText(state)}`),
      el("span", { className: "hud-phase" }, state.phase),
      el("span", { className: "hud-weather" }, weatherText(state)),
      el("span", { className: "badge hud-pace" }, clockBadge(state)),
      status === "open" && state.pulse?.alive === false
        ? el("span", { className: "status closed" }, "kernel sem sinal")
        : el("span", { className: `status ${status}` }, STATUS[status]),
    ),
    el(
      "div",
      { className: "hud-avatar" },
      el("strong", { className: "hud-name" }, avatar?.display_name ?? avatarId),
      el(
        "span",
        { className: "hud-controller" },
        controller === undefined ? "sem controlador" : `${controller.type} · ${controller.id}`,
      ),
      el(
        "span",
        { className: "hud-doing" },
        state.asleep[avatarId] === true ? "dormindo" : action === undefined ? "parado" : doingText(action.action, action.intent),
      ),
    ),
    el("div", { className: "hud-needs" }, ...needs.map(([name, value]) => needBar(name, value))),
    el(
      "div",
      { className: "hud-items" },
      el("label", {}, "inventário"),
      ...items.map(([item, qty]) => itemChip(item, qty ?? 0, icon)),
      ...held.map((text) => el("span", { className: "item held" }, text)),
    ),
    el(
      "div",
      { className: "hud-others" },
      ...othersText(state, avatarId).map((text) => el("span", { className: "other" }, text)),
    ),
  );
}
