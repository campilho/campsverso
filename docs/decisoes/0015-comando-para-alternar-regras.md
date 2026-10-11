# ADR-0015 — Comando `campsverso.cmd.rules.toggle.v1` para alternar regras

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0 (contrato), M1 (kernel)
**Altera:** `contratos-eventos-v0.md` §7 e exemplo §8.3; `kernel-gestao-do-tempo.md` §12 (`rules.hot_applied.v1`)

## Contexto

- A bíblia (§10) diz que a R-001 é alternável a quente.
- O exemplo 8.3 mostra `rules.toggled` publicado por `/ops/rules-admin`. Isso contradiz o princípio de que só o kernel escreve a verdade do mundo, e não existe comando para *pedir* a alternância.
- O documento de tempo cria ainda `campsverso.rules.hot_applied.v1` ("regra ou parâmetro aplicado a quente numa fronteira de tick"), que se sobrepõe a `rules.toggled.v1` ("ligada, desligada ou parametrizada").

## Decisão

1. Novo comando **`campsverso.cmd.rules.toggle.v1`** com a regra, o novo estado (`enabled`), parâmetros opcionais, motivo e, opcionalmente, o id do experimento.
2. O kernel valida, aplica numa fronteira de tick e publica `campsverso.rules.toggled.v1` (internal), com `source` do próprio kernel e o tick efetivo.
3. O estado inicial das regras continua em `rules.yaml` do cartucho (`FlagPort`) e é anunciado por `campsverso.rules.loaded.v1`.
4. **`rules.hot_applied.v1` não será criado**: `rules.toggled.v1` já cobre o caso.
5. Na v0.1, só o operador emite o comando (pela UI do operador ou por uma ferramenta de linha de comando, a definir).

## Consequências

- O exemplo 8.3 passa a ter `source: /kernel/<worldid>`.
- Os experimentos de "tempo até desaprender" ganham um caminho auditável: comando → validação → fato.
