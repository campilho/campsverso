# Pedido de arte: os balões, a fonte, o corredor e as plantas

Os ajustes finos da tela do escritório, depois dos prints de 18/nov: o rótulo da ação sobre a cabeça, o balão de fala, o corredor que puxa o olho e as plantas iguais. O texto entre as linhas abaixo é o pedido; o usuário o dispara para o Claude Design na mesma sessão que fez a arte do escritório e a bancada ([briefing-arte-bancada.md](briefing-arte-bancada.md)), com a imagem [rotulos-antes.png](rotulos-antes.png) anexada.

---

## O pedido

Continuando a arte do escritório que você já fez (as folhas e o `metadados.json` em `docs/design/escritorio-arte/folhas/`), quero cinco ajustes. **Todas as regras de antes valem:**
- a grade de 32 × 32;
- a vista de cima em 3/4, com só a face sul e o topo;
- o contorno e as camadas, com a âncora no meio da borda de baixo da pegada;
- pixel art sem antialiasing, sem degradê e sem transparência parcial;
- tudo desenho original seu.

**A paleta continua a mesma** (47 cores). Use as que existem; se faltar uma, acrescente no máximo uma, sem passar de 48, com o par de penumbra e de escuro na tabela da luz.

### O que está feio hoje

A imagem anexa mostra três recortes da sala. Sobre a cabeça de quem faz alguma coisa, a tela escreve o nome da ação:
- na fonte monoespaçada do sistema, amarela e em negrito;
- numa caixa escura sem borda, com a barra de progresso solta embaixo.

Os problemas:
- não parece parte do jogo;
- é largo: "Jogando videogame" ocupa quatro tiles;
- cobre o monitor do dev, que agora mostra o que ele faz;
- quando duas pessoas fazem a mesma coisa lado a lado, no sofá ou na mesa da copa, os rótulos se encavalam.

O balão de fala é uma caixa branca sem ponta, na mesma fonte.

### 1. O balão de ação, com um ícone

O texto sobre a cabeça vira um balão pequeno com um ícone. O nome da ação continua na tela, ao passar o mouse sobre a pessoa, e no painel.

| Peça | Quadro | Âncora | O que é |
|---|---|---|---|
| o balão | 24 × 24 | (12, 24) | o corpo claro com contorno e cantos arredondados em pixel, e uma ponta de 3 a 4 px embaixo, no meio, que aponta para a cabeça |
| cada ícone | 16 × 16 | | desenhado para caber no miolo do balão |

- **O miolo:** declare no `metadados.json`, na entrada do balão, `miolo: [x, y]`, o canto de cima à esquerda onde o ícone pousa.
- **O progresso:** um fio de 1 ou 2 px na base do corpo do balão, que enche da esquerda para a direita. A tela desenha o fio. Declare `progresso: { x, y, largura, altura, trilho, cheio }`, com o trilho e o cheio como nomes de cores da paleta.
- **À noite,** o balão não escurece: é informação, não cenário. Fica acima da luz, como as luzes emissivas.

**Os ícones do escritório:**

| Nome | O que mostra | Ações |
|---|---|---|
| `trabalhar` | um teclado, ou `</>` | `work` |
| `pedido` | uma ficha do quadro com um lápis | `write_ticket`, `take_ticket` |
| `entregar` | a ficha com um sinal de certo | `deliver`, `accept_ticket` |
| `devolver` | a ficha com uma seta de volta | `return_ticket` |
| `agua` | um copo d'água | `drink` |
| `cafe` | uma xícara com fumaça | `coffee` |
| `banheiro` | um símbolo neutro (um rolo de papel, por exemplo) | `restroom` |
| `marmita` | a marmita fechada | `fridge` |
| `esquentar` | a marmita com ondas de calor | `microwave` |
| `comer` | o garfo e a faca, ou um prato | `lunch` e o comer da fazenda |
| `lixo` | a lixeira | `trash` |
| `tv` | uma TV pequena | `tv` |
| `videogame` | um controle | `videogame` |
| `dormir` | "Zz" | o sono |

**Os ícones da fazenda.** A mesma tela serve as fazendas:

| Nome | O que mostra | Ações |
|---|---|---|
| `plantar` | um broto saindo da terra | plantar |
| `regar` | um regador | regar |
| `colher` | um cesto com um rabanete | colher |
| `cavar` | uma enxada | cavar e limpar o canteiro |
| `bau` | um baú | guardar e pegar do baú |
| `dinheiro` | uma moeda | vender e comprar |
| `cozinhar` | uma panela no fogo | cozinhar, o tacho |
| `adubar` | um saco de adubo | adubar e compostar |
| `encomenda` | uma caixa com etiqueta | aceitar e entregar a encomenda |
| `fincar` | uma estaca | fincar |
| `mandar` | uma mão que aponta | as ordens ao ajudante, contratar e dispensar |

**A folha:** `icones.png`, com 8 colunas de 16 × 16, na ordem das duas tabelas. No `metadados.json`, `icones: { nome: [coluna, linha] }`.

**Sem ícone:**
- andar, esperar e falar não mostram balão: a animação e a fala já dizem;
- uma ação que não tiver ícone vai na etiqueta escura (item 2), com o nome curto.

### 2. A etiqueta escura e o balão de fala, em nove partes

Duas molduras que a tela estica no tamanho do texto (nove fatias: quatro cantos, quatro bordas e o miolo, cada parte de 8 × 8):

| Peça | Fundo | Ponta | Para quê |
|---|---|---|---|
| a etiqueta | escuro, com contorno | nenhuma | o nome da ação ao passar o mouse, e a ação sem ícone |
| o balão de fala | claro, com contorno | uma peça à parte, de 8 × 8, que a tela põe embaixo, no meio | o que a pessoa disse, com até três linhas |

**A folha:** `baloes.png`, com o balão de ação, as duas molduras e a ponta onde couber. No `metadados.json`, `pecas: { acao: [x, y, l, a], fala: [x, y, 24, 24], fala_ponta: [x, y, 8, 8], etiqueta: [x, y, 24, 24] }`, e a cor do texto em cada moldura.

### 3. A fonte

Uma fonte pixel sua, para todo texto dentro da sala: a etiqueta, a fala e os nomes.
- **O tamanho:** cada glifo numa célula de 8 × 12 px; as maiúsculas com 7 px de altura e as descendentes (g, j, p, q, y) com 2 px; a largura varia de 1 a 7 px; a tela põe 1 px entre as letras.
- **A cor:** desenhe em branco; a tela tinge com a cor de cada moldura.
- **Os caracteres:**
  - A–Z, a–z e 0–9;
  - `. , ; : ! ? ' " ( ) - – / % + = × … @ # &`;
  - os acentos do português: á à â ã é ê í ó ô õ ú ü ç, e as maiúsculas Á À Â Ã É Ê Í Ó Ô Õ Ú Ç.
- **A legibilidade:** a fonte deve ser legível no tamanho do pixel do jogo (a tela dobra).

**A folha:** `fonte.png`, com 16 colunas de células. No `metadados.json`: `fonte: { celula: [8, 12], base: <a linha de base, em px>, glifos: "<os caracteres na ordem da folha>", larguras: [<a largura de cada um>] }`.

### 4. O corredor mais discreto

O chão em xadrez do corredor (`corredor.png`) puxa o olho para fora da sala. É claro, tem contraste demais e não muda à noite.

**De dia:** redesenhe o piso mais escuro e mais calmo que o carpete da sala, em dois tons próximos. Pode ser um granilite, ou um piso liso com rejunte discreto.

**À noite:** o corredor deixa de ser sempre aceso e fica na penumbra, a luz fraca do prédio. As faces que dão para ele também ficam (a parede de baixo e o banheiro). A janela continua como está. Atualize `luz.sempreAceso` no `metadados.json` e a prévia.

Do nosso lado, o corredor encolhe de três linhas para duas.

### 5. Duas plantas novas

A `planta.png` ganha dois quadros (três colunas), cada um de 32 × 64, com a pegada 1 × 1 e a âncora (16, 64), como a de hoje:

| Coluna | Planta |
|---|---|
| 0 | a de hoje |
| 1 | uma espada-de-são-jorge alta, num vaso de cerâmica |
| 2 | uma costela-de-adão mais larga, num cesto de palha |

No `metadados.json`, `quadros: ["planta", "espada-de-são-jorge", "costela-de-adão"]`.

### A entrega

- **As folhas novas e as atualizadas** vão para `docs/design/escritorio-arte/folhas/`: `baloes.png`, `icones.png`, `fonte.png`, `corredor.png` e `planta.png`.
- **O `metadados.json` ganha as entradas novas** no formato das outras, com os campos dos itens acima.
- **A prévia** (`escritorio-arte.html`) mostra:
  - o dev na mesa com o balão `trabalhar` e o progresso pela metade;
  - o dev e o gerente no sofá, cada um com o seu balão `videogame`, sem se encavalar;
  - uma fala longa ("Anotado. Começo depois do café.");
  - a etiqueta com "Jogando videogame";
  - o corredor de dia e à noite;
  - as três plantas na sala.
- **A API de exportar folhas** da página passa a exportar as peças novas, sem precisar clicar em nada.
- **Não escreva texto** nos ícones, a não ser o "Zz".

---

## Para nós

**Já feito, antes da arte:**
- andar, esperar e falar não mostram rótulo sobre a cabeça; o retrato do HUD continua dizendo;
- dois rótulos iguais lado a lado viram um só, entre os dois, e rótulos diferentes que se tocam se empilham;
- o corredor tem duas linhas em vez de três e fica na penumbra à noite, e as faces que dão para ele também.

**A arte chegou na noite de 18/nov e entrou na tela em 19/nov** (o adendo de 19/nov da ADR-0082). O plano era este:
- o manifesto do escritório (`art.json`) ganha os balões, ação → ícone; a tela desenha o balão sobre a cabeça, com o fio do progresso;
- a ação sem ícone vai na etiqueta, e o nome completo aparece ao passar o mouse;
- a fonte vira uma fonte de bitmap do Phaser, gerada do `metadados.json` pelo `make arte-escritorio`; a fala e as etiquetas passam a usá-la;
- o corredor novo entra pelo `make arte-escritorio` e pelo `make mapa-visual`;
- cada planta ganha uma espécie no mapa (`especie`), e o manifesto escolhe o quadro, como a cor dos pufes.

**O relógio** já mostra a hora do mundo desde 15/nov (ADR-0082): o ponteiro das horas anda e o dos minutos fica no 12.
