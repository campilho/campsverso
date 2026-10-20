# ADR-0063 — Decisões do plano do M14 (a segunda rodada da arena, na Fazenda Boa Vista)

**Status:** aceita · **Data:** 2026-10-20 · **Marco:** M14
**Complementa:** `docs/planos/m14-segunda-rodada.md`; ADR-0061 (a arena), ADR-0062 (a Fazenda Boa Vista e as métricas da bíblia 2 §13)
**Altera:** o corredor da arena (`campsverso_testkit.arena`: dias e teto por corrida, duas rodadas, reserva ao começar) e o relatório (`campsverso_tools.arena`: os grupos do mundo, as linhas da bíblia 2 §13, "descobriu o rio" e as outras regras ocultas)

## Decisão

As decisões do plano, aprovadas pelo usuário em 20/out/2026, no mesmo dia do fechamento do M13:

1. **As corridas:** o fazendeiro-script 2, o Haiku 5.5 com memória em quatro seeds, o Haiku com memória sem a regra R-001 (o controle), o Sonnet 5.5 e o Opus 5.5 com memória, todos no mundo `farm-boavista-01`, com o mesmo manual, o mesmo catálogo e a mesma memória: só o id do modelo muda. O Haiku sem memória fica de fora (o M12 já mediu o efeito da memória). O usuário perguntou se Sonnet e Opus não podiam correr os 30 dias como os outros: pela conta do plano (US$ 0,60 e 0,95 por dia simulado, uns 20% a mais pelo manual maior), 30 dias de cada custam uns US$ 22 e 34, e a rodada inteira uns US$ 60, dentro do orçamento de US$ 100 da v0.2 mas gastando mais da metade do que resta. A lista nasce com os dois a 30 dias e com tetos (decisão 2) que dizem até onde cabem; o número de dias é confirmado na hora de rodar (`ARENA_DIAS` limita todos).
2. **Dias e teto por corrida** (`Spec.days`, `Spec.limits`): Sonnet a US$ 1,50 por dia simulado e 25 no total, Opus a 2,50 e 35; o Haiku fica com o teto do M12 (0,60 e 10). A corrida que bate no teto para no dia em que bateu, marcado em `budget_day` no resumo e numa linha do relatório, e vale até onde foi.
3. **A seed base para Sonnet e Opus** (a do mundo, 20261019), não seeds novas: a comparação é direta com o Haiku da seed 1 e com o script.
4. **`make arena RODADA=boavista`** escolhe a segunda lista de corridas; a padrão continua a do M12, para reproduzir a fazenda 1.
5. **A reserva da corrida ao começar:** a pasta da corrida é de quem a criou (`mkdir` sem sobrescrever); outro processo pula a pasta tomada ou feita, e três `make arena` em paralelo dividem a rodada sozinhos. Uma corrida abandonada se apaga à mão para refazer.
6. **O relatório** com os grupos do mundo (`rio`/`fora` na Boa Vista, `oeste`/`leste` na fazenda 1), as linhas da bíblia 2 §13 (canteiros cavados na faixa do rio, o dia da compra de cada ferramenta, a mistura de culturas, refeições, estragos, murchas da madura, vendas abaixo de 80%), "descobriu o rio" pelo dado da memória com o vocabulário da Boa Vista (rio, margem, beira, perto da água, leste) e pelo comportamento de cavar na faixa, e uma linha por regra oculta (tomate, alho, baú, ensopado, adubo) com a primeira anotação, a primeira crença e o que a corrida fez.
7. **A arte própria durante as corridas** (a decisão 14 do M13, adiada pelo usuário): sprites LPC com crédito, sem mexer em número nenhum.
8. **Custo:** teto de US$ 30 na rodada com Sonnet e Opus por 14 e 10 dias, ou uns US$ 60 com os dois por 30 dias, a decidir na hora de rodar; se o Opus custar mais que o dobro do estimado por dia, a corrida dele cai para 7 dias.
9. **O humano** fica fora da tabela, como referência qualitativa (`futuro.md`).

## Consequências

- O corredor ganha `days` e `limits` por corrida, a lista `SPECS_BOAVISTA`, `--rodada`, a reserva ao começar e a parada no teto (a guarda pausa o mundo; em processo isso vira um `DeadlockError`, que o corredor lê como "bateu no teto" quando o resumo tem `budget_exceeded`). O `--only` passa a ser conferido contra a rodada escolhida.
- O relatório lê os grupos pelas métricas (ADR-0062: o canteiro cavado não tem grupo; a faixa do rio vem da posição e da água do mapa) e mostra a coluna do teto e a linha "parou no teto". O relatório da fazenda 1 regenerado só muda por essas duas adições.
- As heurísticas das regras ocultas são declaradas no código (o assunto e o efeito no mesmo trecho) e o relatório mostra o que cada corrida escreveu e fez, para quem quiser discordar.
- Custo de API da rodada: uns US$ 26 com Sonnet e Opus por 14 e 10 dias, uns US$ 60 por 30 dias, sempre com teto por corrida. O CI não roda nada disto.
