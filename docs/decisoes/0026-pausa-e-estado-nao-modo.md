# ADR-0026 — Pausa é estado, não modo

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0 (contratos), M1 (kernel)
**Altera:** `escopo-v0.1.md` §3 e §5; `kernel-gestao-do-tempo.md` §5

## Contexto

O escopo e o documento de tempo (§5) listam "pausado / passo a passo" como um **modo** de relógio. Mas o mesmo documento (§12 e §13) dá à pausa eventos e comandos próprios (`clock.paused`, `clock.resumed`, `cmd.clock.pause`, `resume`, `step`), separados de `clock.mode_changed` e `cmd.clock.set_mode`.

## Decisão

- **Modos da v0.1:** `continuous` e `max`.
- **Pausa é um estado** (`paused: true | false`), independente do modo.
- `cmd.clock.pause` e `cmd.clock.resume` alternam esse estado; `resume` volta a andar no modo em que se estava.
- `cmd.clock.step` só é aceito com o relógio pausado e avança N ticks.
- `world.session.started` informa o `mode` e se começa `paused`.

## Consequências

- Trocar de modo não tira o mundo da pausa, o que permite depurar o lockstep (`max`) passo a passo.
- A UI mostra o modo e a pausa separadamente.
