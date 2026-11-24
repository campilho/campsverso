# As sessões do Codex

Duas saídas do `codex exec --json`, para o conector do Codex (o plano do M26, §8; ADR-0089; o M27, ADR-0093):

- **`sessao-0.171.0.jsonl`** é uma sessão de verdade do Codex 0.171.0, o pacote completo do `make tools-maos`, **gravada no ensaio de 23/nov/2026**. O Codex rodou no nosso cercado, chamando o modelo pela porta das mãos, diante de uma OpenAI falsa que pedia cinco ferramentas e depois respondia: um `ls`, um patch que cria um arquivo, o robô testador e uma anotação (as ferramentas do mundo, pelo `/mcp` da porta) e um comando que sai com 1. O modelo era falso, então o texto e os tokens são os dele; o formato é o do Codex.
- **`exemplo.jsonl`** é uma sessão mais longa, **montada à mão em 22/nov** para a criação do M26, quando o dev não tinha rede nem o Codex na oficina. É ela que o `codex_falso.py` imprime nos testes das mãos.

As fontes do exemplo, lidas em 22/nov:
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

## O que o ensaio confirmou (o Codex 0.171.0)

- **O modo código.** O modelo não recebe o `exec_command` nem o `apply_patch` direto: recebe a ferramenta `exec`, que roda um JavaScript num isolado V8, e o JavaScript chama `tools.exec_command({cmd})` e `tools.apply_patch(texto)`. O `exec` precisa do `codex-code-mode-host` ao lado do `codex`, que o binário avulso do release não traz e o pacote (`codex-package-<alvo>.tar.gz`) traz. Sem ele, o Codex avisa num item `error` e segue sem ferramenta nenhuma.
- **Os itens.** As chamadas de dentro do JavaScript saem como os itens de sempre: o `command_execution` (com `item.started` e `item.completed`) e o `file_change`, que também tem `item.started`. O `exec` em si não vira item.
- **O comando** vem num shell de login, `/bin/zsh -lc 'ls -a'`; o passo mostra só o `ls -a`. O comando que sai com 1 acaba com `status` `failed` e o `exit_code`.
- **O caminho do `file_change`** é absoluto.
- **As ferramentas do mundo** vêm do `[mcp_servers.oficina]` do `config.toml`, no `/mcp` da porta das mãos, com a chave da sessão no `bearer_token_env_var`. O modelo as chama de dentro do JavaScript (`tools.mcp__oficina__chamar_robo`), e cada chamada sai como um `mcp_tool_call`, com o `server`, a `tool`, os `arguments` e o `result`.
- **Os tokens:** o `cached_input_tokens` é parte do `input_tokens`, como na API da OpenAI.
- **O cercado:** o Codex roda com o sandbox dele desligado (`danger-full-access`, `"sandbox":"none"` no pedido) e guarda o estado na casa da sessão (`.oficina/casa-codex`: as sessões, as memórias, os bancos SQLite), que fica fora da entrega.
- **O pedido ao modelo** é um `POST /v1/responses`, com `stream`, `store: false`, o `reasoning.effort` da sessão e as ferramentas num item `additional_tools` da entrada, não no campo `tools`.
