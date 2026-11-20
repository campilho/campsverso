# Plano do M24 — O dev pensa e cria

*Proposto em 15/nov/2026, depois do fechamento do M23 (ADR-0078 e ADR-0079). **Aprovado em 15/nov/2026 como recomendado, com duas ressalvas do usuário (ADR-0080):** as pausas são só ilustrativas, feitas por uma rotina que não custa nada; e o orçamento estourado desliga a mente, e a rotina assume. É o segundo marco da v0.4 (ADR-0077): a mente chega ao dev do escritório e ele passa a trabalhar de verdade, num espaço de trabalho isolado, com a entrega num patch que o humano aplica. Entra também o que o usuário pediu em 15/nov: a copa e as pausas.*

**Pronto quando:**
- **A mente:** o dev pensa com um modelo pelo nosso harness: o Haiku, o Sonnet, o Opus ou o Fable pela API, e o Astra pela OpenRouter. O script fica de reserva, e cada modelo passou na prova de conformidade.
- **A oficina:** o dev trabalha num espaço de trabalho isolado: lê, busca, escreve e roda os testes. Ali não há rede, `.env`, `data/` nem `privado/`.
- **A entrega:** é um patch, conferido contra a constituição e as palavras proibidas, que o humano aplica.
- **A primeira criação:**
  - você pede o testador no quadro, e o dev o faz;
  - o testador passa no teste de aceite, e o humano aplica;
  - ele aparece na bancada como o primeiro robô, e o dev passa a chamá-lo.
- **A mente com rotina:**
  - o modelo só é chamado quando há trabalho;
  - sem trabalho, uma rotina determinística conduz o dev de graça: o café, a água, o banheiro e o almoço na copa;
  - trabalhando num código, ele fica sentado na mesa.
- **A fala:** falar com o dev interrompe o que ele faz, e ele responde.
- **O orçamento:**
  - há teto por dia e por pedido, que muda com o mundo vivo;
  - estourar desliga a mente: a rotina assume, o dev avisa que não pode mais programar, e o escritório segue.
- **A fazenda intacta:** os soaks e as fitas da fazenda continuam iguais.

## O que o levantamento mostrou

- **A mente** (`libs/mind`) é genérica na estrutura:
  - o cartão, as notas e as ferramentas vêm do pacote de mente do cartucho;
  - cada ação do catálogo vira uma ferramenta;
  - a janela de conversa transforma cada mudança do mundo no resultado da ferramenta anterior.
- **Mas o texto tem a fazenda dentro:**
  - "ticks de um minuto" nas instruções;
  - "Dura N minutos" nas ferramentas;
  - o relógio da memória em minutos;
  - a nota que fala de fome, moedas e canteiro;
  - "Você acordou." para o `woke_up`, que o escritório usa para a entrada na sala;
  - a reflexão "da noite, nesta fazenda".
- **A reflexão depende de dormir.**
  - Ela dispara pela ação `sleep`, que o escritório não tem, ou pela primeira decisão do dia seguinte, olhando só a véspera.
  - Fora da sala, o kernel não pede decisões ao dev. Então a sexta-feira e a véspera de feriado nunca seriam revistas.
- **O escritório não tem pacote de mente,** nem `minds:` e `budget:` no arquivo do mundo. As ferramentas de teste da mente (`make corrida`, `make fita`) só conhecem as fazendas.
- **Nada fala com o dev:**
  - não existe um motivo de decisão para a fala;
  - a ADR-0078 adiou a mudança no enum do `decision_requested`, que seria incompatível.
- **Os parâmetros das ferramentas são todos obrigatórios,** só de texto ou número.
- **O orçamento** tem teto por dia simulado e no total. Ele não tem teto por pedido nem comando para mudar o teto, e ao estourar pausa o mundo inteiro.
- **As necessidades** do kernel servem para as pausas:
  - a taxa por hora e o limiar que pede decisão;
  - o gerador de números aleatórios por nome, que vai no snapshot;
  - o `add_need_modifier`.
  - A taxa precisa render um número inteiro por tick: com o tick de 2 s, são múltiplos de 15 por hora.
- **Não existe código para agir fora do mundo:** nem espaço de trabalho, nem ferramenta de arquivo ou de teste. A "oficina" só existe na ADR-0055 e no `futuro.md`.

## 1. O mundo do dev

### 1.1 A rotina e a copa

As pausas são ilustrativas: não pesam no trabalho do dev (ressalva do usuário, ADR-0080).

- **A rotina** é um script determinístico que conduz o dev quando a mente não tem o que fazer (§2.5). Ela não custa nada.
- **O que a rotina faz:**
  - fica na mesa, sentado;
  - vai ao bebedouro, faz um café na copa e vai ao banheiro;
  - almoça na copa.
  - Os horários saem de um sorteio pelo dia, sempre o mesmo para o mesmo dia.
- **As ações novas,** baratas e sem efeito no trabalho:

  | Ação | Onde | Duração |
  |---|---|---|
  | `drink` | ao lado do bebedouro | 30 s |
  | `coffee` | ao lado da cafeteira da copa | 2 min |
  | `restroom` | ao lado da porta do banheiro: o dev sai pela porta e volta | 4 min |
  | `lunch` | na mesa da copa | até as 13h |

- **Sem necessidades no kernel:** nada de sede ou café que suba e cobre um preço. Os tempos, os lugares e a frequência das pausas são dados do cenário.
- **O dev-script de hoje** continua com o trabalho simulado, para os mundos sem mente, os testes e o soak. A rotina é a parte dele sem os pedidos, mais as pausas.

### 1.2 A copa e o almoço

- **A copa fica num canto da sala:**
  - a geladeira, o micro-ondas, a pia, a cafeteira e uma mesa com duas cadeiras;
  - a porta do banheiro na parede ao lado.
- **O mapa cresce.** O lugar exato sai com a arte: o teste do Claude Design já tem as peças, e sem ele usamos peças LPC de cozinha.
- **O almoço passa a ser na copa,** das 12 às 13, pela rotina. O dev não sai mais pela porta.
- **No meio de um trabalho ao meio-dia,** o dev almoça quando a sessão acabar, até as 13h.
- **No arquivo do cenário,** o almoço é na `copa` ou na `rua`, como hoje.

### 1.3 A fala que interrompe

- **Quando alguém fala com o dev** (`say` com `to: camps`), o kernel interrompe a ação dele, se o cartucho declarar `interrupt_on_speech`.
- **O dev recebe um pedido de decisão** com o motivo que já existe, `action_interrupted`. A fala chega junto, na mudança do mundo.
- **O trabalho é `partial`,** então o progresso fica guardado.
- **Nenhum contrato muda.** A alternativa era um `decision_requested.v2` com um motivo novo, e todos os consumidores mudariam juntos.
- **Para o dev-script nada muda:** ele já responde entre um bloco de um minuto e outro.
- **Na rotina,** a fala é trabalho para a mente: o gerente fala com o dev na copa, e a mente assume para responder (§2.5).

## 2. A mente no dev

### 2.1 Os pacotes da mente

- **`cartridges/office/mind`, o gênero:**
  - as notas do escritório: o expediente, o quadro e os pedidos, a copa e as pausas, a oficina e a bancada;
  - as descrições das ferramentas do mundo: pegar, trabalhar, entregar, falar, andar, esperar, beber, café, banheiro e almoçar.
- **`cartridges/office_campsverso/mind`, o cenário:** o cartão do Camps no escritório, com o ponto de entrada `camps_escritorio`. Ele é o líder técnico e o único dev, conhece o repositório e responde ao gerente.
- **O princípio 5 continua:** o cartão e as notas não contam nada que o mundo esconde. O escritório ainda não tem regra oculta.

### 2.2 A mente sem a fazenda

- **O tempo:** a duração do tick, o "Dura N minutos" e o relógio da memória saem do relógio do cartucho, em segundos e minutos.
- **Os textos passam ao pacote de mente do cartucho:**
  - a descrição da nota;
  - os textos dos motivos (o `woke_up` vira "você chegou ao escritório");
  - as palavras da reflexão;
  - a tabela de importância dos episódios.
- **As fitas da fazenda continuam valendo.** Os textos da fazenda ficam iguais, byte a byte, e um teste confere que o pedido ao modelo não mudou.

> **Como ficou** (16/nov; o adendo da ADR-0080): com a mente com rotina, a janela e as ferramentas do catálogo não chegam ao modelo no escritório. O §2.2 se resumiu à memória: um perfil por cartucho (`memoria.yaml`) com o tick, os pesos, as linhas, o ruído e a revisão.

### 2.3 A revisão do dia

- **A reflexão vira a revisão da manhã:** quando o dev chega, ele revê os dias de trabalho que ainda não revisou. É como a reunião rápida do começo do dia.
- **Ela cobre o fim de semana e o feriado:** olha para trás até o último dia revisto, e não só a véspera. O limite é de três dias, para o custo.
- **Na fazenda nada muda:** ela continua refletindo ao dormir.

### 2.4 Os modelos e a prova de conformidade

- **A prova** vem antes de cada modelo (decisão 11 da ADR-0077).
  - São dois pedidos curtos, num repositório de exemplo: escrever um arquivo pequeno e corrigir um teste quebrado.
  - Os limites: nenhuma recusa, no máximo 5% de respostas sem ação e no máximo dois erros de formato.
- **Os cinco modelos:**
  - pela API: o Haiku 5.5, o Sonnet 5.5, o Opus 5.5 e o Fable;
  - pela OpenRouter: o Astra.
- **A criação** (§4) fica com o melhor da prova entre o Sonnet e o Opus.
- **As fitas do escritório** (`make fita CARTUCHO=office_campsverso`) gravam um dia com o repositório de exemplo, e o CI só as reproduz.

> **Como ficou** (16/nov; o adendo da ADR-0080): os cinco passaram na prova (`make conformidade`), o Fable no 5.2, por US$ 0,36. A criação fica com o Sonnet: acertou como o Opus, em menos passos e pela metade do custo.

### 2.5 A mente com rotina

É uma versão híbrida do nosso harness: o modelo pensa quando há trabalho, e a rotina conduz o resto (ressalva do usuário, ADR-0080).

- **Há trabalho para a mente** quando:
  - há um pedido no quadro a fazer;
  - há um pedido dele em andamento ou devolvido;
  - há uma entrega a avisar;
  - alguém falou com ele.
  - Quem decide é uma função do cenário que lê a foto.
- **Sem trabalho,** a rotina decide, de graça.
- **Um controlador só para o kernel:** o avatar continua com o controlador `llm`, e a troca é por dentro. Cada proposta leva a intenção, e as da rotina começam com "rotina:".
- **A tela mostra quem conduz:** "pensando (Sonnet)" ou "rotina".
- **O custo de um dia a 1×** cai muito: o modelo não é chamado para esperar, sentar ou tomar café.
- **A reserva continua:** três falhas seguidas do modelo devolvem o dev ao dev-script, como na fazenda.

## 3. A oficina

### 3.1 A porta e o adaptador

- **A `WorkshopPort`** fica em `libs/ports`. É a porta de efeitos externos da ADR-0055 e o que o princípio 3 pede. Ela abre um espaço de trabalho por pedido e o fecha na entrega.
- **O adaptador local** fica em `libs/adapters`. Ele faz um clone raso do repositório (`git clone --depth 1`) em `data/oficina/<mundo>/<pedido>/`.
  - O clone é isolado: tem o próprio `.git`.
  - Nele não há `.env`, `data/` nem `privado/`, que estão fora do git.
  - Uma worktree dividiria o `.git` com o repositório de verdade.
- **O ambiente Python** do espaço sai do cache do `uv`, sem rede (`uv sync --offline --frozen`).
  - Os testes da tela, que pedem o `node_modules`, ficam para o M26.
  - A criação do M24 é em Python.

### 3.2 As ferramentas da oficina

São ferramentas do computador, e não ações do mundo. A mente as chama durante o trabalho, e o controlador as executa pela porta.

| Ferramenta | O que faz | Limite |
|---|---|---|
| `ver_arquivos` | lista os arquivos de um caminho | 200 nomes |
| `ler` | lê um arquivo, por faixa de linhas | 300 linhas |
| `buscar` | procura uma expressão, num caminho | 50 resultados |
| `escrever` | cria ou troca um arquivo inteiro | 2.000 linhas |
| `editar` | troca um trecho exato, que precisa aparecer uma vez | — |
| `rodar_testes` | roda o `pytest` de um caminho e devolve o resumo: quantos passaram, quantos falharam e as primeiras falhas | 2 minutos e 60 linhas |
| `ver_mudancas` | mostra o diff do espaço de trabalho | 400 linhas |
| `pronto` | encerra a sessão para entregar | — |

- **Cada passo vira um fato,** o `workshop.step.v1`: a ferramenta, o caminho, um resumo de uma linha e a duração. A tela mostra o último passo no monitor da mesa, e o arquivo guarda tudo.
- **O `make` não é ferramenta.** O dev não roda nenhum alvo, e portanto nenhum que chame a API.

### 3.3 O isolamento

- **Os caminhos:** toda ferramenta resolve o caminho e recusa o que sai do espaço de trabalho, inclusive por link simbólico.
- **Os testes rodam sob o `sandbox-exec` do macOS,** o mesmo mecanismo que o Claude Code usa:
  - sem rede;
  - escrita só no espaço de trabalho e numa pasta temporária;
  - um ambiente sem segredos: só o `PATH` e um `HOME` dentro do espaço.
- **O `sandbox-exec` está obsoleto** na documentação da Apple, mas funciona. A saída definitiva é o computador do dev, no M28.

### 3.4 O trabalho no tempo do mundo

- **A mente propõe `work` no pedido,** e a ação dura até uma hora do mundo. Enquanto isso, a mente conduz uma sessão de passos na oficina.
- **A sessão acaba:**
  - quando a mente chama `pronto`, e então o controlador propõe `deliver`;
  - quando alguém fala com o dev, depois do passo em curso;
  - quando um limite estoura: os passos do pedido ou o teto do pedido.
- **O controlador propõe sem esperar um pedido de decisão** quando a sessão acaba. O kernel já aceita isso: é o que a tela do jogador faz.
- **A 1×, a sessão anda no tempo real,** e o dev aparece trabalhando na mesa. No sandbox acelerado, o mundo corre mais que a sessão, e o dev fica na mesa até ela acabar.
- **O tamanho do pedido** (P, M e G em minutos simulados) continua só para o dev-script. Quem entrega um patch não precisa de tempo simulado.

### 3.5 A entrega

- **O patch:**
  - é o diff do espaço de trabalho contra o commit de onde ele saiu;
  - vai para o depósito de arquivos do mundo;
  - leva um resumo: os arquivos, as linhas a mais e a menos, e o commit de base.
- **O `office.ticket.delivered.v1`** ganha o campo opcional `patch`, com a referência e o resumo.
- **O gerente vê o patch no quadro.** A tela busca o arquivo pelo gateway, que só serve a esta máquina.
- **O `make aplicar PEDIDO=N`:**
  - confere de novo o patch;
  - cria o ramo `dev/pedido-N`;
  - aplica o patch;
  - mostra o resumo.
- **O humano revisa, roda o `make check` e decide o commit.** No M25 isso vira o PR.

### 3.6 A constituição e a varredura

- **A entrega é recusada,** e o dev recebe o motivo, quando o diff:
  - toca a constituição: `CLAUDE.md`, `contracts/`, `.github/`, o `Makefile`, `services/budget/`, os tetos em `config/`, as ADRs aceitas e `data/archive/`;
  - apaga um teste ou desliga uma verificação (um `skip` novo, um `noqa`, um `type: ignore`);
  - tem uma palavra da lista proibida.
- **A lista proibida** fica em `privado/palavras-proibidas.txt`, fora do git. O adaptador lê o caminho da configuração local. O `make aplicar` confere tudo de novo.

## 4. A criação: o testador e a bancada

- **O pedido:** você escreve no quadro, como gerente, o título, o que fazer e o teste de aceite. A proposta:
  - **título:** "Testador";
  - **o que fazer:** "Dado um ou mais caminhos do repositório, rodar os testes que cobrem esses caminhos e devolver um resumo curto";
  - **aceite:** "Em até 5 linhas: quantos passaram, quantos falharam, a primeira falha com o arquivo e a linha; e um teste do próprio testador".
- **Onde a criação mora:**
  - o código em `tools/robos/testador.py`, com o teste;
  - uma linha no registro de robôs do cenário (`robos:` no `escritorio.yaml`, com o nome, o comando e a descrição).
- **A bancada:** ao subir, o cenário põe na bancada um robô por linha do registro. A mente ganha a ferramenta `chamar_robo`, que roda o comando do robô no espaço de trabalho, sob o mesmo isolamento, e devolve o que ele diz.

> **Como ficou** (20/nov): o dev-script, o script de reserva, também chama o robô, para o caminho rodar sem modelo. A linha do registro ganhou um campo opcional, `reserva`: os argumentos com que o script o chama antes de entregar. O testador recebe os testes da própria bancada (`tools/robos/tests`), que existem em todo clone e rodam em uns 3 s. O resultado não muda a entrega, porque o script não sabe ler o que o robô disse. No navegador, o teste do escritório vê o testador trabalhando na bancada e depois o verde de "passou".
- **O M25 usa o testador** antes de cada PR.
- **Se o dev não conseguir,** nós fazemos, e a tentativa fica no arquivo como dado (decisão 12 da ADR-0077).

## 5. O orçamento

- **O teto por pedido:**
  - o `llm.call.completed.v1` ganha o campo opcional `ticket_id`, que a mente preenche com o pedido em que está;
  - a guarda soma por pedido, além de por dia e no total.
- **O `cmd.ops.budget.set`:** você muda os tetos com o mundo vivo, pela tela do operador.
- **Estourar** (ressalva do usuário, ADR-0080):
  - no escritório, a mente desliga e a rotina assume;
  - o dev diz uma vez "Fiquei sem bateria: não consigo mais programar hoje.";
  - os pedidos esperam no quadro, e o escritório segue;
  - na fazenda, o mundo continua pausando (`on_exceeded` no arquivo do mundo).
- **A guarda dá sinal de vida** (`live.budget.v1`, como o pulso do kernel; o adendo da ADR-0080). Sem o sinal, a mente desliga do mesmo jeito.

## 6. A tela

- **O monitor da mesa** mostra o último passo da oficina, como "lendo tools/robos/testador.py" ou "rodando os testes: 12 passaram". Com a arte nova, a tela do monitor acende.
- **O painel mostra:**
  - quem conduz o dev: a mente, com o modelo, ou a rotina;
  - o custo do pedido.
- **No quadro,** o pedido entregue tem o "ver o patch": o resumo e o diff.
- **A bancada** mostra os robôs.
- **A copa e a porta do banheiro:** na rotina, o dev entra e some por uns minutos, sem nada desenhado lá dentro.

## 7. Contratos

- **Campos opcionais:**
  - `office.ticket.delivered.v1`: `patch`;
  - `llm.call.completed.v1`: `ticket_id`;
  - ~~`ops.budget.exceeded.v1`: `scope` (dia, pedido ou total)~~: virou o v2, abaixo (o enum do escopo não muda no v1).
- **Tipos novos:**
  - `campsverso.workshop.step.v1`, num domínio novo da plataforma, `workshop`, publicado pelo processo da mente;
  - `campsverso.cmd.ops.budget.set.v1`;
  - `campsverso.live.budget.v1` (no lugar do `ops.heartbeat.v1`), `campsverso.ops.budget.limits_changed.v1` e os avisos `ops.budget.*.v2`, com o escopo do pedido (o adendo da ADR-0080).
- **O `decision_requested` não muda** (§1.3).

## 8. Testes do marco

- **Unidade:**
  - a rotina, igual para o mesmo dia;
  - as ações da copa;
  - a mente com rotina: quando a mente assume e quando a rotina volta;
  - a fala que interrompe;
  - os textos da mente vindos do cartucho, e o pedido da fazenda byte a byte;
  - a revisão que cobre o feriado;
  - o adaptador da oficina num repositório temporário, com o caminho que escapa recusado e a rede negada dentro do `rodar_testes`;
  - a constituição, os testes apagados e as palavras proibidas, com uma lista de teste;
  - o teto por pedido, o `budget.set` e o sinal de vida, com a rotina assumindo.
- **Ponta a ponta, com as fitas:** um dia do escritório com o dev com LLM num repositório de exemplo (`tests/fixtures/oficina/`). O repositório de verdade mudaria as respostas das ferramentas, e a fita deixaria de bater.
- **O soak:** o escritório em 5 dias com o dev-script e a rotina, com os invariantes:
  - todo pedido de dia útil entregue;
  - as pausas acontecem;
  - ninguém na copa fora do expediente.
- **No navegador:**
  - a pausa;
  - a fala que interrompe;
  - o "ver o patch";
  - o robô na bancada.
- **As fazendas intactas:** os soaks com as mesmas métricas e as fitas de sempre.

## 9. Ordem do trabalho, em quatro partes

1. **O mundo, sem API:**
   - a rotina, a copa e o almoço;
   - a fala que interrompe;
   - a mente sem a fazenda;
   - a revisão do dia;
   - o orçamento por pedido, o `budget.set` e o sinal de vida;
   - os contratos.
2. **A oficina, sem API:**
   - a porta e o adaptador, com as ferramentas e o isolamento;
   - a entrega, a constituição e a varredura;
   - o `make aplicar`;
   - o monitor e o "ver o patch".
3. **A mente no dev, com pouca API:**
   - os pacotes da mente e as fitas;
   - a mente com rotina;
   - a prova de conformidade dos cinco modelos;
   - um dia do escritório com o dev com LLM.
4. **A criação, com API:**
   - você escreve o pedido do testador;
   - o dev faz;
   - você aplica;
   - o robô aparece na bancada;
   - o fechamento.

**A arte** corre ao lado: quando o teste do Claude Design chegar, a comparação com a LPC e a sua escolha.

## 10. Custo

- **API, em passos pagos, cada um com o seu ok:**
  - a prova dos cinco modelos: US$ 5 a 10;
  - um dia com o dev com LLM: US$ 5 a 15;
  - a criação: US$ 10 a 30;
  - **total:** US$ 20 a 55, dentro dos US$ 30 a 60 do plano macro.
- **O Claude Code:** um marco maior que o M23, que levou dois dias.

## 11. Riscos

- **O `sandbox-exec` está obsoleto.** *A resposta:* ele funciona e é o que o Claude Code usa. O M28 traz o computador do dev.
- **A sessão da oficina a 1× é um laço aberto.** *A resposta:* o limite de passos, o teto por pedido e o sinal de vida.
- **As fitas e o repositório de verdade.** *A resposta:* o repositório de exemplo nos testes.
- **O dev não consegue o testador.** *A resposta:* nós fazemos, e a tentativa é dado.
- **O escopo.** *A resposta:* o que não couber vai para o `futuro.md`, como o escritório 2.

## 12. Decisões

1. **Quatro partes:** o mundo, a oficina, a mente e a criação, com a arte ao lado. *Recomendação: sim.*
2. **As pausas são ilustrativas,** feitas pela rotina, sem necessidades no kernel e sem efeito no trabalho. *Ressalva do usuário: sim.*
3. **A copa num canto da sala e o banheiro como porta,** com o lugar exato definido junto com a arte. *Recomendação: sim.*
4. **O almoço na copa, das 12 às 13, pela rotina.** No meio de um trabalho, o dev almoça quando ele acabar. *Recomendação: sim.*
5. **Falar com o dev interrompe a ação dele** por `action_interrupted`, quando o cartucho declara. Sem contrato novo. *Recomendação: sim.*
6. **Os pacotes da mente do gênero e do cenário,** e a mente genérica sem as palavras da fazenda, com as fitas da fazenda valendo. *Recomendação: sim.*
7. **A revisão do dia ao chegar,** cobrindo os dias sem revisão, no máximo três. *Recomendação: sim.*
8. **A oficina:** a `WorkshopPort` e um clone raso em `data/oficina/`, sem `.env`, `data/` e `privado/`, só com Python no M24. *Recomendação: sim.*
9. **As oito ferramentas da oficina** (§3.2), com os limites, e um fato `workshop.step.v1` por passo. *Recomendação: sim.*
10. **O isolamento pelo `sandbox-exec`:** sem rede, escrita só no espaço de trabalho, um ambiente sem segredos. *Recomendação: sim.*
11. **O trabalho:**
    - o `work` de até uma hora, com a sessão da oficina dentro;
    - a sessão acaba no `pronto`, na fala ou num limite;
    - o controlador propõe a entrega sem esperar um pedido de decisão.

    *Recomendação: sim.*
12. **A entrega:**
    - o patch no depósito de arquivos;
    - as recusas pela constituição, pelos testes apagados e pelas palavras proibidas, com a lista em `privado/`;
    - o `make aplicar` num ramo.

    *Recomendação: sim.*
13. **O testador como a criação:**
    - o pedido e o aceite escritos por você no escritório;
    - o registro de robôs do cenário;
    - a ferramenta `chamar_robo`.

    *Recomendação: sim.*
14. **Os modelos:** os cinco na prova de conformidade, e a criação com o melhor da prova entre o Sonnet e o Opus. *Recomendação: sim.*
15. **O orçamento:**
    - o teto por pedido;
    - o `cmd.ops.budget.set`;
    - no escritório, estourar desliga a mente, a rotina assume, e o dev avisa que não pode mais programar, sem pausar o mundo;
    - na fazenda, segue pausando.

    *Ressalva do usuário: sim.*
16. **O sinal de vida da guarda:** sem ele, a mente desliga e a rotina assume. *Sim, no lugar de pausar o mundo, que a §6 do plano macro previa.*
17. **As fitas do escritório com um repositório de exemplo.** *Recomendação: sim.*
18. **A mente com rotina** (§2.5): o modelo só quando há trabalho, a rotina determinística no resto, sob o mesmo controlador `llm`. *Ressalva do usuário: sim.*
