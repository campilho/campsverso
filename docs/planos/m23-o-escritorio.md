# Plano do M23 — O escritório

*Proposto em 14/nov/2026, depois da ADR-0077. **Aprovado em 14/nov/2026 como recomendado (ADR-0078), em duas entregas:** a parte 1, as bases (o andar sem pulo, o tempo real no kernel, os controladores por avatar e a fala), e a parte 2, o escritório. É o primeiro marco da v0.4: o cartucho do escritório, em tempo real e na vista de cima com arte LPC, com o dev-script, o gerente que o humano assume e o vigia. A mente entra no M24. A referência visual é o par do Claude Design de outubro ([escritorio-dia.png](../design/escritorio-dia.png) e [escritorio-noite.png](../design/escritorio-noite.png)), sem o painel de energia, foco e café, que fica para quando houver necessidades.*

**Pronto quando:**
- existe um quarto mundo, `office-campsverso-01`: uma sala com a mesa e o computador do dev, a bancada, o quadro dos pedidos e a porta, em arte LPC;
- o escritório roda a 1× no relógio de São Paulo, com o tick curto, e salta até agora quando a pilha sobe de novo;
- o usuário entra como o gerente, fala com o dev e escreve um pedido no quadro;
- o dev-script vê o pedido, pega, trabalha na mesa (o trabalho ainda é simulado), entrega e avisa;
- o gerente aceita ou devolve o pedido;
- o dev vai embora no fim do expediente, e o vigia passa a noite;
- nenhum humano consegue assumir o dev: o kernel recusa;
- o soak do escritório passa em 5 dias, com o gerente-script, e o replay de um dia confere;
- o andar não pula, com um teste para cada causa conhecida, e a fazenda ganha junto;
- as três fazendas continuam intactas, com os mesmos números nos soaks (1.175, 220 e 85).

## O que o levantamento mostrou

Dois levantamentos do código, um no kernel e outro na tela, em 14/nov.

**O relógio:**
- **O tick é do cartucho** (`ClockDef`), e não do kernel nem do mundo. O escritório pode ter o seu sem tocar na fazenda. O calendário exige que o tick divida 60 s, então 1, 2 e 5 s são aceitos.
- **As necessidades precisam render um número inteiro por tick.** Com um tick de 2 s, as taxas viram múltiplos de 15 por hora; com 1 s, de 30. As da fazenda (3, 1, 5, 12,5 por hora) não caberiam, o que é mais um motivo para o tick ser do cartucho.
- **As durações das ações estão em ticks crus,** e a espera do kernel vai de 1 a 60 ticks. Num tick de 2 s, plantar levaria 10 s, e a espera máxima seria de 2 minutos. O kernel já converte o andar (`tiles_per_minute`), as taxas por hora e os horários do dia.
- **O relógio real não ancora nada.** Ao subir de novo, o mundo continua do tick do snapshot, e o tempo parado se perde. Mas o salto já existe no kernel: `advance(jump=True)` publica o `world.clock.jumped.v1` e roda os sistemas do dia que venceram no caminho. Hoje só os testes o usam.
- **O tick adiantado (ADR-0057)** aplica um comando na hora, quando não há dívida de tempo. Por isso o primeiro clique responde em 0,1 a 0,2 s, e os seguintes esperam o tick normal.
- **O modo máximo** leva cerca de 1,1 s por dia simulado com os processos. Cada tick roda os 8 estágios e uma consulta ao SQLite, e o snapshot completo sai a cada 60 ticks. Com 30 vezes mais ticks por dia, um dia levaria uns 30 s, e o snapshot sairia 720 vezes por dia, se nada mudar.

**Os avatares e a fala:**
- **Ninguém impede um humano de assumir qualquer avatar.**
  - O gateway troca o controlador pelo humano sem conferir qual avatar foi pedido.
  - A tela do jogador sempre assume o avatar do `--avatar`, o Camps por padrão.
  - O kernel só confere se o avatar existe.
- **A presença existe** (M20): `enter` e `leave`, com o avatar ausente parado e sem decisões.
- **Não há ação nem evento de fala** em lugar nenhum, nem nos contratos.
- **A mente supõe um minuto por tick** em três lugares: a frase "ticks de um minuto", o "Dura N minutos" das ferramentas e a memória. Isso se conserta no M24, quando a mente entra no escritório.
- **As camadas de arte da fazenda** (`farm` e `farm_camps`) não têm `only_for`, então carregariam num mundo do escritório.

**O pulo do avatar.** O desenho do andar tem um teto de 12 tiles por segundo, e o kernel, acelerado, anda de 36 a 720. Os mecanismos que fazem o avatar pular são estes:

1. **O salto para o destino.** O desenho fica atrás do kernel. Quando o trajeto acaba antes de o desenho chegar (uma ação que não é andar, um desmaio, uma reconexão), o avatar salta para onde o kernel o pôs. Acelerado, com o script ou um LLM, o atraso se acumula de um trajeto para o outro, e o salto seguinte é grande. **É o que o usuário viu.**
2. **Dois trajetos no mesmo tick.** O trajeto é identificado pelo tick de saída. Com a tecla segurada ou cliques rápidos, vários caem no mesmo tick, a tela guarda só o primeiro e salta para o fim do último. Nenhum teste cobre esse caso.
3. **A emenda para trás.** A tela só procura a origem do trajeto novo para a frente. Quando o desenho está adiantado, o que é normal a 1× e a 6×, um segmento inteiro é desenhado num quadro.
4. **O trajeto já terminado.** O trajeto seguinte começa da origem dele, sem emenda. Se o fim desenhado não bater com essa origem, o avatar se teletransporta.
5. **A aba em segundo plano.** O orçamento de desenho de um trajeto cresce sem limite enquanto a aba não desenha, e na volta o avatar salta para a frente.
6. **A reconexão.** O relógio da tela pode voltar no tempo, e os trajetos perdidos enquanto a conexão caiu viram saltos.
7. **A arena.** As miniaturas dividem um só relógio de movimento, todas com o id `camps`. Os avatares de corridas diferentes se emendam uns nos outros.

**A 1×, com o tick de hoje,** o andar fica errado:
- a pulsação traz o tick seguinte em 1 s, e a tela desenha o trajeto inteiro a 12 tiles por segundo, como uma corrida;
- depois o avatar fica parado num quadro de andar, com a barra "Andando", até o tick acabar;
- o comentário do código e a ADR-0057, que dizem que a 1× o teto nunca é atingido, estão errados.

Nenhum dos 6 testes no navegador confere que o andar é suave.

## 1. O mundo (a bíblia do escritório)

Os números vão para uma bíblia nova, `docs/arquitetura/escritorio-campsverso-biblia.md`, como as das fazendas.

### 1.1 A sala

**A sala tem uns 20 × 14 tiles,** cabe inteira na tela (que mostra até 32 × 18) e fica sem câmera rolando. Do lado de fora, uma faixa de corredor, por onde se entra e se sai. Dentro:
- **a mesa do dev,** com o computador e a cadeira;
- **a bancada,** vazia no M23: é onde os robôs vão ficar a partir do M24;
- **o quadro dos pedidos,** na parede de cima, com as colunas;
- **a porta,** para o corredor;
- **o lugar da segunda mesa,** demarcado no chão, como os cubículos da referência;
- **para o visual:** a janela, o relógio de parede com a hora real, plantas e a cadeira do vigia perto da porta.

### 1.2 O elenco

| Quem | Controlador | Quando está |
|---|---|---|
| **Camps,** o líder técnico | o dev-script no M23; a mente a partir do M24, com o script de reserva. Nunca um humano. | no expediente |
| **O gerente,** de roupa formal | o humano, pela tela do jogador; o gerente-script nos testes | enquanto alguém o assume |
| **O vigia** | um script | sempre que o dev não está: à noite, no fim de semana e nos feriados |

### 1.3 O dia

- **O expediente** é de segunda a sexta, das 09:00 às 18:00. O dev sai para almoçar das 12:00 às 13:00: sai pela porta e volta.
- **Os feriados nacionais** ficam numa lista nos dados do cenário.
- **Fora do expediente,** o dev não está, e o vigia faz a ronda com a lanterna.

**Sem necessidades no M23.** O dia é regido pelo expediente. A energia e o café entram quando a mente pedir (M24 em diante). Com o tick de 2 s, a energia poderia cair 15 por hora, de 100 a zero em umas 6 horas e meia, o que cabe num dia de trabalho.

### 1.4 O pedido

Um pedido é uma entidade do gênero `office`, criada pelas primitivas do kernel. A economia fica de fora: as encomendas têm item, quantidade e preço, e o pedido não tem nenhum dos três.

**O que o pedido tem:**
- o título (até 80 caracteres);
- a descrição (até 1.000);
- o teste de aceite (até 500): o "pronto quando" do gerente;
- o tamanho (P, M ou G), que no M23 só dá a duração do trabalho simulado do script;
- o autor;
- o progresso.

**Os estados:** a fazer → fazendo → entregue → aceito. Devolvido, o pedido volta para "a fazer" com o comentário do gerente.

**Os fatos com nome** são eventos do cartucho, como o `farm.crop.matured`:
- `office.ticket.created.v1`;
- `office.ticket.taken.v1`;
- `office.ticket.delivered.v1`;
- `office.ticket.accepted.v1`;
- `office.ticket.returned.v1`.

Nos ids, "ticket", em inglês, como manda a convenção; na tela, "pedido".

### 1.5 As ações

| Ação | Quem | Onde | O que faz |
|---|---|---|---|
| `say` (do kernel) | todos | qualquer lugar | fala até 280 caracteres, opcionalmente para alguém; quem está na mesma sala ouve |
| `write_ticket` | o gerente | diante do quadro | escreve um pedido |
| `take_ticket` | o dev | diante do quadro | pega o pedido mais antigo "a fazer", ou o escolhido |
| `work` | o dev | na mesa | trabalha no pedido; é longa e `partial`, e o fim do expediente a interrompe guardando o progresso |
| `deliver` | o dev | na mesa | entrega o pedido |
| `accept` e `return` | o gerente | diante do quadro | aceita, ou devolve com um comentário |
| `leave` | o gerente | na porta | sai do escritório |

A chegada e a saída do dev e do vigia são sistemas do cartucho, como os turnos dos ajudantes da Morada.

**O dev anda a 72 tiles por minuto,** 1,2 tile por segundo, que é o andar de uma pessoa num tile de um metro.

## 2. O tempo real

A ADR do M23 registra o que segue, porque toca o princípio 7.

- **O tick do escritório sai de uma medida,** no começo do marco: o tempo do soak por dia e a resposta ao clique, com 1, 2 e 5 s. A aposta é 2 s: o soak fica em uns 30 s por dia simulado, e o andar curto, de 3 a 10 tiles, não arredonda demais.
- **As durações do escritório são declaradas em segundos e minutos,** e o kernel as converte em ticks, como já faz com o andar e as taxas. A espera também vai para segundos. A fazenda continua em ticks de um minuto, com os mesmos números.
- **A âncora:**
  - o arquivo do mundo tem um início fixo;
  - ao subir, a pilha salta até agora pelo salto que o kernel já tem, e o salto entra no diário de entradas, para o replay reproduzir;
  - o relógio real continua lido só na raiz de composição (princípio 4).
- **O tick adiantado** continua, com um limite: o mundo fica no máximo um tick à frente do relógio real.
- **O snapshot passa a ser contado em minutos simulados** (a cada 60, como a fazenda já faz em ticks), por mundo. Com o tick curto, ele não sai 720 vezes por dia.
- **A tela:**
  - o botão 1× na tela do jogador;
  - a hora com os segundos quando o tick for menor que um minuto;
  - o fim das contas que supõem um minuto ou 72× (o `lead()` da tecla segurada, a velocidade das animações, o "faltam N min").

## 3. O movimento

O conserto vem antes do escritório e vale para a fazenda e para o escritório:

1. **Reproduzir cada mecanismo com um teste** (Vitest), simulando os quadros a 1×, 72×, 144× e 720×. Um pulo é um deslocamento de mais de um tile entre dois quadros. Os testes falham antes do conserto.
2. **O desenho segue o tempo do trajeto,** e não um orçamento de tiles por segundo:
   - a posição sai de `depart_tick`, do passo e do relógio da tela;
   - quando o kernel corrige (destino novo, interrupção, reconexão), a tela faz uma emenda curta e suave, de uns 200 ms, em vez de um salto;
   - acelerado, o desenho anda na velocidade do kernel, que é a verdade. Não se mostra devagar o que já terminou.
3. **O trajeto passa a ser identificado pela ação** (`action_id`, que o `moved` já traz), e não pelo tick de saída. Dois trajetos no mesmo tick deixam de colidir.
4. **A emenda procura a origem nos dois sentidos,** para a frente e para trás.
5. **O orçamento tem teto quando a aba volta,** e o relógio de movimento usa uma fonte de tempo só.
6. **Um relógio de movimento por corrida na arena.**
7. **O ciclo de andar do LPC acompanha a distância percorrida,** como o `per_tile` já faz, para o passo não deslizar.

Um teste no navegador anda com o Camps a 1× e a 72× e confere que nenhum quadro desloca mais de um tile.

## 4. O kernel e os contratos

- **Os controladores aceitos por avatar.**
  - O `AvatarDef` ganha a lista de tipos que podem controlar o avatar: o dev aceita `llm`, `script` e `replay`; o gerente, `human`, `script` e `replay`.
  - O kernel recusa `possess` fora da lista, com o motivo `controller_not_allowed`, e confere o arquivo do mundo ao subir.
  - O gateway passa a ler a cadeira do jogador no mundo (o gerente) e confere o avatar pedido.
- **A presença com a possessão.** O gerente começa ausente.
  - Assumido, ele entra pela porta.
  - O botão "Sair" o leva até a porta, e ele sai pela ação `leave`.
  - Se a tela fechar sem sair, ele sai na hora, quando a posse cair.
- **A fala.**
  - É a ação `say` do kernel, ao lado de `move` e `wait`.
  - Gera o evento novo `campsverso.avatar.spoke.v1`, com quem fala, o texto, para quem e onde.
  - A percepção entrega a fala a quem está na mesma sala, pela mesma régua da visão (princípio 5).
  - A fazenda não muda: o catálogo dela não oferece a fala.
- **Os eventos do pedido** (§1.4), com schemas, exemplos e o `CHANGELOG`.
- **O tempo** (§2): as durações em segundos e minutos, a espera em segundos, o salto ao subir no diário de entradas, o snapshot por minutos simulados.
- **Nenhuma mudança incompatível:** só campos opcionais novos e tipos novos (`make compat`).

## 5. O gênero e o cenário

| Pacote | O que tem |
|---|---|
| `cartridges/office/sim` | o gênero: o pedido, as ações, o quadro, o expediente, o vigia, as métricas e os rótulos |
| `cartridges/office/script` | o dev-script, o vigia-script e o gerente-script |
| `cartridges/office/art` e `locale` | a arte e os nomes do gênero |
| `cartridges/office_campsverso/sim` | o cenário: o mapa, o elenco, o expediente, os feriados e os números |
| `cartridges/office_campsverso/art` e `locale` | o mapa visual e os personagens |

**Onde entram:**
- os membros do workspace;
- as listas do import-linter;
- os entry points;
- o `only_for` nas camadas da fazenda, para a arte não se misturar.

**A mente do escritório** (`office/mind` e `office_campsverso/mind`) fica para o M24.

**Os comandos:**
- `make escritorio`: sobe o mundo persistente `office-campsverso-01` a 1× e mostra o endereço da tela do gerente;
- `make sandbox MUNDO=office-campsverso-01`: um escritório descartável;
- `make soak MUNDO=office-campsverso-01 DAYS=5`.

## 6. Os scripts

- **O dev-script:**
  - chega no começo do expediente e diz bom dia, se houver alguém;
  - olha o quadro e pega o pedido mais antigo;
  - trabalha na mesa: P por 15 minutos, M por 1 hora, G por 3 horas;
  - entrega e avisa ("Entreguei o pedido 3");
  - sai para almoçar e vai embora no fim do expediente;
  - com um pedido devolvido, pega de novo;
  - quando falam com ele, responde com uma frase pronta ("Anotado."). Entender o que o gerente disse é do M24.
- **O vigia-script:** chega quando o dev sai, faz a ronda com a lanterna por pontos fixos, senta na cadeira da porta e sai quando o dev chega.
- **O gerente-script,** só para os testes:
  - escreve pedidos de um roteiro, em horários fixos;
  - fala com o dev;
  - aceita o que foi entregue, e devolve um de cada três, para exercitar a volta.

## 7. A arte

Os pacotes do OpenGameArt:
- **"LPC Revised: The Office":** mesa, laptops, copiadora e quadros, em CC-BY-SA 3.0 ou OGA-BY 3.0;
- **"LPC Wooden Furniture";**
- **"LPC House Interior and Decorations":** o piso, as paredes e as janelas.

**O download** pede o seu ok na hora, com o arquivo, a origem e o tamanho de cada um.

**Os personagens** saem do gerador LPC:
- **o Camps de escritório:** o mesmo rosto, o mesmo cabelo e a mesma barba do Camps da fazenda, com óculos e roupa de escritório;
- **o gerente:** um senhor de cabelo grisalho, de roupa formal;
- **o vigia:** de roupa escura e boné, com a lanterna.

O gerador tem roupa formal, óculos e gravata-borboleta. A gravata comprida, se você quiser, a gente desenha. A animação de sentar e digitar fica a conferir no gerador. Se não houver, o dev fica de pé na mesa com a animação de mexer as mãos, como a de regar na fazenda.

**O que falta, desenhado no estilo:**
- o quadro dos pedidos, com as colunas e os cartões;
- a tela do computador acesa, com linhas rolando enquanto o dev trabalha;
- a placa da bancada.

Os créditos vão no `CREDITS.csv` de cada pasta e na tela, como hoje.

**O capricho:**
- o andar suave (§3);
- os balões de fala com rabicho, que aparecem e somem;
- os cartões do quadro, com o alfinete vermelho no pedido novo;
- a tela do computador;
- a luz da janela pela hora real, com a passagem gradual em vez dos degraus de hoje, o que a fazenda também ganha;
- a lanterna do vigia à noite, com a luz que a Morada já tem;
- a porta que abre;
- as sombras dos móveis.

## 8. A tela

- **A tela do gerente** (a visão do jogador, que assume o gerente ao abrir):
  - andar pelo clique e pelo teclado, como na fazenda;
  - uma caixa de fala, que manda com Enter;
  - diante do quadro, o formulário do pedido (título, descrição, teste de aceite e tamanho);
  - nos entregues, aceitar ou devolver com um comentário;
  - o botão "Sair".
- **Os balões** mostram até uns 90 caracteres com "…", e o texto inteiro fica na linha do tempo. É a regra do protótipo.
- **O quadro** desenha os pedidos nas colunas, e um clique abre a ficha do pedido.
- **A barra sobre o dev:** "trabalhando · pedido 3 · 40%", como na referência.
- **O painel do operador** ganha as métricas dos pedidos, declaradas pelo cartucho (ADR-0054):
  - pedidos escritos, entregues, aceitos e devolvidos;
  - o tempo médio até a entrega;
  - as falas do dia.
- **Os textos novos da tela do escritório** nascem em `apps/ui/src/locale/pt-BR.json` (o `futuro.md`, ADR-0075). Os da fazenda passam depois.

## 9. Testes do marco

- **Unidade (Python):**
  - as ações do pedido, com as recusas (longe do quadro, sem pedido, o estado errado);
  - o `work` parcial no fim do expediente, com o progresso guardado;
  - a fala, com o limite de caracteres e quem ouve;
  - a possessão recusada (o humano no dev);
  - a presença do gerente;
  - a conversão das durações;
  - o salto ao subir.
- **Ponta a ponta, em memória:** um dia com o gerente-script escrevendo três pedidos e o dev-script entregando os três; um devolvido e refeito; o vigia só quando o dev não está.
- **O soak:** `make soak MUNDO=office-campsverso-01 DAYS=5`, com os invariantes:
  - todo pedido escrito é entregue;
  - o dev só está no expediente;
  - o vigia, só quando o dev não está;
  - nenhum controle humano no dev.
- **O replay e a recuperação:** `make replay DAY=2` no escritório confere, e o salto ao subir de novo é reproduzido.
- **A tela (Vitest):** os sete mecanismos do pulo; os balões e o quadro a partir dos eventos.
- **No navegador (Playwright),** um servidor novo do escritório:
  - o gerente entra, fala e escreve um pedido, que aparece no quadro;
  - o andar sem pulo, a 1× e a 72×.
- **As fazendas intactas:** os soaks com os mesmos números, e os 6 testes do navegador.

## 10. Ordem do trabalho

1. **O pulo,** com os testes primeiro e depois o conserto. É independente, e a fazenda ganha já.
2. **A medida do tick** (1, 2 e 5 s) e a ADR do tempo.
3. **O kernel:**
   - as durações em segundos e minutos;
   - os controladores por avatar;
   - a presença com a possessão;
   - a fala e os contratos;
   - o salto ao subir;
   - o snapshot por tempo.
4. **O gênero e o cenário:** o mapa lógico, o pedido, as ações, o expediente e a bíblia.
5. **Os scripts:** o dev, o vigia e o gerente.
6. **A arte:** os downloads com o seu ok, os personagens e o mapa visual.
7. **A tela:** a cena, os balões, o quadro, o formulário, o painel e os textos.
8. **Os testes:** ponta a ponta, o soak, o replay e o navegador.
9. **Você joga de gerente** no escritório vivo, a 1×.
10. **O fechamento:** o diário, o `futuro.md` e o "Como ficou".

## 11. Custo

- **De API: nada.** O M23 não chama modelo: o dev é o script.
- **De desenvolvimento:** é um marco grande, do tamanho do M16 com o M17 (umas 4 horas de Claude Code), por causa do tempo real, da arte e do movimento.

## 12. Decisões

1. **O tick do escritório:** medir 1, 2 e 5 s e escolher pela medida. *Recomendação: a aposta é 2 s.*
2. **A âncora:**
   - um início fixo no arquivo do mundo;
   - ao subir, o salto até agora, gravado no diário de entradas;
   - o tick adiantado no máximo um tick à frente do relógio real.

   *Recomendação: sim, com a ADR do M23.*
3. **As durações do escritório em segundos e minutos,** convertidas pelo kernel, e a espera em segundos. A fazenda não muda. *Recomendação: sim.*
4. **O snapshot contado em minutos simulados,** por mundo. *Recomendação: sim, a cada 60.*
5. **O expediente:** de segunda a sexta, das 09:00 às 18:00, com o almoço fora das 12:00 às 13:00 e os feriados nacionais. O vigia fica sempre que o dev não está. *Recomendação: sim. O protótipo abria às 08:40, se você preferir.*
6. **Sem necessidades no M23.** A energia e o café entram com a mente. *Recomendação: sim.*
7. **Os controladores aceitos por avatar,** conferidos pelo kernel. O gateway toma a cadeira do jogador do mundo e confere o avatar pedido. *Recomendação: sim.*
8. **O gerente entra ao ser assumido e sai pela porta,** com o "Sair", ou na hora se a tela fechar. *Recomendação: sim.*
9. **A fala:**
   - a ação `say` do kernel;
   - o evento `avatar.spoke.v1`;
   - ouvida na mesma sala;
   - até 280 caracteres.

   *Recomendação: sim.*
10. **O pedido como entidade do gênero `office`,** sem a economia, com os eventos `office.ticket.*` e o tamanho só para o script. *Recomendação: sim.*
11. **O dev-script e as frases prontas,** com o trabalho simulado de 15 minutos, 1 hora e 3 horas. *Recomendação: sim.*
12. **A sala de uns 20 × 14 tiles,** com o corredor, sem câmera rolando e com o lugar da segunda mesa demarcado. *Recomendação: sim.*
13. **A arte:** os três pacotes e os três personagens do gerador. O download pede o seu ok com o tamanho de cada arquivo, e as camadas da fazenda ganham o `only_for`. *Recomendação: sim.*
14. **O movimento:** o desenho segue o tempo do trajeto, a correção vira uma emenda suave, o trajeto é identificado pela ação, e há um teste para cada mecanismo. *Recomendação: sim, como o primeiro passo do marco.*
15. **A tela do gerente:** a fala, o formulário do quadro, aceitar e devolver, e o "Sair". O painel ganha as métricas dos pedidos, e os textos novos vão para `locale`. *Recomendação: sim.*
16. **A bíblia do escritório e o `make escritorio`** com o mundo persistente. *Recomendação: sim.*
17. **O gerente-script e o soak de 5 dias,** com os invariantes da §9. *Recomendação: sim.*
