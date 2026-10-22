# Critérios de aceite da v0.2

Conferidos em 21/out/2026, no fechamento do M15. Cada critério é o "pronto quando" de um marco do [plano macro](planos/v0.2-macro.md), mais um critério para os princípios. Todos têm a evidência e o resultado.

- **Os testes automáticos** rodam no `make check`, na máquina local e no CI, a cada push. No fechamento, o `make check` rodou com `TZ=UTC`, como no CI. Deu verde com 381 testes em Python, 44 da tela, 3 dos contratos e 12 contratos de arquitetura.
- **Os soaks** rodaram no código final, num MacBook Pro M3, no modo máximo, com processos e NATS próprios (`make soak DAYS=30`, um por mundo).
- **As corridas com modelo** rodaram em processo, com o mundo esperando cada resposta (ADR-0061). O CI nunca chama a API: os testes da mente reproduzem as fitas de `tests/fixtures/llm/`.

| # | Critério | Evidência | Resultado |
|---|---|---|---|
| B1 | **M8:** um script sobrevive 30 dias com as regras novas, e a foto e o delta cabem num orçamento de tokens medido | soak `data/soak/20261021-214938` (fazenda 1); `make percepcao` sobre o arquivo dele | ok: 30 dias em 33,4 s, sem recusa nem desmaio, 1.175 moedas, pico de fome 79; a foto média tem 5,1 KB, e o dia custa uns 63 mil tokens com deltas contra 232 mil só com fotos (2,1 caracteres por token, calibrado no M9) |
| B2 | **M9:** uma chamada real e uma gravada passam pelo mesmo contrato, e estourar o teto pausa o mundo | `make llm-smoke` no fechamento; `test_fita_grava_e_reproduz_pelo_hash_do_pedido`, `test_estourar_o_teto_do_dia_pausa_o_mundo_e_o_gasto_sobrevive_a_uma_queda`, `test_a_corrida_para_no_teto_de_orcamento` | ok: Haiku 5.5, 532 tokens de entrada e 137 de saída, US$ 0,00012, 4,1 s, `charged: true`; o mesmo pedido volta da fita com `charged: false`, validado pelo mesmo schema `llm.call.completed.v1` |
| B3 | **M10:** o LLM vive 7 dias simulados sem intervenção, dentro do orçamento | os 7 dias no sandbox do M10, a 72×; as 13 corridas de 30 dias com modelo nas duas arenas | ok: 7 dias por US$ 0,14 (US$ 0,020 por dia, com teto de 0,60); nas arenas, as 13 corridas completaram 30 dias, nenhuma desistiu, nenhuma bateu no teto, e só 3 de 17 mil chamadas falharam |
| B4 | **M11:** a memória sobrevive a um reinício, e uma reflexão cita fatos do arquivo de eventos | `test_a_memoria_sobrevive_a_um_reinicio_da_mente`, `test_a_memoria_sobrevive_a_um_reinicio`, `test_dois_dias_do_camps_pela_fita` (as horas citadas nas evidências das crenças existem no arquivo) | ok; nas arenas, as crenças aparecem com as evidências em [2026-10-19](arena/2026-10-19.md) e [2026-10-20](arena/2026-10-20.md) |
| B5 | **M12:** o relatório compara script, Haiku com e sem memória e o controle em 30 dias, com quem descobriu o leste | [docs/arena/2026-10-19.md](arena/2026-10-19.md) | ok: sete corridas de 30 dias, a tabela da bíblia lado a lado e a seção "Quem descobriu o leste" |
| B6 | **M13:** o script 2 vive 30 dias na Boa Vista; a mente joga nela com o manual novo; a fazenda 1 fica intacta | soak `data/soak/20261021-215018` (Boa Vista); `test_dois_dias_do_camps_na_boa_vista_pela_fita`; os testes da fazenda 1 e o soak de B1 | ok: 30 dias em 31,3 s, sem recusa nem desmaio, 220 moedas, 141 colheitas, 16 canteiros cavados; a fita da Boa Vista (57 chamadas) passa no `make check`; a fazenda 1 repete os números da v0.1 (1.175 moedas, leste em 2,0 dias e oeste em 3,0) |
| B7 | **M14:** o relatório compara os modelos onde as decisões custam | [docs/arena/2026-10-20.md](arena/2026-10-20.md) | ok: oito corridas de 30 dias, com script 2, Haiku em quatro seeds, o controle sem a regra, Sonnet e Opus |
| B8 | **Os princípios continuam valendo:** arquitetura, contratos, determinismo e replay nos dois mundos, e a regra oculta fora do manual e do catálogo | `make check` (`import-linter`, `dependency-cruiser`, os dois validadores, `make compat`); `test_a4_mesma_seed_mesmo_hash_pelo_ciclo_inteiro` e `test_replay_reproduz_a_sessao_gravada` nos dois mundos; `test_as_notas_nao_contam_a_regra_oculta`, `test_o_cartao_nao_conta_a_regra_oculta`, `test_as_notas_contam_o_visivel_e_calam_o_oculto` (notas e descrições das ferramentas); `make ui-e2e` nos dois mundos | ok: 12 contratos de arquitetura mantidos; 60 tipos, 66 exemplos válidos e 19 inválidos nos dois validadores; nenhuma mudança incompatível; o mesmo hash pela seed nos dois mundos; `make ui-e2e` com 3 de 3 em cada mundo |

## Os dois soaks de 30 dias

| | Fazenda do Camps (`farm-camps-01`) | Fazenda Boa Vista (`farm-boavista-01`) |
|---|---|---|
| Pasta | `data/soak/20261021-214938` | `data/soak/20261021-215018` |
| Controlador | fazendeiro-script 1 | fazendeiro-script 2 |
| Tempo real | 33,4 s (1,05 s por dia) | 31,3 s (1,00 s por dia) |
| Moedas no fim | 1.175 | 220 |
| Colheitas | 112 no leste, 72 no oeste | 141, todas fora da faixa do rio |
| Dias até amadurecer | 2,0 no leste, 3,0 no oeste | 3,15 |
| Canteiros cavados, ferramentas | (canteiros fixos) | 16 canteiros; o regador grande |
| Murchas, desmaios, recusas | 0, 0, 0 | 0, 0, 0 |
| Pico de fome | 78,9 | 91,1 |
| Memória máxima | 104 MB (kernel) | 104 MB (kernel) |

Os dois soaks repetem os números de referência: a fazenda 1 os da v0.1 e a Boa Vista os do M13. O código da v0.2 não mudou o que os scripts fazem.

## A resposta à pergunta da v0.2

A pergunta era: **"Um LLM consegue viver na Fazenda do Camps, sobreviver, prosperar e descobrir sozinho a regra oculta do rio?"**

- **Viver e sobreviver: sim.** As 13 corridas de 30 dias terminaram sem intervenção e dentro do teto.
- **Prosperar: sim, onde o mundo deixa.**
  - Na fazenda 1, o Haiku com memória passou o fazendeiro-script em moedas em três de quatro seeds: 1.340, 1.225 e 1.185, contra 1.175.
  - Na Boa Vista, onde as decisões custam, os modelos se separaram:
    - o Opus fez 1.143 moedas, cinco vezes as 220 do script 2;
    - o Sonnet fez 18;
    - o Haiku quebrou nas quatro seeds, com 0 a 5 moedas.
- **Descobrir a regra: não.**
  - Na fazenda 1, crenças sobre o leste apareceram em três das quatro seeds com memória, mas nenhuma mudou o plantio: depois do dia 3, entre 42% e 56% dos plantios ficaram no leste, contra 60% do script, que planta em todos os canteiros.
  - Na Boa Vista, ninguém cavou na faixa do rio, e a regra nunca agiu.
  - Memória guarda; não faz ciência.
- **O humano** ficou como referência qualitativa: ninguém jogou uma tarde inteira gravada.
- **Outros modelos:** só Claude (Haiku, Sonnet e Opus). As outras famílias, pela OpenRouter, ficaram para a v0.3.

A v0.3 herda a pergunta da descoberta: canteiros sem teto, um mapa que pede exploração, um fazendeiro-script que faz experimentos e um oráculo que diz quanto vale descobrir ([plano macro da v0.3](planos/v0.3-macro.md)).
