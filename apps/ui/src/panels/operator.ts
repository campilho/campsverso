/** Painel do operador: relógio, controlador, decisão atual, o caderno do avatar, o custo das mentes,
 * métricas do dia e linha do tempo (escopo §6; ADR-0050, ADR-0054, ADR-0060, ADR-0074).
 *
 * Os botões só pedem: quem aceita ou recusa é o kernel, e a resposta volta como evento. Desabilitar
 * "Avançar" fora da pausa é conforto (ADR-0026), não regra.
 */
import type { EnvelopeV1, EventLabel, ObserverState, RealtimeReplyV1 } from "@campsverso/contracts";

import { budgetLine, costLines, guardLine } from "../costs.ts";
import { button, el } from "../dom.ts";
import { metricTable } from "../metrics.ts";
import { clockText } from "../simclock.ts";
import { describe, matches, shortType, summarize, type TimelineFilter, type Visibility } from "../timeline.ts";

const CMD = "campsverso.cmd.clock.";
/** Os tetos do orçamento com o mundo vivo (ADR-0080): quem aceita é a guarda. */
export const BUDGET_SET = "campsverso.cmd.ops.budget.set.v1";
const LIMITS = [
  ["usd_per_sim_day", "dia"],
  ["usd_per_ticket", "pedido"],
  ["usd_total", "total"],
] as const;
const VISIBILITIES: readonly Visibility[] = ["world", "agent", "internal", "observer"];
const SHOWN = 300;

export type Send = (command: string, data: Record<string, unknown>) => void;

export class OperatorPanel {
  private filter: TimelineFilter = { visibilities: new Set(VISIBILITIES), text: "" };
  // Os nomes `op-*` deixam a gaveta da tela retrô arrumar as seções (docs/design/briefing-tela.md, §3.8).
  private readonly controls = el("section", { className: "card op-clock" });
  private readonly decision = el("section", { className: "card op-decision" });
  private readonly notebook = el("section", { className: "card notebook" });
  private readonly costs = el("section", { className: "card costs" });
  private readonly costLines = el("div");
  /** O formulário dos tetos fica fora do redesenho do custo: o sinal da guarda chega a cada 5 s e
   * apagaria o que o operador está digitando. */
  private readonly limits = el("form", { className: "limits" });
  private readonly limitInputs = new Map<(typeof LIMITS)[number][0], HTMLInputElement>();
  private readonly metrics = el("section", { className: "card metrics" });
  private readonly filters = el("div", { className: "filters" });
  private readonly list = el("ol", { className: "timeline" });
  /** O que cada parte mostrou da última vez: refazer o DOM sem mudança engoliria cliques. */
  private readonly shown = { controls: "", decision: "", notebook: "", costs: "", metrics: "", timeline: "" };

  private readonly send: Send;
  private readonly onFilter: () => void;

  constructor(root: HTMLElement, send: Send, onFilter: () => void) {
    this.send = send;
    this.onFilter = onFilter;
    this.buildFilters();
    this.buildLimits();
    this.costs.replaceChildren(el("h3", {}, "Custo"), this.costLines, this.limits);
    root.replaceChildren(
      el("h2", {}, "Painel do operador"),
      this.controls,
      this.decision,
      this.notebook,
      this.costs,
      this.metrics,
      el("section", { className: "card grow op-timeline" }, el("h3", {}, "Linha do tempo"), this.filters, this.list),
    );
  }

  private buildLimits(): void {
    const fields = LIMITS.map(([key, label]) => {
      const input = el("input");
      input.type = "number";
      input.min = "0.01";
      input.step = "0.01";
      input.name = key;
      this.limitInputs.set(key, input);
      return el("label", {}, `${label} US$ `, input);
    });
    const submit = el("button", {}, "Mudar os tetos");
    submit.type = "submit";
    this.limits.addEventListener("submit", (event) => {
      event.preventDefault();
      const data: Record<string, unknown> = { reason: "pela tela do operador" };
      for (const [key, input] of this.limitInputs) {
        const value = Number(input.value);
        if (input.value !== "" && Number.isFinite(value) && value > 0) {
          data[key] = value;
        }
      }
      this.send(BUDGET_SET, data);
    });
    this.limits.hidden = true;
    this.limits.replaceChildren(...fields, submit);
  }

  private buildFilters(): void {
    const boxes = VISIBILITIES.map((visibility) => {
      const input = el("input");
      input.type = "checkbox";
      input.checked = true;
      input.addEventListener("change", () => {
        const next = new Set(this.filter.visibilities);
        if (input.checked) {
          next.add(visibility);
        } else {
          next.delete(visibility);
        }
        this.filter = { ...this.filter, visibilities: next };
        this.shown.timeline = "";
        this.onFilter();
      });
      return el("label", { className: `vis ${visibility}` }, input, visibility);
    });
    const text = el("input");
    text.placeholder = "filtrar por tipo (ex.: action, farm)";
    text.addEventListener("input", () => {
      this.filter = { ...this.filter, text: text.value };
      this.shown.timeline = "";
      this.onFilter();
    });
    this.filters.replaceChildren(...boxes, text);
  }

  render(
    state: ObserverState,
    avatarId: string,
    commands: readonly string[],
    timeline: readonly EnvelopeV1[],
    reply: RealtimeReplyV1 | undefined,
  ): void {
    this.renderControls(state, commands, reply);
    this.renderDecision(state, avatarId);
    this.renderNotebook(state, avatarId);
    this.renderCosts(state);
    this.renderMetrics(state);
    this.renderTimeline(timeline, state.session?.labels ?? []);
  }

  private renderMetrics(state: ObserverState): void {
    const table = metricTable(state);
    const key = JSON.stringify(table ?? null);
    if (key === this.shown.metrics) {
      return;
    }
    this.shown.metrics = key;
    this.metrics.hidden = table === undefined;
    if (table === undefined) {
      return;
    }
    const head = el("tr", {}, el("th", {}, ""), el("th", {}, "hoje"), el("th", {}, "ontem"), el("th", {}, table.weekLabel));
    const rows = table.rows.map((row) =>
      el("tr", {}, el("th", {}, row.label), el("td", {}, row.today), el("td", {}, row.yesterday), el("td", {}, row.week)),
    );
    this.metrics.replaceChildren(el("h3", {}, "Métricas do dia"), el("table", {}, el("thead", {}, head), el("tbody", {}, ...rows)));
  }

  private renderControls(state: ObserverState, commands: readonly string[], reply: RealtimeReplyV1 | undefined): void {
    const key = JSON.stringify([state.clock, commands, reply]);
    if (key === this.shown.controls) {
      return;
    }
    this.shown.controls = key;
    const can = (verb: string): boolean => commands.includes(`${CMD}${verb}.v1`);
    const paused = state.clock.paused === true;
    const { mode, scale } = state.clock;
    const step = (ticks: number): HTMLButtonElement =>
      button(`+${String(ticks)}`, () => { this.send(`${CMD}step.v1`, { ticks }); }, can("step") && paused);
    const pace = (value: number): HTMLButtonElement =>
      button(
        `${String(value)}×`,
        () => {
          if (mode !== "continuous") {
            this.send(`${CMD}set_mode.v1`, { mode: "continuous", reason: "operador pela UI" });
          }
          this.send(`${CMD}set_scale.v1`, { scale: value, reason: "operator" });
        },
        can("set_scale"),
        mode === "continuous" && scale === value,
      );
    this.controls.replaceChildren(
      el("h3", {}, "Relógio"),
      el(
        "div",
        { className: "buttons" },
        paused
          ? button("Retomar", () => { this.send(`${CMD}resume.v1`, {}); }, can("resume"))
          : button("Pausar", () => { this.send(`${CMD}pause.v1`, { reason: "debug" }); }, can("pause")),
        el("span", { className: "hint" }, "avançar (ticks):"),
        step(1),
        step(10),
        step(60),
      ),
      el(
        "div",
        { className: "buttons" },
        pace(1),
        pace(72),
        pace(144),
        pace(720),
        button(
          "Máximo",
          () => { this.send(`${CMD}set_mode.v1`, { mode: "max", reason: "operador pela UI" }); },
          can("set_mode"),
          mode === "max",
        ),
      ),
      ...(reply?.ok === false && reply.error !== undefined
        ? [el("p", { className: "error" }, `gateway: ${reply.error.code}: ${reply.error.message}`)]
        : []),
    );
  }

  private renderDecision(state: ObserverState, avatarId: string): void {
    const controller = state.controllers[avatarId];
    const decision = state.decisions[avatarId];
    const action = state.actions[avatarId];
    const key = JSON.stringify([controller, decision, action]);
    if (key === this.shown.decision) {
      return;
    }
    this.shown.decision = key;
    this.decision.replaceChildren(
      el("h3", {}, "Controlador e decisão"),
      el("p", {}, controller === undefined ? "—" : `${controller.type} · ${controller.id}`),
      el("p", {}, decision === undefined ? "sem pedido de decisão" : `último pedido: ${decision.reason} (tick ${String(decision.tick)})`),
      el(
        "p",
        { className: "mono" },
        action === undefined
          ? "nenhuma ação em andamento"
          : `${action.action} ${JSON.stringify(action.params)} até o tick ${String(action.end_tick)}${action.intent === undefined ? "" : ` · ${action.intent}`}`,
      ),
    );
  }

  /** O caderno do avatar (ADR-0060): o que a mente anotou, acredita e resumiu da última noite. */
  private renderNotebook(state: ObserverState, avatarId: string): void {
    const book = state.memory?.[avatarId];
    const key = JSON.stringify(book ?? null);
    if (key === this.shown.notebook) {
      return;
    }
    this.shown.notebook = key;
    if (book === undefined) {
      this.notebook.replaceChildren(el("h3", {}, "Caderno"), el("p", { className: "hint" }, "vazio: só a mente escreve nele"));
      return;
    }
    const beliefs = book.beliefs.map((b) => el("li", {}, el("b", {}, b.confidence.toFixed(2)), ` ${b.statement}`));
    const notes = [...book.notes]
      .reverse()
      .slice(0, 10)
      .map((n) => el("li", {}, el("span", { className: "tick" }, clockText(state, n.tick)), ` ${n.text}`));
    this.notebook.replaceChildren(
      el("h3", {}, "Caderno"),
      ...(book.summary === undefined ? [] : [el("p", {}, el("b", {}, `Dia ${String(book.day ?? "?")}, ao dormir: `), book.summary)]),
      ...(book.plan === undefined ? [] : [el("p", {}, el("b", {}, "Plano: "), book.plan)]),
      el("h4", {}, "Crenças"),
      beliefs.length > 0 ? el("ul", {}, ...beliefs) : el("p", { className: "hint" }, "nenhuma ainda"),
      el("h4", {}, "Anotações"),
      notes.length > 0 ? el("ul", {}, ...notes) : el("p", { className: "hint" }, "nenhuma ainda"),
    );
  }

  /** O custo das mentes (ADR-0074): some num mundo sem modelo. */
  private renderCosts(state: ObserverState): void {
    const lines = costLines(state);
    const budget = budgetLine(state);
    const guard = guardLine(state);
    const limits = state.costs?.guard?.limits;
    const key = JSON.stringify([lines, budget, guard, limits]);
    if (key === this.shown.costs) {
      return;
    }
    this.shown.costs = key;
    this.costs.hidden = lines.length === 0 && budget === undefined && guard === undefined;
    this.costLines.replaceChildren(
      el("ul", {}, ...lines.map((line) => el("li", {}, line))),
      ...[guard, budget].filter((line) => line !== undefined).map((line) => el("p", { className: "hint" }, line)),
    );
    // Os tetos de agora nos campos, menos no que o operador está editando.
    this.limits.hidden = limits === undefined;
    for (const [key, input] of this.limitInputs) {
      const value = limits?.[key];
      if (document.activeElement !== input) {
        input.value = value === undefined ? "" : String(value);
      }
    }
  }

  private renderTimeline(timeline: readonly EnvelopeV1[], labels: readonly EventLabel[]): void {
    const key = `${String(timeline.length)}:${timeline.at(-1)?.id ?? ""}`;
    if (key === this.shown.timeline) {
      return;
    }
    this.shown.timeline = key;
    const rows: HTMLElement[] = [];
    for (let i = timeline.length - 1; i >= 0 && rows.length < SHOWN; i--) {
      const event = timeline[i];
      if (event === undefined || !matches(event, this.filter)) {
        continue;
      }
      const rejected = event.type.endsWith(".rejected.v1");
      // O rótulo do cartucho, quando há (ADR-0068); embaixo, o tipo cru, para quem depura.
      const label = describe(event, labels);
      rows.push(
        el(
          "li",
          { className: `${event.visibility}${rejected ? " rejected" : ""}`, title: JSON.stringify(event.data, null, 2) },
          el("span", { className: "tick" }, String(event.tick ?? "")),
          el("span", { className: "vis-tag" }, event.visibility),
          label === undefined ? el("span", { className: "type" }, shortType(event.type)) : el("span", { className: "type label" }, label),
          el("span", { className: "summary" }, label === undefined ? summarize(event) : shortType(event.type)),
        ),
      );
    }
    this.list.replaceChildren(...rows);
  }
}
