# ADR-0013 — Comandos usam o mesmo envelope, com visibilidade `observer`

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0
**Altera:** `contratos-eventos-v0.md` §7 (coluna de visibilidade dos comandos) e exemplo §8.1

## Contexto

O envelope exige `visibility`. Mas o catálogo lista os comandos com visibilidade "—", o exemplo 8.1 usa `agent`, e o assunto NATS dos comandos (`campsverso.<worldid>.cmd.…`) não tem segmento de visibilidade.

## Decisão

- Comandos usam o `envelope.v1` sem alterações.
- Em todo comando, `visibility` é **`observer`**: leem o kernel, a UI do operador e o arquivo; controladores e agentes nunca leem comandos de outros.
- A validação dos contratos garante essa regra para todo tipo `campsverso.cmd.*` (mecanismo definido no M0).
- Como em qualquer evento, `seq` é monotônica por `source`: cada controlador mantém a sua.

## Consequências

- Na v0.2, com vários agentes LLM, um agente não descobre as intenções de outro lendo comandos.
- Permissões NATS: controladores **publicam** em `cmd.…`, mas não **assinam** `cmd.>`.
- O exemplo 8.1 (`visibility: "agent"`) fica desatualizado; os exemplos de `contracts/examples/` seguem esta ADR.
