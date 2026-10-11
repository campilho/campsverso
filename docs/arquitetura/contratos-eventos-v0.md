# Arquitetura orientada a eventos e contratos — v0

**Status:** rascunho para revisão · **Data:** 07/out/2026 · **Revisão:** 10/out/2026 (decisões D1–D7, namespace `campsverso`, acréscimos da v0.1 na seção 14)
**Escopo:** infraestrutura de eventos, padrão de contrato, catálogo inicial de eventos e comandos, e o mapa de portas/adaptadores da plataforma (vilarejo remoto na Patagônia, estúdio, startup, simulação econômica).
**Uso:** base para a spec e para o Claude Code gerar o pacote `contracts/`.

---

## 1. Princípios (inegociáveis)

1. **Módulos só se conhecem por contrato.** Nenhum módulo importa código de outro nem acessa o banco de outro. A comunicação é feita por eventos (fatos) e comandos (pedidos), sempre via barramento.
2. **Todo recurso externo passa por uma porta.** LLM, embeddings, memória, flags, TTS, git, sandbox, storage, segredos, telemetria. Pode começar com um único adaptador (por exemplo, OpenRouter), mas a porta existe desde o dia zero.
3. **O kernel é o único escritor da verdade do mundo.** Agentes *propõem* ações por comando; só o kernel emite fatos sobre o mundo. Isso garante determinismo e replay.
4. **Eventos são imutáveis e versionados.** Dentro de uma versão maior só se adicionam campos opcionais. Mudança incompatível gera um novo tipo `...v2`.
5. **Entrega pelo menos uma vez + consumidores idempotentes.** Não perseguimos "exatamente uma vez"; deduplicamos pelo `id` do evento.
6. **Visibilidade é arquitetura, não convenção.** O que um agente pode ler é garantido por permissões de assunto no barramento, não pelo prompt. Regras ocultas não podem vazar nem por bug.
7. **Tudo que acontece é reproduzível.** Event log arquivado + snapshots + seeds de RNG = replay idêntico.

---

## 2. Duas coisas diferentes que costumam ser misturadas

| Conceito | Função | Requisito | Nesta arquitetura |
|---|---|---|---|
| **Log de verdade** | Registro durável e ordenado do que aconteceu | Ordem, durabilidade, replay, retenção longa | Kernel grava na sua própria store (SQLite → Postgres) com número de sequência e publica no barramento via *outbox* |
| **Barramento** | Entregar mensagens entre processos | Baixa latência, fan-out, grupos de consumidores, ACL | NATS JetStream (dia zero) |
| **Arquivo histórico** | Análise, replay público, métricas | Barato, consultável | JSONL diário em disco → S3 + Athena |

Dentro do kernel, o loop de ticks continua **em processo** (sem barramento), porque o lockstep precisa de microssegundos. O barramento conecta módulos, não funções.

**Padrão outbox:** o kernel grava o evento e a sequência na sua store na mesma transação, e um publicador lê a outbox e publica no barramento. Isso evita a inconsistência de "gravou mas não publicou" (dual write).

---

## 3. Decisões de arquitetura (ADRs resumidos)

| ADR | Decisão | Alternativa considerada | Motivo |
|---|---|---|---|
| 001 | Envelope **CloudEvents 1.0** | Envelope próprio | Padrão CNCF, suportado nativamente pelo EventBridge e por SDKs em Python/TS; facilita a migração para AWS |
| 002 | Payload em **JSON + JSON Schema 2020-12** | Avro, Protobuf | Legível, nativo no browser, volume baixo; codegen para Pydantic e TS. Revisitar se o mini-Brasil exigir alto volume |
| 003 | Documentação de canais em **AsyncAPI 3.0** | Só README | "OpenAPI dos eventos"; gera docs e ajuda o Claude Code a respeitar contratos |
| 004 | Barramento dia zero: **NATS JetStream** | Redis Streams, Redpanda | Ver seção 4 |
| 005 | Kernel é escritor único da verdade do mundo | Cada módulo escreve estado | Determinismo e replay |
| 006 | Pelo menos uma vez + idempotência por `id` | Exatamente uma vez | Simplicidade |
| 007 | Visibilidade por permissão de assunto | Filtro no código | Segurança do experimento de regras ocultas |
| 008 | Portas e adaptadores para todo recurso externo | Chamada direta | Troca de provedor = configuração |
| 009 | IDs **UUIDv7** | UUIDv4, ULID | Ordenáveis por tempo, padrão RFC 9562 |
| 010 | Schemas versionados em git (`contracts/`) como registro | Schema registry gerenciado | Dia zero sem infra; migrar para EventBridge Schema Registry ou Glue se fizer sentido |

---

## 4. Infraestrutura do barramento — opções avaliadas

| Opção | Dia zero (Mac) | Na AWS | Prós | Contras |
|---|---|---|---|---|
| Barramento em processo (asyncio) | trivial | — | Zero infra | Viola o princípio 1: módulos não ficam separados |
| Tabela append-only + polling / Postgres LISTEN/NOTIFY | SQLite/Postgres | RDS | Simples, durável, consultável com SQL | Fan-out e grupos de consumidores feitos à mão; não escala bem |
| **Redis Streams** | 1 container | ElastiCache / MemoryDB (durável) | Leve, grupos de consumidores, replay por ID, caminho gerenciado na AWS | Retenção limitada pela memória; ACL por chave menos expressiva; sem wildcards de assunto |
| **NATS JetStream** | 1 binário (~20 MB) | Auto-hospedado em ECS/EC2 (sem serviço gerenciado AWS; Synadia Cloud é a opção gerenciada) | Assuntos hierárquicos com wildcards, request-reply nativo, streams duráveis com replay por sequência ou tempo, **ACL por assunto**, KV e Object Store embutidos, consumo mínimo de recursos | Sem serviço gerenciado nativo na AWS; menos comum no mundo corporativo que Kafka |
| **Redpanda** (API Kafka) | 1 binário, sem JVM | MSK (Kafka gerenciado) ou Redpanda Cloud | Mesmo modelo mental do Kafka, padrão de mercado; ecossistema Kafka (Connect, Schema Registry) | Mais pesado que NATS; MSK tem custo fixo relevante mesmo ocioso |
| Kafka (Apache) | pesado localmente | MSK / MSK Serverless | Padrão corporativo | Custo e operação desproporcionais para este volume |
| **EventBridge** (+ SQS) | só via LocalStack | nativo | Roteamento por regras, **archive & replay**, schema registry, cobrança por evento, integrações AWS | Latência de centenas de ms; não serve para comunicação fina entre módulos em tempo real |
| **Kinesis Data Streams** | só via LocalStack | nativo (on-demand) | Log ordenado por shard, retenção longa, replay | Cobrança por stream-hora mesmo ocioso; API menos ergonômica |
| KurrentDB (EventStoreDB) | 1 container | Kurrent Cloud | Event sourcing nativo, projeções | Mais uma infra de nicho; não substitui o barramento |

### Recomendação

- **Dia zero e fases locais:** **NATS JetStream** como barramento + **store do kernel com outbox** como verdade + **arquivador JSONL**. É a menor infraestrutura que mantém os módulos totalmente separados, com replay e ACL.
- **AWS, caminho 1 (mais barato e com o mesmo código):** NATS em ECS Fargate ou numa EC2 pequena + S3/Athena para o arquivo.
- **AWS, caminho 2 (mais "nativo" e didático para aprender os serviços da AWS):** trocar o adaptador do barramento por **EventBridge** (integrações, regras, archive/replay, ponte com o pipeline do podcast) + **SQS** para filas de trabalho. Kinesis só se o volume do mini-Brasil exigir.
- **Se a familiaridade com Kafka pesar**: Redpanda como alternativa B no dia zero. A porta `EventBus` torna a troca uma questão de adaptador.

> Valores de custo na AWS variam por região e modelo de cobrança; checar na calculadora antes da fase de migração.

---

## 5. Envelope (CloudEvents 1.0 + extensões)

Atributos obrigatórios do CloudEvents: `specversion`, `id`, `source`, `type`. As extensões seguem a regra do padrão: só letras minúsculas e dígitos.

| Atributo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `specversion` | string | sim | `"1.0"` |
| `id` | UUIDv7 | sim | Identificador único; chave de idempotência |
| `source` | URI-ref | sim | Módulo produtor, ex. `/kernel/farm-01`, `/cognition/tomas` |
| `type` | string | sim | `campsverso.<dominio>.<nome>.v<major>` |
| `time` | RFC 3339 | sim | Tempo real (relógio de parede) da emissão |
| `subject` | string | não | Entidade principal, ex. `agent/tomas`, `plot/3` |
| `datacontenttype` | string | sim | `application/json` |
| `dataschema` | URI | sim | Schema do payload, ex. `contracts://events/action/completed.v1` |
| `worldid` | string | sim | Instância do mundo, ex. `farm-01`, `studio-01` |
| `cartridge` | string | sim | `farm`, `studio`, `startup`, `economy` |
| `tick` | integer | não | Tick do kernel (eventos do mundo) |
| `simtime` | RFC 3339 | não | Data e hora dentro do mundo, ex. `2026-03-14T07:30:00-03:00` |
| `seq` | integer | sim | Sequência monotônica **por `source`** (detecção de lacunas e ordenação) |
| `actor` | string | não | Quem causou: `agent/tomas`, `human/visitor-123`, `system/director` |
| `controller` | enum | não | Tipo de controlador que emitiu o comando: `human` · `script` · `llm` · `replay` · `mcp` · `supervised` (seção 14.1) |
| `controllerid` | string | não | Instância do controlador, ex. `script/farmer-v1`, `human/camps-browser` |
| `causationid` | UUIDv7 | não | `id` do evento ou comando que causou este |
| `correlationid` | UUIDv7 | não | Agrupa uma cadeia (ex. uma decisão inteira) |
| `provenance` | enum | sim | `simulated` · `real` · `staged` |
| `visibility` | enum | sim | `world` · `agent` · `observer` · `internal` (ver 5.1) |
| `traceparent` | string | não | W3C Trace Context (extensão oficial de tracing do CloudEvents) |
| `data` | object | sim | Payload validado pelo `dataschema` |

### 5.1 Visibilidade

| Valor | Quem lê | Exemplos |
|---|---|---|
| `world` | Kernel, filtro de percepção, UI, arquivo. Agentes recebem só **depois** do filtro de percepção | entidade se moveu, colheita concluída |
| `agent` | Apenas o agente destinatário (+ observadores) | percepção entregue, resultado de recall de memória |
| `observer` | Humanos/UI/arquivo; **agentes nunca** | pensamento, plano, custo de LLM |
| `internal` | Sistema e experimentos; **não sai no broadcast público** | regra oculta ligada/desligada, efeitos de regras aplicadas |

### 5.2 Schema do envelope

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "contracts://envelope.v1",
  "type": "object",
  "required": ["specversion", "id", "source", "type", "time", "datacontenttype",
               "dataschema", "worldid", "cartridge", "seq", "provenance", "visibility", "data"],
  "properties": {
    "specversion":   { "const": "1.0" },
    "id":            { "type": "string", "format": "uuid" },
    "source":        { "type": "string", "minLength": 1 },
    "type":          { "type": "string", "pattern": "^campsverso\\.[a-z0-9_]+(\\.[a-z0-9_]+)+\\.v[0-9]+$" },
    "time":          { "type": "string", "format": "date-time" },
    "subject":       { "type": "string" },
    "datacontenttype": { "const": "application/json" },
    "dataschema":    { "type": "string" },
    "worldid":       { "type": "string", "pattern": "^[a-z0-9-]+$" },
    "cartridge":     { "enum": ["farm", "studio", "startup", "economy"] },
    "tick":          { "type": "integer", "minimum": 0 },
    "simtime":       { "type": "string", "format": "date-time" },
    "seq":           { "type": "integer", "minimum": 0 },
    "actor":         { "type": "string" },
    "controller":    { "enum": ["human", "script", "llm", "replay", "mcp", "supervised"] },
    "controllerid":  { "type": "string" },
    "causationid":   { "type": "string", "format": "uuid" },
    "correlationid": { "type": "string", "format": "uuid" },
    "provenance":    { "enum": ["simulated", "real", "staged"] },
    "visibility":    { "enum": ["world", "agent", "observer", "internal"] },
    "traceparent":   { "type": "string" },
    "data":          { "type": "object" }
  },
  "additionalProperties": false
}
```

---

## 6. Convenções de nomes

**Tipo de evento:** `campsverso.<dominio>.<nome_no_passado>.v<major>`, ex. `campsverso.action.completed.v1`.
**Tipo de comando:** `campsverso.cmd.<dominio>.<verbo_no_imperativo>.v<major>`, ex. `campsverso.cmd.action.propose.v1`.
Fatos no passado, pedidos no imperativo: a distinção aparece no nome.

**Assuntos NATS:**

```
campsverso.<worldid>.<visibility>.<dominio>.<nome>.v<major>
campsverso.<worldid>.agent.<agentid>.<dominio>.<nome>.v<major>      # visibilidade "agent"
campsverso.<worldid>.cmd.<dominio>.<verbo>.v<major>                 # comandos
```

Exemplos:
- `campsverso.farm-01.world.action.completed.v1`
- `campsverso.farm-01.agent.tomas.perception.delivered.v1`
- `campsverso.farm-01.observer.cognition.thought.v1`
- `campsverso.farm-01.internal.rules.toggled.v1`
- `campsverso.farm-01.cmd.action.propose.v1`

**Permissões (exemplo para o processo do agente Tomás):**
- publicar: `campsverso.farm-01.cmd.action.propose.v1`, `campsverso.farm-01.observer.cognition.>`, `campsverso.farm-01.cmd.memory.>`
- assinar: `campsverso.farm-01.agent.tomas.>`
- **negado:** `campsverso.farm-01.internal.>`, `campsverso.farm-01.world.>` (ele só vê o mundo pela percepção filtrada)

**Streams JetStream (dia zero):**

| Stream | Assuntos | Retenção | Uso |
|---|---|---|---|
| `WORLD` | `campsverso.*.world.>` | limites (ex. 30 dias) | fatos do mundo |
| `AGENT` | `campsverso.*.agent.>` | limites | percepções e respostas individuais |
| `OBSERVER` | `campsverso.*.observer.>` | limites | pensamentos, custos, UI |
| `INTERNAL` | `campsverso.*.internal.>` | limites | regras, experimentos, ops |
| `COMMANDS` | `campsverso.*.cmd.>` | work-queue | pedidos consumidos uma vez pelo responsável |

O **arquivador** assina todos os streams e grava JSONL diário (→ S3/Athena na AWS).

---

## 7. Catálogo v0 (eventos e comandos)

### Mundo e ações (produtor: kernel)

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.world.session.started.v1` | world | Mundo carregado (cartucho, seed, versão das regras) |
| `campsverso.world.clock.phase_changed.v1` | world | Amanheceu, anoiteceu, abriu ou fechou o expediente |
| `campsverso.world.entity.spawned.v1` | world | Entidade criada (planta, item, personagem) |
| `campsverso.world.entity.moved.v1` | world | Movimento como **trajeto** (origem, caminho, duração), não tile a tile; a UI interpola |
| `campsverso.world.entity.state_changed.v1` | world | Mudança de componente relevante (umidade, maturidade, estoque) |
| `campsverso.world.need.threshold_crossed.v1` | agent | Fome, energia ou humor cruzou limiar (gatilho cognitivo) |
| `campsverso.cmd.action.propose.v1` | — | **Comando** do agente: ação proposta |
| `campsverso.action.accepted.v1` | world | Validada e agendada |
| `campsverso.action.rejected.v1` | agent | Recusada, com motivo (sinal de aprendizado) |
| `campsverso.action.completed.v1` | world | Concluída com efeitos observáveis |
| `campsverso.action.failed.v1` | world | Iniciada, mas falhou durante a execução |
| `campsverso.action.effects_explained.v1` | internal | Quais regras (incluindo ocultas) contribuíram para o resultado |
| `campsverso.world.snapshot.created.v1` | internal | Snapshot persistido (ref no blob store) |

### Regras e experimentos

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.rules.loaded.v1` | internal | Conjunto de regras carregado (versões) |
| `campsverso.rules.toggled.v1` | internal | Regra ligada/desligada/parametrizada (com autor e motivo) |
| `campsverso.experiment.started.v1` / `.ended.v1` | internal | Ablation, seed, hipótese |

### Cognição (produtor: runtime do agente)

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.perception.delivered.v1` | agent | Observação filtrada entregue ao agente |
| `campsverso.cognition.woke.v1` | observer | Nível acordado (reflexo/tático/estratégico) e gatilho |
| `campsverso.cognition.thought.v1` | observer | Texto de "pensamento" para a UI |
| `campsverso.cognition.plan.created.v1` | observer | Plano do dia ou de curto prazo |
| `campsverso.cognition.decision.made.v1` | observer | Decisão tomada, ligada ao comando emitido |
| `campsverso.llm.call.completed.v1` | observer | Tokens, cache, custo, latência, modelo, provedor |

### Memória (produtor: serviço de memória)

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.cmd.memory.recall.v1` | — | **Comando** (request-reply): buscar memórias |
| `campsverso.memory.recorded.v1` | observer | Memória episódica registrada (com importância) |
| `campsverso.memory.belief.formed.v1` | observer | Nova crença |
| `campsverso.memory.belief.updated.v1` | observer | Confiança mudou (com evidência e fonte) |
| `campsverso.memory.belief.retracted.v1` | observer | Crença abandonada |
| `campsverso.memory.skill.learned.v1` / `.used.v1` | observer | Skill procedural criada e usada (com resultado) |

### Social

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.cmd.social.speak.v1` | — | **Comando**: falar com alguém |
| `campsverso.social.utterance.spoken.v1` | world | Fala audível para quem estiver no raio |
| `campsverso.social.conversation.started.v1` / `.ended.v1` | world | Início e fim de conversa |
| `campsverso.social.relation.changed.v1` | observer | Afinidade ou confiança entre agentes mudou |

### Sono e manutenção

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.maintenance.window.opened.v1` / `.closed.v1` | world | Todos dormem / acordam |
| `campsverso.maintenance.consolidation.completed.v1` | observer | Reflexão noturna concluída (via batch ou não) |
| `campsverso.maintenance.deploy.applied.v1` | internal | Código ou regras novos aplicados na janela |
| `campsverso.maintenance.digest.published.v1` | observer | Digest matinal para você |

### Ponte com a realidade, Diretor e portal

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.bridge.external.ingested.v1` | world | Evento real entrou (ex. pipeline do podcast) — `provenance: real` |
| `campsverso.cmd.effector.invoke.v1` | — | **Comando**: efeito real (git, TTS, publicar) |
| `campsverso.effector.completed.v1` / `.denied.v1` | observer | Resultado ou bloqueio por política/budget |
| `campsverso.director.scene.scheduled.v1` / `.started.v1` | world | Cena encenada — `provenance: staged` |
| `campsverso.portal.session.started.v1` | observer | Visitante entrou |
| `campsverso.cmd.portal.message.v1` | — | **Comando**: visitante fala com personagem |

### Operação

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.ops.budget.threshold_reached.v1` | internal | 50/80/100% do teto |
| `campsverso.ops.budget.exceeded.v1` | internal | Mundo pausado por custo |
| `campsverso.ops.heartbeat.v1` | internal | Saúde de cada módulo (watchdog) |

---

## 8. Payloads de exemplo

### 8.1 Comando — agente propõe ação

```json
{
  "specversion": "1.0",
  "id": "01928f6a-4c1e-7b3a-9f10-2a6c0e8d1a01",
  "source": "/cognition/tomas",
  "type": "campsverso.cmd.action.propose.v1",
  "time": "2026-10-10T14:03:11Z",
  "subject": "agent/tomas",
  "datacontenttype": "application/json",
  "dataschema": "contracts://commands/action/propose.v1",
  "worldid": "farm-01",
  "cartridge": "farm",
  "tick": 18240,
  "simtime": "2026-03-14T07:30:00-03:00",
  "seq": 412,
  "actor": "agent/tomas",
  "correlationid": "01928f6a-4b00-7c11-8e00-55aa00000001",
  "provenance": "simulated",
  "visibility": "agent",
  "data": {
    "agentid": "tomas",
    "action": "water",
    "params": { "target": "plot-3" },
    "intent": "O canteiro 3 parecia seco ontem à tarde.",
    "decisionlevel": "tactical"
  }
}
```

### 8.2 Fato — ação concluída (público) e explicação (interna)

```json
{
  "type": "campsverso.action.completed.v1",
  "source": "/kernel/farm-01",
  "visibility": "world",
  "causationid": "01928f6a-4c1e-7b3a-9f10-2a6c0e8d1a01",
  "data": {
    "actionid": "act-000981",
    "agentid": "tomas",
    "action": "water",
    "params": { "target": "plot-3" },
    "durationticks": 6,
    "observable": [
      { "entity": "plot-3", "property": "soil.moisture", "from": "seco", "to": "úmido" }
    ]
  }
}
```

```json
{
  "type": "campsverso.action.effects_explained.v1",
  "source": "/kernel/farm-01",
  "visibility": "internal",
  "data": {
    "actionid": "act-000981",
    "rulesapplied": [
      { "rule": "water_basic", "version": "1.0.0", "hidden": false },
      { "rule": "river_proximity_bonus", "version": "1.2.0", "hidden": true, "multiplier": 1.4 }
    ]
  }
}
```

(Envelope abreviado nos exemplos a partir daqui; todos os campos obrigatórios da seção 5 se aplicam.)

### 8.3 Regra oculta alternada

```json
{
  "type": "campsverso.rules.toggled.v1",
  "source": "/ops/rules-admin",
  "visibility": "internal",
  "data": {
    "rule": "river_proximity_bonus",
    "fromversion": "1.2.0",
    "toversion": "1.2.0",
    "enabled": false,
    "by": "human/camps",
    "reason": "Experimento E-003: medir tempo até desaprender.",
    "experimentid": "E-003",
    "effectiveattick": 21000
  }
}
```

### 8.4 Crença atualizada

```json
{
  "type": "campsverso.memory.belief.updated.v1",
  "source": "/memory/farm-01",
  "visibility": "observer",
  "data": {
    "agentid": "tomas",
    "beliefid": "bel-0042",
    "statement": "Canteiros perto do rio rendem mais.",
    "confidence": { "from": 0.55, "to": 0.72 },
    "evidence": { "for": 7, "against": 1 },
    "source": { "kind": "observation" },
    "reason": "Colheita do canteiro 2 (junto ao rio) superou a dos canteiros 5 e 6."
  }
}
```

Quando a crença vem de outro personagem: `"source": { "kind": "told", "by": "agent/esteban" }`.

### 8.5 Chamada de LLM concluída (custo)

```json
{
  "type": "campsverso.llm.call.completed.v1",
  "source": "/cognition/tomas",
  "visibility": "observer",
  "data": {
    "agentid": "tomas",
    "decisionlevel": "tactical",
    "purpose": "next_action",
    "provider": "openrouter",
    "model": "anthropic/claude-haiku-4.5",
    "tokens": { "input": 1040, "cachedinput": 2100, "output": 286 },
    "costusd": 0.00265,
    "latencyms": 1840,
    "status": "ok",
    "promptsha256": "9c1f…"
  }
}
```

### 8.6 Evento real do pipeline do podcast

```json
{
  "type": "campsverso.bridge.external.ingested.v1",
  "source": "/bridge/podcast-pipeline",
  "provenance": "real",
  "visibility": "world",
  "data": {
    "system": "podcast-pipeline",
    "externaltype": "tts.generated",
    "occurredat": "2026-10-08T06:14:52-03:00",
    "payload": { "episodeid": "2026-10-08", "durationsec": 412, "attempt": 2 },
    "mapping": { "actor": "studio/locutor", "scene": "recording" }
  }
}
```

---

## 9. Evolução de schema

- **Compatível (mesma major):** adicionar campo opcional, adicionar valor a um enum *apenas se* os consumidores tratarem valores desconhecidos.
- **Incompatível (nova major `v2`):** remover ou renomear campo, mudar tipo, tornar obrigatório, mudar semântica.
- Na troca de major, o produtor publica **v1 e v2 em paralelo** por um período, e os consumidores migram.
- **Leitor tolerante:** consumidores ignoram campos desconhecidos.
- Todo schema tem `examples/` validados no CI.
- `contracts/CHANGELOG.md` registra cada mudança.

---

## 10. Estrutura do repositório de contratos

```
contracts/
  envelope/
    envelope.v1.schema.json
  events/
    world/      session.started.v1.schema.json, entity.moved.v1.schema.json, ...
    action/     completed.v1.schema.json, rejected.v1.schema.json, ...
    cognition/  thought.v1.schema.json, ...
    memory/     belief.updated.v1.schema.json, ...
    ...
  commands/
    action/propose.v1.schema.json
    memory/recall.v1.schema.json
    ...
  examples/            # um JSON válido por tipo
  asyncapi.yaml        # canais NATS, mensagens, permissões
  CHANGELOG.md
packages/
  contracts-py/        # gerado: modelos Pydantic v2 (datamodel-code-generator)
  contracts-ts/        # gerado: tipos TS (json-schema-to-typescript ou quicktype)
```

**CI mínimo:**
1. Validar todos os schemas (meta-schema 2020-12).
2. Validar `examples/` contra os schemas (Python `jsonschema` e `ajv` em TS).
3. Regerar os pacotes e falhar se houver diff não commitado.
4. Checar incompatibilidade contra a versão anterior (diff de schema).
5. Testes de contrato por consumidor: cada módulo declara os tipos que consome e roda contra os `examples/`.

---

## 11. Módulos como processos independentes

| Módulo | Consome | Produz | Pode cair sem derrubar os outros? |
|---|---|---|---|
| Kernel (por mundo) | `cmd.action.*`, `cmd.social.speak` | `world.*`, `action.*`, `internal.*` | Não (é a verdade), mas os outros aguardam e retomam |
| Filtro de percepção | `world.*` | `agent.<id>.perception.*` | Sim (agentes ficam "cegos" temporariamente) |
| Runtime do agente (1 por personagem) | `agent.<id>.>` | `cmd.*`, `observer.cognition.*`, `llm.*` | Sim (no lockstep, o kernel usa a ação reflexa por timeout) |
| Serviço de memória | `cmd.memory.*`, `perception.*` | `memory.*` | Sim (recall retorna vazio, degradado) |
| Orquestrador de sono | `world.clock.*` | `maintenance.*` | Sim |
| Diretor | `bridge.*`, `world.clock.*` | `director.*` | Sim |
| Ponte / efetores | `cmd.effector.*` | `bridge.*`, `effector.*` | Sim |
| Gateway de UI | `world.*`, `observer.*` | — (WebSocket para o browser) | Sim |
| Portal humano | WebSocket do visitante | `cmd.portal.*` | Sim |
| Arquivador | tudo | JSONL / S3 | Sim (o JetStream retém até ele voltar) |
| Guarda de orçamento | `llm.call.completed` | `ops.budget.*` | Sim, mas sem ele o mundo pausa por segurança |

**Lockstep (fazenda):** o kernel emite um gatilho cognitivo e aguarda o comando correlacionado até um prazo; sem resposta, executa a ação reflexa padrão e registra `cognition.timeout`. Assim, nenhum módulo bloqueia o mundo indefinidamente.

---

## 12. Portas e adaptadores

| Porta | Responsabilidade | Adaptador dia zero | Adaptador AWS | Outros possíveis |
|---|---|---|---|---|
| `EventBus` | publicar, assinar, request-reply | NATS JetStream | NATS em ECS / EventBridge + SQS | Redis Streams, Redpanda |
| `EventArchive` | gravar e ler histórico | JSONL em disco | S3 + Athena | Parquet + DuckDB local |
| `WorldStore` | estado + outbox do kernel | SQLite | RDS Postgres | — |
| `BlobStore` | snapshots, áudios, assets | disco local | S3 | — |
| `ModelPort` | completions, tool use, cache, batch | **OpenRouter** | Bedrock Converse | Anthropic direto, Ollama, LiteLLM |
| `EmbeddingPort` | vetores | sentence-transformers / Ollama | Titan Embeddings | OpenRouter |
| `MemoryPort` | registrar, recall, refletir, crenças | própria (SQLite + sqlite-vec) | RDS pgvector / AgentCore Memory | Hindsight |
| `RulesPort` | avaliar regras | registry Python | idem | ZEN Engine |
| `FlagPort` | regras ocultas, parâmetros | YAML versionado no git | AWS AppConfig | Flipt, OpenFeature |
| `EffectorPort` | TTS, git, publicação | ElevenLabs, git local, script | idem + Lambda | — |
| `SandboxPort` | executar código de agentes | Docker | AgentCore Code Interpreter / Fargate | E2B, Daytona |
| `SecretsPort` | chaves e tokens | `.env` / Keychain | Secrets Manager | — |
| `TelemetryPort` | traces, métricas | OpenTelemetry → Langfuse | OTel → CloudWatch/X-Ray + Langfuse | Phoenix, Opik |
| `ClockPort` | tempo real, lockstep, roteiro | relógio do sistema | idem | — |
| `RealtimeGateway` | WebSocket para a UI | FastAPI WS | API Gateway WebSocket | — |
| `IdentityPort` | visitantes do portal | nenhum (local) | Cognito | Clerk |

**Regra:** nenhum módulo importa SDK de provedor fora do seu adaptador. Um teste de arquitetura no CI (ex. `import-linter` em Python, `dependency-cruiser` em TS) quebra o build se isso acontecer.

### 12.1 Exemplo de porta: `ModelPort`

Contrato mínimo, independente de provedor:

- `complete(request) -> response` — mensagens, ferramentas, `max_tokens`, temperatura, marcadores de cache.
- `submit_batch(requests) -> batch_id` e `collect_batch(batch_id) -> responses` — **opcional por adaptador**: OpenRouter não tem; Anthropic direto e Bedrock têm. O orquestrador de sono pergunta `capabilities()` e escolhe.
- `capabilities() -> {tool_use, prompt_cache, batch, vision, max_context}`.
- Toda chamada emite `campsverso.llm.call.completed.v1` (o adaptador não decide isso; um decorador da porta faz).

A configuração por personagem vive no cartucho:

```yaml
characters:
  tomas:
    reflex: rules
    tactical:  { port: model, provider: openrouter, model: anthropic/claude-haiku-4.5 }
    strategic: { port: model, provider: openrouter, model: anthropic/claude-sonnet-5.5 }
    budget_usd_per_simday: 0.60
```

---

## 13. Decisões da primeira passada (10/out/2026)

### D1 — Movimento: um evento por trajeto
- O **kernel** calcula o caminho (pathfinding é autoritativo, nunca da UI) e publica `entity.moved` com os **pontos de inflexão** do trajeto (só as esquinas, não cada tile), o tick de partida e a velocidade.
- A UI apenas **interpola** entre os pontos; não recalcula caminho nem conhece obstáculos.
- O filtro de percepção calcula a posição em qualquer tick a partir do trajeto (conta simples), sem eventos intermediários.
- **Obstáculo surgindo no meio do caminho** (outro personagem, porta fechada): o kernel emite `campsverso.world.entity.move_interrupted.v1` com a posição real no momento e, se o agente ou o reflexo decidir seguir, um novo `entity.moved` com o desvio.
- **Encontros** ("Tomás passou ao lado de Esteban") são detectados pelo kernel cruzando trajetos e emitidos como evento próprio (`campsverso.world.proximity.entered.v1`), porque disparam percepção e conversa.

### D2 — Pensamento em dois níveis, como log normal e log de debug
- **`summary` (padrão):** uma frase curta para a UI e o replay. É gerada **na mesma chamada** do LLM, como um campo da resposta estruturada (sem chamada extra).
- **`full` (debug):** prompt, resposta completa e raciocínio, ligado por **flag por personagem e com prazo** (ex. "Tomás em full por 2 dias simulados"); desliga sozinho para não esquecer ligado.
- O `full` vai para um assunto `internal` com retenção curta e **nunca** para o replay público.
- Detalhe de custo: o raciocínio já foi pago quando o modelo o gerou; o que a flag controla é o **armazenamento e a exposição**, não o custo do LLM. Raciocínio estendido (thinking) é outro parâmetro, configurado no `ModelPort` por nível cognitivo.
- **Reuso como contexto:** pensamentos brutos **nunca** voltam crus para um novo turno de LLM (ficariam caros em todas as rodadas futuras). O que retorna como contexto é a memória consolidada no sono (episódios com importância, crenças, skills), compacta e recuperada sob demanda. O `full` é material de investigação humana, não de contexto do agente.
- Eventos: `campsverso.cognition.thought.v1` ganha o campo `detail: summary | full`; novo comando `campsverso.cmd.observability.set_trace_level.v1` com `agentid`, `level` e `until`.

### D3 — Retenção configurável por stream
- Correção técnica: o JetStream grava em **disco** por padrão (pode usar memória, mas não é o indicado aqui). O limite real é espaço em disco, não RAM.
- Cada stream recebe `max_age` e `max_bytes` no arquivo de configuração do ambiente (`env/local.yaml`, `env/aws.yaml`). Um Mac mini com disco grande ou um volume maior na AWS = só mudar a configuração.
- Ponto inicial sugerido: `WORLD` e `OBSERVER` 30 dias; `AGENT` 14 dias; `INTERNAL` 90 dias (experimentos); `COMMANDS` até consumo; `full` traces 7 dias.
- O **arquivo** (JSONL → S3) é a memória longa; o JetStream é só a janela quente.
- **Desempenho em disco:** não é um gargalo. O JetStream escreve sequencialmente (append) e o sistema operacional mantém os dados recentes no cache de página em RAM, então leituras recentes são servidas da memória. A ordem de grandeza suportada é de dezenas a centenas de milhares de mensagens por segundo numa máquina comum; a fazenda gera dezenas por segundo no pico.
- **Fila em memória existe** e fica disponível sem infraestrutura nova: (a) o **NATS Core** (pub/sub sem persistência, puramente em memória); (b) streams JetStream com `storage: memory`; (c) filas em processo (asyncio). O loop de ticks do kernel já é em processo. Só usaríamos (a) ou (b) para tráfego efêmero de alta frequência, que hoje não existe.
- **Corte:** além de `max_age`/`max_bytes`, o arquivador fecha um JSONL por dia simulado e por dia real, o que permite apagar ou mover para armazenamento frio por data.

### D4 — Um NATS por mundo principal; forks fora do barramento
- Mundos principais: um servidor NATS cada (no início, um só).
- Forks não são mundos: são sandboxes minimalistas dentro do mundo principal (simulação dentro da simulação). **Não entram no dia 1.**
- **Forks (oráculo e crença) não usam o NATS**: rodam em processo, em modo máximo, com um barramento em memória que implementa a mesma porta `EventBus`. Isso evita subir um NATS para cada "e se" e mantém o fork fisicamente isolado do mundo vivo.
- Se um dia houver vários mundos principais na mesma máquina, a alternativa é um NATS com **contas** (accounts) isoladas por mundo; a porta não muda.

### D5 — Replay público sem custo
- Nova camada de audiência, ortogonal à visibilidade: **`public`** é uma *allowlist* de tipos de evento por cartucho (ex. movimento, ações, falas, pensamento `summary`, fases do dia).
- Custo, tokens e traces ficam no painel privado e nos posts (agregados), não no site.
- Implementação: o publicador do replay filtra pela allowlist; nada de campo novo no envelope por enquanto.
- A allowlist deve mudar bastante com a evolução do projeto; fica versionada no cartucho.

### D6 — Namespace: `campsverso`
- Tipos: `campsverso.<dominio>.<nome>.v<major>` (ex. `campsverso.action.completed.v1`).
- Comandos: `campsverso.cmd.<dominio>.<verbo>.v<major>`.
- Assuntos NATS: `campsverso.<worldid>.<visibility>....`
- Os documentos e o regex do envelope já foram atualizados.

### D7 — Consciência da simulação: o modelo do ator
- **Todos os personagens sempre sabem que são IA.** A diferença está no papel que interpretam, definido no cartucho e no cartão de identidade.
- **Estúdio:** transparente. Os agentes têm nomes e funções (jornalista, editor, locutor), mas se apresentam como IA quando perguntados.
- **Vilarejo remoto (futuro alternativo):** **modelo do ator**. O LLM sabe que interpreta um personagem de uma história, como um ator num filme, e permanece no papel: diante de um visitante, Tomás se comporta como Tomás e nega ser um robô.
- **O humano sempre sabe**: o portal avisa, ao entrar, que todos os personagens são IAs interpretando papéis.
- **Saída do personagem (fora de cena):** o personagem sai do papel e responde honestamente se o visitante pedir isso de forma explícita e sincera (por um botão "fora do personagem" no portal ou um comando claro), ou se a conversa indicar sofrimento real, confusão sobre o que é real ou risco. A ficção protege a experiência, não engana a pessoa.
- **Fase 1:** sem visitantes humanos; a política existe no contrato, mas só é exercitada quando o portal entrar.
- Configuração no cartucho: `awareness: transparent | actor` e `out_of_character: { trigger: [button, explicit_request], safety_break: true }`.
- Evento novo: `campsverso.portal.out_of_character.v1` (observer) quando um personagem sai do papel, com motivo.

## 14. Acréscimos para a v0.1 (Fazenda do Camps)

### 14.1 Controladores e posse

O avatar é um corpo; quem decide é um **controlador** plugável. O kernel trata todos igualmente: mesmo catálogo de ações, mesmas regras, mesmo custo de tempo.

| Controlador | v0.1 | Descrição |
|---|---|---|
| `human` | sim | pessoa pela UI (clique para mover, menu de ações) |
| `script` | sim | lógica determinística (fazendeiro-script; futuro nível reflexo e o robô mech) |
| `replay` | sim | reemite comandos gravados no tick de aplicação original |
| `llm` | v0.2 | runtime cognitivo |
| `mcp` | futuro | cliente MCP externo (Claude Code, Kiro) jogando via ferramentas |
| `supervised` | futuro | LLM propõe, humano aprova |

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.cmd.avatar.possess.v1` | — | **Comando**: `avatarid`, `controller`, `controllerid` |
| `campsverso.cmd.avatar.release.v1` | — | **Comando**: devolve o avatar ao controlador padrão do cartucho |
| `campsverso.avatar.possessed.v1` | world | posse assumida (anterior e novo controlador) |
| `campsverso.avatar.released.v1` | world | posse liberada |
| `campsverso.avatar.decision_requested.v1` | agent | o avatar está ocioso; motivo (`action_completed`, `action_rejected`, `action_interrupted`, `phase_changed`, `need_threshold`, `woke_up`); o controlador responde com `cmd.action.propose` usando o mesmo `correlationid` |

Regras:
- Um controlador por avatar. Comandos de quem não tem a posse → `action.rejected` com motivo `not_in_control`.
- O kernel registra em `action.accepted` o campo `appliedtick`; o controlador `replay` usa esse tick para reproduzir a execução exatamente.
- No modo máximo (lockstep), o kernel aguarda a resposta a cada `decision_requested`; só permitido com `script` ou `replay`.

### 14.2 Itens e contêineres

Itens (inclusive moedas) vivem em contêineres (inventário do avatar, baú, caixa de vendas). A troca de dados entre personagens em cartuchos futuros (artefatos do estúdio) usa a mesma primitiva.

| Tipo | Vis. | Descrição |
|---|---|---|
| `campsverso.world.item.created.v1` | world | item surgiu (colheita, compra, pagamento): `item`, `qty`, `container`, `reason` |
| `campsverso.world.item.transferred.v1` | world | `item`, `qty`, `from`, `to`, `reason` (`deposit`, `withdraw`, `sell`) |
| `campsverso.world.item.consumed.v1` | world | `item`, `qty`, `container`, `reason` (`eat`, `plant`, `buy_payment`) |

### 14.3 Clima e eventos próprios do cartucho

- Domínios do kernel são reservados (`world`, `action`, `avatar`, `perception`, `cognition`, `memory`, `social`, `rules`, `experiment`, `maintenance`, `bridge`, `director`, `portal`, `llm`, `ops`).
- Eventos específicos de um cartucho usam o **nome do cartucho como domínio**: `campsverso.farm.crop.planted.v1`, `.stage_changed.v1`, `.matured.v1`, `.withered.v1`; `campsverso.farm.plot.watered.v1`; `campsverso.farm.kiosk.opened.v1` / `.closed.v1`; `campsverso.farm.buyer.paid.v1`.
- Clima é genérico: `campsverso.world.weather.changed.v1` (world) com `condition` (`sun`, `rain`) e o dia de validade.
- Necessidades: `campsverso.world.need.threshold_crossed.v1` (já previsto) e `campsverso.world.need.changed.v1` (agent), emitido no máximo uma vez por hora simulada por necessidade, para não inundar o barramento.
- O crescimento afetado pela regra oculta gera `campsverso.rules.effect_applied.v1` (internal) com `rule`, `entity`, `tick` e o efeito numérico.

### 14.4 Percepção na v0.1

- `campsverso.perception.delivered.v1` (agent) leva um **instantâneo** do que o avatar percebe a cada `decision_requested`, e **deltas** entre instantâneos.
- Conteúdo e restrições definidos na bíblia da fazenda, seção 12. Pontos de crescimento e regras ocultas nunca aparecem.

### 14.5 Reservado para versões futuras (não implementar na v0.1)

- **Fora de cena (presença):** `campsverso.world.entity.left_stage.v1` / `.entered_stage.v1` — entidade existe, mas não está no mapa (agentes do estúdio indo para casa, visitante desconectado, personagem que partiu).
- **Artefatos com conteúdo** (estúdio): itens com `payload` referenciando o `BlobStore`.

## 15. Questões ainda em aberto

Do contrato (nenhuma bloqueante): valores iniciais de retenção podem ser ajustados após uma semana de uso real.

Do tempo (ver `kernel-gestao-do-tempo.md`, seção 15):
1. Valores iniciais do teto de pensar por nível cognitivo e do prazo real.
2. Fator do ritmo `híbrido` do estúdio.
3. O que muda num agente que "acorda sonolento".
4. Horário e visibilidade da janela de manutenção global.
