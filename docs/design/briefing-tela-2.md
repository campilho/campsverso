# Pedido de tela, 2: o relógio, os retratos e o gerente novo

A continuação do [briefing-tela.md](briefing-tela.md), depois da tela retrô no ar (ADR-0087). O usuário pediu em 22/11:

1. o relógio da barra de baixo como um relógio digital dos anos 90, de 7 segmentos, verde num fundo escuro;
2. um gerente parecido com ele, de camisa social azul e calça bege, com e sem o blazer azul;
3. o retrato dos chips no estilo da referência dele: um busto de frente, e não o recorte do sprite;
4. o gerente antigo, o senhor de terno, continua na arte, para outros usos;
5. mais quatro personagens variados, para os próximos lugares;
6. mais espaço para o monitor. Este item ainda espera a escolha do usuário (§6).

O canvas tem as telas novas: a página 4 mostra o elenco, os retratos e o relógio, e a página 5, o monitor maior. Aqui ficam os números. A regra de sempre vale: a tela desenha o que o estado diz, e nada aqui muda contrato ou regra do mundo.

| Onde | O quê |
|---|---|
| `escritorio-arte/tela/relogio_7seg.png` | os dígitos do relógio, com o `tela.json` atualizado |
| `escritorio-arte/folhas/retratos.png` | os bustos de 40 × 40, com a entrada `retratos` no `metadados.json` |
| `escritorio-arte/folhas/gerente_camisa.png`, `gerente_blazer.png` | o gerente novo, nas duas roupas |
| `escritorio-arte/folhas/tiago.png`, `dandara.png`, `livia.png`, `kenji.png` | o elenco novo |
| `escritorio-arte/previa/elenco.gif` | os seis andando nas quatro direções |

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

**Onde fica:** no lugar da hora em Pixelify 38 da barra de baixo e da faixa do celular. O resto da barra não muda.

**Como desenhar:** cinco `span` com a folha de fundo, um `background-position` por dígito, ou um canvas pequeno. O que for mais simples na moldura.

## 2. Os retratos

**A folha:** `folhas/retratos.png`, com 9 colunas e 2 linhas de 40 × 40.
- A linha 0 é o rosto parado; a linha 1, piscando.
- As colunas, nesta ordem: `gerente_camisa`, `gerente_blazer`, `camps`, `vigia`, `tiago`, `dandara`, `livia`, `kenji` e `gerente` (o antigo).
- No `metadados.json`, `folhas.retratos.retratos` dá a coluna de cada id.
- Os retratos vêm sem fundo: o chip põe a cor.

**Nos chips da barra:** o retrato inteiro em 1x (40 × 40), no lugar do recorte de 38 × 36 do sprite, sobre a cor de fundo de hoje de cada pessoa. Os robôs continuam com o sprite deles.

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
- O avatar `gerente` passa a usar `gerente_camisa`. É a sugestão; o usuário confirma, e a outra é a troca de uma linha.
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

## 6. Em aberto: o monitor maior (não implementar antes do OK do usuário)

A página 5 do canvas mostra uma proposta para dar mais espaço ao monitor:
- a barra de baixo vira o painel do próprio monitor, numa linha só: o relógio, os chips rolando de lado, o "?", o assumir e o escrever pedido;
- a sala escala para a altura toda;
- a coluna da direita fica com 30% da largura, entre 380 e 520 px;
- a barra de cima tem 44 px, e os espaços passam a 8 px.

**Os números, por tamanho de janela:**

| Janela | A sala | A coluna da direita |
|---|---|---|
| 1456 × 816 | 1,27x | 437 px |
| 1288 × 720 (o print do usuário) | 1,08x | 386 px |
| 1728 × 980 | 1,59x | 518 px |

A sala continua 20 × 16 tiles (5:4, quase o 4:3 da TV de tubo). Nada muda no mapa nem no kernel.

**O custo é a escala fracionária.** Num retina, ela ainda fica a 2 px de tela ou mais por pixel. Quando o usuário escolher, o pedido detalhado vem aqui.

## 7. Como conferir

- **Os testes de unidade:**
  - a hora em células, com `--:--` sem hora;
  - a coluna do retrato por id;
  - o recorte do rosto.
- **No navegador:**
  - o relógio mostra a hora do mundo e pisca;
  - os chips mostram os bustos;
  - o gerente anda com a folha nova;
  - os prints ao lado dos do canvas.
