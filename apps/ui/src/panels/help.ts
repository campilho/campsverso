/** Os comandos de quem joga (ADR-0068): aparecem sozinhos na primeira vez que o humano assume o
 * Camps, e depois pelo botão "Comandos" ou pela tecla "?". Quem já viu fica guardado no navegador;
 * sem acesso ao armazenamento, a dica aparece de novo, e nada quebra. */
import { button, el } from "../dom.ts";

const SEEN = "campsverso.comandos.v1";

const COMMANDS: readonly (readonly [string, string])[] = [
  ["clique esquerdo", "anda até o tile"],
  ["clique direito", "abre o menu da coisa, da grama ou do Camps"],
  ["shift com o clique", "põe a ação na fila, que o Camps faz em ordem"],
  ["Esc", "esvazia a fila"],
  ["setas ou WASD", "um passo"],
  ["espaço", "volta a seguir o Camps"],
  ["E", "abre o menu do Camps"],
  ["arrastar", "rola o mapa"],
];

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

export class CommandsHelp {
  private readonly root = el("div", { className: "commands" });

  constructor(host: HTMLElement) {
    const rows = COMMANDS.map(([key, what]) => el("li", {}, el("kbd", {}, key), ` ${what}`));
    this.root.append(
      el("strong", {}, "Comandos"),
      el("ul", {}, ...rows),
      button("Entendi", () => { this.hide(); }),
    );
    this.root.hidden = true;
    host.append(this.root);
  }

  show(): void {
    this.root.hidden = false;
  }

  hide(): void {
    this.root.hidden = true;
    remember();
  }

  /** Na primeira vez que o humano assume o Camps. */
  firstTime(): void {
    if (!seen()) {
      this.show();
    }
  }
}
