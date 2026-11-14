# Critérios de aceite da v0.3

Conferidos em 14/nov/2026, no fechamento do M22. Cada critério é o "pronto quando" de um marco do [plano macro](planos/v0.3-macro.md), mais um para os princípios e um para o custo (ADR-0076). Todos têm a evidência e o resultado.

- **Os testes automáticos** rodam no `make check`, na máquina local e no CI, a cada push. No fechamento, o `make check` rodou com `TZ=UTC`, como no CI, e deu verde:
  - 655 testes em Python, 90 da tela e 3 dos contratos;
  - 14 contratos de arquitetura mantidos;
  - 73 tipos de contrato, com 83 exemplos válidos e 20 inválidos recusados nos dois validadores.
- **O `make ui-e2e`** passou 6 de 6 no navegador, nos três servidores: a fazenda 1, a Morada do Sol e uma rodada sintética da arena no modo de assistir.
- **Os soaks** rodaram no código final, num MacBook Pro M3, no modo máximo, com processos e NATS próprios (`make soak`, um por mundo, e a Morada do Sol nos mapas a e d).
- **As corridas com modelo** rodaram em processo, com o mundo esperando cada resposta (ADR-0061). O CI nunca chama a API: os testes da mente reproduzem as fitas de `tests/fixtures/llm/`.

| # | Critério | Evidência | Resultado |
|---|---|---|---|
| C1 | **M16:** a fazenda 1 e a Boa Vista intactas; o script 2 adaptado vive um ano na Morada do Sol | soaks `data/soak/20261114-122106` (fazenda 1), `-122148` (Boa Vista), `-122228` (Morada do Sol, mapa a) e `-122303` (mapa d) | ok: a fazenda 1 repete 1.175 moedas, e a Boa Vista 220. O script 2 vive o ano de 28 dias da Morada do Sol com 85 moedas, 38 colheitas, 54 plantios e 16 canteiros, sem desmaio nem recusa, nos dois mapas. É a régua dele na bíblia 3 (§19) |
| C2 | **M17:** uma corrida assistida ao vivo e outra gravada, na visão arena | `make ui-e2e` (o teste "a arena mostra as duas corridas, acelera e abre uma", na rodada sintética); `make assistir` sobre a rodada do M21 em 14/nov, com o Astra consertado rodando | ok: a rodada gravada abre, acelera e entra numa corrida; o Astra consertado apareceu como "ao vivo" ao lado das 45 corridas gravadas |
| C3 | **M18:** o script 2 adaptado vive um ano com a economia; a mente entende as encomendas pela fita | os soaks da Morada de C1; `test_dois_dias_do_camps_na_morada_do_sol_pela_fita` (67 chamadas gravadas) | ok: o ano de C1 tem o mercado, as encomendas, a feira e o clima ligados, com 19 vendas e nenhuma abaixo do piso; a fita passa no `make check` |
| C4 | **M19:** o script 3 descobre as regras por experimento em mapas diferentes; o oráculo dá o teto | as réguas nos quatro mapas (bíblia 3, §19) e "O que o script 3 aprendeu" no [relatório do M21](arena/m21-terceira-energia.md) | em parte: o script 3 aprende a fadiga do solo nos quatro mapas (de 0,49 a 0,61) e a água só no mapa d (1,43). Não mede o adubo, porque não aduba. O oráculo dá o teto: 247, 817, 300 e 1.113 moedas nos mapas a, b, c e d |
| C5 | **M20:** um ajudante contratado trabalha um ano, como o critério ficou no M20: a contratação forçada, sem travar, com as recusas esperadas, e o replay de um dia com dois avatares igual ao arquivo | a rodada `ajudantes` ([2026-10-26](arena/2026-10-26.md), ADR-0073); `test_o_script_3_contrata_e_o_dia_com_dois_avatares_se_reproduz` | ok: 20 corridas de um ano nos mapas a e b; os ajudantes regaram e colheram sem travar, e o dia com dois avatares se reproduz. A medida mostrou que, nesta Morada, o ajudante não paga (ADR-0073) |
| C6 | **M21:** o relatório compara todos, com o valor de aprender | [docs/arena/m21-terceira-energia.md](arena/m21-terceira-energia.md) | ok: 46 corridas, entre elas os scripts, o oráculo, o humano, seis modelos de três famílias, os braços do Haiku e o procedimento; o valor de saber e a fração capturada no mapa d; dois juízes; e o Astra consertado (ADR-0076) |
| C7 | **Os princípios continuam valendo:** arquitetura, contratos, determinismo e replay nos três mundos; a regra oculta fora do manual, do catálogo e do procedimento | `make check` (`import-linter`, `dependency-cruiser`, os dois validadores, `make compat`); `test_a4_mesma_seed_mesmo_hash_pelo_ciclo_inteiro` e `test_replay_reproduz_a_sessao_gravada` nas três fazendas; `test_o_manual_conta_o_visivel_e_cala_o_oculto` (as notas, o catálogo, o procedimento, a comparação, o conselheiro e o caderno da Morada), `test_as_notas_contam_o_visivel_e_calam_o_oculto` (Boa Vista), `test_as_notas_nao_contam_a_regra_oculta` e `test_o_cartao_nao_conta_a_regra_oculta`; o teste "o jogador vê só o que o Camps vê" no navegador | ok: 14 contratos de arquitetura mantidos; nenhuma mudança incompatível em 80 schemas; o mesmo hash pela seed nas três fazendas; nada oculto chega à foto nem ao texto da mente |
| C8 | **O custo:** a v0.3 dentro do teto de US$ 300 (ADR-0074, decisão 21) | o custo de cada marco no "Como ficou" do plano dele; `docs/custos/creditos.csv` | ok: cerca de US$ 266 de API na versão: US$ 0,32 do M16 ao M18 (as fitas e a corrida de verificação), uns US$ 6,60 no M19 com o agricultor treinado, US$ 0,10 no M20, uns US$ 247 no M21 e uns US$ 12,40 no M22 |

## Os soaks

| | Fazenda do Camps (`farm-camps-01`) | Fazenda Boa Vista (`farm-boavista-01`) | Morada do Sol, mapa a (`farm-morada-do-sol-01`) | Morada do Sol, mapa d (`farm-morada-do-sol-04`) |
|---|---|---|---|---|
| Pasta | `data/soak/20261114-122106` | `data/soak/20261114-122148` | `data/soak/20261114-122228` | `data/soak/20261114-122303` |
| Controlador | fazendeiro-script 1 | fazendeiro-script 2 | fazendeiro-script 2 adaptado | fazendeiro-script 2 adaptado |
| Dias | 30 | 30 | 28 (um ano) | 28 (um ano) |
| Moedas no fim | 1.175 | 220 | 85 | 85 |
| Colheitas | 112 no leste, 72 no oeste | 141 | 38 | 38 |
| Desmaios e recusas | 0 e 0 | 0 e 0 | 0 e 0 | 0 e 0 |

O script 2 não sabe as regras e cava perto do poço, então faz o mesmo ano nos dois mapas: nenhum plantio cai perto da água. Os quatro soaks repetem os números de referência, e o código da v0.3 não mudou o que os scripts fazem.

## A resposta à pergunta da v0.3

A pergunta era: **num mundo maior, com estações, encomendas e regras escondidas em lugares que pedem exploração, quem aprende o mundo e lucra com o que aprendeu: um modelo, um script que faz experimentos, ou um humano? E quanto vale aprender?**

- **Quanto vale aprender:** depende do mapa. No mapa d, o oráculo, que sabe as regras, fez 1.113 moedas no ano, contra 85 do script 2, que não sabe: 1.028 moedas e 19 dias sem fome. Nos mapas a, b e c, o valor fica entre 162 e 732 moedas.
- **O script que faz experimentos aprende, e não lucra.** O script 3 achou com estatística a fadiga do solo nos quatro mapas e a água no mapa d. Mesmo assim, o ano dele no mapa d não passa do script 2: 84 moedas, com 22 dos 94 plantios na faixa da lagoa. Saber o efeito não basta: ele também precisa mudar a fazenda de lugar, e não muda a tempo.
- **Os modelos grandes lucram, e não aprendem.**
  - Ninguém achou a água pela causa, nem com o procedimento científico do M21.
  - O tamanho do adubo saiu pela causa três vezes, e a fadiga uma.
  - Jogando a economia visível (o mercado, as encomendas, a feira), capturaram até metade do valor de saber no ano do mapa d: o Fable 54% e o Opus 49%, o Sonnet 31%.
  - O Opus plantou 41% na faixa da lagoa, pelo motivo errado: a crença dele diz que aqueles canteiros ficam perto do poço e do quiosque.
- **O modelo barato quase não chega lá.** O Haiku fica em torno de zero na maioria das corridas, com ou sem o procedimento, a ferramenta de comparação ou o conselheiro. A melhor, com o caderno completo, chegou a 15%, e as outras duas repetições do mesmo braço ficaram em 0 e −4%.
- **O humano, que sabia as regras e não o mapa,** plantou tudo na faixa da lagoa desde o primeiro dia e terminou 15 dias com 2 moedas. Saber as regras levou ao lugar certo, não ao caixa.
- **As outras famílias:** o Gemini não roda por um erro do Google no meio da geração. O Astra do M21 respondeu vazio em quase metade das chamadas, por uma tradução nossa. Consertado, o Astra rodou 14 dias no mapa d sem nenhuma resposta sem ação: no dia 14, tinha 187 moedas e 31 colheitas, contra 8 moedas e 23 colheitas do Astra do M21 no mesmo dia, e gastou menos (US$ 10,42 contra 12,05). Também não achou regra nenhuma, não plantou na faixa da lagoa e repetiu a cultura do canteiro em todos os 31 plantios.

**Em uma frase:** aprender e lucrar são habilidades separadas. O script aprende sem lucrar, os modelos grandes lucram sem aprender, e só o oráculo, que sabe, faz os dois.

A v0.4 herda a pergunta de como juntar as duas, com agentes que planejam, lembram e calculam fora do modelo (plano do M22, §7), e a pergunta do harness: o nosso, ou o de cada laboratório (a bancada dos harnesses).
