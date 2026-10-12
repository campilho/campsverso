# Changelog dos contratos

Toda mudança em `contracts/` entra aqui (contratos §9). Dentro de uma versão maior, só entram campos opcionais novos; mudança incompatível vira um tipo novo (`.v2`). A checagem `make compat` confere isso a cada commit.

## Não publicado (M2)

- **Eventos novos** `campsverso.avatar.sleep.started.v2` e `campsverso.avatar.sleep.ended.v2` (ADR-0041, ADR-0042):
  - `cause` passa a ser `voluntary | faint` (o motivo, não o lugar);
  - `bed_id` opcional diz qual cama ou análogo foi usado; sem ele, o avatar dormiu onde estava.
- `sleep.started.v1` e `sleep.ended.v1` ficam marcados com `deprecated`, sem produtor. Nenhum campo mudou.

## v0.1: 2026-10-11

Primeira versão, gerada a partir do [catálogo da v0.1](../docs/arquitetura/catalogo-eventos-v0.1.md) (ADR-0029).

- **Envelope** `envelope.v1`: CloudEvents 1.0 com as extensões do Campsverso.
  - `cartridge` aceita qualquer nome no padrão `^[a-z][a-z0-9_]*$` (ADR-0012, ADR-0031).
  - `id`, `causationid` e `correlationid` são UUIDv7.
- **Tipos comuns** `common/defs.v1`: `uuid7`, `entity_id`, `item_id`, `action_id`, `token`, `position`, `item_stack`, `controller_ref`, `attributes`, `needs`, `params` e outros.
- **38 eventos**: 35 genéricos do modelo de mundo (ADR-0025) e 3 do cartucho `farm`.
- **9 comandos**, todos com visibilidade `observer` (ADR-0013).
- **Exemplos:** um válido por tipo e 10 inválidos, cada um com o código de erro esperado.
- **Domínios:** `contracts/domains.json` lista os domínios reservados do kernel e os de cartucho. Acrescentamos `clock` aos reservados, porque os comandos de relógio são `campsverso.cmd.clock.*` (documento de tempo §13).
- **`asyncapi.yaml`**: AsyncAPI 3.1, gerado a partir dos schemas (ADR-0033).

### Pacotes gerados (sem mudança nos schemas)

- `subject()` em `campsverso_contracts` e `@campsverso/contracts`: a regra do assunto NATS (catálogo §1.1) num lugar só.
