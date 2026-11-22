# Pedido de tela, 4: o menu, os comandos, os créditos, o quadro com quatro colunas e o interruptor

A continuação do [briefing-tela-3.md](briefing-tela-3.md), pedida pelo usuário em 22/11. São cinco partes:

1. As três janelas que ainda estão no visual antigo passam para o padrão da tela retrô:
   - o menu do clique direito;
   - os comandos (o `?` do monitor);
   - os créditos (pelo Sobre).
2. O quadro da parede ganha a quarta coluna. Hoje ele tem três, e a tela mostra "Entregue" e "Aceito" juntos na terceira.
3. O interruptor sumiu da sala. Abaixo, onde ele se perdeu e como corrigir.

**O que não muda:**
- o contrato, a projeção e o kernel, fora a correção do item 3;
- o que cada janela mostra: só a forma muda;
- quem decide uma ação continua sendo o kernel. O menu só mostra.

O canvas tem a página 7, "o menu, os comandos e os créditos". Nas telas dela as janelas abrem de verdade: o clique no sofá, o `?` e o "Créditos" do Sobre. Os prints estão em `escritorio-tela/`:

| Arquivo | O quê |
|---|---|
| `menu.webp` | o print 1 refeito: o menu do sofá, colado ao clique |
| `comandos.webp` | o print 2 refeito: os comandos, sobre a tela escurecida |
| `creditos.webp` | o print 3 refeito: os créditos do escritório |
| `janelas.webp` | as variantes: o menu em seis casos, os comandos do escritório e da fazenda, os créditos do escritório e da fazenda |

---

## 1. A moldura das três janelas

É a mesma do Sobre, da prancheta e da ficha aberta.

- **Bisel creme:**
  - borda de 3 px `#1b1726`;
  - fundo `#e7d9b4`;
  - luz `inset 3px 3px 0 #f4ead0`;
  - sombra `inset -4px -4px 0 #ae9b72`;
  - sombra de fora `0 18px 44px rgba(0, 0, 0, .55)`.
- **A barra de título listrada do Mac clássico,** com 28 px:
  - a classe `.listras` que a tela já tem;
  - a caixinha de fechar de 18 px à esquerda;
  - o título no meio, em Pixelify Sans 700, 14 px, sobre um retalho creme.
- **Os botões** são os da prancheta:
  - o principal amarelo `#f2c94c`, com a sombra `#d49b5d`;
  - o secundário creme `#f4ead0`.

## 2. O menu do clique direito (`panels/menu.ts`)

O print 1 era uma lista solta com um "Fechar" embaixo. Agora o menu é uma janelinha com o título na barra, um ícone por ação e o porquê de cada coisa.

### Onde abre

- **Colado ao ponto do clique,** com um rabicho de 13 px apontando para ele.
  - O ponto do clique ganha uma bolinha amarela de 8 px.
  - O menu abre à direita do clique e vira para a esquerda quando não cabe; o rabicho vai junto.
  - Ele sobe quando não cabe embaixo e nunca sai da tela do monitor.
- **A coisa clicada ganha um contorno tracejado amarelo** de 2 px (`#f2c94c`, raio 4) no retângulo do sprite, enquanto o menu está aberto.
- **Para fechar:** clicar fora, `Esc` ou a caixinha da barra. O botão "Fechar" sai.

### As linhas

- **Cada linha é um botão** `role="menuitem"` de 44 px de altura. Ela tem:
  - o ícone de 32 px (o de 16 px da folha `icones`, em 2x);
  - o rótulo em Inter 600, 14 px;
  - embaixo, o `detail`, em 12 px `#563521`.
- **O ícone** vem do mesmo mapa dos balões: `bubbles.icons.actions` no `art.json` do gênero `office`, com os quadros do `baloes.json`.
  - Uma ação sem ícone ganha uma bolinha vazada de 8 px, como no "Andar até aqui".
  - Uma entrada só da tela, como o "Ver a tela" do dev, usa o mesmo desenho.
- **Foco e mouse em cima:**
  - fundo `#f2c94c`;
  - borda de 2 px `#1b1726`;
  - um `↵` pequeno à direita da linha com foco.
- **Uma ação que não vale agora** (`blocked`):
  - continua na lista, com `aria-disabled="true"` e o cursor `not-allowed`;
  - o ícone fica a 40%, em cinza;
  - o motivo aparece em itálico, 12 px, `#7e5032`;
  - exemplo: "Acender a luz · a luz já está acesa".
- **Os parâmetros:** a ação que tem o que escolher vira um bloco.
  - O bloco tem o fundo `#f4ead0` e um anel `#cdbb8f`.
  - Os campos ficam embaixo da linha, recuados 48 px.
  - Cada campo tem o rótulo em 12 px 600 `#563521` (mínimo 58 px) e:
    - o `select` com a borda de 2 px, o fundo `#f6f2e8` e o triângulo desenhado; ou
    - o número com `−` e `+` nas pontas.
- **A ficha da opção** (o `option-sheet`): o retrato de 40 px e a nota, numa caixa clara embaixo do campo. Ela muda com o campo.
- **O interior de um contêiner** (o `contents`) fica em cima das linhas, num bloco "Dentro":
  - à direita, "ocupa X de Y" em JetBrains Mono;
  - uma régua de 12 células numa moldura escura, cada coisa com a cor da sua amostra e o resto claro;
  - a lista: a amostra, o nome ×quantidade e, à direita, "ocupa N" em 11 px.
- **Nada a fazer:** "Nada a fazer aqui." em itálico, numa janela pequena sem rodapé.
- **O rodapé:** "**shift** + clique põe na fila · **Esc** fecha", em 11 px.

### O teclado e o leitor de tela

- O menu é `role="menu"`, com `aria-labelledby` apontando para o título.
- Ao abrir, o foco vai para a primeira linha pronta.
- `↑` e `↓` andam pelas linhas prontas.
- `Enter` faz a ação.
- `shift + Enter` e `shift + clique` põem a ação na fila e deixam o menu aberto, como hoje.

### Os ícones novos da luz

A folha `icones.png` ganhou dois quadros nos espaços livres, sem mudar o tamanho da folha. O `metadados.json` já os traz.

| Quadro | Coluna, linha | Ação |
|---|---|---|
| `acender`, a lâmpada amarela com o brilho | 6, 3 | `light_on` |
| `apagar`, a lâmpada cinza | 7, 3 | `light_off` |

Rode `make arte-escritorio` e acrescente `"light_on": "acender", "light_off": "apagar"` em `bubbles.icons.actions`. O balão sobre a cabeça de quem acende a luz ganha o ícone de graça.

## 3. Os comandos (`panels/help.ts`)

O print 2 era uma lista de texto com "Entendi". Agora é uma janela "Comandos" sobre a tela escurecida (`rgba(23, 20, 31, .62)`, como o Sobre), com 660 px de largura e duas colunas.

- **Mouse:**
  - um mouse desenhado de 20 × 28 px, com o botão da vez em amarelo;
  - ao lado, o nome do gesto em mono 11 px: "clique", "direito", "arrastar";
  - o `shift` + clique é a tecla mais o mouse.
- **Teclado:**
  - teclas de 28 px, com a borda de 2 px, o fundo `#f6f2e8`, a sombra de baixo `#cdbb8f` e o texto em JetBrains Mono 700, 12 px;
  - as setas em T invertido.
- **Só aparece o que vale neste mundo e nesta tela:**
  - "da grama" no texto do clique direito: só na fazenda;
  - "arrastar" e "espaço": só quando o mapa é maior que a tela, porque no escritório a sala cabe inteira;
  - "P": só quando a tela pode pausar, no sandbox.

  Com isso, a lista `COMMANDS` vira uma função de três coisas: o gênero do mundo, a câmera e o poder de pausar.
- **Embaixo,** "Aparece sozinha na primeira vez que você assume; depois, pelo **?** do monitor.", e o botão "Entendi" em Pixelify. O "Entendi" guarda o já-visto como hoje.

## 4. Os créditos (`panels/credits.ts`)

O print 3 era uma lista escura e longa, uma linha por arquivo, com a frase "Pixel art do Liberated Pixel Cup (LPC)…". **Essa frase está errada no escritório:** toda a arte dele é desenho próprio, MIT.

A janela nova tem 740 px de largura, com a altura da tela no máximo e o meio rolando.

- **O cabeçalho:**
  - o ícone do Campsverso;
  - "Quem fez o escritório" (ou "a fazenda") em Pixelify 22;
  - a frase de abertura;
  - as pílulas de resumo: as peças, os grupos de autores e as licenças.
- **A frase de abertura sai dos dados:**
  - **Nenhuma linha aponta para o opengameart:** "Toda a arte deste mundo é desenho próprio do Campsverso, feito em código. As fontes vêm junto com a tela."
  - **Senão:** "A arte vem do Liberated Pixel Cup (LPC) e de quem a estendeu; o que faltava foi desenhado no mesmo estilo. Cada bloco junta as peças de um mesmo grupo de autores, com as licenças."
- **Um bloco por grupo de autores,** juntando as linhas de todas as camadas com os mesmos `authors` e `licenses`. Cada bloco tem:
  - os autores em negrito;
  - as licenças em selos: MIT verde, CC-BY-SA amarelo, GPL laranja, CC0 cinza, OFL azul;
  - o link em mono 11 px;
  - os arquivos como fichinhas em mono 12 px, cada uma com a nota no `title`;
  - um `<details>` "o que cada peça é", com as notas.
- **As linhas que remetem a outro arquivo** (`ver cartridges/office/art/CREDITS.csv`, o `map-visual.tmj`) entram como uma fichinha no bloco das peças que elas montam. No escritório, isso dá um bloco só, com 31 fichinhas.
- **As fontes da tela** ficam num bloco tracejado, todas OFL 1.1:
  - Pixelify Sans, de Stefie Justprince;
  - Inter, de Rasmus Andersson;
  - JetBrains Mono, da JetBrains;
  - Patrick Hand, de Patrick Wagesreiter.

  A lista sai do que o `main.ts` importa. Se a tela do dev adotar a VT323 (de Peter Hull), ela entra aqui.
- **No pé da janela:** "dos arquivos `CREDITS.csv` de cada camada", "Voltar ao Sobre" e "Fechar".
- **No Sobre,** o "Créditos" vira um botão que abre esta janela no lugar dele. O "Voltar ao Sobre" volta.

## 5. O quadro da parede com quatro colunas

A arte já serve: o `quadro_pedidos.png` é feito de módulos de começo, meio e fim, um por coluna, e a quarta coluna é um meio a mais. **A mudança é só no cartucho `office_campsverso`:**

- **`art/decor.json`:** as peças do quadro na linha 0 passam a ser:

  | Coluna | Peça |
  |---|---|
  | 2 | `quadro-comeco` |
  | 3 | `quadro-meio` |
  | 4 | `quadro-meio` |
  | 5 | `quadro-fim` |

  A janela continua nas colunas 7 a 11; a coluna 6 fica livre. O texto do `about` passa de "três colunas" para quatro.
- **`art/art.json`, em `cards.columns`:** `"aceito": 3`. Antes era 2, e as fichas aceitas caíam por cima das entregues.
  - O resto não muda: `x: 64`, `column_width: 32`, `first_inset: 6` e `inset: 3`.
  - A coluna 3 começa em `x = 64 + 3 × 32 = 160`, o tile 5, que é o módulo de fim.

As prévias `sala_noite` e `sala_versao` em `escritorio-arte/previa/` já mostram o quadro com quatro módulos. As outras prévias ainda mostram três, até a próxima vez que forem regravadas.

## 6. O interruptor: onde ele se perdeu

**Nada foi apagado.** A arte, o `kind` `light_switch` no `art.json` e o lugar no `escritorio.yaml` (`light_switch: { x: 10, y: 13 }`) estão todos no `main`.

**O que falta é a entidade, no mundo ao vivo:**
- **Quem cria o interruptor:** o sistema `lights` (ADR-0088) cria a entidade `interruptor` quando ela falta. Ele roda em dois gatilhos: `OnSessionStart()` e o `DailyAt` das 18:00 e das 21:00.
- **Por que ele nunca rodou:** o `office-campsverso-01` foi criado antes da ADR-0088 e volta de um snapshot a cada `make escritorio`.
  - No caminho da recuperação, `recovery.py` devolve o mundo "pronto" sem chamar `KernelCore.start()`.
  - Então nenhum sistema `OnSessionStart` roda num mundo retomado.
  - Conferido em 22/11: o snapshot das 17:00 e a projeção das 17:32 não têm `interruptor`.
- **O que deve acontecer:** o `DailyAt` das 18:00 deve criá-lo hoje. Até lá, a sala fica sem ele.

**A correção proposta** é um destes caminhos, nesta ordem de preferência:

1. **O kernel roda os sistemas `OnSessionStart` também ao retomar um mundo.**
   - A sessão começa nos dois casos.
   - Os sistemas desse gatilho precisam ser idempotentes. O `lights` já é: só cria o que falta.
   - Com isso, toda peça nova de um cartucho aparece em mundos antigos na primeira subida.
2. **Ou o `lights` também roda a cada minuto enquanto o interruptor não existe.** É mais simples, mas o problema volta na próxima peça que nascer da mesma forma.

**O teste e2e:**
1. Retomar um snapshot sem o interruptor.
2. Dar um passo.
3. Conferir que a entidade existe, apagada antes das 18:00 e acesa depois.

Ajuste também a docstring do `lights`, que promete o interruptor "ao começar a sessão".

**A arte do interruptor também foi refeita** (`escritorio-arte/folhas/interruptor.png`, 64 × 32: dois quadros de 32 × 32, apagado e aceso).
- O espelho branco tem o contorno escuro e a sombra na parede.
- Ele fica na faixa creme da parede de baixo, à direita da porta.
- Aceso, a tecla de cima clareia e um led âmbar de 1 px acende, emissivo à noite.
- Ela pode substituir a que o `office_art.py` gera hoje, a placa creme de 10 × 12. A pegada, a âncora e os quadros são os mesmos do `art.json` (`frame` 0 e 1 em `acesa`).
