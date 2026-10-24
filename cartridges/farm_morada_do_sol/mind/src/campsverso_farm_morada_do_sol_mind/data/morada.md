## A Fazenda Morada do Sol, para quem acabou de chegar

**O tempo e o ano.** Um tick é um minuto simulado. O dia agrícola vira às 06:00: é quando as plantas crescem, o comprador paga, o quiosque muda o estoque e os preços voltam à tabela. As fases do dia: amanhecer às 06:00, meio-dia às 12:00, entardecer às 18:00, noite às 20:00, madrugada às 00:00. Às 05:00 o clima do dia é sorteado: chove em cerca de um dia em cinco, e a chuva conta como rega para todos os canteiros daquele dia.

Aqui o ano passa depressa: um ano inteiro cabe em 28 dias, 7 dias para cada estação, e cada dia avança uns 13 dias do calendário. O relógio da foto traz a data (`date`) e a estação (`season`): o ano começa na primavera, em 22 de setembro; o verão começa em 21 de dezembro, o outono em 20 de março e o inverno em 21 de junho.

**O mapa.** A fazenda é maior do que você enxerga: de dia você vê 12 tiles em volta de você, em qualquer direção, e o resto só andando. No entardecer você vê 7, e à noite e de madrugada, 5. Com uma lanterna (`lanterna`, 40 moedas no quiosque) no inventário, você vê pelo menos 10 a qualquer hora. As construções (a casa com a cama, a mesa, o fogão e o baú; o poço; a caixa de vendas; o quiosque) você sempre sabe onde estão. O que você já viu e saiu da vista fica no seu caderno, em "Fora de vista", com o estado em que você viu por último; o que mudou longe de você, só voltando lá para saber.

A foto traz o terreno à vista em `map`: cada linha de `rows` é uma linha do mapa (y cresce para baixo), cada caractere é um tile, `legend` diz o que cada caractere é e se dá para pisar, e `origin` é a coordenada do canto superior esquerdo do recorte. Para agir sobre uma coisa é preciso estar a até 1 tile dela, em qualquer direção; senão a ação é recusada com `not_adjacent`. Use `move_near` com o id da coisa, ou `move_to` com coordenadas, e depois a ação. Árvores, rio, paredes e os próprios objetos não se pisam. Andar cansa: cada 20 tiles percorridos gastam 1 de energia.

**Os canteiros.** A fazenda não tem canteiro nenhum no começo: é você que cava. `dig` cava um canteiro num tile de grama ao seu lado (um dos 8 ao redor, ou o seu), pelas coordenadas dele (precisa da pá no inventário, leva 15 minutos e gasta 8 de energia). Só se cava na grama, e não há limite de canteiros: os freios são a energia, as sementes e a rega. Cada canteiro ganha um número que nunca se repete (`plot-001`, `plot-002`...). Um canteiro que passa três manhãs vazio volta a ser grama e some. Com o arado no inventário, cavar leva 5 minutos e plantar leva 1 minuto e 1 de energia.

**O que você tem.** Seu inventário aparece em `containers` com o seu id, e tem uma capacidade: `capacity` (20) e `weight` (quanto já carrega) aparecem nos seus atributos. Cada item tem peso: sementes 0,1; colheitas 0,5 (abóbora 2, melancia 3, mandioca 1); adubo 1; o espantalho 4; a lanterna 1; e as ferramentas, que são entidades com `container_id` igual ao seu id: a pá pesa 3, o regador (10 cargas) 4, o regador grande (25 cargas) 9 e o arado 12. O que não cabe é recusado com `too_heavy`. O baú (`chest`) guarda o que você não quer carregar, itens e ferramentas (uma ferramenta vai e volta pelo id dela, ex.: `plow-1`). A caixa de vendas (`sell_box`) é esvaziada pelo comprador às 22:00, que paga às 06:00 em moedas no seu inventário. O regador só enche no poço (`well`); se tiver dois regadores, enche os dois.

**As plantas.** Cada canteiro (`plot`) tem no máximo uma planta, com os estágios `semente`, `broto`, `crescendo` e `madura`; abandonada, fica `murcha`, e um canteiro murcho precisa ser limpo antes de plantar de novo. Toda manhã, às 06:00, uma planta que foi regada no dia anterior (pelo regador ou pela chuva) avança no crescimento; `watered_today` no canteiro diz se já está regado hoje. Cada cultura reage à seca do seu jeito. Uma planta madura que fica três dias sem ser colhida murcha. Cada colheita rende 1 unidade. Os dias até amadurecer, na estação boa, são aproximados:

| Cultura | Semente (compra) | Dias, mais ou menos | Venda | Mata a fome | Dura (dias) |
|---|---|---|---|---|---|
| rabanete | 10 | 3 | 25 | 25 | 4 |
| batata | 20 | 5 | 50 | 35 | 10 |
| abobora | 40 | 8 | 104 | 50 | 30 |
| cenoura | 15 | 4 | 20 | 15 | 6 |
| morango | 60 | 6 | 90 | 20 | 2 |
| tomate | 30 | 4 | 70 | 30 | 3 |
| alho | 12 | 7 | 40 | 10 | 60 |
| milho | 20 | 6 | 45 | 25 | 8 |
| melancia | 35 | 8 | 120 | 40 | 12 |
| mandioca | 25 | 10 | 80 | 45 | 20 |
| couve | 12 | 4 | 30 | 12 | 5 |

**O calendário de plantio.** Cada cultura tem a sua estação. Na estação **boa**, cresce no ritmo da tabela; na **fraca**, leva cerca de duas vezes mais tempo; na **parada**, não cresce, mas também não morre (ela espera a estação voltar, ou a seca a mata como em qualquer estação).

| Cultura | Primavera | Verão | Outono | Inverno |
|---|---|---|---|---|
| milho | boa | boa | fraca | parada |
| melancia | boa | boa | parada | parada |
| mandioca | boa | boa | fraca | fraca |
| abobora | boa | boa | fraca | parada |
| tomate | boa | fraca | boa | parada |
| batata | fraca | parada | boa | boa |
| cenoura | fraca | parada | boa | boa |
| rabanete | boa | fraca | boa | boa |
| alho | parada | parada | boa | boa |
| morango | fraca | parada | boa | boa |
| couve | fraca | parada | boa | boa |

A validade de cada pilha aparece em `expires_in_days` no seu inventário e no baú: no dia em que vence, o que estava no inventário estraga de manhã. O adubo (`adubo`, 15 moedas no quiosque) se aplica com `fertilize` num canteiro vazio, antes de plantar, e faz a planta seguinte crescer melhor; o canteiro mostra `adubado`.

**O espantalho.** O espantalho (`espantalho`, 60 moedas no quiosque) protege a lavoura. Ele se finca com `place` num tile de grama ao seu lado, e fica lá.

**O quiosque e o mercado.** O quiosque (`kiosk`) abre das 08:00 às 18:00; `open` diz se está aberto. Ele não tem toda semente todo dia: `estoque_hoje` lista o que há hoje, e a semente de uma cultura parada na estação não é vendida. Adubo, espantalho, lanterna, o regador grande (150 moedas) e o arado (300 moedas) estão sempre à venda. A caixa de vendas mostra o preço de hoje de cada colheita (`preco_rabanete`, `preco_milho`...): vender muitas unidades da mesma colheita no mesmo dia derruba o preço dela, que volta à tabela no dia seguinte. O que você põe na caixa vale o preço do momento em que pôs.

**O seu corpo.** `needs` traz a fome (0 saciado, 100 faminto) e a energia (0 a 100). A fome sobe cerca de 3 por hora acordado e 1 dormindo; a partir de 80, cada ação gasta o dobro de energia; em 100 você perde 4 de energia por hora acordado até comer. Comer uma colheita crua tira a fome da tabela. No fogão (`stove`) da casa, `cook` faz um prato com ingredientes do seu inventário: sopa de batata (2 batatas, 10 minutos), ensopado (1 batata, 1 cenoura e 1 alho, 20 minutos) e purê de abóbora (1 abóbora, 15 minutos); quanto cada prato mata a fome, só comendo se descobre, e um prato dura 2 dias. A energia cai 1 por hora acordado, com cada ação e ao andar; em 0 você desmaia onde estiver. Quem ainda está acordado às 02:00 também desmaia. Depois de desmaiar, acorda às 06:00 com energia 50.

**O sono.** Dorme-se a qualquer hora e em qualquer lugar. À noite, das 20:00 às 06:00, dorme-se até as 06:00; de dia é um cochilo, até a energia encher ou até as 06:00. Na cama (`bed`, ao lado dela) a energia recupera 12,5 por hora; no chão, só 5. Não dá para acordar antes da hora, nem para agir dormindo: uma ação durante o sono é recusada com `busy`. Dormir às 20:00 na cama é o jeito de chegar às 06:00 inteiro.

**Uma ação por vez.** Cada ação tem uma duração, e o mundo não espera: enquanto uma ação dura, outra é recusada com `busy`; quando termina, você recebe um novo pedido de decisão. Motivos de recusa que você pode ver: `not_adjacent` (longe do alvo), `busy` (ocupado ou dormindo), `missing_item` (não tem o item, ou a pá), `missing_ingredients` (faltam ingredientes), `insufficient_funds` (faltam moedas), `closed` (quiosque fechado), `out_of_stock` (a semente não está no estoque de hoje), `too_heavy` (não cabe no inventário ou no baú), `not_grass` (aqui não é grama), `occupied` (já há algo neste tile), `no_room` (canteiros demais), `not_ripe` (planta não madura), `not_withered` (planta não murcha), `plot_occupied` (canteiro ocupado), `already_fertilized` (canteiro já adubado), `no_plant` (canteiro sem planta), `can_empty` (regador vazio), `not_edible` (não se come), `not_tired` (cochilo com a energia cheia), `unreachable` e `not_passable` (não dá para chegar ou pisar), `already_there` (você já está ao lado disso), `invalid_params` (parâmetros errados).

**Nem tudo está escrito aqui.** O que a foto mostra é o que você sabe; o que ela não mostra, você descobre observando o que acontece.
