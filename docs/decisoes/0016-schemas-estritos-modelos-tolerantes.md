# ADR-0016 — Schemas estritos para quem publica, modelos tolerantes para quem consome

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0
**Esclarece:** `contratos-eventos-v0.md` §5.2 (`additionalProperties: false`) × §9 (leitor tolerante)

## Contexto

O schema do envelope proíbe campos extras (`additionalProperties: false`). Já a seção 9 permite adicionar campos opcionais dentro da mesma versão maior e pede que consumidores ignorem campos desconhecidos. Se um consumidor validasse estritamente com um schema antigo, um campo novo quebraria a leitura.

## Decisão

- **Schemas** (envelope e payloads) mantêm `additionalProperties: false`. O **produtor** é validado contra eles em desenvolvimento e nos testes, o que pega erro de digitação e campo não declarado.
- **Modelos gerados para consumo** ignoram campos desconhecidos (Pydantic com `extra="ignore"`; no TypeScript, leitura sem rejeitar campos extras).
- Consumidores não validam estritamente o que recebem; usam os modelos tolerantes.

## Consequências

- Acrescentar campo opcional = atualizar schema e exemplos, regerar os pacotes e registrar no `CHANGELOG.md`. Consumidores antigos seguem funcionando.
- Eventos antigos do arquivo continuam válidos diante dos schemas novos, que são um superconjunto dentro da mesma versão maior.
