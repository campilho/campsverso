/** A tela do dev (ADR-0089): a sessão dele na oficina, ao vivo, num monitor por cima da sala.
 *
 * O gerente abre pelo chip do dev. A tela mostra o pedido, as mãos e o modelo, o começo, quanto
 * tempo, quantos passos e quanto custou até agora, e os últimos passos, um por linha. No fim, o
 * motivo, as voltas, o custo e o tempo. Tudo vem da sessão que o gateway projeta
 * (`state.workshop.sessions`); nada aqui decide coisa do mundo. */
import type { ObserverState } from "@campsverso/contracts";

import { el } from "../dom.ts";
import { choiceName } from "../locale.ts";
import { ticketsOf } from "../panels/office.ts";
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

export class DevScreen {
  readonly element: HTMLDialogElement;
  private devId: string | undefined;
  private shown = "";
  private readonly list = el("ol", { className: "retro-devscreen-lines" });

  constructor(parent: HTMLElement) {
    this.element = el("dialog", { className: "retro-devscreen-dialog" });
    this.element.setAttribute("aria-modal", "true");
    // O teclado anda com o avatar: com a tela aberta, ele fica aqui.
    this.element.addEventListener("keydown", (event) => { event.stopPropagation(); });
    this.element.addEventListener("close", () => {
      this.devId = undefined;
      this.shown = "";
    });
    this.list.setAttribute("aria-live", "polite");
    parent.append(this.element);
  }

  get isOpen(): boolean {
    return this.element.open;
  }

  open(devId: string, state: ObserverState, tick: number): void {
    this.devId = devId;
    this.shown = "";
    this.update(state, tick);
    if (!this.element.open) {
      this.element.showModal();
    }
    this.element.querySelector<HTMLElement>(".retro-devscreen-close")?.focus();
  }

  /** A cada quadro: a sessão anda, e a tela acompanha; o fim fica na tela até fechar. */
  update(state: ObserverState, tick: number): void {
    if (this.devId === undefined || !this.element.open) {
      return;
    }
    const view = screenView(state, this.devId, tick);
    const key = JSON.stringify(view ?? null);
    if (key === this.shown) {
      return;
    }
    this.shown = key;
    const atBottom = this.list.scrollHeight - this.list.scrollTop - this.list.clientHeight < 24;
    this.render(view);
    if (atBottom) {
      this.list.scrollTop = this.list.scrollHeight; // segue o passo novo, se ninguém subiu a lista
    }
  }

  close(): void {
    if (this.element.open) {
      this.element.close();
    }
  }

  private render(view: ScreenView | undefined): void {
    const heading = el("h2", { className: "retro-devscreen-heading" }, view?.heading ?? "Tela do dev");
    heading.id = "retro-devscreen-heading";
    this.element.setAttribute("aria-labelledby", heading.id);
    const close = el("button", { className: "retro-button retro-devscreen-close" }, "Fechar");
    close.type = "button";
    close.addEventListener("click", () => { this.close(); });
    const screen: HTMLElement[] = [];
    if (view === undefined) {
      screen.push(el("p", { className: "retro-devscreen-status" }, "Nenhuma sessão na oficina ainda."));
      this.list.replaceChildren();
    } else {
      screen.push(
        el("p", { className: "retro-devscreen-title" }, view.title),
        el("p", { className: "retro-devscreen-status" }, view.status),
      );
      this.list.replaceChildren(
        ...view.lines.map((line) =>
          el("li", { className: line.ok ? "" : "falhou" }, el("time", {}, line.time), el("span", {}, line.text)),
        ),
      );
      screen.push(this.list);
      screen.push(el("p", { className: `retro-devscreen-end${view.end === undefined ? " live" : ""}` }, view.end ?? "trabalhando…"));
    }
    this.element.replaceChildren(
      el(
        "div",
        { className: "retro-devscreen-panel" },
        el("header", { className: "retro-devscreen-head" }, heading, el("span", { className: "retro-devscreen-hands" }, view?.hands ?? "")),
        el("div", { className: "retro-devscreen-screen" }, ...screen),
        el("div", { className: "retro-devscreen-bar" }, close),
      ),
    );
  }
}
