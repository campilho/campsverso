# ADR-0034 — Volta para o Python 3.14

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0
**Substitui:** ADR-0023 (Python 3.15)
**Altera:** ADR-0033, item 4 (o gerador de modelos não precisa mais rodar isolado)

## Contexto

O M0 rodou no Python 3.15, que saiu em 09/out/2026. Tudo funcionou, com três contornos:

- o `datamodel-code-generator` 0.83 quebra ao rodar sob o 3.15 e precisou rodar isolado no 3.14 via `uvx`;
- `pyyaml` não tem versão pronta (wheel) para o 3.15 e compila a partir do código-fonte;
- o stub do pyright para `frozendict` ainda é incompleto.

Num levantamento de 11/out das dependências previstas até o M4 (`pydantic-core`, `orjson`, `uvloop`, `httptools`, `watchfiles`, `websockets`, `pyyaml`, `msgspec`, `aiosqlite`), 7 já têm wheel para o 3.15. Faltam `pyyaml` e `watchfiles`. No 3.14, todas têm.

## Decisão

- Voltar para o **Python 3.14** enquanto o projeto está no começo: `.python-version`, `requires-python = ">=3.14"`, ruff `py314`, pyright `3.14`.
- O gerador de modelos volta a rodar no próprio ambiente do projeto, com a versão travada no `uv.lock`. A saída gerada ficou idêntica byte a byte.
- **Revisitar o 3.15 no início da v0.2**, ou antes se aparecer um motivo concreto. Gatilho: `datamodel-code-generator` e todas as dependências com suporte oficial ao 3.15.

## Consequências

- Nenhum contorno de versão no pipeline. O CI fica mais simples: não precisa de um segundo Python nem do `uvx`.
- Perdemos o `frozendict` nativo, que ainda não era usado. Para estado imutável há `types.MappingProxyType`, tuplas e dataclasses congeladas.
- O projeto não serve de cobaia para o 3.15 nas dependências do M2 ao M4 (NATS, FastAPI, WebSocket), onde um problema custaria mais tempo.
