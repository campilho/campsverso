/** As mensagens do sistema da tela retrô (docs/design/briefing-tela.md, §3.9), em funções puras: o
 * `bannerOf` de hoje decide o que vale, e aqui se escolhe a forma. A troca de versão e a conexão
 * que caiu travam a tela num modal; a espera, a volta e a versão nova só avisam, no canto.
 *
 * Os passos do modal da troca são texto fixo: o supervisor só avisa depois de testar a versão nova
 * numa cópia do mundo (ADR-0086), e daí para a frente a tela não sabe em que passo ele está, então
 * não finge progresso. */
import type { Banner, Fresh, Notice } from "../banner.ts";

export type SystemView =
  | {
      readonly form: "modal";
      readonly kind: "troca";
      readonly from: string | undefined;
      readonly to: string | undefined;
      readonly pullRequests: readonly number[];
    }
  | {
      readonly form: "modal";
      readonly kind: "queda";
      /** A hora do mundo na última resposta: "10:59". */
      readonly last: string;
      readonly attempt: number;
      /** Em quantos segundos sai a próxima tentativa, quando a conexão diz. */
      readonly nextIn: number | undefined;
    }
  | {
      readonly form: "aviso";
      readonly kind: "espera" | "volta" | "fresh";
      readonly tone: "amarelo" | "vermelho" | "verde";
      readonly title: string;
      readonly text: string;
      /** Muda a cada aviso novo: o "×" fecha só o de agora. */
      readonly key: string;
    };

export interface SystemInput {
  readonly banner: Banner | undefined;
  /** A versão que roda (o `welcome.build`), antes da troca. */
  readonly running: string | undefined;
  readonly notice: Notice | undefined;
  readonly fresh: Fresh | undefined;
  readonly last: string;
  readonly attempt: number;
  readonly nextRetryAt: number | undefined;
  readonly now: number;
}

function short(commit: string | undefined): string | undefined {
  return commit === undefined || commit === "" ? undefined : commit.slice(0, 7);
}

/** "com o PR #11", "com os PRs #11 e #12", ou nada. */
export function prsText(pullRequests: readonly number[]): string {
  const names = pullRequests.map((n) => `#${String(n)}`);
  if (names.length === 0) {
    return "";
  }
  const last = names.pop() ?? "";
  return names.length === 0 ? `com o PR ${last}` : `com os PRs ${names.join(", ")} e ${last}`;
}

/** O que a tela mostra do sistema agora, ou nada. */
export function systemOf(input: SystemInput): SystemView | undefined {
  const { banner, notice, fresh } = input;
  switch (banner?.kind) {
    case undefined:
      return undefined;
    case "troca":
      return {
        form: "modal",
        kind: "troca",
        from: short(input.running),
        to: short(notice?.message.commit),
        pullRequests: notice?.message.pull_requests ?? [],
      };
    case "queda":
      return {
        form: "modal",
        kind: "queda",
        last: input.last,
        attempt: input.attempt,
        nextIn: input.nextRetryAt === undefined ? undefined : Math.max(0, Math.ceil((input.nextRetryAt - input.now) / 1000)),
      };
    case "espera":
      return { form: "aviso", kind: "espera", tone: "amarelo", title: "Versão nova na fila", text: banner.text, key: `espera:${String(notice?.at ?? 0)}` };
    case "volta":
      return { form: "aviso", kind: "volta", tone: "vermelho", title: "O escritório voltou", text: banner.text, key: `volta:${String(notice?.at ?? 0)}` };
    case "fresh": {
      const version = short(fresh?.commit) ?? "";
      const prs = prsText(fresh?.pullRequests ?? []);
      return {
        form: "aviso",
        kind: "fresh",
        tone: "verde",
        title: "Versão nova no ar",
        text: `${version}${prs === "" ? "" : `, ${prs}`}.`,
        key: `fresh:${String(fresh?.at ?? 0)}`,
      };
    }
  }
}
