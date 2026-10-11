/**
 * Codegen TypeScript dos contratos: tipos (json-schema-to-typescript) e registro de tipos.
 *
 * Lê packages/contracts-ts/schemas, que o codegen Python (tools/contracts) gera a partir de
 * contracts/. Com --check, nada é escrito: a saída é comparada com o que está no repositório.
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { compile } from "json-schema-to-typescript";
import type { JSONSchema } from "json-schema-to-typescript";

import { REPO_ROOT, loadSchemas, readJson, typeInfos } from "./contracts.ts";

const HEADER = "GERADO por tools/contracts-ts a partir de contracts/: não editar à mão.";
const PACKAGE = join(REPO_ROOT, "packages", "contracts-ts");
const SCHEMAS = join(PACKAGE, "schemas");
const SRC = join(PACKAGE, "src");

/**
 * Remove o que acompanha um $ref (como a descrição do campo). O json-schema-to-typescript
 * criaria um tipo novo para cada combinação (EntityId1, EntityId2…).
 */
function stripRefSiblings(node: unknown): unknown {
  if (Array.isArray(node)) {
    return node.map(stripRefSiblings);
  }
  if (node === null || typeof node !== "object") {
    return node;
  }
  const schema = node as Record<string, unknown>;
  if ("$ref" in schema) {
    return { $ref: schema.$ref };
  }
  return Object.fromEntries(Object.entries(schema).map(([k, v]) => [k, stripRefSiblings(v)]));
}

async function renderTypes(): Promise<string> {
  const bundle = stripRefSiblings(readJson(join(SCHEMAS, "bundle.json"))) as JSONSchema;
  return compile(bundle, "ContractsBundle", {
    bannerComment: `/* ${HEADER} */`,
    unreachableDefinitions: true,
    additionalProperties: false,
    strictIndexSignatures: true,
    declareExternallyReferenced: true,
    format: true,
    style: { printWidth: 100, singleQuote: false, trailingComma: "all" },
  });
}

function renderRegistry(): string {
  const infos = typeInfos(loadSchemas(SCHEMAS));
  const entries = infos
    .map(
      (i) =>
        `  "${i.name}": {\n    kind: "${i.kind}",\n    visibility: "${i.visibility}",\n` +
        `    producer: "${i.producer}",\n    dataschema: "${i.dataschema}",\n  },`,
    )
    .join("\n");
  const payloads = infos.map((i) => `  "${i.name}": T.${i.title};`).join("\n");
  return `/* ${HEADER} */
import type * as T from "./types.ts";

export type Visibility = "world" | "agent" | "observer" | "internal";
export type Kind = "event" | "command";

export interface ContractTypeInfo {
  readonly kind: Kind;
  readonly visibility: Visibility;
  readonly producer: string;
  readonly dataschema: string;
}

export const CONTRACT_TYPES = {
${entries}
} as const satisfies Record<string, ContractTypeInfo>;

export type ContractTypeName = keyof typeof CONTRACT_TYPES;

export interface PayloadByType {
${payloads}
}

/** Envelope com o payload tipado pelo tipo do evento ou comando (união discriminada por \`type\`). */
export type Envelope<K extends ContractTypeName = ContractTypeName> = {
  [P in K]: Omit<T.EnvelopeV1, "type" | "data"> & { readonly type: P; readonly data: PayloadByType[P] };
}[K];
`;
}

const INDEX = `/* ${HEADER} */
export type * from "./types.ts";
export * from "./registry.ts";
`;

async function main(): Promise<number> {
  const check = process.argv.includes("--check");
  const outputs = new Map<string, string>([
    [join(SRC, "types.ts"), await renderTypes()],
    [join(SRC, "registry.ts"), renderRegistry()],
    [join(SRC, "index.ts"), INDEX],
  ]);
  const changed = [...outputs].filter(
    ([path, content]) => !existsSync(path) || readFileSync(path, "utf8") !== content,
  );
  if (check) {
    for (const [path] of changed) {
      console.error(`[codegen_drift] ${path.slice(REPO_ROOT.length + 1)}: difere do codegen (make contracts)`);
    }
    return changed.length > 0 ? 1 : 0;
  }
  for (const [path, content] of changed) {
    writeFileSync(path, content, "utf8");
  }
  console.log(`codegen ts: ${String(changed.length)} arquivo(s) atualizado(s)`);
  return 0;
}

process.exitCode = await main();
