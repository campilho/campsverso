# Arte do gênero farm

O que serve a qualquer fazenda (ADR-0053): terreno, objetos e culturas, em pixel art LPC de 32 px.

- `art.json`: o manifesto que a tela lê para saber como desenhar cada tipo de tile, cada `kind` e cada estágio das culturas.
- `terrain.png` e `terrain.tsj`: os tiles do mapa visual, cada um com um nome (`grass-0`, `soil-tl`…).
- `objects.png`: poço, baú, mesa, quiosque, caixa de vendas e cama, em células de 64×96 ancoradas embaixo.
- `crops.png`: batata, rabanete e abóbora, uma coluna por cultura e uma linha por estágio.

## Licença

Só entram aqui os recortes que o jogo usa. A arte desta pasta é distribuída sob **CC-BY-SA 3.0** ou **GPL 3.0**, como as originais, e exige crédito a cada autor. O código do Campsverso continua MIT.

- Os créditos, arquivo por arquivo, estão em `CREDITS.csv`, e a tela os mostra no link "créditos".
- Os textos de atribuição originais de cada pacote estão em `credits/`.
