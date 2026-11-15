# ADR-0080 — Decisões do plano do M24 (o dev pensa e cria)

**Status:** aceita · **Data:** 2026-11-15 · **Marco:** M24
**Complementa:** `docs/planos/m24-o-dev-pensa-e-cria.md`; ADR-0077 (o plano macro da v0.4); ADR-0078 e ADR-0079 (o escritório); ADR-0055 (a oficina); ADR-0058, ADR-0059 e ADR-0060 (a porta de modelo, a mente e a memória)

## Contexto

O M24 põe a mente no dev do escritório e o faz trabalhar de verdade, num espaço de trabalho isolado, com a entrega num patch que o humano aplica. A primeira criação é o testador, que vira o primeiro robô da bancada.

O levantamento achou:
- a mente genérica na estrutura, mas com textos da fazenda dentro: o tick de um minuto, a nota sobre fome e moedas, a reflexão "da noite, nesta fazenda";
- a reflexão presa ao sono, que o escritório não tem;
- nenhum motivo de decisão para a fala;
- o orçamento sem teto por pedido e pausando o mundo inteiro;
- nenhum código para agir fora do mundo.

O plano foi aprovado em 15/nov como recomendado, com duas ressalvas do usuário:
- **As pausas são ilustrativas.** O dev faz café, água e banheiro quando a rotina o conduz, e não quando o modelo trabalha. Trabalhando num código, ele fica sentado na mesa. Quando não há o que fazer para o modelo, um script determinístico assume e faz o que não custa nada, como os avatares que passam o dia no café na página do CampsCast.
- **O orçamento estourado desliga a mente.** A rotina assume, e o dev avisa que não pode mais programar.

## Decisão

1. **Quatro partes:** o mundo, a oficina, a mente e a criação. A arte corre ao lado, com o teste do Claude Design.
2. **As pausas são ilustrativas,** feitas pela rotina, sem necessidades no kernel e sem efeito no trabalho.
3. **A copa fica num canto da sala, e o banheiro é uma porta.** O lugar exato sai com a arte.
4. **O almoço é na copa, das 12 às 13, pela rotina.** Se estiver no meio de um trabalho, o dev almoça quando ele acabar.
5. **Falar com o dev interrompe a ação dele,** com o motivo que já existe (`action_interrupted`), quando o cartucho declara `interrupt_on_speech`. Nenhum contrato muda.
6. **Os pacotes da mente do gênero `office` e do cenário `office_campsverso`.** A mente genérica perde as palavras da fazenda, e as fitas da fazenda continuam valendo, byte a byte.
7. **A revisão do dia acontece ao chegar** e cobre os dias sem revisão, no máximo três.
8. **A oficina:**
   - a `WorkshopPort`;
   - um clone raso do repositório por pedido, em `data/oficina/`, sem `.env`, `data/` e `privado/`;
   - só Python no M24.
9. **As oito ferramentas da oficina,** com limites de tamanho e de tempo. Cada passo publica um `workshop.step.v1`.
10. **O isolamento pelo `sandbox-exec`:** sem rede, escrita só no espaço de trabalho e um ambiente sem segredos.
11. **O trabalho:**
    - o `work` dura até uma hora do mundo, com a sessão da oficina dentro;
    - a sessão acaba no `pronto`, na fala ou num limite;
    - o controlador propõe a entrega sem esperar um pedido de decisão.
12. **A entrega:**
    - o patch vai para o depósito de arquivos;
    - é recusado se toca a constituição, apaga um teste ou desliga uma verificação, ou traz uma palavra proibida (a lista fica em `privado/`, fora do git);
    - o `make aplicar` põe o patch num ramo.
13. **O testador é a criação.**
    - O pedido e o aceite são escritos pelo usuário no escritório.
    - O registro de robôs fica no cenário.
    - A mente ganha a ferramenta `chamar_robo`.
14. **Os modelos:** os cinco passam na prova de conformidade, e a criação fica com o melhor da prova entre o Sonnet e o Opus.
15. **O orçamento:**
    - o teto por pedido;
    - o `cmd.ops.budget.set`;
    - no escritório, estourar desliga a mente: a rotina assume, e o dev diz uma vez que ficou sem bateria e não consegue mais programar, sem pausar o mundo;
    - na fazenda, o mundo segue pausando.
16. **O sinal de vida da guarda:** sem ele, a mente desliga e a rotina assume, no lugar de pausar o mundo, como a §6 do plano macro previa.
17. **As fitas do escritório** usam um repositório de exemplo, e não o de verdade.
18. **A mente com rotina:**
    - o modelo é chamado só quando há trabalho: um pedido a fazer, um pedido dele em andamento ou devolvido, uma entrega a avisar, alguém que falou com ele;
    - no resto, a rotina determinística conduz o dev;
    - o kernel vê um controlador só (`llm`);
    - as propostas da rotina levam a intenção "rotina:".

## Consequências

- **O custo de um dia a 1× cai muito:** o modelo não é chamado para esperar, sentar ou tomar café.
- **O escritório fica vivo o dia inteiro** sem custo, e o orçamento estourado não para nada além da programação.
- **A rotina e o dev-script dividem o código.** O dev-script, com o trabalho simulado, continua nos mundos sem mente, nos testes e no soak.
- **O plano macro (§6) muda num ponto:** a guarda caída não pausa o escritório. Ela desliga a mente.
