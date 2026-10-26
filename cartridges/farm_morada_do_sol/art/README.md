# Arte da Fazenda Morada do Sol

A camada de arte do cenário `farm_morada_do_sol` (ADR-0053, ADR-0067). O Camps, os objetos, as culturas e a cor da terra do canteiro cavado vêm das camadas `farm`, `farm_camps` e `farm_boavista`, que este cenário estende. As quatro culturas novas (milho, melancia, mandioca e couve) estão na folha `crops2.png` do gênero.

- `map-visual.tmj`: o mapa visual de 64 por 40 tiles, gerado por `make mapa-visual` a partir do mapa lógico (`sim/.../data/map.tmj`), com o tileset do gênero e uma camada de árvores por cima da mata.
- `trees.png`, `trees-outono.png` e `trees-inverno.png`: quatro árvores do [LPC] Trees Mega-Pack, de 3 x 4 tiles cada, em verde (primavera e verão), laranja (outono) e marrom (o inverno seco). A tela troca a folha quando a estação muda (`seasons` no `art.json`), e o chão ganha o tom da estação.
- `objects.png`: o espantalho, desenho próprio no estilo LPC.
- `items.png`: os ícones dos itens no inventário (`items` no `art.json`), desenho próprio no estilo LPC: a lanterna (ADR-0068), a geleia, o molho de tomate, a farinha, o adubo e os restos de planta (ADR-0069). A luz em volta do Camps à noite é desenhada pela tela, com o raio da hora.
- `economia.png`: o quadro de encomendas, a barraca da feira (cinza quando fechada), o tacho e a composteira, que mostram as horas que faltam; desenho próprio no estilo LPC (ADR-0069).
- `dita.png`, `nina.png`, `ze-graudo.png`, `seu-bento.png` e `tiao.png`: os cinco ajudantes (ADR-0072), montados com peças do gerador de personagens LPC, no mesmo leiaute do Camps: estocada, andar, parado e caído, em quadros de 64×64. As cores da pele, do cabelo, dos olhos e da roupa foram trocadas por rampas. A peça sem a animação parada (a blusa da Dita, a regata da Nina) usa o primeiro quadro do andar.
  - **Dita:** corpo e cabeça femininos, trança e lenço vermelho, blusa verde, saia e sapato.
  - **Nina:** rabo de cavalo alto, regata, legging e bota.
  - **Zé Graúdo:** corpo musculoso, cabelo raspado e barba, calça e bota. Nenhuma camisa do pacote serve no corpo musculoso, por isso ele trabalha sem camisa.
  - **Seu Bento:** cabeça idosa, calvo e grisalho, barba branca, camisa de manga longa, calça e bota.
  - **Tião:** corpo adolescente, cabelo desarrumado, camiseta, bermuda e sapato.

## Licença

A arte desta pasta é CC-BY-SA 3.0 (o espantalho, a lanterna e a arte da economia também GPL 3.0), como as originais, e exige crédito a cada autor: `CREDITS.csv`, arquivo por arquivo, `credits/lpc-trees.txt`, o texto de atribuição do pacote de árvores, e `credits/ajudantes-gerador-lpc.csv`, as camadas dos ajudantes com os autores e as licenças de cada uma (algumas são OGA-BY 3.0, CC-BY 3.0 ou CC0; a folha montada segue a mais restritiva, CC-BY-SA 3.0 ou GPL 3.0). O código do Campsverso continua MIT.
