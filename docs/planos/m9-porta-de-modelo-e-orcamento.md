# Plano do M9 — Porta de modelo e orçamento

**Status:** aprovado em 18/out/2026 (ADR-0058). Segundo marco da v0.2 (`v0.2-macro.md`). Nenhum controlador LLM entra aqui (é o M10): o M9 constrói a porta por onde ele vai falar com o modelo, o registro de cada chamada, a guarda de orçamento e a gravação das respostas para testar sem gastar.

**Pronto quando (macro):** uma chamada real e uma gravada passam pelo mesmo contrato; estourar o teto pausa o mundo. Em testes: a chamada da fumaça (`make llm-smoke`) e a mesma chamada reproduzida da fita publicam um `llm.call.completed.v1` válido, a segunda com `charged: false`; e, no pipeline em memória, chamadas que estouram o teto fazem a guarda publicar `ops.budget.exceeded.v1` e `cmd.clock.pause` com `reason: budget`, e o kernel para.

## O que o levantamento mostrou

- **O desenho de origem já existe.** O documento de contratos (§8.5 e §12.1) previa a `ModelPort` com `complete`, `capabilities` e, opcionalmente, lote; "toda chamada emite `llm.call.completed.v1`, e quem emite é um decorador da porta, não o adaptador"; e a guarda de orçamento como um módulo que lê `llm.call.completed` e publica `ops.budget.*`. Os domínios `llm` e `ops` estão reservados em `domains.json`, e `cmd.clock.pause` já aceita `reason: budget`.
- **O custo cabe no teto de US$ 0,60 por dia simulado** que o documento usa como exemplo. Com os números do M8 (37 mil tokens de percepção por dia com deltas, uns 100 pedidos de decisão por dia, 150 tokens de resposta por decisão e um prompt de sistema de uns 2 mil tokens por chamada), um dia simulado custa na ordem de **US$ 0,01 a 0,03 no Claude Haiku 5.5**, **US$ 0,26 a 0,62 no Claude Sonnet 5.5** e **US$ 0,49 a 1,25 no Claude Opus 5.5**, o valor menor com o prompt de sistema em cache. Preços de tabela em 18/out: Haiku 5.5 US$ 0,10 / 0,50 por milhão de tokens (entrada / saída), Sonnet 5.5 US$ 2 / 10, Opus 5.5 US$ 4 / 20; leituras de cache a US$ 0,20 por milhão no Sonnet e no Opus. São estimativas: o `make llm-smoke` mede.
- **O SDK oficial em Python está na versão 1.15**, pura (roda no 3.14), sobre `httpx2`. Ele faz retentativas (429 e 5xx) e tem tipos de erro próprios; o adaptador não reimplementa nada disso.
- **Três regras da API de agora que mudam o desenho da porta:** nos modelos atuais o raciocínio é adaptativo e sempre ligado (controla-se a profundidade por `effort`, não por orçamento de tokens de raciocínio); o Sonnet 5.5 e o Opus 5.5 recusam `tool_choice` forçado (a porta usa `auto` com `strict: true` e instrução no prompt); e uma resposta pode terminar com `stop_reason: refusal`, que a porta repassa em vez de esconder.
- **A contagem de tokens tem endpoint próprio** (`count_tokens`), sem cobrança de tokens: serve para calibrar o fator 3,5 do `make percepcao` do M8.
- **Segredos:** o `.env` já fica fora do git (chmod 600) e o honcho o lê para os processos; o SDK também aceita um perfil do `ant auth login`. A chave nunca passa por mim nem por um evento: o evento leva o hash do pedido, nunca o prompt.

## 1. A porta e o adaptador (decisões 1 a 3)

- **`ModelPort` em `libs/ports/model.py`:** `async complete(request) -> response` e `capabilities()`. O pedido leva `model`, `system` (texto ou blocos, com marcadores de cache), `messages` e `tools` no formato de blocos da Messages API (`text`, `tool_use`, `tool_result`, `thinking`), `max_tokens`, `effort` opcional e `metadata` (`purpose`, `avatar_id`, `controller`). A resposta leva os blocos de conteúdo, `stop_reason`, `usage` (entrada, saída, cache lido, cache gravado), `model`, `request_id`, `latency_ms` e `replayed`. Lote (`submit_batch`) fica para quando a reflexão noturna do M11 precisar.
- **Um adaptador, `libs/adapters/model_anthropic.py`,** com o SDK oficial (`AsyncAnthropic`, `client.messages.create`, sem streaming: as respostas de decisão são curtas). Raciocínio adaptativo (`thinking: {type: adaptive}`) e `output_config.effort` quando o pedido traz; `tool_choice: auto`; `max_retries` do SDK e um tempo limite de 30 s por chamada. Erros do SDK viram `ModelCallError(kind, retryable)`: `rate_limit`, `timeout`, `connection`, `auth`, `bad_request`, `server`.
- **Provedor:** a API da Anthropic direta. O LiteLLM e o OpenRouter resolvem "muitos provedores e teto por chave", que não é o problema de agora; o Bedrock fica para a versão nuvem, pelo mesmo SDK (cliente Mantle). A porta é o que permite trocar.
- **De onde vem o crédito (aprofundado em 18/out).** A assinatura Claude Max não cobre a API pela senha de login, mas dá **créditos de API mensais**: US$ 100 por mês no Max 5x e US$ 200 no Max 20x, válidos para a API, o Agent SDK e os Managed Agents (não para o Claude Code), resgatados numa organização da Console vinculada à assinatura, depois de 7 dias no plano, e que expiram no fim de cada ciclo ([documentação](https://platform.claude.com/docs/en/about-claude/api-credits-for-subscribers.md)). Com a fazenda custando centavos por dia simulado no Haiku 5.5, os créditos sobram; sem resgate, a API é pré-paga por créditos comprados na Console.
- **Por que não os CLIs em modo headless como porta** (Claude Code `-p`, `codex exec`, Antigravity CLI), mesmo provisoriamente:
  - *Termos.* Os termos de consumidor dos planos Free, Pro e Max proíbem acessar o serviço "por meios automatizados ou não humanos, por bot, script ou de outra forma", salvo por chave de API ou permissão explícita ([consumer terms](https://www.anthropic.com/legal/consumer-terms), seção 3). A página legal do Claude Code reserva o login da assinatura ao "uso ordinário" do Claude Code e manda quem constrói produto usar chave de API ([legal and compliance](https://code.claude.com/docs/en/legal-and-compliance.md); [Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview.md)). Uma simulação fazendo cem chamadas por dia como backend de modelo não é uso ordinário, e o modo rápido do headless (`--bare`) exige chave de API de qualquer forma. Os planos do ChatGPT e do Google têm a mesma zona cinzenta.
  - *Limites e custo.* Cada `claude -p` carrega o prompt de sistema do Claude Code e conta nas janelas de 5 horas e semanal da assinatura; só esta sessão de trabalho consumiu 49% da janela de 5 horas numa noite. Cem decisões por dia simulado esgotariam a cota em dias.
  - *Engenharia.* Um subprocesso por decisão, com o harness e as ferramentas de um agente de código no meio; a saída estruturada existe (`--json-schema`, `structured_output`), mas o tool use não é o da API. O `codex exec` (`--json`, `--output-schema`) e o Antigravity CLI (`-p --output-format json`; o Gemini CLI de conta pessoal migrou para ele em junho) têm o mesmo perfil.
  - *Onde eles cabem:* nas **mãos do escritório** (v0.3), pelo Agent SDK, que os créditos do Max cobrem. É uso explicitamente previsto.
- **OpenRouter entra como segundo adaptador no M12,** a arena: API compatível com a da OpenAI, uma chave para Claude, GPT, Gemini e os demais, preços repassados sem margem e taxa de 5,5% na compra de créditos, `usage.cost` em toda resposta e cache de prompt dos modelos Anthropic por `cache_control` ([usage accounting](https://openrouter.ai/docs/use-cases/usage-accounting); [prompt caching](https://openrouter.ai/docs/features/prompt-caching); [FAQ](https://openrouter.ai/docs/faq)). A porta não muda; o adaptador é um irmão do da Anthropic.
- **Modelo padrão para o desenvolvimento: `claude-haiku-5-5`,** por custar uma ordem de grandeza menos; Sonnet 5.5 e Opus 5.5 entram na arena (M12), e o modelo é dado do mundo (`config/worlds/*.yaml`, por controlador, a partir do M10). A porta não sabe de nenhum modelo em particular.

## 2. Os eventos e o custo (decisões 4 e 5)

- **`campsverso.llm.call.completed.v1`** (visibilidade `observer`, produtor `controller`): `controller`, `purpose`, `avatar_id?`, `provider`, `model`, `request_id?`, `prompt_sha256`, `latency_ms`, `usage` (entrada, saída, cache lido, cache gravado), `cost_usd`, `charged` (falso quando veio da fita), `stop_reason`, `effort?`. **`campsverso.llm.call.failed.v1`** (`observer`): o mesmo cabeçalho mais `error` (`rate_limit`, `timeout`, `connection`, `auth`, `bad_request`, `server`, `cassette_miss`), `message` e `retryable`.
- **Quem publica é o decorador da porta** (`MeteredModel`, em `libs/adapters`), como o documento de contratos previa: o adaptador do provedor não conhece o barramento.
- **`campsverso.ops.budget.threshold_reached.v1`** (`scope: day|total`, `day?`, `threshold_pct`, `spent_usd`, `limit_usd`) e **`campsverso.ops.budget.exceeded.v1`** (`scope`, `day?`, `spent_usd`, `limit_usd`, `paused`), ambos com visibilidade **`observer`**, não `internal` como o documento de contratos listava: `internal` é para o que os agentes não podem saber (regras ocultas); o orçamento é assunto do operador, que o vê na linha do tempo, e nunca chega aos agentes de qualquer forma. O produtor `budget` entra na lista das ferramentas.
- **Preços são dados,** em `config/env/local.yaml` (`models: {claude-haiku-5-5: {input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok}, …}`), com a data da tabela. O custo de cada chamada sai do `usage`; um modelo sem preço na tabela derruba o processo na partida, nunca durante uma chamada.

## 3. Gravação e reprodução (decisão 6)

- **Fitas** (`cassettes`) em JSONL: uma linha por chamada, com o hash sha256 do pedido canônico (modelo, sistema, mensagens, ferramentas, `max_tokens`, `effort`; sem metadados nem tempo), o pedido, a resposta (blocos, `stop_reason`, `usage`, `model`, `request_id`) e a data da gravação.
- **Três modos** no `RecordingModel`, que envolve o adaptador: `live` (não grava), `record` (chama de verdade e grava o que não tinha) e `replay` (só a fita; faltou, erro `cassette_miss`). Os testes reproduzem fitas pequenas versionadas em `tests/fixtures/llm/`; o desenvolvimento grava em `data/llm/<mundo>.jsonl`, fora do git. Uma chamada reproduzida publica `llm.call.completed` com o `usage` original e `charged: false`; a guarda não a conta.

## 4. A guarda de orçamento (decisão 7)

- **Um serviço novo, `services/budget`** (usuário NATS `budget`): consumidor durável de `campsverso.<mundo>.observer.llm.>`, soma `cost_usd` das chamadas com `charged: true` por dia simulado (pelo `tick` do envelope) e no total do mundo, publica `threshold_reached` em 50, 80 e 100% de cada teto e, ao passar de 100%, `exceeded` e `cmd.clock.pause` com `reason: budget`. Guarda o gasto num arquivo (`data/budget/<mundo>.json`) e retoma dele depois de uma queda.
- **O teto é dado do mundo:** `config/worlds/*.yaml` ganha `budget: {usd_per_sim_day: 0.60, usd_total: 10.0}`; cada experimento da arena tem o seu.
- **Pausado por orçamento, o mundo só volta pelo operador** (`Retomar` na tela), e a guarda pausa de novo na próxima chamada cobrada se o teto continuar estourado. Subir o teto é editar o mundo e reiniciar a guarda; um comando `cmd.ops.budget.set` fica para o futuro, assim como "sem guarda viva o mundo pausa" (o `ops.heartbeat`).

## 5. Segredos, fumaça e calibração (decisões 8 e 9)

- **`ANTHROPIC_API_KEY` no `.env`,** digitada pelo usuário; `make secrets` passa a deixar a linha vazia pronta (`ANTHROPIC_API_KEY=`) quando falta. Os processos leem do ambiente, como leem as senhas do NATS. Nenhum log nem evento leva a chave nem o prompt. **Quando:** só no passo 5 (`make llm-smoke`); antes disso nada precisa da chave. O caminho: na Console (platform.claude.com), vincular a organização à assinatura e resgatar os créditos do mês, criar uma chave de API e colar no `.env`. Cuidado documentado: com a chave no ambiente, o próprio `claude -p` passa a cobrar da API em vez da assinatura; a chave fica no `.env` do projeto, que só o honcho e o `make llm-smoke` carregam.
- **`make llm-smoke`:** uma chamada real pela porta medida (modelo configurável, `claude-haiku-5-5` por padrão), imprimindo tokens, custo, latência, `request_id` e o evento publicado num barramento em memória. É o "uma chamada real" do critério, rodado à mão: o CI nunca chama a API.
- **`make percepcao CONTAR=1`:** conta com `count_tokens` uma amostra de fotos e deltas do arquivo e imprime o fator real de caracteres por token, para calibrar o 3,5 do M8.

## 6. Testes (decisão 10)

- **Sem rede no CI:** o adaptador é testado com um transporte HTTP falso do próprio SDK (`DefaultHttpxClient` com `MockTransport`): respostas boas, 429, 500, tempo esgotado e 400, conferindo o mapeamento de erros e o `usage`. O decorador é testado com o `ValidatingBus`: todo evento que sai passa pelo contrato. A fita é testada em ida e volta e no `cassette_miss`.
- **A guarda:** teste de unidade dos limiares e teste de pipeline em memória: eventos `llm.call.completed` sintéticos estouram o teto, a guarda publica e o kernel fica pausado.
- **Ao vivo, opcional:** um teste marcado `live`, pulado sem `ANTHROPIC_API_KEY` e sem `CAMPSVERSO_LIVE=1`, que faz uma chamada e confere o contrato. É o mesmo caminho do `make llm-smoke`.

## 7. Ordem do trabalho

1. **Contratos:** os quatro eventos, exemplos válidos e inválidos, `CHANGELOG`, catálogo §3.7 (ou uma §3.13 de LLM e operação), produtor `budget`; `make contracts` e `make compat`.
2. **Porta e adaptador:** `libs/ports/model.py`, `libs/adapters/model_anthropic.py`, o SDK como dependência do `libs/adapters` (`import-linter` já proíbe SDK fora dos adaptadores); testes com transporte falso.
3. **Fita e decorador:** `RecordingModel`, `MeteredModel`, o hash canônico, a tabela de preços em `config/env/local.yaml` e nas settings; testes.
4. **Guarda:** `services/budget`, usuário NATS, `NATS_ROLES`, Procfile, `budget` no mundo; testes de unidade e de pipeline.
5. **Fumaça e calibração:** `make llm-smoke`, `make secrets` com a linha da chave, `make percepcao CONTAR=1`; rodar os dois e anotar os números.
6. **Fechamento:** ADR-0058 com as decisões, diário, `futuro.md` (lote, `cmd.ops.budget.set`, heartbeat), `make sessoes MARCO=M9`, custos.

## 8. Decisões

1. **Provedor: a API da Anthropic direta, com o SDK oficial em Python (1.15), dentro de um adaptador, paga pelos créditos de API mensais da assinatura Max.** Os CLIs em modo headless não servem de porta (termos, cotas e engenharia); o OpenRouter entra no M12 como segundo adaptador; Bedrock fica para a nuvem. *Recomendação: sim.*
2. **Modelo padrão do desenvolvimento: `claude-haiku-5-5`;** Sonnet 5.5 e Opus 5.5 na arena, como dado do mundo. *Recomendação: sim; custa uma ordem de grandeza menos e o M10 é para aprender a usar a porta, não para medir o modelo.*
3. **A porta no formato de blocos da Messages API,** assíncrona, com `effort` por pedido, `tool_choice: auto` e sem lote por enquanto. *Recomendação: sim.*
4. **Quatro eventos com visibilidade `observer`,** publicados pelo decorador da porta e pela guarda; `ops.budget.*` deixa de ser `internal`. *Recomendação: sim.*
5. **Preços como dados em `config/env/local.yaml`,** custo por chamada a partir do `usage`, modelo sem preço derruba na partida. *Recomendação: sim.*
6. **Fitas JSONL com hash do pedido, três modos;** fitas de teste no git, fitas de desenvolvimento fora; reprodução com `charged: false`. *Recomendação: sim.*
7. **A guarda como serviço próprio,** com teto por dia simulado e total no arquivo do mundo, limiares 50/80/100%, pausa por `cmd.clock.pause`, retomada só pelo operador. *Recomendação: sim; os valores iniciais US$ 0,60 por dia e US$ 10 por mundo.*
8. **A chave no `.env`, digitada pelo usuário,** com `make secrets` preparando a linha. *Recomendação: sim.*
9. **`make llm-smoke` e `make percepcao CONTAR=1`** como a chamada real do critério e a calibração do fator de tokens. *Recomendação: sim.*
10. **O CI nunca chama a API:** transporte falso, fitas e um teste `live` pulado por padrão. *Recomendação: sim.*
