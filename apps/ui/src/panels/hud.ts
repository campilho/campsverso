/** HUD das duas visões: relógio, clima, avatar, necessidades e inventário (escopo §6). */
import type { ObserverState } from "@campsverso/contracts";

import { el } from "../dom.ts";
import { clockText } from "../simclock.ts";
import type { Status } from "../store.ts";

const STATUS: Record<Status, string> = { connecting: "conectando…", open: "ao vivo", closed: "sem conexão" };

function clockBadge(state: ObserverState): string {
  const { mode, scale, paused } = state.clock;
  const pace = mode === "max" ? "máximo" : `${String(scale ?? "?")}×`;
  return paused === true ? `${pace} · pausado` : pace;
}

function needBar(name: string, value: number): HTMLElement {
  const bar = el("div", { className: "bar" }, el("span", { style: `width: ${String(Math.round(value))}%` }));
  return el("div", { className: "need" }, el("label", {}, name), bar, el("b", {}, value.toFixed(0)));
}

export function renderHud(
  root: HTMLElement,
  state: ObserverState,
  tick: number,
  avatarId: string,
  status: Status,
  portrait?: HTMLElement,
): void {
  const avatar = state.entities[avatarId];
  const controller = state.controllers[avatarId];
  const action = state.actions[avatarId];
  const weather = state.weather[String(state.day)] ?? "?";
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
      el("strong", { className: "hud-time" }, `Dia ${String(state.day)} · ${clockText(state, tick)}`),
      el("span", { className: "hud-phase" }, state.phase),
      el("span", { className: "hud-weather" }, `clima: ${weather}`),
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
        state.asleep[avatarId] === true ? "dormindo" : action === undefined ? "parado" : `fazendo: ${action.action}`,
      ),
    ),
    el("div", { className: "hud-needs" }, ...needs.map(([name, value]) => needBar(name, value))),
    el(
      "div",
      { className: "hud-items" },
      el("label", {}, "inventário"),
      ...items.map(([item, qty]) => el("span", { className: "item" }, `${item} ×${String(qty)}`)),
      ...held.map((text) => el("span", { className: "item held" }, text)),
    ),
  );
}
