# O exemplo do Codex

O `exemplo.jsonl` é o que o `codex exec --json` imprime numa sessão curta, montado à mão em 22/nov/2026 para o conector do Codex, a criação do M26 (o plano do M26, §8; ADR-0089). O dev não tem rede nem o Codex na oficina: ele escreve o conector contra este exemplo, e o M27 liga o Codex de verdade, com a prova de conformidade.

**O exemplo não foi gravado de uma sessão de verdade.** Ele segue duas fontes, lidas em 22/nov:
- a página do modo não interativo, `https://learn.chatgpt.com/docs/non-interactive-mode.md` (o endereço `https://developers.openai.com/codex/noninteractive.md` redireciona para ela): os tipos de evento e uma amostra de cinco linhas;
- o código dos eventos no repositório público `openai/codex`, `codex-rs/exec/src/exec_events.rs`, no `main` do dia: os campos de cada evento e de cada item.

## O formato

Cada linha é um evento, com o campo `type`:
- `thread.started`, com `thread_id`: o primeiro, uma vez por sessão;
- `turn.started`, sem campos;
- `item.started`, `item.updated` e `item.completed`, com o `item`;
- `turn.completed`, com o `usage`: `input_tokens`, `cached_input_tokens`, `cache_write_input_tokens` (pode faltar; vale 0), `output_tokens` e `reasoning_output_tokens`;
- `turn.failed`, com o `error` (`message`);
- `error`, com `message`.

**O item** é plano: o `id`, o `type` e os campos do tipo.
- `agent_message` e `reasoning`: `text`.
- `command_execution`: `command`, `aggregated_output`, `exit_code` (nulo enquanto roda) e `status` (`in_progress`, `completed`, `failed` ou `declined`).
- `file_change`: `changes`, cada uma com `path` e `kind` (`add`, `delete` ou `update`), e `status` (`in_progress`, `completed` ou `failed`). Sai só no `item.completed`, quando o patch é aplicado ou falha.
- `mcp_tool_call`: `server`, `tool`, `arguments`, `result`, `error` e `status`.
- `web_search`: `query`.
- `todo_list`: `items`, cada um com `text` e `completed`.
- `error`: `message`.

O código traz também o `collab_tool_call` (os subagentes do Codex), que a oficina não usa.

## O que o exemplo não confere

- **O caminho do `file_change`:** aqui é relativo à pasta da sessão. O Codex de verdade pode dar o caminho absoluto; o conector deve aceitar os dois.
- **Os tokens:** pela amostra da página, `cached_input_tokens` é parte de `input_tokens` (24.448 de 24.763), como na API da OpenAI. O custo deve contar o cache uma vez só.
- **O número da versão:** o app do Codex traz a CLI 0.171.0-alpha.13 (22/nov), que não foi rodada para montar o exemplo.
