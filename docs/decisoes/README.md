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
| [0012](0012-cartridge-aceita-qualquer-nome.md) | `cartridge` no envelope aceita qualquer nome (padrão refinado pela 0031) | M0 | contratos §5.2 |
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
| [0023](0023-python-3-15.md) | ~~Python 3.15~~ (substituída pela 0034) | M0 | CLAUDE.md (stack) |
| [0024](0024-nats-binario-local-containers-antes-da-aws.md) | `nats-server` como binário local; containers antes da AWS | M2 | CLAUDE.md (stack, estrutura) |
| [0025](0025-modelo-de-mundo-do-kernel.md) | O kernel tem um modelo de mundo genérico ("física"); cartuchos mudam o mundo só pelas primitivas; evento do cartucho só com significado próprio | M0/M1 | CLAUDE.md, princípio 8; contratos §14.3 |
| [0026](0026-pausa-e-estado-nao-modo.md) | Pausa é estado; modos `continuous` e `max` | M0/M1 | escopo §3, §5; tempo §5 |
| [0027](0027-avatar-id-nos-eventos-do-kernel.md) | `avatar_id` nos eventos do kernel; `agent_id` fica para a cognição | M0 | contratos §8.1, §8.2 |
| [0028](0028-percepcao-so-com-instantaneos.md) | Percepção só com instantâneos na v0.1; deltas na v0.2 | M0/M3 | contratos §14.4 |
| [0029](0029-catalogo-de-eventos-da-v0-1.md) | Catálogo da v0.1 (38 eventos, 9 comandos) é a especificação do M0 | M0 | contratos §7, §14; tempo §12, §13 |
| [0030](0030-snake-case-nos-payloads.md) | `snake_case` nos payloads; envelope segue o CloudEvents | M0 | contratos §8, §14 (grafia) |
| [0031](0031-cartuchos-em-camadas.md) | Cartuchos em camadas (gênero → cenário → mundo); v0.1 com `farm` + `farm_camps`; nome do cartucho `^[a-z][a-z0-9_]*$` | M0/M1 | ADR-0011, 0012, 0025; bíblia §1 |
| [0032](0032-ferramentas-typescript.md) | Node 24 fixado no projeto, pnpm 12, TypeScript 6.0; scripts de instalação bloqueados por padrão | M0 | CLAUDE.md (stack) |
| [0033](0033-pipeline-dos-contratos.md) | Pipeline dos contratos: visibilidade fixa por tipo, validação dupla, codegen (gerador no 3.14), AsyncAPI 3.1 gerado, compatibilidade | M0 | contratos §10 |
| [0034](0034-volta-para-python-3-14.md) | Volta para o Python 3.14; revisitar o 3.15 no início da v0.2 | M0 | ADR-0023, ADR-0033 |
| [0035](0035-ci-no-github-actions.md) | CI no GitHub Actions: make check num Linux limpo a cada push e pull request; actions fixadas por hash | M0 | escopo §7 |
| [0036](0036-convencao-de-nomes-e-ids.md) | Convenção de nomes e ids; unicidade dentro do mundo e da cadeia de cartuchos | M1 | catálogo §1.3, §1.4 |
| [0037](0037-pipeline-do-tick-configuravel.md) | Ordem do tick em etapas nomeadas e configuráveis, travada por teste de referência | M1 | ADR-0018 |
| [0038](0038-decisoes-do-kernel-para-o-m1.md) | Kernel do M1: necessidades inteiras, modelo e A* próprios, calendário 2026-10-10, RNG próprio, núcleo + serviço | M1 | ADR-0025 |
| [0039](0039-decisoes-do-cartucho-farm-para-o-m1.md) | Fazenda do M1: estágios, ids dos objetos, limiares 80/20/0, regra genérica de água, chuva, venda | M1 | bíblia §4, §6, §7, §10 |
| [0040](0040-kits-de-teste.md) | Kits de teste: laboratório genérico no kernel; Fazenda do Camps em `campsverso_testkit`, fora do sistema | M1 | ADR-0011, ADR-0025 |
| [0041](0041-sono-em-qualquer-lugar.md) | Dormir em qualquer lugar; a cama (e análogos) turbina a recuperação; sono ruim 5/h; indicadores ligados por cartucho | M2 | bíblia §7, §8; ADR-0039 |
| [0042](0042-eventos-de-sono-v2.md) | Eventos `sleep.started/ended.v2` (`cause: voluntary\|faint`, `bed_id` opcional); taxa do chão = taxa `asleep` do gênero; camas em `sleep.beds` | M2 | catálogo §3.5; ADR-0041 |
| [0043](0043-arquivo-jsonl-por-data-simulada.md) | Arquivo JSONL por mundo e data simulada; confirmar depois de gravar; linha cortada removida; dias antigos em `.gz` | M2 | plano do M2 §2 |
| [0044](0044-recuperacao-transparente.md) | Recuperação transparente (sem `session.started` no reinício); só grava o que produziu algo; snapshot é fato; versão = sha256 do código | M2 | plano do M2 §1 |
| [0045](0045-nats-local-usuarios-e-senhas.md) | nats-server 2.14.8 com sha256 fixado; um usuário por processo; senhas em `.env`; `make up`/`stop`/`run` | M2 | ADR-0024; plano do M2 §3 |
| [0046](0046-kernel-recusa-comandos-fora-do-contrato.md) | O kernel valida comandos contra o contrato no caminho determinístico; inválidos viram `invalid_command` | M2 | ADR-0013; A2 |
| [0047](0047-decisoes-do-plano-do-m3.md) | Decisões do M3: `move {near}`, percepção durável, soak de 2 dias no check e 30 à mão, `make replay` pelo kernel, lockstep sem prazo, `make metrics`, sem salto de tempo; futuro: enxergar o mapa num raio N | M3 | plano do M3 |
| [0048](0048-ciclo-de-decisao-do-m3.md) | Ciclo de decisão do M3: a foto traz o pedido (`decision`), lockstep pela dívida de decisão, replay com agenda (`at_tick`), ids derivados, `caught_up`, controlador inicial por mundo, hash sem o sha256 do snapshot | M3 | catálogo §3.7; ADR-0021, 0028, 0047 |

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
