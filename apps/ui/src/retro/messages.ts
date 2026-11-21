/** As mensagens do sistema na tela retrô (docs/design/briefing-tela.md, §3.9): o modal que trava a
 * tela na troca de versão e na conexão que caiu, e os avisos do canto de cima à direita. A forma
 * sai de `systemOf`; aqui só se desenha. No lugar da faixa de hoje. */
import { el } from "../dom.ts";
import { retroWindow } from "./about.ts";
import { prsText, type SystemView } from "./system.ts";

type Step = "feito" | "agora" | "depois";

function stepItems(items: readonly (readonly [Step, string])[]): HTMLElement[] {
  return items.map(([state, text]) => el("li", { className: state }, text));
}

function steps(...items: (readonly [Step, string])[]): HTMLElement {
  return el("ul", { className: "retro-steps" }, ...stepItems(items));
}

/** Os passos da conexão que caiu: a última resposta, a tentativa e a próxima. */
function fallSteps(view: Extract<SystemView, { kind: "queda" }>): (readonly [Step, string])[] {
  const items: (readonly [Step, string])[] = [["feito", `a última resposta veio às ${view.last}`]];
  items.push(["agora", view.attempt > 0 ? `tentando de novo · tentativa ${String(view.attempt)}` : "tentando de novo"]);
  if (view.nextIn !== undefined) {
    items.push(["depois", `a próxima em ${String(view.nextIn)} s`]);
  }
  return items;
}

function monitor(off: boolean): HTMLElement {
  const icon = el("img", { className: `retro-about-icon${off ? " off" : ""}` });
  icon.src = "/tela/icone.png";
  icon.alt = "";
  return el("div", { className: "retro-about-frame" }, icon);
}

export class SystemMessages {
  private readonly modal: HTMLDialogElement;
  private readonly corner: HTMLElement;
  private readonly retry: () => void;
  private shownModal = "";
  private shownSteps = "";
  private readonly fallList = el("ul", { className: "retro-steps" });
  private shownCorner = "";
  /** O aviso que a pessoa fechou no "×": fica fechado até chegar outro. */
  private dismissed = "";

  constructor(parent: HTMLElement, retry: () => void) {
    this.retry = retry;
    this.modal = el("dialog", { className: "retro-dialog retro-system" });
    this.modal.setAttribute("role", "alertdialog");
    this.modal.setAttribute("aria-modal", "true");
    // O modal do sistema não fecha no Esc: ele some quando o escritório volta.
    this.modal.addEventListener("cancel", (event) => { event.preventDefault(); });
    this.modal.addEventListener("keydown", (event) => { event.stopPropagation(); });
    this.corner = el("div", { className: "retro-toasts" });
    parent.append(this.modal, this.corner);
  }

  render(view: SystemView | undefined): void {
    this.renderModal(view?.form === "modal" ? view : undefined);
    this.renderCorner(view?.form === "aviso" ? view : undefined);
  }

  private renderModal(view: Extract<SystemView, { form: "modal" }> | undefined): void {
    // A queda guarda a mesma janela (e o "Tentar agora") enquanto dura; só os passos andam.
    const key = view === undefined ? "" : view.kind === "queda" ? "queda" : JSON.stringify(view);
    if (key !== this.shownModal) {
      this.shownModal = key;
      this.shownSteps = "";
      if (view !== undefined) {
        this.modal.replaceChildren(view.kind === "troca" ? this.swap(view) : this.fall());
        this.modal.setAttribute("aria-labelledby", "retro-system-title");
      }
    }
    if (view?.kind === "queda") {
      const items = fallSteps(view);
      const stepsKey = JSON.stringify(items);
      if (stepsKey !== this.shownSteps) {
        this.shownSteps = stepsKey;
        this.fallList.replaceChildren(...stepItems(items));
      }
    }
    if (view === undefined && this.modal.open) {
      this.modal.close();
    } else if (view !== undefined && !this.modal.open) {
      this.modal.showModal(); // e de novo, se o navegador o fechou à força
    }
  }

  private body(title: string, ...content: HTMLElement[]): HTMLElement {
    const heading = el("h3", { className: "retro-system-title" }, title);
    heading.id = "retro-system-title";
    return el("div", { className: "retro-about" }, ...content.slice(0, 1), el("div", {}, heading, ...content.slice(1)));
  }

  private swap(view: Extract<SystemView, { kind: "troca" }>): HTMLElement {
    const prs = prsText(view.pullRequests);
    const to = view.to === undefined ? "para a versão nova" : `para a ${view.to}`;
    const text = el(
      "p",
      {},
      "Ele está trocando ",
      view.from === undefined ? "" : el("span", {}, "da versão ", el("code", {}, view.from), " "),
      view.to === undefined ? to : el("span", {}, "para a ", el("code", {}, view.to)),
      prs === "" ? "" : `, ${prs}`,
      ". Espere um instante: a tela volta sozinha quando o escritório subir.",
    );
    return retroWindow(
      "Mensagem do sistema",
      () => undefined,
      this.body(
        "O Campsverso está se atualizando",
        monitor(false),
        text,
        el("div", { className: "retro-stripes" }),
        steps(["feito", "testou a versão nova numa cópia do mundo"], ["agora", "trocando de versão"], ["depois", "subindo o escritório de novo"]),
      ),
    );
  }

  private fall(): HTMLElement {
    const again = el("button", { className: "retro-button" }, "Tentar agora");
    again.type = "button";
    again.addEventListener("click", () => { this.retry(); });
    return retroWindow(
      "Mensagem do sistema",
      () => undefined,
      this.body(
        "A conexão caiu",
        monitor(true),
        el("p", {}, "O escritório não responde. A tela tenta de novo sozinha; o mundo continua de onde estava."),
        el("div", { className: "retro-stripes" }),
        this.fallList,
        el("div", { className: "retro-about-buttons" }, again),
      ),
    );
  }

  private renderCorner(view: Extract<SystemView, { form: "aviso" }> | undefined): void {
    const visible = view !== undefined && view.key !== this.dismissed ? view : undefined;
    const key = visible === undefined ? "" : JSON.stringify(visible);
    if (key === this.shownCorner) {
      return;
    }
    this.shownCorner = key;
    if (visible === undefined) {
      this.corner.replaceChildren();
      return;
    }
    const close = el("button", { className: "retro-toast-close" }, "×");
    close.type = "button";
    close.setAttribute("aria-label", "Fechar o aviso");
    close.addEventListener("click", () => {
      this.dismissed = visible.key;
      this.shownCorner = "";
      this.corner.replaceChildren();
    });
    const icon = el("img", { className: "retro-toast-icon" });
    icon.src = "/tela/icone.png";
    icon.alt = "";
    const toast = el(
      "div",
      { className: `retro-toast ${visible.tone}` },
      el("i", { className: "retro-toast-stripe" }),
      icon,
      el("div", { className: "retro-toast-text" }, el("b", {}, visible.title), el("span", {}, visible.text)),
      close,
    );
    toast.setAttribute("role", visible.kind === "volta" ? "alert" : "status");
    this.corner.replaceChildren(toast);
  }
}
