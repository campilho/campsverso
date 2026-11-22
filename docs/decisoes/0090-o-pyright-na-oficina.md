# ADR-0090 — O pyright na oficina: o node vem do lock

**Status:** aceita · **Data:** 2026-11-22 · **Marco:** M26
**Complementa:** ADR-0080 (a oficina isolada); ADR-0086 (o testador com o `ruff` e o `pyright`); ADR-0089 (as mãos e o sandbox do Claude Code)

## Contexto

Na comparação das mãos (22/nov, `docs/arena/m26-as-maos.md`), as duas mãos anotaram na memória que "o `pyright` não roda na oficina". No mesmo dia, o PR #4 do dev (o conector do Codex) caiu no CI com 11 erros do `pyright` estrito, que o dev não tinha como ver.

A causa:
- **O pacote `pyright` do PyPI já traz o pyright do npm** (`pyright/dist`), mas não o node.
- **Ele procura o node nesta ordem:**
  1. o pacote `nodejs_wheel`, do extra `pyright[nodejs]`;
  2. um `node` no `PATH`;
  3. um download pelo `nodeenv` para `~/.cache/pyright-python`.
- **Na oficina, sobra só o download:** o `PATH` não tem node, e o sandbox corta a rede. O pyright cai em `nodeenv failed`.
- **Fora da oficina, o node vinha de fora do projeto:** na máquina, o `/usr/local/bin/node` 22; no CI, o da imagem do Ubuntu. O Node 24 do `devEngines` fica em `node_modules/`, que o `uv run` não vê.

## Decisão

1. **O node do pyright vem do lock:** o extra `pyright[nodejs]` no grupo `dev`, travado no `uv.lock` com hash. O node fica dentro do ambiente Python, e o `uv sync --offline --frozen` de cada espaço o traz do cache, como os outros pacotes. Os perfis do sandbox não mudam, porque o node fica no `.venv` do espaço.
   - **Ficaram de fora:** o node que o pnpm baixa para `node_modules/`, um node próprio em `.tools/` e o cache do pyright preenchido antes. Os dois primeiros abriam uma leitura na casa do usuário em cada perfil; o terceiro baixava o node sem hash e fora do lock.
2. **Na versão maior do front:** `nodejs-wheel-binaries>=24,<25`. Hoje o lock tem o 24.19.0; o pnpm, o 24.21.0.
3. **O pyright do espaço não pergunta ao PyPI por uma versão nova:** `PYRIGHT_PYTHON_IGNORE_WARNINGS=1` no ambiente das mãos e dos robôs. No sandbox das mãos a conexão é cortada, mas a consulta de DNS passaria, pelo soquete do sistema que o perfil libera.
4. **O texto da sessão das mãos** (`sessao-maos.md`) pede o `pyright` do projeto junto com os testes. A memória do dev não muda à mão: ele lê no texto da sessão que agora roda.
5. **O testador é pedido do dev:** rodar o `pyright` nos arquivos mudados, só nos que o `include` do projeto cobre, como o CI. É a metade da ADR-0086 que parou neste node.

## Consequências

- **O Claude Code roda o `pyright` no terminal do espaço:**
  - o projeto inteiro, num espaço, sob o sandbox das mãos e com a casa fechada, em 8 s;
  - dois arquivos em 2 s.
- **O nosso harness só terá o `pyright` pelo testador,** depois do pedido do dev.
- **O `pyright` usa o mesmo node na máquina, no CI e na oficina,** fixado no lock.
- **O ambiente Python fica maior:** um pacote de 56 MB no macOS e 61 MB no Linux, uns 200 MB aberto.
  - No macOS, cada espaço clona os arquivos do cache, sem gastar disco: o `uv sync` do espaço levou 0,4 s.
  - No Linux, o uv usa links fixos quando o cache e o espaço estão no mesmo disco, como no CI.
- **Três testes:**
  - o ambiente traz o `nodejs_wheel`;
  - no macOS, o `pyright` estrito roda como robô no sandbox da oficina;
  - no macOS, ele roda pelo lançador das mãos, com a casa de verdade fechada.

  Sem o node, os três caem com o mesmo `nodeenv failed` da oficina.
