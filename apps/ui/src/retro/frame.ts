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
  /** A câmera do celular: a sala inteira, ou seguindo o gerente (§4). */
  camera(mode: Camera): void;
  /** A tela do dev: a sessão dele na oficina (ADR-0089). */
  screen(devId: string): void;
}

export type Camera = "sala" | "seguir";
type Tab = "quadro" | "conversa" | "pessoas";

/** O celular (§4): abaixo de 760 px, a barra de baixo se desfaz na faixa, nas abas e na barra de ação. */
export const PHONE = "(max-width: 759px)";

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
  /** As contagens das abas do celular: os pedidos e as falas. */
  readonly counts: { readonly tickets: number; readonly talk: number };
  readonly camera: Camera;
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
  private readonly drawer: HTMLElement;
  private readonly drawerBody = el("div", { className: "retro-drawer-body" });
  private readonly portraits = new Map<string, Portrait>();
  private art: ArtManifest | undefined;
  private mounted = false;
  private shownChips = "";
  private shownCommands = "";
  private shownClock = "";
  // As peças do celular (§4): a faixa, as abas, o painel das pessoas e a barra de ação.
  private readonly cameraButtons: Record<Camera, HTMLButtonElement>;
  private readonly stripHour = el("b", { className: "retro-strip-hour" });
  private readonly stripDay = el("span", { className: "retro-strip-day" });
  private readonly stripLive = el("span", { className: "retro-strip-live" });
  private readonly tabs = el("div", { className: "retro-phone-tabs" });
  private readonly tabButtons = new Map<Tab, HTMLButtonElement>();
  private tab: Tab = "quadro";
  private readonly peoplePanel = el("section", { className: "retro-people-panel" });
  private readonly bar: HTMLElement;
  private readonly actionBar = el("div", { className: "retro-actionbar" });
  readonly minimapSlot = el("div", { className: "retro-minimap-slot" });
  private readonly phone = matchMedia(PHONE);
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

    this.screen = el(
      "div",
      { className: "retro-screen" },
      el("span", { className: "retro-follow-tag" }, "seguindo o gerente"),
      this.minimapSlot,
    );
    const sala = button("sala", "", () => { this.actions.camera("sala"); });
    const seguir = button("seguir", "", () => { this.actions.camera("seguir"); });
    this.cameraButtons = { sala, seguir };
    const camera = el("div", { className: "retro-camera" }, sala, seguir);
    camera.setAttribute("aria-label", "A câmera");
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
        camera,
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
    const bar = (this.bar = el(
      "section",
      { className: "retro-bar" },
      el("div", { className: "retro-clock" }, this.hour, this.day, this.liveLine),
      this.people,
      this.commands,
    ));

    const strip = el("div", { className: "retro-strip" }, this.stripHour, this.stripDay, this.stripLive);
    this.tabs.setAttribute("role", "tablist");
    this.tabs.setAttribute("aria-label", "O que mostrar");
    for (const id of ["quadro", "conversa", "pessoas"] as const) {
      const tab = button("", "retro-phone-tab", () => { this.select(id); });
      tab.setAttribute("role", "tab");
      tab.setAttribute("aria-controls", `retro-panel-${id}`);
      this.tabButtons.set(id, tab);
      this.tabs.append(tab);
    }
    this.peoplePanel.id = "retro-panel-pessoas";
    this.peoplePanel.dataset.panel = "pessoas";

    this.right = el("div", { className: "retro-right" });
    // A gaveta do operador (§3.8): cobre a coluna da direita, como a Central de Notificações; o "×"
    // é o mesmo que "Jogador".
    const closeDrawer = button("×", "retro-drawer-close", () => { this.go("player"); });
    closeDrawer.setAttribute("aria-label", "Fechar o painel do operador");
    this.drawer = el("section", { className: "retro-drawer" }, closeDrawer, this.drawerBody);
    this.drawer.setAttribute("aria-label", "Painel do operador");
    this.drawer.setAttribute("aria-hidden", "true");
    this.main = el(
      "main",
      { className: "retro-main" },
      el("div", { className: "retro-left" }, monitor, bar, strip, this.tabs),
      el("div", { className: "retro-rightwrap" }, this.right, this.drawer),
      this.actionBar,
    );
    this.phone.addEventListener("change", () => { this.arrange(); });
  }

  /** No celular, as pessoas vão para a aba delas, e os comandos, para a barra de ação; no
   * computador e no tablet, voltam para a barra de baixo. */
  private arrange(): void {
    if (this.phone.matches) {
      this.peoplePanel.append(this.people);
      this.actionBar.append(this.commands);
    } else {
      this.commands.before(this.people);
      this.bar.append(this.commands);
    }
    this.renderTabs();
  }

  get isPhone(): boolean {
    return this.phone.matches;
  }

  /** O tamanho da tela do monitor em pixels, para o recorte da câmera no celular. */
  screenSize(): { width: number; height: number } {
    return { width: this.screen.clientWidth, height: this.screen.clientHeight };
  }

  private select(tab: Tab): void {
    this.tab = tab;
    this.renderTabs();
  }

  private counts = { tickets: 0, talk: 0 };

  private renderTabs(): void {
    this.right.dataset.tab = this.tab;
    const numbers: Record<Tab, number> = { quadro: this.counts.tickets, conversa: this.counts.talk, pessoas: this.people.children.length };
    const labels: Record<Tab, string> = { quadro: "Quadro", conversa: "Conversa", pessoas: "Pessoas" };
    for (const [id, tab] of this.tabButtons) {
      tab.textContent = `${labels[id]} · ${String(numbers[id])}`;
      tab.setAttribute("aria-selected", id === this.tab ? "true" : "false");
    }
  }

  /** Põe as peças de sempre dentro da moldura: o mapa no monitor, o quadro e a conversa na coluna
   * da direita e, na visão do operador, o painel dele na gaveta, que entra deslizando. */
  mount(app: HTMLElement, world: HTMLElement, sides: readonly HTMLElement[], drawer: HTMLElement | undefined): void {
    if (this.mounted) {
      return;
    }
    this.mounted = true;
    document.body.classList.add("retro");
    this.screen.prepend(world);
    const [board, talk] = sides;
    if (board !== undefined) {
      board.id = "retro-panel-quadro";
      board.dataset.panel = "quadro";
    }
    if (talk !== undefined) {
      talk.id = "retro-panel-conversa";
      talk.dataset.panel = "conversa";
    }
    this.right.append(...sides, this.peoplePanel);
    // Sem o painel do operador (a visão do jogador), a gaveta nem entra no layout: escondida fora da
    // tela, ela alargaria a página no celular.
    this.drawer.hidden = drawer === undefined;
    app.replaceChildren(this.top, this.main);
    this.arrange();
    if (drawer !== undefined) {
      this.drawerBody.append(drawer);
      requestAnimationFrame(() => {
        requestAnimationFrame(() => { this.openDrawer(true); }); // depois do primeiro desenho, para deslizar
      });
    }
  }

  private openDrawer(open: boolean): void {
    this.drawer.classList.toggle("open", open);
    this.drawer.setAttribute("aria-hidden", open ? "false" : "true");
    this.right.inert = open; // o quadro e a conversa ficam atrás do vidro
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
    this.stripHour.textContent = input.clock.hour;
    this.stripDay.textContent = input.clock.day;
    if (this.stripLive.dataset.key !== liveKey) {
      this.stripLive.dataset.key = liveKey;
      this.stripLive.replaceChildren(el("i", { className: `dot ${input.connected ? "" : "off"}` }), input.live, ...(input.clock.pace === undefined ? [] : [el("span", { className: "retro-pace" }, input.clock.pace)]));
    }
    for (const [mode, node] of Object.entries(this.cameraButtons)) {
      pressed(node, mode === input.camera);
    }
    this.screen.classList.toggle("seguindo", input.camera === "seguir");
    if (input.counts.tickets !== this.counts.tickets || input.counts.talk !== this.counts.talk) {
      this.counts = { ...input.counts };
      this.renderTabs();
    }
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
    this.renderTabs(); // "Pessoas · n"
  }

  private chip(chip: Chip): HTMLElement {
    const item = el("li", { className: `retro-chip${chip.away ? " away" : ""}${chip.screen === true ? " has-screen" : ""}`, title: chip.title });
    if (chip.screen === true) {
      // O chip do dev com uma sessão na oficina abre a tela dele (ADR-0089).
      item.tabIndex = 0;
      item.setAttribute("role", "button");
      item.setAttribute("aria-label", `Ver a tela de ${chip.name}: ${chip.line}`);
      const open = (): void => { this.actions.screen(chip.id); };
      item.addEventListener("click", open);
      item.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          event.stopPropagation();
          open();
        }
      });
    }
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
      const who = summon.id === "" ? summon.name : `o ${summon.name}`; // sem o dev na visão, "o dev"
      parts.push(
        summon.summoned
          ? button(`Dispensar ${who}`, "retro-small", () => { this.actions.dismiss(summon.id); }, input.connected)
          : button(`Convocar ${who}`, "retro-small", () => { this.actions.summon(summon.id); }, input.connected),
      );
    }
    this.commands.replaceChildren(...parts);
  }

  private go(target: "player" | "operator"): void {
    if (target === this.view) {
      return;
    }
    const search = `?view=${target}${this.debug ? "&render=debug" : ""}`;
    if (target === "player" && this.drawer.classList.contains("open") && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
      this.openDrawer(false); // a gaveta sai deslizando, e a tela troca de visão depois
      window.setTimeout(() => { location.search = search; }, 350);
      return;
    }
    location.search = search;
  }
}
