# ADR-0012 — Campo `cartridge` do envelope aceita qualquer nome

**Status:** aceita; padrão refinado pela ADR-0031 (`^[a-z][a-z0-9_]*$`) · **Data:** 2026-10-11 · **Marco:** M0
**Altera:** `contratos-eventos-v0.md` §5 (tabela) e §5.2 (schema do envelope)

## Contexto

O envelope define `cartridge` como lista fechada: `farm`, `studio`, `startup`, `economy`. Cada cartucho novo (por exemplo, um mundo de RPG online) obrigaria a mudar o envelope, que é o contrato mais compartilhado de todos. Acrescentar valor a um enum só é compatível se todos os consumidores tratarem valores desconhecidos (§9).

## Decisão

```json
"cartridge": { "type": "string", "pattern": "^[a-z0-9-]+$" }
```

A lista de cartuchos conhecidos vira documentação e configuração, não schema.

## Consequências

- Cartucho novo não muda o envelope.
- Consumidores não podem assumir um conjunto fechado de cartuchos.
- Perde-se a validação de nome digitado errado. O risco é baixo: o kernel publica o nome do cartucho que ele mesmo carregou.
