# ADR-0021 — Campos ignorados no hash de determinismo

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M3
**Esclarece:** `escopo-v0.1.md` §8, critérios A4 e A5

## Contexto

A4 e A5 comparam o hash do conteúdo dos eventos de duas execuções, "ignorando `id`, `time` e campos de parede". Mas `causationid` e `correlationid` também são UUIDv7, que embutem relógio de parede e bits aleatórios, então mudam a cada execução mesmo quando o mundo é idêntico.

## Decisão

O hash canônico:

- ignora `id`, `time`, `causationid`, `correlationid`, `traceparent` e qualquer campo de payload medido em tempo de parede (latências, por exemplo);
- usa serialização canônica (chaves ordenadas, sem espaços) e SHA-256;
- **inclui** `seq`, `tick`, `simtime`, `source`, `type` e o restante do payload.

## Consequências

- O hash prova que os fatos são iguais, mas não prova que a cadeia de causas é igual.
- **Melhoria possível depois:** em vez de ignorar `causationid`/`correlationid`, substituir cada um pela posição do evento referenciado na execução. Assim a estrutura causal também entra no hash.
