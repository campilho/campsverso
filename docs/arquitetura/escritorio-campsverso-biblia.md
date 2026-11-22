# Bíblia do escritório do Campsverso

*A v0.4 (ADR-0077), o M23 (ADR-0078); as mãos do dev, no M26 (ADR-0089); o Tiago e o gerente Camps (ADR-0092). As regras e os números do escritório: o gênero `office` e o cenário `office_campsverso`. Os dados ficam em `cartridges/office/sim/.../data/office.yaml` (o gênero) e `cartridges/office_campsverso/sim/.../data/escritorio.yaml` (o cenário); se este texto e os dados discordarem, valem os dados, e o texto se corrige.*

## 1. O que é

Um escritório de programação em tempo real. Um dev de IA, o Tiago, mora nele; um humano entra como o gerente, o Camps, escreve os pedidos no quadro, conversa com o dev e aceita ou devolve o que ele entrega. Não há regra oculta: a medida é o pedido (ADR-0077).

## 2. O tempo

| | |
|---|---|
| Tick | 250 ms (ADR-0081; os 2 s da medida do M23 faziam o clique esperar até 2 s a 1×) |
| Relógio | o de São Paulo, a 1×; ao subir, o mundo salta até agora (`clock.anchor: wall`) |
| Dia | começa às 00:00 (o dia do calendário) |
| Fases | madrugada 00:00, manhã 06:00, tarde 12:00, noite 18:00 |
| Expediente | de segunda a sexta, das 09:00 às 18:00 |
| Almoço | das 12:00 às 13:00, na copa (ADR-0080; até o M23, fora do escritório) |
| Feriados | os nacionais, na lista do cenário |

O escritório vivo é o mundo `office-campsverso-01` (`make escritorio`). O `office-campsverso-teste` (modo máximo, com o gerente-script) serve aos testes e ao soak, e o `office-campsverso-demo` começa numa segunda às 08:59, para ver o dev em qualquer dia.

## 3. A sala

Uma sala de 20 × 14 tiles com as paredes, e o corredor embaixo, em duas linhas (o mapa tem 20 × 16), na planta da arte nova (ADR-0082; a prévia em `docs/design/escritorio-arte/escritorio-arte.html`).

| Coisa | Tile | Tipo |
|---|---|---|
| Quadro dos pedidos | (3, 1), na parede do fundo; o desenho vai das colunas 2 a 5 | `board` |
| Os quatro cubículos | divisórias nas linhas 3 e 7 (colunas 2 a 10) e nas colunas 2, 6 e 10 | o tile `partition`, que não deixa passar; abertos para o sul |
| Mesa do Tiago | (4, 4), no cubículo de cima à esquerda; o desenho vai de 3 a 5 | `desk`, bloqueia; `dono: tiago` |
| Cadeira do Tiago | (4, 5) | `chair` |
| As outras mesas e cadeiras | (8, 4) e (8, 5); (4, 8) e (4, 9); (8, 8) e (8, 9) | `desk` e `chair`, vazias |
| Arquivos | (12, 2) e (13, 2) | `file_cabinet`, bloqueiam |
| Sala de descompressão | o tapete de (14, 3) a (18, 6), a TV em (16, 2), o sofá em (16, 5) e os pufes em (14, 3), (18, 3) e (18, 5) | `rug`, `tv`, `sofa` e `puff` |
| A copa | a lixeira (12, 9), a máquina de café (13, 9), a pia (15, 9), o micro-ondas (16, 9), a geladeira (17, 9) e o bebedouro (18, 9) | `trash`, `coffee_machine`, `copa_counter`, `microwave`, `fridge` e `water_cooler`, bloqueiam |
| As mesinhas da copa | (13, 11) e (17, 11), com as cadeiras de lado em (12, 11), (14, 11), (16, 11) e (18, 11) | `copa_table`; `copa_chair`, com a `virada` |
| O banheiro | o bloco de (1, 11) a (4, 13), com as portas em (2, 13), masculino, e (3, 13), feminino | `restroom` e `restroom_door`; as portas dão para o corredor, e quem entra some |
| Plantas | (1, 2), (1, 7) e (18, 7) | `plant`, bloqueiam |
| Porta | (9, 13) | `door` |
| Interruptor | (10, 13), na parede à direita da porta; quem está ao lado dele, de dentro da sala ou do corredor, acende e apaga | `light_switch`; `acesa` (ADR-0088) |
| Posto do vigia | (11, 14), no corredor, ao lado da porta | |
| Entrada | (9, 15) | o tile do corredor por onde todos entram e saem |

Andar: 4 tiles por segundo na tela, em qualquer escala; o kernel converte pela escala do momento (ADR-0079). A 1× é um tile por tick de 250 ms; a 72×, andar até o quadro custa uns 2 minutos do mundo. A percepção vê a sala inteira.

## 4. O elenco

| Quem | Papel | Controlador padrão | Aceita | Quando está |
|---|---|---|---|---|
| Tiago | `dev` | `script/dev` | `llm`, `script`, `replay`: nunca um humano | no expediente, e convocado fora dele (ADR-0086) |
| Camps, o gerente | `gerente` | `script/gerente-fora` (fora do escritório) | `human`, `script`, `replay` | enquanto alguém o assume; entra pela porta e sai quando é devolvido |
| Vigia | `vigia` | `script/vigia` | `script`, `replay` | sempre que o dev não está: à noite, no fim de semana e nos feriados (não no almoço, nem com o dev convocado) |

A cadeira do jogador é o gerente (`player: gerente`): a tela do jogador o assume, e o gateway recusa qualquer outro avatar.

**Os nomes** (ADR-0092): desde 22/nov, o dev é o Tiago (id `tiago`), e o gerente se chama Camps, de blazer; o id dele continua `gerente`, a cadeira do jogador. Até então, o dev era o Camps (id `camps`), no mundo `office-campsverso-01`, que ficou no arquivo; o escritório vivo é o `office-campsverso-02`.

**A convocação** (ADR-0086): fora do expediente, entre 08:00 e 23:00, o gerente convoca o dev, só de entrar no escritório (uma vez por visita) ou pelo botão "Convocar" do painel.
- O dev chega pela porta 2 minutos depois e fica até ser dispensado, até o gerente sair, até 6 horas, até as 23:00 ou até o expediente começar, que o assume.
- O vigia sai enquanto ele está.
- Os números ficam em `office.schedule.on_call`, e cada dev do elenco pode ter o próprio acordo.

## 5. O pedido

Uma entidade `ticket` guardada no quadro, com os atributos:

| Atributo | O que é |
|---|---|
| `numero` | a ordem em que foi escrito |
| `titulo` | até 80 caracteres |
| `descricao` | até 1.000 |
| `aceite` | o teste de aceite, o "pronto quando": até 500 |
| `tamanho` | P, M ou G: 15, 60 ou 180 minutos de trabalho simulado (no M23, só o dev-script) |
| `estado` | `a_fazer`, `fazendo`, `entregue` ou `aceito` |
| `autor`, `dono` | quem escreveu e quem está fazendo |
| `trabalho` | os segundos de trabalho já feitos |
| `comentario` | o que o gerente disse ao devolver |
| `maos`, `modelo` | quem programa e com que modelo, escolhidos na prancheta (ADR-0089); sem escolha, valem os do mundo |

## 6. As ações

| Ação | Quem | Onde | Duração | O que faz |
|---|---|---|---|---|
| `say` (do kernel) | todos | qualquer lugar | 2 a 12 s, pelo tamanho | fala até 280 caracteres, para alguém (`to`) ou para quem estiver perto |
| `write_ticket` | gerente | ao lado do quadro | 20 s | escreve um pedido |
| `take_ticket` | dev | ao lado do quadro | 4 s | pega o pedido mais antigo a fazer, ou o escolhido; um de cada vez |
| `work` | dev | ao lado da mesa | o que falta, ou um bloco (`seconds`) | trabalha; `partial`: parar guarda o feito |
| `deliver` | dev | ao lado da mesa | 6 s | entrega o pedido terminado |
| `accept_ticket` | gerente | ao lado do quadro | 6 s | aceita o entregue |
| `return_ticket` | gerente | ao lado do quadro | 10 s | devolve com o comentário; o pedido volta a "a fazer" e o trabalho recomeça |
| `drink` | todos | ao lado do bebedouro | 30 s | uma pausa da rotina, ilustrativa (ADR-0080) |
| `coffee` | todos | ao lado da máquina de café | 2 min | um café, ilustrativo |
| `restroom` | todos | ao lado da porta do banheiro, no corredor | 4 min | some atrás da porta, ilustrativo |
| `fridge` | todos | ao lado da geladeira | 15 s | pega o almoço (ADR-0082) |
| `microwave` | todos | ao lado do micro-ondas | 90 s | esquenta o almoço |
| `lunch` | todos | ao lado da mesinha da copa | até as 12:55 | come, só na hora do almoço; os 5 minutos do fim são para jogar fora e voltar |
| `trash` | todos | ao lado de uma lixeira | 5 s | joga fora o resto; entre a geladeira e o lixo, o avatar carrega a marmita (`carregando`) |
| `tv` | todos | no tapete, logo acima ou abaixo do sofá | 10 min | vê TV sentado no sofá (ADR-0082) |
| `videogame` | todos | no tapete, logo acima ou abaixo do sofá | 15 min | joga videogame sentado no sofá; a rotina joga uma partida por dia, à tarde |
| `light_on`, `light_off` | todos | ao lado do interruptor | 2 s | acende ou apaga a luz da sala; recusada se ela já está assim (ADR-0088) |

**A luz da sala** (ADR-0088): o temporizador do prédio acende às 18:00 e apaga às 21:00 (`lights` no `office.yaml`); no meio e depois, quem está na sala manda no interruptor. De dia, a tela não muda; à noite, desenha as luminárias com a luz acesa e o escuro com ela apagada, com a lanterna do vigia por cima.

Fora do papel, a ação é recusada (`not_allowed`); longe do lugar, `not_adjacent`. As pausas são de qualquer um: o gerente do humano as encontra no menu de cada coisa (ADR-0082).

## 7. Os eventos

`campsverso.office.ticket.created.v1`, `taken`, `delivered`, `accepted` e `returned`, a luz (`campsverso.office.light.switched.v1`, com quem mexeu ou, sem `by`, o temporizador; ADR-0088), mais a fala (`campsverso.avatar.spoke.v1`) e a entrada e a saída de cada um (`avatar.entered` e `avatar.left`, com os motivos `expediente`, `plantao`, `possessed` e `released`; `almoco` só quando o almoço é na rua). Falar com alguém (`say` com `to`) interrompe a ação dele, que decide de novo (`action_interrupted`; ADR-0080).

## 8. Os scripts

- **O dev-script**, a linha de base:
  - responde a quem falou com ele ("Bom dia!" na primeira vez do dia, "Anotado." depois);
  - cumprimenta o gerente quando ele chega;
  - pega o pedido mais antigo e avisa;
  - trabalha em blocos de um minuto, entrega e avisa;
  - avisa o almoço e almoça na copa, das 12 às 13, mesmo com um pedido em andamento, em quatro etapas: a geladeira, o micro-ondas, a mesinha (sentado na cadeira de lado) e o lixo (ADR-0082);
  - sem pedido, segue a rotina (ADR-0080): as pausas do dia, num sorteio pelo dia (dois cafés perto das 10:00 e das 15:30, água a cada uns 100 minutos, o banheiro duas vezes), e a cadeira da mesa no resto. As pausas são ilustrativas e não pesam no trabalho.
- **O vigia:** faz a ronda nos 10 primeiros minutos de cada hora e passa o resto de pé no posto, no corredor, ao lado da porta. A luz (ADR-0088): quando falam com ele sobre a luz (com a menção, ou dizendo "vigia"), responde ("Já vou acender a luz.") e vai ao interruptor; na ronda, apaga a sala vazia.
- **O gerente-script** (só nos testes e no soak):
  - escreve três pedidos por dia, às 09:30, 10:30 e 14:00;
  - cumprimenta o dev;
  - aceita os entregues e devolve um de cada três, na primeira entrega.

## 9. As mãos do dev

O dev programa na oficina por uma de duas mãos (ADR-0089), atrás da mesma porta (`HandsPort`):
- **o nosso harness:** a sessão da mente, com as oito ferramentas da oficina (`api`);
- **o Claude Code:** pelo Claude Agent SDK, no mesmo espaço, com as ferramentas dele (`claude_code`).

**A escolha:**
- **Na prancheta,** o pedido escolhe quem programa e o modelo, dentro das listas do `office.yaml` (`hands` e `models`): o Sonnet 5.5, o Opus 5.5 ou o Fable 5.2.
- **Sem escolha,** valem as do mundo (`minds.<dev>.hands` e `model`). No escritório vivo, desde 22/nov, é o Claude Code com o Opus 5.5, a recomendação da comparação das mãos (`docs/arena/m26-as-maos.md`). Sem a chave da Anthropic, vale o nosso harness.

**A sessão:**
- **O briefing abre a sessão** nas duas mãos (a criação do M25).
- **Ela termina** em 80 voltas, US$ 4 ou 45 minutos, o que vier primeiro.
- **Cada chamada ao modelo** passa pela porta das mãos, que põe a chave, mede o custo e recusa acima do teto. O teto é de US$ 5 por pedido e US$ 10 por dia (`budget`, no mundo).
- **O isolamento:** o Claude Code só escreve no espaço do pedido. Ele não lê o `.env`, o `privado/` nem o `data/`, e só fala com a rede pela porta.

**Na tela:**
- os passos das duas mãos (`workshop.step.v2`) e o fim da sessão (`workshop.session_finished.v1`), com o motivo, as voltas, o custo e o tempo;
- **o último passo,** sobre o dev, no lugar da barra;
- **os marcos na conversa:** o começo, cada robô chamado e o fim;
- **a tela da sessão,** que o gerente abre pelo chip do dev: o pedido, as mãos e o modelo, o tempo, os passos, o custo e os últimos passos, um por linha.

## 10. As métricas do dia

Os pedidos escritos, entregues, aceitos e devolvidos; os segundos de trabalho entregues; as falas.
