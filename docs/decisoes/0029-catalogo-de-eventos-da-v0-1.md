# ADR-0029 — Catálogo de eventos da v0.1

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0
**Altera:** `contratos-eventos-v0.md` §7 e §14; `kernel-gestao-do-tempo.md` §12 e §13

## Contexto

Os eventos e comandos da v0.1 estavam espalhados em três documentos, a maioria só com nome e descrição.

## Decisão

- **[`catalogo-eventos-v0.1.md`](../arquitetura/catalogo-eventos-v0.1.md) é a especificação do M0:** 38 eventos e 9 comandos, com os campos de cada um.
- **Itens novos**, que os documentos não previam:
  - `world.clock.stepped.v1`;
  - `world.command.rejected.v1`;
  - motivos `session_started` e `possessed` em `avatar.decision_requested`, que também leva `needs` e `position`;
  - `at_tick` opcional em `cmd.action.propose`;
  - motivo `buyer_collect` em `item.consumed`.
- **Itens removidos:** cinco eventos do cartucho `farm` que só repetiam mudanças de estado já cobertas por eventos genéricos (ADR-0025).
- **Fora da v0.1:** os tipos do catálogo geral listados na seção 4 do catálogo.
- O conjunto pode crescer ou encolher; cada mudança atualiza o catálogo, os schemas e o `contracts/CHANGELOG.md`.

## Consequências

Depois do M0, os schemas em `contracts/` passam a ser a fonte da verdade, e o catálogo vira o guia de leitura deles.
