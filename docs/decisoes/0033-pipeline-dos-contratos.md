# ADR-0033 — Pipeline dos contratos: validação dupla, codegen e compatibilidade

**Status:** aceita; item 4 alterado pela ADR-0034 (o gerador roda no próprio ambiente, no 3.14) · **Data:** 2026-10-11 · **Marco:** M0
**Complementa:** `contratos-eventos-v0.md` §10 (CI mínimo); ADR-0016, ADR-0023, ADR-0029

## Contexto

O CI mínimo da seção 10 dos contratos pede: validar os schemas, validar os exemplos em Python e em TypeScript, regerar os pacotes sem diferenças e checar compatibilidade contra a versão anterior. Ao implementar, surgiram escolhas que os documentos não cobrem.

## Decisão

1. **Fonte da verdade:** os JSON Schemas em `contracts/`.
   - `packages/contracts-py`, `packages/contracts-ts` e **também `contracts/asyncapi.yaml`** são gerados.
   - O AsyncAPI gerado a partir dos schemas nunca diverge deles. Usamos a versão **3.1**, uma versão menor e compatível dentro da linha 3.
2. **Visibilidade fixa por tipo:** cada schema declara `x-visibility`, e o validador recusa um envelope que diga outra coisa. É a primeira linha de defesa da regra oculta, antes das permissões do NATS.
3. **Validação dupla com os mesmos códigos de erro:** Python (`jsonschema`) e TypeScript (`ajv`, modo estrito) usam `envelope_schema`, `unknown_type`, `dataschema_mismatch`, `visibility_mismatch` e `payload_schema`. Cada exemplo inválido declara o código esperado.
4. **Codegen a partir de um pacote único** (`bundle.json`) com todos os tipos em `$defs`:
   - Python: `datamodel-code-generator` 0.83, que **roda isolado no Python 3.14 via `uvx`**, porque ainda quebra sob o 3.15 (ADR-0023). O código gerado roda no 3.15.
   - TypeScript: `json-schema-to-typescript`, com um registro que tipa o envelope pelo campo `type` (união discriminada).
   - O pacote descarta palavras que só servem à validação (`propertyNames`, irmãos de `$ref`), porque atrapalham a geração de tipos. A validação de verdade usa os schemas completos.
5. **Drift:** `make contracts-check` regenera em memória e falha se algum arquivo gerado mudaria.
6. **Compatibilidade** (`make compat`): comparado com um commit base, um schema da mesma versão maior só pode ganhar campos opcionais ou afrouxar restrições.
   - Mudar um enum, inclusive acrescentar valor, conta como incompatível, porque os modelos gerados usam `Literal` e um consumidor antigo recusaria o valor novo.

## Consequências

- Mudar um contrato é: editar o schema e os exemplos, rodar `make contracts`, registrar no `contracts/CHANGELOG.md`. O `make check` pega o resto.
- Gerar os modelos Python exige o `uv` e, na primeira vez, acesso à rede para baixar o gerador.
