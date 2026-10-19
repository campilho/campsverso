import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { CONTRACTS_DIR, EventValidator, checkExamples, loadSchemas, readJson, typeInfos } from "../src/contracts.ts";

describe("validador ajv dos contratos", () => {
  it("aceita os válidos e recusa os inválidos com o código esperado", () => {
    expect(checkExamples()).toEqual([]);
  });

  it("conhece os 50 eventos (38 da v0.1, 2 de sono v2, o delta da percepção, 4 de modelo e orçamento e 5 de memória) e 9 comandos", () => {
    const kinds = typeInfos(loadSchemas()).map((info) => info.kind);
    expect(kinds.filter((kind) => kind === "event")).toHaveLength(50);
    expect(kinds.filter((kind) => kind === "command")).toHaveLength(9);
  });

  it("recusa um evento da regra oculta publicado como world", () => {
    const path = join(CONTRACTS_DIR, "examples", "valid", "campsverso.rules.effect_applied.v1.json");
    const event = { ...readJson(path), visibility: "world" };
    const codes = new EventValidator().validate(event).map((problem) => problem.code);
    expect(codes).toEqual(["visibility_mismatch"]);
  });
});
