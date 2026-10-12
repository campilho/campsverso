# Critérios de aceite da v0.1

Conferidos em 12/out/2026, no fechamento do M7 (escopo §8; ADR-0054). Cada critério tem a evidência e o resultado.

- **Os testes automáticos** rodam no `make check`, na máquina local e no CI, a cada push.
- **O CI ficou verde por engano** de 11/out à noite até 12/out (ver o diário de 12/out, M6). Desde o run [38308340293](https://github.com/campilho/campsverso/actions/runs/38308340293), ele é verde de verdade: `make check` com `pipefail` e o teste de fumaça da tela, num Linux limpo.
- **Os soaks** rodaram num MacBook Pro M3, no modo máximo, com processos e NATS próprios (`make soak DAYS=30`).

| # | Critério | Evidência | Resultado |
|---|---|---|---|
| A1 | Contratos são a única dependência compartilhada | `import-linter` (10 contratos de arquitetura) e `dependency-cruiser` no `make check` | ok: 10 mantidos, 0 quebrados; nenhuma violação no TypeScript |
| A2 | Todo evento publicado valida contra seu schema | validação no publicador (`validate_events: true`) e nos testes; 55 exemplos válidos e 13 inválidos nos dois validadores (`jsonschema` e `ajv`) | ok |
| A3 | 30 dias com o script, em modo máximo, sem erro e sem intervenção | soak `data/soak/20261012-181416`; no CI, `test_a3_tres_dias_sem_intervencao_e_a5_replay_pelo_kernel` | ok: 30 dias em 35,3 s, sem erro; memória máxima de 57,5 MB (kernel) |
| A4 | Mesma seed e mesmos comandos dão o mesmo resultado | `test_a4_mesma_seed_mesmo_hash_pelo_ciclo_inteiro`, `test_a4_duas_execucoes_com_processos_dao_o_mesmo_hash`, `test_mesma_seed_e_mesmos_comandos_dao_o_mesmo_hash` | ok: o mesmo hash do conteúdo dos eventos |
| A5 | Reexecutar um dia gravado reproduz os mesmos eventos | `test_a5_reexecutar_um_dia_reproduz_o_arquivo`; `make replay DAY=N` | ok: o mesmo hash do dia original |
| A6 | Derrubar gateway, arquivador ou percepção não derruba o kernel; ao voltarem, retomam do ponto certo | `test_gateway_visoes_comandos_e_a6`, `test_a6_arquivador_cai_e_volta_sem_perder_nem_repetir`, `test_a6_percepcao_cai_e_volta_sem_derrubar_o_kernel`, todos com `kill -9` | ok: o gateway volta com a mesma projeção de quem nunca caiu; o arquivo não perde nem repete; a percepção não repete fotos |
| A7 | Queda do kernel não perde nem duplica eventos | `test_a7_kill_9_no_kernel_no_meio_do_dia` | ok: `seq` contínuo depois do `kill -9` |
| A8 | O controlador não consegue assinar `internal` | `test_a8_controlador_nao_assina_internal_nem_world`, `test_a8_controlador_nao_cria_consumidor_no_stream_internal` | ok: o NATS nega pela permissão do usuário |
| A9 | Humano assume, joga, devolve; comandos de quem não tem a posse são recusados | `test_a9_humano_assume_joga_e_devolve`, `test_a9_humano_joga_pela_ui_e_devolve`, `make ui-e2e`; as partidas do usuário no M5 e no M6 | ok: `not_in_control` para o script enquanto o humano joga |
| A10 | O script sobrevive 30 dias e termina com mais moedas do que começou | os dois soaks de 30 dias | ok: de 100 para 1.175 moedas com a regra e para 750 sem ela |
| A11 | As métricas mostram o leste amadurecendo mais rápido | `make metrics` dos dois soaks; o painel do operador mostra as colheitas por grupo a cada dia | ok: com a regra, leste amadurece em 2,0 dias e o oeste em 3,0, e são 112 colheitas no leste contra 72 no oeste; sem a regra, 3,0 dias e 72 colheitas nos dois |

## Os dois soaks de 30 dias

| | Com a regra oculta (R-001) | Sem a regra |
|---|---|---|
| Pasta | `data/soak/20261012-181416` | `data/soak/20261012-181456` |
| Tempo real | 35,3 s (1,07 s por dia) | 38,2 s (1,16 s por dia) |
| Moedas no fim | 1.175 | 750 |
| Colheitas leste / oeste | 112 / 72 | 72 / 72 |
| Dias até amadurecer leste / oeste | 2,0 / 3,0 | 3,0 / 3,0 |
| Plantas murchas, desmaios, recusas | 0, 0, 0 | 0, 0, 0 |
| Pico de fome | 79,1 | 100 |
| Arquivo | 6,8 MB (comprimido) | parecido |

- **Sem a regra, a fome encosta em 100,** porque a reserva de rabanetes do script não cobre os dias sem colheita. Fome em 100 ainda não tem consequência. Isso está anotado em `docs/planos/futuro.md`.
- **No modo máximo, um dia simulado custa cerca de 1,1 s,** e o arquivo cresce cerca de 0,23 MB por dia simulado.
