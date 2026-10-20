# ADR-0062 — Decisões do plano do M13 (a fazenda 2, "Fazenda Boa Vista")

**Status:** aceita · **Data:** 2026-10-19 · **Marco:** M13
**Complementa:** `docs/planos/m13-fazenda-2.md`; `docs/planos/ideia-m13-fazenda-mais-rica.md`; `docs/planos/v0.2-macro.md`; ADR-0025 (modelo de mundo), ADR-0031 (cartuchos em camadas), ADR-0061
**Altera:** o plano macro da v0.2 (o M13 passa a ser a fazenda 2, a segunda rodada da arena vira o M14 e o fechamento, o M15); o modelo de mundo do kernel (ADR-0025) ganha quatro primitivas genéricas

## Decisão

As decisões do plano, aprovadas pelo usuário na noite de 19/out/2026, depois da conversa sobre a proposta da fazenda mais rica:

1. **Três marcos:** M13 a fazenda 2, M14 a segunda rodada da arena (com Sonnet e Opus), M15 o fechamento da v0.2 com a tag `v0.2.0`.
2. **Um cenário novo que estende `farm_camps`** (ADR-0031): o cartucho `farm_boavista`, com o mundo `farm-boavista-01`. A fazenda 1 (`farm-camps-01`) fica intacta, com seus testes, seu arquivo e sua arena como linha de base.
3. **Sete culturas,** as três de hoje recalibradas (abóbora a 8 moedas por canteiro-dia, vendendo a 104) e quatro novas (cenoura, morango, tomate a 10 por canteiro-dia vendendo a 70, alho), com duas regras ocultas por cultura: o tomate murcha com um dia sem rega e o alho cresce sem rega.
4. **O mapa nasce sem canteiros.** A ação `cavar`, com a pá, em qualquer tile de grama, leva 15 minutos e 8 de energia e cria um canteiro; teto de 32. A regra R-001 do rio não muda; "onde cavar" vira a descoberta.
5. **Peso e capacidade:** avatar 20, baú 100; pá 3, regador 4, regador grande 9 (150 moedas, 25 cargas), arado 12 (300 moedas; plantar em 1 minuto e 1 de energia, cavar em 5 minutos); sementes 0,1, colheitas 0,5 (abóbora 2), adubo 1. Arado e regador grande não cabem juntos pelos números; a recusa é `too_heavy`.
6. **Mercado:** cada 5 unidades da mesma colheita vendidas no dia derrubam o preço dela 10% (piso 50%), voltando no dia seguinte, com o preço do dia visível na caixa; o quiosque vende sementes num ciclo de 6 dias (rabanete e cenoura todos os dias; batata 1, 3, 5; alho 2, 4, 6; tomate 2, 5; abóbora 1, 4; morango 3), mostrando só o estoque do dia, sem o ciclo no manual.
7. **Adubo:** 15 moedas, peso 1, aplicado no canteiro vazio antes de plantar, +0,5 ponto por dia regado naquele plantio, com o tamanho do efeito oculto.
8. **Cozinhar:** um fogão fixo na casa e três receitas (sopa de batata 90; ensopado 110 e a fome subindo à metade por 8 horas, oculto; purê de abóbora 60), com ingredientes e tempo no manual e o valor em fome só comendo. O efeito do ensopado usa a primitiva de modificador de necessidade; se ela não couber no marco, o ensopado fica só com o valor alto.
9. **Urgência:** a planta madura murcha depois de 3 dias sem colher (visível); as colheitas têm validade (rabanete 4, batata 10, abóbora 30, cenoura 6, morango 2, tomate 3, alho 60 dias), visível, e o baú dobra a validade (oculto), pela primitiva de lotes com idade.
10. **Andar gasta 1 de energia a cada 20 tiles.**
11. **O fazendeiro-script 2** (`farmer2`, no gênero) segue o manual com regras boas e nenhuma oculta: cava 16 canteiros ao redor do poço, planta a melhor conta visível que o dinheiro permite guardando comida para dois dias, rega, colhe, vende, compra o regador grande com 150 sobrando e o arado com 300, cozinha a sopa com duas batatas, dorme na cama.
12. **O manual da mente conta o visível e cala o oculto:** preços, dias aproximados, validades, receitas e peso sim; tomate, alho, baú, ensopado, tamanho do adubo e ciclo do quiosque não. O teste de "nenhuma dica da regra" cobre todos.
13. **Métricas novas,** definidas agora e usadas no M14: canteiros a até 4 tiles do rio, dia da compra de cada ferramenta, mistura de culturas, refeições cozinhadas, itens estragados.
14. **Arte LPC** para pá, arado, regador grande, fogão, adubo e as culturas novas, com crédito; placeholder desenhado onde o LPC não tiver.
15. **O nome da fazenda 2 é "Fazenda Boa Vista"**, um nome genérico, por escolha do usuário; o Camps continua o avatar.

## Consequências

- **O kernel ganha quatro primitivas genéricas** (princípio 8), sem tipo de evento novo: peso por item e capacidade por contêiner (`too_heavy` em `action.rejected`); criação de entidade em tempo de execução por `WorldOps.spawn` (`world.entity.spawned`, como no início da sessão, com ids por sequência derivada do estado); lotes de item com idade e o sistema `spoilage` (`world.item.consumed` com motivo `spoiled`; o contêiner pode multiplicar a validade); modificadores de necessidade com fator e validade. A percepção ganha campos opcionais: peso e capacidade, a validade mais curta por item, os modificadores ativos.
- **O gênero `farm`** ganha dados por cultura (`needs_water`, `wither_after_dry_days`, `shelf_life_days`, `harvest_withers_after_days`), itens com peso e categorias `ferramenta` e `adubo`, receitas, as ações `dig`, `fertilize` e `cook`, os sistemas `market` e `kiosk_stock`, afordâncias e métricas novas. A fazenda 1 não liga nada disso.
- **O cenário `farm_boavista`** traz o mapa sem canteiros, os números, o mundo `farm-boavista-01`, a arte e a tela com canteiros que nascem em tempo de execução. O carregador precisa resolver a cadeia `farm_boavista` → `farm_camps` → `farm`.
- **A bíblia 2** (`docs/arquitetura/fazenda-boa-vista-biblia.md`) fixa números e regras e é o primeiro entregável; a arena do M14 ganha mundo e modelo por corrida.
- Para a fazenda 3 (`futuro.md`): espantalho e corvos (R-002), cesta, ferramentas que quebram, pragas, estações.
