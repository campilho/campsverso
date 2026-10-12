# Arte do cenário farm_camps

O que é só da Fazenda do Camps (ADR-0053). Cobre o gênero `farm`, camada por camada.

- `art.json`: o manifesto do cenário, com o mapa visual e as animações do Camps.
- `camps.png`: o Camps, montado no gerador de personagens LPC. Só as animações usadas: estocada (agir e regar), andar, parado e deitado (dormir e desmaiar), em quadros de 64×64.
- `map-visual.tmj`: o mapa visual, gerado a partir do mapa lógico por `make mapa-visual`. O kernel nunca o lê.

## Licença

A arte desta pasta é distribuída sob **CC-BY-SA 3.0** ou **GPL 3.0** e exige crédito a cada autor. O código do Campsverso continua MIT.

- Os créditos de cada camada do personagem estão em `CREDITS.csv`.
- O arquivo exportado pelo gerador está em `credits/camps-gerador-lpc.csv`.
