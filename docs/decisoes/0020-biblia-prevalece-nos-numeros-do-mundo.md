# ADR-0020 — Nos números do mundo, a bíblia prevalece sobre exemplos

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0 (exemplos), M1 (cartucho)
**Esclarece:** `contratos-eventos-v0.md` §8.2; `kernel-gestao-do-tempo.md` §7

## Contexto

A ação `water` dura 6 ticks no exemplo 8.2 dos contratos e no documento de tempo (§7), mas 2 ticks na bíblia (§8).

## Decisão

- Para regras e números do mundo, a fonte é a bíblia do cartucho e, depois, a configuração do cartucho. Valores em exemplos de outros documentos são ilustrativos.
- `water` dura **2 ticks**.
- Os exemplos de `contracts/examples/` usam os números da bíblia.

## Consequências

Divergências futuras desse tipo se resolvem sem nova pergunta: vale a bíblia (ou a configuração do cartucho).
