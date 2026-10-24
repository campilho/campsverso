# Arte da Fazenda Morada do Sol

A camada de arte do cenário `farm_morada_do_sol` (ADR-0053, ADR-0067). O Camps, os objetos, as culturas e a cor da terra do canteiro cavado vêm das camadas `farm`, `farm_camps` e `farm_boavista`, que este cenário estende. As quatro culturas novas (milho, melancia, mandioca e couve) estão na folha `crops2.png` do gênero.

- `map-visual.tmj`: o mapa visual de 64 por 40 tiles, gerado por `make mapa-visual` a partir do mapa lógico (`sim/.../data/map.tmj`), com o tileset do gênero e uma camada de árvores por cima da mata.
- `trees.png`, `trees-outono.png` e `trees-inverno.png`: quatro árvores do [LPC] Trees Mega-Pack, de 3 x 4 tiles cada, em verde (primavera e verão), laranja (outono) e marrom (o inverno seco). A tela troca a folha quando a estação muda (`seasons` no `art.json`), e o chão ganha o tom da estação.
- `objects.png`: o espantalho, desenho próprio no estilo LPC.

## Licença

A arte desta pasta é CC-BY-SA 3.0 (o espantalho também GPL 3.0), como as originais, e exige crédito a cada autor: `CREDITS.csv`, arquivo por arquivo, e `credits/lpc-trees.txt`, o texto de atribuição do pacote de árvores. O código do Campsverso continua MIT.
