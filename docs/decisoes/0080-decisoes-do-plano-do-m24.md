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

## Adendo (16/nov): a memória do escritório

**A mente sem a fazenda (§2.2) ficou menor.** Com a mente com rotina, o modelo não escolhe os passos do dev: a janela de decisões e as ferramentas do catálogo nunca chegam a ele no escritório. O que precisava sair da fazenda era só a memória (ADR-0060).

**O perfil da memória** (`MemoryProfile`, em `libs/mind`) é o que a memória tira do pacote de mente do cartucho (`memoria.yaml`), e não mais da fazenda:
- a duração do tick, para dar a hora de cada acontecimento: o relógio da memória contava um minuto por tick, e o do escritório é de 250 ms;
- o peso e a linha legível de cada evento, inclusive a do próprio avatar ("peguei o pedido 3", "eu disse: …");
- o que é ruído: as ações da rotina (andar, trabalhar no relógio, as pausas, o almoço) e os eventos que o pedido já conta melhor (o progresso do trabalho, o pedido como coisa no mundo);
- se guarda os lugares vistos: numa sala sem raio, não;
- os textos e a ferramenta da revisão, e a ferramenta de anotar.

O perfil padrão é a fazenda, byte a byte: os testes da memória e as fitas do CI passam sem mudança.

**A revisão da manhã (§2.3):**
- **Quando:** na primeira decisão de cada dia do mundo. O dev só decide dentro da sala, então é a chegada.
- **O que revê:** os dias com episódios desde a última revisão, até três. A segunda revê a sexta, e o fim de semana, sem episódios, não conta.
- **Uma chamada só,** com a ferramenta `revisar`: o resumo, o plano do dia e as lições, que são as crenças da porta de memória, sobre o repositório, o gerente e o jeito de trabalhar. A revisão fica guardada no dia mais novo, e o evento `memory.reflected.v1` ganha o campo opcional `days`.
- **Em segundo plano:** a rotina segue andando, e a sessão de um pedido espera a revisão acabar, por até 2 minutos, para ter o plano.
- **Se falhar,** o dia segue sem ela, e ela volta no dia seguinte, com os dias que faltam.
- **Na fazenda nada muda:** ela continua refletindo ao dormir.

**O que o dev guarda e onde a memória aparece:**
- cada entrega vira episódios, pelo perfil, e cada sessão na oficina vira uma linha (os passos, o que saiu, os últimos testes);
- a ferramenta `anotar` na sessão é de graça: a mente guarda a nota, e a oficina nem a vê;
- a memória abre a sessão, antes do pedido, e vai junto na conversa.

**Ligada** no mundo de demonstração e no escritório vivo, num arquivo por avatar fora do snapshot, como na fazenda.

**A sessão paga (16/nov, com o ok do usuário)** achou três defeitos, consertados em seguida:
- **A foto da percepção apagava o meio-tempo.** A cada 20 deltas, a percepção manda a foto inteira, e a foto não levava o que aconteceu desde a entrega anterior: a devolução do pedido nunca chegou à memória do dev. Agora o mundo pode pedir que a foto leve os eventos (`perception.snapshot_events`; o campo opcional `events` no `perception.delivered.v1`). O escritório pede. A fazenda segue sem eles, porque com eles os pedidos ao modelo mudariam e as fitas não valeriam mais.
- **As ações do gerente viravam "fiz".** Num mundo com mais de um avatar à vista, o `action.completed` de outro avatar chegava à memória como se fosse do dev ("fiz accept_ticket"). O perfil diz agora se as ações dos outros contam (`others_actions`); no escritório, não, porque o pedido conta o que o gerente fez.
- **A memória de um sandbox ia para o `data/` do repositório,** e não para a pasta do sandbox. Ela passa a seguir o `--data-dir`, como a oficina. Isso também vale para a fazenda: um sandbox antigo retomado depois deste conserto começa sem a memória que tinha.

## Adendo (16/nov, à noite): a prova de conformidade

A ferramenta `make conformidade` (`campsverso_testkit.conformidade`) faz, com cada modelo, dois pedidos curtos num repositório de exemplo: escrever um arquivo com o teste e consertar um defeito que faz um teste falhar, sem mudar o teste.
- **O caminho é o do escritório:** a sessão da oficina, as instruções e o cartão do dev, as ferramentas da oficina e a de anotar, e a memória vazia na abertura.
- **A correção é por fora:** os testes de novo, um teste escondido e a revisão da oficina.
- **Os limites são os da decisão 11 da ADR-0077:** nenhuma recusa, até 5% de respostas sem ação e até dois erros de formato.

**Os cinco passaram, por US$ 0,36 no total,** sem nenhuma resposta sem ação, recusa, erro de formato ou chamada falha. O relatório está em `docs/arena/conformidade-2026-11-16.md`.

**O Fable é o 5.2,** o atual, a US$ 8 e 40 por milhão de tokens, no lugar do 5.1 da arena do M21.

**A criação (decisão 14) fica com o Sonnet 5.5.** Ele e o Opus acertaram tudo; o Sonnet fez em 14 respostas contra 17, em 15 s contra 23 s, e por US$ 0,028 contra 0,066. A prova não ordena qualidade: se a criação mostrar que falta fôlego, o Opus é a troca.

**Ficam para depois as fitas do escritório no CI:** os resultados da oficina trazem o tempo dos testes ("1 passou (1,2 s)"), e o pedido seguinte ao modelo muda a cada execução. Uma fita que o CI reproduza pede esse tempo fora do texto que volta ao modelo.

## Adendo (16/nov, à noite): a bancada, o registro de robôs e o ver o patch

A parte 4 começou pelo que a criação precisa antes do pedido do testador.
- **O ver o patch:** o pedido entregue tem o botão "Ver o patch", com os arquivos, as linhas a mais e a menos e o diff. O gateway serve o depósito de entregas só para leitura, e só `.patch` e `.json` (`/content/entregas/<chave>`).
- **A bancada:** volta à sala no cubículo ao lado do dev, no lugar da mesa vazia de (8, 4), e a cadeira desse cubículo sai. A arte veio do Claude Design na mesma noite (o pedido em `docs/design/briefing-arte-bancada.md`): a bancada com o painel de ferramentas e o osciloscópio, e três robôs de mesa de um corpo-base (o testador, o revisor e o publicador). Cada robô fica no apoio dele, 22 px acima do chão, com a luz da antena piscando; a variante sai do nome.
- **O registro de robôs:** a lista `robos:` no `escritorio.yaml` do cenário, que começa vazia. Cada linha (o nome, o módulo Python e a descrição) põe um robô num dos três apoios da bancada, como uma entidade `robot` com o módulo nos atributos. O cartucho recusa um nome fora do formato, um nome repetido, um módulo que não é módulo Python e mais de três robôs.
- **A ferramenta `chamar_robo`:** a mente a oferece só quando há robô na bancada, com os nomes deles no enum e o que cada um faz na descrição. O robô roda pela porta da oficina (`run_robot`): `python -m <módulo> <argumentos>` no espaço do pedido, sob o mesmo `sandbox-exec` dos testes, sem rede e sem escrever fora dele, até o mesmo limite de tempo. A saída volta até 60 linhas.
- **O evento novo, `workshop.robot_called.v1`,** e não um valor novo no enum de ferramentas do `workshop.step.v1`, o que seria incompatível. A arte já tem as animações de trabalhando, passou e falhou, e a mesa do dev os quadros de ler e dos testes; ligá-las pede um campo no estado da tela, que fica para o fechamento do M24.
- **As notas do escritório** contam ao dev onde fica a bancada e como pôr um robô novo nela.


## Adendo (18/nov): o monitor e o robô seguem a oficina, e os invariantes do soak

O que ficou para o fechamento, sem API:
- **O robô trabalha enquanto roda:** o `robot_called.v1` só sai quando o robô termina, e a tela não tinha como mostrá-lo trabalhando durante a chamada, que pode levar até 60 s. Entra o tipo novo `workshop.robot_started.v1` (o robô e os argumentos), publicado antes de ele rodar.
- **A oficina no estado da tela:** a projeção do gateway lê os eventos `workshop.*` do stream observer, como o caderno e o custo, e o estado (`state.workshop`, opcional) leva:
  - o último passo de cada dev: a ferramenta, se deu certo e o tick;
  - a última chamada de cada robô: rodando, passou ou falhou.

  Vai para as duas visões, porque o gerente vê a sala. Um passo depois de um robô que começou e não terminou (o processo caiu no meio) o devolve ao parado.
- **O desenho, por dados:** cada tipo de coisa diz no `art.json` de quem é o estado (`workshop.of`) e o quadro de cada estado.
  - **A mesa do dev (`owner`)** mostra o último passo do dono dela (o atributo `dono`) enquanto ele está sentado nela: lendo, escrevendo, os testes verdes ou vermelhos. O `pronto` devolve o monitor ao de sempre. Um passo vale por até 2 horas do mundo, porque a 72× uma chamada lenta ao modelo passa de meia hora.
  - **O robô (`self`)** trabalha entre o começo e o fim da chamada e mostra o resultado por 15 minutos do mundo.
  - **A bancada (`any`)** liga o osciloscópio enquanto algum robô trabalha.
- **Os invariantes do escritório** (`campsverso_testkit.escritorio`), conferidos nos fatos do kernel pelo `make soak` num mundo do escritório, que os mostra no lugar das métricas da fazenda, e pelo teste de um dia:
  - todo pedido de dia de expediente entregue;
  - em cada dia de expediente, ao menos uma pausa do dev (água, café ou banheiro) e o almoço;
  - nenhuma ação da copa fora do expediente.
- **O "ver o patch" no navegador:** o teste do escritório abre o patch da entrega do dev-script (a sessão fixa dele na oficina registra o pedido num arquivo), entre a entrega e o aceite.
