import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { CONTRACTS_DIR, EventValidator, checkExamples, loadSchemas, readJson, typeInfos } from "../src/contracts.ts";

describe("validador ajv dos contratos", () => {
  it("aceita os válidos e recusa os inválidos com o código esperado", () => {
    expect(checkExamples()).toEqual([]);
  });

  it("conhece os 75 eventos (os da v0.1 e da v0.2, os da Morada do Sol, os 4 das encomendas, a entrada e a saída do avatar, os 3 do contrato de trabalho, a fala, o relógio que alcança o real, os 5 do pedido do escritório, os 2 avisos do orçamento na v2, os tetos mudados e a sessão em milissegundos) e 11 comandos", () => {
    const kinds = typeInfos(loadSchemas()).map((info) => info.kind);
    expect(kinds.filter((kind) => kind === "event")).toHaveLength(75);
    expect(kinds.filter((kind) => kind === "command")).toHaveLength(11);
  });

  it("recusa um evento da regra oculta publicado como world", () => {
    const path = join(CONTRACTS_DIR, "examples", "valid", "campsverso.rules.effect_applied.v1.json");
    const event = { ...readJson(path), visibility: "world" };
    const codes = new EventValidator().validate(event).map((problem) => problem.code);
    expect(codes).toEqual(["visibility_mismatch"]);
  });
});
