/** O que a UI sabe do mundo: o estado do gateway, a linha do tempo e a conexão (ADR-0050).
 *
 * Só guarda o que chega pelo contrato `realtime`. Nada aqui aplica regra de jogo (escopo §9).
 */
import type {
  EnvelopeV1,
  ObserverState,
  RealtimeNoticeV1,
  RealtimeReplyV1,
  RealtimeUpdateV1,
  RealtimeWelcomeV1,
} from "@campsverso/contracts";

import type { Fresh, Notice } from "./banner.ts";
import { applyMergePatch } from "./patch.ts";

export const TIMELINE_LIMIT = 1000;

export type Status = "connecting" | "open" | "closed";

export class Store {
  status: Status = "connecting";
  welcome: RealtimeWelcomeV1 | undefined;
  state: ObserverState | undefined;
  /** Quantos welcomes chegaram: cada um recomeça o relógio da tela (simclock.ts). */
  welcomes = 0;
  /** Da mais antiga para a mais nova; só as últimas TIMELINE_LIMIT. */
  timeline: EnvelopeV1[] = [];
  lastReply: RealtimeReplyV1 | undefined;
  /** O último aviso do supervisor (a parte 5 do M25) e quando chegou. */
  notice: Notice | undefined;
  /** A versão nova que subiu numa troca, vista no welcome depois de reconectar. */
  fresh: Fresh | undefined;
  /** Já houve uma conexão aberta: a primeira carga da página não é uma queda. */
  everOpen = false;
  private readonly now: () => number;
  private readonly listeners = new Set<() => void>();
  private readonly eventListeners = new Set<(events: readonly EnvelopeV1[]) => void>();

  constructor(now: () => number = Date.now) {
    this.now = now;
  }

  onChange(listener: () => void): void {
    this.listeners.add(listener);
  }

  /** Os eventos novos de cada update, na ordem (os do welcome são histórico e não entram). */
  onEvents(listener: (events: readonly EnvelopeV1[]) => void): void {
    this.eventListeners.add(listener);
  }

  private changed(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }

  setStatus(status: Status): void {
    this.status = status;
    this.everOpen ||= status === "open";
    this.changed();
  }

  applyNotice(message: RealtimeNoticeV1): void {
    this.notice = { message, at: this.now() };
    this.changed();
  }

  applyWelcome(message: RealtimeWelcomeV1): void {
    const before = this.welcome?.build?.commit;
    const after = message.build?.commit;
    if (message.notice !== undefined && message.notice.text !== this.notice?.message.text) {
      this.notice = { message: message.notice, at: this.now() };
    }
    if (before !== undefined && after !== undefined && before !== after) {
      // A troca terminou: a versão nova, com os PRs que o aviso trouxe, e o aviso da troca sai.
      const told = this.notice?.message.commit === after ? (this.notice.message.pull_requests ?? []) : [];
      this.fresh = { commit: after, pullRequests: told, at: this.now() };
      if (this.notice?.message.kind !== "volta") {
        this.notice = undefined;
      }
    }
    this.welcome = message;
    this.state = message.state;
    this.welcomes += 1;
    this.timeline = message.events.slice(-TIMELINE_LIMIT);
    this.changed();
  }

  applyUpdate(message: RealtimeUpdateV1): void {
    if (this.state === undefined) {
      return; // sem welcome não há sobre o que aplicar; o próximo welcome traz tudo
    }
    this.state = applyMergePatch(this.state, message.patch) as unknown as ObserverState;
    if (message.events.length > 0) {
      this.timeline = [...this.timeline, ...message.events].slice(-TIMELINE_LIMIT);
      for (const listener of this.eventListeners) {
        listener(message.events);
      }
    }
    this.changed();
  }

  applyReply(message: RealtimeReplyV1): void {
    this.lastReply = message;
    this.changed();
  }
}
