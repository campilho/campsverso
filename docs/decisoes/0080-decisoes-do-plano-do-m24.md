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

## Adendo (15/nov): o orçamento, como ficou

A parte 1 fez o lado da guarda; a reação da mente vem com ela, na parte 3. Quatro pontos saíram diferentes do plano:

1. **Os avisos com o pedido são um tipo novo** (`ops.budget.threshold_reached.v2` e `ops.budget.exceeded.v2`). O plano punha o escopo do pedido como campo opcional, mas o escopo já existia, com `day` e `total`, e acrescentar um valor ao enum é incompatível.
2. **O sinal de vida é uma mensagem viva** (`live.budget.v1`), e não o evento `ops.heartbeat.v1`. Ele segue o pulso do kernel (ADR-0051): sai a cada 5 s num assunto que nenhum stream guarda, com os tetos, o gasto e o que está estourado. Um evento a cada 5 s encheria o arquivo de um mundo que roda o dia inteiro.
3. **Mudar os tetos vira um fato** (`ops.budget.limits_changed.v1`), para que o arquivo registre quem subiu o teto, quando e por quê. Os tetos do comando ficam no livro-caixa da guarda e valem também depois de uma queda; o arquivo do mundo vale até o primeiro comando. Subir um teto acima do gasto desfaz o estouro e rearma os avisos.
4. **O teto do pedido nunca pausa o mundo,** nem na fazenda. No dia e no total, quem decide é o mundo (`budget.on_exceeded`): `pause` nas fazendas, como antes; `mind_off` no escritório, onde o mundo segue e a mente desliga.

O kernel consome todos os comandos do mundo e passa a deixar de lado os do domínio `ops`, que são da guarda: sem recusa e sem entrada no diário.

**Um defeito do M23, achado no caminho.** O `make escritorio` caía assim que subia. O mundo do escritório não tinha `budget`, a guarda saía com erro, e o honcho derrubava os outros processos junto. Os mundos do escritório ganharam tetos provisórios (US$ 3 por dia, US$ 1 por pedido, US$ 30 no total, `mind_off`), que a parte 3 ajusta quando a mente chegar.

## Adendo (15/nov, à noite): a oficina, como ficou

A parte 2 fez a oficina sem a mente. Quem a usa por enquanto é o dev-script, o script de reserva, para que o caminho inteiro possa ser testado sem modelo:
- **a porta** (`WorkshopPort`, em `libs/ports`) e o **adaptador local** (`libs/adapters`): o clone raso pelo `file://`, com o próprio `.git`; o ambiente pelo `uv sync --offline --frozen`. Abrir um espaço leva cerca de 1 s;
- **as oito ferramentas,** com os limites do plano. Toda ferramenta recusa o caminho que sai do espaço, inclusive por link simbólico, e o que entra no `.git`;
- **os testes sob o `sandbox-exec`:** um teste que tenta a rede falha, e um que escreve fora do espaço também;
- **a sessão no controlador:** a proposta de entrega do dev-script leva a sessão (os passos). O controlador a roda pela porta, publica um `workshop.step.v1` por passo, revisa o patch, guarda-o em `data/entregas/` e põe o resumo na entrega (`office.ticket.delivered.v1`, `patch`). Num mundo sem oficina (`workshop: true` no arquivo do mundo), a sessão sai da proposta, e a entrega vai como antes;
- **a revisão** é uma função pura, montada na raiz de composição: os serviços não importam adaptadores (princípio 3). Ela recusa a constituição, uma ADR aceita mudada, um teste apagado ou a menos, uma verificação desligada e uma palavra da lista proibida (`privado/palavras-proibidas.txt`, que o adaptador lê se existir);
- **o `make aplicar PEDIDO=N`** confere de novo e cria o ramo `dev/pedido-N` com o patch, numa worktree temporária: o checkout de quem roda não muda.

A sessão do dev-script é fixa: ler o README, registrar o pedido em `docs/oficina/pedido-NNN.md`, ver as mudanças e pronto. A mente, na parte 3, troca a sessão fixa pela dela.

## Adendo (15/nov, à noite): a mente com rotina, a primeira versão

A parte 3 começou pelo que deixa o dev pensar de verdade no escritório. Três pontos saíram mais simples que o plano:
- **A logística fica com a rotina.** Pegar o pedido, sentar, as pausas, o almoço, entregar e avisar são o dev-script, de graça. O modelo pensa em duas coisas: o trabalho do pedido e a conversa.
- **O trabalho é uma sessão própria** (`WorkSession`, em `libs/mind`): uma conversa com o modelo, com as oito ferramentas da oficina e o pedido do quadro, separada da janela das decisões. Ela corre em segundo plano enquanto o dev aparece trabalhando na mesa (o `work` em blocos e, depois do tamanho simulado do pedido, sentado, pensando). No `pronto`, o patch é revisado e a entrega sai na hora, sem esperar um pedido de decisão (`propose_now`). Uma entrega com patch não precisa do tempo simulado.
- **A fala é uma chamada curta:** quem fala com o dev recebe a resposta do modelo, com o que ele está fazendo; se o modelo falha, a rotina responde.

**O controlador é um só para o kernel** (`llm`). A rotina precisa da foto inteira e o `llm` recebe deltas: a foto é refeita dos deltas (`apply_delta`, em `libs/world-view`).

**O orçamento:** a sessão leva o `ticket_id` em cada chamada, e a guarda soma por pedido. A mente escuta o sinal de vida da guarda (`live.budget`): o teto do pedido para a sessão entre um passo e outro; o do dia ou do total, ou a guarda calada por 15 s, desliga a mente. O dev diz uma vez "Fiquei sem bateria: não consigo mais programar hoje.", e a rotina conduz. Com o teto subido, a mente volta.

**Ficam para depois:** a mente sem os textos da fazenda e a revisão da manhã (a memória do escritório), a prova de conformidade dos cinco modelos e as fitas do escritório, que chamam a API e pedem o ok do usuário.

