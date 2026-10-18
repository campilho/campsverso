# ADR-0058 — Decisões do plano do M9 (porta de modelo e orçamento)

**Status:** aceita · **Data:** 2026-10-18 · **Marco:** M9
**Complementa:** `docs/planos/m9-porta-de-modelo-e-orcamento.md`; `docs/planos/v0.2-macro.md`; contratos §8.5 e §12.1; ADR-0048, ADR-0056
**Altera:** contratos §8.5 (visibilidade de `ops.budget.*`)

## Decisão

As decisões do plano, aprovadas pelo usuário em 18/out/2026:

1. **Provedor: a API da Anthropic direta, pelo SDK oficial em Python (1.15), dentro de um adaptador,** paga pelos créditos de API mensais da assinatura Max (US$ 100 ou 200 por mês, válidos para a API e o Agent SDK, resgatados na Console). Os CLIs em modo headless (Claude Code `-p`, `codex exec`, Antigravity) não servem de porta: os termos dos planos de consumidor reservam o login da assinatura ao uso ordinário e vedam acesso por script sem chave de API; cada chamada carregaria o prompt de um agente de código e contaria nas cotas; e o tool use não seria o da API. Eles cabem nas mãos do escritório (v0.3), pelo Agent SDK. O OpenRouter entra no M12 como segundo adaptador; o Bedrock fica para a nuvem.
2. **Modelo padrão do desenvolvimento: `claude-haiku-5-5`;** Sonnet 5.5 e Opus 5.5 na arena, como dado do mundo.
3. **A porta (`ModelPort`) é assíncrona, no formato de blocos da Messages API,** com `effort` por pedido, `tool_choice: auto` (Sonnet 5.5 e Opus 5.5 recusam o forçado), marcadores de cache repassados e `stop_reason` repassado (inclusive `refusal`). Lote fica para quando a reflexão noturna (M11) precisar.
4. **Quatro eventos com visibilidade `observer`:** `llm.call.completed.v1`, `llm.call.failed.v1`, `ops.budget.threshold_reached.v1` e `ops.budget.exceeded.v1`. Os de orçamento deixam de ser `internal`, como o documento de contratos listava: `internal` é para o que os agentes não podem saber; o orçamento é assunto do operador. Quem publica os de chamada é o decorador da porta (`MeteredModel`), não o adaptador; os de orçamento, a guarda.
5. **Preços são dados em `config/env/local.yaml`;** o custo de cada chamada sai do `usage`; um modelo sem preço derruba o processo na partida.
6. **Fitas (cassettes) JSONL,** com o hash sha256 do pedido canônico, em três modos: `live`, `record` e `replay`; as de teste no git, as de desenvolvimento fora; uma chamada reproduzida publica `charged: false`, e a guarda não a conta.
7. **A guarda de orçamento é um serviço próprio (`services/budget`, usuário NATS `budget`):** teto por dia simulado e total no arquivo do mundo (`budget: {usd_per_sim_day: 0.60, usd_total: 10}`), avisos em 50, 80 e 100%, pausa por `cmd.clock.pause` com `reason: budget`; só o operador retoma.
8. **A chave fica no `.env`, digitada pelo usuário,** e só é necessária no `make llm-smoke`; `make secrets` deixa a linha pronta.
9. **`make llm-smoke`** é a chamada real do critério; **`make percepcao CONTAR=1`** calibra o fator de tokens do M8 com `count_tokens`. A língua do prompt de sistema é decisão do M10.
10. **O CI nunca chama a API:** o adaptador é testado com um transporte HTTP falso do SDK, o resto com fitas, e um teste `live` fica pulado por padrão.

## Consequências

- Contratos: quatro tipos novos no domínio `llm` e `ops`, `llm_usage` em `common/defs.v1`, e o produtor `budget`. Nenhum tipo muda.
- `libs/ports` ganha `ModelPort`; `libs/adapters` ganha o adaptador da Anthropic, a fita e o decorador, e passa a depender do SDK `anthropic` (só ali: o `import-linter` já proíbe SDK fora dos adaptadores).
- Um processo a mais no Procfile e um usuário a mais no NATS; o arquivo do mundo ganha `budget`.
- O mundo pausado por orçamento é um fato visível na linha do tempo do operador; a guarda caída não pausa o mundo (o `ops.heartbeat` fica no `futuro.md`), assim como `cmd.ops.budget.set` e o lote.
