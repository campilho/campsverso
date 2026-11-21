/** O WebSocket com o gateway: reconecta sozinho e manda comandos (contracts/realtime, ADR-0050). */
import type {
  RealtimeCommandV1,
  RealtimeNoticeV1,
  RealtimeReplyV1,
  RealtimeUpdateV1,
  RealtimeWelcomeV1,
} from "@campsverso/contracts";

import type { Store } from "./store.ts";

type Incoming = RealtimeWelcomeV1 | RealtimeUpdateV1 | RealtimeReplyV1 | RealtimeNoticeV1;
export type View = RealtimeWelcomeV1["view"];

const RETRY_MS = [500, 1000, 2000, 5000];

export class Connection {
  private socket: WebSocket | undefined;
  private attempts = 0;
  private retry: number | undefined;
  /** Quando a próxima tentativa sai (ms de `Date.now()`), enquanto a conexão está fechada. */
  nextRetryAt: number | undefined;
  private nextRequest = 1;
  private readonly url: string;
  private readonly store: Store;

  constructor(url: string, store: Store) {
    this.url = url;
    this.store = store;
  }

  /** Quantas tentativas já falharam desde a última conexão aberta. */
  get attempt(): number {
    return this.attempts;
  }

  /** O "Tentar agora" da tela: sem esperar a próxima tentativa. */
  retryNow(): void {
    if (this.retry === undefined) {
      return; // aberta, ou já tentando
    }
    window.clearTimeout(this.retry);
    this.retry = undefined;
    this.nextRetryAt = undefined;
    this.open();
  }

  open(): void {
    this.store.setStatus("connecting");
    const socket = new WebSocket(this.url);
    this.socket = socket;
    socket.addEventListener("open", () => {
      this.attempts = 0;
      this.store.setStatus("open");
    });
    socket.addEventListener("message", (event: MessageEvent<string>) => {
      this.receive(JSON.parse(event.data) as Incoming);
    });
    socket.addEventListener("close", () => {
      this.store.setStatus("closed");
      const delay = RETRY_MS[Math.min(this.attempts, RETRY_MS.length - 1)] ?? 5000;
      this.attempts += 1;
      this.nextRetryAt = Date.now() + delay;
      this.retry = window.setTimeout(() => {
        this.retry = undefined;
        this.nextRetryAt = undefined;
        this.open();
      }, delay);
    });
  }

  private receive(message: Incoming): void {
    switch (message.type) {
      case "campsverso.realtime.welcome.v1":
        this.store.applyWelcome(message);
        break;
      case "campsverso.realtime.update.v1":
        this.store.applyUpdate(message);
        break;
      case "campsverso.realtime.reply.v1":
        this.store.applyReply(message);
        break;
      case "campsverso.realtime.notice.v1":
        this.store.applyNotice(message);
        break;
    }
  }

  /** Pede ao gateway que publique um comando. A resposta do mundo chega como evento. */
  send(command: string, data: Record<string, unknown>): void {
    const message: RealtimeCommandV1 = {
      type: "campsverso.realtime.command.v1",
      request_id: `ui-${String(this.nextRequest++)}`,
      command,
      data,
    };
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }
}
