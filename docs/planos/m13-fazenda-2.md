# Plano do M13 — A fazenda 2, "Fazenda Boa Vista"

**Status:** aprovado na noite de 19/out/2026 (ADR-0062), a partir de `ideia-m13-fazenda-mais-rica.md` e da conversa que a seguiu; o nome escolhido pelo usuário é "Fazenda Boa Vista", e com ele o cenário se chama `farm_boavista` e o mundo, `farm-boavista-01`. Sexto marco da v0.2. Com ele, o plano macro muda: o M13 é a fazenda 2, o **M14** é a segunda rodada da arena (com Sonnet e Opus) e o **M15** é o fechamento da v0.2.

**Pronto quando:** existe um segundo mundo, `farm-boavista-01`, no cenário `farm_boavista`, com todas as mecânicas da §1; o fazendeiro-script 2 vive 30 dias nele em modo máximo sem recusa; a mente joga nele com o manual novo e uma fita de dois dias reproduz sem rede; `make check` verde com determinismo, replay e soak no mundo novo; a bíblia 2 documenta números e regras; e a fazenda 1 (`farm-camps-01`, seus testes e seu arquivo) continua intacta.

## A pergunta

A arena do M12 mostrou que, na fazenda 1, um Haiku com memória empata ou passa o script em moedas em duas de quatro seeds, mas em 30 dias nenhuma seed guardou uma crença sobre o rio: a mais perto chegou a "a abóbora amadurece em 6 dias nos canteiros do leste, não 8" no dia 23 e diluiu isso para "depende do canteiro" até o dia 30. O comportamento não discrimina (todo mundo planta uns 55 a 60% no leste, o script por rotina). A fazenda 1 é simples demais para separar quem decide bem de quem segue a rotina, e a sua geometria (dois grupos iguais, um colado ao rio) entrega a pergunta. A fazenda 2 é o mundo em que as escolhas custam: o que plantar, onde cavar, que ferramenta comprar, o que comer e quando vender. É nela que a segunda rodada (M14) compara Haiku, Sonnet e Opus com o script 2.

## O que o levantamento mostrou

- **O cenário é a camada certa.** Um cartucho `farm_boavista` que estende `farm_camps` (ADR-0031) herda o Camps, o cartão, a arte e a regra R-001, e troca o mapa, os números e as mecânicas ligadas. As mecânicas novas vão para o gênero `farm` como dados, ações, sistemas e regras que o cenário liga; a fazenda 1 não as vê. O carregador precisa resolver a cadeia de três (`farm_boavista` → `farm_camps` → `farm`); se hoje só resolve um nível, é um ajuste pequeno.
- **Quatro primitivas faltam no kernel,** todas genéricas (princípio 8): o `WorldOps` não cria entidade em tempo de execução (o `spawn` é só do construtor), os itens são contagens por contêiner (sem peso, sem capacidade, sem idade) e as necessidades não têm modificadores. Nenhuma pede contrato novo: `world.entity.spawned` já existe, a recusa `too_heavy` é um token de `action.rejected`, o estrago é `world.item.consumed` com motivo `spoiled`, e a validade entra como campo opcional dos itens na percepção.
- **O mapa sem canteiros muda a pergunta da regra oculta.** Com o terreno livre e a pá, "onde cavar" vira a descoberta: a fração dos canteiros a até 4 tiles do rio substitui "plantios no leste" como sinal, e a primeira crença que fale do rio é o sinal da memória.
- **O script 2 é a linha de base competente e cega.** Ele segue o manual com regras boas (cava perto da casa, planta a melhor conta visível que o dinheiro e a comida permitem, compra o regador grande quando sobra) e não sabe nenhuma regra oculta. A distância dele para o LLM é a medida do M14.

## 1. O mundo da fazenda 2 (bíblia 2)

A bíblia 2 (`docs/arquitetura/fazenda-boa-vista-biblia.md`) é o primeiro entregável e fixa estes números; o que está aqui é o resumo.

**Culturas** (moedas por canteiro-dia = (venda − semente) / dias):

| Cultura | Semente | Dias | Venda | Por canteiro-dia | Reduz fome | Validade (dias) | O truque |
|---|---|---|---|---|---|---|---|
| Rabanete | 10 | 3 | 25 | 5 | 25 | 4 | a comida barata |
| Batata | 20 | 5 | 50 | 6 | 35 | 10 | |
| Abóbora | 40 | 8 | 104 | 8 | 50 | 30 | prende capital 8 dias |
| Cenoura | 15 | 4 | 20 | 1,25 | 15 | 6 | parece barata, rende menos que tudo |
| Morango | 60 | 6 | 90 | 5 | 20 | 2 | cara, rende como o rabanete, estraga rápido |
| Tomate | 30 | 4 | 70 | 10 | 30 | 3 | murcha com um dia sem rega (oculto) |
| Alho | 12 | 7 | 40 | 4 | 10 | 60 | não precisa de rega (oculto) |

Regras visíveis no manual: preços de semente e de venda (também no quiosque e na caixa), dias "aproximados", validade das colheitas, a madura murcha depois de 3 dias sem colher. Regras ocultas, só pelos efeitos: o tomate murcha com um dia seco (as outras com dois), o alho cresce sem rega, o baú dobra a validade, a R-001 do rio (canteiros a até 4 tiles ganham 1,5 ponto por dia regado).

**Terreno e canteiros:** o mapa nasce sem canteiro. A ação `cavar` (ou "montar canteiro"), com a pá no inventário, em qualquer tile de grama, leva 15 minutos e 8 de energia e cria um canteiro vazio; o menu de plantar só aparece nele. Teto de 32 canteiros no terreno. O rio continua a leste, o poço no meio, a casa (com baú, cama e fogão) a oeste, o quiosque e a caixa de vendas como hoje.

**Ferramentas e peso** (capacidade do avatar 20; do baú 100):

| Item | Peso | Preço | Efeito |
|---|---|---|---|
| Pá (inicial) | 3 | | cava |
| Regador (inicial), 10 cargas | 4 | | rega |
| Regador grande, 25 cargas | 9 | 150 | menos idas ao poço |
| Arado | 12 | 300 | plantar em 1 minuto e 1 de energia (em vez de 5 e 2); cavar em 5 minutos |
| Sementes | 0,1 | tabela | |
| Colheitas | 0,5 (abóbora 2) | | |
| Adubo | 1 | 15 | +0,5 ponto por dia regado no plantio seguinte (tamanho oculto) |

Arado e regador grande somam 21 e não cabem juntos; pá, regador e arado (19) cabem. Quem não cabe fica no baú (`deposit` e `withdraw`). A recusa é `too_heavy`.

**Mercado:** cada 5 unidades da mesma colheita vendidas no dia derrubam o preço dela 10% (piso 50%), e o preço volta ao normal no dia seguinte; a caixa mostra o preço de hoje. O quiosque vende sementes num ciclo de 6 dias, mostrando só o estoque do dia; o ciclo não vai para o manual:

| Semente | Dias do ciclo |
|---|---|
| Rabanete, cenoura | todos |
| Batata | 1, 3, 5 |
| Alho | 2, 4, 6 |
| Tomate | 2, 5 |
| Abóbora | 1, 4 |
| Morango | 3 |

**Comida:** as colheitas cruas matam a fome pela tabela. O fogão da casa cozinha três receitas, com ingredientes e tempo no manual e o valor em fome só comendo:

| Receita | Ingredientes | Preparo | Reduz fome | O truque |
|---|---|---|---|---|
| Sopa de batata | 2 batatas | 10 min | 90 | melhor que as duas cruas (70) |
| Ensopado | batata, cenoura, alho | 20 min | 110 | a fome sobe à metade por 8 h (oculto) |
| Purê de abóbora | 1 abóbora | 15 min | 60 | mal paga o tempo (crua dá 50) |

**Andar gasta energia:** 1 ponto a cada 20 tiles, para a distância custar e não só o tempo (tarefa do `futuro.md` desde o M3).

**O fazendeiro-script 2** (`farmer2`, no gênero, com os números do cenário): nos dois primeiros dias cava 16 canteiros ao redor do poço; planta a cultura de melhor conta visível que o dinheiro permite, guardando comida para dois dias; rega tudo, colhe o maduro, vende o que não come; compra o regador grande quando sobram 150 e o arado quando sobram 300; cozinha a sopa quando tem duas batatas; dorme na cama. Nada de regra oculta.

## 2. O kernel (ADR-0062): quatro primitivas genéricas

1. **Peso e capacidade.** `ItemDef.weight` e `KindDef.capacity`; `transfer_item` e `create` recusam com `too_heavy`; a percepção mostra o peso carregado e a capacidade (campos opcionais).
2. **Criar entidade em tempo de execução.** `WorldOps.spawn(SpawnDef)` por efeito de ação ou sistema, publicando `world.entity.spawned` como no início da sessão; ids estáveis por sequência (`plot-01`, `plot-02`...) derivados do estado, não do relógio.
3. **Lotes de item com idade.** Um item com `shelf_life_days` vive em lotes (dia de criação, quantidade) dentro do contêiner; o sistema `spoilage` do kernel, às 06:00, consome os vencidos com `world.item.consumed` motivo `spoiled`; a percepção mostra a validade mais curta por item (campo opcional). O contêiner pode multiplicar a validade (`KindDef.shelf_life_factor`, oculto): é como o baú dobra.
4. **Modificadores de necessidade.** Um modificador com fator e validade em ticks sobre a taxa de uma necessidade (`needs` multiplica a taxa pelos ativos), aplicado por ação ou sistema, visível como atributo do avatar (`satisfeito até 14:00`); é o ensopado, e serve ao sono e ao escritório depois.

Determinismo como sempre: funções puras do estado, ordenação por id, RNG nomeado. Snapshots ganham os lotes e os modificadores; o replay continua exato.

## 3. O gênero `farm`

- **Dados por cultura:** `needs_water`, `wither_after_dry_days`, `shelf_life_days`, `harvest_withers_after_days`; `items` com peso, categoria `ferramenta` (pá, regador, regador grande, arado) e `adubo`; `recipes`.
- **Ações novas:** `dig` (cavar), `fertilize` (adubar um canteiro vazio), `cook` (no fogão, com a receita como parâmetro); `plant` e `dig` mais rápidos com o arado; `buy` passa a vender ferramentas e adubo; `water` com o regador que estiver no inventário (10 ou 25 cargas).
- **Sistemas novos:** `market` (o preço do dia por colheita, a partir das vendas do dia, com o preço visível na caixa), `kiosk_stock` (o ciclo de sementes), a murcha da madura e o tomate/alho dentro do `crop_growth` por dados.
- **Afordâncias e métricas:** cavar na grama, cozinhar no fogão, adubar no canteiro vazio; métricas novas: canteiros a até 4 tiles do rio, ferramentas compradas (dia), mistura de culturas, refeições cozinhadas, itens estragados.
- **Testes de unidade** para cada ação e sistema, e `hypothesis` para peso e capacidade (nunca ultrapassa; nunca fica negativo).

## 4. O cenário `farm_boavista`

- `cartridges/farm_boavista/sim`: manifesto `extends=("farm_camps",)`; `data/map.tmj` (terreno sem canteiros: grama ao redor, o rio a leste, o poço no meio, a casa com cama, baú e fogão, o quiosque e a caixa); `world.yaml` com os números da §1 e as mecânicas ligadas; `rules.yaml` com a R-001 como está.
- `config/worlds/farm-boavista-01.yaml`: `cartridge: farm_boavista`, seed própria, orçamento e `minds` como o mundo 1.
- Arte: `cartridges/farm_boavista/art` com o mapa visual (`make mapa-visual MUNDO=farm-boavista-01`), e no gênero os sprites LPC de pá, arado, regador grande, fogão, adubo e das culturas novas, com `CREDITS.csv`. O Camps não muda.
- A tela: canteiros que nascem em tempo de execução (o renderer já recebe `entity.spawned`; falta desenhar o canteiro na hora), o fogão e os itens novos no menu de ações, o peso no painel.

## 5. A mente

- O manual do gênero (`cartridges/farm/mind/data/fazenda.md`) ganha o que é visível na §1 e nada do que é oculto; o teste de "nenhuma dica da regra" passa a cobrir tomate, alho, baú, ensopado, adubo e o ciclo do quiosque.
- `tools.yaml` ganha `dig`, `fertilize`, `cook` e os parâmetros novos de `buy`; o teste do catálogo contra as afordâncias continua.
- `make fita DIAS=2 MUNDO=farm-boavista-01` grava a fixture do mundo 2 (uns centavos); o teste e2e da mente roda nos dois mundos.

## 6. Testes do marco

- Determinismo e replay no mundo 2 (os testes de hoje, parametrizados pelo mundo).
- `make soak DAYS=30 MUNDO=farm-boavista-01` com o script 2: nenhuma recusa, nenhum desmaio, moedas crescendo.
- Um dia do humano no sandbox do mundo 2, para ver os menus novos (referência qualitativa).
- O CI nunca chama a API: só a fita.

## 7. Ordem do trabalho

1. **A bíblia 2 e a ADR-0062** (números, regras, primitivas), aprovadas antes do código; `CLAUDE.md`, README e o plano macro com M13 a M15.
2. **O kernel:** as quatro primitivas, com testes e os campos opcionais nos contratos da percepção.
3. **O gênero:** dados, ações, sistemas, afordâncias e métricas.
4. **O cenário:** mapa, números, mundo, arte, tela.
5. **O script 2, o manual da mente e a fita** do mundo 2.
6. **Fechamento:** `make check`, soak, §9, diário, `futuro.md` (fazenda 3: espantalho e corvos, cesta, ferramentas que quebram, pragas), `make sessoes MARCO=M13`, custos.

Estimativa: cinco ou seis sessões, o maior marco da v0.2. Custo de API: só a fita (centavos).

## 8. Decisões

Aprovadas em 19/out/2026 (ADR-0062), todas como recomendado; a 15 com o nome do usuário.

1. **Três marcos:** M13 a fazenda 2, M14 a segunda rodada da arena, M15 o fechamento. *Recomendação: sim; o M13 sozinho já tem cinco sessões, e a rodada tem decisões de custo próprias.*
2. **Um cenário `farm_boavista` que estende `farm_camps`,** com o mundo `farm-boavista-01`; a fazenda 1 intacta. *Recomendação: sim.*
3. **As culturas da §1,** com as duas regras ocultas por cultura (tomate, alho). *Recomendação: sim.*
4. **Canteiros a partir do zero, com a pá;** teto de 32; cavar só na grama; 15 minutos e 8 de energia. *Recomendação: sim.*
5. **Peso e capacidade com os números da §1** (avatar 20, baú 100), arado e regador grande excludentes pelos números, recusa `too_heavy`. *Recomendação: sim.*
6. **Mercado:** saturação (−10% a cada 5, piso 50%, volta no dia seguinte) e o ciclo de 6 dias do quiosque, fora do manual. *Recomendação: sim.*
7. **Adubo** a 15, peso 1, no canteiro vazio, +0,5 com o tamanho oculto. *Recomendação: sim.*
8. **Cozinhar:** o fogão e as três receitas, com o efeito do ensopado pela primitiva de modificador. *Recomendação: sim; se a primitiva não couber, o ensopado fica só com o valor alto.*
9. **A madura murcha depois de 3 dias sem colher** (visível) e **validade das colheitas** pela tabela, com o baú dobrando (oculto), pela primitiva de lotes. *Recomendação: sim; é o que dá sentido ao baú e pune o estoque parado.*
10. **Andar gasta 1 de energia a cada 20 tiles.** *Recomendação: sim.*
11. **O script 2** com as regras visíveis da §1, no gênero. *Recomendação: sim.*
12. **O manual conta o visível e cala o oculto,** como na §1. *Recomendação: sim.*
13. **As métricas novas** (canteiros no rio, ferramentas, mistura, refeições, estragos) definidas agora e usadas no M14. *Recomendação: sim.*
14. **Arte LPC para os itens novos,** com crédito; placeholder desenhado onde o LPC não tiver. *Recomendação: sim, meia sessão.*
15. **O nome da fazenda 2.** *Recomendação: "Sítio do Camps", a decidir pelo usuário.* **Decidido: "Fazenda Boa Vista"**, um nome genérico.

## 9. Como ficou

*(Em curso; o fechamento completa esta seção.)* Na noite de 19 para 20/out, as etapas 1 a 5 do trabalho ficaram prontas, menos a arte própria e a tela: a bíblia 2 e a ADR-0062; as primitivas do kernel (peso e capacidade, entidade em tempo de execução, lotes com validade, modificadores de necessidade, ferramentas como entidades guardadas pelo evento novo `world.entity.stored`, custo de andar); o gênero com `contribute_extensions` e as ações `dig`, `fertilize` e `cook`, o mercado, o estoque do quiosque e o crescimento por cultura; o cenário `farm_boavista` (estende `farm_camps`, como decidido; o carregador já resolvia cadeias), o mundo `farm-boavista-01` e `MUNDO=` nos alvos do make; o fazendeiro-script 2; a mente `camps_boavista` com o manual e o catálogo novos; a camada de arte com o mapa visual e cores de reserva para o fogão e as culturas novas (a tela já desenha canteiros que nascem, porque percorre as entidades a cada quadro). Duas decisões de implementação, a vetar: cavar não recebe coordenadas (cava-se no tile de grama em que o avatar está), e o grupo visível do canteiro é `oeste` ou `leste` pelo lado do mapa, não a faixa do rio, que é a regra oculta e a arena calcula pelas posições.
