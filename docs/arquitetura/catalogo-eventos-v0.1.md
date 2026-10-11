# Catálogo de eventos e comandos — v0.1

**Status:** aprovado · **Data:** 11/out/2026 (ADR-0029)
**Fontes:** `contratos-eventos-v0.md` (§5, §7, §8, §13, §14), `kernel-gestao-do-tempo.md` (§12, §13), `fazenda-camps-biblia-v0.1.md`, ADRs 0011 a 0030.
**Uso:** especificação do que o M0 transforma em JSON Schema em `contracts/`. Depois do M0, os schemas passam a ser a fonte da verdade e este documento vira o guia de leitura deles.

---

## 0. Decisões que moldam este catálogo

| ADR | Decisão |
|---|---|
| [0025](../decisoes/0025-modelo-de-mundo-do-kernel.md) | O kernel conhece a "física" genérica de um mundo (tempo, espaço, entidades, itens, necessidades, ações, avatares, clima, regras). Cartuchos mudam o mundo só por essas primitivas, e cada mudança vira um **evento genérico**. Evento do cartucho só quando carrega significado próprio. |
| [0026](../decisoes/0026-pausa-e-estado-nao-modo.md) | Modos `continuous` e `max`; a pausa é um estado separado. |
| [0027](../decisoes/0027-avatar-id-nos-eventos-do-kernel.md) | `avatar_id` (o corpo) em tudo o que é do kernel. |
| [0028](../decisoes/0028-percepcao-so-com-instantaneos.md) | Percepção só com instantâneos na v0.1. |
| [0029](../decisoes/0029-catalogo-de-eventos-da-v0-1.md) | Este catálogo, com os itens novos e os removidos. |
| [0030](../decisoes/0030-snake-case-nos-payloads.md) | Campos de payload em `snake_case`; o envelope segue o CloudEvents. |

---

## 1. Convenções

### 1.1 Do tipo ao arquivo, ao `$id` e ao assunto NATS

| Tipo | Arquivo do schema (payload) | `$id` e `dataschema` | Assunto NATS |
|---|---|---|---|
| `campsverso.action.completed.v1` | `contracts/events/action/completed.v1.schema.json` | `contracts://events/action/completed.v1` | `campsverso.<worldid>.world.action.completed.v1` |
| `campsverso.world.clock.phase_changed.v1` | `contracts/events/world/clock.phase_changed.v1.schema.json` | `contracts://events/world/clock.phase_changed.v1` | `campsverso.<worldid>.world.world.clock.phase_changed.v1` |
| `campsverso.action.rejected.v1` (vis. `agent`) | `contracts/events/action/rejected.v1.schema.json` | `contracts://events/action/rejected.v1` | `campsverso.<worldid>.agent.<avatar_id>.action.rejected.v1` |
| `campsverso.cmd.action.propose.v1` | `contracts/commands/action/propose.v1.schema.json` | `contracts://commands/action/propose.v1` | `campsverso.<worldid>.cmd.action.propose.v1` |

**Regra do assunto:** `campsverso.<worldid>.<visibilidade>[.<avatar_id>].<tipo sem o prefixo campsverso.>`. O segmento `<avatar_id>` só existe na visibilidade `agent`, e todo evento `agent` leva `avatar_id` no payload.

O CI confere que tipo, arquivo e `$id` batem.

### 1.2 Visibilidade fixa por tipo

Cada schema declara a visibilidade do seu tipo (`"x-visibility": "internal"`). O validador exige que `envelope.visibility` seja igual à declarada. Assim, um evento da regra oculta publicado por engano como `world` é recusado antes de sair do processo. Comandos declaram `observer` (ADR-0013).

### 1.3 Grafia (ADR-0030)

- Campos de payload em `snake_case` (`applied_tick`, `avatar_id`), conferidos pelo CI.
- Atributos do envelope seguem o CloudEvents (`correlationid`, `worldid`).
- Nada de palavras reservadas como nome de campo (`from`, `to`, `class`): usam-se pares como `previous_value` e `value`.

### 1.4 Identificadores e tipos comuns (`contracts/common/defs.v1.schema.json`)

| Tipo | Formato | Exemplos |
|---|---|---|
| `uuid7` | padrão UUID com versão 7 (vale para `id`, `causationid`, `correlationid`) | `01928f6a-4c1e-7b3a-9f10-2a6c0e8d1a01` |
| `entity_id` | `^[a-z0-9]+(-[a-z0-9]+)*$` | `camps`, `plot-e-03`, `bed`, `chest` |
| `item_id` | `^[a-z0-9]+(_[a-z0-9]+)*$` (conteúdo do cartucho, em português, sem acento) | `moeda`, `semente_rabanete`, `abobora` |
| `action_id` | `^act-[0-9]{6,}$`, contador determinístico do kernel | `act-000981` |
| `position` | `{ x: int ≥ 0, y: int ≥ 0 }`, em tiles | `{ "x": 17, "y": 10 }` |
| `item_stack` | `{ item: item_id, qty: int ≥ 1 }` | `{ "item": "rabanete", "qty": 5 }` |
| `controller_ref` | `{ type: human\|script\|replay\|llm\|mcp\|supervised, id: string }` | `{ "type": "script", "id": "script/farmer-v1" }` |
| `attributes` | objeto com valores escalares (string, número, booleano, nulo); chaves em `snake_case` | `{ "stage": "broto", "watered_today": true }` |

**Idioma dos valores:**
- conteúdo do cartucho em português: itens, culturas, estágios, necessidades, fases do dia;
- estrutura em inglês: tipos, campos, motivos de rejeição, ids de objetos (`plot-…`, como na bíblia), condição do clima (`sun`, `rain`, como em §14.3).

### 1.5 Rigor

- Schemas estritos (`additionalProperties: false`); modelos gerados tolerantes (ADR-0016).
- Valores que são **dados do cartucho** (nome de ação, fase, estágio, necessidade, tipo de entidade, motivo de item) são strings com padrão, não enums: o kernel não conhece a fazenda. Os valores esperados ficam documentados no schema.
- Valores que pertencem à **física do kernel** (modo do relógio, motivo de pedido de decisão, tipo de controlador) são enums.

---

## 2. Envelope (`contracts/envelope/envelope.v1.schema.json`)

É o schema da seção 5.2 dos contratos, com estas mudanças:

- `cartridge`: padrão `^[a-z0-9-]+$` (ADR-0012);
- `id`, `causationid`, `correlationid`: UUIDv7 (tipo `uuid7`), cumprindo a ADR-009 dos contratos;
- `visibility` igual à declarada pelo schema do tipo (1.2), e `observer` em todo comando (ADR-0013).

---

## 3. Catálogo da v0.1

Notação dos payloads (`data`): `campo: tipo`; `?` marca campo opcional.

### 3.1 Tempo (produtor: kernel)

| Tipo | Vis. | Payload | Origem |
|---|---|---|---|
| `campsverso.world.session.started.v1` | world | `cartridge_version: string` · `seed: int` · `tick_seconds: int` · `mode: continuous\|max` · `paused: bool` · `scale: number` · `resumed: bool` (reinício a partir de snapshot) · `map: { id, width, height }` | contratos §7 |
| `campsverso.world.clock.phase_changed.v1` | world | `phase: string` (`amanhecer`, `meio_dia`, `entardecer`, `noite`, `madrugada`) · `day: int` | contratos §7; bíblia §3 |
| `campsverso.world.clock.mode_changed.v1` | world | `previous_mode`, `mode: continuous\|max` · `reason: string` · `by: string` | tempo §12; ADR-0026 |
| `campsverso.world.clock.scale_changed.v1` | world | `previous_scale`, `scale: number > 0` · `reason: operator\|experiment\|budget\|human` · `by: string` | tempo §12 |
| `campsverso.world.clock.paused.v1` | world | `reason: debug\|maintenance\|budget` · `by: string` | tempo §12; ADR-0026 |
| `campsverso.world.clock.resumed.v1` | world | `by: string` | tempo §12; ADR-0026 |
| `campsverso.world.clock.stepped.v1` | world | `ticks: int` · `from_tick: int` · `to_tick: int` | **novo**: sem ele, a UI não sabe que o tempo andou num passo em que nada aconteceu |
| `campsverso.world.clock.jumped.v1` | internal | `from_tick: int` · `to_tick: int` | tempo §12 |

### 3.2 Espaço, entidades, itens e clima (produtor: kernel)

| Tipo | Vis. | Payload | Origem |
|---|---|---|---|
| `campsverso.world.entity.spawned.v1` | world | `entity_id` · `kind: string` · `position?` **ou** `container_id?` · `blocking: bool` · `display_name?: string` · `attributes?` (estado visível inicial) | contratos §7 |
| `campsverso.world.entity.moved.v1` | world | `entity_id` · `action_id` · `origin: position` · `waypoints: [position]` (só esquinas e destino) · `depart_tick: int` · `arrival_tick: int` · `tiles_per_tick: number` | D1 |
| `campsverso.world.entity.move_interrupted.v1` | world | `entity_id` · `action_id` · `position` (posição real) · `reason: cancelled\|blocked\|fainted` | D1 |
| `campsverso.world.entity.state_changed.v1` | world | `entity_id` · `changes: attributes` (só atributos visíveis) · `cause?: string` (ação ou nome do sistema) · `action_id?` | contratos §7; ADR-0025 |
| `campsverso.world.item.created.v1` | world | `item` · `qty` · `container_id` · `reason: string` (`initial`, `harvest`, `buy`, `payment`) · `action_id?` | §14.2 |
| `campsverso.world.item.transferred.v1` | world | `item` · `qty` · `from_container`, `to_container: entity_id` · `reason: string` (`deposit`, `withdraw`, `sell`) · `action_id?` | §14.2 |
| `campsverso.world.item.consumed.v1` | world | `item` · `qty` · `container_id` · `reason: string` (`eat`, `plant`, `buy_payment`, `buyer_collect`) · `action_id?` | §14.2; `buyer_collect` é **novo**: o comprador esvazia a caixa às 22:00 |
| `campsverso.world.weather.changed.v1` | world | `condition: string` (`sun`, `rain`) · `day: int` (dia agrícola de validade, ADR-0018) | §14.3 |

### 3.3 Necessidades (produtor: kernel; assunto `agent.<avatar_id>`)

| Tipo | Vis. | Payload | Origem |
|---|---|---|---|
| `campsverso.world.need.changed.v1` | agent | `avatar_id` · `need: string` (`fome`, `energia`) · `previous_value: number` · `value: number` (0–100) | §14.3 (no máximo 1 por hora simulada por necessidade) |
| `campsverso.world.need.threshold_crossed.v1` | agent | `avatar_id` · `need` · `threshold: number` · `direction: up\|down` · `value: number` | contratos §7 |

### 3.4 Ações (produtor: kernel)

| Tipo | Vis. | Payload | Origem |
|---|---|---|---|
| `campsverso.action.accepted.v1` | world | `action_id` · `avatar_id` · `action: string` · `params: object` · `applied_tick: int` · `duration_ticks: int` (previsto) · `replaces?: action_id` (ação cancelada por esta) | contratos §7, §14.1 |
| `campsverso.action.rejected.v1` | agent | `avatar_id` · `action` · `params` · `reason: string` · `detail?: string` | contratos §7; bíblia §8 |
| `campsverso.action.completed.v1` | world | `action_id` · `avatar_id` · `action` · `params` · `duration_ticks: int` (real) · `observable?: [{ entity_id, property, before, after }]` (resumo legível; o estado vem dos eventos genéricos) | §8.2 |
| `campsverso.action.failed.v1` | world | `action_id` · `avatar_id` · `action` · `reason: string` (`cancelled`, `fainted`, `blocked`, `precondition_lost`) | contratos §7 |
| `campsverso.action.effects_explained.v1` | internal | `action_id` · `rules_applied: [{ rule, version, hidden: bool, multiplier?: number }]` | §8.2; bíblia §10 |

**Motivos de rejeição previstos** (string aberta; o cartucho pode acrescentar):
`not_in_control`, `unknown_action`, `invalid_params`, `busy` (dormindo; `sleep` não se cancela), `unreachable`, `not_passable`, `not_adjacent`, `missing_item`, `insufficient_funds`, `closed`, `not_ripe`, `not_withered`, `plot_occupied`, `no_plant`, `can_empty`, `not_edible`, `too_early_to_sleep`.

**Parâmetros por ação:** validados pelo cartucho, não pelo schema genérico.

| Ação | Parâmetros |
|---|---|
| `move` | `{ target: position }` |
| `plant` | `{ target: plot_id, crop }` |
| `water`, `harvest`, `clear` | `{ target: plot_id }` |
| `refill` | `{ target: well_id }` |
| `eat` | `{ item }` |
| `deposit`, `withdraw`, `sell`, `buy` | `{ item, qty }` |
| `sleep` | `{ target: bed_id }` |
| `wait` | `{ ticks: 1–60 }` |

### 3.5 Avatares e posse (produtor: kernel)

| Tipo | Vis. | Payload | Origem |
|---|---|---|---|
| `campsverso.avatar.possessed.v1` | world | `avatar_id` · `previous_controller?: controller_ref` (ausente na abertura da sessão) · `controller: controller_ref` · `by: string` | §14.1 |
| `campsverso.avatar.released.v1` | world | `avatar_id` · `previous_controller: controller_ref` · `controller: controller_ref` (o padrão do cartucho) · `by: string` | §14.1 |
| `campsverso.avatar.decision_requested.v1` | agent | `avatar_id` · `reason: session_started\|possessed\|action_completed\|action_rejected\|action_interrupted\|phase_changed\|need_threshold\|woke_up` · `controller: controller_ref` (quem deve responder) · `needs: { <nome>: number }` · `position` | §14.1. **Novo:** os dois primeiros motivos, mais `needs` e `position`. As necessidades mudam a cada tick e só o kernel sabe o valor exato no momento do pedido |
| `campsverso.avatar.sleep.started.v1` | world | `avatar_id` · `cause: bed\|faint` · `position` · `wake_at_tick: int` | ADR-0014 |
| `campsverso.avatar.sleep.ended.v1` | world | `avatar_id` · `cause: bed\|faint` · `energy: number` | ADR-0014 |
| `campsverso.avatar.fainted.v1` | world | `avatar_id` · `reason: late_night\|exhausted` · `position` | ADR-0014 |

### 3.6 Regras (produtor: kernel)

| Tipo | Vis. | Payload | Origem |
|---|---|---|---|
| `campsverso.rules.loaded.v1` | internal | `rules: [{ rule, version, hidden: bool, enabled: bool, params: attributes }]` · `source_ref: string` | contratos §7 |
| `campsverso.rules.toggled.v1` | internal | `rule` · `from_version` · `to_version` · `enabled: bool` · `params?: attributes` · `by: string` · `reason: string` · `experiment_id?: string` · `effective_at_tick: int` | §8.3; ADR-0015 |
| `campsverso.rules.effect_applied.v1` | internal | `rule` · `version` · `entity_id` · `property: string` · `base: number` · `applied: number` (ex.: `growth_points` 1,0 → 1,5) | §14.3; bíblia §10 |

### 3.7 Percepção (produtor: serviço de percepção)

| Tipo | Vis. | Payload | Origem |
|---|---|---|---|
| `campsverso.perception.delivered.v1` | agent | `avatar_id` · `kind: snapshot` · `as_of_tick: int` · `view` (abaixo) | §14.4; ADR-0025, ADR-0028 |

Estrutura de `view`, inteiramente genérica (sem nada específico da fazenda):

- `clock: { tick, sim_time, day, phase }`
- `weather: { condition, day }`
- `self: { entity_id, position, needs, asleep: bool, action?: { action_id, action, params, end_tick } }`
- `containers: [{ container_id, items: [item_stack] }]`
- `entities: [{ entity_id, kind, position?, container_id?, attributes }]`

### 3.8 Cartucho `farm` (produtor: kernel, executando código do cartucho)

Só os eventos que carregam significado que os genéricos não carregam (ADR-0025):

| Tipo | Vis. | Payload | Por que existe |
|---|---|---|---|
| `campsverso.farm.crop.matured.v1` | world | `plot_id` · `crop` · `planted_day: int` · `day: int` · `days: int` | "dias até amadurecer" é a evidência observável da regra oculta (bíblia §13), calculada pelo kernel |
| `campsverso.farm.crop.withered.v1` | world | `plot_id` · `crop` · `day: int` · `dry_days: int` | a causa da perda (métrica "plantas murchas") |
| `campsverso.farm.buyer.paid.v1` | world | `container_id` · `items: [{ item, qty, unit_price }]` · `total: int` · `day: int` | o detalhe da venda (preço por item); os eventos de item mostram só as moedas que chegaram |

**Atributos visíveis das entidades da fazenda** (chegam por `world.entity.spawned` e `world.entity.state_changed`):

| Tipo de entidade | Atributos visíveis | Ocultos (nunca saem em `world`) |
|---|---|---|
| `plot` | `crop` (ou nulo), `stage` (`semente`, `broto`, `crescendo`, `madura`, `murcha`), `watered_today` | pontos de crescimento |
| `kiosk` | `open` | — |
| `watering_can` (o regador, guardado no inventário) | `charges`, `capacity` | — |

### 3.9 Operação (produtor: kernel)

| Tipo | Vis. | Payload | Origem |
|---|---|---|---|
| `campsverso.world.snapshot.created.v1` | internal | `snapshot_id: string` · `ref: string` (chave no `BlobStore`) · `last_seq: int` · `sha256: string` · `size_bytes: int` | contratos §7 |
| `campsverso.world.command.rejected.v1` | observer | `command_id: uuid7` · `command_type: string` · `reason: string` · `detail?: string` | **novo**: rejeição de posse, relógio e regras. Ações continuam em `action.rejected` |

### 3.10 Comandos (todos com visibilidade `observer`)

| Tipo | Quem emite na v0.1 | Payload | Origem |
|---|---|---|---|
| `campsverso.cmd.action.propose.v1` | controladores | `avatar_id` · `action` · `params: object` · `intent?: string` · `at_tick?: int` (só do `replay` em modo máximo) | contratos §7; `at_tick` é **novo**: reproduz no tick exato comandos que, no modo contínuo, chegaram sem pedido de decisão |
| `campsverso.cmd.avatar.possess.v1` | operador (UI) | `avatar_id` · `controller: controller_ref` | §14.1 |
| `campsverso.cmd.avatar.release.v1` | operador (UI) | `avatar_id` | §14.1 |
| `campsverso.cmd.clock.set_mode.v1` | operador | `mode: continuous\|max` · `reason?: string` | tempo §13 |
| `campsverso.cmd.clock.set_scale.v1` | operador | `scale: number > 0` · `reason: operator\|experiment\|budget\|human` | tempo §13 |
| `campsverso.cmd.clock.pause.v1` | operador | `reason: debug\|maintenance\|budget` | tempo §13 |
| `campsverso.cmd.clock.resume.v1` | operador | — (objeto vazio) | tempo §13 |
| `campsverso.cmd.clock.step.v1` | operador | `ticks: int` (1–1440) | tempo §13 |
| `campsverso.cmd.rules.toggle.v1` | operador | `rule` · `enabled: bool` · `params?: attributes` · `reason: string` · `experiment_id?: string` | ADR-0015 |

**Total:** 38 eventos (35 genéricos e 3 do cartucho) e 9 comandos, mais o envelope e o arquivo de tipos comuns.

---

## 4. Do catálogo geral, fora da v0.1

Não ganham schema agora. Entram quando a versão que os usa chegar:

- cognição, LLM, memória, social: `cognition.*`, `llm.*`, `memory.*`, `social.*`;
- manutenção e efeitos no mundo real: `maintenance.*`, `bridge.*`, `director.*`, `portal.*`, `effector.*`;
- operação e experimentos: `experiment.*`, `ops.budget.*`, `ops.heartbeat.v1`;
- mais de um avatar e mundos maiores: `world.proximity.entered.v1`, `world.entity.left_stage/entered_stage.v1` (§14.5), `world.entity.despawned.v1`;
- observabilidade de agentes: `cmd.observability.set_trace_level.v1`.

---

## 5. Exemplos inválidos do CI

Cada um precisa ser recusado **pelos dois validadores** (Python `jsonschema` e TS `ajv`):

| # | Exemplo | Protege |
|---|---|---|
| 1 | Envelope sem `seq` | campos obrigatórios |
| 2 | `type` fora do padrão (sem versão, ou com maiúscula) | convenção de nomes |
| 3 | `id` UUIDv4 em vez de v7 | ADR-009 |
| 4 | `rules.effect_applied` publicado com `visibility: world` | **isolamento da regra oculta** (1.2) |
| 5 | Comando com `visibility: agent` | ADR-0013 |
| 6 | Campo não declarado no payload | ADR-0016 |
| 7 | `cartridge` com maiúscula | ADR-0012 |
| 8 | `item.created` com `qty: 0` | regras de payload |
| 9 | Tipo sem schema declarado em `contracts/` | "nunca publicar evento sem schema" |

Além disso, qualquer arquivo inválido colocado em `examples/valid/` quebra o `make check` (critério do M0).

---

## 6. Lacunas para o M1 (não bloqueiam o M0)

1. **Limiares dos estágios `broto` e `crescendo`.** A bíblia só define quando a planta fica `madura`. Proposta: `broto` com ≥ 1 ponto, `crescendo` com ≥ 50% dos pontos necessários. A sequência visível vai diferir entre os grupos (perto do rio, o rabanete passa de `semente` a `crescendo` em um dia). É um efeito observável da regra, não um vazamento.
2. **Ids dos objetos** (`bed`, `table`, `chest`, `sell-box`, `well`, `kiosk`) **e do regador**, que agora é uma entidade.
3. **Unidade interna das necessidades:** inteiros em 1/120 de ponto por tick. Assim fome (+3/h acordado, +1/h dormindo) e energia (+12,5/h) ficam exatas, sem erro de arredondamento de ponto flutuante, o que protege o determinismo.
4. **Ordem dos sistemas que rodam no mesmo tick** (ADR-0018, item 4).
5. **Limiares de necessidade que geram `decision_requested`** (fome 70 e 80; energia 10 e 0?).
