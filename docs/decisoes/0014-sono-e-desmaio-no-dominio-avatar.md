# ADR-0014 — Sono e desmaio no domínio `avatar`

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0
**Altera:** `kernel-gestao-do-tempo.md` §12 (`campsverso.agent.sleep.started/ended.v1`)

## Contexto

- O documento de tempo usa `campsverso.agent.sleep.*`, mas `agent` não está na lista de domínios reservados do kernel (`contratos-eventos-v0.md` §14.3).
- `agent` já é um valor de visibilidade e aparece nos assuntos NATS (`campsverso.<worldid>.agent.<agentid>.…`). Usá-lo também como domínio confunde.
- A bíblia (§7, §9) define o desmaio (às 02:00 ou com energia 0), mas não há evento para ele no catálogo.

## Decisão

| Tipo | Visibilidade |
|---|---|
| `campsverso.avatar.sleep.started.v1` | world |
| `campsverso.avatar.sleep.ended.v1` | world |
| `campsverso.avatar.fainted.v1` | world |

Os payloads são propostos no M0, junto com o restante do catálogo.

## Consequências

- O domínio `avatar` reúne tudo o que é do corpo, independente de quem o controla: posse, pedido de decisão, sono e desmaio.
- `agent` fica só como visibilidade; nenhum tipo de evento usa `agent` como domínio.
