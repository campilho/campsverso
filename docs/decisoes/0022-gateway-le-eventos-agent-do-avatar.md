# ADR-0022 — O gateway entrega ao humano os eventos `agent` do avatar

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M4/M5
**Esclarece:** `escopo-v0.1.md` §5 (controlador `human` recebe eventos `world`)

## Contexto

O controlador humano recebe o mundo pelo gateway, que assina eventos `world` (e `internal`, no modo operador). Mas `action.rejected` e `avatar.decision_requested` têm visibilidade `agent`. Sem eles, quem joga não sabe por que uma ação foi recusada.

## Decisão

- A credencial NATS do gateway pode assinar `campsverso.<worldid>.agent.camps.>` (o único avatar da v0.1).
- A visão **jogador** mostra rejeições e pedidos de decisão; eventos `internal` aparecem só na visão **operador**.

## Consequências

- Na v0.1, o gateway é um processo privilegiado de operador (local, sem autenticação): lê `world`, `agent` do avatar e `internal`.
- Quando houver visitantes (portal, ou um RPG com vários jogadores), a separação jogador/operador vai precisar de credenciais ou processos distintos, para que a garantia de visibilidade continue vindo das permissões do NATS, e não da UI.
