# ADR-0091 — Os testes em paralelo e o check de cada commit

**Status:** aceita · **Data:** 2026-11-22 · **Marco:** M26
**Complementa:** ADR-0035 (o CI roda o `make check` a cada push e pull request)

## Contexto

Em 22/nov, o usuário mediu o custo do dia: cada passo de programação esperava de 20 a 30 minutos, entre o `make check` local antes do commit e o CI depois do push. O GitHub rodou o CI 10 vezes nesse dia.

A medição, nesta máquina (11 núcleos):

| Parte do `make check` | Tempo |
|---|---|
| `ruff` e `eslint` | 7 s |
| `pyright` e `tsc` | 11 s |
| Arquitetura, contratos e compatibilidade | 9 s |
| `vitest` (a tela) | uns segundos |
| **pytest, em série** | **10min47s** |

- **O gargalo é o pytest,** que usava um núcleo só.
- **Dentro dele, os 91 testes de `tests/e2e` comem quase todo o tempo.** Os dois mais lentos, o mapa d e o script 3 das fazendas, levam um minuto cada. Os outros 854 testes rodam em 94 s.
- **Em paralelo, com 8 processos:** tudo em 3min30s; sem os e2e, 27 s.

Os testes já estavam prontos para o paralelo: as portas vêm do sistema (`bind` na porta 0), e as pastas são temporárias. Nenhum teste precisou mudar.

Um teste caiu na primeira rodada completa, mas não pelo paralelo: o robô do briefing escolhe arquivos do repositório pelo nome, com empate pela ordem alfabética, e a própria ADR-0091 e uma foto do teste do navegador (`apps/ui/test-results/`, fora do git) passaram na frente do `tools/robos/testador.py`. O briefing passou a pular as pastas de resultado de teste, e o empate frágil foi para o `futuro.md`.

## Decisão

1. **O pytest roda em paralelo,** aqui e no CI.
   - Usa o `pytest-xdist`, no grupo `dev`, travado no lock, com um processo por núcleo (`-n auto`).
   - O `--dist worksteal` reparte o trabalho de novo quando um processo pega os e2e lentos.
   - `PYTEST_N=0` roda num processo só, para depurar um teste.
   - Rodar o `pytest` direto (`uv run pytest caminho`) continua em série: o paralelo mora no Makefile, e não no `addopts`.
2. **O `make check-rapido` vem antes de cada commit.** Ele é o `make check` sem os e2e de `tests/e2e`: lint, tipos, arquitetura, contratos, compatibilidade, o resto do pytest e a tela. Leva cerca de 1 minuto. Antes, a regra era o `make check` completo a cada commit.
3. **O `make check` completo vem antes de cada push,** e o `make ui-e2e` vem antes do push que leva mudança de tela, no fim do dia. Se o completo pegar algo que o rápido deixou passar, o conserto vai num commit novo antes do push. Nunca sobe push vermelho.
4. **O CI usa o mesmo paralelo,** sem passo novo: o `make check` do CI chama o mesmo `make test`, e o `-n auto` usa os 4 núcleos da máquina do GitHub.
5. **Ninguém espera o CI depois do push.** O trabalho segue, e o CI é conferido na próxima parada natural. Só duas coisas dependem dele:
   - a mesclagem de um PR;
   - a troca do escritório vivo, que o supervisor só faz com o CI verde (ADR-0083).

## Consequências

- **Cada passo de programação espera cerca de 1 minuto,** e não uns 12. O primeiro `make check-rapido` levou 69 s, com 856 testes do pytest em 35 s.
- **O check completo antes do push** cai de uns 11 minutos para 174 s, com o pytest em 157 s, nos 11 processos desta máquina.
- **O CI:** a estimativa é que os 13 a 19 minutos do `make check` caiam para uns 6 a 8, a conferir no primeiro push.
- **Os e2e de `tests/e2e` só rodam antes do push e no CI.** Um commit do meio do dia pode ter um e2e vermelho; ele é consertado antes do push.
- **Um teste pode oscilar sob a carga do paralelo,** como o do gateway já oscilou sozinho. Se isso acontecer, ele ganha uma marca e passa a rodar num passo próprio, em série, depois dos outros.
- **As fixtures de sessão e de módulo rodam uma vez por processo,** e não uma vez no total. Hoje nenhuma é cara o bastante para pesar.
- **A oficina do dev não muda.** O testador chama o `pytest` direto, em série, no espaço do pedido. O CI dos PRs do dev fica mais rápido junto com o do `main`.
