# Pedido de arte: o escritório (v2)

Um teste de arte para o escritório do Campsverso, antes de refazer tudo. O que sair daqui vai para a tela de verdade, ao lado da arte LPC de hoje, e o usuário decide olhando (ADR-0079 e o diário de 15/11).

**Estado (15/11):** a fase 1 foi desenhada pelo Claude numa sessão do Cowork, a partir deste pedido, e está em [escritorio-arte/](escritorio-arte/). À noite ganhou a planta nova, com o banheiro, a copa e a sala de descompressão. Falta o passo 2 em diante de "Para nós".

**O que mudou da v1:**

- o pedido agora tem duas fases. A fase 1 é uma fatia pequena, que basta para decidir; a fase 2 é o resto, e só sai se a arte nova ganhar;
- a imagem de referência passa a valer só para cores, materiais e contorno. A perspectiva dela não entra;
- o pedido agora define âncoras, pegadas, camadas e o mapa das folhas, que o manifesto vai precisar;
- os personagens partem de um corpo-base parametrizável;
- o quadro dos pedidos, a janela e as divisórias passam a ser modulares;
- a página expõe uma API para exportar as folhas sem clicar em nada.

O texto entre as linhas abaixo é o pedido. Os anexos são `escritorio-retro-image2.webp`, `escritorio-crescimento.webp` e `escritorio/sprites.js`. O resto deste arquivo é para nós.

---

## O pedido

Quero a arte de um jogo de escritório em pixel art, desenhada em código. O arquivo anexo `sprites.js` mostra o jeito: cada boneco é montado por funções (cabeça, tronco, braços, pernas), com a aparência vinda de dados. Ele é de um protótipo antigo, com o escritório em corte, de lado. Desta vez a vista é **de cima, em 3/4, como num RPG de 16 bits**.

### O alvo de estilo

Da imagem do cubículo (`escritorio-retro-image2.webp`), aproveite:
- o contorno escuro em tudo;
- as cores e os materiais: divisória bege, carpete azul-acinzentado, mesa de madeira, monitor de tubo bege com a tela verde, arquivo de aço cinza, plantas em vaso, a janela com a cidade;
- os personagens com a cabeça um pouco grande.

**Não aproveite a perspectiva.** A imagem mistura ângulos: as divisórias têm linhas de fuga em diagonal, e o arquivo e o rack estão tortos. Aqui a projeção é a do RPG:
- o chão é de tiles quadrados;
- as alturas sobem na vertical, em escala cheia;
- só se vê a face sul de cada coisa (a que dá para a câmera) e o topo;
- nada vai em diagonal.

Uma divisória que corre de norte a sul aparece só como uma faixa fina, o topo dela.

**Nos personagens, vale o texto, não a imagem.** O homem na porta da imagem não é o gerente.

A segunda imagem (`escritorio-crescimento.webp`) mostra a sala crescendo: um dev, depois o dev e o revisor, depois o squad. Desenhe as peças para que a sala cresça assim, por peças soltas. Os cubículos ficam **abertos para o sul**, para que a divisória não esconda quem está sentado.

**Tudo é desenho original seu.** Não copie nem recorte pacotes de terceiros (LPC, itch.io etc.).

### A grade

- Tiles de **32 × 32 px**. A sala tem 20 tiles de largura e 17 de altura.
- Linhas 0 e 1: a parede do fundo, com dois tiles de altura.
- Linhas 2 a 12: o chão da sala, entre as paredes do lado nas colunas 0 e 19.
- Linha 13: a parede de baixo, com a porta na coluna 9.
- Linhas 14 a 16: o corredor, de piso xadrez.

### As regras de encaixe

- **Quadro e pegada.** Cada peça declara o tamanho do quadro (múltiplos de 32 na largura) e a pegada no chão, em tiles: os tiles que ela ocupa e bloqueia. O quadro pode ser mais alto que a pegada. A altura da peça sobe para os tiles de cima.
- **Âncora.** É o ponto do quadro que coincide com o meio da borda de baixo da pegada. Em quase tudo, ela fica em (largura/2, altura): o pé encosta na última linha do quadro, contorno incluído. Os personagens usam quadros de 64 de largura sobre tiles de 32, com a âncora em (32, 64).
- **Camadas.** A tela desenha por ordem da borda de baixo da pegada. No empate, a ordem é a peça de trás, depois o personagem, depois a peça da frente. A cadeira de escritório vem em duas camadas: o assento e a base atrás, o encosto na frente.
- **Sentado.** O quadro do sentado vai no mesmo lugar do quadro em pé, no tile da cadeira. O corpo já vem desenhado na altura do assento. Para cima (de costas, na mesa), o corpo vem encostado na mesa. A cadeira fica no tile logo abaixo do meio da mesa.
- **Contorno.** Contorne a silhueta de cada peça solta e de cada personagem. Peças que se emendam (paredes, divisórias, carpete) têm contorno só nas bordas expostas, nunca na junta. Os tiles de chão não têm contorno.
- **Espelhar é permitido.** A direita pode ser a esquerda espelhada. Se um acessório trocar de mão, como a lanterna, tudo bem.

### A paleta

- **Uma paleta só, declarada no começo do código, com no máximo 48 cores**, organizadas em rampas: claro, base e sombra de cada material.
- **Nenhuma cor calculada.** Nada de clarear, escurecer ou misturar em tempo de execução. Sombras e luzes são entradas da paleta.
- **Pixel art de verdade:** sem antialiasing, sem degradê (pontilhado pode), sem transparência parcial.
- A página mostra quantas cores foram usadas.

### As peças

Cada peça vai numa folha (spritesheet) separada, sobre fundo transparente.

**1. O chão e as paredes** (tiles de 32 × 32):
- o carpete da sala, em 4 variações para quebrar a repetição, e uma faixa de sombra pontilhada para a linha 2, junto ao rodapé;
- o piso xadrez do corredor;
- a parede do fundo, com o tile de cima (com o topo) e o de baixo (com o rodapé);
- as paredes do lado, vistas de cima (só o topo);
- os quatro cantos: fundo com lado e lado com baixo;
- a parede de baixo, com o topo e a face curta que dá para o corredor;
- a porta na parede de baixo, fechada e aberta, com os batentes.

**2. Na parede do fundo** (quadros de 32 de largura e 64 de altura, nas linhas 0 e 1):
- a janela com a cidade, de dia e de noite, em módulos que emendam: começo, dois meios diferentes e fim;
- o relógio e o quadro de avisos pequeno;
- **o quadro dos pedidos**, de cortiça, em módulos de um tile: começo, meio e fim. **Cada módulo é uma coluna**, e 4 colunas são 4 tiles; com 5 colunas, entra mais um meio. No alto de cada coluna fica uma faixa clara vazia, onde a tela escreve o nome. Não escreva os nomes;
- as **fichas**, como sprites soltos de uns 10 × 8 px, em 5 cores (o tipo do pedido). A tela as põe nas colunas conforme o estado real. Uma versão com as fichas pregadas fica só na prévia;
- o quadro branco da especificação (64 × 64), em branco, porque a tela escreve.

**3. Os móveis** (cada um com o seu quadro e a sua pegada):

| Peça | Quadro | Pegada | Quadros |
|---|---|---|---|
| mesa do dev, vista do lado de quem senta: monitor de tubo, teclado, telefone, xícara | 96 × 64 | 3 × 1 | 4: tela apagada e 3 de código rolando |
| cadeira de escritório, de costas | 32 × 64 | 1 × 1 | 3: base (atrás), encosto (frente), inteira (vazia) |
| rack do servidor, com o botão vermelho de publicar | 32 × 64 | 1 × 1 | 3: LEDs A, LEDs B, botão apertado |
| divisória de cubículo | 32 × 64 | 1 × 1 | 16 (abaixo) |
| arquivo de aço | 32 × 64 | 1 × 1 | 1 |
| planta em vaso | 32 × 64 | 1 × 1 | 1 |
| lixeira | 32 × 32 | 1 × 1 | 1 |
| bancada, com cafeteira e notebook | 96 × 64 | 3 × 1 | 1 |
| impressora matricial (vai sobre a mesa ou a bancada) | 32 × 32 | – | 2: parada, imprimindo |
| mesa redonda de reunião | 96 × 64 | 3 × 2 | 1 |

**A divisória é um autotile de 16 peças.** Cada peça liga o centro do tile aos vizinhos marcados numa máscara de 4 bits (norte = 1, leste = 2, sul = 4, oeste = 8). A folha tem 4 × 4 quadros, na ordem da máscara (0 a 15). A divisória corre pelo centro do tile, tem uns 28 px de altura e um topo de 4 a 5 px. Os trechos leste-oeste mostram a face sul; os trechos norte-sul mostram só o topo, e a ponta sul mostra a face.

**4. O banheiro, a copa e a sala de descompressão** (a planta está em "Para nós"):

| Peça | Quadro | Pegada | Quadros |
|---|---|---|---|
| o banheiro: um bloco com teto, para não ver dentro, e duas portas na face sul, masculino e feminino, com a plaquinha; quem entra some e volta depois | 128 × 96 | 4 × 3 | 3: fechado, a do masculino aberta, a do feminino aberta |
| a geladeira | 32 × 64 | 1 × 1 | 2: fechada, aberta (com as marmitas) |
| o balcão da copa, com a pia e o micro-ondas | 96 × 64 | 3 × 1 | 2: micro-ondas desligado e ligado |
| a máquina de café, sobre um armarinho | 32 × 64 | 1 × 1 | 2: parada, servindo |
| o bebedouro, com o garrafão | 32 × 64 | 1 × 1 | 2: as bolhas |
| a mesinha redonda da copa | 32 × 64 | 1 × 1 | 1 |
| a cadeira da copa, de lado | 32 × 64 | 1 × 1 | 2: virada para a direita e para a esquerda |
| o sofá de costas, virado para a TV | 96 × 64 | 3 × 1 | 1 |
| o sofá de lado | 32 × 96 | 1 × 2 | 1 |
| o móvel com a TV de tubo, o videogame e os cartuchos | 64 × 64 | 2 × 1 | 3: desligada e 2 de jogo |
| o puff | 32 × 32 | 1 × 1 | 3 cores |
| o tapete da descompressão, em 9 peças (cantos, bordas, miolo) | 32 × 32 | 1 × 1 | 9 |

O rack do servidor fica para o futuro: a folha existe, mas ele sai da sala por enquanto.

### Os personagens

Monte os personagens a partir de **um corpo-base parametrizável**: pele, cabelo e penteado, barba e bigode, óculos, camisa, calça, sapato e acessório (paletó com gravata, boné, lanterna). Cada personagem é uma configuração desse corpo. Assim, quem chegar depois (o revisor, o squad) sai da mesma base.

- **O Camps,** o dev: barba cheia, óculos, cabelo castanho curto, camisa vermelha de manga comprida, jeans, sapato marrom.
- **O gerente,** um senhor grisalho de bigode: terno grafite, camisa branca, gravata vermelha, sapato preto.
- **O vigia:** farda azul-marinho, boné com aba e a lanterna na mão.

Os quadros são de **64 × 64**. O personagem tem de 44 a 46 px de altura, com a âncora em (32, 64).

### As animações e o mapa da folha

Todos os personagens usam **a mesma folha**: 8 colunas (512 px) e 23 linhas. O que um personagem não tem fica transparente, para o manifesto ser o mesmo para todos. As direções vêm nesta ordem: **para cima, para a esquerda, para baixo, para a direita**.

| Linhas | Animação | Quadros | O que é |
|---|---|---|---|
| 0–3 | andar | 8 | o ciclo de passos, um tile por ciclo; o quadro 0 é o pé no chão |
| 4–7 | parado | 2 | respirar e piscar |
| 8–11 | usar | 6 | estender a mão para uma coisa à frente: pegar uma ficha, apertar o botão |
| 12–15 | sentado | 1 | na cadeira; para cima é de costas, com as mãos no teclado |
| 16 | digitando | 4 | sentado de costas, digitando (só para cima) |
| 17–20 | beber | 3 | levar o copo ou a xícara à boca, em pé |
| 21–22 | comer sentado | 4 | à mesa da copa, para a esquerda e para a direita |

O gerente não tem sentado, digitando nem comer.

A rotina do dev (ADR-0080) vai pedir animações novas: carregar a marmita andando, jogar videogame sentado no sofá (de costas) e cochilar no puff. Elas entram **só no fim da folha**, a partir da linha 23, para não mexer nas linhas que o manifesto já usa.

### A entrega

- **Um único HTML com JavaScript**, em que cada peça é uma função que desenha num canvas.
- **Uma prancha:** todas as folhas lado a lado, ampliadas, com o nome, o tamanho do quadro e um botão "baixar PNG" por folha (`canvas.toBlob`).
- **Uma prévia da sala montada**, em 20 × 17, com o Camps sentado digitando, o gerente andando pela sala e o vigia parado na porta. Tem uma chave de dia e noite.
- **Uma API para exportar sem clicar:**
  - `window.folhas()` devolve `{ nome: dataURL }`;
  - `window.metadados()` devolve, para cada folha, o tamanho do quadro, as colunas, as linhas, a pegada, a âncora, a camada e o mapa de animações;
  - `window.quadroPrevia(i, { noite })` devolve o quadro `i` da prévia, em passos de 100 ms.
- **Tudo determinístico:** nada de `Math.random` sem semente. Rodar duas vezes dá os mesmos pixels.

### As fases

**Fase 1 (a fatia, que decide):**
- a paleta inteira;
- o carpete, o corredor, as paredes, os cantos e a porta;
- a janela (dia e noite) e o relógio;
- o quadro dos pedidos com as fichas;
- um cubículo completo: a mesa com a tela animada, a cadeira nas duas camadas, as 16 divisórias e o rack;
- o arquivo, a planta e a lixeira;
- o Camps andando, parado, sentado e digitando;
- o gerente andando e parado;
- o vigia andando e parado;
- a prévia.

**Fase 1, segunda parte (15/11, à noite):** a sala na planta nova, com o banheiro, a copa e a sala de descompressão.

**Fase 2 (só se a arte nova ganhar):**
- as animações da rotina: usar, beber, comer sentado, carregar a marmita, jogar videogame e cochilar;
- a bancada dos robôs, a impressora, a mesa de reunião e o quadro branco;
- o revisor e o squad, a partir do corpo-base.

---

## Para nós: o que fazer com a entrega

### A planta proposta (15/11, à noite)

O usuário pediu os cubículos mais para cima e para a esquerda, o quadro dos pedidos à esquerda, o banheiro no canto de baixo à esquerda, a copa no canto de baixo à direita e a sala de descompressão no canto de cima à direita. A prévia segue esta planta. Ela **difere da bíblia §3 e do `map.tmj` de hoje** (ADR-0080, com a copa à direita no meio e a porta do banheiro na parede de baixo): quem cuida do mapa decide e registra. Coordenadas em tiles, (coluna, linha):

| Coisa | Tiles |
|---|---|
| Quadro dos pedidos | na parede, colunas 2 a 5; o gerente fica na linha 2, de frente para ele |
| Janela | na parede, colunas 7 a 11 |
| Relógio | na parede, coluna 12 |
| Arquivos | (12, 2) e (13, 2) |
| Divisórias | a linha 3, das colunas 2 a 10; e as colunas 2, 6 e 10, nas linhas 4 e 5 |
| Mesa do Camps | (3 a 5, 4); a cadeira em (4, 5); a lixeira em (5, 5) |
| Mesa vaga | (7 a 9, 4); a cadeira em (8, 5) |
| Sala de descompressão | o tapete de (14, 3) a (18, 6); o móvel da TV em (15 e 16, 2); o sofá de costas em (15 a 17, 5); o sofá de lado em (18, 3 e 4); os puffs em (14, 3), (17, 3) e (14, 5) |
| Banheiro | o bloco de (1, 9) a (4, 11); as portas em (2, 11), masculino, e (3, 11), feminino, usadas de (2, 12) e (3, 12) |
| Copa, a linha da cozinha | a lixeira em (12, 9), a máquina de café em (13, 9), o balcão com a pia e o micro-ondas em (14 a 16, 9), a geladeira em (17, 9), o bebedouro em (18, 9); tudo usado da linha 10, de frente para cima |
| Copa, as mesinhas | (12, 11), (15, 11) e (18, 11); as cadeiras de lado em (11, 11), (13, 11), (14, 11), (16, 11) e (17, 11) |
| Plantas | (1, 2), (1, 7) e (18, 7) |
| Porta | (9, 13); o vigia em (9, 14), no corredor |
| Rack do servidor | fora, para o futuro |

### Os passos

1. **Guardar** os arquivos em `docs/design/escritorio-arte/`, sem mudar nada. O Claude Design avulso (claude.ai/design) fecha até 14/12/2026 e passa a viver dentro do Claude: o que importa precisa estar no repositório antes disso.
2. **Gerar os PNGs.** Uma ferramenta nossa abre a página num navegador sem tela (Playwright, como os testes da tela), chama `window.folhas()` e `window.metadados()` e salva tudo numa pasta de teste, fora de `cartridges/`.
3. **Montar o manifesto** de teste a partir de `metadados()`:
   - as animações entram com a linha da primeira direção e as colunas (`Animation` em `apps/ui/src/art/manifest.ts`);
   - o andar usa `per_tile`;
   - a mesa ganha os quadros da tela acesa;
   - a divisória entra como autotile por máscara;
   - o quadro dos pedidos se monta por colunas, com as fichas por cima.
4. **Ver lado a lado:**
   - o sandbox do escritório com a arte LPC de hoje e com a arte nova;
   - capturas das duas no mesmo minuto do dia;
   - o usuário escolhe.
5. **Se a arte nova ganhar:**
   - pedir a fase 2;
   - ela entra no gênero `office` e no cenário `office_campsverso` no lugar da LPC;
   - os créditos passam a ser só do Campsverso;
   - uma ADR revê a arte LPC da ADR-0077.
6. **Se não ganhar,** o plano B é um pacote comercial de interiores modernos. Conferir a licença antes: em geral ela proíbe redistribuir os arquivos, e o repositório é público.

### Decisões em aberto

- **Os agentes são humanos ou robôs?** O protótipo tinha robôs retrô (o revisor de pernas com lupa, o integrador de monociclo, o pesquisador drone, o mensageiro de tubo). A imagem do crescimento mostra humanos. O corpo-base humano serve ao squad humano. Se forem robôs, a fase 2 precisa de corpos-base de robô, um por tipo, nas mesmas regras de folha.
- **A altura da parede do fundo.** Com dois tiles (64 px) e o personagem de 46 px, o pé-direito fica baixo, e a cidade na janela fica apertada. Se a grade puder mudar, três tiles ficam mais perto da imagem.
