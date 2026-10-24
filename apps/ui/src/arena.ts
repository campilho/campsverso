/** A visão arena (ADR-0068): as corridas de uma rodada lado a lado, pequenas, no canvas 2D, com a
 * velocidade da reprodução para todas; um clique abre a corrida na visão do operador. Só funciona
 * com o gateway no modo de assistir (`make assistir PASTA=...`). */
import "./style.css";

import { Connection } from "./connection.ts";
import { button, el } from "./dom.ts";
import { MapCanvas } from "./render/canvas.ts";
import { Store } from "./store.ts";
import { parseTiledMap } from "./tiled.ts";

const LIMIT = 6; // de 4 a 6 corridas por tela, por agora (decisão 6)
const SET_MODE = "campsverso.cmd.clock.set_mode.v1";
const PAUSE = "campsverso.cmd.clock.pause.v1";
const RESUME = "campsverso.cmd.clock.resume.v1";
const SPEEDS: readonly (readonly [string, Record<string, unknown> | undefined])[] = [
  ["Pausar", undefined],
  ["1 dia por minuto", { mode: "continuous", scale: 1440 }],
  ["1 dia a cada 10 s", { mode: "continuous", scale: 8640 }],
  ["Máximo", { mode: "max" }],
];

interface RunInfo {
  readonly name: string;
  readonly day: number;
  readonly done: boolean;
  readonly controller?: string | null;
  readonly model?: string | null;
  readonly coins?: number | null;
  readonly cost_usd?: number | null;
}

interface Card {
  readonly info: RunInfo;
  readonly store: Store;
  readonly connection: Connection;
  readonly map: MapCanvas;
  readonly status: HTMLElement;
  mapId?: string;
}

const scheme = location.protocol === "https:" ? "wss" : "ws";
const grid = el("div", { className: "arena-grid" });
const notice = el("p", { className: "hint" }, "carregando as corridas…");
const cards: Card[] = [];

function title(info: RunInfo): string {
  const who = info.controller === "llm" ? (info.model ?? "llm") : (info.controller ?? "corrida");
  return `${info.name} · ${who}`;
}

function card(info: RunInfo): Card {
  const store = new Store();
  const connection = new Connection(
    `${scheme}://${location.host}/ws?view=operator&run=${encodeURIComponent(info.name)}`,
    store,
  );
  const map = new MapCanvas(el("canvas"));
  const status = el("p", { className: "arena-status" }, info.done ? "gravada" : "ao vivo");
  const open = (): void => {
    location.href = `/?view=operator&run=${encodeURIComponent(info.name)}`;
  };
  const box = el("article", { className: "arena-card", title: "abrir na visão do operador" }, el("h3", {}, title(info)), map.element, status);
  box.addEventListener("click", open);
  grid.append(box);
  connection.open();
  return { info, store, connection, map, status };
}

async function loadGrid(target: Card, id: string): Promise<void> {
  const response = await fetch(`/content/maps/${encodeURIComponent(id)}.tmj`);
  if (response.ok) {
    target.map.setGrid(parseTiledMap(await response.json()));
  }
}

/** As miniaturas se redesenham duas vezes por segundo: são para acompanhar, não para jogar. */
function paint(): void {
  for (const target of cards) {
    const state = target.store.state;
    if (state === undefined) {
      continue;
    }
    const id = state.session?.map?.id;
    if (id !== undefined && id !== target.mapId) {
      target.mapId = id;
      void loadGrid(target, id);
    }
    target.map.draw(state, state.tick);
    const coins = state.containers.camps?.moeda ?? 0;
    const live = target.info.done ? "gravada" : "ao vivo";
    target.status.textContent = `Dia ${String(state.day)} · ${state.phase} · ${String(coins)} moedas · ${live}`;
  }
}

function speed(data: Record<string, unknown> | undefined): void {
  for (const target of cards) {
    if (data === undefined) {
      target.connection.send(PAUSE, {});
    } else {
      target.connection.send(SET_MODE, data);
      target.connection.send(RESUME, {});
    }
  }
}

async function start(): Promise<void> {
  const response = await fetch("/arena/runs");
  const runs = response.ok ? ((await response.json()) as RunInfo[]) : [];
  if (runs.length === 0) {
    notice.textContent = "Nenhuma corrida aqui. Suba o gateway com make assistir PASTA=data/arena/<rodada>.";
    return;
  }
  notice.textContent =
    runs.length > LIMIT
      ? `Mostrando ${String(LIMIT)} de ${String(runs.length)} corridas. Clique numa para abrir.`
      : "Clique numa corrida para abrir na visão do operador.";
  for (const info of runs.slice(0, LIMIT)) {
    cards.push(card(info));
  }
  setInterval(paint, 500);
}

document.body.append(
  el(
    "div",
    { className: "arena" },
    el("header", {}, el("strong", {}, "Campsverso"), el("span", { className: "view" }, "arena: assistir as corridas")),
    el("div", { className: "arena-speeds" }, ...SPEEDS.map(([label, data]) => button(label, () => { speed(data); }))),
    notice,
    grid,
  ),
);
void start();
