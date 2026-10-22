# ADR-0066 — As decisões do plano macro da v0.3 (a fazenda sofisticada)

**Status:** aceita · **Data:** 2026-10-21 · **Marco:** começo da v0.3
**Complementa:** `docs/planos/v0.3-macro.md` (§2 e §8); ADR-0064; ADR-0065

## Contexto

O plano macro da v0.3 trazia vinte decisões com recomendação. No M15 o usuário aprovou a linha e pediu para revisá-las em detalhe quando a v0.3 começasse. As respostas vieram em 21/out, depois da tag `v0.2.0`, com mudanças em quatro pontos (as estações, as regras ocultas, a economia e os ajudantes) e dois pedidos novos: o visual antes das outras famílias de modelos, e uma rodada do humano em cada versão.

## Decisão

1. **Sete marcos, M16 a M22, numa ordem nova:**
   - M16: a Fazenda Morada do Sol;
   - M17: ver e assistir;
   - M18: a economia;
   - M19: os controladores e a medição;
   - M20: os ajudantes;
   - M21: a terceira arena;
   - M22: o fechamento.

   Antes do M16, uma rodada do humano na Boa Vista fecha a lacuna da v0.2. O visual vem antes das conexões com outras famílias de modelos.
2. **O cenário novo é a Fazenda Morada do Sol,** que estende `farm`. A Boa Vista e a fazenda 1 ficam intactas. O mapa é maior que a tela, e a câmera rola.
3. **Canteiros sem teto, só na grama.** O canteiro sem planta volta a ser grama depois de alguns dias, o que pede uma primitiva de remover entidade no kernel.
4. **O relógio é um ano acelerado,** com as quatro estações nas datas do hemisfério sul. O agente sabe a data e a estação. O manual traz o calendário de plantio, com a afinidade de cada cultura com cada estação. Nem tudo nasce em qualquer estação, e nem toda planta morre na troca.
5. **A névoa tem raio configurável.** A noite pode reduzir o raio, e uma luz (lanterna ou lampião) pode ampliá-lo.
6. **As regras ocultas são verdades do mundo, fixas.** O que varia entre as corridas é o mapa: com o rio em outro lugar, o lugar bom de plantar muda. Uma variante do mapa fica reservada para a arena final.
7. **A economia vira um módulo robusto,** reaproveitável pelo escritório e pelo vilarejo, que tem uma feira:
   - encomendas com prazo;
   - oferta e demanda nos dois sentidos: vender muito do mesmo item baixa o preço, e comprar muito do mesmo item sobe o preço;
   - a feira, o processamento, os adubos e o clima com previsão.
8. **O fazendeiro-script 3 e o oráculo,** como na proposta.
9. **O caderno de campo** fica na mente do avatar, calculado por código a partir do que o avatar viu, e entra na arena como variável (com e sem caderno). O mundo nunca escreve nele.
10. **O ajudante contratável** tem uma diária cara, e o limite de ajudantes é o dinheiro. Haverá uns cinco personagens, cada um com uma ficha: nome, especialidade, e pelo menos um ponto bom e um ruim.
11. **A medição:**
    - a prova do mundo e o juiz;
    - uma seed por modelo na terceira arena, e mais seeds só depois de medir a primeira;
    - um GPT e um Gemini pela OpenRouter, escolhidos no M21.
12. **Assistir as corridas na tela, de preferência ao vivo,** numa visão arena com várias fazendas pequenas lado a lado, aceleradas, e um clique para entrar numa.
13. **Orçamento de API da v0.3 de US$ 150,** com teto por corrida.
14. **Ficam fora desta versão:**
    - os animais (que voltam no futuro com várias espécies);
    - a qualidade da colheita;
    - a necessidade "sono";
    - os irrigadores (que voltam no futuro);
    - a busca por relevância na memória, que fica em observação: medir o bloco de abertura, e um RAG de documentos fica para depois.

## Consequências

- **Ficam para o plano de cada marco, com números:**
  - **M16:** quantos dias simulados dura o ano; o que acontece com a planta fora da estação; em quantos dias o canteiro volta a ser grama.
  - **M17:** como assistir. A recomendação é a projeção da tela lendo o arquivo de eventos de cada corrida enquanto ele cresce, sem reexecutar o kernel.
  - **M18:** onde mora o módulo de economia (primitivas do kernel ou uma biblioteca para cartuchos), com ADR.
  - **M19:** como fazer as variantes do mapa.
  - **M20:** as fichas dos personagens e quem controla o ajudante.
- **A ideia de sortear as regras por seed sai do plano.** O teste do script 3 passa a ser vencer em mapas diferentes.
- **A conta da OpenRouter** é do usuário, que cria a conta e a chave. A estimativa de custo está na §6 do plano macro.
