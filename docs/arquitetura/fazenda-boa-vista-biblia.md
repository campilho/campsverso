# Bíblia da Fazenda Boa Vista (a fazenda 2, M13)

**Status:** escrita em 19/out/2026 a partir do plano do M13 e da ADR-0062; é a fonte dos números e das regras do cenário `farm_boavista` e do mundo `farm-boavista-01`. O que a bíblia da v0.1 (`fazenda-camps-biblia-v0.1.md`) não diz aqui vale como lá: calendário, fases do dia, sono, desmaio, percepção, política de interrupção.

## 1. Conceito

A Fazenda do Camps (v0.1) validou o núcleo e a ligação com o LLM. A Fazenda Boa Vista existe para medir **como** e **se** um agente decide melhor que um script ou que outro modelo: é um mundo em que as escolhas custam. Sete culturas com custo-benefício bom e ruim, um terreno sem canteiros em que é preciso cavar, ferramentas que pesam e se excluem, um mercado que satura, um quiosque que não tem tudo todo dia, comida que estraga e um fogão. As regras visíveis estão no manual da mente e nesta bíblia; as ocultas, só pelos efeitos, como a R-001 do rio.

O avatar continua o Camps, com o mesmo cartão de identidade.

## 2. O avatar

| Item | Valor |
|---|---|
| Capacidade de carga | **20** (peso; ver §5) |
| Inventário inicial | 100 moedas, pá, regador cheio (10 cargas), 10 sementes de rabanete |
| Baú inicial | 5 rabanetes |
| Velocidade | 30 tiles por minuto, como na v0.1 (ADR-0057) |
| Andar | gasta **1 de energia a cada 20 tiles** percorridos (acumulado por trajeto, arredondado para baixo, com o resto guardado) |

## 3. Calendário, tempo e clima

Como na v0.1: tick de 1 minuto, dia agrícola virando às 06:00, clima sorteado às 05:00 no fluxo `weather` com **20% de chuva**, e a chuva conta como rega para todos os canteiros naquele dia. Sem estações.

**Ciclo do quiosque:** 6 dias, começando no dia 1 (o dia 7 é de novo o dia 1 do ciclo). O estoque do dia é definido às 06:00 e aparece no quiosque; o ciclo não está no manual.

| Semente | Dias do ciclo |
|---|---|
| Rabanete, cenoura | todos |
| Batata | 1, 3, 5 |
| Alho | 2, 4, 6 |
| Tomate | 2, 5 |
| Abóbora | 1, 4 |
| Morango | 3 |

## 4. Mapa

Grade de **32 × 18 tiles**, as mesmas bordas, o rio a leste, **sem canteiros**: eles nascem onde o Camps cava.

```
        0         1         2         3
        01234567890123456789012345678901
y00     TTTTTTTTTTTTTTTTTTTTTTTTTTTTRRRR
y01     T...........................RRRR
y02     T.CCCCC.....................RRRR
y03     T.Cb.mC.....................RRRR
y04     T.Cf..CB....................RRRR
y05     T.CCPCC.....................RRRR
y06     T...=...V...................RRRR
y07     T...=.......................RRRR
y08     T...=.......................RRRR
y09     T...=.......................RRRR
y10     T...=............W..........RRRR
y11     T...=.......................RRRR
y12     T...=.......................RRRR
y13     T...========================RRRR
y14     T..............=............RRRR
y15     T..............=S...........RRRR
y16     T..............=............RRRR
y17     TTTTTTTTTTTTTTTEETTTTTTTTTTTRRRR
```

| Símbolo | Elemento | Coordenadas | Passável |
|---|---|---|---|
| `T` | árvores / cerca | bordas | não |
| `R` | rio | x 28–31 | não |
| `C` | parede da casa | x 2–6, y 2–5 | não |
| `P` | porta da casa | (4, 5) | sim |
| `b` | cama | (3, 3) | não (interagir adjacente) |
| `m` | mesa | (5, 3) | não |
| `f` | **fogão** | (3, 4) | não (interagir adjacente) |
| `B` | baú | (7, 4) | não |
| `V` | caixa de vendas | (8, 6) | não |
| `W` | poço | (17, 10) | não |
| `S` | quiosque | (16, 15) | não |
| `E` | entrada da propriedade | (15–16, 17) | sim (decorativa) |
| `=` | caminho | — | sim |
| `.` | grama: onde se pode **cavar** | — | sim |

**Canteiros:** não existem no início. `cavar` num tile de grama (`.`) ao lado do avatar (um dos 8 ao redor, ou o dele; sem alvo, o dele, que é o que o menu do humano manda), como se rega, cria um canteiro vazio, passável, com id por sequência (`plot-01`, `plot-02`…) e **sem grupo nem rótulo**: o terreno não dá pista, nem o nome; teto de **32** canteiros. Os tiles de terra dos canteiros antigos viraram grama. A **faixa do rio** (a R-001 vale a até 4 tiles do rio, ou seja, x de 24 a 27) tem 64 tiles de grama; o poço fica a 7 tiles dela e a 13 da casa. A faixa só existe para o analista, que a calcula pelas posições (§13). O regador só enche no poço, como na v0.1.

**Interação e movimento:** como na v0.1 (vizinhança de 8 para agir; 4 direções para andar; pathfinding pelo kernel).

## 5. Itens

Todo item tem **peso**; todo contêiner tem **capacidade**: inventário do avatar 20, baú 100, caixa de vendas sem limite. Transferir ou criar além da capacidade recusa com `too_heavy`.

| Item | Categoria | Peso | Compra | Venda | Reduz fome | Validade (dias) |
|---|---|---|---|---|---|---|
| `moeda` | moeda | 0 | | | | |
| `pa` | ferramenta | 3 | (inicial) | | | |
| `regador` (10 cargas) | ferramenta | 4 | (inicial) | | | |
| `regador_grande` (25 cargas) | ferramenta | 9 | 150 | | | |
| `arado` | ferramenta | 12 | 300 | | | |
| `adubo` | adubo | 1 | 15 | | | |
| `semente_*` | semente | 0,1 | tabela §6 | | | |
| `rabanete` | colheita | 0,5 | | 25 | 25 | 4 |
| `batata` | colheita | 0,5 | | 50 | 35 | 10 |
| `abobora` | colheita | 2 | | 104 | 50 | 30 |
| `cenoura` | colheita | 0,5 | | 20 | 15 | 6 |
| `morango` | colheita | 0,5 | | 90 | 20 | 2 |
| `tomate` | colheita | 0,5 | | 70 | 30 | 3 |
| `alho` | colheita | 0,5 | | 40 | 10 | 60 |
| `sopa_de_batata` | prato | 0,5 | | | 90 | 2 |
| `ensopado` | prato | 0,5 | | | 110 (e `satisfeito` por 8 h, **oculto**) | 2 |
| `pure_de_abobora` | prato | 0,5 | | | 60 | 2 |

**Validade:** cada lote de item nasce com o dia de criação; às 06:00 o kernel consome os lotes vencidos (`world.item.consumed`, motivo `spoiled`). A percepção mostra, por item, a validade mais curta. **O baú dobra a validade** de tudo o que guarda (oculto; o manual diz só que o baú "guarda bem").

**Pesos que se excluem:** arado e regador grande somam 21 e não cabem juntos; pá, regador e arado (19) cabem; pá e regador grande (12) cabem. Quem não cabe fica no baú.

## 6. Culturas

| Cultura | Semente | Dias para amadurecer | Venda | Moedas por canteiro-dia | Rega | Seca até murchar | O truque |
|---|---|---|---|---|---|---|---|
| Rabanete | 10 | 3 | 25 | 5 | precisa | 2 dias | a comida barata |
| Batata | 20 | 5 | 50 | 6 | precisa | 2 | |
| Abóbora | 40 | 8 | 104 | 8 | precisa | 2 | prende capital 8 dias |
| Cenoura | 15 | 4 | 20 | 1,25 | precisa | 2 | parece barata, rende menos que tudo |
| Morango | 60 | 6 | 90 | 5 | precisa | 2 | cara, rende como o rabanete, estraga em 2 dias |
| Tomate | 30 | 4 | 70 | 10 | precisa | **1** (oculto) | a melhor conta, se nunca faltar rega |
| Alho | 12 | 7 | 40 | 4 | **não** (oculto) | — | cresce sem rega: a cultura de quem tem pouco tempo |

As colunas "Rega" e "Seca até murchar" são dados por cultura (`needs_water`, `wither_after_dry_days`); o manual diz só que "cada cultura reage à seca do seu jeito".

**Ciclo da planta:** como na v0.1 (`semente` → `broto` → `crescendo` → `madura`; 1,0 ponto por dia regado, ou 1,5 na faixa do rio pela R-001). Mais:

- **A madura murcha depois de 3 dias sem colher** (visível no manual). O sistema de crescimento passa a contar os dias de uma madura; no quarto amanhecer, `murcha`.
- **Adubo:** `adubar` um canteiro vazio marca o próximo plantio com +0,5 ponto por dia regado (o manual diz "faz crescer melhor"; o tamanho é oculto). Na faixa do rio, 2,0 por dia.
- A colheita rende 1 unidade; a percepção expõe só o estágio.

**A conta visível** (por canteiro-dia): tomate 10, abóbora 8, batata 6, rabanete 5, morango 5, alho 4, cenoura 1,25. E a conta da comida: por ponto de fome, o rabanete custa 1 moeda de venda perdida, o alho 4; a sopa de batata (2 batatas, 100 de venda) dá 90.

## 7. Necessidades

Como na v0.1 (fome +3 por hora acordado e +1 dormindo; energia por ação e 1 por hora acordado; dobro de energia por ação a partir de 80 de fome; desmaio em 0), mais:

- **Andar** gasta 1 de energia a cada 20 tiles.
- **Modificadores de necessidade:** um modificador tem um fator sobre a taxa de uma necessidade e uma validade em ticks; o `needs` multiplica a taxa pelos ativos. O ensopado aplica `satisfeito` (fome a 0,5× por 8 horas), visível como atributo do avatar (`satisfeito_ate`) depois de comer; o manual não diz que o ensopado faz isso.

## 8. Catálogo de ações

As da v0.1 continuam (`move`, `water`, `refill`, `harvest`, `clear`, `eat`, `deposit`, `withdraw`, `sell`, `buy`, `sleep`, `wait`), com as mudanças marcadas, e entram três novas.

| Ação | Alvo | Pré-condições | Duração (ticks) | Energia | Efeito |
|---|---|---|---|---|---|
| **`dig`** (cavar) | tile de grama ao lado (`target: {x, y}`; sem alvo, o próprio) | pá no inventário; tile adjacente (ou o próprio), de grama, livre; menos de 32 canteiros | 15 (**5** com o arado) | 8 | cria um canteiro vazio (`world.entity.spawned`) |
| `plant` | canteiro | canteiro vazio; semente no inventário | 5 (**1** com o arado) | 2 (**1** com o arado) | semente consumida; planta em `semente`; se adubado, o bônus do adubo |
| **`fertilize`** (adubar) | canteiro | canteiro vazio e sem adubo; adubo no inventário | 3 | 1 | adubo consumido; canteiro `adubado` até o próximo plantio |
| `water` | canteiro | um regador com carga no inventário; planta no canteiro | 2 | 2 | regador −1 (o grande, se o tiver); regado hoje |
| `refill` | poço | adjacente | 3 | 1 | enche o regador que carrega (10 ou 25) |
| `harvest` | canteiro | `madura` | 3 | 1 | +1 colheita (lote de hoje) |
| `clear` | canteiro | `murcha` | 3 | 2 | canteiro vazio |
| **`cook`** (cozinhar) | fogão | adjacente; ingredientes da receita no inventário | sopa 10, purê 15, ensopado 20 | 2 | ingredientes consumidos; +1 prato (lote de hoje) |
| `eat` | item | comestível (colheita ou prato) no inventário | 10 | 0 | fome reduzida; o ensopado aplica `satisfeito` |
| `sell` | caixa | adjacente; colheita no inventário | 1 | 0 | itens vão para a caixa, pelo preço do dia (§9) |
| `buy` | quiosque | aberto; moedas; item no estoque do dia (sementes, adubo, ferramentas) | 2 | 0 | moedas −; item + (recusa `too_heavy` se não couber) |
| `deposit` / `withdraw` | baú | adjacente; quantidade; capacidade | 1 | 0 | transfere lotes |
| `sleep`, `wait`, `move` | | como na v0.1 | | | andar gasta energia (§7) |

Motivos de recusa novos: `too_heavy`, `no_room` (teto de canteiros), `not_grass`, `out_of_stock`, `missing_ingredients`, `already_fertilized`.

## 9. Sistemas do mundo

| Sistema | Quando | O que faz |
|---|---|---|
| os da v0.1 (`clock_phases`, `weather`, `crop_growth`, `needs`, `buyer`, `kiosk_hours`, `faint`) | como lá | `crop_growth` ganha a murcha da madura, a seca por cultura, a rega por cultura e o adubo |
| **`kiosk_stock`** | 06:00 | define o estoque de sementes do dia pelo ciclo da §3; adubo e ferramentas todo dia |
| **`market`** | a cada venda e às 22:00 | o preço do dia de cada colheita: a cada 5 unidades vendidas no dia, −10% (piso 50%); a caixa mostra o preço de hoje; às 22:00 o comprador recolhe pelo preço de cada lote vendido; às 06:00 paga e os preços voltam |
| **`spoilage`** (kernel) | 06:00 | consome os lotes vencidos, com o fator do contêiner |
| **`needs`** (kernel) | cada tick | aplica os modificadores ativos e expira os vencidos |

## 10. Regras ocultas

| Regra | Onde mora | Visibilidade |
|---|---|---|
| **R-001, bônus do rio:** canteiros a até 4 tiles do rio ganham 1,5 ponto por dia regado | regra do cenário (`rules.yaml`), como na v0.1 | `internal`; só o efeito (dias até amadurecer) |
| O tomate murcha com 1 dia seco | dado da cultura | o manual cala; o efeito é a murcha |
| O alho cresce sem rega | dado da cultura | o manual cala; o efeito é crescer |
| O baú dobra a validade | fator do contêiner | o manual diz "guarda bem" |
| O ensopado deixa `satisfeito` por 8 h | efeito da receita | o atributo aparece depois de comer |
| O tamanho do efeito do adubo (+0,5) | dado do item | o manual diz "faz crescer melhor" |
| O ciclo do quiosque | dado do sistema | o estoque do dia é visível; o ciclo não |

Efeito da R-001 em dias até amadurecer: rabanete 3 → 2, cenoura e tomate 4 → 3, batata 5 → 4, morango 6 → 4, alho 7 → 5, abóbora 8 → 6. Com adubo e rio, 2,0 por dia: rabanete em 2, abóbora em 4.

## 11. Fazendeiro-script 2

Prioridades a cada decisão, na ordem; a primeira aplicável vence; empates por menor distância e depois menor id. Só usa a percepção e **nenhuma regra oculta**.

1. **Dormir:** energia < 10, ou horário ≥ 21:30 → cama.
2. **Comer:** fome ≥ 70 → prato pronto no inventário; senão, com 2 batatas, cozinhar a sopa; senão, a colheita de menor valor de venda no inventário; senão, retirar do baú.
3. **Cavar:** menos de 16 canteiros e pá no inventário → entre os tiles de grama livres a até 2 do poço, cavar um que esteja ao lado (o mais perto do poço); se nenhum estiver, andar até o mais perto do poço.
4. **Colher:** madura → a mais próxima.
5. **Limpar:** murcha → limpar.
6. **Encher:** o regador que carrega está vazio e há planta por regar → poço.
7. **Regar:** não choveu hoje e há planta não regada hoje → a mais próxima (rega tudo, inclusive o alho: não sabe que não precisa).
8. **Plantar:** canteiro vazio e semente no inventário → a semente de melhor conta visível (§6) que tiver.
9. **Guardar:** colheita que vence em 1 dia e não vai comer → baú.
10. **Vender:** colheita além da comida para dois dias (112 pontos de fome, em rabanetes) → vender enquanto o preço do dia for ≥ 80% da tabela; abaixo disso, guardar no baú.
11. **Comprar:** quiosque aberto → o regador grande quando sobrarem 150 + 30 e não o tiver (e depositar o pequeno no baú); senão, para cada canteiro vazio sem semente, a semente de melhor conta no estoque de hoje, guardando 30 moedas. Nunca o arado, nunca o adubo: são as decisões que ficam para quem pensa.
12. **Esperar** 15 minutos.

## 12. Percepção

Como na v0.1 (a propriedade inteira, o terreno, estágios, regado hoje, clima, inventário, baú, fome, energia, horário, quiosque aberto), mais: o peso carregado e a capacidade de cada contêiner visível; a validade mais curta de cada item; o estoque do dia do quiosque; o preço do dia de cada colheita na caixa; os modificadores ativos do avatar. **Não expõe:** pontos de crescimento, dias secos, regras ocultas, o ciclo do quiosque, o fator do baú.

## 13. Métricas

As da v0.1 (colheitas por grupo passa a ser **colheitas na faixa do rio e fora dela**; dias até amadurecer; moedas ao fim do dia; recusas por motivo; murchas; pico de fome e desmaios; tempo real por dia) mais, para a arena do M14:

| Métrica | Por quê |
|---|---|
| Canteiros cavados na faixa do rio / total | descobriu onde cavar |
| Dia da compra de cada ferramenta | planejou capital |
| Mistura de culturas por semana (plantios por cultura) | fez a conta |
| Refeições cozinhadas, por receita | usou o fogão, e qual |
| Itens estragados (por item) e murchas da madura | desperdício por falta de urgência |
| Vendas abaixo de 80% do preço | inundou a caixa |
