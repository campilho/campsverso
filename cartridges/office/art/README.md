# Arte do gênero office

O que é de todo escritório (ADR-0078), recortado de três pacotes LPC e completado com desenho próprio no estilo deles. As cores do desenho próprio são tiradas dos próprios pacotes.

- `art.json`: o manifesto do gênero. A cadeira é um assento (`seat`): quem para nela senta, olhando para a mesa.
- `terrain.png` e `terrain.tsj`: os tiles do mapa visual, cada um com um nome:
  - o chão de tábuas e o piso xadrez do corredor, do pacote de interiores;
  - a parede do fundo em duas linhas (`north-t`, `north-b`): a moldura dourada, o reboco claro com listras finas, o rodameio, o lambri em painéis e o rodapé, desenho próprio;
  - a moldura das paredes do lado vista de cima, a parede de baixo com a face curta que dá para o corredor e a porta, desenho próprio;
  - a decoração da parede, em peças de dois tiles de altura (`-t` e `-b`): a janela e o quadro de avisos pequeno (desenho próprio), o relógio (interiores), o bebedouro (The Office) e a estante (Wooden Furniture).
- `objects.png`: os móveis, em quadros de 96 × 64, desenhados com o pé no tile da coisa:
  - 0, a mesa do Camps, vista do lado de quem senta, com o notebook ligado, o telefone vermelho e a xícara;
  - 1, a bancada, uma mesa dobrável cinza com a cafeteira e um notebook claro;
  - 2, o quadro dos pedidos, de cortiça, com as fichas nas quatro colunas, de pé na frente da parede (desenho próprio);
  - 3, a cadeira, de costas.
- Os nomes que a tela mostra ficam em `../locale/pt-BR.json` (ADR-0075).

O mapa visual de cada escritório fica na pasta de arte do cenário e é gerado por `make mapa-visual`.

## Licença

A arte desta pasta é distribuída sob **CC-BY-SA 3.0** ou **GPL 3.0**, como as originais, e exige crédito a cada autor. O código do Campsverso continua MIT.

- `CREDITS.csv` dá os créditos arquivo por arquivo.
- Os textos de atribuição dos três pacotes estão em `credits/`:
  - `lpc-the-office.txt`: [LPC Revised: The Office](https://opengameart.org/content/lpc-revised-the-office), de Eliza Wyatt e Lanea Zimmerman, OGA-BY 3.0;
  - `lpc-wooden-furniture.txt`: [LPC Wooden Furniture](https://opengameart.org/content/lpc-wooden-furniture);
  - `lpc-house-interior.txt`: [[LPC] House interior and decorations](https://opengameart.org/content/lpc-house-interior-and-decorations), de Tuomo Untinen e outros.
