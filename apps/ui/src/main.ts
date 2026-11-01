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
import { loadLocale } from "./locale.ts";
import { motionClock, pathFrom } from "./motion.ts";
import { CreditsDialog } from "./panels/credits.ts";
import { CommandsHelp } from "./panels/help.ts";
import { renderHud } from "./panels/hud.ts";
import { ActionMenu } from "./panels/menu.ts";
import { OperatorPanel } from "./panels/operator.ts";
import { Portrait } from "./panels/portrait.ts";
import { contentsOf, holdTarget, inControl, menuFor, proposal, refusalText, thingAt, tileMenu, walkTo, type MenuEntry, type Tile } from "./play.ts";
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
// `make jogar`: a tela do jogador assume o avatar sozinha ao abrir (achado do usuário no mapa d).
let autoAssume = view === "player" && run === null && query.get("assumir") === "1";
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
const footStack = el("div", { className: "map-foot-stack" }, queueBox, notice);
const foot = el("div", { className: "map-foot" }, footStack);
let footAt = "";

/** A fila e o aviso flutuam sobre o canto de baixo do mapa desenhado, que fica no meio da largura
 * quando a tela é mais larga que o mapa. */
function alignFoot(): void {
  const drawn = (map.element.querySelector("canvas") ?? map.element).getBoundingClientRect();
  const around = world.getBoundingClientRect();
  const at = `${String(Math.round(drawn.left - around.left + 12))}px,${String(Math.round(around.right - drawn.right + 12))}px`;
  if (at !== footAt) {
    footAt = at;
    const [left = "12px", right = "12px"] = at.split(",");
    footStack.style.left = left;
    footStack.style.right = right;
  }
}
const world = el("section", { className: "world" }, control, map.element, foot, hud);
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
    return refusalText(String(data.action), String(data.reason), typeof data.detail === "string" ? data.detail : undefined);
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
    if (event.type === MOVED && data !== undefined) {
      observeMove(data);
      continue;
    }
    if (holding() && event.type === "campsverso.action.rejected.v1" && data?.action === "move" && data.avatar_id === avatarId()) {
      continue; // segurando a seta, o kernel recusar um trecho (a cerca, o baú) só para a caminhada
    }
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

/** O trajeto que chega pelo evento: a tela o desenha mesmo que ele comece e termine entre duas
 * atualizações (a 144× e a 720×; achado do usuário no mapa d). */
const MOVED = "campsverso.world.entity.moved.v1";

function observeMove(data: Record<string, unknown>): void {
  const origin = data.origin as Tile | undefined;
  const waypoints = data.waypoints as Tile[] | undefined;
  if (typeof data.entity_id !== "string" || origin === undefined || waypoints === undefined) {
    return;
  }
  motionClock.observe(
    data.entity_id,
    { path: pathFrom(origin, waypoints), depart_tick: Number(data.depart_tick), tiles_per_tick: Number(data.tiles_per_tick) },
    performance.now(),
  );
}

// ---------------------------------------------------------------- jogar (ADR-0051)

function assume(state: ObserverState): void {
  if (view === "operator" && state.clock.mode === "max") {
    // O modo máximo é só de script e replay (princípio 7): o operador passa o mundo ao contínuo.
    connection.send(SET_MODE, { mode: "continuous", reason: "o humano vai jogar" });
  }
  connection.send(POSSESS, { avatar_id: avatarId() });
}

function renderControl(state: ObserverState): void {
  if (autoAssume && store.status === "open" && store.welcome !== undefined) {
    autoAssume = false; // uma vez por tela: devolver ao script continua valendo
    if (!inControl(state, avatarId())) {
      assume(state);
    }
  }
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
const PACES = [72, 144, 720, 1440] as const;

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
 * e 1440x para a noite dormindo (uma noite de 10 horas em 25 segundos; achado do usuário no mapa d). */
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
  hold = undefined;
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
  const me = avatarTile(state);
  const mine = me?.x === tile.x && me.y === tile.y;
  // O tile do próprio avatar nunca está sob a nuvem: logo depois de abrir a tela, a névoa ainda não
  // olhou em volta, e o E andava até onde ele já estava.
  if (!mine && map.sight?.(tile.x, tile.y) === "unseen") {
    act(walkStep(state, tile), queued); // sob a nuvem não há menu: o jogador não sabe o que tem lá
    return;
  }
  const clicked = mine ? "self" : thingAt(state, tile.x, tile.y);
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
  // Em cima de uma coisa (o canteiro), o clique cai no avatar: o menu junta as ações dela às dele
  // (achado do usuário no mapa d: não havia como regar o canteiro em que se está).
  const under = clicked === "self" ? thingAt(state, tile.x, tile.y) : undefined;
  const thing = under ?? (clicked === "self" ? undefined : clicked);
  const self = `${state.entities[avatarId()]?.display_name ?? avatarId()} (você)`;
  const title = [thing === undefined ? undefined : (state.entities[thing]?.display_name ?? thing), clicked === "self" ? self : undefined]
    .filter((part) => part !== undefined)
    .join(" · ");
  const entries = [...(thing === undefined ? [] : menuFor(state, avatarId(), thing)), ...(clicked === "self" ? menuFor(state, avatarId(), "self") : [])];
  const contents = thing === undefined ? undefined : contentsOf(state, thing);
  menu.open(pageX, pageY, `${title}${suffix}`, entries, choose, {
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

/** Segurar uma seta anda neste ritmo, em tiles por segundo real (achado do usuário no mapa d: um
 * passo por toque esperava um tick do mundo para começar). O kernel aceita cada trecho só no tick
 * seguinte, então o destino vai adiante do desenho o que o avatar anda num tick (`lead`), e o
 * desenho, nesse ritmo, segue sem parar. Soltar a seta para no tile logo à frente. */
const HOLD_TILES_PER_SECOND = 6;
/** De quanto em quanto tempo um trecho novo vai ao kernel, enquanto a seta está segurada. */
const HOLD_SEND_MS = 200;
/** Depois de soltar, por quanto tempo uma recusa de andar ainda é da caminhada do teclado. */
const HOLD_GRACE_MS = 1500;

interface Hold {
  readonly key: string;
  readonly delta: readonly [number, number];
  readonly from: Tile;
  readonly since: number;
  sent?: Tile;
  sentAt: number;
}

let hold: Hold | undefined;
let heldUntil = 0;
let paced = false;

function holding(): boolean {
  return hold !== undefined || performance.now() < heldUntil;
}

function sendMove(target: Tile): void {
  queue.clear();
  connection.send(PROPOSE, { avatar_id: avatarId(), action: "move", params: { target: { x: target.x, y: target.y } } });
}

/** Quantos tiles o avatar anda num tick do mundo, no ritmo do teclado: o quanto o destino vai
 * adiante do desenho. */
function lead(state: ObserverState): number {
  const scale = state.clock.scale ?? 72;
  const tick = (state.session?.tick_seconds ?? 60) / Math.max(1, scale);
  return Math.ceil(HOLD_TILES_PER_SECOND * tick) + 1;
}

function startHold(state: ObserverState, key: string, delta: readonly [number, number]): void {
  const from = avatarTile(state);
  if (from === undefined) {
    return;
  }
  hold = { key, delta, from, since: performance.now(), sentAt: 0 };
  motionClock.pace(avatarId(), HOLD_TILES_PER_SECOND);
  paced = true;
  steerHold(state, performance.now());
}

/** A cada quadro: estende o destino da seta segurada e o manda ao kernel, se mudou. */
function steerHold(state: ObserverState, now: number): void {
  if (hold === undefined || now - hold.sentAt < HOLD_SEND_MS) {
    return;
  }
  const walked = Math.floor(((now - hold.since) / 1000) * HOLD_TILES_PER_SECOND);
  const target = holdTarget(state, hold.from, hold.delta, 1 + walked + lead(state));
  if (target.x === hold.from.x && target.y === hold.from.y) {
    return; // a cerca logo à frente: nada a mandar
  }
  if (hold.sent?.x !== target.x || hold.sent.y !== target.y) {
    sendMove(target);
    hold.sent = target;
    hold.sentAt = now;
  }
}

/** Soltou a seta: para no tile logo à frente de onde o avatar aparece, se o destino mandado está
 * além dele. */
function releaseHold(): void {
  const state = store.state;
  const released = hold;
  hold = undefined;
  heldUntil = performance.now() + HOLD_GRACE_MS;
  if (state === undefined || released?.sent === undefined) {
    return;
  }
  const me = avatarTile(state);
  if (me === undefined) {
    return;
  }
  const [dx, dy] = released.delta;
  const along = (t: Tile): number => (t.x - released.from.x) * dx + (t.y - released.from.y) * dy;
  const stop = holdTarget(state, me, released.delta, 1);
  if (along(released.sent) > along(stop)) {
    sendMove(stop);
  }
}

document.addEventListener("keyup", (event) => {
  const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
  if (hold?.key === key) {
    releaseHold();
  }
});
window.addEventListener("blur", () => {
  if (hold !== undefined) {
    releaseHold();
  }
});

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
    if (!event.repeat && hold?.key !== key) {
      startHold(state, key, delta); // a repetição do sistema não conta: o quadro estende a caminhada
    }
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
    if (hold !== undefined) {
      steerHold(state, now);
    } else if (paced && !holding() && state.actions[avatarId()] === undefined) {
      motionClock.pace(avatarId(), undefined); // a caminhada do teclado acabou: o desenho volta ao teto
      paced = false;
    }
    if (run === null && inControl(state, avatarId())) {
      const next = queue.next(state, avatarId());
      if (next !== undefined) {
        connection.send(PROPOSE, { ...next });
      }
    } else if (queue.list.length > 0) {
      queue.clear(); // sem o controle, a fila não vale
    }
    renderQueue();
    if (!queueBox.hidden || !notice.hidden) {
      alignFoot();
    }
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
  void loadLocale(loaded.layers).then(() => {
    lastClock = ""; // os nomes chegaram: o HUD se redesenha no próximo quadro
  });
  map.setArt(loaded.manifest);
  icons.setArt(loaded.manifest);
  portrait.setArt(loaded.manifest, avatarId());
});
requestAnimationFrame(frame);
