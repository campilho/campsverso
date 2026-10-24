# Bíblia da Fazenda Morada do Sol (a fazenda 3, M16)

**Status:** escrita em 23/out/2026, ao fim do M16, a partir do plano do marco e da ADR-0067. É a fonte dos números e das regras do cenário `farm_morada_do_sol` e do mundo `farm-morada-do-sol-01`. O cenário estende a Fazenda Boa Vista: o que esta bíblia não diz vale como na bíblia 2 (`fazenda-boa-vista-biblia.md`) e, abaixo dela, na bíblia da v0.1. Isso inclui as ferramentas, o baú, o mercado que satura, o fogão, a validade, o sono e o desmaio.

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
| O centro | em volta da casa | o poço em (14, 20), a caixa de vendas em (9, 20) |
| A estrada | a linha 22, de x = 6 até o rio | caminho de terra, com ramais para o norte (x = 26) e para o sul (x = 32..33) |
| O quiosque | ao sul, em (34, 36), junto da entrada da fazenda | as sementes, o adubo, o espantalho e as ferramentas |
| O rio | a leste, colunas 60..63, de ponta a ponta | não se pisa |
| A várzea | a grama entre a estrada e o rio, a leste | grama larga, longe da casa |
| O morro | ao norte, linhas 1..7 | uma faixa de mata com uma clareira e uma lagoa pequena em (24..29, 3..5) |
| A clareira | ao sul, dentro de um bosque, em (42..53, 30..35) | grama cercada de mata, com uma trilha de acesso |
| Bosques | soltos no campo | manchas de mata que bloqueiam o caminho reto |

O mapa lógico é gerado por script a partir desta tabela e editado no Tiled daqui em diante. O mapa visual vem do `make mapa-visual`, com árvores LPC por cima da mata, que trocam de cor com a estação (verde, laranja no outono e marrom no inverno seco).

## 4. A percepção

| | |
|---|---|
| Raio | 12 tiles (distância de Chebyshev) em volta do avatar: o script e o LLM recebem o recorte |
| Marcos | cama, porta, baú, fogão, poço, caixa de vendas e quiosque se veem além do raio: quem mora na fazenda sabe onde ficam (`perception_config.landmarks`, decisão 15) |
| Fora da vista | o delta separa `out_of_view` (saiu do raio e continua no mundo) de `gone` (deixou de existir à vista) |
| A lembrança | a mente guarda o último estado visto de cada coisa (os lugares, na `MemoryPort`) e lista no bloco de abertura o que está fora de vista; o fazendeiro-script guarda a sua própria lembrança, com o terreno |

## 5. Os canteiros

| | |
|---|---|
| Onde | em qualquer grama; nunca na estrada, no rio, na mata, na casa ou num tile ocupado |
| Teto | 400, técnico, só para o desempenho; no jogo, os freios são a energia (8 por canteiro cavado), as sementes e a rega |
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
| As da Boa Vista | o tomate murcha com um dia seco; o alho dispensa rega; o baú conserva; o ensopado segura a fome; o adubo vale para o próximo plantio | os da bíblia 2, §10 | os efeitos de sempre |

Os quatro critérios do plano macro: as três novas são **frequentes** (agem sobre plantar, colher e plantar longe), **descobríveis por experimento** (dois canteiros, um perto e outro longe da água, ou um com e outro sem repetição), **valiosas** (a várzea rende uma vez e meia, os corvos levam metade das maduras longe da casa, a fadiga atrasa dois dias um rabanete) e **sistêmicas** (água faz crescer, bicho come o que está sem guarda, monocultura cansa a terra).

## 9. O fazendeiro-script 2 na Morada do Sol

O mesmo script da Boa Vista, com o que só age onde há estação e recorte:

- **A lembrança:** guarda o último estado visto de cada coisa e o terreno; esquece o que estava à vista e sumiu; esquece tudo numa sessão nova.
- **A exploração:** sem nada para fazer, das 08:00 às 17:00, com energia de 45 ou mais e fome abaixo de 55, anda até a fronteira do que já viu. No soak do ano, viu o mapa inteiro entre os dias 2 e 3.
- **O calendário:** não planta nem compra a cultura parada na estação, conta a fraca como duas vezes mais lenta e escolhe a base de comida da estação (rabanete, couve ou milho, a primeira que cresce no ritmo cheio).

Ele não sabe nenhuma regra oculta, e sofre com elas: repete o rabanete nos mesmos canteiros, e a fadiga do solo leva o rabanete de 3 para uns 5,5 dias. No soak de um ano, ele vive sem desmaiar (67 plantios, 56 colheitas, 15 moedas ao fim) e é a linha de base cega até o fazendeiro-script 3, no M19.

## 10. As métricas

As da Boa Vista (bíblia 2, §13), mais duas:

| Métrica | Por quê |
|---|---|
| Plantas comidas, por cultura | quanto a R-002 custou |
| Canteiros que voltaram a ser grama | quanto se cavou à toa |

As de exploração (tiles vistos, distância dos canteiros à casa, canteiros por zona) ficam para o M19, com as variantes do mapa.
