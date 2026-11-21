/** A faixa do escritório vivo (a parte 5 do M25): a troca de versão que vem, a que espera o dev, a
 * volta, a conexão que caiu e a versão nova que subiu.
 *
 * O supervisor avisa pelo gateway (`realtime/notice.v1`) antes de parar a pilha; quando a conexão
 * cai logo depois, a tela sabe que é a troca, e não uma queda. Na volta, o welcome traz a versão
 * nova, e a faixa a diz por alguns segundos. Nada aqui decide coisa do mundo.
 */
import type { RealtimeNoticeV1 } from "@campsverso/contracts";

/** Quanto tempo cada aviso vale na faixa, em ms. */
export const SWAP_MS = 3 * 60_000; // a troca: até a tela voltar, com folga
export const WAIT_MS = 35 * 60_000; // a espera pelo dev, que tem um limite de 30 minutos
export const BACK_MS = 60_000; // a volta
export const FRESH_MS = 12_000; // a versão nova, depois de reconectar

export interface Notice {
  readonly message: RealtimeNoticeV1;
  readonly at: number;
}

export interface Fresh {
  readonly commit: string;
  readonly pullRequests: readonly number[];
  readonly at: number;
}

export interface BannerInput {
  readonly status: "connecting" | "open" | "closed";
  /** Já houve uma conexão aberta: a primeira carga da página não é uma queda. */
  readonly everOpen: boolean;
  readonly notice: Notice | undefined;
  readonly fresh: Fresh | undefined;
  readonly now: number;
}

export interface Banner {
  readonly text: string;
  /** info: a troca e a versão nova; warn: a queda e a volta. */
  readonly tone: "info" | "warn";
  /** O que é: a troca, a espera, a volta, a queda ou a versão nova (a tela retrô escolhe a forma). */
  readonly kind: "troca" | "espera" | "volta" | "queda" | "fresh";
}

function version(commit: string, pullRequests: readonly number[]): string {
  const prs = pullRequests.map((n) => `#${String(n)}`).join(", ");
  return commit.slice(0, 7) + (prs === "" ? "" : ` (PR ${prs})`);
}

/** O que a faixa diz agora, ou nada. */
export function bannerOf(input: BannerInput): Banner | undefined {
  const { status, notice, fresh, now } = input;
  const age = notice === undefined ? Number.POSITIVE_INFINITY : now - notice.at;
  if (status !== "open") {
    if (notice?.message.kind === "troca" && age < SWAP_MS) {
      return { text: "Trocando de versão… o escritório volta em instantes.", tone: "info", kind: "troca" };
    }
    return input.everOpen ? { text: "Conexão perdida; tentando de novo…", tone: "warn", kind: "queda" } : undefined;
  }
  if (fresh !== undefined && now - fresh.at < FRESH_MS) {
    return { text: `Versão nova no ar: ${version(fresh.commit, fresh.pullRequests)}.`, tone: "info", kind: "fresh" };
  }
  if (notice?.message.kind === "volta" && age < BACK_MS) {
    return { text: notice.message.text, tone: "warn", kind: "volta" };
  }
  if (notice?.message.kind === "espera" && age < WAIT_MS) {
    return { text: notice.message.text, tone: "info", kind: "espera" };
  }
  if (notice?.message.kind === "troca" && age < SWAP_MS) {
    return { text: notice.message.text, tone: "info", kind: "troca" }; // avisou, e a conexão ainda não caiu
  }
  return undefined;
}
