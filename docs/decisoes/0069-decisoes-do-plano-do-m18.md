# ADR-0069 — Decisões do plano do M18 (a economia)

**Status:** aceita · **Data:** 2026-10-24 · **Marco:** M18
**Complementa:** `docs/planos/m18-a-economia.md`; ADR-0062 (o mercado que satura na Boa Vista); ADR-0066 (decisão 7, a economia reaproveitável); ADR-0067 (o ano e as estações)

## Contexto

A economia de hoje é código do gênero farm: a caixa de vendas que satura no dia, o quiosque com ciclo e preço fixo, o comprador que paga de manhã. O escritório da v0.4 vai precisar de pedidos com prazo e pagamento (os tickets), e o vilarejo, de uma feira. O usuário pediu uma economia que siga a regra básica: o que é raro custa caro, o que sobra custa pouco.

## Decisão

1. **A economia é uma biblioteca, `libs/economy`,** e não uma primitiva do kernel. Ela é Python puro e determinístico, sem I/O e sem saber o que é uma fazenda: mercado, encomendas e agenda. **Cada mundo escolhe se a usa:** o cartucho importa a biblioteca e guarda o estado nos atributos das suas entidades, e o kernel nunca a importa (o teste de arquitetura confere). O escritório pode usar a economia sem a fazenda.
2. **O clima de mundo aberto é outra biblioteca, `libs/climate`,** separada da economia, para os mundos ao ar livre: o sorteio do tempo por estação, a previsão do dia seguinte e as condições que não são só sol e chuva. O escritório não precisa dela. O calendário e as estações continuam no kernel (ADR-0067), porque o tempo é física de todo mundo; a biblioteca lê a estação do kernel. *(Pergunta do usuário na aprovação; a separação sai neste marco, porque o sorteio do tempo é reescrito agora de qualquer jeito.)* O que o tempo faz com as plantas, e a reação do mercado ao tempo, continuam no cartucho, que liga as duas bibliotecas.
3. **O domínio `economy` nos contratos,** da plataforma, como `memory` e `llm`: os eventos das encomendas (publicada, aceita, entregue, vencida).
4. **O preço de venda tem memória:** cada unidade vendida derruba o preço daquela colheita, até um piso, e na virada do dia ele recupera parte da distância até a referência. Na Morada do Sol: −2% por unidade, piso de 40%, um terço por dia.
5. **O preço de compra sobe:** cada unidade comprada da mesma semente sobe o preço no dia, e de manhã ele volta à tabela. Na Morada do Sol: +3% por unidade.
6. **A referência muda com a estação e oscila:** fora da estação boa, a colheita vale mais (fraca 1,25; parada 1,6), e a referência anda um pouco a cada dia (até 4%, limitada a 15%), por um RNG nomeado.
7. **As encomendas:** um quadro com pedidos de clientes, com prazo e pagamento acima da referência, pago na entrega. Na Morada do Sol: até 4 abertas, até 2 aceitas, prazo de 3 a 7 dias, prêmio de 50%.
8. **A reputação é a regra oculta nova (R-004):** cumprir o prazo traz mais pedidos e prêmios maiores; deixar vencer um pedido aceito, o contrário. O manual só diz que os clientes lembram de quem cumpre. *(Nota do usuário: com um avatar faz pouca diferença; com os ajudantes e vários jogadores, vai fazer.)*
9. **A feira** é um evento da agenda, numa barraca que compra com prêmio e paga na hora. Na Morada do Sol: a cada 7 dias, das 06:00 às 14:00, na entrada da fazenda, a 30% acima da referência.
10. **O tacho** transforma colheita em produto que vale mais e dura mais, trabalhando sozinho: geleia, molho de tomate e farinha de mandioca.
11. **A composteira** transforma o que ia se perder em adubo.
12. **O clima com previsão:** o tempo de amanhã sai às 18:00. A tempestade derruba parte das plantas maduras, e a seca pede rega até o meio-dia. Depois de uma delas, a referência das colheitas sobe por alguns dias.
13. **O contrato do tempo:** `world.weather.changed.v1` ganha o campo opcional `forecast`; as condições novas (`storm`, `drought`) cabem no campo, que já é texto aberto.
14. **A mente** ganha o manual, as ferramentas e a fita nova, e uma corrida de verificação de 7 dias com o Haiku.
15. **O script 2 adaptado só no essencial:** encomendas da cultura que já planta e a colheita antes da tempestade. A feira e o tacho ficam para o script 3 (M19).
16. **A tela:** o menu do quadro com os pedidos, a previsão no HUD, o progresso do tacho, a arte e as métricas por canal. *(Nota do usuário: ajustes de visual depois, se precisar.)*

**Todos os números são dados do cenário** (`morada.yaml`), e não do código: o preço de venda e o de compra, a feira, as encomendas, a reputação, as receitas e o clima podem mudar sem mexer na biblioteca nem no gênero. *(Nota do usuário nas decisões 3, 4 e 8.)*

## Consequências

- **O kernel não muda,** a não ser para marcar como previsão o tempo de um dia que ainda não chegou.
- **Duas bibliotecas novas** no workspace, com as mesmas proibições de determinismo da simulação (sem relógio de parede, sem `random` global) e um contrato no `import-linter`: o kernel e os serviços não as importam, e elas não importam kernel, serviços, adaptadores nem cartuchos.
- **A Boa Vista e a fazenda 1 ficam como estão:** o mercado que volta à tabela de manhã, só sol e chuva, nenhuma encomenda.
- **A rodada do M14 continua comparável,** e a Morada do Sol ganha uma linha de base nova (o script 2 adaptado).
