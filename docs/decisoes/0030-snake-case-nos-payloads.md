# ADR-0030 — `snake_case` nos payloads; o envelope segue o CloudEvents

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0
**Altera:** grafia dos campos nos exemplos de `contratos-eventos-v0.md` §8 e §14

## Contexto

- O CloudEvents exige que os atributos de extensão do envelope tenham só letras minúsculas e dígitos (`correlationid`, `worldid`).
- Os exemplos dos documentos estenderam essa grafia aos payloads (`appliedtick`, `durationticks`), que o CloudEvents não restringe.
- Nomes sem separador são mais difíceis de ler.

## Decisão

- **Campos de payload (`data`) em `snake_case`:** `applied_tick`, `action_id`, `avatar_id`. Vale também para nomes de atributos de entidade (`watered_today`).
- **Atributos do envelope seguem o CloudEvents:** minúsculas sem separador, como já definidos (`correlationid`, `controllerid`).
- **Palavras reservadas** em Python ou TypeScript (`from`, `to` como campo isolado, `class`, `default`…) não são usadas como nome de campo. Usam-se pares descritivos: `previous_value` e `value`, `from_container` e `to_container`.
- O CI confere a grafia de todo campo de payload: `^[a-z][a-z0-9]*(_[a-z0-9]+)*$`.

## Consequências

- Os modelos Python ficam naturais. No TypeScript os campos mantêm o mesmo nome, sem conversão para camelCase: um nome só em todo lugar evita erros de mapeamento.
- Convivem duas grafias (envelope e payload), cada uma com sua razão documentada.
