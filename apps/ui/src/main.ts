/** UI de depuração do Campsverso (M4; ADR-0050): o mundo pelo gateway, desenhado num canvas.
 *
 * `?view=player` (padrão) mostra o mapa e o HUD; `?view=operator` acrescenta o painel do operador.
 */
import "./style.css";

import type { EnvelopeV1 } from "@campsverso/contracts";

import { Connection, type View } from "./connection.ts";
import { el } from "./dom.ts";
import { renderHud } from "./panels/hud.ts";
import { OperatorPanel } from "./panels/operator.ts";
import { MapCanvas } from "./render/canvas.ts";
import { DisplayClock, clockText, isLive } from "./simclock.ts";
import { Store } from "./store.ts";
import { parseTiledMap } from "./tiled.ts";

const REJECTION_SHOWN_MS = 6000;
const PANEL_EVERY_MS = 150;

const view: View = new URLSearchParams(location.search).get("view") === "operator" ? "operator" : "player";
const store = new Store();
const scheme = location.protocol === "https:" ? "wss" : "ws";
const connection = new Connection(`${scheme}://${location.host}/ws?view=${view}`, store);

const canvas = el("canvas");
const hud = el("div", { className: "hud" });
const aside = el("aside", { className: "operator" });
const other = view === "operator" ? "player" : "operator";
const header = el(
  "header",
  {},
  el("h1", {}, "Campsverso"),
  el("span", { className: "view" }, view === "operator" ? "visão do operador" : "visão do jogador"),
);
const switchLink = el("a", {}, `abrir a visão ${other === "operator" ? "do operador" : "do jogador"}`);
switchLink.href = `?view=${other}`;
header.append(switchLink);
const app = document.querySelector<HTMLElement>("#app");
if (app === null) {
  throw new Error("#app não existe no index.html");
}
app.className = view;
app.replaceChildren(header, el("main", {}, el("section", { className: "world" }, canvas, hud), view === "operator" && aside));

const map = new MapCanvas(canvas);
const panel =
  view === "operator"
    ? new OperatorPanel(aside, (command, data) => { connection.send(command, data); }, () => { dirty = true; })
    : undefined;

const clock = new DisplayClock();
let welcomes = 0;
let mapId: string | undefined;
let dirty = true;
let lastPanel = 0;
let lastClock = "";
let rejection: { event: EnvelopeV1; seenAt: number } | undefined;

async function loadMap(id: string): Promise<void> {
  const response = await fetch(`/content/maps/${encodeURIComponent(id)}.tmj`);
  if (response.ok) {
    map.setGrid(parseTiledMap(await response.json()));
  }
}

store.onChange(() => {
  dirty = true;
  const state = store.state;
  if (state !== undefined) {
    if (store.welcomes !== welcomes) {
      welcomes = store.welcomes;
      clock.reset(state, performance.now());
    } else {
      clock.observe(state, performance.now());
    }
  }
  const id = state?.session?.map?.id;
  if (id !== undefined && id !== mapId) {
    mapId = id;
    void loadMap(id);
  }
  const last = store.timeline.at(-1);
  if (last?.type === "campsverso.action.rejected.v1" && last.id !== rejection?.event.id) {
    rejection = { event: last, seenAt: performance.now() };
  }
});

function frame(now: number): void {
  const state = store.state;
  const avatarId = store.welcome?.avatar_id ?? "camps";
  if (state !== undefined) {
    const tick = clock.at(state, now, isLive(state, store.status === "open"));
    map.draw(state, tick);
    const shownClock = clockText(state, tick);
    const panelDue = (dirty || now - lastPanel > 1000) && now - lastPanel >= PANEL_EVERY_MS;
    if (panelDue || shownClock !== lastClock) {
      // O HUD acompanha cada minuto mostrado; o painel do operador, só as mudanças de estado.
      const recent = rejection !== undefined && now - rejection.seenAt < REJECTION_SHOWN_MS ? rejection.event : undefined;
      renderHud(hud, state, tick, avatarId, store.status, recent);
      lastClock = shownClock;
    }
    if (panelDue) {
      panel?.render(state, avatarId, store.welcome?.commands ?? [], store.timeline, store.lastReply);
      dirty = false;
      lastPanel = now;
    }
  } else {
    hud.replaceChildren(el("p", {}, store.status === "closed" ? "sem conexão com o gateway…" : "conectando ao gateway…"));
  }
  requestAnimationFrame(frame);
}

connection.open();
requestAnimationFrame(frame);
