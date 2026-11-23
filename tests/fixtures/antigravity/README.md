# O exemplo do Antigravity

O `exemplo.jsonl` é o que o `agy -p … --output-format stream-json` imprime numa sessão curta, **montado à mão em 22/nov/2026** para o conector do Antigravity (o plano do M27, §5; ADR-0093). Ele não foi gravado de uma sessão de verdade: a primeira sessão da prova de conformidade (`make conformidade MAOS=antigravity`) grava a fita que o substitui.

Ele segue a documentação oficial, lida em 22/nov:
- o modo sem interface, `https://antigravity.google/docs/cli/headless/` (as seções do JSON em streaming e das ferramentas no streaming);
- a referência da CLI, `https://antigravity.google/docs/cli/reference/`;
- a autenticação, `https://antigravity.google/docs/install/`.

O `{espaco}` do exemplo vira a pasta onde o `agy_falso.py` roda, como o caminho absoluto que o `agy` dá.

## O formato

Cada linha é um objeto com o campo `event`, que dá o tipo, e o corpo numa chave de mesmo nome:
- **`init`**, uma vez, no começo: `cwd`, `tools`, `permission_mode` (`always-proceed` com o `--dangerously-skip-permissions`) e o `model`, quando dado. O `conversation_id` fica fora do corpo.
- **`step_update`**, a cada mudança de um passo: `conversation_id`, `step_index` (a partir de zero), `state` (`ACTIVE` ou `DONE`), `step_type` (`user_input`, `agent_response`, `tool`, `checkpoint`), e ainda:
  - `text_delta`: o pedaço novo do texto de uma resposta. Uma resposta sai em um ou mais `ACTIVE` e um `DONE`; a curta, num `DONE` só;
  - `tool_name` e `tool_info`, num passo de ferramenta: `name`, `parameters`, `output` e, só quando a ferramenta falha, `error` (com `type` e `message`);
  - `duration_seconds` e `usage`, quando conhecidos.
- **`result`**, uma vez, no fim: `conversation_id`, `status` (`SUCCESS`, `ERROR`, `CANCELED`, `INTERRUPTED`, `INVALID`, `WAITING`, `RUNNING`), `response`, `error` (só na falha), `duration_seconds`, `num_turns` e o `usage`, plano: `input_tokens`, `output_tokens`, `thinking_tokens`, `cache_read_tokens` e `total_tokens`.

A documentação não traz um evento de erro: a falha é um `result` com o `status` `ERROR`. Também não há id de chamada de ferramenta: o passo é o `step_index`.

## O que o exemplo não confere

- **Os nomes das ferramentas de arquivo e dos parâmetros.** A documentação só mostra o `run_command`, com o `CommandLine`. O `view_file` (`AbsolutePath`), o `write_to_file` e o `replace_file_content` (`TargetFile`) vêm da família do Antigravity e são palpite. O conector pega como caminho o primeiro parâmetro cujo nome termina em `path` ou `file`.
- **O texto de uma resposta.** O exemplo trata o `text_delta` do `DONE` como o último pedaço, somado aos dos `ACTIVE`. Se o `DONE` trouxer o texto inteiro, o resumo sai repetido; o resumo da entrega usa o `response` do `result`, que não depende disso.
- **Os tokens.** O exemplo trata o `cache_read_tokens` como parte do `input_tokens` (o `total_tokens` é a entrada, a saída e o pensamento), como na API do Gemini.
- **O comando que falha.** A documentação não diz se um comando com saída diferente de zero traz o `error`; no exemplo, o pytest que falha traz só a saída.
- **O SIGTERM.** O falso entrega um `result` `CANCELED` com os tokens; o `agy` de verdade não foi visto parando.
- **O slug do modelo.** O `agy models` lista o modelo com o esforço no fim (`gemini-4-neon-high`); o conector manda o slug e não o `--effort`. Que modelo o `agy` pede à API pelo `GOOGLE_GEMINI_BASE_URL` (o falso pede o `gemini-4-neon`) só a primeira sessão mostra.
- **O pedido pela linha de comando.** O briefing vai no `-p`. A documentação não dá limite; o conector recusa um briefing maior que 120 KB, abaixo do limite de um argumento no Linux.
