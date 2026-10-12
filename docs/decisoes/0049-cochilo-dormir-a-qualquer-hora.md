# ADR-0049 — Cochilo: dormir a qualquer hora

**Status:** aceita · **Data:** 2026-10-12 · **Marco:** M4 (passo zero)
**Altera:** `fazenda-camps-biblia-v0.1.md` §7, §8 e §11; ADR-0041 (decisão 4)

## Contexto

O sono da v0.1 tinha uma só hora para acordar, as 06:00. Por isso só se podia dormir das 20:00 em diante: quem deitasse às 14:00 dormiria 16 horas. Antes disso, a ação era recusada com `too_early_to_sleep`, e a ADR-0041 deixou o cochilo para o futuro.

Na revisão do M3, o usuário pediu que se possa dormir a qualquer hora, com uma regra para acordar que dependa de ser noite ou dia.

## Decisão

1. **`sleep` vale a qualquer hora**, com ou sem cama, como na ADR-0041.
2. **Começou à noite** (das 20:00 às 06:00): dorme até as 06:00, como antes.
3. **Começou de dia: é um cochilo.**
   - Acorda quando a energia chega a 100, na taxa do lugar (cama 12,5/h, chão 5/h), ou às 06:00, o que vier antes.
   - A duração sai de uma conta no começo do sono. O kernel não ganha nada novo: `start_sleep` já recebe quantos ticks dormir.
   - O cochilo não acorda o avatar no meio da noite, então ele não cai no desmaio das 02:00.
4. **De dia com energia 100**, o cochilo duraria zero e é recusado com `not_tired`. O motivo `too_early_to_sleep` deixa de existir.
5. **Fazendeiro-script:** energia abaixo de 10 leva a dormir a qualquer hora. De dia, isso vira cochilo.
6. **Dados do gênero:** `sleep.allowed_from` vira `sleep.night_from`, porque deixou de ser uma permissão e passou a marcar onde começa a noite.

## Para o futuro (não agora)

- **A necessidade "sono"** (ADR-0041), uma pressão de sono que sobe acordado e só baixa dormindo. Um dia que acabou tarde deixaria o avatar com sono no dia seguinte. Faz sentido quando houver quem vire a noite: o LLM, ou o humano jogando. Está em `docs/planos/futuro.md`.

## Consequências

- Nenhum contrato muda: `sleep.started.v2` já traz `wake_at_tick` e `cause: voluntary`.
- Nos soaks de 30 dias a energia do script nunca ficou abaixo de 30. Ele não cochila, e os números do M3 continuam valendo.
