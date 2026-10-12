# ADR-0054 — Decisões do plano do M7 (fechamento da v0.1)

**Status:** aceita · **Data:** 2026-10-12 · **Marco:** M7
**Complementa:** `docs/planos/m7-fechamento.md`; escopo §6, §7 e §8; bíblia §13; ADR-0047, ADR-0051

## Decisão

As decisões do plano, aprovadas pelo usuário:

1. **O cartucho declara as métricas como dados.**
   - Fica no `farm.yaml`, como o catálogo de ações. O kernel publica o catálogo no `session.started`, num campo opcional.
   - A projeção comum conta por dia simulado, e o painel do operador mostra.
   - Três tipos genéricos:
     - `count`: conta um tipo de evento, com filtro por campos e agrupamento por um campo ou por um atributo da entidade citada;
     - `max_need`: o pico de uma necessidade no dia;
     - `item`: a quantidade de um item com os avatares no fim do dia.
   - **Em camadas:** um cartucho que especializa outro acrescenta métricas às do gênero.
   - **Os grupos oeste e leste** viram o atributo `group` dos canteiros, uma propriedade dos objetos do mapa. Nenhum código conhece prefixos de id.
2. **O painel mostra hoje, ontem e os últimos 7 dias,** quando houver. `make metrics` continua lendo o arquivo inteiro, com "dias até amadurecer" e "tempo real por dia".
3. **Um documento de aceite (`docs/aceite-v0.1.md`)** traz cada critério com a evidência e o resultado.
   - A3, A10 e A11 vêm de dois soaks de 30 dias, com e sem a regra oculta.
   - Simulações mais longas ficam para depois; com estações do ano, roda-se 1 ano.
4. **O mundo oficial `farm-camps-01` é criado pelo usuário com `make run`,** no fechamento. Quanto tempo e em que modo ele roda na primeira noite fica para depois de medir a velocidade nos soaks do M7.
5. **README final com um diagrama de arquitetura em Mermaid,** e um `docs/diario/README.md` com o índice do diário e "a v0.1 em números".
6. **Tag `v0.1.0`,** com notas de lançamento, no fim e com o ok do usuário para o push da tag.

## Consequências

- `session.started.v1` ganha `metrics`, e o `ObserverState` ganha as métricas por dia (só os últimos 8 dias, para o estado não crescer).
- A cartridge-api ganha `MetricDef` e `WorldBuilder.add_metric`. O kernel confere cada métrica ao montar o mundo: o evento existe nos contratos, e a necessidade e o item existem no mundo.
- Propriedades extras dos objetos do mapa viram atributos visíveis da entidade. Hoje, só o `group` dos canteiros.
