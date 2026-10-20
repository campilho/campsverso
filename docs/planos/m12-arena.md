# Plano do M12 — A arena

**Status:** aprovado em 19/out/2026 (ADR-0061), com três mudanças sobre o rascunho de 18/out: o Sonnet fica de fora, "descobriu o leste" passa a ser lido pelo dado da memória, e o OpenRouter sai do marco. Quinto marco da v0.2 (`v0.2-macro.md`). Começou depois do fechamento do M11.

**Pronto quando (macro, encolhido pela ADR-0055):** o mesmo mundo e a mesma seed para o script e para os modelos, com as métricas da bíblia §13 lado a lado, o custo por dia simulado e quem descobriu o leste. O relatório fica em `docs/arena/`. O humano entra como referência qualitativa, não na tabela de 30 dias.

## O que o levantamento mostrou

- **Tempo real é o gargalo, não dinheiro.** A 72×, um dia simulado leva 20 minutos e 30 dias levam 10 horas por controlador. Em processo (o `make corrida` do M11), o mundo espera cada resposta e um dia leva o tempo das chamadas: uns 90 segundos no Haiku 5.5, 30 dias em menos de uma hora. O custo é pequeno: a fita de dois dias com memória custou US$ 0,034, uns US$ 0,017 por dia; 30 dias ficam em meio dólar no Haiku. Os 7 dias a 72× do M10 e do M11 ficam como demonstração ao vivo; o experimento roda em processo.
- **Em processo é lockstep sem mexer no kernel.** O pipeline em memória roda o relógio contínuo, mas o barramento entrega e espera a resposta antes do próximo tick: o mundo espera o modelo por construção, como o documento do tempo (§6) reserva para experimentos. A ADR-0057 e o princípio 7 não mudam; a decisão 3 do plano macro fica respondida assim.
- **O humano não cabe numa tabela de 30 dias.** Jogar 30 dias a 72× são 10 horas de alguém na tela. As sessões humanas que existem (M5 e M6, no sandbox) são curtas. O humano entra como referência qualitativa (o que ele faz no primeiro dia, comparado com o Camps) e a comparação longa fica para quando houver uma tarde de jogo gravada.
- **"Descobriu o leste" precisa de três sinais,** porque descobrir não é dizer: as colheitas por grupo ao longo dos dias (`make metrics` já separa oeste e leste), onde o agente escolhe plantar depois do dia 3 (o comportamento), e uma crença que fale do leste com confiança (a memória, só para quem a tem). A ablação limpa é a regra oculta desligada (`SEM_REGRA=1`, que o `make soak` já tem): se a crença e o comportamento só aparecem com a regra ligada, o agente descobriu.
- **Observabilidade: o que já existe cobre o experimento.** Cada chamada é um `llm.call.completed` com tokens, custo e latência; a fita guarda o pedido e a resposta; o `summary.json` de cada corrida resume o dia. O Langfuse (self-host multi-serviço em containers, ou nuvem) e o OpenTelemetry GenAI ficam para a versão em nuvem (pesquisa §13; ADR-0024, sem containers antes da AWS).
- **OpenRouter.** O segundo adaptador (ADR-0058) é o que põe GPT e Gemini na arena, com `usage.cost` em toda resposta e cache por `cache_control`. Vale meio dia de trabalho e abre a comparação entre famílias; entra como o último passo, opcional.

## 1. A arena em processo (decisões 1 e 2)

- **`make arena`:** uma corrida por controlador, em sequência ou em paralelo (cada uma com a sua chave de API é a mesma; o limite de taxa do nível segura), em `data/corridas/<data-hora>-<controlador>/`: `summary.json`, `metrics.txt`, `llm.jsonl` (a fita inteira), `memory.sqlite` e `archive.jsonl`. O `make corrida` do M11 vira a unidade; a arena só compõe.
- **Mesmo mundo, mesma seed** (`farm-camps-01`, 20261010) para todos; três seeds a mais para o Haiku com memória, que é o controlador principal, para ver a variância sem gastar mais que uns dólares.
- **Quem corre e por quanto tempo:**

  | Controlador | Dias | Seeds | Custo estimado |
  |---|---|---|---|
  | script (bíblia §11) | 30 | 1 | zero |
  | Haiku 5.5 sem memória (M10) | 30 | 1 | ~US$ 0,5 |
  | Haiku 5.5 com memória (M11) | 30 | 4 | ~US$ 2,5 |
  | Haiku 5.5 com memória, sem a regra R-001 | 30 | 1 | ~US$ 0,6 |

  O Sonnet 5.5 (14 dias, uns US$ 7) estava no rascunho e saiu na aprovação: o mundo é simples demais para a diferença entre modelos aparecer; a comparação entre modelos fica para uma segunda rodada numa fazenda mais rica (proposta para o M13, `ideia-m13-fazenda-mais-rica.md`). Opus 5.5 idem. GPT e Gemini só com o OpenRouter, que também saiu do marco.

## 2. As métricas e o relatório (decisões 3 a 5)

- **A tabela da bíblia §13 lado a lado,** por controlador, nos totais de 30 dias: colheitas por grupo, dias até amadurecer, moedas ao fim, recusas por motivo, murchas, pico de fome, desmaios, mais chamadas por dia, custo por dia, latência mediana e, para quem tem memória, crenças ao fim (quantas, e as três mais confiantes).
- **"Descobriu o leste" pelo dado da memória,** por pedido do usuário na aprovação: para cada corrida com memória, quando o agente escreveu pela primeira vez sobre o leste (a primeira anotação e a primeira crença, com dia e hora) e como manteve isso ao longo dos dias: a trajetória da confiança de cada crença sobre o leste a cada reflexão (formada, confirmada, enfraquecida, retirada), com o enunciado e a confiança ao fim. O comportamento fica como sinal secundário, único para quem não tem memória: a fração dos plantios e das colheitas no leste a partir do dia 4 (contra os dias 1 a 3). A corrida sem a regra é o controle.
- **`make arena-report`:** lê os `summary.json` e os arquivos das corridas e escreve `docs/arena/AAAA-MM-DD.md` com as tabelas, os gráficos em texto (moedas por dia, por controlador) e os links para as fitas. É o artefato da v0.2 para o M13 e para publicar.

## 3. O que fica de fora (decisões 6 e 7)

- **Observabilidade externa adiada:** Langfuse e OpenTelemetry GenAI vão para o `futuro.md`, para a versão em nuvem; o que a arena precisa já está nos eventos, nas fitas e nos resumos.
- **OpenRouter fora do marco,** por decisão do usuário: GPT e Gemini não entram na arena da v0.2; o segundo adaptador (`OpenRouterModel`, pela mesma `ModelPort`) fica no `futuro.md`, talvez para a v0.3.

## 4. Testes (decisão 8)

- A arena e o relatório são ferramentas de desenvolvimento, testadas com corridas sintéticas (resumos e arquivos pequenos escritos pelo teste); o CI nunca chama a API. O adaptador OpenRouter, se vier, é testado com o transporte falso como o da Anthropic.

## 5. Ordem do trabalho

1. **ADR-0061 e o plano aprovado;** `CLAUDE.md` e `README.md`.
2. **`make arena`:** a composição das corridas (controlador, modelo, memória, regra, seed, dias) sobre o `make corrida`, com o script e o Haiku; os três sinais do leste no `summary.json`.
3. **`make arena-report`** e `docs/arena/`.
4. **As corridas do Haiku** (sem memória, com memória em quatro seeds, sem a regra) e do script.
5. **Fechamento:** o relatório, a §9, o diário, o `futuro.md`, `make sessoes MARCO=M12`, custos.

## 8. Decisões

Aprovadas em 19/out/2026 (ADR-0061). As três mudanças do usuário sobre o rascunho estão marcadas.

1. **A arena roda em processo,** sobre o `make corrida`, com o mundo esperando o modelo por construção; os 7 dias a 72× ficam como demonstração. *Recomendação: sim.* **Aprovada.**
2. **Mesmo mundo e mesma seed para todos; três seeds a mais para o Haiku com memória.** *Recomendação: sim.* **Aprovada.**
3. **Quem corre:** script e Haiku sem memória por 30 dias, Haiku com memória por 30 dias em quatro seeds e uma vez sem a regra; o humano como referência qualitativa. *Recomendação no rascunho: também o Sonnet com memória por 14 dias.* **Aprovada sem o Sonnet:** o mundo é simples demais para a diferença aparecer; Sonnet e Opus entram numa segunda rodada, numa fazenda mais rica (proposta para o M13).
4. **A tabela da bíblia §13 lado a lado,** com custo, chamadas, latência e crenças. *Recomendação: sim.* **Aprovada.**
5. **"Descobriu o leste":** *recomendação no rascunho: três sinais (colheitas, plantios e crença).* **Aprovada com foco no dado da memória:** quando cada agente escreveu pela primeira vez sobre o leste e como manteve isso ao longo dos dias; o comportamento fica como sinal secundário, e a corrida sem a regra como controle.
6. **`make arena-report` em `docs/arena/`.** *Recomendação: sim.* **Aprovada.**
7. **Langfuse e OpenTelemetry adiados** para a nuvem. *Recomendação: sim.* **Aprovada.**
8. **OpenRouter:** *recomendação no rascunho: último passo, opcional.* **Fora do marco:** fica para o futuro, talvez para a v0.3.
9. **Ferramentas testadas com corridas sintéticas; o CI nunca chama a API.** *Recomendação: sim.* **Aprovada.**

## 9. Como ficou

Sete corridas de 30 dias em 19/out/2026, todas no mesmo mundo e na mesma seed (mais três seeds para o Haiku com memória), em processo, com o relatório inteiro em [`docs/arena/2026-10-19.md`](../arena/2026-10-19.md). Os totais:

| | script | Haiku sem memória | Haiku com memória (seed 1) | seed 2 | seed 3 | seed 4 | com memória, sem a regra |
|---|---|---|---|---|---|---|---|
| Moedas ao fim | 1.175 | 790 | 1.340 | 1.225 | 1.185 | 345 | 85 |
| Colheitas | 184 | 101 | 117 | 111 | 99 | 70 | 76 |
| Recusas | 0 | 98 | 94 | 98 | 91 | 103 | 111 |
| Pico de fome, desmaios | 79, 0 | 100, 0 | 100, 0 | 100, 0 | 100, 1 | 100, 0 | 100, 1 |
| Chamadas, custo | | 1.656, US$ 0,60 | 1.722, US$ 0,91 | 1.647, US$ 0,87 | 1.681, US$ 0,87 | 1.464, US$ 0,79 | 1.572, US$ 0,82 |
| Crenças ao fim | | | 24 | 27 | 32 | 34 | 26 |

O que as corridas disseram:

1. **A memória paga em moedas, com variância grande.** Três das quatro seeds com memória passaram o script (1.340, 1.225 e 1.185 contra 1.175); a quarta passou fome do dia 7 ao 22 e fechou com 345. A média das quatro é 1.024, e o Haiku sem memória, numa seed só, fez 790. O script continua imbatível em colheitas (184 contra 99 a 117) e em recusas (zero contra uns 95): ele não erra distância.
2. **Ninguém descobriu o leste.** Nenhuma corrida com memória guardou, ao fim de 30 dias, uma crença de que o leste amadurece mais rápido. As três que chegaram perto desaprenderam: a seed 1 formou no dia 11 uma crença sobre canteiros do leste que "não avançam na virada" e a retirou no dia 18; a seed 2 escreveu no dia 23 que "a abóbora amadurece em cerca de 6 dias nos canteiros do leste, não 8 como eu pensava" e, até o dia 30, diluiu para "6 a 8 dias, dependendo do canteiro" com confiança 0,50; a seed 3 viu no dia 15 que "o oeste ficou parado enquanto o leste avançou" e transformou isso numa crença sobre rega (0,95). A primeira anotação que nota a vantagem do leste, na seed 1, é do dia 30. A memória guarda o que o agente escreve; ela não faz ele comparar o que mediu.
3. **O comportamento não discrimina.** Todos plantam uns 55 a 60% no leste, o script inclusive, por rotina; a seed 4 e o controle sem a regra ficam em 42 a 45%. O sinal do comportamento, que era o do rascunho, não separa quem descobriu de quem não descobriu; por isso a decisão 5 virou o dado da memória, e por isso a fazenda 2 nasce sem canteiros (ADR-0062).
4. **A regra é o que faz a fazenda pagar.** O controle sem a R-001, com memória, fechou com 85 moedas: na fazenda 1, metade do rendimento vem do rio, mesmo para quem não sabe que ele existe. Os dias até amadurecer no arquivo mostram o efeito a quem olhar (oeste 4,2 a 5,1 contra leste 3,1 a 4,1 nas corridas com a regra), e nenhum agente olhou.
5. **O Haiku erra distância, não regra.** Entre 66 e 81 das recusas de cada corrida são `not_adjacent`, como no M11; `already_there` vem depois. A fome bate 100 em todas as corridas do modelo (o script fica em 79): ele não guarda comida.
6. **Custo e ritmo.** US$ 0,020 a 0,030 por dia simulado, 49 a 57 chamadas por dia, latência mediana de 1,7 a 1,9 s; a arena inteira custou US$ 4,86 de API, e uma corrida leva uns 70 minutos de relógio quando o Mac está acordado.

O que mudou em relação ao plano: a arena rodou em cinco processos em paralelo para recuperar o dia perdido com o Mac dormindo, com as corridas novas em pastas próprias e reservas na pasta principal (a reserva ao começar vai para o corredor antes do M14, `futuro.md`); o `make arena` passou a rodar sob `caffeinate`; a heurística de "descobriu" ficou estrita (um comparativo de tempo ou de vantagem no trecho que fala do leste) e o relatório mostra a primeira redação de cada crença, porque foi nela que a descoberta apareceu e sumiu. Custo do marco: US$ 4,86 de API e, no Claude Code, 13 turnos e 48 minutos de conversa (`docs/custos`).
