# ADR-0027 — `avatar_id` nos eventos e comandos do kernel

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0
**Altera:** `contratos-eventos-v0.md` §8.1 e §8.2 (`agentid`)

## Contexto

Os exemplos 8.1 e 8.2 usam `agentid`; a seção 14.1 usa `avatarid`. O kernel lida com o **corpo**. Quem decide por ele pode ser um humano, um script, um replay ou, a partir da v0.2, um agente LLM.

## Decisão

- Todos os eventos e comandos do kernel usam **`avatar_id`** (grafia da ADR-0030).
- `agent_id` fica reservado para a cognição (v0.2): identifica a mente de um controlador LLM, não o corpo.

## Consequências

- O mesmo `avatar_id` atravessa trocas de posse: os eventos do corpo não dependem de quem o controla.
- Os exemplos 8.1 e 8.2 ficam com a grafia antiga; os de `contracts/examples/` seguem esta ADR.
