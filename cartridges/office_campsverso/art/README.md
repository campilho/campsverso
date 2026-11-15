# Arte do escritório do Campsverso

A camada de arte do cenário `office_campsverso`, na arte do Claude Design (ADR-0082). Os tiles e os móveis vêm do gênero, em `cartridges/office/art`.

- `art.json`: o manifesto do cenário, com o mapa visual e os três personagens.
- `camps.png`, `gerente.png` e `vigia.png`: os personagens, copiados de `docs/design/escritorio-arte/folhas/` por `make arte-escritorio`. As três folhas têm o mesmo mapa, em quadros de 64 × 64 com o pé na borda de baixo: andar (linhas 0 a 3, 8 quadros por tile), parado (4 a 7), usar (8 a 11), sentado (12 a 15), digitando (16, só de costas), beber (17 a 20) e comer sentado (21 e 22). O que um personagem não tem fica transparente.
  - **O Camps:** anda, fica parado, senta e digita. Usar, beber e comer ainda não foram desenhados: nessas ações, ele fica parado.
  - **O gerente e o vigia:** andam e ficam parados. Não têm o sentado: numa cadeira, ficam de pé, olhando para a mesa.
- Quem está no banheiro some da tela: a ação `restroom` está em `hidden` de cada personagem (ADR-0080), e o bloco do banheiro mostra a porta aberta.
- `decor.json`: o que fica pendurado na parede do fundo: o quadro dos pedidos em quatro módulos, a janela com a cidade e o relógio, como na prévia.
- `map-visual.tmj`: o mapa visual, gerado a partir do mapa lógico e de `decor.json` por `make mapa-visual`. O kernel nunca o lê.

## Licença

Desenho próprio do Campsverso, sob a mesma licença do código (MIT). `CREDITS.csv` dá os créditos arquivo por arquivo.
