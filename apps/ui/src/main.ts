/** A UI do Campsverso (M4 a M6; ADR-0050, ADR-0051, ADR-0053): o mundo pelo gateway.
 *
 * `?view=player` (padrão) mostra o mapa e o HUD; `?view=operator` acrescenta o painel do operador.
 * Nas duas visões dá para assumir o Camps e jogar: o clique esquerdo anda, o direito abre o menu.
 * O mapa é desenhado pelo Phaser com a arte dos cartuchos; `?render=debug` volta ao canvas de
 * depuração, com ids e rótulos.
 */
import "./style.css";

import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

import { loadArt, type LoadedArt } from "./art/load.ts";
import { Connection, type View } from "./connection.ts";
import { button, el } from "./dom.ts";
import { motionClock } from "./motion.ts";
import { CreditsDialog } from "./panels/credits.ts";
import { renderHud } from "./panels/hud.ts";
import { ActionMenu } from "./panels/menu.ts";
import { OperatorPanel } from "./panels/operator.ts";
import { Portrait } from "./panels/portrait.ts";
import { inControl, menuFor, proposal, thingAt, walkTo } from "./play.ts";
import { busyText, progressOf } from "./progress.ts";
import { MapCanvas } from "./render/canvas.ts";
import { PhaserRenderer } from "./render/phaser.ts";
import type { WorldRenderer } from "./render/renderer.ts";
import { DisplayClock, clockText, isLive } from "./simclock.ts";
import { Store } from "./store.ts";
import { parseTiledMap } from "./tiled.ts";

const NOTICE_MS = 6000;
const PANEL_EVERY_MS = 150;
const PROPOSE = "campsverso.cmd.action.propose.v1";
const POSSESS = "campsverso.cmd.avatar.possess.v1";
const RELEASE = "campsverso.cmd.avatar.release.v1";
const SET_MODE = "campsverso.cmd.clock.set_mode.v1";

const query = new URLSearchParams(location.search);
const view: View = query.get("view") === "operator" ? "operator" : "player";
const debug = query.get("render") === "debug";
const store = new Store();
const scheme = location.protocol === "https:" ? "wss" : "ws";
const connection = new Connection(`${scheme}://${location.host}/ws?view=${view}`, store);

const map: WorldRenderer = debug ? new MapCanvas(el("canvas")) : new PhaserRenderer();
const hud = el("div", { className: "hud" });
const control = el("div", { className: "control" });
const notice = el("div", { className: "notice" });
const aside = el("aside", { className: "operator" });
const other = view === "operator" ? "player" : "operator";
const header = el(
  "header",
  {},
  el("h1", {}, "Campsverso"),
  el("span", { className: "view" }, view === "operator" ? "visão do operador" : "visão do jogador"),
);
const switchLink = el("a", {}, `abrir a visão ${other === "operator" ? "do operador" : "do jogador"}`);
switchLink.href = `?view=${other}${debug ? "&render=debug" : ""}`;
const renderLink = el("a", {}, debug ? "visual de jogo" : "canvas de depuração");
renderLink.href = `?view=${view}${debug ? "" : "&render=debug"}`;
const creditsLink = el("a", {}, "créditos");
creditsLink.href = "#creditos";
header.append(el("nav", {}, creditsLink, renderLink, switchLink));
const app = document.querySelector<HTMLElement>("#app");
if (app === null) {
  throw new Error("#app não existe no index.html");
}
app.className = view;
app.replaceChildren(
  header,
  el("main", {}, el("section", { className: "world" }, control, map.element, notice, hud), view === "operator" && aside),
);

const menu = new ActionMenu(document.body);
const portrait = new Portrait();
const credits = new CreditsDialog(document.body);
let art: LoadedArt | undefined;
creditsLink.addEventListener("click", (event) => {
  event.preventDefault();
  void credits.open(art?.credits ?? []);
});
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
let lastControl = "";
let shownTick = 0;
let noticeUntil = 0;
let lastReply = "";

function avatarId(): string {
  return store.welcome?.avatar_id ?? "camps";
}

function say(text: string): void {
  notice.textContent = text;
  notice.hidden = false;
  noticeUntil = performance.now() + NOTICE_MS;
}

/** Recusas que interessam a quem joga: as ações do avatar e os comandos desta conexão. */
function explain(event: EnvelopeV1): string | undefined {
  const data = event.data as Record<string, unknown>;
  const detail = typeof data.detail === "string" ? `: ${data.detail}` : "";
  if (event.type === "campsverso.action.rejected.v1" && data.avatar_id === avatarId()) {
    const state = store.state;
    if (data.reason === "busy" && state !== undefined) {
      return busyText(state, avatarId(), shownTick); // ADR-0052: o trabalho não se cancela
    }
    return `O kernel recusou ${String(data.action)} (${String(data.reason)}${detail}).`;
  }
  if (event.type === "campsverso.world.command.rejected.v1") {
    const command = String(data.command_type).replace(/^campsverso\.cmd\./, "").replace(/\.v\d+$/, "");
    return `O kernel recusou ${command} (${String(data.reason)}${detail}).`;
  }
  return undefined;
}

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
      if (art !== undefined) {
        portrait.setArt(art.manifest, avatarId());
      }
    } else {
      clock.observe(state, performance.now());
    }
  }
  const id = state?.session?.map?.id;
  if (id !== undefined && id !== mapId) {
    mapId = id;
    void loadMap(id);
  }
  const reply = store.lastReply;
  if (reply?.ok === false && reply.error !== undefined && reply.request_id !== lastReply) {
    lastReply = reply.request_id;
    say(`O gateway recusou o pedido (${reply.error.code}): ${reply.error.message}`);
  }
});

store.onEvents((events) => {
  for (const event of events) {
    const text = explain(event);
    if (text !== undefined) {
      say(text);
    }
  }
});

// ---------------------------------------------------------------- jogar (ADR-0051)

function assume(state: ObserverState): void {
  if (view === "operator" && state.clock.mode === "max") {
    // O modo máximo é só de script e replay (princípio 7): o operador passa o mundo ao contínuo.
    connection.send(SET_MODE, { mode: "continuous", reason: "o humano vai jogar" });
  }
  connection.send(POSSESS, { avatar_id: avatarId() });
}

function renderControl(state: ObserverState): void {
  const mine = inControl(state, avatarId());
  const controller = state.controllers[avatarId()];
  const busy = state.actions[avatarId()] !== undefined || state.asleep[avatarId()] === true;
  const key = JSON.stringify([mine, controller, busy, store.status, state.clock.mode]);
  if (key === lastControl) {
    return; // refazer o botão sem mudança engoliria cliques
  }
  lastControl = key;
  const hint = !mine
    ? `O Camps está com ${controller === undefined ? "ninguém" : controller.id}. Assuma para jogar.`
    : busy
      ? "Você controla o Camps."
      : "Sua vez: clique esquerdo anda; clique direito abre o menu (no Camps, o menu de si).";
  control.replaceChildren(
    mine
      ? button("Devolver ao script", () => { connection.send(RELEASE, { avatar_id: avatarId() }); }, store.status === "open")
      : button("Assumir o Camps", () => { assume(state); }, store.status === "open"),
    el("span", { className: "hint" }, hint),
  );
}

/** Onde o avatar aparece na tela agora (o trajeto interpolado, arredondado ao tile). */
function avatarTile(state: ObserverState): { x: number; y: number } | undefined {
  const motion = state.motion[avatarId()];
  const at = motion === undefined ? state.entities[avatarId()]?.position : motionClock.at(avatarId(), motion, shownTick);
  return at === undefined ? undefined : { x: Math.round(at.x), y: Math.round(at.y) };
}

map.element.addEventListener("click", (event) => {
  menu.close();
  const state = store.state;
  const tile = map.tileAt(event.clientX, event.clientY);
  if (state === undefined || tile === undefined) {
    return;
  }
  if (!inControl(state, avatarId())) {
    say("Assuma o controle do Camps para jogar.");
    return;
  }
  connection.send(PROPOSE, { ...walkTo(state, avatarId(), tile.x, tile.y) });
});

map.element.addEventListener("contextmenu", (event) => {
  event.preventDefault();
  const state = store.state;
  const tile = map.tileAt(event.clientX, event.clientY);
  if (state === undefined || tile === undefined) {
    return;
  }
  if (!inControl(state, avatarId())) {
    say("Assuma o controle do Camps para jogar.");
    return;
  }
  const me = avatarTile(state);
  const clicked = me?.x === tile.x && me.y === tile.y ? "self" : thingAt(state, tile.x, tile.y);
  if (clicked === undefined) {
    connection.send(PROPOSE, { ...walkTo(state, avatarId(), tile.x, tile.y) }); // chão: só andar
    return;
  }
  const entity = clicked === "self" ? state.entities[avatarId()] : state.entities[clicked];
  const title = clicked === "self" ? `${entity?.display_name ?? avatarId()} (você)` : (entity?.display_name ?? clicked);
  menu.open(event.pageX, event.pageY, title, menuFor(state, avatarId(), clicked), (entry, chosen) => {
    connection.send(PROPOSE, { ...proposal(avatarId(), entry, chosen) });
  });
});

// ---------------------------------------------------------------- quadros

function frame(now: number): void {
  const state = store.state;
  if (state !== undefined) {
    const tick = clock.at(state, now, isLive(state, store.status === "open"));
    shownTick = tick;
    map.draw(state, tick);
    renderControl(state);
    const shownClock = clockText(state, tick);
    const panelDue = (dirty || now - lastPanel > 1000) && now - lastPanel >= PANEL_EVERY_MS;
    if (panelDue || shownClock !== lastClock) {
      // O HUD acompanha cada minuto mostrado; o painel do operador, só as mudanças de estado.
      portrait.setBadge(progressOf(state, avatarId(), tick)?.label ?? "");
      renderHud(hud, state, tick, avatarId(), store.status, portrait.element);
      lastClock = shownClock;
    }
    if (panelDue) {
      panel?.render(state, avatarId(), store.welcome?.commands ?? [], store.timeline, store.lastReply);
      dirty = false;
      lastPanel = now;
    }
  } else {
    hud.replaceChildren(el("p", {}, store.status === "closed" ? "sem conexão com o gateway…" : "conectando ao gateway…"));
  }
  if (!notice.hidden && now > noticeUntil) {
    notice.hidden = true;
  }
  requestAnimationFrame(frame);
}

notice.hidden = true;
connection.open();
void loadArt().then((loaded) => {
  art = loaded;
  map.setArt(loaded.manifest);
  portrait.setArt(loaded.manifest, avatarId());
});
requestAnimationFrame(frame);
