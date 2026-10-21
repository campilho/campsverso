# Plano do M14 — a segunda rodada da arena, na Fazenda Boa Vista

*Proposto em 20/out/2026, depois do fechamento do M13. Aprovado em 20/out/2026 (ADR-0063), com a decisão 1 em aberto quanto aos dias de Sonnet e Opus: a lista nasce com os dois a 30 dias e tetos, e o número de dias se confirma na hora de rodar.*

## A pergunta

A arena do M12 (ADR-0061) mostrou que, na fazenda 1, um Haiku com memória empata ou passa o script em moedas, mas ninguém guardou a regra do rio em 30 dias, e o comportamento não separa quem decide de quem segue a rotina: o mundo era simples demais e a geometria entregava a pergunta. A Fazenda Boa Vista (M13, ADR-0062) existe para medir **como** e **se** um agente decide melhor que um script ou que outro modelo, num mundo em que as escolhas custam: o que plantar, onde cavar, que ferramenta comprar, o que comer, quando vender. O M14 é a rodada que faz essa medida, com o Haiku, o Sonnet e o Opus contra o fazendeiro-script 2.

## O que o levantamento mostrou

- **A arena já aceita cartucho e modelo por corrida** (`Spec(cartridge, model)`, feito no M13), mas os dias são um só número para a rodada inteira (`--days`), o teto de orçamento é o mesmo para todas (`LIMITS`: US$ 0,60 por dia simulado, US$ 10 por corrida, calibrado para o Haiku) e a lista de corridas é fixa (`SPECS`, a do M12).
- **O relatório ainda é da fazenda 1:** lê o leste pelo id `plot-e-`, nomeia os grupos `oeste`/`leste` e não mostra as métricas novas da bíblia 2 §13 (canteiros na faixa do rio, ferramentas, mistura, refeições, estragos, murchas da madura, vendas abaixo de 80%), que `metrics.py` já calcula com os grupos `rio`/`fora`.
- **O custo cabe no estimado.** Na arena do M12 uma chamada do Haiku com memória leva uns 20,6 mil tokens de cache lido, 1,1 mil de cache escrito, 170 de entrada e 340 de saída, a 55 chamadas por dia simulado. Com a mesma mistura e a tabela de preços de `config/env/local.yaml`: Haiku US$ 0,03 por dia, **Sonnet US$ 0,60 por dia, Opus US$ 0,95 por dia**. O manual e o catálogo da Boa Vista são maiores (uns 20% a mais de cache lido): Sonnet por 14 dias ≈ US$ 10, Opus por 10 dias ≈ US$ 11, quatro Haikus por 30 dias ≈ US$ 4, o controle sem a regra ≈ US$ 1. **Uns US$ 26, abaixo dos US$ 30 da ADR-0062.** A fita da Boa Vista confirma a mistura (US$ 0,00054 por chamada, igual à fazenda 1).
- **O tempo de parede:** Haiku a uns 2 s por chamada são 1 h 15 min por corrida de 30 dias (M12); Sonnet e Opus respondem em 5 a 10 s, o que dá 1 a 2 h para 14 e 10 dias. Em paralelo, a rodada inteira cabe numa tarde, sob `caffeinate`.
- **A reserva da corrida ao começar** (anotada no M12) evita que dois processos em paralelo façam a mesma corrida; hoje só `summary.json` marca uma corrida feita, e a solução do M12 foi um `summary.json` de reserva à mão.
- **A linha de base cega está medida:** o script 2 em 30 dias faz 220 moedas e 141 colheitas, cava os 16 canteiros fora da faixa do rio, compra o regador grande no dia 25, não cozinha, estraga um rabanete e não vende abaixo de 80%.

## 1. As corridas

| Corrida | Modelo | Memória | Regra R-001 | Seed | Dias | Teto (US$/dia · total) | Custo estimado |
|---|---|---|---|---|---|---|---|
| script2 | fazendeiro-script 2 | – | ligada | 20261019 | 30 | – | 0 |
| haiku-memoria | Haiku 5.5 | sim | ligada | 20261019 | 30 | 0,60 · 10 | 1 |
| haiku-memoria-s2, -s3, -s4 | Haiku 5.5 | sim | ligada | +1, +2, +3 | 30 | 0,60 · 10 | 3 |
| haiku-memoria-sem-regra | Haiku 5.5 | sim | desligada | 20261019 | 30 | 0,60 · 10 | 1 |
| sonnet-memoria | Sonnet 5.5 | sim | ligada | 20261019 | 14 | 1,50 · 15 | 10 |
| opus-memoria | Opus 5.5 | sim | ligada | 20261019 | 10 | 2,50 · 15 | 11 |

Todas no mundo `farm-boavista-01`, com o mesmo manual, o mesmo catálogo e a mesma memória: só o id do modelo muda. O Haiku sem memória fica de fora (o M12 já mediu o efeito da memória). A seed do Sonnet e do Opus é a base, para a comparação direta com o Haiku da seed 1 e com o script. Uma corrida que bate no teto para no dia em que bateu, marcado no resumo, como a que desiste.

## 2. O corredor

- `Spec` ganha `days` e `limits` (o teto por corrida), e uma segunda lista, `SPECS_BOAVISTA`; `make arena RODADA=boavista [SO=nome]` escolhe a lista (a padrão continua a do M12, para reproduzir a fazenda 1).
- **Reserva ao começar:** a corrida é tomada quando a pasta dela ganha `progresso.txt`; outro processo pula a pasta tomada ou feita. Assim três `make arena RODADA=boavista` em paralelo dividem a rodada sozinhos; uma corrida abandonada (pasta sem `summary.json` e sem processo) se apaga à mão para refazer.
- O resto fica: cada corrida na sua pasta com `summary.json`, `metrics.txt`, `archive.jsonl`, `llm.jsonl` e `memory.sqlite`; `caffeinate` no macOS; `api.aclose()` ao fim.

## 3. O relatório

- **A tabela da bíblia** com os grupos do mundo (`rio`/`fora` na Boa Vista, `oeste`/`leste` na fazenda 1, lidos de `report.groups`) e as linhas novas da bíblia 2 §13: canteiros cavados na faixa do rio / total, o dia da compra do regador grande e do arado, a mistura de culturas por semana, refeições por receita, estragos por item, murchas da madura, vendas abaixo de 80% do preço.
- **"Descobriu o rio"**, pelo dado da memória como no M12 (a primeira anotação e a primeira crença, a trajetória de cada crença, a primeira redação), com o vocabulário da Boa Vista: rio, margem, perto da água, leste. O sinal de comportamento passa a ser **cavar na faixa**: a fração dos canteiros cavados na faixa do rio e o dia do primeiro deles, em vez de "plantou no leste".
- **As outras regras ocultas**, uma linha cada, pelo mesmo método (anotação ou crença que fala do efeito, e o comportamento que confirma): o tomate que murcha com um dia seco (parou de plantar tomate, ou regou todo dia), o alho que não precisa de rega (deixou de regar alho), o baú que conserva (guardou o que vence), o ensopado que sacia (cozinhou de novo), o adubo (adubou mais de uma vez). Só o efeito é visível; o relatório diz o que cada um escreveu e fez.
- O humano continua referência qualitativa (`futuro.md`).

## 4. A arte própria, durante as corridas

A decisão 14 do M13 ficou para cá por decisão do usuário: sprites LPC para o fogão, a pá, o arado, o regador grande, o adubo, os pratos e as culturas novas, com crédito no `CREDITS.csv`; placeholder desenhado onde o LPC não tiver. Meia sessão, enquanto as corridas rodam; não muda nenhum número.

## 5. Testes

- `test_arena.py` (ferramentas): as linhas novas da tabela e os sinais da Boa Vista com envelopes sintéticos; os grupos pelo mundo.
- `tests/e2e/test_arena.py`: uma corrida de um dia do script 2 na Boa Vista, mais a reserva ao começar (um segundo corredor pula a pasta tomada).
- O CI nunca chama a API: as corridas são `make arena`, à mão, fora do CI.

## 6. Ordem do trabalho

1. **Plano e ADR-0063.**
2. **O corredor:** `Spec.days`, `Spec.limits`, `SPECS_BOAVISTA`, `RODADA=`, a reserva ao começar; testes.
3. **O relatório:** grupos pelo mundo, linhas novas, "descobriu o rio" e as outras regras; testes.
4. **A rodada:** `make arena RODADA=boavista` em três processos sob `caffeinate`, numa tarde; `make arena-report`.
5. **A arte,** enquanto roda.
6. **Fechamento:** o relatório em `docs/arena/`, a §9, o diário, `futuro.md` (o que a rodada sugere para a fazenda 3), `make sessoes MARCO=M14`, custos.

Estimativa: duas sessões de trabalho e uma tarde de máquina. Custo de API: uns US$ 26, com teto por corrida.

## 7. Decisões

Aprovadas em 20/out/2026 (ADR-0063), todas como recomendado; a 1 com a pergunta do usuário sobre os 30 dias de Sonnet e Opus (uns US$ 60 na rodada, contra uns US$ 26 com 14 e 10 dias), a decidir na hora de rodar com os tetos como seguro; a 8 segue a 1.

1. **As corridas da §1** (script 2, Haiku com memória em quatro seeds, o controle sem a regra, Sonnet 14 dias, Opus 10 dias), todas no `farm-boavista-01` com o mesmo manual, catálogo e memória. *Recomendação: sim; é a ADR-0062 mais o controle, que custa US$ 1 e diz quanto da diferença é a regra.*
2. **Dias e teto por corrida** (`Spec.days`, `Spec.limits`), com Sonnet a US$ 1,50 por dia e 15 no total e Opus a US$ 2,50 e 15. *Recomendação: sim; o teto é o seguro contra uma saída mais longa do que a estimada, e a corrida que bate nele vale até onde foi.*
3. **A seed base para Sonnet e Opus** (a do mundo), não seeds novas. *Recomendação: sim, para comparar direto com o Haiku da seed 1 e com o script; seeds novas ficam para uma terceira rodada, se a diferença aparecer.*
4. **`make arena RODADA=boavista`** com uma segunda lista de corridas; a padrão continua a do M12. *Recomendação: sim.*
5. **A reserva da corrida ao começar** (`progresso.txt` marca a pasta tomada). *Recomendação: sim; é pequeno e tira a gambiarra do M12.*
6. **O relatório com os grupos do mundo e as linhas da bíblia 2 §13,** "descobriu o rio" pela memória e pelo cavar na faixa, e uma linha por regra oculta (tomate, alho, baú, ensopado, adubo). *Recomendação: sim; é o que a Boa Vista existe para medir.*
7. **A arte própria durante as corridas** (decisão 14 do M13). *Recomendação: sim, meia sessão, sem mexer em número nenhum.*
8. **Custo:** teto de US$ 30 na rodada; se o Opus custar mais que o dobro do estimado por dia, a corrida cai para 7 dias. *Recomendação: sim.*
9. **O humano** fica fora da tabela (referência qualitativa, como no M12). *Recomendação: sim.*

## 8. Como ficou

Fechado em 20/out/2026, no mesmo dia do M13: o plano e as decisões à tarde, o corredor e o relatório na sessão da Fable, a rodada e a arte à noite numa sessão no Opus. O relatório está em `docs/arena/2026-10-20.md`. Sonnet e Opus correram os 30 dias (decisão 1, com os tetos como seguro; nenhum bateu no teto).

**Os números.**

| Corrida | Moedas | Colheitas | Canteiros | Ferramentas | Fome máx. | Desmaios | US$ |
|---|---|---|---|---|---|---|---|
| script 2 | 220 | 141 | 16 | regador grande (dia 25) | 91 | 0 | 0 |
| Haiku com memória (4 seeds) | 0 a 5 | 22 a 29 | 4 a 5 | nenhuma | 100 | 1 a 2 | 0,45 a 0,49 |
| Haiku sem a regra | 5 | 28 | 6 | nenhuma | 100 | 1 | 0,51 |
| Sonnet | 18 | 81 | 15 | nenhuma | 100 | 0 | 11,58 |
| Opus | 1.143 | 161 | 32 | arado (dia 19), regador grande (dia 25) | 72 | 0 | 26,35 |

**O que a rodada disse.**

- **Na Boa Vista os modelos se separam.** Na fazenda 1, o Haiku com memória empatava ou passava o script; aqui ele quebrou nas quatro seeds: terminou sem dinheiro, com a fome em 100 e desmaios, decidindo umas 26 vezes por dia (contra 55 na fazenda 1) e esperando mais do que trabalhava. O Sonnet sobreviveu sem desmaio, mas ficou longe do script em moedas. O Opus terminou com cinco vezes as moedas do script e mais colheitas que ele.
- **O Opus planejou o capital.** Cavou os 32 canteiros até o dia 14, diversificou (rabanete, batata, abóbora, tomate, cenoura), comprou o arado e o regador grande e os revezou pelo baú por causa do peso, cozinhou duas sopas e anotou o mercado saturando ("até 4 unidades saem a preço cheio"). Reinvestiu tudo em semente até o dia 21 e colheu o retorno no fim: a curva de moedas sobe nos últimos oito dias.
- **Ninguém cavou na faixa do rio,** nem o script: os 16 canteiros dele ficam ao redor do poço, a 7 tiles da faixa, e os modelos cavam perto da casa e do poço porque andar gasta energia. Sem canteiro na faixa, a R-001 nunca agiu, e o controle sem a regra terminou igual aos outros Haikus. Com o teto de 32 e nenhum jeito de desfazer um canteiro, quem descobrisse o rio tarde não poderia mudar a fazenda de lugar. Descobrir o rio na Boa Vista pede exploração, e nenhum controlador explorou.
- **As outras regras ocultas quase não apareceram:** ninguém plantou alho, ninguém adubou, ninguém fez ensopado; os tomates foram regados todo dia e nunca murcharam; só o Opus usou o baú (12 vezes). Nenhuma corrida vendeu abaixo de 80% do preço.
- **Custo:** US$ 40,30 na rodada (Haikus 2,38, Sonnet 11,58, Opus 26,35), mais US$ 0,11 das corridas duplicadas no começo; o plano estimava uns US$ 60 com Sonnet e Opus por 30 dias. O Opus custou US$ 0,88 por dia simulado e levou 1 h 37 min.

**O que deu errado.** Os três `make arena` abertos em paralelo criaram três pastas (a padrão levava a hora), e a reserva não valia entre elas; dois foram parados no dia 3 ou 4 do Haiku e a pasta padrão passou a ser uma por dia e por rodada. Conferindo o relatório, três heurísticas estavam frouxas: "margem" casava com a margem de lucro do tomate, "todo dia" com o tempo para amadurecer e "guard" com "guardar comida". A última revelou uma dica da regra oculta do baú na descrição da ferramenta `deposit` e no manual ("o baú guarda bem"), que o teste de palavras proibidas não lia; uma crença do Opus repetiu a frase. A dica saiu do manual e do catálogo, o teste passou a ler as descrições das ferramentas, as heurísticas ficaram estreitas e o relatório foi regerado. O sinal do baú desta rodada fica contaminado e não conta como descoberta.

**Para depois** (`futuro.md`): canteiros sem teto e um jeito de aterrar o canteiro vazio, para a descoberta do rio poder mudar a fazenda; um fazendeiro-script que planeja o capital e faz experimentos (canteiros de teste em lugares diferentes) para competir com o Opus; assistir uma corrida na tela pelo replay em modo contínuo. O usuário considera fazer da v0.3 uma fazenda de novo, com essas complexidades, e empurrar o escritório para a v0.4; a decisão fica para o fechamento da v0.2 (M15).
