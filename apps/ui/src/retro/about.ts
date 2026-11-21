/** O Sobre da tela retrô (docs/design/briefing-tela.md, §3.7): uma janela de Mac clássico com o
 * ícone, a versão, o que roda, o mundo, o relógio e a arte; os créditos e o canvas de depuração,
 * que saíram da barra de cima, ficam aqui. */
import { el } from "../dom.ts";

/** A versão da UI: muda a cada versão do projeto. */
export const UI_VERSION = "v0.4 · o escritório que constrói a si mesmo";
export const UI_MILESTONE = "v0.4, em curso · marco M25";

export interface AboutInfo {
  /** O commit curto e a data do que roda (o `welcome.build`), ou nada fora do escritório vivo. */
  readonly running: string | undefined;
  readonly world: string;
  readonly clock: string;
  readonly debug: boolean;
}

/** A moldura de janela da tela retrô: a barra listrada, a caixinha de fechar e o título. */
export function retroWindow(title: string, onClose: () => void, ...content: HTMLElement[]): HTMLElement {
  const close = el("button", { className: "retro-close" });
  close.type = "button";
  close.setAttribute("aria-label", "Fechar");
  close.addEventListener("click", onClose);
  const titleId = `retro-title-${title.replace(/\W+/g, "-").toLowerCase()}`;
  const heading = el("h2", { className: "retro-window-title" }, title);
  heading.id = titleId;
  const box = el(
    "div",
    { className: "retro-window" },
    el("div", { className: "retro-window-bar" }, close, heading),
    el("div", { className: "retro-window-body" }, ...content),
  );
  box.setAttribute("aria-labelledby", titleId);
  return box;
}

export class AboutDialog {
  readonly element: HTMLDialogElement;
  private returnTo: HTMLElement | null = null;
  private readonly credits: () => void;

  constructor(parent: HTMLElement, credits: () => void) {
    this.credits = credits;
    this.element = el("dialog", { className: "retro-dialog" });
    this.element.setAttribute("aria-modal", "true");
    // O teclado anda com o avatar: dentro da janela, ele para aqui.
    this.element.addEventListener("keydown", (event) => { event.stopPropagation(); });
    this.element.addEventListener("close", () => { this.returnTo?.focus(); });
    parent.append(this.element);
  }

  open(info: AboutInfo): void {
    this.returnTo = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const icon = el("img", { className: "retro-about-icon" });
    icon.src = "/tela/icone.png";
    icon.alt = "O ícone do Campsverso: um monitor de tubo com um mundo dentro";
    const row = (term: string, ...value: (Node | string)[]): HTMLElement[] => [el("dt", {}, term), el("dd", {}, ...value)];
    const debugLink = el("a", { className: "retro-button primary" }, info.debug ? "Visual de jogo" : "Canvas de depuração");
    const params = new URLSearchParams(location.search);
    if (info.debug) {
      params.delete("render");
    } else {
      params.set("render", "debug");
    }
    debugLink.href = `?${params.toString()}`;
    const creditsButton = el("button", { className: "retro-button" }, "Créditos");
    creditsButton.type = "button";
    creditsButton.addEventListener("click", () => {
      this.element.close();
      this.credits();
    });
    const window = retroWindow(
      "Sobre o Campsverso",
      () => { this.element.close(); },
      el(
        "div",
        { className: "retro-about" },
        el("div", { className: "retro-about-frame" }, icon),
        el(
          "div",
          {},
          el("div", { className: "retro-about-name" }, "Campsverso"),
          el("div", { className: "retro-about-tag" }, UI_VERSION),
          el(
            "dl",
            { className: "retro-about-list" },
            ...row("Versão", UI_MILESTONE),
            ...row("Rodando", ...(info.running === undefined ? ["esta pasta, sem supervisor"] : [el("i", { className: "dot" }), info.running])),
            ...row("Mundo", info.world),
            ...row("Relógio", info.clock),
            ...row("Arte", "pixel art desenhada em código · 48 cores"),
          ),
        ),
      ),
      el("div", { className: "retro-about-buttons" }, creditsButton, debugLink),
    );
    this.element.replaceChildren(window);
    this.element.setAttribute("aria-labelledby", window.getAttribute("aria-labelledby") ?? "");
    this.element.showModal();
    window.querySelector<HTMLElement>(".retro-close")?.focus();
  }
}
