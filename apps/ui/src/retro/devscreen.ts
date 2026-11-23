/** A tela do dev (ADR-0089): a sessão dele na oficina, ao vivo, por cima da sala.
 *
 * Desde a ADR-0092 (docs/design/briefing-tela-3.md), o modal é o próprio computador do dev: um
 * terminal antigo de fósforo verde, num gabinete bege. A tela de entrada diz quem entrou, com que
 * mãos e em que pedido; cada passo é um comando com o prompt, e o resultado vem num selo como o da
 * inicialização do Linux (`[  OK  ]`, `[FALHOU]`, `[ ROBÔ ]`). Ao vivo, o prompt espera o próximo
 * passo com o cursor piscando; no fim, o resumo. Embaixo, a barra de status em vídeo invertido.
 *
 * O gerente abre pelo computador do dev na sala ou pelo chip. Tudo vem da sessão que o gateway
 * projeta (`state.workshop.sessions`); não há onde digitar, e nada aqui decide coisa do mundo. */
import type { ObserverState } from "@campsverso/contracts";

import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";
import { choiceName } from "../locale.ts";
import { pullRequestLine, ticketsOf } from "../panels/office.ts";
import { faceCell, faceSheet } from "../panels/portrait.ts";
import { clockText, tickSeconds } from "../simclock.ts";
import { handsName, sessionOf, sessionTicketState, stepShort } from "../workshop.ts";

export interface ScreenLine {
  readonly time: string;
  readonly text: string;
  readonly ok: boolean;
}

export interface ScreenView {
  /** "Tela do Camps". */
  readonly heading: string;
  /** "Pedido 2 · Conector do Codex". */
  readonly title: string;
  /** "Claude Code · Opus 5.5". */
  readonly hands: string;
  /** "começou 14:32 · 18 min · 23 passos · US$ 0,61". */
  readonly status: string;
  readonly lines: readonly ScreenLine[];
  /** "terminou: pronto · 19 voltas · US$ 0,50 · 5,4 min"; sem o fim, a sessão está em curso. */
  readonly end: string | undefined;
}

const STATE_WORDS: Readonly<Record<string, string>> = { entregue: "entregue", aceito: "aceito", a_fazer: "de volta em A fazer" };

function money(value: number): string {
  return `US$ ${value.toFixed(2).replace(".", ",")}`;
}

function minutes(seconds: number): string {
  const value = seconds / 60;
  return value < 10 ? `${value.toFixed(1).replace(".", ",")} min` : `${String(Math.round(value))} min`;
}

/** O que a tela mostra de um dev agora; sem sessão, nada. */
export function screenView(state: ObserverState, devId: string, tick: number): ScreenView | undefined {
  const session = sessionOf(state, devId);
  if (session === undefined) {
    return undefined;
  }
  const name = state.entities[devId]?.display_name ?? devId.charAt(0).toUpperCase() + devId.slice(1);
  const ticket = ticketsOf(state).find((t) => t.id === session.ticket_id);
  const title = ticket === undefined ? session.ticket_id : `Pedido ${String(ticket.number)} · ${ticket.title}`;
  const hands = [handsName(session.harness, (id) => choiceName("hands", id))];
  if (session.model !== undefined) {
    hands.push(choiceName("models", session.model));
  }
  const finished = session.finished;
  const last = session.steps.at(-1)?.tick ?? session.started_tick;
  const until = finished?.tick ?? (sessionTicketState(state, session) === "fazendo" ? tick : last);
  const elapsed = Math.max(0, until - session.started_tick) * tickSeconds(state.session);
  const steps = `${String(session.count)} ${session.count === 1 ? "passo" : "passos"}`;
  const status = [`começou ${clockText(state, session.started_tick).slice(0, 5)}`, minutes(elapsed), steps, money(session.cost_usd)].join(" · ");
  const lines = session.steps.map((step) => ({ time: clockText(state, step.tick).slice(0, 5), text: stepShort(step, 80), ok: step.ok }));
  let end: string | undefined;
  const estado = sessionTicketState(state, session);
  if (finished === undefined && estado !== undefined && estado !== "fazendo") {
    // A sessão fixa da rotina não publica o fim: a ficha diz que ela acabou.
    end = `fim: o pedido está ${STATE_WORDS[estado] ?? estado.replace("_", " ")}`;
  }
  if (finished !== undefined) {
    const parts = [`terminou: ${finished.reason}`, `${String(finished.turns)} voltas`];
    if (finished.cost_usd !== undefined) {
      parts.push(money(finished.cost_usd));
    }
    parts.push(minutes(finished.duration_ms / 1000));
    end = parts.join(" · ");
  }
  return { heading: `Tela do ${name}`, title, hands: hands.join(" · "), status, lines, end };
}

// ---------------------------------------------------------------- o terminal, em funções puras

/** O selo do resultado: deu certo, falhou ou foi um robô da bancada. */
export type Badge = "ok" | "falhou" | "robo";

const BADGE_TEXT: Readonly<Record<Badge, string>> = { ok: "  OK  ", falhou: "FALHOU", robo: " ROBÔ " };
/** O selo por extenso, para o leitor de tela. */
export const BADGE_SAID: Readonly<Record<Badge, string>> = { ok: "ok", falhou: "falhou", robo: "robô" };

export function badgeText(badge: Badge): string {
  return BADGE_TEXT[badge];
}

/** Um passo como comando: a linha do prompt e a do resultado. */
export interface TermEntry {
  /** O número do passo na sessão: a chave que nunca muda, para só acrescentar linhas. */
  readonly key: number;
  readonly command: string;
  readonly time: string;
  readonly badge: Badge;
  /** Depois do selo; vazio quando o comando já é o resumo do passo. */
  readonly result: string;
}

export type TermState = "live" | "done" | "empty";

export interface TerminalView {
  readonly devId: string;
  /** "Tela do Tiago": o título da plaqueta e do diálogo. */
  readonly heading: string;
  /** "o dev · LLM · mesa 1". */
  readonly plate: string;
  readonly state: TermState;
  /** A tela de entrada; `dim` é o texto apagado. */
  readonly boot: readonly { readonly text: string; readonly dim: boolean }[];
  /** "tiago@oficina:~/pedido-2$"; sem sessão, "tiago@oficina:~$". */
  readonly prompt: string;
  readonly entries: readonly TermEntry[];
  /** O resumo do fim, embaixo do divisor "fim da sessão". */
  readonly end: readonly string[];
  readonly bar: {
    readonly who: string;
    readonly ticket: string;
    readonly right: readonly string[];
    readonly state: string;
  };
}

/** Um passo como comando (briefing-tela-3.md, §3.3): a ferramenta e o caminho inteiro, com o resumo
 * depois do selo; sem caminho, o resumo é o comando; o robô da bancada, "robô testador". */
export function stepCommand(step: { readonly tool: string; readonly summary: string; readonly ok: boolean; readonly path?: string }): {
  readonly command: string;
  readonly badge: Badge;
  readonly result: string;
} {
  if (step.tool === "robô") {
    const [name = "", ...rest] = step.summary.split(" ");
    return { command: `robô ${name}`.trim(), badge: "robo", result: rest.join(" ") };
  }
  const badge: Badge = step.ok ? "ok" : "falhou";
  if (step.path !== undefined) {
    return { command: `${step.tool} ${step.path}`, badge, result: step.summary };
  }
  const said = step.summary.startsWith(`${step.tool}:`) ? step.summary.slice(step.tool.length + 1).trim() : step.summary;
  return { command: `${step.tool} ${said}`.trim(), badge, result: "" };
}

/** O comando cortado com "…" no que couber na linha, em letras (`ch`). */
export function fitCommand(command: string, width: number): string {
  const room = Math.max(4, Math.floor(width));
  return command.length <= room ? command : `${command.slice(0, room - 1)}…`;
}

const ROLE: Readonly<Record<string, string>> = { dev: "o dev", gerente: "o gerente", vigia: "o vigia" };
const CONTROLLER: Readonly<Record<string, string>> = { llm: "LLM", script: "script", human: "humano", replay: "replay" };

/** "o dev · LLM · mesa 1": o papel, quem o conduz e a mesa dele, pela ordem das mesas. */
function plateOf(state: ObserverState, devId: string): string {
  const entity = state.entities[devId];
  const papel = entity?.attributes.papel;
  const parts = [typeof papel === "string" ? (ROLE[papel] ?? papel) : "o dev"];
  const controller = state.controllers[devId]?.type;
  if (controller !== undefined) {
    parts.push(CONTROLLER[controller] ?? controller);
  }
  const desks = Object.entries(state.entities)
    .filter(([, e]) => e?.kind === "desk")
    .map(([id, e]) => ({ id, owner: e?.attributes.dono }))
    .sort((a, b) => (a.id < b.id ? -1 : 1));
  const desk = desks.findIndex((d) => d.owner === devId);
  if (desk >= 0) {
    parts.push(`mesa ${String(desk + 1)}`);
  }
  return parts.join(" · ");
}

const BOOT = "Campsverso OS 0.4 (oficina-1) tty1";

/** O terminal de um dev agora: a entrada, os passos como comandos, o fim e a barra. */
export function terminalOf(state: ObserverState, devId: string, tick: number): TerminalView {
  const name = state.entities[devId]?.display_name ?? devId.charAt(0).toUpperCase() + devId.slice(1);
  const heading = `Tela do ${name}`;
  const plate = plateOf(state, devId);
  const login = [
    { text: BOOT, dim: true },
    { text: `login: ${devId}`, dim: true },
  ];
  const session = sessionOf(state, devId);
  const view = screenView(state, devId, tick);
  if (session === undefined || view === undefined) {
    return {
      devId,
      heading,
      plate,
      state: "empty",
      boot: [
        ...login,
        { text: "Nenhuma sessão na oficina ainda.", dim: false },
        { text: `A tela acende quando o ${name} sentar para trabalhar num pedido.`, dim: false },
      ],
      prompt: `${devId}@oficina:~$`,
      entries: [],
      end: [],
      bar: { who: `[${devId}]`, ticket: "", right: [], state: "SEM SESSÃO" },
    };
  }
  const ticket = ticketsOf(state).find((t) => t.id === session.ticket_id);
  const number = ticket?.number;
  const ticketName = ticket === undefined ? session.ticket_id : `#${String(ticket.number)} ${ticket.title}`;
  const harness = handsName(session.harness, (id) => choiceName("hands", id));
  const welcome = session.model === undefined ? `Mãos: ${harness}` : `Mãos: ${harness} · modelo: ${choiceName("models", session.model)}`;
  const since = clockText(state, session.started_tick).slice(0, 5);
  const boot = [
    ...login,
    { text: `Bem-vindo, ${name}. ${welcome}`, dim: false },
    { text: `${ticket === undefined ? session.ticket_id : `Pedido #${String(ticket.number)} · ${ticket.title}`} · sessão desde ${since}`, dim: false },
  ];
  const first = session.count - session.steps.length + 1;
  const entries = session.steps.map((step, i) => ({
    key: first + i,
    time: clockText(state, step.tick).slice(0, 5),
    ...stepCommand(step),
  }));
  const estado = sessionTicketState(state, session);
  const finished = session.finished;
  const done = finished !== undefined || (estado !== undefined && estado !== "fazendo");
  const end: string[] = [];
  if (finished !== undefined) {
    const parts = [finished.reason, `${String(finished.turns)} voltas`, `${String(session.count)} passos`];
    if (finished.cost_usd !== undefined) {
      parts.push(money(finished.cost_usd));
    }
    parts.push(minutes(finished.duration_ms / 1000));
    end.push(parts.join(" · "));
  }
  if (done && ticket !== undefined && (estado === "entregue" || estado === "aceito")) {
    const pr = ticket.pr === undefined ? "" : `: ${pullRequestLine(ticket.pr)}`;
    end.push(`o pedido #${String(ticket.number)} foi ${estado === "aceito" ? "aceito" : "entregue"}${pr}`);
  } else if (done && estado !== undefined && estado !== "fazendo") {
    end.push(`o pedido está ${STATE_WORDS[estado] ?? estado.replace("_", " ")}`);
  }
  // A barra: as mãos e o modelo, o tempo, os passos e o custo, de `screenView`.
  const [, elapsed = "", steps = "", cost = ""] = view.status.split(" · ");
  return {
    devId,
    heading,
    plate,
    state: done ? "done" : "live",
    boot,
    prompt: `${devId}@oficina:~/pedido-${number === undefined ? session.ticket_id : String(number)}$`,
    entries,
    end,
    bar: {
      who: `[${devId}]`,
      ticket: ticketName,
      right: [view.hands, elapsed, steps, cost].filter((part) => part !== ""),
      state: done ? `TERMINOU · ${finished?.reason ?? (estado === undefined ? "fim" : (STATE_WORDS[estado] ?? estado))}` : "AO VIVO",
    },
  };
}

// ---------------------------------------------------------------- o gabinete

const MAX_LINES = 50;
/** O comando se digita a 32 ms por letra, entre 350 ms e 1,6 s. */
const TYPE_MS = 32;
const TYPE_MIN = 350;
const TYPE_MAX = 1600;
/** Vários passos de uma vez entram em fila, no máximo 0,8 s cada; mais de cinco, todos juntos. */
const QUEUE_MS = 800;
const QUEUE_MAX = 5;
const PHONE = "(max-width: 759px)";

function stillMotion(): boolean {
  return matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export class DevScreen {
  readonly element: HTMLDialogElement;
  private devId: string | undefined;
  private art: ArtManifest | undefined;
  private returnTo: HTMLElement | null = null;
  // As peças que ficam entre um desenho e outro: o log só acrescenta (§4).
  private readonly heading = el("h2", { className: "retro-term-heading" });
  private readonly plate = el("span", { className: "retro-term-plate-sub" });
  private readonly face = el("canvas", { className: "retro-term-face" });
  private readonly led = el("span", { className: "retro-term-led" });
  private readonly ledLabel = el("span", { className: "retro-term-led-label" });
  private readonly log = el("div", { className: "retro-term-log" });
  private readonly bootBox = el("div", { className: "retro-term-boot" });
  private readonly list = el("ol", { className: "retro-term-entries" });
  private readonly endBox = el("div", { className: "retro-term-end" });
  private readonly promptLine = el("div", { className: "retro-term-prompt" });
  private readonly pill = el("button", { className: "retro-term-pill" });
  private readonly bar = el("div", { className: "retro-term-bar" });
  private readonly measure = el("span", { className: "retro-term-measure" }, "0000000000");
  private shown = new Map<number, HTMLElement>();
  private session = "";
  private shownBoot = "";
  private shownEnd = "";
  private shownBar = "";
  private stuck = true;
  private unread = 0;

  constructor(parent: HTMLElement) {
    this.element = el("dialog", { className: "retro-devscreen-dialog" });
    this.element.setAttribute("aria-modal", "true");
    this.heading.id = "retro-devscreen-heading";
    this.element.setAttribute("aria-labelledby", this.heading.id);
    // O teclado anda com o avatar: com a tela aberta, ele fica aqui.
    this.element.addEventListener("keydown", (event) => { event.stopPropagation(); });
    this.element.addEventListener("close", () => {
      this.devId = undefined;
      this.returnTo?.focus();
    });
    this.log.setAttribute("role", "log");
    this.log.setAttribute("aria-live", "polite");
    this.log.setAttribute("aria-label", "Os passos do dev na oficina");
    this.log.tabIndex = 0;
    this.log.addEventListener("scroll", () => {
      this.stuck = this.log.scrollHeight - this.log.scrollTop - this.log.clientHeight < 24;
      if (this.stuck) {
        this.unread = 0;
        this.renderPill();
      }
    });
    this.pill.type = "button";
    this.pill.hidden = true;
    this.pill.addEventListener("click", () => { this.toBottom(); });
    const wrap = el("div", { className: "retro-term-wrap" }, this.bootBox, this.list, this.endBox, this.promptLine);
    this.log.append(wrap, this.measure);
    // Preso embaixo enquanto ninguém subiu: o passo novo cresce e a lista acompanha.
    new ResizeObserver(() => {
      if (this.stuck) {
        this.log.scrollTop = this.log.scrollHeight;
      }
    }).observe(wrap);
    const close = el("button", { className: "retro-button retro-devscreen-close" }, "Fechar");
    close.type = "button";
    close.addEventListener("click", () => { this.close(); });
    this.face.width = 32;
    this.face.height = 32;
    // A VT323 só baixa quando um texto a usa: pedida já, a régua do `ch` mede a letra certa na
    // primeira vez que a tela abre.
    void document.fonts.load('22px "VT323"').catch(() => undefined);
    this.element.append(
      el(
        "div",
        { className: "retro-term-cabinet" },
        el("div", { className: "retro-term-glass" }, el("div", { className: "retro-term-tube" }, this.log, this.pill, this.bar)),
        el(
          "div",
          { className: "retro-term-chin" },
          el(
            "div",
            { className: "retro-term-brand" },
            el("span", { className: "retro-term-brand-name" }, "CAMPSVERSO"),
            el("span", { className: "retro-term-brand-model" }, "OFICINA-1 · 640K"),
          ),
          el("span", { className: "retro-term-slits" }, el("i"), el("i"), el("i"), el("i"), el("i"), el("i")),
          el("div", { className: "retro-term-plate" }, this.face, el("div", {}, this.heading, this.plate)),
          el("span", { className: "retro-term-light" }, this.led, this.ledLabel),
          close,
        ),
      ),
    );
    parent.append(this.element);
  }

  get isOpen(): boolean {
    return this.element.open;
  }

  setArt(art: ArtManifest | undefined): void {
    this.art = art;
  }

  open(devId: string, state: ObserverState, tick: number): void {
    if (!this.element.open) {
      this.returnTo = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    }
    this.devId = devId;
    this.reset();
    this.drawFace(devId);
    if (!this.element.open) {
      this.element.showModal();
    }
    // Ao abrir, a história aparece de uma vez, pronta (§4); só o que chega depois anima.
    this.update(state, tick, false);
    this.toBottom();
    this.element.querySelector<HTMLElement>(".retro-devscreen-close")?.focus();
  }

  /** A cada quadro: a sessão anda, e a tela acompanha; o fim fica na tela até fechar. */
  update(state: ObserverState, tick: number, animate = true): void {
    if (this.devId === undefined || !this.element.open) {
      return;
    }
    const view = terminalOf(state, this.devId, tick);
    const session = `${view.prompt}|${view.state === "empty" ? "" : view.boot.map((b) => b.text).join("\n")}`;
    if (session !== this.session) {
      // Outro pedido, ou a sessão acabou de nascer com a tela aberta: a tela recomeça, e os passos
      // que chegam agora chegaram depois de abrir, então animam (só a abertura mostra tudo pronto).
      this.reset();
      this.session = session;
    }
    this.heading.textContent = view.heading;
    this.plate.textContent = view.plate;
    this.element.dataset.state = view.state;
    const light = view.state === "live" ? "ao vivo" : view.state === "done" ? "terminou" : "sem sessão";
    if (this.ledLabel.textContent !== light) {
      this.ledLabel.textContent = light;
    }
    this.renderBoot(view);
    this.renderEntries(view, animate);
    this.renderEnd(view);
    this.renderPrompt(view);
    this.renderBar(view);
  }

  close(): void {
    if (this.element.open) {
      this.element.close();
    }
  }

  private reset(): void {
    this.shown = new Map();
    this.list.replaceChildren();
    this.session = "";
    this.shownBoot = "";
    this.shownEnd = "";
    this.shownBar = "";
    this.unread = 0;
    this.stuck = true;
    this.renderPill();
  }

  /** O rosto do dev na plaqueta: o busto dos retratos cortado a partir de (4, 4). */
  private drawFace(devId: string): void {
    const art = this.art;
    const src = art === undefined ? undefined : faceSheet(art, devId);
    const context = this.face.getContext("2d");
    context?.clearRect(0, 0, 32, 32);
    if (art === undefined || src === undefined || context === null) {
      return;
    }
    const image = new Image();
    image.onload = () => {
      const cell = faceCell(art, devId, image);
      if (cell === undefined) {
        return;
      }
      context.imageSmoothingEnabled = false;
      const inset = cell.blinkDy === undefined ? 0 : 4;
      const size = cell.blinkDy === undefined ? cell.size : 32;
      context.drawImage(image, cell.sx + inset, cell.sy + inset, size, size, 0, 0, 32, 32);
    };
    image.src = src;
  }

  private renderBoot(view: TerminalView): void {
    const key = JSON.stringify(view.boot);
    if (key === this.shownBoot) {
      return;
    }
    this.shownBoot = key;
    this.bootBox.replaceChildren(
      ...view.boot.map((line) => el("div", { className: line.dim ? "retro-term-dim" : "" }, line.text)),
      ...(view.state === "empty" ? [] : [el("div", { className: "retro-term-divider" })]),
    );
  }

  /** Quantas letras cabem na linha do comando: a largura do log, menos o prompt e a hora. */
  private room(prompt: string): number {
    const ch = this.measure.getBoundingClientRect().width / 10;
    const width = this.log.clientWidth - 24; // o recuo da lista
    if (ch <= 0 || width <= 0) {
      return 60;
    }
    return Math.floor(width / ch) - prompt.length - 1 - 7; // o espaço, a folga e a hora
  }

  /** Só acrescenta: uma linha nova é um nó novo, e as velhas saem pela ponta de cima, até 50. */
  private renderEntries(view: TerminalView, animate: boolean): void {
    const fresh = view.entries.filter((entry) => !this.shown.has(entry.key));
    if (fresh.length === 0) {
      return;
    }
    const phone = matchMedia(PHONE).matches;
    const moving = animate && !stillMotion() && !phone && fresh.length <= QUEUE_MAX;
    const room = this.room(view.prompt);
    let start = 0;
    for (const entry of fresh) {
      const node = this.entry(view.prompt, entry, phone ? entry.command : fitCommand(entry.command, room));
      if (moving) {
        const letters = node.querySelector(".retro-term-cmd")?.textContent.length ?? 0;
        const typing = Math.min(TYPE_MAX, Math.max(TYPE_MIN, letters * TYPE_MS));
        node.classList.add("entering");
        node.style.setProperty("--start", `${String(start)}ms`);
        node.style.setProperty("--n", String(Math.max(1, letters)));
        node.style.setProperty("--type", `${String(typing)}ms`);
        start += Math.min(QUEUE_MS, 300 + typing + 400);
      }
      this.list.append(node);
      this.shown.set(entry.key, node);
    }
    while (this.list.children.length > MAX_LINES) {
      this.list.firstElementChild?.remove();
    }
    for (const [key, node] of this.shown) {
      if (!node.isConnected) {
        this.shown.delete(key); // saiu pela ponta de cima
      }
    }
    if (animate && !this.stuck) {
      this.unread += fresh.length;
      this.renderPill();
    }
  }

  private entry(prompt: string, entry: TermEntry, command: string): HTMLElement {
    // O selo desenhado fica fora do leitor de tela, que ouve o selo por extenso (§5).
    const badge = el(
      "span",
      { className: "retro-term-seal" },
      el("span", { className: "retro-term-bracket" }, "["),
      el("span", { className: `retro-term-badge ${entry.badge}` }, badgeText(entry.badge)),
      el("span", { className: "retro-term-bracket" }, "]"),
    );
    badge.setAttribute("aria-hidden", "true");
    const result: (HTMLElement | string)[] = [badge];
    if (entry.result !== "") {
      result.push(" ", el("span", { className: entry.badge === "falhou" ? "retro-term-failed" : "" }, entry.result));
    }
    const said = el("span", { className: "retro-term-said" }, ` ${BADGE_SAID[entry.badge]}`);
    const short = el("span", { className: "retro-term-prompt-short" }, "$ ");
    short.setAttribute("aria-hidden", "true");
    const late = el("time", { className: "retro-term-time-short" }, entry.time);
    late.setAttribute("aria-hidden", "true");
    const node = el(
      "li",
      { className: `retro-term-entry ${entry.badge}` },
      el(
        "div",
        { className: "retro-term-line" },
        el("span", { className: "retro-term-prompt-long" }, `${prompt} `),
        short,
        el("span", { className: "retro-term-cmd" }, command),
        el("time", { className: "retro-term-time" }, entry.time),
      ),
      el("div", { className: "retro-term-result" }, ...result, said, late),
    );
    node.title = entry.command;
    return node;
  }

  private renderEnd(view: TerminalView): void {
    const key = JSON.stringify([view.state, view.end]);
    if (key === this.shownEnd) {
      return;
    }
    this.shownEnd = key;
    this.endBox.replaceChildren(
      ...(view.state === "done"
        ? [el("div", { className: "retro-term-fim" }, "fim da sessão"), ...view.end.map((line) => el("div", { className: "retro-term-bright" }, line))]
        : []),
    );
  }

  private renderPrompt(view: TerminalView): void {
    const key = `${view.prompt}|${view.state}`;
    if (this.promptLine.dataset.key === key) {
      return;
    }
    this.promptLine.dataset.key = key;
    this.promptLine.replaceChildren(
      el("span", { className: "retro-term-prompt-long" }, `${view.prompt} `),
      el("span", { className: "retro-term-prompt-short" }, "$ "),
      el("span", { className: "retro-term-cursor" }),
    );
    this.promptLine.setAttribute("aria-hidden", "true");
  }

  private renderBar(view: TerminalView): void {
    const key = JSON.stringify(view.bar);
    if (key === this.shownBar) {
      return;
    }
    this.shownBar = key;
    this.bar.replaceChildren(
      el("span", { className: "retro-term-bar-left" }, el("span", {}, view.bar.who), " ", el("span", { className: "retro-term-bar-ticket" }, view.bar.ticket)),
      ...view.bar.right.map((part) => el("span", { className: "retro-term-bar-seg" }, part)),
      el("span", { className: `retro-term-bar-state ${view.state}` }, view.bar.state),
    );
  }

  private renderPill(): void {
    this.pill.hidden = this.unread === 0;
    this.pill.textContent = `▼ ${String(this.unread)} ${this.unread === 1 ? "linha nova" : "linhas novas"}`;
  }

  private toBottom(): void {
    this.stuck = true;
    this.unread = 0;
    this.renderPill();
    this.log.scrollTop = this.log.scrollHeight;
  }
}
