## A Fazenda Morada do Sol, para quem acabou de chegar

**O tempo e o ano.** Um tick é um minuto simulado. O dia agrícola vira às 06:00: é quando as plantas crescem, o comprador paga, o quiosque muda o estoque e o mercado se ajusta. As fases do dia: amanhecer às 06:00, meio-dia às 12:00, entardecer às 18:00, noite às 20:00, madrugada às 00:00.

**A previsão do tempo.** Às 18:00 sai o tempo de amanhã, e a foto o traz em `weather.tomorrow`; a previsão não erra. O tempo de um dia é sol (`sun`), chuva (`rain`), tempestade (`storm`) ou seca (`drought`). Chove em cerca de um dia em cinco. A chuva e a tempestade contam como rega para todos os canteiros do dia. Na manhã de uma tempestade, as plantas maduras que ainda estão no canteiro podem ser derrubadas e se perdem: quem vê a tempestade na previsão colhe na véspera. Na seca não chove, a planta que não for regada até o meio-dia não cresce naquele dia, e cada rega gasta 2 cargas do regador. A tempestade é mais comum no verão, e a seca no inverno.

Aqui o ano passa depressa: um ano inteiro cabe em 28 dias, 7 dias para cada estação, e cada dia avança uns 13 dias do calendário. O relógio da foto traz a data (`date`) e a estação (`season`): o ano começa na primavera, em 22 de setembro; o verão começa em 21 de dezembro, o outono em 20 de março e o inverno em 21 de junho.

**O mapa.** A fazenda é maior do que você enxerga: de dia você vê 12 tiles em volta de você, em qualquer direção, e o resto só andando. No entardecer você vê 7, e à noite e de madrugada, 5. Com uma lanterna (`lanterna`, 40 moedas no quiosque) no inventário, você vê pelo menos 10 a qualquer hora. As construções (a casa com a cama, a mesa, o fogão e o baú; a composteira ao lado da casa; o poço; a caixa de vendas; o quiosque e o quadro de encomendas; a barraca da feira na entrada da fazenda) você sempre sabe onde estão. O que você já viu e saiu da vista fica no seu caderno, em "Fora de vista", com o estado em que você viu por último; o que mudou longe de você, só voltando lá para saber.

A foto traz o terreno à vista em `map`: cada linha de `rows` é uma linha do mapa (y cresce para baixo), cada caractere é um tile, `legend` diz o que cada caractere é e se dá para pisar, e `origin` é a coordenada do canto superior esquerdo do recorte. Para agir sobre uma coisa é preciso estar a até 1 tile dela, em qualquer direção; senão a ação é recusada com `not_adjacent`. Use `move_near` com o id da coisa, ou `move_to` com coordenadas, e depois a ação. Árvores, rio, paredes e os próprios objetos não se pisam. Andar cansa pouco: cada 60 tiles percorridos gastam 1 de energia.

**Os canteiros.** A fazenda não tem canteiro nenhum no começo: é você que cava. `dig` cava um canteiro num tile de grama ao seu lado (um dos 8 ao redor, ou o seu), pelas coordenadas dele (precisa da pá no inventário, leva 15 minutos e gasta 2 de energia). Só se cava na grama, e não há limite de canteiros: os freios são a energia, as sementes e a rega. Cada canteiro ganha um número que nunca se repete (`plot-001`, `plot-002`...). Um canteiro que passa três manhãs vazio volta a ser grama e some. Com o arado no inventário, cavar leva 5 minutos e plantar leva 1 minuto e 0,5 de energia.

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

**O quiosque.** O quiosque (`kiosk`) abre das 08:00 às 18:00; `open` diz se está aberto. Ele não tem toda semente todo dia: `estoque_hoje` lista o que há hoje, e a semente de uma cultura parada na estação não é vendida. O preço de agora de cada semente do estoque aparece no quiosque (`preco_semente_milho`...): cada unidade que você compra da mesma semente sobe o preço dela, e de manhã ele volta à tabela. Adubo, espantalho, lanterna, o tacho (200 moedas), o regador grande (150) e o arado (300) estão sempre à venda, a preço fixo.

**O mercado.** A caixa de vendas mostra o preço de agora de cada colheita e de cada produto (`preco_milho`, `preco_geleia`...). O mercado segue a oferta e a procura: cada unidade que você vende derruba o preço daquele item, e ele não volta de manhã; sobe aos poucos nos dias seguintes. Uma colheita fora da sua estação boa vale mais, porque é rara: na estação fraca, um pouco mais; na parada, bem mais (só quem guardou tem o que vender). Todo preço oscila um pouco de um dia para o outro, e depois de uma tempestade ou de uma seca as colheitas valem mais por alguns dias. O que você põe na caixa vale o preço do momento em que pôs.

**As encomendas.** O quadro de encomendas (`order_board`), ao lado do quiosque, tem os pedidos dos clientes da cidade, mas só se leem de perto. Cada pedido (`order-012`...) é uma coisa dentro do quadro, com o cliente (`cliente`), o `item`, a `quantidade`, o `prazo` (o último dia para entregar) e o `pagamento` total, acima do que a caixa pagaria. Pedidos novos aparecem de manhã, e o que ninguém aceita some no prazo. `accept_order` aceita um pedido (até 2 ao mesmo tempo); `deliver_order`, ao lado do quadro e com os itens no inventário, entrega e recebe na hora. Um pedido aceito que passa do prazo sai do quadro sem pagamento. Os clientes lembram de quem cumpre o prazo.

**A feira.** A cada 7 dias (os dias 7, 14, 21 e 28 do ano: o último de cada estação) há feira na barraca (`fair_stall`) da entrada da fazenda, das 06:00 às 14:00; `open` diz se está aberta e `proxima_feira`, o dia da próxima. A barraca compra colheitas e produtos acima do preço da caixa e paga na hora: use `sell` com a barraca como alvo. Vender muito do mesmo item derruba o preço dela também, até a próxima feira.

**O tacho e a composteira.** O tacho (`tacho`, 200 moedas no quiosque, peso 6) se finca na grama com `place`, como o espantalho, e trabalha sozinho: `process` carrega o tacho com os ingredientes de uma receita, e enquanto ele faz você segue a vida; `fazendo` e `faltam_horas` dizem o que ele faz e quanto falta. O produto fica no tacho até você pegar (`withdraw`, com o tacho como alvo). Uma receita por vez em cada tacho:

| Produto | Ingredientes | Horas | Venda | Validade (dias) |
|---|---|---|---|---|
| geleia | 3 morangos | 12 | 330 | 30 |
| molho_de_tomate | 3 tomates | 8 | 280 | 30 |
| farinha | 4 mandiocas | 8 | 450 | 90 |

Os produtos não se comem: vendem-se na caixa, na feira e nas encomendas. A composteira (`composteira`), ao lado da casa, faz 1 adubo em 3 dias com 3 unidades de uma colheita, ou de restos de planta (`resto`), que a limpeza de um canteiro murcho deixa: use `compost`, e depois `withdraw` com a composteira como alvo.

**Os ajudantes.** No quadro de ajudantes (`helper_board`), ao lado do quadro de encomendas, dá para contratar ajuda por 1, 3 ou 7 dias, pagando agora a diária vezes os dias (`hire_helper`). O quadro mostra quem está livre. O ajudante chega na manhã seguinte pela entrada da fazenda às 06:00 e vai embora às 18:00, deixando no baú o que carrega; o Seu Bento trabalha das 08:00 às 16:00. Ele traz o próprio regador e a própria pá. Quando a fome dele chega a 60, ele come do baú; sem comida no baú, vai embora mais cedo, e o dia está perdido. Você manda nele ao lado dele, e a ordem vale até você dar outra: cuidar (o que ele faz ao chegar: regar o que precisa e colher o maduro, guardando no baú), regar, colher, plantar uma cultura com as sementes do baú, cavar canteiros em volta de você, vender um item do baú na caixa (o pagamento vem para você) ou parar. Dispensar é ao lado dele ou no quadro, e os dias pagos não voltam. As fichas:
- `dita`, a Dita, a plantadeira, 40 moedas por dia: planta e colhe duas vezes mais rápido, mas anda devagar (cada passo leva o dobro).
- `ze-graudo`, o Zé Graúdo, o carregador, 40 por dia: carrega o dobro e cava mais rápido, mas come o dobro.
- `nina`, a Nina, a batedora, 30 por dia: vê o dobro em volta e enxerga à noite, mas cansa rápido (gasta 50% mais energia) e não carrega ferramenta pesada.
- `seu-bento`, o Seu Bento, o veterano, 70 por dia: faz tudo 20% mais rápido e não desmaia, mas só trabalha das 8h às 16h.
- `tiao`, o Tião, o aprendiz, 20 por dia: a diária mais barata, mas faz tudo 50% mais devagar e perde uma semente em cada dez plantios.

Um ajudante só se paga com muitos canteiros produzindo: faça a conta da diária contra o que ele colhe a mais antes de contratar.

**O seu corpo.** `needs` traz a fome (0 saciado, 100 faminto) e a energia (0 a 100). A fome sobe cerca de 2 por hora acordado e 1 dormindo, uns 40 por dia; a partir de 80, cada ação gasta o dobro de energia; em 100 você perde 4 de energia por hora acordado até comer. Comer uma colheita crua tira a fome da tabela. No fogão (`stove`) da casa, `cook` faz um prato com ingredientes do seu inventário: sopa de batata (2 batatas, 10 minutos), ensopado (1 batata, 1 cenoura e 1 alho, 20 minutos) e purê de abóbora (1 abóbora, 15 minutos); quanto cada prato mata a fome, só comendo se descobre, e um prato dura 2 dias. A energia cai 1 por hora acordado, com cada ação e ao andar; em 0 você desmaia onde estiver. Quem ainda está acordado às 02:00 também desmaia. Depois de desmaiar, acorda às 06:00 com energia 50.

**Para não passar fome.** Coma quando a fome passar de 60, para ela nunca chegar aos 80. Separe os canteiros da comida dos canteiros de vender. Um canteiro de comida mata, por dia, a fome da cultura dividida pelos dias que ela leva: o rabanete na primavera (25 em 3 dias) mata uns 8 por dia, então uns 5 canteiros de rabanete pagam os 40 do dia, e 7 dão folga; na estação fraca da sua comida, que leva o dobro dos dias, são o dobro de canteiros. Os outros canteiros são os de vender. Guarde comida para dois dias e não a venda. Não gaste todo o dinheiro em cultura longa ou cara: guarde o da semente da próxima leva dos canteiros de comida, ou a fome chega antes da colheita. Com moedas sobrando, compare as comidas: a fome que cada uma mata, os dias que leva e o preço da semente; o que você descobrir dos pratos vale anotar.

**O sono.** Dorme-se a qualquer hora e em qualquer lugar. À noite, das 20:00 às 06:00, dorme-se até as 06:00; de dia é um cochilo, até a energia encher ou até as 06:00. Na cama (`bed`, ao lado dela) a energia recupera 12,5 por hora; no chão, só 5. Não dá para acordar antes da hora, nem para agir dormindo: uma ação durante o sono é recusada com `busy`. Dormir às 20:00 na cama é o jeito de chegar às 06:00 inteiro.

**Uma ação por vez.** Cada ação tem uma duração, e o mundo não espera: enquanto uma ação dura, outra é recusada com `busy`; quando termina, você recebe um novo pedido de decisão. Motivos de recusa que você pode ver: `not_adjacent` (longe do alvo), `busy` (ocupado ou dormindo), `missing_item` (não tem o item, ou a pá), `missing_ingredients` (faltam ingredientes), `insufficient_funds` (faltam moedas), `closed` (quiosque fechado), `out_of_stock` (a semente não está no estoque de hoje), `too_heavy` (não cabe no inventário ou no baú), `not_grass` (aqui não é grama), `occupied` (já há algo neste tile), `no_room` (canteiros demais), `not_ripe` (planta não madura), `not_withered` (planta não murcha), `plot_occupied` (canteiro ocupado), `already_fertilized` (canteiro já adubado), `no_plant` (canteiro sem planta), `can_empty` (regador vazio), `not_edible` (não se come), `not_tired` (cochilo com a energia cheia), `unreachable` e `not_passable` (não dá para chegar ou pisar), `already_there` (você já está ao lado disso), `machine_busy` (a máquina ainda está fazendo), `no_order` (não há esse pedido no quadro), `order_taken` (outro já aceitou), `too_many_orders` (já são 2 aceitos), `not_your_order` (o pedido não é seu), `order_expired` (o prazo passou), `invalid_params` (parâmetros errados).

**Nem tudo está escrito aqui.** O que a foto mostra é o que você sabe; o que ela não mostra, você descobre observando o que acontece.
