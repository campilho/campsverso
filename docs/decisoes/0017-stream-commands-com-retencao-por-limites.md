# ADR-0017 — Stream `COMMANDS` com retenção por limites

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M2
**Altera:** `contratos-eventos-v0.md` §6 (tabela de streams) e D3 ("COMMANDS até consumo")

## Contexto

O stream `COMMANDS` foi definido como fila de trabalho (*work-queue*). Nesse modo, o JetStream entrega cada mensagem a um único consumidor e não aceita consumidores com filtros que se sobreponham. O arquivador, que deve assinar todos os streams, não conseguiria ler os comandos, e os rejeitados sumiriam do registro histórico.

## Decisão

- `COMMANDS` usa retenção **por limites** (`max_age` e `max_bytes` em `config/env/local.yaml`; valores iniciais definidos no M2).
- O kernel consome com um consumidor durável e confirmação explícita (*ack*), deduplicando pelo `id` (princípio 5 dos contratos).
- O arquivador tem o seu próprio consumidor durável.

**Alternativa considerada:** retenção por interesse, em que a mensagem fica até todos os consumidores confirmarem. Ficaria mais perto do "até consumo" original, mas comandos publicados antes de existir um consumidor seriam descartados, e não sobraria nada para depurar.

## Consequências

- Todos os comandos, inclusive os rejeitados, ficam auditáveis no arquivo JSONL.
- O kernel precisa ser idempotente por `id`, o que já estava previsto.
