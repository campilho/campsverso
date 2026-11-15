# Arte do gênero office

O que é de todo escritório, na arte do Claude Design (ADR-0082): pixel art desenhada em código, vista de cima em 3/4, com uma paleta só e o contorno escuro em tudo. As folhas originais, a prévia e a página que as desenha ficam em `docs/design/escritorio-arte/`; esta pasta recebe cópias, feitas por `make arte-escritorio` (`campsverso_tools.office_art`), e o tileset montado a partir delas.

- `art.json`: o manifesto do gênero.
  - A cadeira de escritório é um assento (`seat`), de costas, em duas camadas: a base atrás e o encosto (`front`) por cima de quem senta.
  - A cadeira da copa é um assento de lado, virado para a mesinha pelo atributo `virada`.
  - A mesa do dev rola o código na tela enquanto alguém faz `work` ao lado dela (`in_use`); a máquina de café serve no `coffee`, o micro-ondas do balcão liga no `microwave`, a geladeira abre no `fridge` e a porta do banheiro abre no `restroom`.
  - A TV passa o jogo e o bebedouro borbulha sempre (`loop`).
  - A divisória dos cubículos é desenhada sobre cada tile `partition` do mapa lógico (`tile_props`), com o quadro pela máscara dos vizinhos, e cobre o pé de quem passa atrás dela.
  - O quadro dos pedidos, o micro-ondas, a porta da sala e as portas do banheiro usam a folha vazia (`vazio.png`): o mapa visual, o balcão e o bloco do banheiro já os desenham.
- `terreno.png` e `terreno.tsj`: os tiles do mapa visual, cada um com um nome: o carpete em quatro variações e a faixa de sombra junto ao rodapé, o corredor xadrez, a parede do fundo em duas linhas, as paredes do lado e os cantos, a parede de baixo e a porta, o tapete 3 x 3 e, em duas metades (`-t` e `-b`), o quadro dos pedidos em módulos, a janela com a cidade e o relógio.
- As folhas dos móveis, uma por peça, com o pé na borda de baixo do quadro: a mesa, as cadeiras, a divisória, o arquivo, a planta, a lixeira, a geladeira, o balcão da copa, a máquina de café, o bebedouro, a mesinha, o sofá, o móvel da TV, os pufes e o bloco do banheiro.
- Os nomes que a tela mostra ficam em `../locale/pt-BR.json` (ADR-0075).

O mapa visual de cada escritório fica na pasta de arte do cenário e é gerado por `make mapa-visual`.

## Licença

Desenho próprio do Campsverso, sob a mesma licença do código (MIT). `CREDITS.csv` dá os créditos arquivo por arquivo.
