/** O que a UI sabe do mundo: o estado do gateway, a linha do tempo e a conexão (ADR-0050).
 *
 * Só guarda o que chega pelo contrato `realtime`. Nada aqui aplica regra de jogo (escopo §9).
 */
import type {
  EnvelopeV1,
  ObserverState,
  RealtimeReplyV1,
  RealtimeUpdateV1,
  RealtimeWelcomeV1,
} from "@campsverso/contracts";

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
  private readonly listeners = new Set<() => void>();

  onChange(listener: () => void): void {
    this.listeners.add(listener);
  }

  private changed(): void {
    for (const listener of this.listeners) {
      listener();
    }
  }

  setStatus(status: Status): void {
    this.status = status;
    this.changed();
  }

  applyWelcome(message: RealtimeWelcomeV1): void {
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
    }
    this.changed();
  }

  applyReply(message: RealtimeReplyV1): void {
    this.lastReply = message;
    this.changed();
  }
}
