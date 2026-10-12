# ADR-0042 — Eventos de sono v2 e a taxa do chão no gênero

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M2
**Complementa:** ADR-0041 · **Altera:** catálogo §3.5 (`sleep.started`, `sleep.ended`)

## Contexto

A ADR-0041 deixou dormir em qualquer lugar, mas não disse como isso aparece nos eventos.

- `sleep.started.v1` e `sleep.ended.v1` têm `cause ∈ {bed, faint}`. Dormir no chão por escolha não cabe em nenhum dos dois.
- Acrescentar um valor a um enum é mudança incompatível (ADR-0033): os modelos gerados usam `Literal`, e um consumidor antigo recusaria o valor novo. O `make compat` do CI barraria.

## Decisão

1. **Tipos novos `campsverso.avatar.sleep.started.v2` e `sleep.ended.v2`** (aprovado pelo usuário):
   - `cause ∈ {voluntary, faint}`: o motivo de dormir, não o lugar;
   - `bed_id` opcional: a cama ou análogo usado. Ausente quando o avatar dorme onde está.
   - O kernel publica só os v2. Os v1 ficam no catálogo marcados com `deprecated`, sem produtor.
2. **A taxa do chão é a taxa `asleep` da energia no gênero: 5/h.**
   - A cama passa à primitiva `start_sleep` as taxas que substituem essa, declaradas nos dados do gênero (`sleep.beds.bed: {energia: 12,5}`).
   - Um análogo futuro (rede, sofá) só acrescenta uma linha em `sleep.beds`.
   - Assim o número 5 fica num lugar só. O desmaio também dorme no chão, a 5/h, e continua acordando com energia 50 (bíblia §7).
3. **`sleep` sem alvo dorme onde está, mesmo ao lado da cama.** Com alvo, o alvo precisa ser um tipo listado em `sleep.beds` e estar adjacente (`invalid_params` e `not_adjacent`, nessa ordem).

## Consequências

- Quem consome eventos de sono (percepção no M3, UI no M4) lê os v2.
- `SleepCause` na cartridge-api passa a ser `voluntary | faint`. A cartridge-api não é contrato publicado, então muda sem tipo novo.
- Durante o desmaio, a energia sobe 5/h em vez de 12,5/h até as 06:00, quando vira 50. Só os valores intermediários mudam.
