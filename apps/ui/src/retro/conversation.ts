/** A conversa da tela retrô (docs/design/briefing-tela.md, §3.5): o cabeçalho com quem está na sala
 * e o aumentar, o registro das falas e dos fatos do quadro, e a linha de escrever, com as menções e
 * as sugestões do `@`. No lugar do cartão "Falar" do painel de hoje.
 *
 * A fala vai como hoje, um `say` do gerente; a primeira menção de quem está na sala vira o `to`, e,
 * sem menção, quem decide para quem vai é a tela de sempre (o dev). O kernel decide se ela vale. */
import { el } from "../dom.ts";
import { SPEECH_MAX } from "../panels/office.ts";
import type { FaceCache } from "./faces.ts";
import {
  completeMention,
  mentionQuery,
  mentionTarget,
  peopleLine,
  personTag,
  splitMentions,
  suggestionsOf,
  type Person,
  type TalkLine,
} from "./talk.ts";

export interface TalkInput {
  /** O gerente está com quem joga, e a conexão está aberta. */
  readonly manager: boolean;
  readonly lines: readonly TalkLine[];
  /** Quem está na sala, menos quem joga: a pilha do cabeçalho e as sugestões. */
  readonly people: readonly Person[];
}

const STACK = 3;

export class RetroTalk {
  readonly element: HTMLElement;
  private readonly faces: FaceCache;
  private readonly send: (text: string, to: string | undefined) => void;
  private readonly stack = el("span", { className: "retro-talk-faces" });
  private readonly who = el("span", { className: "retro-talk-who" });
  private readonly toggle = el("button", { className: "retro-button retro-talk-toggle" });
  private readonly log = el("div", { className: "retro-talk-log" });
  private readonly list = el("ul", { className: "retro-suggest" });
  private readonly field = el("input", { className: "retro-talk-field" });
  private readonly sendButton = el("button", { className: "retro-button retro-talk-send" }, "Enviar");
  private readonly at = el("button", { className: "retro-button retro-talk-at" }, "@");
  private big = false;
  private manager = false;
  private people: readonly Person[] = [];
  private options: Person[] = [];
  private active = 0;
  private shownLog = "";
  private shownHead = "";

  constructor(faces: FaceCache, send: (text: string, to: string | undefined) => void) {
    this.faces = faces;
    this.send = send;
    this.log.setAttribute("role", "log");
    this.log.setAttribute("aria-label", "As falas e os fatos do quadro");
    this.log.tabIndex = 0;
    this.list.id = "retro-suggest";
    this.list.setAttribute("role", "listbox");
    this.list.setAttribute("aria-label", "Chamar quem precisa responder");
    this.list.hidden = true;
    this.field.maxLength = SPEECH_MAX;
    this.field.setAttribute("aria-label", "Falar");
    this.field.setAttribute("aria-autocomplete", "list");
    this.field.setAttribute("aria-controls", this.list.id);
    this.field.setAttribute("aria-expanded", "false");
    this.at.type = "button";
    this.at.setAttribute("aria-label", "Chamar alguém com @");
    this.sendButton.type = "button";
    this.toggle.type = "button";
    this.toggle.addEventListener("click", () => { this.setBig(!this.big); });
    this.at.addEventListener("click", () => {
      const value = this.field.value;
      this.field.value = value === "" || value.endsWith(" ") ? `${value}@` : `${value} @`;
      this.field.focus();
      this.refresh();
    });
    this.sendButton.addEventListener("click", () => { this.submit(); });
    this.field.addEventListener("input", () => { this.refresh(); });
    this.field.addEventListener("blur", () => { this.close(); });
    this.field.addEventListener("keydown", (event) => {
      event.stopPropagation(); // o teclado anda com o avatar: aqui ele escreve
      this.key(event);
    });
    this.element = el(
      "section",
      { className: "retro-talk" },
      el("header", { className: "retro-talk-head" }, el("h2", {}, "Conversa"), this.stack, this.who, this.toggle),
      this.log,
      el("div", { className: "retro-talk-write" }, this.list, this.at, this.field, this.sendButton),
    );
    this.element.setAttribute("aria-label", "Conversa");
    this.setBig(false);
  }

  render(input: TalkInput): void {
    this.people = input.people;
    if (input.manager !== this.manager || this.field.placeholder === "") {
      this.manager = input.manager;
      this.field.disabled = !input.manager;
      this.at.disabled = !input.manager;
      this.field.placeholder = input.manager ? "Escreva @ para chamar quem precisa responder" : "Assuma o gerente para falar";
      if (!input.manager) {
        this.close();
      }
      this.refresh();
    }
    const head = JSON.stringify([input.people, this.faces.version]);
    if (head !== this.shownHead) {
      this.shownHead = head;
      this.stack.replaceChildren(...input.people.slice(0, STACK).map((p) => this.face(p.id, p.name)));
      this.who.textContent = peopleLine(input.people);
    }
    const key = JSON.stringify([input.lines.map((line) => line.id), this.faces.version]);
    if (key !== this.shownLog) {
      const first = this.shownLog === "";
      this.shownLog = key;
      const atEnd = this.log.scrollHeight - this.log.scrollTop - this.log.clientHeight < 24;
      this.log.replaceChildren(...(input.lines.length === 0 ? [el("p", { className: "retro-talk-empty" }, "Ninguém falou ainda.")] : input.lines.map((line) => this.line(line))));
      // Fica no fim, a menos que a pessoa tenha subido para ler.
      if (first || atEnd) {
        this.log.scrollTop = this.log.scrollHeight;
      }
    }
  }

  /** A conversa normal (300 px) ou aumentada (520 px); com ela aumentada, o quadro vira uma fileira. */
  private setBig(big: boolean): void {
    this.big = big;
    this.element.classList.toggle("big", big);
    this.element.parentElement?.classList.toggle("talk-big", big);
    this.toggle.textContent = big ? "⌄ Diminuir" : "⌃ Aumentar";
    this.toggle.setAttribute("aria-label", big ? "Diminuir a conversa" : "Aumentar a conversa");
    this.toggle.setAttribute("aria-pressed", big ? "true" : "false");
  }

  private face(id: string, name: string): HTMLElement {
    const url = this.faces.url(id);
    if (url === undefined) {
      return el("span", { className: "retro-face-small empty" });
    }
    const image = el("img", { className: "retro-face-small" });
    image.src = url;
    image.alt = name;
    return image;
  }

  private line(line: TalkLine): HTMLElement {
    if (line.kind === "system") {
      return el("p", { className: "retro-sys" }, line.time === "" ? line.text : `${line.time} · ${line.text}`);
    }
    const bubble = el(
      "div",
      { className: "retro-bubble" },
      ...splitMentions(line.text).map((part) => (part.mention ? el("span", { className: "retro-mention" }, part.text) : part.text)),
    );
    const meta = el("div", { className: "retro-say-meta" }, line.time === "" ? line.name : `${line.name} · ${line.time}`);
    if (line.mine) {
      return el("div", { className: "retro-say mine" }, el("div", { className: "retro-say-body" }, bubble, meta));
    }
    return el("div", { className: "retro-say" }, this.face(line.who, line.name), el("div", { className: "retro-say-body" }, bubble, meta));
  }

  private submit(): void {
    const text = this.field.value.trim();
    if (text === "" || !this.manager) {
      return;
    }
    this.send(text, mentionTarget(text, this.people));
    this.field.value = "";
    this.refresh();
  }

  private key(event: KeyboardEvent): void {
    const open = !this.list.hidden && this.options.length > 0;
    if (open && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      this.active = (this.active + step + this.options.length) % this.options.length;
      this.paint();
    } else if (open && (event.key === "Enter" || event.key === "Tab")) {
      event.preventDefault();
      this.choose(this.options[this.active]);
    } else if (open && event.key === "Escape") {
      event.preventDefault();
      this.close();
    } else if (event.key === "Enter") {
      event.preventDefault();
      this.submit();
    }
  }

  /** As sugestões, o botão de enviar e o que o leitor de tela anuncia. */
  private refresh(): void {
    this.sendButton.classList.toggle("ready", this.field.value.trim() !== "");
    this.sendButton.disabled = !this.manager;
    const query = this.manager ? mentionQuery(this.field.value) : undefined;
    this.options = query === undefined ? [] : suggestionsOf(query, this.people);
    this.active = Math.min(this.active, Math.max(0, this.options.length - 1));
    this.paint();
  }

  private paint(): void {
    const open = this.options.length > 0;
    this.list.hidden = !open;
    this.field.setAttribute("aria-expanded", open ? "true" : "false");
    if (!open) {
      this.field.removeAttribute("aria-activedescendant");
      this.list.replaceChildren();
      return;
    }
    const items = this.options.map((person, i) => {
      const item = el(
        "li",
        { className: "retro-suggest-item" },
        this.face(person.id, person.name),
        el("span", {}, el("b", {}, `@${person.name}`), el("span", { className: "retro-suggest-tag" }, personTag(person))),
      );
      item.id = `retro-suggest-${person.id}`;
      item.setAttribute("role", "option");
      item.setAttribute("aria-selected", i === this.active ? "true" : "false");
      item.addEventListener("mousedown", (event) => { event.preventDefault(); }); // o foco fica no campo
      item.addEventListener("click", () => { this.choose(person); });
      return item;
    });
    const title = el("li", { className: "retro-suggest-title" }, "Chamar quem precisa responder");
    title.setAttribute("role", "presentation");
    this.list.replaceChildren(title, ...items);
    const current = this.options[this.active];
    if (current !== undefined) {
      this.field.setAttribute("aria-activedescendant", `retro-suggest-${current.id}`);
    }
  }

  private choose(person: Person | undefined): void {
    if (person === undefined) {
      return;
    }
    this.field.value = completeMention(this.field.value, person);
    this.options = [];
    this.paint();
    this.sendButton.classList.toggle("ready", this.field.value.trim() !== "");
  }

  private close(): void {
    this.options = [];
    this.paint();
  }
}
