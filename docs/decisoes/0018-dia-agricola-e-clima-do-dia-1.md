# ADR-0018 — Dia agrícola e clima do primeiro dia

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M1
**Esclarece:** `fazenda-camps-biblia-v0.1.md` §3 e §6

## Contexto

- A bíblia diz que, às 06:00, cada planta "que foi regada no dia anterior" ganha pontos. Não fica claro se "dia" é o dia do calendário (00:00–24:00) ou o dia agrícola, que vira às 06:00.
- O clima é sorteado às 05:00, mas o mundo começa no dia 1 às 06:00, depois do horário do primeiro sorteio.

## Decisão

1. **Dia agrícola D** = intervalo [06:00 do dia D, 06:00 do dia D+1). "Regado hoje" (percepção e script) e "regada no dia anterior" (crescimento às 06:00) se referem a esse intervalo.
2. O clima sorteado às 05:00 do dia D vale para o dia agrícola D. Se chover, todos os canteiros contam como regados no dia agrícola D.
3. O clima do **dia 1** é sorteado na abertura da sessão, com o mesmo fluxo de RNG `weather`, antes do primeiro tick.
4. A ordem dos sistemas que rodam no mesmo tick (por exemplo, às 06:00: crescimento, pagamento do comprador, novo dia agrícola) é declarada pelo cartucho e documentada no M1.

## Consequências

- O crescimento depende só do estado do dia agrícola anterior, o que simplifica o teste de unidade de `crop_growth`.
- A primeira manhã tem clima definido, como qualquer outra.
