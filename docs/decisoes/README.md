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
| [0049](0049-cochilo-dormir-a-qualquer-hora.md) | Dormir a qualquer hora: à noite até as 06:00; de dia, cochilo até a energia encher (no máximo até as 06:00); `not_tired` com energia cheia | M4 | bíblia §7, §8, §11; ADR-0041 |
| [0050](0050-decisoes-do-plano-do-m4.md) | Decisões do M4: contrato `realtime`, projeção no gateway com merge patch (genérica, sem desenho), mapa do cartucho pelo gateway, visões filtradas no gateway em 127.0.0.1, métricas no M7, `make sandbox`, sem Playwright | M4 | plano do M4; ADR-0022, 0025 |
| [0051](0051-decisoes-do-plano-do-m5.md) | Decisões do M5: catálogo de ações do cartucho no `session.started`, as duas visões jogam, "Assumir" passa o mundo ao contínuo, clique esquerdo anda e direito abre o menu, sem devolução automática, pulso de 1 s, custos em `docs/custos/` | M5 | plano do M5; ADR-0022, 0050 |
| [0052](0052-politica-de-interrupcao-das-acoes.md) | Política de interrupção de cada ação (`never`, `cancel`, `partial`), declarada pelo cartucho; `busy` para quem trabalha; gancho para guardar o trabalho feito; fila e despertador no futuro | M6 | bíblia §8; ADR-0038, 0051 |
| [0053](0053-decisoes-do-plano-do-m6.md) | Decisões do M6: Phaser 4.2.1, arte no cartucho em camadas com manifesto, LPC com créditos, mapa visual num arquivo à parte, noite e chuva simples, `?render=debug`, retrato recortado, Playwright de fumaça no CI | M6 | plano do M6; ADR-0031, 0050 |
| [0054](0054-decisoes-do-plano-do-m7.md) | Decisões do M7: catálogo de métricas declarado pelo cartucho (`count`, `max_need`, `item`) e contado pela projeção comum, painel com hoje, ontem e 7 dias, `docs/aceite-v0.1.md` com soaks de 30 dias, mundo oficial pelo usuário, README com Mermaid, tag `v0.1.0` | M7 | plano do M7; ADR-0047, 0051 |
| [0055](0055-a-v0-3-e-o-escritorio-que-se-constroi.md) | A v0.3 é o escritório que constrói a si mesmo: primeiro cartucho com efeitos externos, a v0.2 inalterada como pré-requisito, "a mente no mundo, as mãos na oficina", portão humano, governança, dev generalista e revisor; o estúdio vem depois | v0.3 | ideia do escritório; escopo §2; ADR-0025, 0031, 0052, 0054 |
| [0056](0056-decisoes-do-plano-do-m8.md) | Decisões do M8: terreno e raio de percepção no `session.started`, `view.map` na foto, delta como tipo novo `perception.updated.v1` com `events`, política por tipo de controlador (foto a cada 20 deltas para o LLM), acordado −1/h e fome em 100 drenando 4/h como dados do cartucho, tokens estimados por bytes ÷ 3,5, Python 3.14 | M8 | plano do M8; ADR-0028, 0034, 0047 |
| [0057](0057-tick-antecipado-e-30-tiles-por-minuto.md) | Tick antecipado no modo contínuo (uma proposta no meio do tick roda o próximo tick na hora, descontado do tempo real; o replay não muda), andar a 30 tiles por minuto e teto de 12 tiles por segundo no desenho | M8 | bíblia §8; tempo §3.3; ADR-0037 |
| [0058](0058-decisoes-do-plano-do-m9.md) | Decisões do M9: API da Anthropic direta pelo SDK num adaptador (créditos de API da assinatura Max; CLIs headless não servem de porta), `claude-haiku-5-5` no desenvolvimento, porta em blocos da Messages API, quatro eventos `observer` (`llm.call.*`, `ops.budget.*`), preços como dados, fitas JSONL, guarda de orçamento como serviço que pausa o mundo, chave no `.env`, `make llm-smoke`, CI sem rede | M9 | plano do M9; contratos §8.5, §12.1 |
| [0059](0059-decisoes-do-plano-do-m10.md) | Decisões do M10: a mente como biblioteca genérica (`libs/mind`), dados dos cartuchos em camadas (catálogo e notas no gênero, cartão de identidade no cenário, entry point `campsverso.minds`), janela de conversa que segue a política da percepção (foto abre, delta é `tool_result`, sem memória até o M11), uma ferramenta estrita por ação com `intent`, JSON cru, prompt em português, recusa como `is_error`, o mundo não espera o modelo, posse por comando com usuário NATS `mind` e fallback ao script após três falhas, `minds:` no mundo (Haiku 5.5, `effort: low`), fita magra de um dia, intenção na tela | M10 | plano do M10; bíblia §2; ADR-0056, ADR-0058 |
| [0060](0060-decisoes-do-plano-do-m11.md) | Decisões do M11: `MemoryPort` com registrar, lembrar e refletir; adaptador SQLite por avatar, sem vetores; a memória mora na mente; episódios sem chamada ao modelo, com importância por tabela; a anotação como parâmetro `note` de toda ferramenta; o bloco de memória na abertura de cada janela; a reflexão uma vez por dia, ao dormir, como ferramenta estrita; crenças com confiança, evidência e origem; cinco eventos `memory.*`; o caderno no painel do operador; Hindsight avaliado e adiado | M11 | plano do M11; contratos §8.4; tempo §9.1; pesquisa §7 |
| [0061](0061-decisoes-do-plano-do-m12.md) | Decisões do M12: a arena em processo sobre o `make corrida` (o mundo espera o modelo por construção); mesmo mundo e mesma seed, três seeds a mais para o Haiku com memória; script × Haiku sem memória × Haiku com memória × Haiku sem a regra, por 30 dias, sem o Sonnet; a tabela da bíblia §13 lado a lado; "descobriu o leste" pelo dado da memória (primeira anotação, primeira crença e a trajetória da confiança); `make arena-report` em `docs/arena/`; Langfuse, OpenTelemetry e OpenRouter adiados | M12 | plano do M12; plano macro (decisão 3); tempo §6; pesquisa §13 |
| [0062](0062-decisoes-do-plano-do-m13.md) | Decisões do M13, a fazenda 2 "Fazenda Boa Vista": três marcos (M13 fazenda 2, M14 segunda rodada da arena, M15 fechamento); o cenário `farm_boavista` estendendo `farm_camps`; sete culturas com duas regras ocultas por cultura; canteiros a partir do zero com a pá; peso e capacidade; mercado que satura e ciclo do quiosque; adubo; fogão e receitas; validade e murcha da madura; andar gasta energia; o fazendeiro-script 2; o manual cala o oculto; métricas novas; arte LPC; quatro primitivas genéricas no kernel | M13 | plano do M13; ADR-0025; ADR-0031; ADR-0061 |
| [0063](0063-decisoes-do-plano-do-m14.md) | Decisões do M14, a segunda rodada da arena na Fazenda Boa Vista: script 2, Haiku com memória em quatro seeds e sem a regra, Sonnet e Opus, todos no mesmo mundo, manual e memória; dias e teto de orçamento por corrida (Sonnet 1,50/25, Opus 2,50/35; 30 dias com os tetos como seguro, a confirmar na hora de rodar); a seed base para Sonnet e Opus; `make arena RODADA=boavista`; a reserva da corrida ao começar; o relatório com os grupos do mundo, as linhas da bíblia 2 §13, "descobriu o rio" e uma linha por regra oculta; a arte própria durante as corridas; o humano fora da tabela | M14 | plano do M14; ADR-0061; ADR-0062 |
| [0064](0064-a-v0-3-e-a-fazenda-sofisticada.md) | A v0.3 é a fazenda sofisticada; o escritório vai para a v0.4 e o estúdio para a v0.5 (substitui a ordem da ADR-0055); a fazenda constrói o que os três pedem (vários avatares, remover entidade, replay na tela, encomendas, rótulos de eventos) e tem corte | fechamento do M14 | ADR-0055; análise da ordem; plano macro da v0.3 |
| [0065](0065-decisoes-do-plano-do-m15.md) | Decisões do M15, o fechamento da v0.2: os critérios B1 a B8 (os "pronto quando" do M8 ao M14 e os princípios) com a resposta à pergunta da versão; a evidência no código final (dois soaks, `make check` em UTC, `make ui-e2e` nos dois mundos, uma chamada real); o `futuro.md` revisto; "a v0.2 em números" com o custo de API; a tag `v0.2.0` com o ok; as vinte decisões da v0.3 revistas quando ela começar (ADR-0066) | M15 | plano do M15; ADR-0054; ADR-0064 |
| [0066](0066-decisoes-do-plano-macro-da-v0-3.md) | As vinte decisões da v0.3, revistas pelo usuário: sete marcos numa ordem nova (a Morada do Sol, ver e assistir, a economia, os controladores e a medição, os ajudantes, a terceira arena, o fechamento), com o visual antes das outras famílias e uma rodada do humano em cada versão; o ano acelerado com as quatro estações; regras ocultas fixas e o mapa que varia; o módulo de economia reaproveitável; cinco ajudantes com ficha; assistir as corridas ao vivo numa visão arena; US$ 150 de API | começo da v0.3 | plano macro da v0.3; ADR-0064; ADR-0065 |
| [0067](0067-decisoes-do-plano-do-m16.md) | Decisões do M16, a Fazenda Morada do Sol: o cenário estendendo a Boa Vista; o mapa de 64 × 40 com raio de 12 tiles e a câmera; a primitiva `despawn` no kernel; canteiros sem teto que voltam a ser grama; o calendário genérico no kernel com o ano de 28 dias declarado só pela Morada do Sol; a afinidade cultura × estação; quatro culturas novas; as regras R-001 a R-003; o script 2 mais sofisticado; a lembrança do que se viu (`out_of_view`, os lugares na `MemoryPort`) | M16 | plano do M16; ADR-0025; ADR-0056; ADR-0060; ADR-0066 |
| [0068](0068-decisoes-do-plano-do-m17.md) | Decisões do M17, ver e assistir: o raio pela fase e pela lanterna na percepção; a névoa como nuvem, com o desenho congelado sob o cinza; assistir lendo os fatos (o gateway no modo de assistir, no lugar do `at_tick`); a arena gravando por partes; a grade de 4 a 6 corridas no canvas 2D; a velocidade da reprodução; os menus do humano com a fila na tela; o teclado com explicação; os rótulos de eventos do cartucho; a lanterna | M17 | plano do M17; ADR-0056; ADR-0061; ADR-0067 |
| [0069](0069-decisoes-do-plano-do-m18.md) | Decisões do M18, a economia: a biblioteca `libs/economy` (mercado, encomendas, agenda), opcional para cada mundo; o clima de mundo aberto em `libs/climate`, separado; o domínio `economy`; a venda com memória e a compra que sobe; a referência pela estação e a oscilação; as encomendas com a reputação (R-004); a feira; o tacho e a composteira; a previsão, a tempestade e a seca; os números todos nos dados do cenário | M18 | plano do M18; ADR-0062; ADR-0066; ADR-0067 |
| [0070](0070-decisoes-do-plano-do-m19.md) | Decisões do M19, os controladores e a medição: as variantes do mapa por receita (a, b, c e a d reservada), escolhidas pelo arquivo do mundo; o fazendeiro-script 3 (modelo bayesiano e amostragem de Thompson sobre atributos genéricos, com distratores) e o oráculo; o caderno de campo e o experimento da noite; o corte do resumo da reflexão; as métricas de exploração no avaliador; a prova antes e depois; o juiz Opus conferido contra um gabarito feito à mão e contra controles; na implementação, a fome da Morada do Sol em 2 por hora e as regras de sobrevivência explícitas | M19 | plano do M19; ADR-0060; ADR-0061; ADR-0066; ADR-0069 |

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
