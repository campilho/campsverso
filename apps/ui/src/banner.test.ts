/** A faixa do escritório vivo (a parte 5 do M25): a troca, a queda, a versão nova, a espera e a
 * volta, e a loja que guarda o aviso e a versão nova do welcome. */
import type { RealtimeNoticeV1, RealtimeWelcomeV1 } from "@campsverso/contracts";
import { describe, expect, it } from "vitest";

import { BACK_MS, FRESH_MS, SWAP_MS, bannerOf, type BannerInput } from "./banner.ts";
import { Store } from "./store.ts";

const NEW = "8".repeat(40);
const OLD = "4".repeat(40);
const swap: RealtimeNoticeV1 = {
  type: "campsverso.realtime.notice.v1",
  kind: "troca",
  text: "O escritório vai trocar para a versão 8888888 (PR #2) agora e volta em instantes.",
  commit: NEW,
  pull_requests: [2],
};

function input(overrides: Partial<BannerInput>): BannerInput {
  return { status: "open", everOpen: true, notice: undefined, fresh: undefined, now: 1_000_000, ...overrides };
}

function welcome(commit: string, notice?: RealtimeNoticeV1): RealtimeWelcomeV1 {
  return {
    type: "campsverso.realtime.welcome.v1",
    worldid: "office-campsverso-01",
    view: "player",
    avatar_id: "gerente",
    build: { commit, date: "2026-11-21T10:00:00-03:00" },
    ...(notice === undefined ? {} : { notice }),
    commands: [],
    events: [],
    state: {} as RealtimeWelcomeV1["state"],
  };
}

describe("a faixa", () => {
  it("não aparece na primeira carga nem sem aviso", () => {
    expect(bannerOf(input({ status: "connecting", everOpen: false }))).toBeUndefined();
    expect(bannerOf(input({}))).toBeUndefined();
  });

  it("diz a troca antes, durante a queda e some quando o aviso fica velho", () => {
    const notice = { message: swap, at: 1_000_000 };
    expect(bannerOf(input({ notice }))?.text).toBe(swap.text);
    expect(bannerOf(input({ notice, status: "closed" }))).toEqual({
      text: "Trocando de versão… o escritório volta em instantes.",
      tone: "info",
    });
    const late = 1_000_000 + SWAP_MS + 1;
    expect(bannerOf(input({ notice, status: "closed", now: late }))?.text).toBe("Conexão perdida; tentando de novo…");
  });

  it("diz a versão nova por alguns segundos e a volta como alerta", () => {
    const fresh = { commit: NEW, pullRequests: [2], at: 1_000_000 };
    expect(bannerOf(input({ fresh }))?.text).toBe("Versão nova no ar: 8888888 (PR #2).");
    expect(bannerOf(input({ fresh, now: 1_000_000 + FRESH_MS }))).toBeUndefined();
    const back = { message: { ...swap, kind: "volta" as const, text: "A versão falhou." }, at: 1_000_000 };
    expect(bannerOf(input({ notice: back }))).toEqual({ text: "A versão falhou.", tone: "warn" });
    expect(bannerOf(input({ notice: back, now: 1_000_000 + BACK_MS }))).toBeUndefined();
  });
});

describe("a loja do aviso", () => {
  it("guarda o aviso, e o welcome da versão nova o troca pela versão nova com os PRs", () => {
    let now = 1_000;
    const store = new Store(() => now);
    store.applyWelcome(welcome(OLD));
    expect(store.fresh).toBeUndefined();
    store.applyNotice(swap);
    expect(store.notice?.message.kind).toBe("troca");
    now = 9_000;
    store.applyWelcome(welcome(NEW));
    expect(store.fresh).toEqual({ commit: NEW, pullRequests: [2], at: 9_000 });
    expect(store.notice).toBeUndefined();
  });

  it("a tela que reconecta no meio da troca recebe o aviso no welcome", () => {
    const store = new Store(() => 5);
    store.applyWelcome(welcome(OLD, swap));
    expect(store.notice).toEqual({ message: swap, at: 5 });
    store.setStatus("open");
    expect(store.everOpen).toBe(true);
  });
});
