# As sessões do Antigravity

Duas saídas do `agy -p … --output-format stream-json`, para o conector do Antigravity (o plano do M27, §5; ADR-0093):

- **`sessao-1.5.14.jsonl`** é uma sessão de verdade do Antigravity CLI 1.5.14 (o `make tools-maos`), **gravada no ensaio de 23/nov/2026**: o `agy` no nosso cercado, chamando o modelo pela porta das mãos, diante de um Gemini falso que pedia seis ferramentas e depois respondia. Um comando, escrever, ler e editar arquivos, ler um que não existe e um comando que sai com 1. O modelo era falso, então o texto e os tokens são os dele; o formato, os nomes e os estados são os do `agy`.
- **`exemplo.jsonl`** é uma sessão mais longa, **montada à mão em 22/nov** da documentação oficial e posta, em 23/nov, no formato do ensaio. É ela que o `agy_falso.py` imprime nos testes das mãos.

A primeira sessão da prova de conformidade (`make conformidade MAOS=antigravity`) grava a fita com o modelo de verdade.

O `{espaco}` das duas vira a pasta do espaço, como o caminho absoluto que o `agy` dá.

As fontes da documentação, lidas em 22/nov:
- o modo sem interface, `https://antigravity.google/docs/cli/headless/` (as seções do JSON em streaming e das ferramentas no streaming);
- a referência da CLI, `https://antigravity.google/docs/cli/reference/`;
- a autenticação, `https://antigravity.google/docs/install/`.

## O formato

Cada linha é um objeto com o campo `event`, que dá o tipo, e o corpo numa chave de mesmo nome:
- **`init`**, uma vez, no começo: `cwd`, `tools` (a lista interna, de umas sessenta), `permission_mode` (`always-proceed` com o `--dangerously-skip-permissions`) e o `model`. O `conversation_id` fica fora do corpo.
- **`step_update`**, a cada mudança de um passo: `conversation_id`, `step_index` (a partir de zero), `state`, `step_type` (`user_input`, `agent_response`, `tool`, `checkpoint`), e ainda:
  - o `state` é `ACTIVE` enquanto o passo corre e `DONE` quando acaba; a ferramenta que falha acaba em `ERROR`;
  - `text_delta`: o texto de uma resposta. A resposta curta sai inteira num `DONE` só;
  - `tool_name` e `tool_info`, num passo de ferramenta: `name`, `parameters` (só o principal: o `CommandLine` ou o `Path`, nunca o conteúdo escrito), `output` e, na falha, `error` (com `type` e `message`);
  - `duration_seconds` e, na resposta, o `usage` da chamada.
- **`result`**, uma vez, no fim: `conversation_id`, `status` (`SUCCESS`, `ERROR`, `CANCELED`, `INTERRUPTED`, `INVALID`, `WAITING`, `RUNNING`), `response`, `error` (só na falha), `duration_seconds`, `num_turns` (os pedidos do usuário, não as chamadas) e o `usage` da sessão.

## O que o ensaio confirmou (o `agy` 1.5.14)

- **As ferramentas que o modelo vê** são catorze. As de arquivo são o `read_file`, o `write_file` e o `edit_file`, com o caminho absoluto no `Path`. O `run_command` pede o `CommandLine`, o `toolSummary` e o `WaitMsBeforeAsync`. O `tool_name` do passo é o mesmo nome.
- **A saída de um comando** é `Created At: …`, `Completed At: …`, e `Command exited with code N.` antes da saída, ou `Command failed to run: …` quando ele nem roda. Um comando que sai com 1 é um `DONE` sem `error`: o conector lê o código.
- **A saída das ferramentas de arquivo** não traz o conteúdo: o `read_file` diz `1 lines, 9 bytes`, e o `write_file` e o `edit_file`, nada.
- **Os tokens:** o `input_tokens` não conta o cache (`cache_read_tokens`), o `output_tokens` já conta o pensamento (`thinking_tokens`), e o `total_tokens` é a entrada mais a saída.
- **O modelo:** com `--model gemini-4-neon-high`, o `agy` pede o `gemini-4-neon` no `streamGenerateContent` do `GOOGLE_GEMINI_BASE_URL`, com o `thinkingLevel` `HIGH`, e a chave no `x-goog-api-key`. O `--model gemini-4-neon --effort high` dá o mesmo pedido.
- **O cercado:** o `agy` roda um servidor de linguagem dentro dele, numa porta local que ele mesmo escolhe, e roda cada comando num terminal novo (o `/dev/ptmx`). Ele também tenta mandar telemetria ao Google, que o cercado barra.

## O que ainda não confere

- **O texto em pedaços.** No ensaio, cada resposta veio inteira num `DONE`. O conector soma os `text_delta` dos `ACTIVE` com o do `DONE`; se o `DONE` de uma resposta longa trouxer o texto inteiro, o texto da volta sai repetido. O resumo da entrega usa o `response` do `result`, que não depende disso.
- **O SIGTERM.** O falso entrega um `result` `CANCELED` com os tokens; o `agy` de verdade não foi visto parando.
- **O pedido pela linha de comando.** O briefing vai no `-p`. A documentação não dá limite; o conector recusa um briefing maior que 120 KB, abaixo do limite de um argumento no Linux.
