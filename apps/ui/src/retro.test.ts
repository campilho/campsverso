/** A tela retrô do escritório (docs/design/briefing-tela.md): a luz, o relógio e os chips das
 * pessoas, em funções puras. */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { bannerOf, type Banner, type Notice } from "./banner.ts";
import { choicesOf, setLocale } from "./locale.ts";
import { summonsOf, type TicketView } from "./panels/office.ts";
import type { Step } from "./queue.ts";
import { chipsOf, clockView, lightOf, robotLine, summonShort, versionLine } from "./retro/model.ts";
import { overHead } from "./progress.ts";
import { handsLine } from "./retro/clipboard.ts";
import { screenView } from "./retro/devscreen.ts";
import { prsText, systemOf } from "./retro/system.ts";
import {
  completeMention,
  linesOf,
  mentionQuery,
  mentionTarget,
  peopleLine,
  peopleOf,
  personTag,
  splitMentions,
  suggestionsOf,
} from "./retro/talk.ts";
import {
  EMPTY_DRAFT,
  badgeOfPullRequest,
  boardSummary,
  counterOf,
  ghostsOf,
  nextNumber,
  nextTab,
  parseDraft,
  pinOf,
  remainingOf,
  squareOf,
  stateLabel,
  tabsOf,
  whoLine,
  writtenOf,
} from "./retro/tickets.ts";

function state(overrides: Partial<ObserverState> = {}): ObserverState {
  return {
    tick: 16200,
    sim_time: "2026-11-16T09:00:00-03:00",
    day: 1,
    phase: "manha",
    session: { cartridge_version: "0.1.0", tick_seconds: 2, map: { id: "office_campsverso", width: 20, height: 17 } },
    clock: { mode: "continuous", scale: 1, paused: false },
    weather: {},
    entities: {},
    containers: {},
    motion: {},
    actions: {},
    needs: {},
    asleep: {},
    controllers: {},
    decisions: {},
    ...overrides,
  };
}

const swap: Banner = { text: "Trocando de versão…", tone: "info", kind: "troca" };

describe("a luz da barra de cima", () => {
  it("é verde online, âmbar na troca e na espera, vermelha sem conexão, sempre com o rótulo", () => {
    expect(lightOf("open", true, undefined)).toEqual({ color: "verde", label: "online" });
    expect(lightOf("open", true, swap)).toEqual({ color: "ambar", label: "atualizando" });
    expect(lightOf("open", true, { ...swap, kind: "espera" }).color).toBe("ambar");
    expect(lightOf("open", true, { ...swap, kind: "fresh" }).color).toBe("verde");
    expect(lightOf("closed", true, swap)).toEqual({ color: "vermelha", label: "sem conexão" });
    expect(lightOf("connecting", true, undefined).color).toBe("vermelha");
    expect(lightOf("open", false, undefined).color).toBe("vermelha"); // o mundo parou de pulsar
  });
});

describe("o relógio da barra de baixo", () => {
  it("diz a hora, o dia com a fase e o ritmo só quando não é 1×", () => {
    expect(clockView(state(), "09:00:12")).toEqual({ hour: "09:00", day: "Dia 1 · manhã", date: "Dia 1", period: "manhã", pace: undefined });
    const fast = state({ day: 3, phase: "tarde", clock: { mode: "continuous", scale: 72, paused: false } });
    expect(clockView(fast, "15:30:00")).toEqual({ hour: "15:30", day: "Dia 3 · tarde", date: "Dia 3", period: "tarde", pace: "72×" });
  });
});

describe("os chips das pessoas", () => {
  const out = { kind: "avatar", display_name: "Camps", attributes: { papel: "dev" } }; // fora: sem posição
  const camps = { ...out, position: { x: 4, y: 6 } };
  const vigia = { kind: "avatar", display_name: "Vigia", position: { x: 2, y: 14 }, attributes: { papel: "vigia" } };
  const gerente = { kind: "avatar", display_name: "Gerente", position: { x: 9, y: 14 }, attributes: { papel: "gerente" } };
  const testador = { kind: "robot", display_name: "Testador", position: { x: 15, y: 4 }, attributes: {} };
  const briefing = { kind: "robot", display_name: "Briefing", position: { x: 16, y: 4 }, attributes: {} };

  it("vêm nesta ordem: o dev, o vigia, o gerente e os robôs, com a etiqueta de quem controla", () => {
    const office = state({
      entities: { testador, gerente, vigia, camps, briefing },
      controllers: {
        camps: { type: "llm" },
        vigia: { type: "script" },
        gerente: { type: "human" },
      } as unknown as ObserverState["controllers"],
    });
    const chips = chipsOf(office, "gerente", office.tick);
    expect(chips.map((c) => [c.id, c.tag])).toEqual([
      ["camps", "LLM"],
      ["vigia", "script"],
      ["gerente", "você"],
      ["briefing", "robô"],
      ["testador", "robô"],
    ]);
    expect(chips.find((c) => c.id === "vigia")).toMatchObject({ icon: "vigiar", line: "vigiando", away: false });
    const looking = state({ ...office, actions: { vigia: { action: "wait" } } as unknown as ObserverState["actions"] });
    expect(chipsOf(looking, "gerente", office.tick).find((c) => c.id === "vigia")?.line).toBe("vigiando"); // olhando a sala
    expect(chips.find((c) => c.id === "gerente")?.line).toBe("no escritório");
    expect(chips.filter((c) => c.robot).map((c) => c.line)).toEqual(["parado", "parado"]);
  });

  it("o gerente com o script não é você, e a ação curta vai na linha, a intenção no title", () => {
    const office = state({
      entities: { camps, gerente },
      controllers: { gerente: { type: "script" } } as unknown as ObserverState["controllers"],
      actions: { camps: { action: "work", intent: "o pedido 3" } } as unknown as ObserverState["actions"],
    });
    const chips = chipsOf(office, "gerente", office.tick);
    expect(chips.find((c) => c.id === "gerente")).toMatchObject({ tag: "script", line: "parado" });
    const dev = chips.find((c) => c.id === "camps");
    expect(dev?.icon).toBe("work");
    expect(dev?.title).toBe(`${dev?.line ?? ""} · o pedido 3`);
    expect(dev?.line.charAt(0)).toBe(dev?.line.charAt(0).toLowerCase());
  });

  it("o dev na mesa com uma sessão na oficina diz quem programa e o modelo (ADR-0089)", () => {
    setLocale([{ choices: { hands: { claude_code: "Claude Code" }, models: { "claude-opus-5-5": "Opus 5.5" } } }]);
    const step = { ticket_id: "pedido-003", tool: "Edit", ok: true, tick: 16100, harness: "claude_code", model: "claude-opus-5-5" };
    const office = state({
      entities: { camps, gerente },
      actions: { camps: { action: "work", intent: "o pedido 3" } } as unknown as ObserverState["actions"],
      workshop: { steps: { camps: step } },
    });
    const dev = chipsOf(office, "gerente", office.tick).find((c) => c.id === "camps");
    expect(dev?.line).toBe("programando · Claude Code · Opus 5.5");
    expect(dev?.title).toBe("programando · Claude Code · Opus 5.5 · o pedido 3");
    // Um passo velho, ou do v1 (sem as mãos), não muda a linha.
    const old = state({ ...office, workshop: { steps: { camps: { ...step, tick: 0 } } } });
    expect(chipsOf(old, "gerente", 16200 + 3 * 3600).find((c) => c.id === "camps")?.line).not.toContain("programando");
    const v1 = state({ ...office, workshop: { steps: { camps: { ticket_id: "pedido-003", tool: "ler", ok: true, tick: 16100 } } } });
    expect(chipsOf(v1, "gerente", v1.tick).find((c) => c.id === "camps")?.line).not.toContain("programando");
    setLocale([]);
  });

  it("quem dorme mostra dormindo, e quem está fora tem a borda tracejada", () => {
    const office = state({
      entities: { camps: out, gerente },
      asleep: { gerente: true },
    });
    const chips = chipsOf(office, "gerente", office.tick);
    expect(chips.find((c) => c.id === "camps")).toMatchObject({ away: true, icon: "fora", line: "fora" });
    expect(chips.find((c) => c.id === "gerente")).toMatchObject({ icon: "dormir", line: "dormindo" });
  });

  it("o dev fora da visão do jogador vem da convocação na linha do tempo, e o gerente fora também aparece", () => {
    const empty = state({ entities: {} });
    expect(chipsOf(empty, "gerente", empty.tick).map((c) => [c.id, c.away])).toEqual([["gerente", true]]);
    const event = {
      type: "campsverso.office.staff.summoned.v1",
      data: { avatar_id: "camps", by: "gerente", origin: "botao", arrives_tick: 16260, until_tick: 16800 },
    } as unknown as EnvelopeV1;
    const chips = chipsOf(empty, "gerente", empty.tick, [event]);
    expect(chips.map((c) => c.id)).toEqual(["camps", "gerente"]);
    expect(chips[0]).toMatchObject({ name: "Camps", away: true, line: "a caminho · 09:02" });
  });

  it("a linha curta da convocação: a caminho, convocado até uma hora, fora", () => {
    const summon = { convocado_por: "gerente", convocado_chega: 16260, convocado_ate: 16200 + 6 * 60 * 30 };
    const coming = state({ entities: { camps: { ...out, attributes: { papel: "dev", ...summon } } } });
    const [dev] = summonsOf(coming);
    expect(dev && summonShort(coming, dev)).toBe("a caminho · 09:02");
    const there = state({ entities: { camps: { ...camps, attributes: { papel: "dev", ...summon } } } });
    const [present] = summonsOf(there);
    expect(present && summonShort(there, present)).toBe("convocado até 15:00");
    const away = state({ entities: { camps: out } });
    const [gone] = summonsOf(away);
    expect(gone && summonShort(away, gone)).toBe("fora");
  });
});

describe("o robô da bancada", () => {
  it("trabalha, passa ou falha pela última chamada, e volta a parado depois", () => {
    const robots = (robot: { state: "working" | "passed" | "failed"; tick: number }): ObserverState =>
      state({ workshop: { robots: { testador: { ...robot, avatar_id: "camps" } } } });
    expect(robotLine(state(), "testador", 16200)).toBe("parado");
    expect(robotLine(robots({ state: "working", tick: 16100 }), "testador", 16200)).toBe("trabalhando");
    expect(robotLine(robots({ state: "passed", tick: 16190 }), "testador", 16200)).toBe("passou");
    expect(robotLine(robots({ state: "failed", tick: 16190 }), "testador", 16200)).toBe("falhou");
    expect(robotLine(robots({ state: "passed", tick: 10000 }), "testador", 16200)).toBe("parado");
    expect(robotLine(robots({ state: "working", tick: 0 }), "testador", 16200)).toBe("parado"); // passou das duas horas
  });
});

describe("o quadro de cortiça (§3.4)", () => {
  const ticket = (n: number, state: string, extra: Partial<TicketView> = {}): TicketView => ({
    id: `pedido-${String(n).padStart(3, "0")}`,
    number: n,
    title: `Pedido ${String(n)}`,
    description: "",
    acceptance: "",
    size: "M",
    state,
    owner: undefined,
    author: "gerente",
    comment: undefined,
    patch: undefined,
    pr: undefined,
    harness: undefined,
    model: undefined,
    ...extra,
  });
  const open = { number: 7, url: "https://github.com/campilho/campsverso/pull/7", state: "aberto", ci: "success" };
  const tickets = [
    ticket(1, "aceito", { pr: { ...open, number: 5, state: "mesclado" } }),
    ticket(2, "entregue", { pr: open }),
    ticket(3, "fazendo", { owner: "camps" }),
    ticket(4, "a_fazer"),
    ticket(5, "a_fazer"),
  ];

  it("conta os pedidos de cada aba, nas quatro colunas", () => {
    expect(tabsOf(tickets).map((t) => [t.label, t.count])).toEqual([
      ["A fazer", 2],
      ["Fazendo", 1],
      ["Entregue", 1],
      ["Aceito", 1],
    ]);
    expect(tabsOf([]).every((t) => t.count === 0)).toBe(true);
  });

  it("diz no cabeçalho os pedidos e os PRs abertos", () => {
    expect(boardSummary(tickets)).toBe("5 pedidos · 1 PR aberto");
    expect(boardSummary([ticket(1, "a_fazer")])).toBe("1 pedido");
    expect(boardSummary([ticket(1, "entregue", { pr: open }), ticket(2, "entregue", { pr: open })])).toBe("2 pedidos · 2 PR abertos");
  });

  it("anda entre as abas pelas setas, dando a volta, e Home e End vão às pontas", () => {
    expect(nextTab(0, "ArrowRight", 4)).toBe(1);
    expect(nextTab(3, "ArrowRight", 4)).toBe(0);
    expect(nextTab(0, "ArrowLeft", 4)).toBe(3);
    expect(nextTab(2, "Home", 4)).toBe(0);
    expect(nextTab(1, "End", 4)).toBe(3);
    expect(nextTab(1, "Enter", 4)).toBeUndefined();
  });

  it("põe a ficha fantasma do pedido que o gerente está escrevendo e dos que estão na fila", () => {
    const step = (title: string, size: string): Step => ({
      label: `Escrever o pedido "${title}"`,
      proposal: { avatar_id: "gerente", action: "write_ticket", params: { title, size } },
      near: "quadro",
    });
    const walk: Step = { label: "Ir até a porta", proposal: { avatar_id: "gerente", action: "move", params: { near: "porta" } } };
    const writing = state({
      actions: { gerente: { action: "write_ticket", params: { title: "A lousa", size: "G" } } } as unknown as ObserverState["actions"],
    });
    expect(ghostsOf([walk, step("O café", "P")], writing, "gerente")).toEqual([
      { title: "A lousa", size: "G" },
      { title: "O café", size: "P" },
    ]);
    expect(ghostsOf([walk], state(), "gerente")).toEqual([]);
    expect(ghostsOf([], writing, "camps")).toEqual([]); // só os passos de quem joga
  });

  it("diz de quem é a ficha, o selo do PR, o pino e o número de prévia", () => {
    const office = state({
      entities: {
        camps: { kind: "avatar", display_name: "Camps", attributes: { papel: "dev" } },
        gerente: { kind: "avatar", display_name: "Gerente", attributes: { papel: "gerente" } },
      },
    });
    expect(whoLine(ticket(3, "fazendo", { owner: "camps" }), office)).toBe("com Camps");
    expect(whoLine(ticket(4, "a_fazer"), office)).toBe("do gerente");
    expect(whoLine(ticket(4, "a_fazer", { author: undefined }), office)).toBe("");
    expect(badgeOfPullRequest(open)).toBe("ci_verde");
    expect(badgeOfPullRequest({ ...open, ci: "failure" })).toBe("ci_vermelho");
    expect(badgeOfPullRequest({ ...open, ci: "" })).toBe("pr");
    expect(badgeOfPullRequest({ ...open, state: "mesclado" })).toBe("mesclado");
    expect(badgeOfPullRequest({ ...open, state: "fechado" })).toBeUndefined();
    expect([pinOf(1), pinOf(2)]).toEqual(["vermelho", "azul"]);
    expect(nextNumber(tickets)).toBe(6);
    expect(nextNumber([])).toBe(1);
    expect(stateLabel("entregue")).toBe("ENTREGUE");
  });
});

describe("a ficha quadrada e a ficha aberta (briefing-tela-2.md, §7; ADR-0092)", () => {
  const base: TicketView = {
    id: "pedido-017",
    number: 17,
    title: "Um relatório da semana no quadro",
    description: "Toda sexta.",
    acceptance: "",
    size: "M",
    state: "a_fazer",
    owner: undefined,
    author: "gerente",
    comment: undefined,
    patch: undefined,
    pr: undefined,
    harness: undefined,
    model: undefined,
  };
  const open = { number: 11, url: "https://github.com/campilho/campsverso/pull/11", state: "aberto", ci: "success" };

  it("mostra o número, o tamanho e o título, e embaixo só os ícones de cada estado", () => {
    expect(squareOf(base)).toEqual({
      number: "#17",
      size: "M",
      title: "Um relatório da semana no quadro",
      label: "Pedido 17: Um relatório da semana no quadro, tamanho médio",
      owner: undefined,
      seal: undefined,
      sealTitle: undefined,
      returned: false,
    });
    // Fazendo, com o rosto do dono.
    expect(squareOf({ ...base, state: "fazendo", owner: "tiago" }).owner).toBe("tiago");
    // Entregue, com o PR: o selo do CI e o texto do PR no `title`.
    const delivered = squareOf({ ...base, state: "entregue", owner: "tiago", pr: open });
    expect([delivered.seal, delivered.sealTitle]).toEqual(["ci_verde", "PR #11 · aberto · CI verde"]);
    // Devolvido: "devolvido" até ser aceito, também no nome que o leitor de tela diz.
    const back = squareOf({ ...base, comment: "Falta o caso vazio." });
    expect(back.returned).toBe(true);
    expect(back.label).toBe("Pedido 17: Um relatório da semana no quadro, tamanho médio, devolvido");
    expect(squareOf({ ...base, state: "aceito", comment: "Falta o caso vazio." }).returned).toBe(false);
  });

  it("conta o que falta da devolução, sempre à vista, até 1.000", () => {
    expect(remainingOf(0, 1000)).toBe("faltam 1.000 de 1.000");
    expect(remainingOf(588, 1000)).toBe("faltam 412 de 1.000");
    expect(remainingOf(999, 1000)).toBe("falta 1 de 1.000");
    expect(remainingOf(1000, 1000)).toBe("faltam 0 de 1.000");
  });

  it("diz quando o pedido foi escrito pelo fato da linha do tempo; sem ele, nada", () => {
    const now = state({ tick: 100_000, day: 3 }); // 09:00 do dia 3, num tick de 2 s
    const created = (tick: number): EnvelopeV1 =>
      ({ type: "campsverso.office.ticket.created.v1", tick, data: { ticket_id: "pedido-017" } }) as unknown as EnvelopeV1;
    expect(writtenOf(now, [created(100_000 - 1800)], "pedido-017")).toBe("escrito no Dia 3 · 08:00");
    expect(writtenOf(now, [created(100_000 - 23 * 1800)], "pedido-017")).toBe("escrito no Dia 2 · 10:00");
    expect(writtenOf(now, [created(100_000 - 1800)], "pedido-018")).toBeUndefined();
    expect(writtenOf(now, [], "pedido-017")).toBeUndefined();
  });
});

describe("a prancheta (§3.6)", () => {
  it("mostra o contador só depois de 80% do limite", () => {
    expect(counterOf(800, 1000)).toBeUndefined();
    expect(counterOf(812, 1000)).toBe("812/1000");
  });

  it("lê o rascunho guardado, e o que vier torto vira o rascunho vazio", () => {
    expect(parseDraft(null)).toEqual(EMPTY_DRAFT);
    expect(EMPTY_DRAFT.size).toBe("M"); // o padrão é M
    expect(parseDraft("{")).toEqual(EMPTY_DRAFT);
    expect(parseDraft(JSON.stringify({ title: "A lousa", description: 3, size: "X" }))).toEqual({ ...EMPTY_DRAFT, title: "A lousa" });
    const draft = { title: "A lousa", description: "Na copa", acceptance: "Entro e vejo", size: "G" };
    expect(parseDraft(JSON.stringify(draft))).toEqual({ ...draft, harness: "", model: "" }); // o rascunho de antes do M26
    const chosen = { ...draft, harness: "claude_code", model: "claude-opus-5-5" };
    expect(parseDraft(JSON.stringify(chosen))).toEqual(chosen);
  });

  it("diz quem programa e o modelo pelos nomes do locale, e o padrão no que não foi escolhido (ADR-0089)", () => {
    setLocale([{ choices: { hands: { api: "harness próprio", claude_code: "Claude Code" }, models: { "claude-opus-5-5": "Opus 5.5" } } }]);
    expect(choicesOf("hands")).toEqual([["api", "harness próprio"], ["claude_code", "Claude Code"]]);
    expect(handsLine(undefined, undefined)).toBeUndefined();
    expect(handsLine("claude_code", "claude-opus-5-5")).toBe("Claude Code · Opus 5.5");
    expect(handsLine(undefined, "claude-opus-5-5")).toBe("o padrão do escritório · Opus 5.5");
    expect(handsLine("api", "claude-haiku-5-5")).toBe("harness próprio · claude-haiku-5-5"); // sem nome, o id
    setLocale([]);
    expect(choicesOf("hands")).toEqual([]);
  });
});

describe("a conversa (§3.5)", () => {
  const room = state({
    entities: {
      camps: { kind: "avatar", display_name: "Camps", position: { x: 4, y: 5 }, attributes: { papel: "dev" } },
      vigia: { kind: "avatar", display_name: "Vigia", position: { x: 2, y: 14 }, attributes: { papel: "vigia" } },
      gerente: { kind: "avatar", display_name: "Gerente", position: { x: 9, y: 14 }, attributes: { papel: "gerente" } },
      faxina: { kind: "avatar", display_name: "Fátima", attributes: { papel: "dev" } }, // fora da sala
      "robo-testador": { kind: "robot", display_name: "Testador", position: { x: 15, y: 4 }, attributes: {} },
    },
    controllers: { camps: { type: "llm" }, vigia: { type: "script" }, gerente: { type: "human" } } as unknown as ObserverState["controllers"],
  });
  const people = peopleOf(room, "gerente");

  it("tem quem está na sala, menos quem joga e menos os robôs, o dev primeiro", () => {
    expect(people.map((p) => [p.id, p.controller])).toEqual([
      ["camps", "LLM"],
      ["vigia", "script"],
    ]);
    expect(peopleLine(people)).toBe("o Camps e o vigia");
    expect(peopleLine(people.slice(0, 1))).toBe("o Camps");
    expect(peopleLine([])).toBe("ninguém na sala");
    expect(people[0] && personTag(people[0])).toBe("o dev · LLM");
  });

  it("a primeira menção de quem está na sala vira o `to`; o gerente e quem está fora, nunca", () => {
    expect(mentionTarget("@Vigia e @Camps, tudo certo?", people)).toBe("vigia");
    expect(mentionTarget("@gerente @camps olha isto", people)).toBe("camps"); // sem diferença de maiúsculas
    expect(mentionTarget("@Fátima vem amanhã?", people)).toBeUndefined();
    expect(mentionTarget("sem menção", people)).toBeUndefined();
  });

  it("sugere pelo começo do nome quando o texto termina em @, e completa a menção", () => {
    expect(mentionQuery("oi @Ca")).toBe("Ca");
    expect(mentionQuery("@")).toBe("");
    expect(mentionQuery("oi @Camps e")).toBeUndefined();
    expect(mentionQuery("email@dominio")).toBeUndefined();
    expect(suggestionsOf("", people).map((p) => p.id)).toEqual(["camps", "vigia"]);
    expect(suggestionsOf("vi", people).map((p) => p.id)).toEqual(["vigia"]);
    const camps = people[0];
    expect(camps && completeMention("oi @ca", camps)).toBe("oi @Camps ");
  });

  it("separa as menções do texto, para a fala as mostrar como pílulas", () => {
    expect(splitMentions("@Camps depois veja o @Vigia.")).toEqual([
      { text: "@Camps", mention: true },
      { text: " depois veja o ", mention: false },
      { text: "@Vigia", mention: true },
      { text: ".", mention: false },
    ]);
    expect(splitMentions("sem nada")).toEqual([{ text: "sem nada", mention: false }]);
  });

  it("monta as falas e as linhas do quadro, do PR e da bancada, na ordem, com a hora", () => {
    const at = (type: string, data: Record<string, unknown>, tick: number, id: string): EnvelopeV1 =>
      ({ id, type, data, tick, visibility: "public" }) as unknown as EnvelopeV1;
    const labels = [
      { event: "campsverso.office.ticket.taken.v1", text: "pegou o pedido {number}" },
      { event: "campsverso.office.ticket.pr_merged.v1", text: "PR #{pull_request} mesclado" },
    ] as unknown as Parameters<typeof linesOf>[3];
    const timeline = [
      at("campsverso.avatar.spoke.v1", { avatar_id: "gerente", text: "@Camps bom dia", action_id: "a1" }, 16200, "e1"),
      at("campsverso.world.entity.moved.v1", { entity_id: "camps" }, 16210, "e2"),
      at("campsverso.office.ticket.taken.v1", { ticket_id: "pedido-001", number: 1, by: "camps" }, 16230, "e3"),
      at("campsverso.workshop.robot_called.v1", { robot_id: "robo-testador", summary: "testes verdes", ok: true }, 16260, "e4"),
      at("campsverso.office.ticket.pr_merged.v1", { ticket_id: "pedido-001", number: 1, pull_request: 7 }, 16290, "e5"),
      at("campsverso.avatar.spoke.v1", { avatar_id: "camps", text: "Anotado.", action_id: "a2" }, 16320, "e6"),
    ];
    expect(linesOf(timeline, room, "gerente", labels)).toEqual([
      { kind: "speech", id: "e1", who: "gerente", name: "Gerente", text: "@Camps bom dia", mine: true, time: "09:00" },
      { kind: "system", id: "e3", text: "Camps pegou o pedido 1", time: "09:01" },
      { kind: "system", id: "e4", text: "o testador passou: testes verdes", time: "09:02" },
      { kind: "system", id: "e5", text: "PR #7 mesclado", time: "09:03" },
      { kind: "speech", id: "e6", who: "camps", name: "Camps", text: "Anotado.", mine: false, time: "09:04" },
    ]);
    expect(linesOf(timeline, room, "gerente", labels, 2).map((l) => l.id)).toEqual(["e5", "e6"]); // só as últimas
    // A luz (ADR-0088): quem acendeu, ou o temporizador do prédio.
    const light = [
      { event: "campsverso.office.light.switched.v1", where: { on: true }, text: "acendeu a luz da sala" },
      { event: "campsverso.office.light.switched.v1", where: { on: false }, text: "apagou a luz da sala" },
    ] as unknown as Parameters<typeof linesOf>[3];
    const switched = [
      at("campsverso.office.light.switched.v1", { switch_id: "interruptor", on: true, by: "gerente" }, 16200, "l1"),
      at("campsverso.office.light.switched.v1", { switch_id: "interruptor", on: false }, 16230, "l2"),
    ];
    expect(linesOf(switched, room, "gerente", light).map((l) => (l.kind === "system" ? l.text : ""))).toEqual([
      "Gerente acendeu a luz da sala",
      "O temporizador apagou a luz da sala",
    ]);
    // A devolução maior (ADR-0092): o v2 conta como o v1 dos dias antigos, com o comentário inteiro.
    const comment = "Falta o caso vazio. ".repeat(50).trim();
    const back = [
      { event: "campsverso.office.ticket.returned.v2", text: "devolveu o pedido {number}: {comment}" },
      { event: "campsverso.office.ticket.returned.v1", text: "devolveu o pedido {number}: {comment}" },
    ] as unknown as Parameters<typeof linesOf>[3];
    const returned = [
      at("campsverso.office.ticket.returned.v1", { ticket_id: "pedido-001", number: 1, by: "gerente", comment: "curto" }, 16200, "r1"),
      at("campsverso.office.ticket.returned.v2", { ticket_id: "pedido-002", number: 2, by: "gerente", comment }, 16230, "r2"),
    ];
    expect(linesOf(returned, room, "gerente", back).map((l) => (l.kind === "system" ? l.text : ""))).toEqual([
      "Gerente devolveu o pedido 1: curto",
      `Gerente devolveu o pedido 2: ${comment}`,
    ]);
  });

  it("conta os marcos da sessão do dev: o começo, os testes e o fim, e não cada passo (ADR-0089)", () => {
    setLocale([{ choices: { hands: { claude_code: "Claude Code" }, models: { "claude-opus-5-5": "Opus 5.5" } } }]);
    const at = (type: string, data: Record<string, unknown>, tick: number, id: string): EnvelopeV1 =>
      ({ id, type, data, tick, visibility: "observer" }) as unknown as EnvelopeV1;
    const who = { avatar_id: "camps", ticket_id: "pedido-002", harness: "claude_code", model: "claude-opus-5-5" };
    const timeline = [
      at("campsverso.workshop.robot_called.v1", { ...who, robot_id: "robo-testador", ok: true, summary: "chamando o robô tools.robos.testador: saída 0" }, 16200, "w1"),
      at("campsverso.workshop.step.v2", { ...who, tool: "Read", summary: "Read: a.py", ok: true }, 16210, "w2"),
      at("campsverso.workshop.step.v2", { ...who, tool: "Edit", summary: "Edit: a.py", ok: true }, 16220, "w3"),
      at("campsverso.workshop.step.v2", { ...who, tool: "Bash", summary: "Bash: python -m pytest -q tests", ok: false }, 16230, "w4"),
      at("campsverso.workshop.session_finished.v1", { ...who, done: true, reason: "pronto", turns: 19, steps: 18, cost_usd: 0.5032, duration_ms: 324000 }, 16290, "w5"),
      at("campsverso.workshop.step.v2", { ...who, tool: "Read", summary: "Read: a.py", ok: true }, 16300, "w6"),
    ];
    expect(linesOf(timeline, room, "gerente", []).map((l) => (l.kind === "system" ? l.text : ""))).toEqual([
      "o testador passou", // a linha da tela do robô não diz nada a quem lê
      "Camps começou a programar o pedido 2: Claude Code (Opus 5.5)",
      "Camps rodou os testes: falharam",
      "Camps terminou a sessão do pedido 2: pronto, 19 voltas, US$ 0,50, 5,4 min",
      "Camps começou a programar o pedido 2: Claude Code (Opus 5.5)", // a devolução abre outra
    ]);
    setLocale([]);
  });
});

describe("a tela do dev (ADR-0089)", () => {
  const session = {
    ticket_id: "pedido-002",
    harness: "claude_code",
    model: "claude-opus-5-5",
    started_tick: 16200,
    count: 23,
    cost_usd: 0.614,
    steps: [
      { tick: 16200, tool: "robô", summary: "briefing passou", ok: true },
      { tick: 16260, tool: "Write", summary: "Write: libs/adapters/src/campsverso_adapters/hands_codex.py", ok: true, path: "libs/adapters/src/campsverso_adapters/hands_codex.py" },
      { tick: 16300, tool: "Bash", summary: "Bash: pytest libs/adapters/tests", ok: false },
    ],
  };
  const working = state({
    entities: {
      camps: { kind: "avatar", display_name: "Camps", position: { x: 4, y: 5 }, attributes: { papel: "dev" } },
      "pedido-002": { kind: "ticket", display_name: "Conector do Codex", attributes: { numero: 2, titulo: "Conector do Codex", estado: "fazendo" } },
    },
    actions: { camps: { action: "work", intent: "o pedido 2" } } as unknown as ObserverState["actions"],
    workshop: { sessions: { camps: session } },
  });

  it("mostra o pedido, as mãos, o andamento e os passos, e no fim o motivo e o custo", () => {
    setLocale([{ choices: { hands: { claude_code: "Claude Code" }, models: { "claude-opus-5-5": "Opus 5.5" } } }]);
    const view = screenView(working, "camps", 16200 + 18 * 60 / 2);
    expect(view).toMatchObject({
      heading: "Tela do Camps",
      title: "Pedido 2 · Conector do Codex",
      hands: "Claude Code · Opus 5.5",
      status: "começou 09:00 · 18 min · 23 passos · US$ 0,61",
      end: undefined,
    });
    expect(view?.lines).toEqual([
      { time: "09:00", text: "robô: briefing passou", ok: true },
      { time: "09:02", text: "Write hands_codex.py", ok: true },
      { time: "09:03", text: "Bash: pytest libs/adapters/tests", ok: false },
    ]);
    const done = state({ ...working, workshop: { sessions: { camps: { ...session, finished: { tick: 16400, done: true, reason: "pronto", turns: 19, steps: 18, cost_usd: 0.5032, duration_ms: 324000 } } } } });
    expect(screenView(done, "camps", 99999)?.end).toBe("terminou: pronto · 19 voltas · US$ 0,50 · 5,4 min");
    expect(screenView(working, "vigia", 16300)).toBeUndefined();
    // A sessão fixa da rotina não publica o fim: a ficha entregue a encerra, e o tempo para.
    const entregue = state({
      ...working,
      entities: { ...working.entities, "pedido-002": { kind: "ticket", display_name: "x", attributes: { numero: 2, titulo: "x", estado: "entregue" } } },
    });
    expect(screenView(entregue, "camps", 99999)).toMatchObject({ end: "fim: o pedido está entregue" });
    expect(screenView(entregue, "camps", 99999)?.status).toContain("começou 09:00 · 3,3 min");
    expect(overHead(entregue, "camps", 16300)?.label ?? "").not.toContain("passo");
    setLocale([]);
  });

  it("o chip do dev com sessão abre a tela, e sobre ele vai o último passo, não a barra", () => {
    const camps = chipsOf(working, "gerente", 16300).find((c) => c.id === "camps");
    expect(camps?.screen).toBe(true);
    expect(chipsOf(state({ entities: working.entities }), "gerente", 16300).find((c) => c.id === "camps")?.screen).toBeUndefined();
    expect(overHead(working, "camps", 16300)).toEqual({ label: "passo 23 · Bash: pytest libs/adapters/tests" });
    const ended = state({ ...working, workshop: { sessions: { camps: { ...session, finished: { tick: 16400, done: true, reason: "pronto", turns: 1, steps: 1, duration_ms: 1 } } } } });
    expect(overHead(ended, "camps", 16410)?.label).not.toContain("passo");
  });
});

describe("as mensagens do sistema (§3.9)", () => {
  const commit = "5485c2e1234567890abcdef1234567890abcdef0";
  const notice = (kind: "troca" | "espera" | "volta", text: string): Notice => ({
    message: { type: "campsverso.realtime.notice.v1", kind, text, commit, pull_requests: [11] },
    at: 1000,
  });
  const base = { running: "89f4167aaaa", notice: undefined, fresh: undefined, last: "10:59", attempt: 0, nextRetryAt: undefined, now: 5000 };

  it("a troca e a queda travam a tela num modal; a espera, a volta e a versão nova só avisam", () => {
    const swap = notice("troca", "O escritório vai trocar.");
    const banner = bannerOf({ status: "closed", everOpen: true, notice: swap, fresh: undefined, now: 2000 });
    expect(systemOf({ ...base, banner, notice: swap })).toEqual({ form: "modal", kind: "troca", from: "89f4167", to: "5485c2e", pullRequests: [11] });
    const fall = bannerOf({ status: "closed", everOpen: true, notice: undefined, fresh: undefined, now: 2000 });
    expect(systemOf({ ...base, banner: fall, attempt: 3, nextRetryAt: 12_100 })).toEqual({ form: "modal", kind: "queda", last: "10:59", attempt: 3, nextIn: 8 });
    const wait = notice("espera", "Há uma versão nova.");
    const waiting = systemOf({ ...base, banner: bannerOf({ status: "open", everOpen: true, notice: wait, fresh: undefined, now: 2000 }), notice: wait });
    expect(waiting).toMatchObject({ form: "aviso", tone: "amarelo", title: "Versão nova na fila", text: "Há uma versão nova." });
    const back = notice("volta", "A versão nova falhou, e o escritório voltou.");
    expect(systemOf({ ...base, banner: bannerOf({ status: "open", everOpen: true, notice: back, fresh: undefined, now: 2000 }), notice: back })).toMatchObject({
      form: "aviso",
      tone: "vermelho",
      title: "O escritório voltou",
    });
    const fresh = { commit, pullRequests: [11, 12], at: 1500 };
    expect(systemOf({ ...base, banner: bannerOf({ status: "open", everOpen: true, notice: undefined, fresh, now: 2000 }), fresh })).toMatchObject({
      form: "aviso",
      tone: "verde",
      title: "Versão nova no ar",
      text: "5485c2e, com os PRs #11 e #12.",
    });
    expect(systemOf({ ...base, banner: undefined })).toBeUndefined();
  });

  it("o aviso novo tem outra chave, para o × fechar só o de agora", () => {
    const wait = notice("espera", "Há uma versão nova.");
    const banner = bannerOf({ status: "open", everOpen: true, notice: wait, fresh: undefined, now: 2000 });
    const first = systemOf({ ...base, banner, notice: wait });
    const second = systemOf({ ...base, banner, notice: { ...wait, at: 9000 } });
    expect(first?.form === "aviso" && second?.form === "aviso" && first.key !== second.key).toBe(true);
  });

  it("diz os PRs por extenso", () => {
    expect(prsText([])).toBe("");
    expect(prsText([7])).toBe("com o PR #7");
    expect(prsText([7, 8, 9])).toBe("com os PRs #7, #8 e #9");
  });
});

describe("a gaveta do operador (§3.8)", () => {
  it("diz a versão que roda e o estado da troca, e sem supervisor, nenhuma versão", () => {
    const build = { commit: "89f4167899ef434436544f05a028f39a51dabc3e" };
    expect(versionLine(build, undefined)).toEqual({ commit: "89f4167", state: "rodando" });
    expect(versionLine(build, { text: "", tone: "info", kind: "espera" }).state).toBe("uma versão nova na fila");
    expect(versionLine(build, { text: "", tone: "info", kind: "troca" }).state).toBe("trocando de versão");
    expect(versionLine(build, { text: "", tone: "warn", kind: "volta" }).state).toBe("voltou de uma troca");
    expect(versionLine(undefined, undefined)).toEqual({ commit: "esta pasta", state: "sem supervisor" });
  });
});
