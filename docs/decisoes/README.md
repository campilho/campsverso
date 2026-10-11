# Decisões de arquitetura (ADRs)

Registro curto das decisões do Campsverso. **Uma ADR aceita prevalece sobre o texto dos documentos em `docs/arquitetura/`.** Os documentos não são reescritos a cada decisão, para preservar o histórico do raciocínio; cada ADR diz o que altera ou esclarece.

## Decisões anteriores, registradas nos próprios documentos

| Faixa | Onde |
|---|---|
| ADR-001 a ADR-010 | `contratos-eventos-v0.md` §3 |
| D1 a D7 | `contratos-eventos-v0.md` §13 |
| T1 a T7 | `kernel-gestao-do-tempo.md` §14 |

A numeração deste diretório continua a partir de **0011**, para não colidir com ADR-001 a 010.

## Índice

| ADR | Decisão | Marco | Altera ou esclarece |
|---|---|---|---|
| [0011](0011-api-de-cartucho.md) | `libs/cartridge-api` só com interfaces; cartucho dividido em `sim` e `script`; carregado por nome via *entry points* | M0/M1 | CLAUDE.md, princípios 1 e 8 |
| [0012](0012-cartridge-aceita-qualquer-nome.md) | `cartridge` no envelope aceita qualquer nome `^[a-z0-9-]+$` | M0 | contratos §5.2 |
| [0013](0013-envelope-dos-comandos.md) | Comandos usam o mesmo envelope, com `visibility: observer` | M0 | contratos §7, §8.1 |
| [0014](0014-sono-e-desmaio-no-dominio-avatar.md) | `avatar.sleep.started/ended.v1` e `avatar.fainted.v1` | M0 | tempo §12 |
| [0015](0015-comando-para-alternar-regras.md) | Novo `cmd.rules.toggle.v1`; kernel publica `rules.toggled.v1`; sem `rules.hot_applied.v1` | M0/M1 | contratos §7, §8.3; tempo §12 |
| [0016](0016-schemas-estritos-modelos-tolerantes.md) | Schemas estritos para o produtor; modelos gerados tolerantes para o consumidor | M0 | contratos §5.2 × §9 |
| [0017](0017-stream-commands-com-retencao-por-limites.md) | Stream `COMMANDS` com retenção por limites, não fila de trabalho | M2 | contratos §6, D3 |
| [0018](0018-dia-agricola-e-clima-do-dia-1.md) | Dia agrícola = [06:00, 06:00); clima do dia 1 sorteado na abertura | M1 | bíblia §3, §6 |
| [0019](0019-ordem-dos-ids-dos-canteiros.md) | Ids dos canteiros numerados por linha, depois por coluna | M1 | bíblia §4, §11 |
| [0020](0020-biblia-prevalece-nos-numeros-do-mundo.md) | Nos números do mundo vale a bíblia; `water` = 2 ticks | M0/M1 | contratos §8.2; tempo §7 |
| [0021](0021-campos-ignorados-no-hash-de-determinismo.md) | Hash de determinismo ignora também `causationid` e `correlationid` | M3 | escopo §8 (A4, A5) |
| [0022](0022-gateway-le-eventos-agent-do-avatar.md) | Gateway assina `agent.camps.>` para o controlador humano | M4/M5 | escopo §5 |

## Modelo

```markdown
# ADR-NNNN — Título curto

**Status:** proposta | aceita | substituída por ADR-NNNN · **Data:** AAAA-MM-DD · **Marco:** Mx
**Altera:** documento §seção (ou **Esclarece:**, ou **Complementa:**)

## Contexto
O problema, e por que os documentos não resolviam.

## Decisão
O que fica decidido.

## Consequências
O que muda, o que fica mais fácil, o que fica mais difícil.
```
