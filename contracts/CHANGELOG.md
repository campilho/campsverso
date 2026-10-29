# Changelog dos contratos

Toda mudança em `contracts/` entra aqui (contratos §9). Dentro de uma versão maior, só entram campos opcionais novos; mudança incompatível vira um tipo novo (`.v2`). A checagem `make compat` confere isso a cada commit.

## Não publicado (M21)

- **O conselheiro** (ADR-0074): `llm.call.completed.v1` ganha o campo opcional `advisor` (o modelo que o provedor consultou dentro da chamada, quantas vezes, os tokens e o custo dele, na tarifa dele). O `cost_usd` continua sendo o total da chamada. Só uma chamada com a ferramenta do conselheiro o publica.
- **A OpenRouter** (ADR-0074): `llm.call.completed.v1` ganha dois campos opcionais, para a ficha de cada corrida: `response_model` (o id do modelo que a resposta disse ser) e `served_by` (quem atendeu de fato, quando o provedor é um roteador: o provedor que a OpenRouter usou). O `cost_usd` passa a ser, quando o provedor diz o que cobrou (a OpenRouter), o que ele disse; sem isso, continua vindo da tabela de preços. Exemplo novo: `campsverso.llm.call.completed.v1--openrouter.json`.
- **O custo na tela** (ADR-0074): o estado da tela (`realtime/welcome.v1`, `state`) ganha o campo opcional `costs`: por controlador, o gasto do último dia com chamadas, o total, as chamadas cobradas e a parte do conselheiro; e o último aviso da guarda de orçamento. Projetado dos `llm.call.completed` cobrados e dos `ops.budget.*`; só a visão do operador o recebe.

## Não publicado (M20)

- **A presença do avatar** (ADR-0072), dois tipos novos de visibilidade `world`, produtor `kernel`:
  - `campsverso.avatar.entered.v1`: o avatar entrou no mundo (`avatar_id`, `position`, `reason`), como o ajudante que chega para trabalhar; passa a receber pedidos de decisão;
  - `campsverso.avatar.left.v1`: o avatar saiu do mundo (`avatar_id`, `position?`, `reason`); some do mapa, a ação em andamento é cancelada, as necessidades param, e ele não recebe pedidos até entrar de novo.
  - Só um mundo com avatares declarados fora dele (os ajudantes da Morada do Sol) os publica.
- **O contrato de trabalho** (ADR-0072), três tipos novos no domínio de biblioteca `economy`, de visibilidade `world`, produtor `kernel`, publicados pelo cartucho que liga os ajudantes:
  - `campsverso.economy.labor.hired.v1`: alguém contratou um ajudante no quadro (`helper`, `employer`, `days`, `wage`, `total`, `first_day`, `day`), pago adiantado;
  - `campsverso.economy.labor.dismissed.v1`: dispensado antes do fim (`helper`, `employer`, `days_left`, `day`); os dias pagos não voltam;
  - `campsverso.economy.labor.ended.v1`: o contrato terminou (`helper`, `employer`, `day`).

## Não publicado (M19)

- **O experimento da noite** (ADR-0070): `memory.reflected.v1` ganha os campos opcionais `experiment` (a hipótese, o teste e a previsão que a reflexão propôs para o dia seguinte) e `experiment_result` (`cumpriu`, `falhou` ou `inconclusivo`: o veredito sobre o experimento da noite anterior). Só a mente que usa experimentos (a da Morada do Sol) os publica.
- **A madura que murcha sem colher** (ADR-0062; achado no M19): `farm.crop.withered.v1` aceita `dry_days: 0`, a planta madura que murchou porque ninguém a colheu em 3 dias na Boa Vista e na Morada do Sol. O código publicava 0 desde o M13, e o leitor das métricas contava as murchas da madura por ele, mas o mínimo do schema era 1: a primeira madura esquecida derrubava o barramento que valida. Relaxar o mínimo é compatível (`make compat`).

## M18 (publicado em 25/out, antes de uma versão)

- **A métrica que soma** (ADR-0069): `metric` ganha o campo opcional `field`: num `count`, o campo numérico do evento que se soma no lugar de contar (as moedas recebidas por canal).
- **O clima com previsão** (ADR-0069): `world.weather.changed.v1` ganha `forecast` (o tempo de um dia que ainda não chegou), e as condições novas `storm` e `drought` cabem no `condition`, que já é texto aberto; a foto (`perception.delivered.v1`, `view.weather`) e o delta (`seen_weather`) ganham `tomorrow`, o tempo de amanhã quando a previsão já saiu; e um tipo novo, `campsverso.farm.crop.knocked_down.v1` (`world`, produtor `kernel`, publicado pelo cartucho farm): a planta madura que a tempestade derrubou (`plot_id`, `crop`, `day`).
- **As encomendas** (ADR-0069): o domínio de biblioteca `economy` (`domains.json`, chave `libraries`), com quatro tipos novos de visibilidade `world`, produtor `kernel`, publicados pelo cartucho que usa a `libs/economy`: `campsverso.economy.order.posted.v1` (um pedido apareceu no quadro: `order_id`, `board_id`, `client`, `item`, `qty`, `reward`, `posted_day`, `due_day`), `campsverso.economy.order.accepted.v1` (`order_id`, `taker`, `day`), `campsverso.economy.order.delivered.v1` (entregue e pago na hora: `order_id`, `client`, `item`, `qty`, `reward`, `taker`, `day`) e `campsverso.economy.order.expired.v1` (o prazo passou: `order_id`, `client`, `item`, `qty`, `due_day`, `taker?`, `day`).

## M16 e M17 (publicados em 24/out, antes de uma versão)

- **A primitiva de remover entidade** (ADR-0067), um tipo novo:
  - `campsverso.world.entity.despawned.v1` (`world`, produtor `kernel`): uma entidade removida em tempo de execução, como o canteiro vazio que volta a ser grama (`entity_id`, `kind`, `position?`, `reason`, `action_id?`). Avatares, contêineres com itens ou com entidades dentro, e o alvo de uma ação em andamento não se removem.
- **O ano acelerado com estações** (ADR-0067), um tipo novo e campos opcionais:
  - `campsverso.world.clock.season_changed.v1` (`world`, produtor `kernel`): a estação mudou na virada do dia (`day`, `date`, `season`, `previous_season?`);
  - `world.clock.phase_changed.v1` ganha `date` (a data do calendário do ano acelerado, à parte do `simtime`) e `season`;
  - o relógio da foto (`perception.delivered.v1`, `view.clock`), o `seen_clock` do delta e o `ObserverState` ganham `date` e `season`.
  - Só um mundo cujo cartucho declara um ano (`WorldBuilder.configure_year`) os publica; as fazendas 1 e 2 continuam sem.
- **O que saiu da vista** (ADR-0067): `perception.updated.v1` ganha `out_of_view`, as entidades que saíram do raio e continuam no mundo; `gone` passa a ser só o que deixou de existir à vista do avatar.
- **A noite e a luz** (ADR-0068): `perception_config` ganha `by_phase` (o raio por fase do dia) e `lights` (itens que, no inventário, garantem um raio mínimo).
- **Os rótulos da linha do tempo** (ADR-0068): `common/defs.v1` ganha `event_label` (`event`, `where?`, `text` com campos entre chaves), e `world.session.started.v1` e o `session` do `realtime.welcome.v1` ganham `labels`, os rótulos que o cartucho declara.
- **Os menus do humano** (ADR-0068): `affordance_param` ganha `entities` (as escolhas incluem as entidades guardadas na fonte, pelo id: as ferramentas no inventário ou no baú), e o `on` de uma `affordance` passa a aceitar um tipo de terreno (`grass`), que põe a ação no menu de um tile vazio com o tile em `target` como `{x, y}`. O `move` aceita `near: {x, y}`, o tile livre mais perto ao lado de um tile (os parâmetros das ações são livres no contrato).
- **Os marcos** (ADR-0067): `common/defs.v1` `perception_config` ganha `landmarks`, os tipos de entidade que todo avatar enxerga além do raio (as construções fixas: a casa, o poço, o quiosque).
- **A planta comida** (ADR-0067): `campsverso.farm.crop.eaten.v1` (`world`, produtor `kernel`, publicado pelo cartucho farm): a planta madura amanheceu comida (`plot_id`, `crop`, `day`, `by`). O efeito é visível; a regra que escolhe o canteiro (a R-002 da Morada do Sol), não.

## v0.2.0: 2026-10-21

A possessão: o mundo pronto para o LLM, a porta de modelo, o controlador LLM, a memória e a Fazenda Boa Vista. São 11 eventos novos, e o resto são campos opcionais; nenhuma mudança incompatível (`make compat`).

### M13

- **As primitivas da Fazenda Boa Vista** (ADR-0062), um tipo novo e campos opcionais:
  - `campsverso.world.entity.stored.v1` (`world`, produtor `kernel`): uma entidade guardada noutro contêiner, como a ferramenta que vai do avatar para o baú (`entity_id`, `from_container?`, `to_container`, `action_id?`); ela deixa de ter posição no mapa;
  - `campsverso.world.entity.spawned.v1` ganha `action_id`, opcional: a ação que criou a entidade em tempo de execução (o canteiro cavado);
  - `campsverso.world.item.created.v1`, `campsverso.world.item.transferred.v1` e `campsverso.world.item.consumed.v1` ganham `expires_day`, o dia em que o lote vence pela validade nominal do item; com validade, o kernel publica um evento por lote, e o estrago na virada do dia é um `consumed` com motivo `spoiled`;
  - `common/defs.v1`: `item_stack` ganha `expires_in_days`, os dias até o lote mais antigo vencer (negativo quando passou da data e ainda não estragou: o contêiner conserva); vale na foto da percepção e nos contêineres vistos do delta;
  - peso e capacidade, e a hora até quando um modificador de necessidade vale, chegam como atributos visíveis das entidades (`weight`, `capacity`, o rótulo do modificador), sem contrato novo; a entidade criada em tempo de execução chega por `world.entity.spawned`, como no início da sessão.

### M11

- **Memória baseline** (ADR-0060): cinco tipos novos no domínio `memory`, todos `observer`, produtor `controller` (a mente), e nenhum tipo mudado:
  - `common/defs.v1` ganha `belief_id`, `confidence` (0 a 1), `belief_source` (`observation`, ou `told` com `by`) e `belief_evidence`;
  - `campsverso.memory.noted.v1` (uma anotação do agente), `campsverso.memory.reflected.v1` (o resumo e o plano de uma reflexão, com as contagens de crenças e o hash do pedido), `campsverso.memory.belief.formed.v1`, `campsverso.memory.belief.updated.v1` (`confidence: {before, after}`) e `campsverso.memory.belief.retracted.v1`, no formato do §8.4 do documento de contratos;
  - o `ObserverState` do `realtime` ganha `memory`, opcional: o caderno de cada avatar (crenças, anotações, último resumo e plano).

### M10

- **O controlador LLM** (ADR-0059), só com campos opcionais e nenhum tipo novo:
  - `campsverso.action.accepted.v1` ganha `intent`, a intenção declarada na proposta (`cmd.action.propose`), copiada pelo kernel; é o que a tela e a linha do tempo mostram ("llm/camps: colher o canteiro leste");
  - o `ObserverState` do `realtime` ganha `intent` na ação corrente de cada avatar (`actions.<avatar>.intent`).

### M9

- **Porta de modelo e orçamento** (ADR-0058): quatro tipos novos, todos com visibilidade `observer`, e nenhum tipo mudado:
  - `common/defs.v1` ganha `llm_usage` (tokens de entrada, saída, lidos do cache e gravados no cache);
  - `campsverso.llm.call.completed.v1` e `campsverso.llm.call.failed.v1` (produtor `controller`, publicados pelo decorador da porta): quem chamou, `purpose`, `provider`, `model`, `prompt_sha256` (nunca o prompt), `latency_ms`; a concluída leva `usage`, `cost_usd`, `charged` (falso quando veio da fita), `stop_reason` e `effort`; a falha leva `error`, `message` e `retryable`;
  - `campsverso.ops.budget.threshold_reached.v1` e `campsverso.ops.budget.exceeded.v1` (produtor novo `budget`, a guarda de orçamento): `scope` (`day` ou `total`), `day`, `spent_usd`, `limit_usd`, e `threshold_pct` (50, 80, 100) ou `paused`. Eram `internal` no documento de contratos; o orçamento é assunto do operador.

### M8

- **O mundo pronto para o LLM** (ADR-0056), só com campos opcionais e um tipo novo:
  - `common/defs.v1` ganha o terreno (`terrain_rows`, `terrain_legend`, `terrain_tile`, `terrain_window`), a configuração da percepção (`perception_config`, com `radius`) e as peças de uma entrega de percepção reaproveitáveis (`seen_clock`, `seen_weather`, `seen_self`, `seen_action`, `seen_container`, `seen_entity`, `seen_event`, `decision_request`);
  - `world.session.started.v1`: o `map` ganha `rows` e `legend` (o terreno inteiro, uma vez) e o evento ganha `perception` (o raio declarado pelo cartucho; `null` é o mapa inteiro);
  - `perception.delivered.v1`: a `view` ganha `map`, o terreno ao alcance do avatar, recortado ao raio;
  - **evento novo `campsverso.perception.updated.v1`**, o delta: `since_tick`, `as_of_tick`, `decision`, `clock`, `self` inteiro, `weather` se mudou, `containers` e `entities` que mudaram (inteiros), `gone` e `events` (o que aconteceu desde a entrega anterior). É um tipo próprio porque acrescentar `delta` ao enum `kind` da foto seria incompatível (`make compat`);
  - o `ObserverState` ganha `session.map.rows`, `session.map.legend` e `session.perception`; como o estado não carrega `null`, o raio nulo (o mapa inteiro) aparece como ausência de `perception`.
- As peças `seen_*` duplicam a forma da `view` da foto, que continua inline por compatibilidade; uma `delivered.v2`, quando vier, passa a referenciá-las.

## v0.1.0: 2026-10-12

A Fazenda do Camps. As mudanças de cada marco sobre a primeira versão dos contratos (M0).

### M7

- **Catálogo de métricas** (ADR-0054), só com campos opcionais:
  - `common/defs.v1` ganha `metric`: `count` de um tipo de evento (com `where` e `by`), `max_need` e `item`;
  - `world.session.started.v1` ganha `metrics`, o catálogo declarado pelo cartucho;
  - o `ObserverState` ganha `session.metrics` e `metrics`, os valores dos últimos 8 dias simulados.

### M6

- **Política de interrupção das ações** (ADR-0052), só com campos opcionais:
  - `common/defs.v1` ganha `interrupt`: `never`, `cancel` ou `partial`;
  - `action.accepted.v1` ganha `interrupt`, a política da ação aceita;
  - `action.failed.v1` ganha `elapsed_ticks`, quanto a ação durou antes de parar;
  - a ação em andamento ganha `applied_tick` e `interrupt` na foto da percepção (`perception.delivered.v1`) e no `ObserverState`;
  - o `ObserverState` ganha `sleep`: o início do sono, o tick previsto para acordar e a cama, se houver, por avatar.
- Exemplo inválido novo: uma política fora das três.

### M5

- **Mensagem nova `campsverso.live.kernel.v1`** em `contracts/live/` (ADR-0051): o pulso do kernel, com o tick de verdade e o relógio. Vai para `campsverso.<mundo>.live.kernel`, fora de todos os streams.
- **`ObserverState` ganha `pulse`,** um campo opcional e compatível: o tick do último pulso e se o kernel está vivo.
- **As ferramentas tratam `realtime` e `live` como mensagens sem envelope.** O AsyncAPI ganha o canal do pulso.

### M4

- **Mensagens do WebSocket** entre gateway e UI, em `contracts/realtime/` (ADR-0050): `welcome`, `update`, `command` e `reply`, com o tipo `campsverso.realtime.<nome>.v1` no campo `type`.
  - O estado (`ObserverState`) é genérico, sem nada de desenho, e não carrega `null`.
  - As ferramentas validam as mensagens nos dois validadores, com os códigos `message_schema` e `unknown_message`, e geram os tipos Python e TypeScript.
- O `asyncapi.yaml` ganha o servidor `gateway` (`ws`), o canal `Realtime` e a indicação do servidor em cada canal NATS.

### M3

- `campsverso.perception.delivered.v1` ganha o campo opcional `decision` (`reason` e `controller`): o pedido que a foto responde. Com ele, o controlador age só com este evento (ADR-0048).

### M2

- **Eventos novos** `campsverso.avatar.sleep.started.v2` e `campsverso.avatar.sleep.ended.v2` (ADR-0041, ADR-0042):
  - `cause` passa a ser `voluntary | faint` (o motivo, não o lugar);
  - `bed_id` opcional diz qual cama ou análogo foi usado; sem ele, o avatar dormiu onde estava.
- `sleep.started.v1` e `sleep.ended.v1` ficam marcados com `deprecated`, sem produtor. Nenhum campo mudou.

### M0: 2026-10-11

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

#### Pacotes gerados (sem mudança nos schemas)

- `subject()` em `campsverso_contracts` e `@campsverso/contracts`: a regra do assunto NATS (catálogo §1.1) num lugar só.
