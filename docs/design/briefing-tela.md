# Pedido de tela: o escritório na versão retrô

A tela do escritório (ADR-0078), redesenhada com o usuário no Claude Design em 21/11/2026. É a referência para a implementação na `apps/ui`. O canvas com as telas interativas está no [claude.ai](https://claude.ai/artifact/9feHAQqgzqu4o4jdxGU57u), na conta do usuário. Aqui ficam os prints e a arte, para quem implementa não depender dele.

O que o usuário escolheu, em ordem:

1. A versão B, a retrô, entre as duas propostas.
2. O ícone 1, o monitor de tubo com um mundo dentro.
3. Os ajustes:
   - o quadro sempre em abas;
   - a conversa que aumenta e diminui;
   - a rolagem suave;
   - a barra de cima limpa;
   - o "Sobre" no lugar dos links;
   - as mensagens do sistema;
   - a placa numa linha;
   - as menções com @;
   - os chips só com a ação;
   - a velocidade só no operador;
   - a prancheta do novo pedido.

A regra de sempre vale: a tela desenha o que os eventos dizem e não decide nada (escopo §9). Cada botão continua virando uma proposta, como hoje.

| Onde | O quê |
|---|---|
| [escritorio-tela/](escritorio-tela/) | 13 prints das telas (webp), nos tamanhos de cada aparelho (§9) |
| [escritorio-arte/tela/](escritorio-arte/tela/) | a arte da moldura em 1x, com o `tela.json`: o ícone, a cortiça, a caneta, o prendedor e dois ícones de chip |
| [escritorio-arte/folhas/](escritorio-arte/folhas/) | o que a tela já usa: `icones.png`, `selos.png` e, para a parede, `placa_versao_linha.png` (a placa numa linha, `<commit> <dd/mm>`) |

---

## 1. O escopo

- **Só o escritório** (`isOffice(state)`). A fazenda, a arena (`?view=arena`) e o assistir (`run`) ficam com a tela de hoje neste passo. A moldura serve a eles depois, como tarefa do `futuro.md`.
- **Nenhum contrato novo.** Tudo o que a tela mostra já existe:
  - a menção é o `to` da ação `say`, que vira o `listener_id` de `avatar.spoke.v1`;
  - os avisos vêm de `realtime/notice.v1` e do `welcome.build`;
  - a convocação, as ações do pedido e o PR já estão no estado.
- **As fontes vão junto com a UI, sem CDN.** O escritório vivo roda local. Use woff2 latin e latin-ext; os pacotes `@fontsource/*` servem. As quatro são OFL e entram nos créditos.
- **O mundo não para** quando um modal abre: princípio 7. A sala continua andando atrás da cortina escura.

## 2. A tela grande (MacBook Pro, 1456 × 816)

```
┌──────────────────────────────────────────────────────────────────────────────┐ 52
│ [ícone] Campsverso ●                                  [ Jogador | Operador ] │
├──────────────────────────────────────┬───────────────────────────────────────┤ gap 12
│ ┌ o monitor (692 × 580) ───────────┐ │ ┌ o quadro (flex 1, mín. 150) ──────┐ │
│ │ ┌ a sala, 640 × 512, 1x ───────┐ │ │ │ Quadro dos pedidos · 15 · 1 PR    │ │
│ │ │   (Phaser)                   │ │ │ │ [A fazer 5][Fazendo 1][Entregue]… │ │
│ │ │   fila e aviso por cima      │ │ │ │ cortiça com as fichas, rolagem    │ │
│ │ └──────────────────────────────┘ │ │ └───────────────────────────────────┘ │
│ │ CAMPSVERSO ||||   câmera ● vivo │ │ ┌ a conversa (300 ou 520) ──────────┐ │
│ └──────────────────────────────────┘ │ │ Conversa  o Camps e o vigia [Aum.]│ │
│ ┌ a barra (flex 1, mín. 132) ──────┐ │ │ mensagens, rolagem                │ │
│ │ 10:59 │ chips em 2 linhas → │ [Assumir] │ │ [@][ escreva…           ][Enviar] │ │
│ │ dia   │ (rolam de lado)     │ [Pedido]  │ └───────────────────────────────────┘ │
│ └──────────────────────────────────┘ │                                       │
└──────────────────────────────────────┴───────────────────────────────────────┘ 12
```

- **A página:** fundo `#17141f`, sem espaço vazio. A grade tem as linhas `52px minmax(0, 1fr)`, `gap: 12px` e `padding: 0 12px 12px`.
- **A coluna da esquerda:** 692 px fixos, com o monitor e a barra.
- **A coluna da direita:** `flex: 1 1 360px`, com o quadro e a conversa. A gaveta do operador cobre só essa coluna.

## 3. Peça por peça

### 3.1 A barra de cima

Ela tem só o ícone, o nome, a luz e a troca de visão. Não mostra versão, data nem "escritório do campsverso".

**O botão do ícone**
- 40 × 40, com `icone.png` em 32 × 32.
- Abre o Sobre (§3.7) e leva `aria-haspopup="dialog"`.

**O nome:** "Campsverso", em Pixelify Sans 700, 22 px.

**A luz:** 9 px, com o aro de 2 px e um `aria-label`.

| Cor | Quando | Rótulo |
|---|---|---|
| verde, `#3fd17a` | conexão aberta e pulso vivo | online |
| âmbar, `#ffab2e` | aviso `troca` ou `espera` valendo | atualizando |
| vermelha, `#ff4646` | conexão fechada, ou "kernel sem sinal" | sem conexão |

**Jogador | Operador:** um grupo de dois botões com `aria-pressed`.
- Na visão do jogador, "Operador" **navega** para `?view=operator`. O socket do jogador não traz o que o operador vê, e a visibilidade é dada pelo NATS (princípio 5).
- Na visão do operador, os dois botões só abrem e fecham a gaveta (§3.8), sem trocar de socket.

**Os links de hoje mudam de lugar:**
- "créditos" e "canvas de depuração" passam para o Sobre;
- "abrir a visão do operador" vira a troca de visão.

### 3.2 O monitor

O gabinete de um monitor de tubo, em creme. O mapa fica dentro da tela de vidro.

**A tela:**
- 640 × 512, a sala inteira em 1x (20 × 16 tiles de 32);
- borda de 3 px escuro, raio 12 e anel de 3 px bege;
- por cima, uma varredura: uma linha preta a 7% a cada 3 px, com `pointer-events: none`;
- escala só inteira: com espaço, 2x; nunca fracionária.

**O rodapé do gabinete**, da esquerda para a direita:
- "CAMPSVERSO", em Pixelify 14, com espaço de 3 px entre as letras;
- cinco frestas;
- a câmera: `sala` | `seguir o gerente`;
- "ao vivo", com um ponto.

**A câmera:**
- no computador, a sala cabe inteira, e o seletor só entra quando a sala passar da tela ou com zoom 2x;
- no celular, "seguir o gerente" é o padrão (§4);
- é o `startFollow` do Phaser, com limites na sala.

**O que hoje fica sobre o mapa continua sobre o vidro, embaixo:**
- a fila (`queueBox`, "Esc esvazia");
- o aviso de recusa (`notice`);
- a ajuda dos comandos.
- O botão "Comandos" vira um "?" de 28 px no rodapé do gabinete.

**O texto de dica de hoje** ("Sua vez: clique esquerdo anda…") vai para o `title` do "?" e para a primeira vez da ajuda (`help.firstTime()`).

**O relógio do sandbox:** quando `playerClock()` é verdadeiro, pausar e os ritmos (`OFFICE_PACES`, botões de 24 px) entram no rodapé do gabinete. No escritório vivo não aparecem.

### 3.3 A barra de baixo

Três partes, com divisórias de 2 px `#ae9b72`.

**1. O relógio**
- **A hora:** `clockText`, em Pixelify 38.
- **O dia:** "Dia 13 · manhã", com `state.phase`, em 12 px 600.
- **A conexão:** "ao vivo" com o ponto verde. Quando não está aberta, segue os textos `STATUS` do HUD.
- **Sem ritmo:** na visão do jogador não aparece "1×". Se a escala for diferente de 1 (no sandbox), aparece "72×" em âmbar.
- **Sem clima:** o escritório não tem; o clima só aparece se `state.weather` tiver o dia.

**2. As pessoas:** os chips, em 2 linhas e `grid-auto-flow: column`.
- As colunas têm `minmax(176px, max-content)` e rolam de lado.
- Uma máscara esmaece os 12% da direita.

Cada chip tem:
- **o retrato:** 38 × 36, o mesmo recorte do `Portrait`. O de um robô é o quadro 0 da folha dele, em 32 × 32.
- **o nome:** 13 px 600.
- **a etiqueta:**

  | Etiqueta | Para quem | Estilo |
  |---|---|---|
  | `LLM` | o controlador é `llm` | escuro, texto claro |
  | `script` | o controlador é `script` | bege |
  | `robô` | um robô | bege |
  | `você` | o gerente que você assumiu | fundo amarelo |

- **a linha:** um ícone de 16 px e **só a ação curta**, sem a intenção. O texto inteiro de `doingText(action, intent)` fica no `title`.
  - O ícone vem do mapa `acoes` da folha `icones` no `metadados.json`.
  - Três casos têm ícone próprio:

    | Quem | Ícone | Linha |
    |---|---|---|
    | quem está fora da sala | `tela/ic_fora.png` | "fora" |
    | o vigia no posto | `tela/ic_vigiar.png` | "vigiando" |
    | quem dorme | `dormir`, da folha | — |

- **Quem está fora da sala** (sem `position`) tem a borda tracejada.
- **O dev fora do expediente:** a linha é a da convocação, `summonLine`, encurtada: "fora", "a caminho · 20:10", "convocado até 22:00".
- **Quem aparece**, nesta ordem:
  1. os avatares do elenco: Camps, Vigia e Gerente;
  2. os robôs de `state.workshop.robots`, com o estado pela regra de `workshop.ts` (trabalhando, passou, falhou, parado).

**3. Os comandos**
- **Assumir o gerente / Soltar o gerente:**
  - 44 px, em Pixelify 16, com `aria-pressed`;
  - amarelo para assumir, bege para soltar;
  - "Soltar o gerente" faz o que hoje faz "Sair do escritório": `leave()`, ele vai até a porta e a tela o devolve.
- **Escrever pedido:** 32 px; desabilitado sem o gerente; abre a prancheta (§3.6).
- **Convocar o Camps / Dispensar o Camps:** 32 px. Aparece só com o gerente assumido e o dev fora ou convocado, e usa as mesmas ações de hoje. Lembre que `on_manager_enter` já convoca ao entrar.

### 3.4 O quadro

**A moldura e o cabeçalho**
- Moldura de madeira `#b07541`, com bisel `#d49b5d` em cima e `#7e5032` embaixo, anel de 3 px `#1b1726` e raio 10.
- Cabeçalho: uma faixa creme com "Quadro dos pedidos" (Pixelify 18) e "15 pedidos · 1 PR aberto" (13 px).

**As abas: sempre**, em qualquer tamanho de tela.
- Uma aba por coluna de `COLUMNS`: **A fazer, Fazendo, Entregue, Aceito**. O canvas desenhou três abas, com "Feito"; vale o código, com quatro.
- Cada aba tem 40 px, raio `6px 6px 0 0` e um contador num pílula de 22 px.
  - Ativa: `#d49b5d`, com texto escuro.
  - Inativa: `#7e5032`, com texto `#fbe7a0`.
- Leva `role="tablist"`, `tab`, `tabpanel` e `aria-selected`, com as setas do teclado.
- A aba ativa só se guarda na tela.

**O painel**
- Fundo de cortiça: `tela/cortica.png`, repetido em 64 × 64.
- Borda de 3 px `#563521`.
- Grade `repeat(auto-fill, minmax(196px, 1fr))` com `gap: 16px 12px`, rolagem vertical e `scroll-behavior: smooth`.

**A ficha compacta**
- Papel `#f6f2e8`, borda de 2 px, sombra dura de 3 px e raio 3.
- Um pino de 8 px no alto, vermelho ou azul, alternando pelo número.
- A faixa de 8 px tem a cor do tamanho:

  | Tamanho | Cor |
  |---|---|
  | P | `#78c25a` |
  | M | `#f2c94c` |
  | G | `#e8635a` |

- Por dentro, de cima para baixo:
  - `#18` e `M`, em JetBrains Mono 12;
  - o título, 14 px 600;
  - uma linha de 12 px: "com Camps", ou "do gerente" e, se o pedido tiver o tick em que foi escrito, "· há 20 min";
  - o PR, se houver: uma pílula com o selo de 6 × 6 em 3x (`selos.png`) e o texto de `pullRequestLine`, que é um link quando passa por `PR_URL`. A pílula é escura com o PR aberto e azul `#3e5580` com ele mesclado.
- **A barra de andamento "3/5"** do canvas não tem dado hoje. Não desenhe sem dado.
- **A ficha inteira é um botão:** abre a prancheta em modo leitura (§3.6). Os `<details>` de hoje saem.

**Com a conversa aumentada**, o quadro vira uma fileira só, com rolagem de lado. As fichas ficam com 210 px e só o número, o tamanho e o título.

### 3.5 A conversa

**A caixa e o cabeçalho**
- Caixa creme com bisel e raio 14.
- Altura de **300 px**, ou **520 px** aumentada, com uma transição de 0,35 s.
- O cabeçalho tem "Conversa" (Pixelify 17), os retratos empilhados, "o Camps e o vigia" e o botão "Aumentar" / "Diminuir" (32 px, com a seta e `aria-label`).

**O registro**
- É `role="log"`, com rolagem vertical suave.
- Fica sempre no fim, a menos que a pessoa tenha subido.
- **As falas** são os `avatar.spoke.v1` da linha do tempo:
  - as do gerente vão à direita, em amarelo, com o raio `8 8 2 8`;
  - as dos outros vão à esquerda, em papel, com o retrato de 26 × 24.
  - Embaixo de cada fala, "Camps · 10:34", em 10 px.
- **As linhas do sistema** (12 px, no centro) são os fatos do quadro e do PR, com o texto de `describe()`: pegou o pedido, entregou, aceito, devolvido, CI.
- O vigia aparece só quando o script dele fala. O canvas o mostra respondendo só para desenhar o balão.

**As menções**
- No texto, `@Nome` vira uma pílula azul `#3e5580` com texto branco.
- **Ao enviar:**
  - a primeira menção de um avatar presente que não seja o próprio gerente vira o `to` do `say`;
  - o texto vai como está, com o @;
  - sem menção, o `to` continua sendo o dev, como hoje (`devOf`).
- **As sugestões:**
  - abrem acima do campo quando o texto termina em `@palavra`;
  - mostram os avatares presentes, menos o gerente, filtrados pelo começo do nome;
  - são um `listbox` de 250 px, com itens de 40 px (retrato, "@Camps", "o dev · LLM");
  - setas, Enter ou Tab escolhem, e Esc fecha.
  - Os robôs não entram: não são avatares.

**A linha de escrever**
- O botão "@" tem 40 × 40, em JetBrains Mono; a Pixelify não tem o @.
- O campo tem 40 px e até 280 caracteres (`SPEECH_MAX`). A dica muda:
  - com o gerente: "Escreva @ para chamar quem precisa responder";
  - sem ele: "Assuma o gerente para falar", com o campo desabilitado.
- "Enviar" fica amarelo quando há texto.
- O `keydown` não passa para o mapa, como hoje.
- **Sai o cartão "Falar" do painel atual.**

### 3.6 A prancheta: o novo pedido, e a ficha aberta

Um modal por cima de tudo, no lugar do cartão "Novo pedido" do painel lateral. Prints: `pedido.webp` e `iphone17-pedido.webp`.

**O fundo:** `rgba(23, 20, 31, 0.72)`. A sala continua viva atrás.

**A prancheta**
- **Tamanho:** 580 px, com `max-height: 100%`.
- **A madeira:** `#b07541`, com veios verticais de 2 px `#7e5032` a 28% e de 1 px `#d49b5d` a 32%, borda de 3 px escuro, raio 22, bisel `#d49b5d` e `#7e5032`, e `padding: 46px 20px 18px`.
- **O prendedor:** `tela/prendedor.png` em 3x (192 × 78), centrado, a 24 px acima da borda, por cima do papel.
- **A caneta:** `tela/caneta.png` em 3x (144 × 144), deitada à direita, fora da prancheta. Some abaixo de 900 px.

**O papel** (`#f6f2e8`, borda de 2 px, sombra dura de 4 px, rolagem própria), de cima para baixo:
- **A faixa:** 10 px, com a cor do tamanho escolhido. Muda junto com o tamanho.
- **O cabeçalho:**
  - "CAMPSVERSO · FICHA DE PEDIDO" (11 px, 700, em caixa alta);
  - "Novo pedido" (Pixelify 28);
  - à direita, "Nº #18" numa caixa (JetBrains Mono 15) e "Dia 13 · 10:59", a hora do mundo ao abrir.
  - O número é uma prévia, o maior número mais um. Quem numera é o kernel.
- **A linha de quem para quem:** "De **Gerente** para **Camps**, o dev. A ficha entra no quadro em **A fazer**.", com um traço de 2 px embaixo.
- **Os campos:** os de hoje, com os mesmos limites.
  - Os rótulos são impressos: 11 px 700, em caixa alta, `#563521`.
  - O que o gerente escreve vai em **Patrick Hand**, na tinta azul da caneta, `#2b3f6e`.

  | Campo | Rótulo | Valor | Limite |
  |---|---|---|---|
  | título | TÍTULO | 23 px, sobre uma linha de pauta de 2 px `#a9bad6` | 80 (`TITLE_MAX`) |
  | o que fazer | O QUE FAZER | `textarea` pautada, 20 px, entrelinha de 28 px, 3 linhas que crescem até 6 e depois rolam | 1000 (`DESCRIPTION_MAX`) |
  | teste de aceite | TESTE DE ACEITE · como você vê que ficou pronto | a mesma pauta, 2 linhas que crescem até 4 | 500 (`ACCEPTANCE_MAX`) |

  - Um contador ("812/1000", 11 px) aparece ao passar de 80% do limite.
  - Os placeholders vão em Inter itálico 14, `#85735a`.
- **O tamanho:** um `radiogroup` com três quadrados de papel de 46 px.
  - Cada um tem a faixa interna de 6 px da cor do tamanho, um quadradinho de 20 px que recebe um "X" em letra de mão, a letra (Pixelify 18) e o nome (12 px).
  - O nome some abaixo de 480 px; o `aria-label` ("P, pequeno") fica.
  - O escolhido ganha um fundo tingido:

    | Tamanho | Fundo escolhido |
    |---|---|
    | P | `#dcefd3` |
    | M | `#f8ecbf` |
    | G | `#f6d3cf` |

  - O padrão é M.
- **A assinatura:** "Gerente", em letra de mão, sobre um traço, com "ASSINATURA" embaixo.

**A barra de madeira, embaixo**
- **Fechar:** 44 px.
- **"Falta o título":** 13 px 600, escuro; aparece só sem título.
- **Pôr no quadro:**
  - 44 px, em Pixelify 17, amarelo, com um pino vermelho;
  - desabilitado, e bege, sem título.

**O comportamento**
- **Abrir:**
  - pelo "Escrever pedido", só com o gerente assumido;
  - o foco vai ao título;
  - o foco fica preso no modal e volta ao botão quando fecha.
- **Fechar:**
  - Esc ou Fechar fecham, e **o rascunho fica** na memória da página;
  - clicar fora não fecha.
- **Soltar o gerente**, ou uma queda, fecham o modal e guardam o rascunho.
- **Todo `keydown` dentro do modal para nele.** O teclado anda com o avatar.
- **Pôr no quadro:**
  1. chama `actions.write(...)`, como hoje;
  2. o gerente anda até o quadro (a fila mostra "Escrever o pedido …");
  3. o modal fecha;
  4. enquanto o passo `write_ticket` estiver na fila, uma **ficha fantasma** tracejada fica no topo de "A fazer", com o título e "o gerente está indo ao quadro". A ficha de verdade só aparece quando o kernel publica o pedido.
- **O rascunho se apaga** quando o passo sai da fila sem recusa. Com recusa, ele fica, e o aviso de hoje diz o motivo.

**A ficha aberta** (não desenhada; segue a mesma prancheta)
- **O que abre:** um clique numa ficha do quadro abre a prancheta em leitura.
- **O papel:**
  - os mesmos campos, com o texto do pedido em letra de mão, sem edição;
  - o Nº de verdade;
  - à direita do cabeçalho, uma etiqueta com o estado ("ENTREGUE");
  - "com Camps";
  - "Devolvido: …", na tinta vermelha `#c63b3b`;
  - a linha do PR, com o selo e o link;
  - "Ver o patch", que abre o `DeliveryDialog` de hoje.
- **A barra de madeira**, quando o pedido está entregue e o gerente está assumido:
  - "Aceitar", ou a dica "Aceite mesclando o PR #n" com o PR aberto;
  - o campo "O que falta" e "Devolver".
- Com o gerente a caminho, aparece "O gerente está indo ao quadro." no lugar dos botões.
- As regras do `card()` de hoje valem iguais. Só a forma muda.

### 3.7 O Sobre

**A janela:** uma janela de Mac clássico, de 600 px.
- **A barra de título:** 30 px, com listras de 1 px a cada 3 px.
- **O título:** "Sobre o Campsverso", numa plaqueta creme (Pixelify 15).
- **O botão de fechar:** a caixinha de 20 × 20 à esquerda, com `aria-label="Fechar"`.

**O conteúdo**
- O ícone em 4x (128 px), numa moldura.
- "Campsverso" (Pixelify 32) e "v0.4 · o escritório que constrói a si mesmo", uma constante da UI que muda a cada versão.
- Uma lista de definições:

  | Item | O que mostra |
  |---|---|
  | Versão | a versão e o marco |
  | Rodando | o `welcome.build`: o commit curto e a data, com o ponto verde |
  | Mundo | o nome e o id do cartucho |
  | Relógio | o dia, a hora, o ritmo e "ao vivo" |
  | Arte | "pixel art desenhada em código · 48 cores" |

- **Os botões:**
  - **Créditos:** abre o `CreditsDialog` de hoje;
  - **Canvas de depuração:** o link `?render=debug`;
  - **Notas da versão:** só se houver um endereço para elas.

**A mesma moldura de janela** (barra listrada, caixinha de fechar, bisel creme e sombra `0 30px 70px rgba(0,0,0,.65)`) vale para:
- o `DeliveryDialog`;
- os créditos;
- a ajuda dos comandos;
- as mensagens do sistema.

### 3.8 O operador: a gaveta

**A gaveta**
- Cobre a coluna da direita, como a Central de Notificações do macOS.
- **O vidro:** `rgba(30, 27, 42, 0.88)`, com `backdrop-filter: blur(18px) saturate(1.4)`, borda de 1 px branca a 12%, raio 18 e sombra.
- **O movimento:** entra da direita, de `translateX(calc(100% + 40px))` a 0, em 0,35 s com `cubic-bezier(.2, .8, .2, 1)`.
- **Ao fechar:** fica com `visibility: hidden` e `aria-hidden`.

**O conteúdo:** as seções do `OperatorPanel` de hoje, em duas colunas, `330px | 1fr`, com rolagem própria.

**A esquerda**
- **O relógio:**
  - pausar;
  - os ritmos que o painel já oferece hoje;
  - avançar +1, +10 e +60 ticks, só com o relógio pausado.
- **A versão e o caderno**, lado a lado:
  - a versão: o commit rodando e o estado da troca;
  - o caderno: "só a mente escreve".
- **O controlador e a decisão.**
- **O custo da API:** as barras de dia, pedido e total, com "Mudar os tetos" (o formulário dos tetos de hoje).
- **As métricas do dia:** não estão no canvas; entram aqui, recolhidas.

**A direita: a linha do tempo**
- Os filtros por visibilidade, com as cores de hoje (`--world`, `--agent`, `--internal`, `--observer`).
- O filtro por tipo.
- A lista: tick, origem, tipo e detalhe, em JetBrains Mono.

O "×" da gaveta é o mesmo que "Jogador". Com a gaveta aberta, a velocidade muda no operador, e a barra de baixo mostra o ritmo em âmbar quando for diferente de 1×.

### 3.9 As mensagens do sistema

O `bannerOf` de hoje decide o texto. A tela passa a precisar também do tipo, então vale acrescentar `kind` ao `Banner`.

| Tipo | Forma | O que mostra |
|---|---|---|
| `troca` | **modal que trava a tela** (`alertdialog`, z 40), sem botão | "O Campsverso está se atualizando": da versão `welcome.build.commit` para a `notice.commit`, com os PRs; uma faixa listrada que anda; os passos em texto fixo, que explicam a troca e não fingem progresso (confira o texto com a ADR-0086) |
| queda (`closed` depois de aberta) | modal que trava a tela | "A conexão caiu": "Tentar agora" só se a `Connection` souber reconectar sob pedido; a tentativa só se ela contar |
| `espera` | aviso no canto de cima à direita, 340 px, com "×" | "Versão nova na fila" |
| `volta` | aviso, com a faixa vermelha | "O escritório voltou", com o texto do aviso |
| versão nova (`fresh`) | aviso, com a faixa verde | "Versão nova no ar", com o commit e os PRs |

- Os prazos são os de `banner.ts`.
- Os avisos ficam acima de tudo, menos dos modais do sistema.
- Com `prefers-reduced-motion`, a faixa listrada para.

## 4. Tablet e celular

| Largura | Arranjo |
|---|---|
| ≥ 1180 (o computador, o iPad deitado) | as duas colunas da §2. Com altura < 760, a conversa normal fica com 240 px |
| 760 a 1179 (o iPad em pé) | o monitor na largura toda, com as caixas de som de grade dos dois lados; a barra; o quadro e a conversa lado a lado, até o fim |
| < 760 (os celulares) | a barra de cima compacta (48 px); o monitor recortado; uma faixa com a hora, o dia e "ao vivo"; as abas **Quadro · n \| Conversa · n \| Pessoas · n**; o painel escolhido até o fim; a barra de ação |

**O monitor no celular**
- A sala não cabe em 1x, e escala fracionária borra o pixel.
- Então a câmera **segue o gerente** em 1x, num recorte de 5:4.
- Junto vão a etiqueta "seguindo o gerente" e um minimapa de 80 × 64 no canto, com o retângulo do que se vê.
- O seletor "sala | seguir" fica no rodapé do gabinete.

**A barra de ação**
- 48 px, com `padding-bottom: env(safe-area-inset-bottom)`.
- Tem "Assumir o gerente" ou "Soltar o gerente" e, com ele assumido, "Escrever pedido".
- A convocação entra aqui também, quando valer.

**Os modais e a gaveta**
- Usam a largura toda, menos 8 px de cada lado.
- O papel da prancheta rola. A caneta e os nomes dos tamanhos somem.

**Os tamanhos que os prints usam:**

| Aparelho | Tela |
|---|---|
| iPad deitado | 1180 × 820 |
| iPad em pé | 820 × 1180 |
| iPhone 17 | 402 × 874 |
| iPhone 17 Pro Max | 440 × 956 |
| Galaxy S24 Ultra | 384 × 832 |

As fontes divergem sobre o Galaxy (há quem diga 412 de largura). Teste também em 412.

**O toque:** todo alvo tem no mínimo 44 px de altura. No computador, "Escrever pedido" e "Convocar" têm 32 px; no toque, 44.

## 5. Os tokens

**As cores** são da paleta da sala (`metadados.json`, `paleta`), pelo nome:

| Nome | Hex | Uso |
|---|---|---|
| `contorno` | `#1b1726` | toda borda dura |
| `escuro` | `#26222f` | texto; botão ativo |
| `creme` | `#e7d9b4` | painéis: barra de cima, gabinete, barra, conversa, janelas |
| `cremeCl` | `#f4ead0` | o brilho do bisel; campos; chips |
| `begeSomb` | `#ae9b72` | a sombra do bisel; divisórias |
| `bege` | `#cdbb8f` | grupos de botões; botão desligado |
| `begeEsc` | `#85735a` | texto apagado; placeholder |
| `branco` | `#f6f2e8` | o papel das fichas e da prancheta |
| `mad` | `#b07541` | a madeira do quadro e da prancheta |
| `madCl` | `#d49b5d` | o veio e o bisel da madeira; aba ativa |
| `madEsc` | `#7e5032` | o veio e o bisel da madeira; aba inativa |
| `madMEsc` | `#563521` | a borda da cortiça; rótulos impressos |
| `amarelo` | `#f2c94c` | o botão principal; tamanho M; as falas do gerente |
| `amareloCl` | `#fbe7a0` | o texto das abas inativas |
| `verdeCl` | `#78c25a` | tamanho P |
| `vermCl` | `#e8635a` | tamanho G |
| `verm` | `#c63b3b` | os pinos; a tinta do "Devolvido" |
| `azulEsc` | `#3e5580` | as menções; o PR mesclado; o foco |
| `azul` | `#5a76a6` | os pinos |
| `azulCl` | `#86a2cb` | o fundo do retrato do Camps |
| `telaTexto` | `#3fd17a` | a luz verde; "ao vivo" |
| `verdeEsc` | `#2f6b30` | o aro da luz verde |
| `ledAmbar` | `#ffab2e` | a luz âmbar; o ritmo diferente de 1× |
| `ledVerm` | `#ff4646` | a luz vermelha |
| `grafite` | `#4a4d57` | o texto secundário da ficha |
| `grafiteEsc` | `#33353e` | o texto secundário da ficha |

**Fora da paleta**, só na moldura:

| Hex | Uso |
|---|---|
| `#17141f` | o fundo da página |
| `#2b3f6e` | a tinta da caneta |
| `#a9bad6` | a pauta |
| `#dcefd3`, `#f8ecbf`, `#f6d3cf` | os tamanhos escolhidos |
| `#ece6d6`, `#d7d1e3`, `#a9a3b8` | os textos da gaveta |

**As fontes**

| Fonte | Uso |
|---|---|
| Pixelify Sans (500, 700) | o nome, os títulos, a hora, as abas, os botões principais |
| Inter (400 a 700) | o texto |
| JetBrains Mono (400, 600) | os números de pedido, os commits, os ticks, o "@" |
| Patrick Hand | **só** o que o gerente escreve na prancheta |

**O bisel**
- Borda de 3 px `contorno`.
- `inset 3px 3px 0 cremeCl` e `inset -4px -4px 0 begeSomb`.
- Raios:

  | Raio | Onde |
  |---|---|
  | 14 | painéis |
  | 10 | janelas |
  | 6 | botões |
  | 3 | papel |

- O botão principal leva `inset 0 -4px 0` com a cor escura dele e `0 3px 0 contorno`.

**As camadas (z)**

| z | O quê |
|---|---|
| 0 | o mapa |
| 10 | a gaveta |
| 20 | o menu de ações e a ajuda |
| 30 | o Sobre e os outros diálogos |
| 32 | a prancheta |
| 35 | os avisos de canto |
| 40 | as mensagens que travam a tela |

**A arte:** sempre com `image-rendering: pixelated` e escala inteira.

## 6. Acessibilidade e teclado

**Os modais**
- Levam `role="dialog"` com `aria-modal`, ou `alertdialog` para os do sistema.
- O título vai em `aria-labelledby`.
- O foco fica preso dentro, e Esc fecha, menos nos do sistema.

**O teclado que anda com o avatar** não pode escapar: os campos e os modais param o `keydown`, como os campos de hoje.

**Os nomes acessíveis**
- **A luz:** tem `aria-label`; nunca é só a cor.
- **Os chips:** são uma `list` com `listitem`.
- **A conversa:** é um `log`.
- **O quadro:** abas ARIA.
- **O tamanho:** `radiogroup`.
- **A sala:** o `alt` do monitor descreve a sala. No Phaser, um `aria-label` no canvas.

**O contraste**
- O texto pequeno sobre a madeira é `#1b1726` (4,5:1).
- A tinta `#2b3f6e` sobre o papel dá cerca de 9:1.

**O movimento:** com `prefers-reduced-motion`, saem a faixa que anda, as transições da gaveta e da conversa e a rolagem suave.

## 7. De onde vem cada coisa

| Na tela | Vem de |
|---|---|
| a luz da barra de cima | `store.status`, `state.pulse.alive`, o `bannerOf` (`troca` e `espera`) |
| a hora e o dia | `clockText`, `state.day`, `state.phase` (o HUD de hoje) |
| o ritmo em âmbar | `state.clock.scale` diferente de 1 |
| os chips | as entidades `avatar` com `position`, `state.controllers`, `state.actions` (`doingText`), `state.asleep`, `summonsOf` e `summonLine`, `state.workshop.robots` |
| o quadro e as fichas | `ticketsOf(state)`, `COLUMNS`, `pullRequestLine`, `PR_URL` |
| a ficha fantasma | os passos `write_ticket` de `queue.list` |
| a conversa | `campsverso.avatar.spoke.v1` (`text`, `listener_id`) e os fatos do quadro e do PR, pela linha do tempo |
| a menção | o `say` com `to` (o kernel aceita um avatar presente que não seja quem fala) |
| a prancheta | `OfficeActions.write`, com os mesmos limites de hoje |
| a ficha aberta | `card()` de hoje: `accept`, `giveBack`, `DeliveryDialog` |
| a convocação | `OfficeActions.summon` e `dismiss` |
| o Sobre | `welcome.build`, o cartucho, `CreditsDialog` |
| a gaveta | `OperatorPanel`, sem mudar o que ele faz |
| as mensagens do sistema | `bannerOf` com o `kind`, `realtime/notice.v1`, `welcome.build` |

## 8. O que fica fora, ou em aberto

- **Já resolvido:** a placa da versão na parede numa linha (`placa_versao_linha`, desde b82047c). A tela escreve `<commit> <dd/mm>` no retângulo do `metadados.json`. Quando trocar, a `placa_versao` de duas linhas sai.
- **Dois ícones de chip:** `ic_fora` e `ic_vigiar` estão soltos em `escritorio-arte/tela/`. Cabem nas casas livres `[6,3]` e `[7,3]` da `icones.png`; a mudança pede `make arte-escritorio`.
- **A câmera que segue no computador** e o zoom 2x ficam para quando a sala crescer.
- **"há 20 min" na ficha:** só se o pedido tiver o tick em que foi escrito. A barra de andamento "3/5" fica de fora sem dado.
- **A moldura na fazenda e no assistir:** uma tarefa no `futuro.md`.
- **Para registrar numa ADR curta:**
  - a tela retrô;
  - a troca de visão que navega;
  - as fontes junto com a UI;
  - o modal no lugar do painel do pedido.

## 9. Como conferir

**Os testes de unidade (Vitest)**
- a menção que vira `to`: a primeira, um avatar presente, nunca o próprio gerente;
- a ação curta e o ícone de cada chip;
- a contagem das abas;
- a ficha fantasma a partir da fila;
- a cor da luz;
- o `kind` do `bannerOf` e a escolha entre modal e aviso.

**No navegador (`make ui-e2e`)**
1. Abra a prancheta pelo "Escrever pedido".
2. Digite: o gerente não anda.
3. Esc fecha e guarda o rascunho.
4. "Pôr no quadro" põe o passo na fila e a ficha fantasma em "A fazer".
5. A troca para o operador navega.
6. A gaveta abre e fecha.

Tire prints em 1456 × 816, 820 × 1180 e 402 × 874 e compare com os da pasta.

**Os prints**, em [escritorio-tela/](escritorio-tela/):

| Arquivo | O que mostra |
|---|---|
| `jogador.webp` | a tela do jogador, com o quadro em "Feito" (no código, "Aceito") e a conversa normal |
| `conversa.webp` | a conversa aumentada, com o quadro numa fileira, o gerente assumido e as sugestões do @ |
| `pedido.webp` | a prancheta do novo pedido, preenchida |
| `operador.webp` | a gaveta do operador aberta |
| `sobre.webp` | o Sobre |
| `atualizando.webp` | a troca de versão travando a tela, com a luz âmbar |
| `avisos.webp` | as duas janelas que travam, os três avisos de canto e as três luzes |
| `ipad-deitado.webp`, `ipad-em-pe.webp` | o iPad |
| `iphone17.webp` | o celular com a câmera seguindo o gerente e o quadro |
| `iphone17-pedido.webp` | a prancheta no celular |
| `iphone17-pro-max-conversa.webp` | a conversa no celular |
| `galaxy-s24-ultra-pessoas.webp` | as pessoas no celular |

Os prints vêm do canvas, desenhados com dados de exemplo:
- o pedido #18;
- a hora 10:59;
- as falas;
- os três robôs nos chips (hoje, a bancada tem só o testador).

Valem como forma, não como número.
