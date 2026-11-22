# Pedido de tela, 2: o relógio, os retratos e o gerente novo

A continuação do [briefing-tela.md](briefing-tela.md), depois da tela retrô no ar (ADR-0087). O usuário pediu em 22/11:

1. o relógio da barra de baixo como um relógio digital dos anos 90, de 7 segmentos, verde num fundo escuro;
2. um gerente parecido com ele, de camisa social azul e calça bege, com e sem o blazer azul;
3. o retrato dos chips no estilo da referência dele: um busto de frente, e não o recorte do sprite;
4. o gerente antigo, o senhor de terno, continua na arte, para outros usos;
5. mais quatro personagens variados, para os próximos lugares;
6. mais espaço para o monitor (§6).

Depois de ver o canvas, ainda em 22/11, o usuário decidiu:

- **o monitor maior está aprovado**, mas sem as caixas de som dos lados: o gabinete abraça a tela, e o quadro e a conversa ficam com o que sobra;
- **as fichas do quadro ficam quadradas**, sem todo o texto, e um clique abre a ficha inteira num modal grande, na prancheta (§7);
- **o gerente usa a versão de blazer.**

O canvas tem as telas novas: a página 4 mostra o elenco, os retratos e o relógio, e a página 5, o monitor maior com as fichas quadradas e a ficha aberta. Aqui ficam os números. A regra de sempre vale: a tela desenha o que o estado diz, e nada aqui muda contrato ou regra do mundo.

| Onde | O quê |
|---|---|
| `escritorio-arte/tela/relogio_7seg.png` | os dígitos do relógio, com o `tela.json` atualizado |
| `escritorio-arte/folhas/retratos.png` | os bustos de 40 × 40, com a entrada `retratos` no `metadados.json` |
| `escritorio-arte/folhas/gerente_camisa.png`, `gerente_blazer.png` | o gerente novo, nas duas roupas |
| `escritorio-arte/folhas/tiago.png`, `dandara.png`, `livia.png`, `kenji.png` | o elenco novo |
| `escritorio-arte/previa/elenco.gif` | os seis andando nas quatro direções |
| `escritorio-tela/grande.webp`, `grande-1288.webp` | o monitor maior, em 1456 × 816 e em 1288 × 720 |
| `escritorio-tela/fichas.webp`, `ficha-aberta.webp` | as fichas quadradas e a ficha aberta na prancheta |

As folhas de antes (`camps`, `gerente`, `vigia` e as outras) não mudaram nem um pixel. No `metadados.json`, as entradas de antes também ficaram iguais: só entraram as novas.

---

## 1. O relógio de 7 segmentos

**A folha:** `tela/relogio_7seg.png`, uma linha de 14 células de 12 × 20, nesta ordem:

| Célula | O quê |
|---|---|
| 0 a 9 | os dígitos |
| `-` | só o segmento do meio |
| ` ` | todos apagados |
| `:` | os dois pontos acesos |
| `:apagado` | os dois pontos apagados |

- Os dois pontos ocupam só as 4 primeiras colunas da célula. Corte essas 4.
- Cada célula traz os segmentos acesos e os apagados juntos, sem fundo. O visor põe o fundo escuro.
- **As cores:**
  - aceso: `telaTexto` (`#3fd17a`), com `telaBrilho` no meio de cada segmento;
  - apagado: `#16261e`, o "fantasma" de um visor de verdade. É uma cor fora da paleta, só da moldura.

**O visor**

| Propriedade | Valor |
|---|---|
| fundo | `#1b1726` |
| raio | 6 |
| `padding` | `6px 10px` |
| anéis | 2 px `#ae9b72` por fora e mais 2 px `#1b1726` |
| sombras internas | `inset 0 2px 0 rgb(0 0 0 / 60%)` e `inset 0 -2px 0 rgb(255 255 255 / 6%)` |

- **Sem brilho em volta.** Um `drop-shadow` acenderia os segmentos apagados também.
- **A escala:**

  | Onde | Escala | Cada dígito |
  |---|---|---|
  | na barra | 2x | 24 × 40 |
  | os dois pontos | 2x | 8 × 40 |
  | na faixa do celular | 1x | 12 × 20 |

  Sempre com `image-rendering: pixelated`.

**O que mostra**
- A hora vem de `clockText`, em `HH:MM`, 24 h. Sem hora conhecida, mostra `--:--`.
- O dia e o "ao vivo" continuam ao lado ou embaixo, em Inter, como hoje.
- **Os dois pontos piscam** a cada segundo do relógio da parede: é só desenho, e o mundo não sabe disso. Com `prefers-reduced-motion`, ficam acesos.

**Acessibilidade:** `role="img"` e `aria-label` com a hora ("10:59"). O rótulo muda a cada minuto, nunca no piscar.

**Onde fica:** no painel do monitor (§6), na faixa do celular e na barra de baixo do iPad, no lugar da hora em Pixelify. O resto não muda.

**Como desenhar:** cinco `span` com a folha de fundo, um `background-position` por dígito, ou um canvas pequeno. O que for mais simples na moldura.

## 2. Os retratos

**A folha:** `folhas/retratos.png`, com 9 colunas e 2 linhas de 40 × 40.
- A linha 0 é o rosto parado; a linha 1, piscando.
- As colunas, nesta ordem: `gerente_camisa`, `gerente_blazer`, `camps`, `vigia`, `tiago`, `dandara`, `livia`, `kenji` e `gerente` (o antigo).
- No `metadados.json`, `folhas.retratos.retratos` dá a coluna de cada id.
- Os retratos vêm sem fundo: o chip põe a cor.

**Nos chips do painel do monitor:** o retrato inteiro em 1x (40 × 40), no lugar do recorte de 38 × 36 do sprite, sobre a cor de fundo de hoje de cada pessoa. O gerente usa a coluna `gerente_blazer`. Os robôs continuam com o sprite deles.

**Na conversa** (as falas, a pilha do cabeçalho e as sugestões do @): o recorte do rosto, 24 × 24 a partir de (8, 4), em 1x. É o que o canvas mostra. O `FaceCache` pode cortar daqui no lugar do `portrait` de hoje.

**O piscar** é opcional e só de tela: a linha 1 por 150 ms, a cada 4 a 7 s, num tempo diferente para cada um. Com `prefers-reduced-motion`, não pisca.

**O manifesto**
- Uma ideia: `avatars.<id>.face = { "sheet": "retratos", "column": N }`, ao lado do `portrait` de hoje. Sem `face`, a tela volta ao recorte.
- A folha vai para `cartridges/office_campsverso/art/`, junto dos personagens.

## 3. O gerente novo

**As folhas:** `gerente_camisa.png` e `gerente_blazer.png`, no mesmo formato das outras:
- quadros de 64 × 64, 8 colunas e 29 linhas;
- as mesmas linhas e animações do Camps, todas preenchidas;
- a âncora em (32, 64).

**As duas roupas**
- **Igual nas duas:**
  - o cabelo quase preto com topete;
  - a barba escura com o queixo grisalho;
  - a calça bege;
  - o sapato marrom.
- **Só o que muda:**

  | Folha | A roupa |
  |---|---|
  | `gerente_camisa` | a camisa social azul de mangas dobradas, com o antebraço à mostra, e o cinto marrom |
  | `gerente_blazer` | o blazer azul-marinho por cima, sem gravata, com o colarinho e os punhos da camisa aparecendo |

**No cartucho**
- O avatar `gerente` passa a usar **`gerente_blazer`**, a escolha do usuário. A `gerente_camisa` fica pronta na pasta.
- O pipeline (`CHARACTERS` em `office_art.py`) ganha as duas folhas.
- O nome no cartucho fica a critério de quem implementa: copiar a escolhida como `gerente.png` ou apontar o `art.json` para o nome novo.

**O gerente antigo:** `folhas/gerente.png`, o senhor de terno, fica na pasta de arte, sem uso no elenco. O usuário quer guardá-lo para outros contextos. Se a cópia do cartucho trocar de nome, ele pode ganhar um nome próprio depois.

**Conferir no sandbox:**
- o sentar na cadeira;
- o digitar de costas, com o antebraço em pele, na versão camisa;
- o sofá;
- o carregar a marmita;
- o comer de lado.

## 4. O elenco novo

Quatro folhas prontas, no mesmo formato, com todas as animações:

| Folha | Quem |
|---|---|
| `tiago.png` | cabelo crespo baixo, cavanhaque, moletom verde com capuz, fone vermelho no pescoço, jeans e tênis branco |
| `dandara.png` | black power, brincos de argola dourados, blazer vermelho sobre a camiseta branca, calça e sapato pretos |
| `livia.png` | rabo de cavalo ruivo com elástico vermelho, brincos pequenos, blusa mostarda, saia azul-marinho até o joelho e sapatilha vinho |
| `kenji.png` | cabelo liso preto com franja, suéter de gola alta creme, crachá azul, calça marrom e sapato preto |

**Agora nada muda no elenco do escritório.** Eles ficam prontos para os próximos lugares, e cada um já tem retrato. A descrição de cada um está em `configuracao` no `metadados.json`.

## 5. O que não muda

- **As cores:** a paleta continua com 48. Todas as folhas novas usam só cores dela; a única de fora é o segmento apagado do relógio, que é moldura.
- **As linhas das folhas antigas:** nenhuma foi mexida, nem as do Camps e do vigia.

## 6. O monitor maior (aprovado em 22/11)

A barra de baixo deixa de existir no escritório: o que ela tinha vai para o painel do próprio monitor e para o cabeçalho do quadro. Com isso, a sala escala para a altura toda. Prints: `grande.webp` (1456 × 816) e `grande-1288.webp` (1288 × 720).

**A grade da página**
- A barra de cima passa a ter 44 px.
- A página usa `padding: 0 8px 8px` e `gap: 8px`.
- A grade tem `grid-template-columns: minmax(0, 1fr)`, para nada alargar a página.

**O monitor (a coluna da esquerda)**
- **Sem as caixas de som:** o gabinete abraça a tela, com 16 px de borda creme dos lados e 14 px em cima. A largura do monitor é a da tela mais 44 px.
- **A escala da sala:** a maior que cabe nas duas medidas.
  - Na altura: `escala = (altura da coluna − 102) / 512`, onde os 102 px são a borda, o topo, a moldura da tela, o espaço e o painel.
  - Na largura: a escala que deixa a coluna da direita com no mínimo 400 px, `(largura da janela − 24 − 400 − 44) / 640`.
  - O canvas do Phaser continua em 1x (640 × 512) e é escalado pelo CSS, com `image-rendering: pixelated`. A escala sai fracionária; num retina, cada pixel da arte fica com 2 px de tela ou mais.

| Janela | A sala | O monitor | A coluna da direita |
|---|---|---|---|
| 1288 × 720 | 1,09x | 742 px | 522 px |
| 1456 × 816 | 1,28x | 861 px | 570 px |
| 1728 × 980 | 1,60x | 1066 px | 638 px |

**O painel embaixo da tela:** uma linha só, com 64 px de altura e uma linha de bisel em cima. Da esquerda para a direita:
1. **o relógio de 7 segmentos** (§1) e, ao lado, "Dia 13" e "manhã" em duas linhas. O "ao vivo" sai daqui: a luz da barra de cima já diz;
2. **os chips das pessoas**, numa linha que rola de lado, com a borda da direita esmaecida e um divisor de 2 px antes;
3. **o "?"** dos comandos do teclado, com 32 px;
4. **"Assumir o gerente" / "Soltar o gerente"**, com 44 px, o mesmo de hoje.

**A convocação** cabe no chip do dev quando ele está fora: um botão pequeno "Convocar" na própria linha do chip ("fora · Convocar"); convocado, "Dispensar". Ela usa as mesmas ações de hoje.

**A coluna da direita** fica com `flex: 1`, o resto da largura:
- o quadro, com `flex: 1`;
- a conversa, com 300 px e 520 aumentada;
- a gaveta do operador por cima dela, numa coluna só, que rola.

**"Escrever pedido"** sai da barra de baixo e vai para o **cabeçalho do quadro**, à direita, depois do "15 pedidos · 1 PR aberto":
- 32 px, com o pino vermelho;
- amarelo com o gerente assumido, bege e desabilitado sem ele;
- o contador encolhe com reticências antes de o botão sair do lugar.

**No iPad e no celular nada muda:** o monitor maior vale a partir de 1180 px de largura.

## 7. As fichas quadradas e a ficha aberta

Prints: `fichas.webp` e `ficha-aberta.webp`.

### A ficha quadrada

As fichas da cortiça viram quadrados (`aspect-ratio: 1`), numa grade `repeat(auto-fill, minmax(112px, 1fr))`, com `gap: 16px 12px`. São 3 por linha a 522 px e 4 a 570 px.

A ficha inteira é um botão, com `aria-haspopup="dialog"` e um `aria-label` com o número, o título e o tamanho. Por dentro, de cima para baixo:
- **o pino de 8 px no alto**, como hoje;
- **a faixa de 8 px** da cor do tamanho;
- **o número** (`#17`, JetBrains Mono 12) e, à direita, **o tamanho** num quadradinho de 18 px da cor do tamanho, com a letra em Inter 800;
- **o título:** 12,5 px 600, no máximo 3 linhas (`-webkit-line-clamp: 3`), sem encolher;
- **embaixo, só ícones:**
  - o rosto do dono, 20 × 20, o recorte do retrato;
  - o selo do PR, de 6 × 6 em 3x, com o texto do PR no `title`;
  - "devolvido", em letra de mão vermelha, quando o pedido voltou.

**O que sai da ficha:** a descrição, o "Pronto quando", "com Camps" por extenso, a linha do PR por extenso e os botões. Tudo isso vai para a ficha aberta.

**Na conversa aumentada,** o quadro vira uma fileira só de quadrados de 112 px.

**A ficha fantasma** do pedido a caminho (a fase 2) também fica quadrada e tracejada.

### A ficha aberta

Um clique na ficha abre a prancheta em leitura. Ela já existe desde a fase 2; o que muda:

**O modal**
- **O tamanho:** a prancheta fica maior, com 660 px de largura (o novo pedido continua com 580).
- **Fechar:** o Esc ou o "Fechar". O foco volta à ficha.

**O papel:** tudo o que o gerente escreveu vem em letra de mão, na tinta azul, e nada se edita.
- **A faixa** com a cor do tamanho.
- **O cabeçalho:**
  - "CAMPSVERSO · FICHA DE PEDIDO" e "Pedido #11" (Pixelify 28);
  - à direita, **o carimbo do estado**: uma caixa de 3 px com o nome em Pixelify 16, em caixa alta e espaçado;

    | Estado | Cor |
    |---|---|
    | A FAZER | `#563521` |
    | FAZENDO | `#7e5032` |
    | ENTREGUE | `#2f6b30` |
    | ACEITO | `#3e5580` |

  - embaixo do carimbo, "escrito no Dia 11 · 09:12", só se o pedido tiver o tick em que foi escrito.
- **A linha de quem para quem:** "De Gerente para Camps, o dev." e, à direita, a pílula "com Camps", com o rosto.
- **Os campos:**
  - **Título:** 24 px, sobre a linha de pauta.
  - **O que fazer** e **Teste de aceite:** 20 px, em papel pautado. O texto inteiro aparece; o papel rola se precisar.
- **O tamanho:** os três quadradinhos, com o "X" no do pedido, sem ser botão.
- **"Devolvido: …"**, quando houver: em letra de mão vermelha, com uma faixa vermelha à esquerda.
- **O PR**, quando houver: um recorte tracejado, como um papel grampeado, com:
  - o selo em 4x;
  - o link "PR #11 · CI verde" e "no GitHub";
  - à direita, "Ver o patch", que abre o diálogo de sempre.

**A barra de madeira**
- **"Fechar"** fica à esquerda.
- **Com o pedido entregue e o gerente assumido:**
  - o campo "o que falta (para devolver)" e "Devolver", num rosa claro;
  - **com o PR aberto:** a frase "Aceite mesclando o PR no GitHub: o quadro só acompanha.", no lugar do "Aceitar";
  - **sem PR:** "Aceitar", em verde.
- **Com o gerente a caminho do quadro:** "O gerente está indo ao quadro." no lugar dos botões, como hoje.

## 8. Como conferir

- **Os testes de unidade:**
  - a hora em células, com `--:--` sem hora;
  - a coluna do retrato por id;
  - o recorte do rosto;
  - a escala da sala por tamanho de janela (a tabela do §6);
  - o que a ficha quadrada mostra em cada estado.
- **No navegador:**
  - o relógio mostra a hora do mundo e pisca;
  - os chips mostram os bustos;
  - o gerente anda de blazer;
  - a página não passa da janela em 1288 × 720 e em 1456 × 816;
  - um clique na ficha abre a prancheta, e o Esc fecha;
  - o devolver e o aceitar pela ficha aberta;
  - os prints ao lado dos do canvas.
