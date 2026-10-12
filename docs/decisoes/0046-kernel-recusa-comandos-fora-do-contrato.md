# ADR-0046 — O kernel recusa comandos fora do contrato

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M2
**Complementa:** ADR-0013; critério A2

## Contexto

O teste do arquivador (A6) mandou `clock.set_scale` com `reason: "teste A6"`, fora do enum do contrato.

- O núcleo aceitou o comando e gerou um `scale_changed` inválido.
- O barramento validador recusou o evento na publicação e derrubou o kernel.
- O pior: o fato já estava no outbox, então o kernel cairia de novo a cada reinício.

Comandos vêm de fora (controladores, gateway, operador) e não podem derrubar a verdade do mundo.

## Decisão

1. **O kernel valida cada comando contra o contrato** antes de entregá-lo ao núcleo.
   - A validação roda no `Engine.submit`, o mesmo caminho que a recuperação reexecuta. Assim, a mesma entrada do diário dá sempre o mesmo resultado.
   - Por isso os contratos entram na versão do código (ADR-0044).
2. **Comando inválido com `id` UUIDv7 e tipo de comando:** vira `world.command.rejected.v1` com `reason: invalid_command` e o primeiro problema em `detail`. O mundo não muda.
3. **Comando sem `id` válido ou sem tipo de comando:** fica no diário e mais nada, porque não há a quem responder.

## Consequências

- Um controlador com bug recebe uma recusa legível, em vez de derrubar o kernel.
- A validação dos eventos publicados continua no barramento validador, como defesa extra (A2).
