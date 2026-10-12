# ADR-0052 — Política de interrupção das ações

**Status:** aceita · **Data:** 2026-10-12 · **Marco:** M6 (passo zero)
**Altera:** bíblia §8, a regra geral "uma ação em andamento pode ser cancelada por novo comando do mesmo controlador (exceto `sleep`)"
**Complementa:** `docs/planos/m6-renderer-phaser.md`; bíblia §8; contratos §7; ADR-0038, ADR-0051

## Contexto

Jogando o M5 a 72× (`data/sandbox/20261012-134710`), um segundo "plantar" mandado antes de o primeiro terminar cancelava o primeiro:
- às 14:04, plantar no `plot-e-07` (5 ticks);
- às 14:05, o pedido do `plot-e-06` cancelou o anterior;
- às 14:07, o do `plot-e-08` cancelou o segundo, e só ele terminou.

Na partida foram 4 plantios, 7 deslocamentos e 2 esperas cancelados. O kernel seguia a bíblia §8. A regra serve para quem anda (mudar de destino), mas não para quem trabalha.

O kernel já tinha meio caminho: cada ação do cartucho dizia se podia ser cancelada (`cancellable`, no código), e o kernel recusava com `busy` as que não podiam (o sono). Faltavam três coisas:
- declarar isso como dado do cartucho;
- um terceiro caso, o de ações longas que podem parar no meio e guardar o que foi feito (cortar uma árvore em 10 golpes e parar no quinto);
- mostrar isso a quem observa.

## Decisão

1. **Cada ação tem uma política de interrupção** (`interrupt`), que diz o que acontece com um comando novo do mesmo controlador enquanto ela está em andamento:

   | Política | Um comando novo durante a ação |
   |---|---|
   | `never` | é recusado com `busy`; a ação continua |
   | `cancel` | cancela a ação (`action.failed`, motivo `cancelled`) e começa a nova; nada da ação cancelada acontece |
   | `partial` | interrompe a ação (`action.failed`, motivo `cancelled`), e o cartucho grava o trabalho feito até ali |

2. **Quem declara.**
   - O cartucho declara a política de cada ação como dado, junto da duração e da energia (`actions` no `farm.yaml`). O campo é obrigatório.
   - Um cenário pode trocar a política, como já troca números (ADR-0031).
   - As ações do kernel, `move` e `wait`, são `cancel`.
3. **Na fazenda:**
   - `never`: plantar, regar, encher, colher, limpar, comer, guardar, pegar, vender, comprar e dormir;
   - `cancel`: andar e esperar;
   - `partial`: nenhuma na v0.1.
4. **Como funciona o `partial`.**
   - Ao interromper, o kernel chama o gancho `interrupted(ctx, ops, elapsed_ticks)` da ação.
   - O cartucho grava o progresso pelas primitivas genéricas (ex.: a árvore com o atributo `golpes: 5`), e isso vira evento genérico como qualquer mudança.
   - Para continuar, basta propor a ação de novo: a validação lê o progresso e devolve uma duração menor.
   - O kernel suporta o `partial` desde já, testado com uma ação de teste, porque acrescentar um valor depois a um campo de contrato que já existe quebraria quem lê.
5. **O mundo interrompe qualquer política.** O desmaio interrompe a ação qualquer que seja a política (motivo `fainted`). Numa ação `partial`, o gancho roda também.
6. **Contratos,** só com campos opcionais (continuam v1):
   - `action.accepted.v1` ganha `interrupt`;
   - `action.failed.v1` ganha `elapsed_ticks`, quanto a ação durou antes de parar;
   - o estado `realtime` ganha o tick de início da ação e a política dela, e o início e o fim previsto do sono.
7. **A recusa `busy`** diz qual ação ocupa o avatar e até qual tick, para a tela mostrar "ocupado: plantando, faltam 3 min".
8. **A fila de ações** (clicar em três canteiros e o avatar fazer um depois do outro) e **o despertador** ficam para o futuro (`docs/planos/futuro.md`). O despertador seria uma regra do mundo que encerra o sono, e não um cancelamento do controlador.

## Consequências

- A bíblia §8 troca a regra geral pela política de cada ação.
- O script não muda: ele só propõe quando a ação anterior terminou.
- A versão dos cartuchos `farm` e `farm_camps` sobe para 0.2.0. Um arquivo gravado com a regra antiga, se reexecutado, daria outro resultado onde houve cancelamento.
- A barra de progresso sobre o avatar sai do estado da tela: início, fim previsto e tick mostrado.
