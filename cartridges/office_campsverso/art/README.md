# Arte do escritório do Campsverso

A camada de arte do cenário `office_campsverso` (ADR-0078). Os tiles e os móveis vêm do gênero, em `cartridges/office/art`.

- `art.json`: o manifesto do cenário, com o mapa visual e os três personagens.
- `camps.png`, `gerente.png` e `vigia.png`: os personagens, montados com peças do gerador de personagens LPC. O leiaute é o do Camps da fazenda, com as linhas do sentar no fim: estocada (linhas 0 a 3), andar (4 a 7), parado (8 a 11), caído (12) e sentado (13 a 16), em quadros de 64 × 64. As cores foram trocadas por rampas.
  - **O Camps:** o mesmo da fazenda, sem o chapéu e o regador, de óculos e de sapato. A camisa vermelha, o jeans e o cabelo castanho saíram da folha da fazenda, pixel a pixel.
  - **O gerente:** cabeça idosa, cabelo repartido grisalho e bigode, camisa social, paletó grafite, gravata vermelha, calça social e sapato preto. O paletó e a camisa social não têm as poses parado e sentado: o parado usa o primeiro quadro do andar, e o gerente nunca senta.
  - **O vigia:** cabelo raspado e bigode, a camisa da farda azul-marinho, calça e coturno pretos. O gerador não tem um boné que sirva, por isso ele trabalha sem chapéu.
- Quem está no banheiro some da tela: a ação `restroom` está em `hidden` de cada personagem (ADR-0080).
- `decor.json`: a decoração da parede, peça por peça: as janelas, o relógio, o quadro de avisos, o bebedouro e a estante.
- `map-visual.tmj`: o mapa visual, gerado a partir do mapa lógico e de `decor.json` por `make mapa-visual`. O kernel nunca o lê.

## Licença

A arte desta pasta é distribuída sob **CC-BY-SA 3.0** ou **GPL 3.0** e exige crédito a cada autor. O código do Campsverso continua MIT.

- `CREDITS.csv` dá os créditos de cada camada de cada personagem.
- `credits/escritorio-gerador-lpc.csv` lista as camadas com os autores e as licenças de cada uma. Algumas são OGA-BY 3.0, CC-BY 3.0 ou CC0; a folha montada segue a mais restritiva, CC-BY-SA 3.0 ou GPL 3.0.
