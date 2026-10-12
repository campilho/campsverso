/** O WebSocket com o gateway: reconecta sozinho e manda comandos (contracts/realtime, ADR-0050). */
import type { RealtimeCommandV1, RealtimeReplyV1, RealtimeUpdateV1, RealtimeWelcomeV1 } from "@campsverso/contracts";

import type { Store } from "./store.ts";

type Incoming = RealtimeWelcomeV1 | RealtimeUpdateV1 | RealtimeReplyV1;
export type View = RealtimeWelcomeV1["view"];

const RETRY_MS = [500, 1000, 2000, 5000];

export class Connection {
  private socket: WebSocket | undefined;
  private attempts = 0;
  private nextRequest = 1;
  private readonly url: string;
  private readonly store: Store;

  constructor(url: string, store: Store) {
    this.url = url;
    this.store = store;
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
      window.setTimeout(() => {
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
