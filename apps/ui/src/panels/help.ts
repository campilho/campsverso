/** Os comandos de quem joga (ADR-0068): aparecem sozinhos na primeira vez que o humano assume o
 * avatar, e depois pelo botão "Comandos", pelo "?" do monitor ou pela tecla "?". Quem já viu fica
 * guardado no navegador; sem acesso ao armazenamento, a dica aparece de novo, e nada quebra.
 *
 * Só aparece o que vale neste mundo e nesta tela (briefing-tela-4.md, §3): "da grama", só na
 * fazenda; arrastar e o espaço, só quando o mapa é maior que a tela; o P, só quando a tela pode
 * pausar (o sandbox). No escritório (`body.retro`), uma janela retrô com o mouse e as teclas
 * desenhados, sobre a tela escurecida; nas fazendas, a lista de sempre, sobre o mapa. */
import { button, el } from "../dom.ts";
import { retroWindow } from "../retro/about.ts";

const SEEN = "campsverso.comandos.v1";

/** O que decide quais comandos valem agora. */
export interface CommandsContext {
  /** Um mundo de fazenda, com a grama: o clique direito também abre o menu dela. */
  readonly farm: boolean;
  /** O mapa é maior que a tela: arrastar rola, e o espaço volta a seguir o avatar. */
  readonly scrolls: boolean;
  /** A tela pode pausar o relógio (o sandbox). */
  readonly pausable: boolean;
}

export type Gesture = "clique" | "direito" | "arrastar";

export interface MouseCommand {
  readonly gesture: Gesture;
  /** O shift junto com o clique. */
  readonly shift: boolean;
  readonly text: string;
}

export interface KeyCommand {
  /** As teclas; "setas" desenha as quatro em T invertido. */
  readonly keys: readonly string[];
  readonly text: string;
}

/** Os comandos que valem neste mundo e nesta tela. */
export function commandsFor(context: CommandsContext): { readonly mouse: readonly MouseCommand[]; readonly keys: readonly KeyCommand[] } {
  const mouse: MouseCommand[] = [
    { gesture: "clique", shift: false, text: "anda até o lugar" },
    {
      gesture: "direito",
      shift: false,
      text: context.farm ? "abre o menu da coisa, da grama; no seu avatar, o seu menu" : "abre o menu da coisa; no seu avatar, o seu menu",
    },
    { gesture: "clique", shift: true, text: "põe a ação na fila: o avatar faz em ordem" },
  ];
  if (context.scrolls) {
    mouse.push({ gesture: "arrastar", shift: false, text: "rola o mapa" });
  }
  const keys: KeyCommand[] = [
    { keys: ["setas"], text: "anda enquanto segura; soltar para. W A S D também" },
    { keys: ["E"], text: "abre o menu do seu avatar" },
    { keys: ["Esc"], text: "esvazia a fila e fecha o que estiver aberto" },
  ];
  if (context.scrolls) {
    keys.push({ keys: ["espaço"], text: "volta a seguir o avatar" });
  }
  if (context.pausable) {
    keys.push({ keys: ["P"], text: "pausa e retoma o relógio" });
  }
  keys.push({ keys: ["?"], text: "abre esta janela" });
  return { mouse, keys };
}

/** O nome do gesto na lista de sempre (as fazendas). */
function plainGesture(command: MouseCommand): string {
  if (command.shift) {
    return "shift com o clique";
  }
  return command.gesture === "clique" ? "clique esquerdo" : command.gesture === "direito" ? "clique direito" : "arrastar";
}

function seen(): boolean {
  try {
    return localStorage.getItem(SEEN) === "1";
  } catch {
    return false;
  }
}

function remember(): void {
  try {
    localStorage.setItem(SEEN, "1");
  } catch {
    // sem armazenamento, a dica volta na próxima vez
  }
}

/** O mouse desenhado, de 20 x 28, com o botão da vez em amarelo. */
function mouseDrawing(gesture: Gesture): HTMLElement {
  const node = el("span", { className: `retro-mouse ${gesture}` }, el("i", { className: "left" }), el("i", { className: "right" }));
  node.setAttribute("aria-hidden", "true");
  return node;
}

function keyCap(key: string): HTMLElement {
  return el("kbd", { className: "retro-key" }, key);
}

/** As quatro setas em T invertido. */
function arrowKeys(): HTMLElement {
  const node = el("span", { className: "retro-arrows" }, keyCap("↑"), el("span", {}, keyCap("←"), keyCap("↓"), keyCap("→")));
  node.setAttribute("aria-label", "as setas");
  return node;
}

export class CommandsHelp {
  private readonly root = el("div", { className: "commands" });
  private readonly dialog = el("dialog", { className: "retro-dialog retro-commands-dialog" });
  private readonly context: () => CommandsContext;
  private shown = "";

  constructor(host: HTMLElement, context: () => CommandsContext) {
    this.context = context;
    this.root.hidden = true;
    host.append(this.root);
    this.dialog.setAttribute("aria-modal", "true");
    // O teclado anda com o avatar: com a janela aberta, ele para aqui.
    this.dialog.addEventListener("keydown", (event) => { event.stopPropagation(); });
    this.dialog.addEventListener("close", () => { remember(); });
    document.body.append(this.dialog);
  }

  show(): void {
    if (document.body.classList.contains("retro")) {
      this.showRetro();
      return;
    }
    this.renderPlain();
    this.root.hidden = false;
  }

  hide(): void {
    this.root.hidden = true;
    if (this.dialog.open) {
      this.dialog.close();
    }
    remember();
  }

  /** Na primeira vez que o humano assume o avatar. */
  firstTime(): void {
    if (!seen()) {
      this.show();
    }
  }

  private renderPlain(): void {
    const { mouse, keys } = commandsFor(this.context());
    const key = JSON.stringify([mouse, keys]);
    if (key === this.shown) {
      return;
    }
    this.shown = key;
    const rows = [
      ...mouse.map((command) => el("li", {}, el("kbd", {}, plainGesture(command)), ` ${command.text}`)),
      ...keys.map((command) => el("li", {}, el("kbd", {}, command.keys[0] === "setas" ? "setas ou WASD" : command.keys.join(" ")), ` ${command.text}`)),
    ];
    this.root.replaceChildren(el("strong", {}, "Comandos"), el("ul", {}, ...rows), button("Entendi", () => { this.hide(); }));
  }

  /** A janela "Comandos" do escritório (briefing-tela-4.md, §3): o mouse e o teclado em duas
   * colunas, e o "Entendi" que guarda o já-visto. */
  private showRetro(): void {
    const { mouse, keys } = commandsFor(this.context());
    const mouseRows = mouse.map((command) =>
      el(
        "li",
        {},
        el(
          "span",
          { className: "retro-commands-how" },
          ...(command.shift ? [keyCap("shift"), el("span", { className: "retro-plus" }, "+")] : []),
          mouseDrawing(command.gesture),
          command.shift ? "" : el("span", { className: "retro-gesture" }, command.gesture),
        ),
        el("span", { className: "retro-commands-what" }, command.text),
      ),
    );
    const keyRows = keys.map((command) =>
      el(
        "li",
        {},
        el("span", { className: "retro-commands-how" }, ...(command.keys[0] === "setas" ? [arrowKeys()] : command.keys.map(keyCap))),
        el("span", { className: "retro-commands-what" }, command.text),
      ),
    );
    const done = el("button", { className: "retro-take retro-entendi" }, "Entendi");
    done.type = "button";
    done.addEventListener("click", () => { this.hide(); });
    const window = retroWindow(
      "Comandos",
      () => { this.hide(); },
      el(
        "div",
        { className: "retro-commands-columns" },
        el("section", {}, el("h3", {}, "Mouse"), el("ul", {}, ...mouseRows)),
        el("section", {}, el("h3", {}, "Teclado"), el("ul", {}, ...keyRows)),
      ),
      el(
        "div",
        { className: "retro-commands-foot" },
        el("span", {}, "Aparece sozinha na primeira vez que você assume; depois, pelo ", el("b", {}, "?"), " do monitor."),
        done,
      ),
    );
    window.classList.add("retro-commands-window");
    this.dialog.replaceChildren(window);
    this.dialog.setAttribute("aria-labelledby", window.getAttribute("aria-labelledby") ?? "");
    if (!this.dialog.open) {
      this.dialog.showModal();
    }
    done.focus();
  }
}
