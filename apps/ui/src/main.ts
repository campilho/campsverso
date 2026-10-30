/** A UI do Campsverso (M4 a M6; ADR-0050, ADR-0051, ADR-0053): o mundo pelo gateway.
 *
 * `?view=player` (padrão) mostra o mapa e o HUD; `?view=operator` acrescenta o painel do operador.
 * Nas duas visões dá para assumir o avatar do jogador e jogar: o clique esquerdo anda, o direito abre o menu, o
 * shift enfileira, e o teclado anda e abre o menu (ADR-0068).
 * O mapa é desenhado pelo Phaser com a arte dos cartuchos; `?render=debug` volta ao canvas de
 * depuração, com ids e rótulos.
 */
import "./style.css";

import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

import { ItemIcons } from "./art/icons.ts";
import { loadArt, type LoadedArt } from "./art/load.ts";
import { Connection, type View } from "./connection.ts";
import { button, el } from "./dom.ts";
import { fogKey } from "./fog.ts";
import { motionClock } from "./motion.ts";
import { CreditsDialog } from "./panels/credits.ts";
import { CommandsHelp } from "./panels/help.ts";
import { renderHud } from "./panels/hud.ts";
import { ActionMenu } from "./panels/menu.ts";
import { OperatorPanel } from "./panels/operator.ts";
import { Portrait } from "./panels/portrait.ts";
import { contentsOf, inControl, menuFor, proposal, thingAt, tileMenu, walkTo, type MenuEntry, type Proposal, type Tile } from "./play.ts";
import { busyText, progressOf } from "./progress.ts";
import { ActionQueue, type Step } from "./queue.ts";
import { MapCanvas } from "./render/canvas.ts";
import { PhaserRenderer } from "./render/phaser.ts";
import type { WorldRenderer } from "./render/renderer.ts";
import { DisplayClock, clockText, isLive } from "./simclock.ts";
import { describe, shortType } from "./timeline.ts";
import { Store } from "./store.ts";
import { parseTiledMap, tileAt as terrainAt, type TileGrid } from "./tiled.ts";

const NOTICE_MS = 6000;
const PANEL_EVERY_MS = 150;
const KEY_REPEAT_MS = 200;
const PROPOSE = "campsverso.cmd.action.propose.v1";
const POSSESS = "campsverso.cmd.avatar.possess.v1";
const RELEASE = "campsverso.cmd.avatar.release.v1";
const SET_MODE = "campsverso.cmd.clock.set_mode.v1";

const query = new URLSearchParams(location.search);
const view: View = query.get("view") === "operator" ? "operator" : "player";
const debug = query.get("render") === "debug";
const store = new Store();
const scheme = location.protocol === "https:" ? "wss" : "ws";
const run = query.get("run"); // uma corrida da arena, no modo de assistir (ADR-0068)
const runParam = run === null ? "" : `&run=${encodeURIComponent(run)}`;
const connection = new Connection(`${scheme}://${location.host}/ws?view=${view}${runParam}`, store);

const map: WorldRenderer = debug ? new MapCanvas(el("canvas")) : new PhaserRenderer();
map.follow?.(avatarId());
map.setFog?.(view === "player" ? "always" : "toggle");
const hud = el("div", { className: "hud" });
const control = el("div", { className: "control" });
const notice = el("div", { className: "notice" });
const queueBox = el("div", { className: "queue" });
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
const world = el("section", { className: "world" }, control, map.element, notice, queueBox, hud);
app.replaceChildren(header, el("main", {}, world, view === "operator" && aside));

const menu = new ActionMenu(document.body);
const help = new CommandsHelp(world); // sobre o mapa, sem cobrir o painel do operador
const queue = new ActionQueue();
const portrait = new Portrait();
const icons = new ItemIcons(() => {
  lastClock = ""; // a folha dos ícones chegou: o HUD se redesenha no próximo quadro
});
// Para os testes no navegador (Playwright): onde fica, na tela, o centro de um tile; o que o
// jogador enxerga nele; o ícone de um item.
Object.assign(window, {
  campsverso: {
    tileCenter: (x: number, y: number) => map.clientOf?.(x, y),
    sight: (x: number, y: number) => map.sight?.(x, y),
    itemIcon: (item: string) => icons.url(item),
  },
});
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
let grid: TileGrid | undefined;
let shownQueue = -1;
let wasInControl = false;
let lastKeyMove = 0;

function avatarId(): string {
  return store.welcome?.avatar_id ?? "camps";
}

/** O nome do avatar do jogador, como o mundo o mostra (ADR-0072: o Camps não é o único avatar). */
function avatarName(state: ObserverState | undefined = store.state): string {
  return state?.entities[avatarId()]?.display_name ?? avatarId();
}

function say(text: string, good = false): void {
  notice.textContent = text;
  notice.classList.toggle("good", good);
  notice.hidden = false;
  noticeUntil = performance.now() + NOTICE_MS;
}

/** Os contratos de quem joga (M21): contratou, dispensou ou o contrato terminou. */
const LABOR = new Set([
  "campsverso.economy.labor.hired.v1",
  "campsverso.economy.labor.dismissed.v1",
  "campsverso.economy.labor.ended.v1",
]);

/** O retrato de um avatar pelo id (a escolha do quadro de ajudantes, M21); nada sem arte dele. */
function portraitOf(id: string): HTMLElement | undefined {
  if (art?.manifest.avatars?.[id] === undefined) {
    return undefined;
  }
  const picture = new Portrait();
  picture.setArt(art.manifest, id);
  return picture.element;
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
    grid = parseTiledMap(await response.json());
    map.setGrid(grid);
  }
}

store.onChange(() => {
  dirty = true;
  const state = store.state;
  if (state !== undefined) {
    if (store.welcomes !== welcomes) {
      welcomes = store.welcomes;
      clock.reset(state, performance.now());
      if (view === "player" && run === null && store.welcome !== undefined) {
        map.rememberFog?.(fogKey(store.welcome.worldid, avatarId())); // a névoa sobrevive à tela
      }
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
    queue.clear();
    say(`O gateway recusou o pedido (${reply.error.code}): ${reply.error.message}`);
  }
});

store.onEvents((events) => {
  for (const event of events) {
    const data = event.data as Record<string, unknown> | undefined;
    if (LABOR.has(event.type) && data?.employer === avatarId()) {
      say(describe(event, store.state?.session?.labels ?? []) ?? shortType(event.type), true);
      continue;
    }
    const text = explain(event);
    const cleared = queue.settle(event, avatarId());
    if (text !== undefined || cleared !== undefined) {
      say([text, cleared].filter((part) => part !== undefined).join(" "));
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
  if (run !== null) {
    if (lastControl === "") {
      // Assistir não muda o mundo: no lugar de assumir o avatar, o que é esta tela e a volta à arena.
      lastControl = "assistindo";
      const back = el("a", {}, "voltar à arena");
      back.href = "/?view=arena";
      const hint = `Assistindo à corrida ${run}: só leitura; o relógio do painel controla a reprodução.`;
      control.replaceChildren(el("span", { className: "hint" }, hint), back);
    }
    return;
  }
  const mine = inControl(state, avatarId());
  const controller = state.controllers[avatarId()];
  const busy = state.actions[avatarId()] !== undefined || state.asleep[avatarId()] === true;
  const clockable = playerClock();
  const { paused, scale } = state.clock;
  const key = JSON.stringify([mine, controller, busy, store.status, state.clock.mode, clockable, paused, scale]);
  if (key === lastControl) {
    return; // refazer o botão sem mudança engoliria cliques
  }
  lastControl = key;
  const hint = !mine
    ? `${avatarName(state)} está com ${controller === undefined ? "ninguém" : controller.id}. Assuma para jogar.`
    : busy
      ? `Você controla ${avatarName(state)}.`
      : "Sua vez: clique esquerdo anda; clique direito abre o menu; shift enfileira.";
  control.replaceChildren(
    mine
      ? button("Devolver ao script", () => { connection.send(RELEASE, { avatar_id: avatarId() }); }, store.status === "open")
      : button(`Assumir ${avatarName(state)}`, () => { assume(state); }, store.status === "open"),
    el("span", { className: "hint" }, hint),
    ...(mine ? [button("Comandos", () => { help.show(); })] : []),
    ...(clockable ? clockButtons(state) : []),
  );
  if (mine && !wasInControl) {
    help.firstTime();
  }
  wasInControl = mine;
}

// ---------------------------------------------------------------- o relógio do jogador (ADR-0074)

const CLOCK = "campsverso.cmd.clock.";
const PACES = [72, 144, 720] as const;

/** No sandbox, quem joga também opera o relógio: o gateway diz se aceita (`--relogio-do-jogador`). */
function playerClock(): boolean {
  return view === "player" && (store.welcome?.commands ?? []).includes(`${CLOCK}pause.v1`);
}

function togglePause(state: ObserverState): void {
  if (state.clock.paused === true) {
    connection.send(`${CLOCK}resume.v1`, {});
  } else {
    connection.send(`${CLOCK}pause.v1`, { reason: "debug" });
  }
}

/** Pausar ou retomar (tecla P) e as velocidades: 72x para o dia, 144x para andar mais rápido, 720x
 * para a noite dormindo. */
function clockButtons(state: ObserverState): HTMLElement[] {
  const open = store.status === "open";
  const pause = button(state.clock.paused === true ? "Retomar (P)" : "Pausar (P)", () => { togglePause(state); }, open);
  const paces = PACES.map((value) =>
    button(`${String(value)}×`, () => { connection.send(`${CLOCK}set_scale.v1`, { scale: value, reason: "human" }); }, open, state.clock.scale === value),
  );
  return [el("span", { className: "clock-buttons" }, pause, ...paces)];
}

// ---------------------------------------------------------------- a fila (ADR-0068)

/** O passo da fila para uma escolha do menu: o rótulo que a fila mostra e o alvo de que o Camps
 * precisa estar ao lado (andar não tem). */
function stepFor(state: ObserverState, entry: MenuEntry, chosen: Record<string, string | number>): Step {
  const values = Object.values(chosen).filter((v): v is string => typeof v === "string").map((v) => v.replace(/_/g, " "));
  const target = entry.target;
  const where =
    typeof target === "string" ? (state.entities[target]?.display_name ?? target) : target === undefined ? "" : `(${String(target.x)}, ${String(target.y)})`;
  const label = [`${entry.label}${values.length > 0 ? ` (${values.join(", ")})` : ""}`, where].filter((part) => part !== "").join(" · ");
  const near = entry.action === "move" ? undefined : target;
  return { label, proposal: proposal(avatarId(), entry, chosen), ...(near === undefined ? {} : { near }) };
}

/** Com o shift, o passo entra no fim da fila; sem, substitui a fila. Andar sem o shift vai na hora,
 * como o clique esquerdo: troca o trajeto em andamento. */
function act(step: Step, queued: boolean): void {
  if (!queued) {
    queue.clear();
    if (step.proposal.action === "move") {
      connection.send(PROPOSE, { ...step.proposal });
      return;
    }
  }
  queue.push(step);
}

function walkStep(state: ObserverState, tile: Tile): Step {
  return { label: `Andar até (${String(tile.x)}, ${String(tile.y)})`, proposal: walkTo(state, avatarId(), tile.x, tile.y) };
}

function renderQueue(): void {
  if (queue.version === shownQueue) {
    return;
  }
  shownQueue = queue.version;
  queueBox.hidden = queue.list.length === 0;
  queueBox.replaceChildren(
    el("strong", {}, "Fila"),
    el("ol", {}, ...queue.list.map((step) => el("li", {}, step.label))),
    el("span", { className: "hint" }, "Esc esvazia"),
  );
}

/** Onde o avatar aparece na tela agora (o trajeto interpolado, arredondado ao tile). */
function avatarTile(state: ObserverState): { x: number; y: number } | undefined {
  const motion = state.motion[avatarId()];
  const at = motionClock.at(avatarId(), motion, state.entities[avatarId()]?.position, shownTick, performance.now());
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
    say(`Assuma o controle de ${avatarName(state)} para jogar.`);
    return;
  }
  act(walkStep(state, tile), event.shiftKey);
});

map.element.addEventListener("contextmenu", (event) => {
  event.preventDefault();
  const state = store.state;
  const tile = map.tileAt(event.clientX, event.clientY);
  if (state === undefined || tile === undefined) {
    return;
  }
  if (!inControl(state, avatarId())) {
    say(`Assuma o controle de ${avatarName(state)} para jogar.`);
    return;
  }
  openMenu(state, tile, event.pageX, event.pageY, event.shiftKey);
});

/** O menu do clique direito: o do avatar, o da coisa no tile, o do terreno vazio, ou só andar. */
function openMenu(state: ObserverState, tile: Tile, pageX: number, pageY: number, queued: boolean): void {
  if (map.sight?.(tile.x, tile.y) === "unseen") {
    act(walkStep(state, tile), queued); // sob a nuvem não há menu: o jogador não sabe o que tem lá
    return;
  }
  const me = avatarTile(state);
  const clicked = me?.x === tile.x && me.y === tile.y ? "self" : thingAt(state, tile.x, tile.y);
  const choose = (entry: MenuEntry, chosen: Record<string, string | number>): void => {
    act(stepFor(state, entry, chosen), queued);
  };
  const suffix = queued ? " · entra na fila" : "";
  if (clicked === undefined) {
    const entries = tileMenu(state, avatarId(), tile, grid === undefined ? "" : terrainAt(grid, tile.x, tile.y));
    if (entries.length === 0) {
      act(walkStep(state, tile), queued); // chão sem ação: só andar
      return;
    }
    menu.open(pageX, pageY, `(${String(tile.x)}, ${String(tile.y)})${suffix}`, entries, choose);
    return;
  }
  const entity = clicked === "self" ? state.entities[avatarId()] : state.entities[clicked];
  const title = clicked === "self" ? `${entity?.display_name ?? avatarId()} (você)` : (entity?.display_name ?? clicked);
  const contents = clicked === "self" ? undefined : contentsOf(state, clicked);
  menu.open(pageX, pageY, `${title}${suffix}`, menuFor(state, avatarId(), clicked), choose, {
    ...(contents === undefined ? {} : { contents }),
    icon: (item) => icons.url(item),
    portrait: (option) => portraitOf(option),
  });
}

// ---------------------------------------------------------------- o teclado (ADR-0068)

const STEPS: Readonly<Record<string, readonly [number, number]>> = {
  ArrowUp: [0, -1],
  ArrowDown: [0, 1],
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
  w: [0, -1],
  s: [0, 1],
  a: [-1, 0],
  d: [1, 0],
};

/** De onde sai um passo do teclado: o fim do trajeto em andamento, ou o tile em que ele está. */
function stepOrigin(state: ObserverState): Tile | undefined {
  const motion = state.motion[avatarId()];
  if (state.actions[avatarId()]?.action === "move" && motion !== undefined) {
    return motion.path[motion.path.length - 1];
  }
  return avatarTile(state);
}

document.addEventListener("keydown", (event) => {
  if (event.target instanceof Element && event.target.closest("input, select, textarea") !== null) {
    return;
  }
  if (event.metaKey || event.ctrlKey || event.altKey) {
    return;
  }
  const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
  if (key === " ") {
    event.preventDefault();
    map.recenter?.();
    return;
  }
  if (key === "?") {
    help.show();
    return;
  }
  if (key === "p" && store.state !== undefined && playerClock()) {
    togglePause(store.state);
    return;
  }
  if (key === "Escape") {
    if (queue.clear()) {
      say("A fila foi esvaziada.");
    }
    return;
  }
  const state = store.state;
  if (state === undefined || run !== null || !inControl(state, avatarId())) {
    return;
  }
  const delta = STEPS[key];
  if (delta !== undefined) {
    event.preventDefault();
    const now = performance.now();
    const from = stepOrigin(state);
    if (from === undefined || (event.repeat && now - lastKeyMove < KEY_REPEAT_MS)) {
      return;
    }
    lastKeyMove = now;
    const step: Proposal = { avatar_id: avatarId(), action: "move", params: { target: { x: from.x + delta[0], y: from.y + delta[1] } } };
    act({ label: "um passo", proposal: step }, false);
    return;
  }
  if (key === "e") {
    const me = avatarTile(state);
    const at = me === undefined ? undefined : map.clientOf?.(me.x, me.y);
    if (me !== undefined && at !== undefined) {
      openMenu(state, me, at.x + window.scrollX, at.y + window.scrollY, event.shiftKey);
    }
  }
});

// ---------------------------------------------------------------- quadros

function frame(now: number): void {
  const state = store.state;
  if (state !== undefined) {
    const tick = clock.at(state, now, isLive(state, store.status === "open"));
    shownTick = tick;
    map.draw(state, tick);
    renderControl(state);
    if (run === null && inControl(state, avatarId())) {
      const next = queue.next(state, avatarId());
      if (next !== undefined) {
        connection.send(PROPOSE, { ...next });
      }
    } else if (queue.list.length > 0) {
      queue.clear(); // sem o controle, a fila não vale
    }
    renderQueue();
    const shownClock = clockText(state, tick);
    const panelDue = (dirty || now - lastPanel > 1000) && now - lastPanel >= PANEL_EVERY_MS;
    if (panelDue || shownClock !== lastClock) {
      // O HUD acompanha cada minuto mostrado; o painel do operador, só as mudanças de estado.
      portrait.setBadge(progressOf(state, avatarId(), tick)?.label ?? "");
      renderHud(hud, state, tick, avatarId(), store.status, portrait.element, (item) => icons.url(item));
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
queueBox.hidden = true;
connection.open();
void loadArt().then((loaded) => {
  art = loaded;
  map.setArt(loaded.manifest);
  icons.setArt(loaded.manifest);
  portrait.setArt(loaded.manifest, avatarId());
});
requestAnimationFrame(frame);
