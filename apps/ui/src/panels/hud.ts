/** HUD das duas visões: relógio, clima, avatar, necessidades e inventário (escopo §6). */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

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
  rejection: EnvelopeV1 | undefined,
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
  root.replaceChildren(
    el(
      "div",
      { className: "hud-clock" },
      el("strong", {}, `Dia ${String(state.day)} · ${clockText(state, tick)}`),
      el("span", {}, state.phase),
      el("span", {}, `clima: ${weather}`),
      el("span", { className: "badge" }, clockBadge(state)),
      el("span", { className: `status ${status}` }, STATUS[status]),
    ),
    el(
      "div",
      { className: "hud-avatar" },
      el("strong", {}, avatar?.display_name ?? avatarId),
      el("span", {}, controller === undefined ? "sem controlador" : `${controller.type} · ${controller.id}`),
      el(
        "span",
        {},
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
    ...(rejection === undefined ? [] : [toast(rejection)]),
  );
}

function toast(rejection: EnvelopeV1): HTMLElement {
  const data = rejection.data as Record<string, unknown>;
  return el("div", { className: "toast" }, `ação recusada: ${String(data.reason)} (${String(data.action)})`);
}
