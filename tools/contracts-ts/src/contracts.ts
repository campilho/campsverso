/**
 * Leitura dos contratos e validação de eventos com ajv (JSON Schema 2020-12).
 *
 * Os códigos de erro são os mesmos do validador Python (tools/contracts), para que os dois
 * validadores concordem sobre cada exemplo (contratos §10).
 */
import { readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

import { Ajv2020 } from "ajv/dist/2020.js";
import type { ErrorObject, ValidateFunction } from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

export const REPO_ROOT = resolve(import.meta.dirname, "../../..");
export const CONTRACTS_DIR = join(REPO_ROOT, "contracts");

export type JsonObject = Record<string, unknown>;

export interface Problem {
  readonly code: string;
  readonly message: string;
}

export interface SchemaFile {
  readonly path: string; // relativo a contracts/
  readonly content: JsonObject;
}

export interface TypeInfo {
  readonly name: string;
  readonly kind: "event" | "command";
  readonly title: string;
  readonly visibility: string;
  readonly producer: string;
  readonly dataschema: string;
}

const SCHEMA_DIRS = ["common", "envelope", "events", "commands"];

export function readJson(path: string): JsonObject {
  return JSON.parse(readFileSync(path, "utf8")) as JsonObject;
}

export function loadSchemas(contractsDir: string = CONTRACTS_DIR): SchemaFile[] {
  const files: SchemaFile[] = [];
  for (const dir of SCHEMA_DIRS) {
    const entries = readdirSync(join(contractsDir, dir), { recursive: true, encoding: "utf8" });
    for (const entry of entries.filter((e) => e.endsWith(".schema.json")).sort()) {
      files.push({ path: `${dir}/${entry}`, content: readJson(join(contractsDir, dir, entry)) });
    }
  }
  return files;
}

export function typeInfos(schemas: SchemaFile[]): TypeInfo[] {
  return schemas
    .filter((s) => typeof s.content["x-type"] === "string")
    .map((s) => ({
      name: String(s.content["x-type"]),
      kind: s.path.startsWith("commands/") ? ("command" as const) : ("event" as const),
      title: String(s.content.title),
      visibility: String(s.content["x-visibility"]),
      producer: String(s.content["x-producer"]),
      dataschema: String(s.content.$id),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

function describe(errors: ErrorObject[] | null | undefined): string[] {
  return (errors ?? [])
    .map((e) => `${e.instancePath === "" ? "(raiz)" : e.instancePath.slice(1)}: ${e.message ?? "inválido"}`)
    .sort();
}

export class EventValidator {
  private readonly envelope: ValidateFunction;
  private readonly payloads = new Map<string, ValidateFunction>();
  private readonly types = new Map<string, TypeInfo>();

  constructor(schemas: SchemaFile[] = loadSchemas()) {
    const ajv = new Ajv2020({ allErrors: true, strict: true, allowUnionTypes: true });
    addFormats(ajv);
    for (const keyword of ["x-type", "x-visibility", "x-producer"]) {
      ajv.addKeyword({ keyword, schemaType: "string" });
    }
    for (const schema of schemas) {
      ajv.addSchema(schema.content);
    }
    this.envelope = ajv.getSchema("contracts://envelope/envelope.v1") ?? fail("envelope ausente");
    for (const info of typeInfos(schemas)) {
      this.types.set(info.name, info);
      this.payloads.set(info.name, ajv.getSchema(info.dataschema) ?? fail(info.dataschema));
    }
  }

  validate(event: JsonObject): Problem[] {
    if (!this.envelope(event)) {
      return describe(this.envelope.errors).map((message) => ({ code: "envelope_schema", message }));
    }
    const type = String(event.type);
    const info = this.types.get(type);
    const payload = this.payloads.get(type);
    if (info === undefined || payload === undefined) {
      return [{ code: "unknown_type", message: `tipo sem schema em contracts/: ${type}` }];
    }
    const problems: Problem[] = [];
    if (event.dataschema !== info.dataschema) {
      problems.push({
        code: "dataschema_mismatch",
        message: `dataschema ${String(event.dataschema)}, esperado ${info.dataschema}`,
      });
    }
    if (event.visibility !== info.visibility) {
      problems.push({
        code: "visibility_mismatch",
        message: `${type} tem visibilidade ${info.visibility}, mas o envelope diz ${String(event.visibility)}`,
      });
    }
    if (!payload(event.data)) {
      problems.push(...describe(payload.errors).map((message) => ({ code: "payload_schema", message })));
    }
    return problems;
  }
}

function fail(what: string): never {
  throw new Error(`schema não carregado: ${what}`);
}

/** Válidos passam e cobrem todos os tipos; cada inválido falha com o código esperado. */
export function checkExamples(contractsDir: string = CONTRACTS_DIR): Problem[] {
  const schemas = loadSchemas(contractsDir);
  const validator = new EventValidator(schemas);
  const problems: Problem[] = [];
  const covered = new Set<string>();

  const validDir = join(contractsDir, "examples", "valid");
  for (const name of readdirSync(validDir).filter((n) => n.endsWith(".json")).sort()) {
    const event = readJson(join(validDir, name));
    const found = validator.validate(event);
    for (const p of found) {
      problems.push({ code: "valid_example_fails", message: `valid/${name}: [${p.code}] ${p.message}` });
    }
    if (found.length === 0) {
      covered.add(String(event.type));
    }
  }
  for (const info of typeInfos(schemas)) {
    if (!covered.has(info.name)) {
      problems.push({ code: "missing_example", message: `${info.name} não tem exemplo em examples/valid/` });
    }
  }

  const invalidDir = join(contractsDir, "examples", "invalid");
  for (const name of readdirSync(invalidDir).filter((n) => n.endsWith(".json")).sort()) {
    const document = readJson(join(invalidDir, name));
    const expected = String(document.expect_error);
    const codes = new Set(validator.validate(document.event as JsonObject).map((p) => p.code));
    if (codes.size === 0) {
      problems.push({ code: "invalid_example_passes", message: `invalid/${name}: deveria falhar (${expected})` });
    } else if (!codes.has(expected)) {
      problems.push({
        code: "invalid_example_wrong_error",
        message: `invalid/${name}: esperado ${expected}, obtido ${[...codes].sort().join(", ")}`,
      });
    }
  }
  return problems;
}
