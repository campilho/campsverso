/** Valida os exemplos com ajv e o contracts/asyncapi.yaml com o parser oficial do AsyncAPI. */
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { Parser } from "@asyncapi/parser";

import { CONTRACTS_DIR, checkExamples } from "./contracts.ts";

// DiagnosticSeverity.Error vale 0. O parser e o Spectral trazem cópias diferentes do enum
// (@stoplight/types), então a comparação é pelo valor numérico.
const isError = (severity: number): boolean => severity === 0;

async function main(): Promise<number> {
  const problems = checkExamples();
  if (problems.length > 0) {
    console.error(`exemplos (ajv): ${String(problems.length)} problema(s)`);
    for (const p of problems) {
      console.error(`  [${p.code}] ${p.message}`);
    }
    return 1;
  }
  const valid = readdirSync(join(CONTRACTS_DIR, "examples", "valid")).length;
  const invalid = readdirSync(join(CONTRACTS_DIR, "examples", "invalid")).length;
  console.log(`exemplos ok (ajv): ${String(valid)} válidos, ${String(invalid)} inválidos recusados`);

  const document = readFileSync(join(CONTRACTS_DIR, "asyncapi.yaml"), "utf8");
  const diagnostics = await new Parser().validate(document);
  const errors = diagnostics.filter((d) => isError(d.severity));
  if (errors.length > 0) {
    console.error(`asyncapi.yaml: ${String(errors.length)} erro(s)`);
    for (const d of errors) {
      console.error(`  ${d.path.join(".")}: ${d.message}`);
    }
    return 1;
  }
  console.log(`asyncapi.yaml ok (${String(diagnostics.length)} aviso(s) de estilo)`);
  return 0;
}

process.exitCode = await main();
