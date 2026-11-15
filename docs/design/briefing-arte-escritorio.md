# Pedido ao Claude Design: a arte do escritório

Um teste de arte para o escritório do Campsverso, antes de refazer tudo. O que sair daqui vai para a tela de verdade, ao lado da arte LPC de hoje, e o usuário decide olhando (ADR-0079 e o diário de 15/11).

O texto entre as linhas abaixo é o pedido, para colar num projeto novo do Claude Design, com três anexos de `docs/design`: `escritorio-retro-image2.webp`, `escritorio-crescimento.webp` e `escritorio/sprites.js`. O resto deste arquivo é para nós.

---

## O pedido

Quero a arte de um jogo de escritório em pixel art, desenhada em código. O arquivo anexo `sprites.js` mostra o jeito: cada boneco é montado por funções, com os quadros de andar e de trabalhar. Ele é de um protótipo antigo, com o escritório em corte, de lado. Desta vez a vista é outra: **de cima, em 3/4**, como num RPG de 16 bits.

**O alvo de estilo** é a imagem anexa do cubículo (`escritorio-retro-image2.webp`):
- contorno escuro em tudo;
- divisórias de cubículo bege, carpete azul-acinzentado, mesa de madeira;
- monitor de tubo bege com a tela verde, arquivo de aço cinza, plantas em vaso;
- a janela com a cidade ao fundo;
- personagens com a cabeça um pouco grande.

A segunda imagem anexa (`escritorio-crescimento.webp`) mostra a mesma sala crescendo: um dev, depois o dev e o revisor, depois o squad. Desenhe as peças para que a sala possa crescer assim, por peças soltas, e não como uma pintura única.

**Tudo é desenho original seu.** Não copie nem recorte pacotes de terceiros (LPC, itch.io etc.).

### A grade

- Tiles de **32 × 32 px**. A sala tem 20 tiles de largura e 17 de altura.
- Linhas 0 e 1: a parede do fundo, com dois tiles de altura.
- Linhas 2 a 12: o chão da sala, entre as paredes do lado nas colunas 0 e 19.
- Linha 13: a parede de baixo, com a porta na coluna 9.
- Linhas 14 a 16: o corredor, de piso xadrez.

### As peças

Desenhe cada peça numa folha (spritesheet) separada, sobre fundo transparente, com o pé da peça na borda de baixo do tile dela.

1. **O chão e as paredes**, em tiles de 32 × 32:
   - o carpete da sala;
   - o piso do corredor;
   - a parede do fundo em dois tiles: o de cima e o de baixo, com o rodapé;
   - as paredes do lado, vistas de cima;
   - a parede de baixo, com a face curta que dá para o corredor;
   - a porta, fechada e aberta.
2. **Na parede do fundo**, cada uma com dois tiles de altura:
   - a janela com a cidade, de dia e de noite;
   - o relógio, o quadro de avisos pequeno, o bebedouro e a estante.
3. **Os móveis**, em quadros de **96 × 64** (três tiles de largura e dois de altura):
   - **a mesa do dev**, vista do lado de quem senta: o monitor de tubo, o teclado, o telefone e a xícara. Também uma versão com a tela do monitor acesa, com linhas de código em 3 quadros, para animar enquanto o dev trabalha;
   - **a bancada**, uma mesa comprida com a cafeteira e um notebook;
   - **o quadro dos pedidos**, de cortiça, com as fichas coloridas em quatro colunas (a fazer, fazendo, entregue, aceito). Não escreva os nomes das colunas; a tela escreve;
   - **a cadeira de escritório**, vista de costas;
   - **a divisória de cubículo**, em pedaços que se emendam: reta, canto e ponta;
   - **o arquivo de aço, a planta em vaso e a lixeira**.
4. **A copa**, onde o dev almoça e faz as pausas, em quadros de 96 × 64 ou de um tile:
   - a geladeira, o micro-ondas, a pia com o armário e a cafeteira de copa;
   - uma mesa de refeição com duas cadeiras, vistas de lado;
   - a porta do banheiro, com a plaquinha.
5. **Os três personagens**, cada um numa folha de quadros de **64 × 64**. O personagem tem uns 40 a 48 px de altura, com o pé na borda de baixo do quadro.
   - **O Camps,** o dev: barba cheia, óculos, cabelo castanho curto, camisa vermelha, jeans.
   - **O gerente,** um senhor grisalho de bigode: terno grafite, camisa branca, gravata vermelha, sapato preto.
   - **O vigia,** a farda azul-marinho, o boné com aba e a lanterna na mão.

### As animações

Cada animação tem as quatro direções, uma por linha, nesta ordem: **para cima, para a esquerda, para baixo, para a direita**.

| Animação | Quadros por direção | O que é |
|---|---|---|
| andar | 8 | o ciclo de passos; o primeiro quadro é o pé no chão |
| parado | 2 | respirar, piscar |
| usar | 6 | estender a mão para uma coisa à frente: pegar uma ficha no quadro, apertar um botão |
| sentado | 1 | sentado na cadeira; para cima é de costas, com as mãos no teclado |
| digitando | 4 | sentado de costas, digitando (só para cima) |
| beber | 3 | levar o copo ou a xícara à boca, em pé |

O gerente não precisa de sentado nem de digitando.

### A entrega

- **Um único HTML com JavaScript**, como no protótipo, em que cada peça é uma função que desenha num canvas.
- **Uma página de prancha:** mostra todas as folhas lado a lado, com o nome de cada uma, e tem um botão "baixar PNG" por folha (`canvas.toBlob`).
- **Uma prévia da sala montada** com as peças, no tamanho 20 × 17, com a copa num canto, e os três personagens se mexendo:
  - o Camps sentado digitando;
  - o gerente andando pela sala;
  - o vigia parado na porta.
- **Uma paleta só**, declarada no começo do código.
- **Pixel art de verdade:** sem antialiasing e sem degradê, com as cores contadas.

---

## Para nós: o que fazer com a entrega

1. **Guardar** os arquivos que o Claude Design entregar em `docs/design/escritorio-arte/`, sem mudar nada, como foi feito com o protótipo. O Claude Design avulso (claude.ai/design) fecha até 14/12/2026 e passa a viver dentro do Claude: o que importa precisa estar no repositório antes disso.
2. **Gerar os PNGs:**
   - uma ferramenta nossa abre a página num navegador sem tela (Playwright, como os testes da tela) e salva cada folha;
   - os PNGs vão para uma pasta de teste, fora de `cartridges/`.
3. **Montar o manifesto** de teste:
   - as animações entram com a linha da primeira direção e as colunas (`Animation` em `apps/ui/src/art/manifest.ts`);
   - o andar usa `per_tile`;
   - a mesa ganha o quadro da tela acesa.
4. **Ver lado a lado:**
   - o sandbox do escritório com a arte LPC de hoje e com a arte nova;
   - capturas das duas no mesmo minuto do dia;
   - o usuário escolhe.
5. **Se a arte nova ganhar:**
   - ela entra no gênero `office` e no cenário `office_campsverso` no lugar da LPC;
   - os créditos passam a ser só do Campsverso;
   - uma ADR revê a arte LPC da ADR-0077.
6. **Se não ganhar,** o plano B é um pacote comercial de interiores modernos. Conferir a licença antes: em geral ela proíbe redistribuir os arquivos, e o repositório é público.
