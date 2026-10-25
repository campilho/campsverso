# Arte do gênero farm

O que serve a qualquer fazenda (ADR-0053): terreno, objetos e culturas, em pixel art LPC de 32 px.

- `art.json`: o manifesto que a tela lê para saber como desenhar cada tipo de tile, cada `kind` e cada estágio das culturas.
- `terrain.png` e `terrain.tsj`: os tiles do mapa visual, cada um com um nome (`grass-0`, `soil-tl`…). As margens da água além da esquerda (`water-t`, `water-r`, `water-b` e os cantos) foram derivadas da margem esquerda do pacote, por espelho e rotação (ADR-0070).
- `objects.png`: poço, baú, mesa, quiosque, caixa de vendas, cama e o fogão da Fazenda Boa Vista (desenho próprio no estilo LPC), em células de 64×96 ancoradas embaixo.
- `crops.png`: batata, rabanete, abóbora, cenoura, morango, tomate e alho, uma coluna por cultura e uma linha por estágio (os cinco estágios do pacote [LPC] Crops; a fazenda usa o 1º como broto, o 3º como crescendo, o 4º como madura, o 3º tingido como murcha e o 5º da batata como canteiro semeado).

## Licença

Só entram aqui os recortes que o jogo usa. A arte desta pasta é distribuída sob **CC-BY-SA 3.0** ou **GPL 3.0**, como as originais, e exige crédito a cada autor. O código do Campsverso continua MIT.

- Os créditos, arquivo por arquivo, estão em `CREDITS.csv`, e a tela os mostra no link "créditos".
- Os textos de atribuição originais de cada pacote estão em `credits/`.
