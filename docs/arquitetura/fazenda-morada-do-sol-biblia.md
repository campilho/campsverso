# Bíblia da Fazenda Morada do Sol (a fazenda 3, M16)

**Status:** escrita em 23/out/2026, ao fim do M16, a partir do plano do marco e da ADR-0067; a noite e a lanterna entraram no M17 (ADR-0068), a economia e o clima no M18 (ADR-0069, §11 a §14), e as variantes do mapa, o fazendeiro-script 3, o oráculo e a fome em 2 por hora no M19 (ADR-0070, §3, §9, §10, §15 e §16), e a energia no M21 (ADR-0074, §18). É a fonte dos números e das regras do cenário `farm_morada_do_sol` e dos mundos `farm-morada-do-sol-01`, `-02` e `-03`. O cenário estende a Fazenda Boa Vista: o que esta bíblia não diz vale como na bíblia 2 (`fazenda-boa-vista-biblia.md`) e, abaixo dela, na bíblia da v0.1. Isso inclui as ferramentas, o baú, o mercado que satura, o fogão, a validade, o sono e o desmaio.

## 1. Conceito

A Boa Vista mostrou que os modelos planejam bem, mas que ninguém explora: os canteiros nasciam perto da casa, e a regra do rio nunca agia. A Morada do Sol é um mundo feito para pedir exploração e para premiar quem aprende:

- um mapa maior que a tela, em que se enxerga só um raio;
- canteiros sem teto que voltam a ser grama, o que torna a escolha do lugar reversível;
- um ano com as quatro estações e um calendário de plantio;
- regras ocultas que valem para o que todo mundo faz: plantar, colher, repetir a cultura, plantar longe.

O avatar continua o Camps, com o mesmo cartão de identidade.

## 2. O ano e as estações

| | |
|---|---|
| Duração do ano | 28 dias simulados, 7 por estação; a corrida da arena passa a ser um ano |
| Início | o dia 1 é 22 de setembro, a primavera do hemisfério sul (o `start` do mundo é 22/09/2026, 06:00) |
| As estações | primavera em 22/09, verão em 21/12, outono em 20/03, inverno em 21/06 |
| A data | cada dia simulado avança 365/28 dias do calendário (uns 13); a data e a estação aparecem no relógio da percepção (`date`, `season`) e no painel da tela |
| A troca | na virada do dia em que a estação muda, o kernel publica `world.clock.season_changed.v1` |

A data do ano acelerado anda à parte do `simtime` dos eventos, que continua minuto a minuto. O kernel calcula as duas a partir do `YearDef` que o cartucho declara (ADR-0067).

## 3. O mapa

São 64 × 40 tiles, quatro vezes a área da Boa Vista, com os nove tipos de terreno do tileset do gênero.

| Região | Onde | O que tem |
|---|---|---|
| A casa | a oeste, em (4..8, 14..18) | cama, mesa, fogão e, do lado de fora, o baú; a porta em (6, 18) |
| O centro | em volta da casa | o poço em (14, 20), a caixa de vendas em (9, 20), a composteira em (2, 17) |
| A estrada | a linha 22, de x = 6 até o rio | caminho de terra, com ramais para o norte (x = 26) e para o sul (x = 32..33) |
| O quiosque | ao sul, em (34, 36), junto da entrada da fazenda | as sementes, o adubo, o espantalho, a lanterna, o tacho e as ferramentas; o quadro de encomendas em (36, 36) e a barraca da feira em (31, 37) |
| O rio | a leste, colunas 60..63, de ponta a ponta | não se pisa |
| A várzea | a grama entre a estrada e o rio, a leste | grama larga, longe da casa |
| O morro | ao norte, linhas 1..7 | uma faixa de mata com uma clareira e uma lagoa pequena em (24..29, 3..5) |
| A clareira | ao sul, dentro de um bosque, em (42..53, 30..35) | grama cercada de mata, com uma trilha de acesso |
| Bosques | soltos no campo | manchas de mata que bloqueiam o caminho reto |

O mapa lógico é gerado por script a partir desta tabela e editado no Tiled daqui em diante. O mapa visual vem do `make mapa-visual`, com árvores LPC por cima da mata, que trocam de cor com a estação (verde, laranja no outono e marrom no inverno seco).

**As variantes (M19, ADR-0070).** O mapa acima é a variante `a`. As outras são receitas sobre ele (`data/maps/receitas.yaml`): a casa, o centro, a estrada e a entrada ficam no lugar, e mudam a água e as matas. `make mapa-variantes` aplica cada receita, grava o mapa e confere o que ela promete; o arquivo do mundo escolhe a variante com `map:`, o id do mapa fica no snapshot, e a tela escolhe o mapa visual pelo id.

| Variante | Mundo | A água | A terra boa (até 4 tiles da água) |
|---|---|---|---|
| **a, o rio** | `farm-morada-do-sol-01` | o rio na borda leste e a lagoa do morro | longe da casa, no caminho dos corvos |
| **b, o córrego** | `farm-morada-do-sol-02` | um córrego de norte a sul na coluna 20, com a ponte da estrada e uma lagoinha no fim; sem rio | de 9 a 22 tiles da porta, 60% ou mais a salvo dos corvos, a 3 tiles do poço ou mais |
| **c, as lagoas** | `farm-morada-do-sol-03` | três lagoas pequenas, no morro, na clareira e a leste; sem rio | só a mais de 22 tiles da porta: toda no caminho dos corvos |
| **d** | (M21) | reservada, com outra receita | nunca entra nos testes do script 3 |

Os três mundos têm a mesma seed (20261022): a diferença entre eles é só o mapa. A água precisa de dois tiles de largura para a margem se desenhar, e as lagoas são retângulos.

## 4. A percepção

| | |
|---|---|
| Raio | 12 tiles (distância de Chebyshev) em volta do avatar: o script e o LLM recebem o recorte |
| Marcos | cama, porta, baú, fogão, poço, caixa de vendas, quiosque, quadro de encomendas, barraca da feira e composteira se veem além do raio: quem mora na fazenda sabe onde ficam (`perception_config.landmarks`, decisão 15). Os pedidos dentro do quadro, não: só de perto |
| A noite | 12 tiles de dia, 7 no entardecer, 5 à noite e de madrugada; a lanterna no inventário garante 10 (ADR-0068) |
| Fora da vista | o delta separa `out_of_view` (saiu do raio e continua no mundo) de `gone` (deixou de existir à vista) |
| A lembrança | a mente guarda o último estado visto de cada coisa (os lugares, na `MemoryPort`) e lista no bloco de abertura o que está fora de vista; o fazendeiro-script guarda a sua própria lembrança, com o terreno |

## 5. Os canteiros

| | |
|---|---|
| Onde | em qualquer grama; nunca na estrada, no rio, na mata, na casa ou num tile ocupado |
| Teto | 400, técnico, só para o desempenho; no jogo, os freios são as sementes, o caixa e a rega de todo dia; a energia (2 por canteiro cavado, §18) segura um dia em uns 20 canteiros novos |
| O id | `plot-001`, `plot-002`…, por um contador do kernel que nunca repete (`next_seq`) |
| A volta à grama | o canteiro cavado que passa 3 manhãs sem planta volta a ser grama: o kernel remove a entidade (`world.entity.despawned.v1`, motivo `reverted_to_grass`). A planta, mesmo murcha, segura o canteiro; o alvo de uma ação em andamento espera a manhã seguinte |

## 6. As culturas e o calendário

As sete da Boa Vista, com os mesmos números, mais quatro novas, do pacote LPC de culturas:

| Cultura | Semente | Pontos para amadurecer | Venda | Fome | Validade (dias) | Peso |
|---|---|---|---|---|---|---|
| milho | 20 | 6 | 45 | 25 | 8 | 0,5 |
| melancia | 35 | 8 | 120 | 40 | 12 | 3 |
| mandioca | 25 | 10 | 80 | 45 | 20 | 1 |
| couve | 12 | 4 | 30 | 12 | 5 | 0,5 |

A afinidade com a estação multiplica o ponto de crescimento do dia regado: **boa** 1, **fraca** 0,5, **parada** 0. Fora da estação a planta não morre (a seca continua matando como sempre). O calendário é visível, no manual:

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

O quiosque não vende a semente de uma cultura parada na estação. As novas entram no ciclo dele: milho e couve todo dia, mandioca nos dias 1, 3 e 5, melancia nos dias 2 e 5. O adubo e o espantalho estão sempre à venda.

## 7. O espantalho

| | |
|---|---|
| Preço | 60 moedas no quiosque; pesa 4 |
| Ação | `place` (fincar): num tile de grama ao lado do avatar, 10 minutos e 3 de energia; vira uma entidade `scarecrow` que bloqueia o tile |
| No manual | "protege a lavoura", sem dizer de quê nem até onde |

## 8. As regras ocultas

São verdades do mundo, fixas (ADR-0066): o que muda de uma corrida para outra é o mapa, numa variante a desenhar no M19.

| Regra | O que faz | Números (ocultos) | O que se vê |
|---|---|---|---|
| R-001, a várzea | água perto faz crescer mais rápido; é a mesma verdade das fazendas 1 e 2 | a até 4 tiles de qualquer tile de água (o rio, a lagoa), o ponto do dia vale 1,5 | a planta amadurece antes |
| R-002, os corvos | toda manhã, depois do crescimento, cada planta madura longe da casa e sem espantalho por perto pode amanhecer comida; o canteiro fica vazio | longe: a mais de 18 tiles da porta; por perto: a até 6 tiles de um espantalho; a chance é de 1 em 2, pelo RNG nomeado `crows` | o canteiro vazio e o evento `farm.crop.eaten.v1` com `by: corvo` |
| R-003, a fadiga do solo | plantar a mesma cultura que acabou de sair do canteiro faz a planta crescer mais devagar; trocar de cultura recupera | o canteiro lembra a última cultura colhida ou limpa (`last_crop`); repetir multiplica o ponto por 0,6 | a planta leva mais dias |
| R-004, a reputação | quem entrega no prazo vê mais pedidos no quadro e prêmios maiores; quem deixa vencer um pedido aceito, o contrário (ADR-0069) | começa em 0,5; sobe 0,1 por entrega, desce 0,2 por pedido aceito que vence; o peso vai de 0,5 a 1,5 na chance de cada vaga e no prêmio | o quadro mais cheio ou mais vazio, e o pagamento dos pedidos novos |
| As da Boa Vista | o tomate murcha com um dia seco; o alho dispensa rega; o baú conserva; o ensopado segura a fome; o adubo vale para o próximo plantio | os da bíblia 2, §10 | os efeitos de sempre |

Os quatro critérios do plano macro: as três novas são **frequentes** (agem sobre plantar, colher e plantar longe), **descobríveis por experimento** (dois canteiros, um perto e outro longe da água, ou um com e outro sem repetição), **valiosas** (a várzea rende uma vez e meia, os corvos levam metade das maduras longe da casa, a fadiga atrasa dois dias um rabanete) e **sistêmicas** (água faz crescer, bicho come o que está sem guarda, monocultura cansa a terra).

## 9. O fazendeiro-script 2 na Morada do Sol

O mesmo script da Boa Vista, com o que só age onde há estação e recorte:

- **A lembrança:** guarda o último estado visto de cada coisa e o terreno; esquece o que estava à vista e sumiu; esquece tudo numa sessão nova.
- **A exploração:** sem nada para fazer, das 08:00 às 17:00, com energia de 45 ou mais e fome abaixo de 55, anda até a fronteira do que já viu. No soak do ano, viu o mapa inteiro entre os dias 2 e 3.
- **O calendário:** não planta nem compra a cultura parada na estação, conta a fraca como duas vezes mais lenta e escolhe a base de comida da estação (rabanete, couve ou milho, a primeira que cresce no ritmo cheio).

Ele não sabe nenhuma regra oculta, e sofre com elas: repete o rabanete nos mesmos canteiros, e a fadiga do solo leva o rabanete de 3 para uns 5,5 dias. Continua a linha de base cega, ao lado do fazendeiro-script 3 e do oráculo (§16).

**Na economia (M18), só no essencial:** não repete uma proposta que acabou de ser recusada; conta o preço da semente que sobe com a compra; na seca, rega com as 2 cargas; perto do quadro, aceita o pedido que já pode cumprir com o que carrega e entrega na hora. A feira e o tacho ficam para o script 3. No soak de um ano com a economia e o clima, ele vive sem desmaio nem recusa: 48 plantios, 38 colheitas, 17 moedas ao fim e 1 encomenda entregue (de 20 que apareceram).

## 10. As métricas

As da Boa Vista (bíblia 2, §13), mais duas:

| Métrica | Por quê |
|---|---|
| Plantas comidas, por cultura | quanto a R-002 custou |
| Canteiros que voltaram a ser grama | quanto se cavou à toa |
| Moedas recebidas por canal | quanto veio da caixa, da feira e das encomendas (a métrica soma o `qty` das moedas, agrupado pelo motivo) |
| Encomendas entregues e vencidas | se a reputação está subindo ou descendo |
| Feito no tacho e na composteira | quanto se agregou de valor |
| Plantas derrubadas pela tempestade | quanto custou não ler a previsão |

**As do avaliador (M19, ADR-0070),** lidas do arquivo da corrida, nunca do kernel:

| Métrica | Por quê |
|---|---|
| Tiles vistos, o dia em que viu 90% do mapa, a primeira água à vista | quanto e quando explorou |
| Canteiros cavados e plantios por zona: a várzea (até 4 tiles da água e até 18 da porta), a várzea longe (a mais de 18 da porta), longe (fora da várzea, a mais de 18 da porta) e o resto | onde plantou, pela verdade das regras, que o avaliador pode saber |
| Plantios na várzea depois de ver a água, plantios longe sem espantalho, a distância média dos canteiros à porta, quantas vezes repetiu a cultura do canteiro | se o que viu mudou o que fez |
| A prova do mundo (`eval/prova.yaml`): 11 perguntas fechadas sobre as regras ocultas, com "não sei", antes e depois | o que aprendeu, separado do que já supunha |
| O juiz (`eval/juiz.yaml`): a causa, só o lugar ou não, por regra oculta, nas crenças do fim | o que as crenças mostram, com a crença que sustenta o veredito |
| O modelo do script 3 (`modelo.json`): o efeito de cada atributo com o intervalo de 90% | o que o script aprendeu |
| Os experimentos da noite: a hipótese e o veredito da noite seguinte | como a mente experimenta |

## 11. O clima e a previsão

O sorteio é da biblioteca `libs/climate`; o que o tempo faz é do cenário (ADR-0069).

| | |
|---|---|
| A previsão | às 18:00 sai o tempo de amanhã (`weather.changed.v1` com `forecast`; `weather.tomorrow` na foto; "amanhã" no HUD), e ele não muda |
| As chances | primavera e outono: chuva 20%, tempestade 4%, seca 3%; verão: chuva 25%, tempestade 8%, seca 3%; inverno: chuva 10%, tempestade 4%, seca 10%; o resto é sol |
| A chuva e a tempestade | regam todos os canteiros do dia |
| A tempestade | na manhã dela, antes do crescimento, cada planta madura tem 30% de chance de cair e se perder (`farm.crop.knocked_down.v1`), pelo RNG `storm`; a que amadureceu na própria manhã está a salvo |
| A seca | não chove; a planta não regada até as 12:00 não cresce no dia, mesmo regada à tarde; cada rega gasta 2 cargas |
| O mercado | depois de uma tempestade ou de uma seca, a referência das colheitas sobe 15% por 3 dias |

## 12. O mercado

A caixa de vendas e o quiosque da Morada do Sol usam o mercado da `libs/economy`; a Boa Vista continua com o mercado do dia.

| | |
|---|---|
| A referência | a tabela de venda, vezes a estação (boa 1,0; fraca 1,25; parada 1,6), vezes a oscilação do dia (até 4% por dia, limitada a 15%, pelo RNG `market`), vezes o choque do clima |
| Vender | cada unidade derruba o preço daquela colheita em 2% da referência, até 40%; o que se põe na caixa vale o preço do momento |
| De um dia para o outro | o preço recupera um terço da distância até a referência: 30 unidades despejadas pesam uns quatro dias |
| Comprar | cada semente comprada sobe o preço dela 3% no dia, até o dobro; de manhã volta à tabela. O adubo, o espantalho, a lanterna, o tacho e as ferramentas têm preço fixo |
| O que a caixa compra | as colheitas e os produtos do tacho |

## 13. As encomendas e a feira

| | |
|---|---|
| O quadro | ao lado do quiosque; os pedidos são entidades dentro dele (`order-012`), com cliente, item, quantidade, pagamento e prazo, e só se leem de perto |
| Os pedidos | às 06:00 os vencidos saem e aparecem os novos: 2 vagas por dia, cada uma com 50% de chance (pesada pela reputação, R-004), até 4 no quadro; de 2 a 6 unidades de uma colheita fora da estação parada ou de um produto, prazo de 3 a 7 dias, pagamento 50% acima da referência do dia (pesado pela reputação) |
| Os clientes | Dona Cida, Seu Juca, Dona Nena, Seu Lourenço, a padaria da praça, o restaurante da estrada, a cantina da escola e o mercadinho |
| Aceitar e entregar | `accept_order` (2 minutos, até 2 aceitos) e `deliver_order` (5 minutos, os itens no inventário, pagamento na hora); as recusas `no_order`, `order_taken`, `too_many_orders`, `not_your_order`, `order_expired` |
| A feira | a barraca da entrada da fazenda abre a cada 7 dias (os dias 7, 14, 21 e 28: o último de cada estação), das 06:00 às 14:00, e mostra `proxima_feira`; compra colheitas e produtos 30% acima da referência, com pressão própria (2% por unidade, até 40%) que zera a cada feira, e paga na hora |

## 14. O tacho e a composteira

| | |
|---|---|
| O tacho | 200 moedas no quiosque, peso 6; fincado na grama com `place`; trabalha sozinho, uma receita por vez, e mostra `fazendo` e `faltam_horas`; o produto espera dentro dele e sai pelo `withdraw` |
| As receitas | geleia: 3 morangos, 12 horas, vale 330, validade 30 dias; molho de tomate: 3 tomates, 8 horas, 280, 30 dias; farinha: 4 mandiocas, 8 horas, 450, 90 dias |
| A composteira | ao lado da casa; 3 unidades de uma colheita, ou de restos de planta, viram 1 adubo em 3 dias (`compost`) |
| Os restos | limpar uma planta murcha deixa 1 `resto` no inventário |
| Os produtos | não se comem; vendem-se na caixa, na feira e nas encomendas |

## 15. A fome e as regras de sobrevivência (M19)

Calibradas em 25/out/2026, no começo do script 3 (ADR-0070, decisões 16 e 17).

| | |
|---|---|
| A fome | sobe 2 por hora acordado e 1 dormindo, uns 40 por dia (nas fazendas 1 e 2, 3 por hora: uns 56); o cenário troca o ritmo do gênero com a seção `needs` |
| Por quê | com 3 por hora, nem quem sabe as regras ocultas comia direito: o script 2 passava 16 dos 28 dias com a fome em 100, e o oráculo, de 16 a 17 nos mapas a e c. Com 2, o oráculo atravessa o ano quase sem fome nos três mapas (de 0 a 4 dias com a fome em 100), o script 2 passa 13 dias, e o script 3, que ainda aprende, de 4 a 14: a diferença é o valor de saber, e onde o script 3 fica nela é o que aprender captou (§16) |
| As regras no manual | comer com a fome em 60; separar os canteiros da comida dos de vender (o rabanete na primavera mata uns 8 de fome por dia: uns 5 canteiros pagam o dia, 7 dão folga; na estação fraca da comida, o dobro); guardar comida para dois dias e não vendê-la; não investir o dinheiro da semente da próxima leva dos canteiros de comida; com moedas sobrando, comparar o custo das comidas e anotar o que se descobre dos pratos |
| Quem segue | o script 3 e o oráculo, pelos números do manual; o fazendeiro LLM, pelo manual. O script 2 fica como era: é a linha de base cega das rodadas anteriores |

## 16. O fazendeiro-script 3 e o oráculo (M19)

Escritos em 25/out/2026 (ADR-0070, decisões 4 a 7, 15 e 17). Os números ficam em `cartridges/farm/script/.../data/farmer3.yaml` e `oracle.yaml`.

**O script 3** herda do script 2 o que o manual diz (as culturas, a comida, o calendário, o sono, a exploração) e não sabe nenhuma regra oculta. Vê o que o LLM vê e acrescenta:

| | |
|---|---|
| O caderno de campo | cada plantio: onde, a cultura, a anterior do canteiro, o adubo, os dias de rega, quando amadureceu e o que houve (colhida, comida, derrubada, murcha, sumida); e a fome que cada comida tirou |
| O modelo do ritmo | o logaritmo do ritmo de cada plantio (os dias que o manual e a estação prometem, divididos pelos que levou) como a soma dos efeitos: a faixa de distância à água, à mata, ao caminho e à porta (até 2, 4, 8, 16 tiles, ou mais), a cultura repetida e o adubo. Regressão bayesiana, com a crença larga no começo (0,78 a 1,28 vez num desvio). A mata, o caminho e a porta são distratores |
| O modelo da perda | a chance de perder a madura por faixa de distância da porta (até 8, 16, 32, ou mais) e do espantalho mais perto (até 4, 8, ou mais), numa beta por faixa |
| Onde cavar | a cada manhã sorteia um mundo da crença (amostragem de Thompson) e cava onde esse mundo rende mais por moeda; os primeiros canteiros vão em 3 pares (um no lugar de sempre, outro onde se sabe menos), e depois um canteiro em cada quatro continua como teste |
| O que plantar | pelo mundo médio da crença; troca a cultura do canteiro quando o efeito da repetição fica abaixo de 0,9 com 90% de confiança; deixa voltar a grama o canteiro que rende menos de 70% do melhor lugar novo, com 10 plantios medidos |
| A sobrevivência | as regras do manual (§15): comer com a fome em 60, o prato pronto primeiro e depois a comida mais barata por ponto de fome; os canteiros da comida separados, com 40% de folga; o caixa da semente da comida não se investe; dois dias de comida guardados |
| O dinheiro | os canteiros de vender pelo retorno por moeda por dia, com o caixa acima da reserva e mais 40 moedas; o espantalho quando 6 canteiros ou mais estão onde o mundo do dia perde 20% das maduras ou mais; a composteira com os restos |

Ele esquece tudo quando o processo reinicia, e cada corrida começa do zero: lembrar de outro mapa seria trapaça.

**O oráculo** é o mesmo código com a verdade no lugar da crença (`oracle.yaml`, conferido contra os dados do cartucho por um teste): a água a até 4 tiles, 1,5; a repetição, 0,6; o adubo, 1,5; os corvos a mais de 18 tiles da porta, 1 em 2, sem espantalho a até 6. A diferença entre os dois é só saber.

**Um ano em cada mapa** (seed 20261022, a fome em 2 por hora; moedas, colheitas e dias com a fome em 100):

| Quem | Mapa a | Mapa b | Mapa c |
|---|---|---|---|
| script 2 (não sabe) | 14 · 41 · 13 | 14 · 41 · 13 | 14 · 41 · 13 |
| script 3 (aprende) | 2 · 59 · 4 | 8 · 48 · 6 | 6 · 29 · 14 |
| oráculo (sabe) | 321 · 78 · 3 | 587 · 95 · 0 | 184 · 69 · 4 |

- **O que o script 3 aprende:** a fadiga nos três mapas (0,51 a 0,54) e a água nos mapas a e b (1,3 a 1,4, com o intervalo acima de 1). No mapa c, com as lagoas longe, quase não planta perto da água e não aprende.
- **Sem a água e a fadiga** (`river_bonus=False`), no mapa a, ele faz 246 moedas e não descobre a água; mas vê a repetição acelerar um pouco (1,07, de 1,01 a 1,14): um intervalo de 90% com 19 atributos às vezes exclui o 1 por acaso.
- **O valor de saber** (o oráculo menos o script 2) vai de 170 moedas no mapa c a 573 no b. O script 3, num ano só, ganha em colheitas e em fome nos mapas a e b, mas ainda não em moedas.
- **O script 2 não depende do mapa:** cava em volta do poço e nunca chega perto da água.

## 17. Os ajudantes (M20)

Escritos em 26/out/2026 (ADR-0072 e ADR-0073). Os números ficam na seção `helpers` de `morada.yaml`, e o script do ajudante em `cartridges/farm/script/.../helper.py`.

| Ficha | Diária | Horário | O bom | O ruim |
|---|---|---|---|---|
| Dita, a plantadeira | 40 | 06:00-18:00 | planta e colhe duas vezes mais rápido | anda devagar, cada passo leva o dobro |
| Zé Graúdo, o carregador | 40 | 06:00-18:00 | carrega o dobro e cava mais rápido | come o dobro, a fome sobe duas vezes mais rápido |
| Nina, a batedora | 30 | 06:00-18:00 | vê o dobro do raio e enxerga à noite | cansa rápido (50% mais energia) e não carrega ferramenta acima de 4 |
| Seu Bento, o veterano | 70 | 08:00-16:00 | faz tudo 20% mais rápido e não desmaia | a diária mais cara e o turno mais curto |
| Tião, o aprendiz | 20 | 06:00-18:00 | a diária mais barata | faz tudo 50% mais devagar e perde uma semente em cada dez plantios |

| | |
|---|---|
| O quadro | `helper-board`, em (36, 38), ao lado do de encomendas; mostra quem está livre (`livre` ou `com camps até o dia N`) e a diária de cada um (`diaria_<id>`) |
| O contrato | 1, 3 ou 7 dias, pago adiantado; o ajudante chega pela entrada (33, 38) na manhã seguinte, com fome 0 e energia 100, e sai no fim do turno deixando no baú o que carrega; o último dia encerra o contrato; dispensar não devolve os dias |
| As ordens | dadas ao lado do ajudante, só pelo patrão: cuidar (o padrão: colher, regar e guardar no baú), regar, colher, plantar (a semente do baú), cavar (até 8 canteiros em volta de onde a ordem foi dada), vender (o item do baú na caixa, pago ao patrão) e parar |
| A comida | come do baú com a fome em 60; sem comida no baú, vai para casa mais cedo |
| Dois no mesmo lugar | a ação que outro avatar desfez no meio (o canteiro já colhido, o item que saiu do baú) falha na conclusão, e o avatar decide de novo |
| A visão | cada avatar vê o que está à volta dele; o inventário de outro avatar não aparece |

**Quanto vale um ajudante:** nada, nesta Morada (ADR-0073). O Camps trabalha umas 2 das 16 horas acordado, e o oráculo, sabendo as regras, só cresce a fazenda com o caixa. Com as diárias das fichas, todo contrato forçado de 1, 3 ou 7 dias perdeu dinheiro no ano, e o de 7 dias quase nunca coube no caixa. O ajudante é um teste de julgamento: contratar por impulso dá prejuízo.

**A rodada de verificação** (26/out, [o relatório](../arena/2026-10-26.md)), um ano nos mapas a e b, com a contratação forçada a partir do dia 8:

| Quem | O que pagou | O que mudou no ano |
|---|---|---|
| oráculo | de 1 a 8 contratos, de 120 a 320 moedas | de −74 a −282 moedas, de −3 a +6 colheitas |
| script 3 | só 2 contratos de 1 dia no mapa a (o caixa não pagava mais) | de +1 a +5 moedas, −4 e −5 colheitas |

Os ajudantes do oráculo regaram de 24 a 63 vezes e colheram de 4 a 21 no ano; o trabalho que fizeram, o Camps faria esperando menos.

## 18. A energia (M21)

Recalibrada em 30/out/2026, depois de o usuário jogar o primeiro dia do mapa d (ADR-0074, decisão 23). O mapa é quatro vezes o da Boa Vista, e com os custos dela cavar levava dois terços do dia.

| | |
|---|---|
| Andar | 1 de energia a cada 60 tiles (uma volta na fazenda, uns 300 tiles, custa 5); a Boa Vista segue com 1 a cada 20 |
| Cavar | 15 minutos e 2 de energia (com o arado, 5 minutos e 2) |
| Plantar | 5 minutos e 1 (com o arado, 1 minuto e 0,5) |
| Regar e limpar | 1 cada; encher o regador e colher, 0,5 cada |
| O que não muda | a energia de 100, 1 por hora acordado, o dobro com a fome em 80, o sono e o desmaio |
| Um dia | uns 20 canteiros novos (cavar, plantar e regar custam 4); regar todo dia o que cresce segura quem trabalha sozinho em uns 57 canteiros, e daí em diante o ajudante tem serviço |
| O freio | a semente e o caixa: com as 100 moedas do começo, uns 12 canteiros no primeiro dia; o oráculo cavou no máximo 12 ou 13 num dia |
| As réguas | refeitas em `data/arena/m21-terceira-energia` (a tabela na ADR-0074); a promessa do mapa d continua de pé |

