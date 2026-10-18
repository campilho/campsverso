# Changelog dos contratos

Toda mudança em `contracts/` entra aqui (contratos §9). Dentro de uma versão maior, só entram campos opcionais novos; mudança incompatível vira um tipo novo (`.v2`). A checagem `make compat` confere isso a cada commit.

## Não publicado (M8)

- **O mundo pronto para o LLM** (ADR-0056), só com campos opcionais e um tipo novo:
  - `common/defs.v1` ganha o terreno (`terrain_rows`, `terrain_legend`, `terrain_tile`, `terrain_window`), a configuração da percepção (`perception_config`, com `radius`) e as peças de uma entrega de percepção reaproveitáveis (`seen_clock`, `seen_weather`, `seen_self`, `seen_action`, `seen_container`, `seen_entity`, `seen_event`, `decision_request`);
  - `world.session.started.v1`: o `map` ganha `rows` e `legend` (o terreno inteiro, uma vez) e o evento ganha `perception` (o raio declarado pelo cartucho; `null` é o mapa inteiro);
  - `perception.delivered.v1`: a `view` ganha `map`, o terreno ao alcance do avatar, recortado ao raio;
  - **evento novo `campsverso.perception.updated.v1`**, o delta: `since_tick`, `as_of_tick`, `decision`, `clock`, `self` inteiro, `weather` se mudou, `containers` e `entities` que mudaram (inteiros), `gone` e `events` (o que aconteceu desde a entrega anterior). É um tipo próprio porque acrescentar `delta` ao enum `kind` da foto seria incompatível (`make compat`);
  - o `ObserverState` ganha `session.map.rows`, `session.map.legend` e `session.perception`.
- As peças `seen_*` duplicam a forma da `view` da foto, que continua inline por compatibilidade; uma `delivered.v2`, quando vier, passa a referenciá-las.

## Não publicado (M2)

- **Eventos novos** `campsverso.avatar.sleep.started.v2` e `campsverso.avatar.sleep.ended.v2` (ADR-0041, ADR-0042):
  - `cause` passa a ser `voluntary | faint` (o motivo, não o lugar);
  - `bed_id` opcional diz qual cama ou análogo foi usado; sem ele, o avatar dormiu onde estava.
- `sleep.started.v1` e `sleep.ended.v1` ficam marcados com `deprecated`, sem produtor. Nenhum campo mudou.

## Não publicado (M3)

- `campsverso.perception.delivered.v1` ganha o campo opcional `decision` (`reason` e `controller`): o pedido que a foto responde. Com ele, o controlador age só com este evento (ADR-0048).

## Não publicado (M4)

- **Mensagens do WebSocket** entre gateway e UI, em `contracts/realtime/` (ADR-0050): `welcome`, `update`, `command` e `reply`, com o tipo `campsverso.realtime.<nome>.v1` no campo `type`.
  - O estado (`ObserverState`) é genérico, sem nada de desenho, e não carrega `null`.
  - As ferramentas validam as mensagens nos dois validadores, com os códigos `message_schema` e `unknown_message`, e geram os tipos Python e TypeScript.
- O `asyncapi.yaml` ganha o servidor `gateway` (`ws`), o canal `Realtime` e a indicação do servidor em cada canal NATS.

## Não publicado (M5)

- **Mensagem nova `campsverso.live.kernel.v1`** em `contracts/live/` (ADR-0051): o pulso do kernel, com o tick de verdade e o relógio. Vai para `campsverso.<mundo>.live.kernel`, fora de todos os streams.
- **`ObserverState` ganha `pulse`,** um campo opcional e compatível: o tick do último pulso e se o kernel está vivo.
- **As ferramentas tratam `realtime` e `live` como mensagens sem envelope.** O AsyncAPI ganha o canal do pulso.

## Não publicado (M7)

- **Catálogo de métricas** (ADR-0054), só com campos opcionais:
  - `common/defs.v1` ganha `metric`: `count` de um tipo de evento (com `where` e `by`), `max_need` e `item`;
  - `world.session.started.v1` ganha `metrics`, o catálogo declarado pelo cartucho;
  - o `ObserverState` ganha `session.metrics` e `metrics`, os valores dos últimos 8 dias simulados.

## Não publicado (M6)

- **Política de interrupção das ações** (ADR-0052), só com campos opcionais:
  - `common/defs.v1` ganha `interrupt`: `never`, `cancel` ou `partial`;
  - `action.accepted.v1` ganha `interrupt`, a política da ação aceita;
  - `action.failed.v1` ganha `elapsed_ticks`, quanto a ação durou antes de parar;
  - a ação em andamento ganha `applied_tick` e `interrupt` na foto da percepção (`perception.delivered.v1`) e no `ObserverState`;
  - o `ObserverState` ganha `sleep`: o início do sono, o tick previsto para acordar e a cama, se houver, por avatar.
- Exemplo inválido novo: uma política fora das três.

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
