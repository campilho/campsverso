# ADR-0056 — Decisões do plano do M8 (mundo pronto para o LLM)

**Status:** aceita · **Data:** 2026-10-17 · **Marco:** M8
**Complementa:** `docs/planos/m8-mundo-pronto-para-o-llm.md`; `docs/planos/v0.2-macro.md`; bíblia §7, §8 e §12; ADR-0028, ADR-0034, ADR-0038, ADR-0047

## Decisão

As decisões do plano, aprovadas pelo usuário em 17/out/2026:

1. **O kernel publica o terreno no `session.started`,** em campos opcionais do `map`: `rows` (uma string por linha, um caractere por tile) e `legend` (código → nome e propriedades do tileset). Vem de onde a regra oculta lê a água. Limite mapeado: até uns 100 × 100 tiles o desenho serve sem mudar nada; acima disso, o mapa sai da foto e o raio vira obrigatório (`futuro.md`).
2. **O raio de percepção é dado do cartucho** (`perception.radius`; `null` é a propriedade inteira) e vale para todos os atores: humano, script e LLM. A foto ganha `view.map` recortado ao raio. Na v0.2 o raio é a propriedade inteira; um raio menor que o mapa, com névoa na tela, fica no `futuro.md`.
3. **O delta é um tipo novo, `campsverso.perception.updated.v1`.** Acrescentar `delta` ao enum `kind` do `delivered.v1` é incompatível pelas regras do `make compat` (os modelos gerados usam `Literal`). O delta existe para não reenviar o mundo inteiro a cada decisão: só o que mudou e o que aconteceu desde a última entrega.
4. **O delta leva** `since_tick`, `as_of_tick`, `self` inteiro, `clock`, `weather` se mudou, os `containers` e as `entities` que mudaram (registro inteiro), `gone` e `events` (os eventos `world` e `agent` aplicados desde a última entrega, como `{tick, type, data}`).
5. **Política por tipo de controlador,** configurada na percepção: `script` e `replay` recebem sempre a foto; `llm` recebe a foto na primeira decisão, ao assumir a posse e a cada N deltas, com N = 20 configurável. Testada com um controlador de teste `llm` no testkit.
6. **Ficar acordado custa 1 de energia por hora** (`energia.rates_per_hour.awake: -1`), dado do gênero com override do cenário. O valor é ponto de partida, a calibrar com o script.
7. **Fome em 100 drena 4 de energia por hora, sem morte,** por um sistema do gênero de hora em hora (`DailyAt` com as 24 horas). `starving_at` e `starving_energy_per_hour` são dados do gênero, com override do cenário. Equilíbrio nunca vai para o kernel nem para o arquivo do mundo.
8. **Tokens estimados por bytes ÷ 3,5,** por um `make percepcao` que lê um arquivo de eventos e compara as políticas; a contagem real, pelo tokenizador do provedor, chega com a `ModelPort` no M9 e calibra o fator.
9. **Python 3.14 continua.** O PyYAML ainda não tem wheel para o 3.15 (o gatilho da ADR-0034); o `datamodel-code-generator` 0.85 já roda nele. Revisitar no M13.

## Consequências

- Contratos: `world.session.started.v1` ganha `map.rows`, `map.legend` e `perception`; `perception.delivered.v1` ganha `view.map`; nasce `perception.updated.v1`. Nenhum tipo `.v2`.
- A percepção passa a guardar, por avatar, a última visão entregue; depois de uma queda, a primeira entrega é uma foto.
- O script e o replay não mudam de comportamento; os soaks de 30 dias mostram o efeito das regras novas na linha de base (moedas, pico de fome, desmaios).
- A necessidade "sono", correr e andar gastando energia continuam no `futuro.md`.
