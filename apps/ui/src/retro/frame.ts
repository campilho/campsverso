/** A moldura retrô do escritório (docs/design/briefing-tela.md, a fase 1 do plano): a barra de
 * cima, o monitor com a sala, a barra de baixo com o relógio, as pessoas e os comandos, e a coluna
 * da direita. A moldura não decide nada: cada botão chama uma ação que vira proposta, como hoje.
 *
 * Ela entra só no escritório. A tela monta a página de sempre e, quando o estado diz que é o
 * escritório, a moldura reorganiza as mesmas peças (o mapa, a fila, o painel do quadro) dentro
 * dela. A fazenda, a arena e o assistir não mudam. */
import type { EnvelopeV1, ObserverState } from "@campsverso/contracts";

import type { ArtManifest } from "../art/manifest.ts";
import { el } from "../dom.ts";
import { summonsOf } from "../panels/office.ts";
import { Portrait } from "../panels/portrait.ts";
import type { Chip, ClockView, Light } from "./model.ts";

export interface FrameActions {
  assume(): void;
  /** Soltar o gerente: ele vai até a porta, e a tela o devolve (o `leave()` de hoje). */
  release(): void;
  write(): void;
  summon(devId: string): void;
  dismiss(devId: string): void;
  help(): void;
  about(): void;
}

export interface FrameInput {
  readonly state: ObserverState;
  /** Os fatos recentes: a convocação do dev que a visão do jogador não vê. */
  readonly timeline: readonly EnvelopeV1[];
  readonly light: Light;
  readonly clock: ClockView;
  readonly live: string;
  readonly chips: readonly Chip[];
  /** O gerente está com quem joga. */
  readonly mine: boolean;
  readonly connected: boolean;
  /** O texto de dica da vez, que vai no `title` do "?". */
  readonly hint: string;
  /** Os botões do relógio do sandbox, feitos só quando a chave muda; nenhum no escritório vivo. */
  readonly clockButtons: () => readonly HTMLElement[];
  readonly clockKey: string;
}

const TELA = "/tela";

function pressed(node: HTMLElement, on: boolean): void {
  node.setAttribute("aria-pressed", on ? "true" : "false");
}

function button(text: string, className: string, onClick: () => void, enabled = true): HTMLButtonElement {
  const node = el("button", { className }, text);
  node.type = "button";
  node.disabled = !enabled;
  node.addEventListener("click", onClick);
  return node;
}

export class RetroFrame {
  readonly top: HTMLElement;
  readonly main: HTMLElement;
  private readonly lightDot: HTMLElement;
  private readonly screen: HTMLElement;
  private readonly footClock: HTMLElement;
  private readonly helpButton: HTMLButtonElement;
  private readonly hour: HTMLElement;
  private readonly day: HTMLElement;
  private readonly liveLine: HTMLElement;
  private readonly people: HTMLElement;
  private readonly commands: HTMLElement;
  private readonly right: HTMLElement;
  private readonly portraits = new Map<string, Portrait>();
  private art: ArtManifest | undefined;
  private mounted = false;
  private shownChips = "";
  private shownCommands = "";
  private shownClock = "";
  private readonly view: "player" | "operator";
  private readonly debug: boolean;
  private readonly actions: FrameActions;

  constructor(view: "player" | "operator", debug: boolean, actions: FrameActions) {
    this.view = view;
    this.debug = debug;
    this.actions = actions;
    const icon = el("img", { className: "retro-icon" });
    icon.src = `${TELA}/icone.png`;
    icon.alt = "";
    const iconButton = button("", "retro-icon-button", () => { this.actions.about(); });
    iconButton.append(icon);
    iconButton.setAttribute("aria-haspopup", "dialog");
    iconButton.setAttribute("aria-label", "Sobre o Campsverso");
    this.lightDot = el("span", { className: "retro-light verde" });
    this.lightDot.setAttribute("role", "img");
    const player = button("Jogador", "", () => { this.go("player"); });
    const operator = button("Operador", "", () => { this.go("operator"); });
    pressed(player, view === "player");
    pressed(operator, view === "operator");
    this.top = el(
      "header",
      { className: "retro-top" },
      iconButton,
      el("span", { className: "retro-name" }, "Campsverso"),
      this.lightDot,
      el("div", { className: "retro-views", title: "A visão do jogador ou a do operador" }, player, operator),
    );

    this.screen = el("div", { className: "retro-screen" });
    this.helpButton = button("?", "retro-help", () => { this.actions.help(); });
    this.helpButton.setAttribute("aria-label", "Os comandos");
    this.footClock = el("div", { className: "retro-foot-clock" });
    const monitor = el(
      "section",
      { className: "retro-monitor" },
      this.screen,
      el(
        "div",
        { className: "retro-monitor-foot" },
        el("span", { className: "retro-brand" }, "CAMPSVERSO"),
        el("span", { className: "retro-slots" }, el("i"), el("i"), el("i"), el("i"), el("i")),
        this.footClock,
        this.helpButton,
        el("span", { className: "retro-onair" }, el("i", { className: "dot" }), "ao vivo"),
      ),
    );

    this.hour = el("div", { className: "retro-hour" });
    this.day = el("div", { className: "retro-day" });
    this.liveLine = el("div", { className: "retro-live" });
    this.people = el("ul", { className: "retro-people" });
    this.people.setAttribute("aria-label", "Quem está no escritório");
    this.commands = el("div", { className: "retro-commands" });
    const bar = el(
      "section",
      { className: "retro-bar" },
      el("div", { className: "retro-clock" }, this.hour, this.day, this.liveLine),
      this.people,
      this.commands,
    );

    this.right = el("div", { className: "retro-right" });
    this.main = el("main", { className: "retro-main" }, el("div", { className: "retro-left" }, monitor, bar), this.right);
  }

  /** Põe as peças de sempre dentro da moldura: o mapa no monitor, o quadro na coluna da direita. */
  mount(app: HTMLElement, world: HTMLElement, sides: readonly (HTMLElement | false)[]): void {
    if (this.mounted) {
      return;
    }
    this.mounted = true;
    document.body.classList.add("retro");
    this.screen.append(world);
    for (const side of sides) {
      if (side !== false) {
        this.right.append(side);
      }
    }
    app.replaceChildren(this.top, this.main);
  }

  get isMounted(): boolean {
    return this.mounted;
  }

  setArt(art: ArtManifest): void {
    this.art = art;
    for (const [id, picture] of this.portraits) {
      picture.setArt(art, id);
    }
    this.shownChips = "";
  }

  render(input: FrameInput): void {
    this.lightDot.className = `retro-light ${input.light.color}`;
    this.lightDot.setAttribute("aria-label", input.light.label);
    this.lightDot.title = input.light.label;
    this.hour.textContent = input.clock.hour;
    this.day.textContent = input.clock.day;
    const pace = input.clock.pace === undefined ? [] : [el("span", { className: "retro-pace" }, input.clock.pace)];
    const liveKey = `${input.live}|${input.clock.pace ?? ""}|${String(input.connected)}`;
    if (this.liveLine.dataset.key !== liveKey) {
      this.liveLine.dataset.key = liveKey;
      this.liveLine.replaceChildren(
        el("i", { className: `dot ${input.connected ? "" : "off"}` }),
        input.live,
        ...pace,
      );
    }
    this.helpButton.title = input.hint;
    if (input.clockKey !== this.shownClock) {
      this.shownClock = input.clockKey;
      this.footClock.replaceChildren(...input.clockButtons());
    }
    this.renderChips(input.chips);
    this.renderCommands(input);
  }

  private renderChips(chips: readonly Chip[]): void {
    const key = JSON.stringify(chips);
    if (key === this.shownChips) {
      return;
    }
    this.shownChips = key;
    this.people.replaceChildren(...chips.map((chip) => this.chip(chip)));
  }

  private chip(chip: Chip): HTMLElement {
    const item = el("li", { className: `retro-chip${chip.away ? " away" : ""}`, title: chip.title });
    item.append(
      this.face(chip),
      el(
        "div",
        { className: "retro-chip-text" },
        el("div", { className: "retro-chip-name" }, chip.name, el("span", { className: `retro-tag ${chip.tag === "você" ? "you" : chip.tag === "LLM" ? "llm" : ""}` }, chip.tag)),
        el("div", { className: "retro-chip-line" }, this.icon(chip.icon), el("span", {}, chip.line)),
      ),
    );
    return item;
  }

  private face(chip: Chip): HTMLElement {
    if (chip.robot) {
      return this.robotFace(chip.id);
    }
    let picture = this.portraits.get(chip.id);
    if (picture === undefined) {
      picture = new Portrait();
      this.portraits.set(chip.id, picture);
      if (this.art !== undefined) {
        picture.setArt(this.art, chip.id);
      }
    }
    return el("div", { className: "retro-face" }, picture.element);
  }

  private robotFace(id: string): HTMLElement {
    const box = el("div", { className: "retro-face robot" });
    const sheet = this.art?.sheets?.[id.replace(/-/g, "_")];
    if (sheet !== undefined) {
      const image = el("span", { className: "retro-robot" });
      image.style.backgroundImage = `url(${sheet.image})`;
      box.append(image);
    }
    return box;
  }

  /** O ícone de 16 px da ação, ou o dos chips ("fora", "vigiar"): a folha `icones` pelo mapa de
   * ações do `art.json`, ou pelo nome. */
  private icon(name: string | undefined): HTMLElement {
    const span = el("span", { className: "retro-ic" });
    const icons = this.art?.bubbles?.icons;
    const frame = name === undefined || icons === undefined ? undefined : (icons.frames[icons.actions?.[name] ?? name]);
    const sheet = icons === undefined ? undefined : this.art?.sheets?.[icons.sheet];
    if (frame === undefined || sheet === undefined) {
      span.classList.add("empty");
      return span;
    }
    span.style.backgroundImage = `url(${sheet.image})`;
    span.style.backgroundPosition = `-${String(frame[0] * 16)}px -${String(frame[1] * 16)}px`;
    return span;
  }

  private renderCommands(input: FrameInput): void {
    const [dev] = summonsOf(input.state, input.timeline);
    const summon = input.mine && dev !== undefined && (dev.summoned || !dev.present) ? dev : undefined;
    const key = JSON.stringify([input.mine, input.connected, summon?.id, summon?.summoned, summon?.name]);
    if (key === this.shownCommands) {
      return; // refazer o botão sem mudança engoliria cliques
    }
    this.shownCommands = key;
    const take = input.mine
      ? button("Soltar o gerente", "retro-take release", () => { this.actions.release(); }, input.connected)
      : button("Assumir o gerente", "retro-take", () => { this.actions.assume(); }, input.connected);
    pressed(take, input.mine);
    const write = button("Escrever pedido", "retro-small", () => { this.actions.write(); }, input.mine && input.connected);
    const parts: HTMLElement[] = [take, write];
    if (summon !== undefined) {
      parts.push(
        summon.summoned
          ? button(`Dispensar o ${summon.name}`, "retro-small", () => { this.actions.dismiss(summon.id); }, input.connected)
          : button(`Convocar o ${summon.name}`, "retro-small", () => { this.actions.summon(summon.id); }, input.connected),
      );
    }
    this.commands.replaceChildren(...parts);
  }

  private go(target: "player" | "operator"): void {
    if (target === this.view) {
      return;
    }
    location.search = `?view=${target}${this.debug ? "&render=debug" : ""}`;
  }
}
