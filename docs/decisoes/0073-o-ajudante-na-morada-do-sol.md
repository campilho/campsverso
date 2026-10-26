# ADR-0073 — O ajudante na Morada do Sol: a medida, e o ajudante como teste de julgamento

**Status:** aceita · **Data:** 2026-10-26 · **Marco:** M20
**Complementa:** ADR-0072 (decisões 5, 9 e 13, e a nota 13 do usuário); ADR-0069 (a economia); ADR-0070 (o script 3 e o oráculo)

## Contexto

O plano do M20 previa calibrar as diárias pelo oráculo, com a premissa de que um ajudante paga a partir de uns 20 canteiros. A nota 13 do usuário pedia o mesmo: com o ajudante, o resultado deve ser melhor do que sem ele.

A medida derrubou a premissa. Foram umas 250 corridas de um ano, em processo e de graça. O oráculo trabalha de 107 a 129 minutos dos 960 acordados, em qualquer configuração:

| Configuração (oráculo, um ano) | Trabalho por dia | Plantios no ano |
|---|---|---|
| A de hoje, mapas a e b | 107 a 115 min | 92 e 107 |
| A fazenda fixa em 28 canteiros | ~120 min | 103 e 121 |
| O mercado 4 vezes maior, 28 e 40 canteiros | 118 a 129 min | 107 a 123 |
| 1.000 moedas a mais no começo | ~110 min | 88 e 92, e perde ~900 moedas |

O ajudante só faz trabalho, e trabalho sobra.

O usuário escolheu então tentar ações mais longas. O tempo das ações da fazenda foi multiplicado por k, e o andar ficou mais lento. Os ajudantes foram contratados à força por 7 dias a partir do dia 8, com diária 1, para medir o ganho bruto nos três mapas:

| Regime | Oráculo sozinho (colheitas) | O que o ajudante soma |
|---|---|---|
| k=8, andar 5 | 70 a 75 | +1 a +3 colheitas |
| k=8 com a fazenda crescendo com o ajudante e o mercado 4 vezes maior | 70 a 73 | +3 a +4 colheitas, moedas iguais |
| k=12, andar 4 | 52 a 54 (o mapa b desaba até sozinho) | nada |

A causa tem duas partes:

- **O tamanho da fazenda** do script 3 e do oráculo vem do caixa na mão (16 canteiros, mais 1 a cada 60 moedas) e do plano de compra, não dos braços. O tempo que o ajudante libera vira espera.
- **Com ações longas,** o que toma o dia é cavar e plantar, que ficam com o Camps. Os canteiros voltam a ser grama, então ele cava uns 50 por ano. O "cuidar" só rega e colhe.

O ganho bruto do ajudante para o oráculo fica entre 1 e 3 moedas por dia. Qualquer diária acima disso dá prejuízo.

A medida também achou três defeitos de vários avatares, consertados aqui:

- dois avatares no mesmo canteiro durante uma ação: o segundo colhia o vazio e o kernel caía;
- o ajudante lembrava como regados os canteiros de outro dia, e esperava o dia inteiro;
- a colheita que o ajudante deixa no baú ficava rodando entre o baú e a mão do Camps.

## Decisão

1. **O tempo das ações da Morada do Sol fica como está.** As ações mais longas foram medidas e desfeitas: não deram valor ao ajudante e deixavam o jogo mais lento. O M19 continua comparável.
2. **O ajudante é um teste de julgamento.** Com a economia de hoje, contratar não paga, e as diárias das fichas ficam (de 20 a 70). Contratar por impulso dá prejuízo, como o plano macro previa. A rodada do M21 mede se o humano e os modelos contratam.
3. **O script 3 contrata pela conta:**
   - o ganho do ajudante: os canteiros que o caixa pede acima dos que ele cuida sozinho, até os da ficha, pelo que um canteiro rende;
   - contrata quando o ganho passa da diária com 20% de folga;
   - o contrato inteiro tem de caber no caixa sem tocar na reserva, no caixa da comida e na folga de investir;
   - só a partir do dia 8, depois da semana do caixa mais apertado;
   - a diária e quem está livre vêm do quadro, que passa a mostrar a diária (`diaria_<id>`).

   Com o tempo de hoje, o Camps cuida sozinho de todos os 28 canteiros do teto (`solo: 28`), e a conta nunca contrata. O oráculo é o mesmo código, e o script 2 nunca contrata.
4. **A contratação forçada** (`helpers.force` no arquivo do script 3, `script_config` no pipeline de testes) mede os contratos de 1, 3 e 7 dias. A tabela está abaixo.
5. **O kernel confere de novo, na conclusão, a ação que outro avatar pode ter desfeito.** O cartucho declara, por ação, o que é compartilhado (o protocolo `Rechecked` da `cartridge-api`). Na fazenda são estes: plantar, regar, colher, limpar, adubar, cavar, fincar, carregar a máquina, mover itens do baú e contratar. Se a ação não vale mais, sai `action.failed` com `precondition_lost`, e o avatar recebe um pedido de decisão `action_interrupted`.
   - Os dois já estavam no contrato.
   - O que muda com a hora fica de fora (comprar, vender na feira, dormir). Com um avatar só, essas ações sempre valem na conclusão, e as fazendas 1 e 2 não mudam.
6. **O script 3 com um ajudante contratado:**
   - busca no baú a colheita fresca que o ajudante deixou lá (a com mais de um dia de validade; a que vence amanhã é a que o script 2 guarda);
   - nos dias em que um ajudante trabalhou, não aprende nada sobre perdas com o canteiro que esvaziou: ele não sabe quem colheu.
7. **O ajudante lembra o dia em que viu cada canteiro.** Um canteiro visto em outro dia perdeu a rega daquele dia, e ele vai ver.

## Os contratos de 1, 3 e 7 dias, com as diárias de verdade

O oráculo nos três mapas, com o tempo de hoje, cada ficha contratada à força sempre que o caixa pagava, a partir do dia 8. Os números são a média da diferença em moedas no fim do ano contra o oráculo sozinho:

| Ficha (diária) | 1 dia | 3 dias | 7 dias |
|---|---|---|---|
| Dita (40) | −188 (de 4 a 8 contratos) | −242 (de 1 a 3) | não coube no caixa |
| Zé Graúdo (40) | −190 (de 4 a 8) | −234 (de 1 a 3) | não coube no caixa |
| Nina (30) | −87 (de 5 a 8) | −159 (de 1 a 3) | −135 (1) |
| Seu Bento (70) | −226 (de 3 a 7) | −135 (1) | não coube no caixa |
| Tião (20) | −97 (de 6 a 7) | −171 (de 2 a 4) | −80 (de 1 a 2) |

- **As colheitas** variam de −7 a +10 por ano, dentro do ruído do oráculo; o que se perde é a diária.
- **O contrato de 7 dias** (de 140 a 490 moedas) quase nunca cabe no caixa, que fica perto de 100 o ano todo.
- **O script 3 forçado** só pagou dois contratos de 1 dia, no mapa c, e nenhum outro.

## Notas do usuário (26/out)

- Primeiro, diante da medida, escolheu as ações mais longas, a recomendação de então.
- Depois da segunda medida, escolheu voltar ao tempo de hoje e fazer do ajudante um teste de julgamento.
- A nota 13 da ADR-0072 (com o ajudante, melhor do que sem) não se cumpre nesta Morada.

## Consequências

- **Uma economia em que o trabalho prende vai para o `futuro.md`,** com o script que cresce a fazenda pela renda e manda o ajudante cavar e plantar.
- **O quadro mostra a diária,** e o script 3 e o oráculo ganham a contratação, a busca no baú e a conta forçada, sem mudar nada quando não contratam: o M19 se repete número por número.
- **A rodada de verificação do passo 8** usa a contratação forçada nos mapas a e b.
