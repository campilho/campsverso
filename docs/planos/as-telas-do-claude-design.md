# Plano do bloco das telas — o escritório do Claude Design

*Proposto em 22/nov/2026, depois do fechamento do M26 (ADR-0089). É um bloco entre o M26 e o M27, como a tela retrô foi dentro do M25 (ADR-0087): leva para a tela os três pedidos do Claude Design de 22/nov (`docs/design/briefing-tela-2.md`, `-3.md` e `-4.md`) e os pedidos do usuário do mesmo dia (os nomes trocados, a devolução maior e a fila da tela).*


***Aprovado em 22/nov/2026 (ADR-0092),*** *com as 10 decisões como recomendado. O dev é o Tiago. A numeração do quadro novo recomeça no 1, com os ramos em `dev/tiago/`, em vez de continuar no 4, para não mexer no kernel (§2).*

**Pronto quando:**
- **Os nomes:** o gerente é o Camps, de blazer, e o dev tem nome de dev, com um avatar do elenco novo. As fazendas não mudam, e o kernel também não.
- **O monitor maior:**
  - a sala escala para a altura toda;
  - o relógio de 7 segmentos, os chips com os bustos, o "?" e o "Assumir" ficam no painel embaixo da tela;
  - o "Escrever pedido" vai para o cabeçalho do quadro.
- **O quadro:**
  - as quatro colunas na parede;
  - as fichas quadradas;
  - a ficha aberta na prancheta grande;
  - a devolução num campo do tamanho do pedido, sem corte escondido.
- **A tela do dev:** o terminal de fósforo verde, aberto pelo computador da sala ou pelo chip.
- **As janelas:** o menu do clique direito, os comandos e os créditos no padrão da tela retrô.
- **A fila:** o passo do quadro interrompe o lazer, e a tela avisa quando um clique troca a fila.
- **O mundo intacto:**
  - os soaks e o replay iguais;
  - o `make check` e o `make ui-e2e` verdes;
  - os prints de cada fase ao lado dos do canvas.

## O que o levantamento mostrou

- **As folhas novas já estão no repositório** (`docs/design/escritorio-arte/folhas/`):
  - o gerente de camisa e de blazer;
  - o Tiago, a Dandara, a Lívia e o Kenji;
  - os retratos de 40 × 40;
  - os ícones da luz;
  - o interruptor redesenhado;
  - o relógio de 7 segmentos.

  O gerador da arte (`office_art.py`) só copia, hoje, o que o elenco usa. As folhas novas entram nele fase a fase.
- **Os nomes são dados do cartucho `office_campsverso`:**
  - o elenco (`escritorio.yaml`);
  - o cartão do dev (`mind/.../data/camps.md`);
  - o `art.json`;
  - o `locale`.

  O kernel não conhece nenhum nome. O `camps` das fazendas é outro avatar, de outro cartucho (`farm_camps`), e não muda.
- **O id `camps` do dev aparece em uns 30 arquivos do escritório:**
  - o cartucho e os testes dele;
  - os testes da tela e o teste do navegador;
  - o mundo `office-campsverso-01`;
  - a mente (`llm/camps`, `camps_escritorio`);
  - os testes da oficina.

  Os outros arquivos com `camps` são das fazendas.
- **O interruptor já está no escritório vivo:** o sistema da luz o criou às 18:00 de hoje. O mundo tinha voltado de um snapshot de antes da ADR-0088, e o gatilho do começo da sessão não roda num mundo retomado (`briefing-tela-4.md`, §6).
- **O limite de 280 caracteres da devolução está no contrato:** o `maxLength` do `office.ticket.returned.v1` e o `comment_max` do `office.yaml`. Subir o limite pede o `office.ticket.returned.v2`.
- **A fila é só da tela:**
  - a TV, o sofá e o videogame já são interrompíveis no kernel (`interrupt: cancel`);
  - é a fila da tela que espera o lazer acabar para mandar o passo do quadro;
  - um clique novo limpa a fila sem dizer nada.
- **As fitas:** a do escritório guarda o hash do pedido, e o nome do dev entra no pedido. Trocar o nome pede regravá-la, por centavos. A da prova pelo Claude Code toca por ordem e por modelo, e deve passar sem regravar; se não passar, também custa centavos.

## 1. Os nomes

**O gerente é o Camps.** O nome na tela passa a ser "Camps", com a folha `gerente_blazer` e o retrato dela.
- O id continua `gerente`: é a cadeira do jogador (`player: gerente`), o papel que o humano assume.
- O senhor de terno (`gerente.png`) e o Camps de óculos (o dev de hoje) ficam guardados na arte, sem uso no elenco.

**O dev ganha nome de dev.** A sugestão é o **Tiago**: o moletom verde com capuz e o fone vermelho no pescoço dizem "dev" de longe. O Kenji, a Lívia e a Dandara ficam para os próximos devs e lugares.
- O id muda de `camps` para `tiago`.
- O cartão do dev e a tela passam a dizer o nome novo: "Tela do Tiago", `login: tiago` e "De Camps para Tiago, o dev." na ficha.

**Por que o id do dev muda, e não só o nome na tela:**
- Com o gerente chamado Camps e o dev com o id `camps`, a menção "@Camps" e o arquivo do mundo ficariam ambíguos.
- O projeto é material de publicação, e um id que contradiz o nome confunde quem lê os fatos.

**As fazendas não mudam.** O Camps continua sendo o fazendeiro, e passa a ser o avatar do humano nos dois mundos: ele joga o Camps na fazenda e é o Camps, gerente, no escritório.

## 2. O escritório vivo, de nome novo

O mundo vivo `office-campsverso-01` tem o dev `camps` no snapshot e nos pedidos. Trocar o id num mundo retomado pediria uma migração dos dados.

A proposta é um mundo novo, o **`office-campsverso-02`**:
- **O quadro do Tiago começa no pedido 1,** e os ramos dele ganham um prefixo próprio, `dev/tiago/pedido-N` (o `codehost.branch_prefix` do mundo), para não colidir com os que já estão no GitHub. O plano dizia "a partir do pedido 4", mas o número vem de um contador do kernel que sempre começa em 1, e o cartucho não sabe em que mundo está. O usuário escolheu recomeçar no 1 a mexer no kernel (22/nov).
- **O `office-campsverso-01` fica inteiro:** o arquivo, o snapshot e a memória do Camps dev.
- **O Tiago começa com a memória limpa.** Ele chega ao escritório pela primeira vez. As lições que importam já estão nas instruções da sessão e no `CLAUDE.md`. Algumas notas antigas estão até desatualizadas, como "o pyright não roda na oficina", e a memória do dev não se edita à mão (ADR-0090).
- **O `make escritorio`** passa a subir o mundo 02, com `MENTE=tiago_escritorio`.

## 3. As fases

Cada fase vai para o `main` inteira, com o `make check-rapido` em cada commit, e o `make check`, o `make ui-e2e` e os prints antes do push, como na tela retrô.

1. **Os nomes e o elenco:**
   - o gerente Camps de blazer e o dev Tiago, com os ids, o cartão e o `locale`;
   - os retratos nos chips (40 × 40) e o rosto na conversa (24 × 24), com o piscar só de tela;
   - o mundo 02 e as fitas regravadas;
   - a documentação: o `CLAUDE.md`, a bíblia do escritório, o README e as minhas notas de memória.
2. **O monitor maior** (`briefing-tela-2.md`, §6, e o relógio do §1):
   - a grade da página e a escala da sala;
   - o painel embaixo da tela, com o relógio de 7 segmentos, os chips com a convocação, o "?" e o "Assumir";
   - o "Escrever pedido" no cabeçalho do quadro.

   No iPad e no celular nada muda: o monitor maior vale a partir de 1.180 px.
3. **O quadro** (`-2.md`, §7, e `-4.md`, §5):
   - as quatro colunas na parede (o `decor.json` e o `art.json`);
   - as fichas quadradas;
   - a ficha aberta na prancheta de 660 px;
   - a devolução maior (§4);
   - os ícones da luz no mapa das ações;
   - o interruptor redesenhado no lugar do nosso.
4. **A tela do dev** (`-3.md`): o terminal de fósforo verde, com a fonte VT323.
   - Ela abre pelo computador da sala e pelo botão do chip.
   - Ela tem a tela de entrada, os passos como comandos, o fim, o vazio e a barra de status.
   - Ela tem a animação: o passo novo entra e se digita, e a pílula avisa as linhas novas.
   - O celular abre em tela cheia.
5. **As janelas** (`-4.md`, §1 a §4):
   - o menu do clique direito, colado ao clique, com ícones e o motivo do que não vale agora;
   - os comandos, com o mouse e as teclas desenhados, só o que vale neste mundo;
   - os créditos por grupo de autores, com a frase certa para o escritório.
6. **A fila:**
   - um passo para o quadro (pegar, aceitar ou devolver uma ficha) interrompe a TV, o sofá e o videogame, em vez de esperar o fim;
   - um clique que troca a fila avisa na tela: "a fila de 3 passos foi trocada".

## 4. A devolução maior

O desenho fica conosco, no estilo que a prancheta já tem: não precisa do Claude Design. A ficha aberta do `-2.md` põe a devolução na barra de madeira, num campo de uma linha. Ela passa para o papel:
- **Com o pedido entregue e o gerente assumido,** um campo "O que falta" em papel pautado, como o "O que fazer", em tinta vermelha.
- **Um contador:** "faltam 412 de 1.000".
- **O "Devolver"** fica na barra, como no desenho.
- **O limite sobe de 280 para 1.000 caracteres,** o mesmo da descrição do pedido, com o `office.ticket.returned.v2`. O dev lê o comentário inteiro no briefing.
- **A tela nunca corta escondido:** o campo para no limite, e o contador mostra quanto falta.

## 5. Contratos

- **`office.ticket.returned.v2`,** com o comentário até 1.000 caracteres. A v1 continua para os dias antigos.
- **O `comment_max` do `office.yaml`** passa a 1.000.
- **As três contagens de tipos** nos testes de contrato.
- **Nada mais muda de contrato.** Os nomes e os ids são dados do cartucho.

## 6. Testes do bloco

- **Unidade:**
  - a hora em células, com `--:--` sem hora;
  - a coluna do retrato por id;
  - a escala da sala por tamanho de janela (a tabela do `-2.md`, §6);
  - o que a ficha quadrada mostra em cada estado;
  - o comando e o resultado de um passo no terminal, com e sem `path`, e o corte pela largura;
  - os comandos de cada mundo;
  - os blocos dos créditos;
  - o contador da devolução;
  - o passo do quadro que interrompe o lazer.
- **No navegador** (o `escritorio.spec.ts`):
  - o Camps de blazer anda;
  - os chips mostram os bustos;
  - a página não passa da janela em 1288 × 720 e em 1456 × 816;
  - a ficha abre e fecha;
  - a devolução longa chega inteira;
  - a tela do dev abre pelo computador e pelo chip;
  - o menu abre colado ao clique;
  - a fila avisa.
- **O mundo intacto:** os soaks das fazendas e do escritório, e o replay.

## 7. Custo

- **API:** só as fitas regravadas, a do escritório e, se preciso, a da prova pelo Claude Code: uns US$ 0,10, com o seu ok no passo.
- **O pacote novo:** o `@fontsource/vt323` (OFL 1.1), a fonte da tela do dev, com o seu ok.
- **O Claude Code:** um bloco do tamanho da tela retrô, que teve seis fases.

## 8. Riscos

- **O mundo novo perde a continuidade do quadro.** *A resposta:* o mundo 01 fica no arquivo, e os PRs antigos no GitHub. Os títulos "Pedido 1" se repetem lá, com números de PR diferentes.
- **O monitor maior quebra em janelas pequenas.** *A resposta:* os prints em 1288 × 720 e em 1456 × 816, e o iPad e o celular sem mudança abaixo de 1.180 px.
- **A animação da tela do dev pesa na sala.** *A resposta:* ela só acrescenta linhas, nunca redesenha a lista, e respeita o `prefers-reduced-motion`.
- **Um nome do elenco coincide com um personagem do livro.** *A resposta:* o usuário confere antes de o nome entrar no repositório.

## 9. Decisões

1. **Um bloco sem número entre o M26 e o M27,** com o plano e a ADR-0092. O plano macro da v0.4 não muda. *Recomendação: sim.*
2. **O gerente é o Camps,** de blazer, com o id `gerente`. *Recomendação: sim.*
3. **O dev é o Tiago.** A Dandara, a Lívia e o Kenji ficam para depois. *Recomendação: o Tiago. A escolha é sua.*
4. **O id do dev muda** de `camps` para `tiago`. *Recomendação: sim.*
5. **O escritório vivo num mundo novo,** o `office-campsverso-02`, com o Tiago de memória limpa. *Recomendação: sim.* Ajustada em 22/nov: o quadro recomeça no pedido 1, com os ramos em `dev/tiago/`, sem mexer no kernel.
6. **A devolução maior,** no papel da ficha aberta, com o contador e o limite de 1.000 pelo `office.ticket.returned.v2`, sem o Claude Design. *Recomendação: sim.*
7. **As seis fases nesta ordem,** cada uma inteira no `main`. *Recomendação: sim.*
8. **A fonte VT323,** pelo `@fontsource/vt323`. *Recomendação: sim. É um pacote novo, então espera o seu ok.*
9. **O interruptor sem mexer no kernel:**
   - ele já existe no mundo vivo, e o mundo 02 nasce com ele;
   - rodar os sistemas do começo da sessão ao retomar um mundo vai para o `futuro.md`, porque muda o que o replay de um dia retomado vê, e isso merece um plano próprio.

   *Recomendação: sim.*
10. **As fitas regravadas** quando o nome muda, por uns US$ 0,10, com o seu ok. *Recomendação: sim.*
