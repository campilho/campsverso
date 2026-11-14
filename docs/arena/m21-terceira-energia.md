# Arena de m21-terceira-energia

46 corrida(s) de até 28 dias em processo, no mesmo mundo (`farm-morada-do-sol-01`), nos mapas a, b, c, d, com o mundo esperando o modelo por construção (ADR-0061). Gerado por `make arena-report` a partir de `data/arena/m21-terceira-energia` (fora do git). A tabela da bíblia §13 é o total dos dias completos de cada corrida; "descobriu o rio" é lido do dado da memória de quem a tem (a primeira anotação e a primeira crença que falam do rio, e a trajetória de cada crença) e do comportamento de todos (canteiros cavados na faixa do rio, e plantios e colheitas nela a partir do dia 4). A corrida sem as regras R-001 e R-003 é o controle.

## As corridas

| Corrida | Controlador | Mapa | Memória | Regras R-001 e R-003 | Seed | Dias | Teto US$ (dia · total) | Tempo real |
|---|---|---|---|---|---|---|---|---|
| script2-a | script 2 | a | não | ligada | 20261022 | 28 | - | 22 s |
| script2-b | script 2 | b | não | ligada | 20261022 | 28 | - | 22 s |
| script2-c | script 2 | c | não | ligada | 20261022 | 28 | - | 22 s |
| script3-a | script 3 | a | não | ligada | 20261022 | 28 | - | 21 s |
| script3-b | script 3 | b | não | ligada | 20261022 | 28 | - | 24 s |
| script3-c | script 3 | c | não | ligada | 20261022 | 28 | - | 20 s |
| oraculo-a | oráculo | a | não | ligada | 20261022 | 28 | - | 31 s |
| oraculo-b | oráculo | b | não | ligada | 20261022 | 28 | - | 34 s |
| oraculo-c | oráculo | c | não | ligada | 20261022 | 28 | - | 33 s |
| humano | humano | d | não | ligada | 20261022 | 15 | - | 275 h 56 min |
| haiku | Claude Haiku 5.5 | d | sim | ligada | 20261022 | 28 | - | 50 min 50 s |
| astra | GPT-6 Astra (flex) | d | sim | ligada | 20261022 | 28 | 5,00 · 70 | 1 h 11 min |
| astra-consertado | GPT-6 Astra (flex) | d | sim | ligada | 20261022 | 14 | 5,00 · 22 | 1 h 03 min |
| astra-consertado-piloto | GPT-6 Astra (flex) | d | sim | ligada | 20261022 | 2 | 4,00 · 8 | 6 min 12 s |
| astra-piloto | GPT-6 Astra (flex) | d | sim | ligada | 20261022 | 2 | 4,00 · 8 | 6 min 28 s |
| astra-procedimento | GPT-6 Astra (flex) com o playbook 4 | d | sim | ligada | 20261022 | 14 | 5,00 · 18 | 50 min 01 s |
| fable | Claude Fable 5.1 | d | sim | ligada | 20261022 | 28 | 10,00 · 110 | 1 h 49 min |
| fable-piloto | Claude Fable 5.1 | d | sim | ligada | 20261022 | 2 | 5,00 · 12 | 7 min 29 s |
| fable-procedimento | Claude Fable 5.1 com o playbook 4 | d | sim | ligada | 20261022 | 14 | 10,00 · 40 | 1 h 00 min |
| gemini | Gemini 4 Argon (flex) | d | sim | ligada | 20261022 | 12 | 0,75 · 15 | 2 h 02 min |
| gemini-piloto | Gemini 4 Argon (flex) | d | sim | ligada | 20261022 | 2 | 0,75 · 2 | 22 min 54 s |
| gemini-procedimento | Gemini 4 Argon (flex) com o playbook 4 | d | sim | ligada | 20261022 | 1 | 1,50 · 7 | 46 min 25 s |
| haiku-comparar | Claude Haiku 5.5 | d | sim | ligada | 20261022 | 28 | - | 41 min 25 s |
| haiku-comparar-r2 | Claude Haiku 5.5 | d | sim | ligada | 20261022 | 28 | - | 58 min 38 s |
| haiku-conselheiro | Claude Haiku 5.5 | d | sim | ligada | 20261022 | 28 | 1,00 · 12 | 1 h 02 min |
| haiku-controle | Claude Haiku 5.5 com o playbook 4 | a | sim | desligada | 20261022 | 28 | 0,60 · 2 | 38 min 22 s |
| haiku-dados | Claude Haiku 5.5 | d | sim | ligada | 20261022 | 28 | 0,60 · 2 | 50 min 32 s |
| haiku-dados-r2 | Claude Haiku 5.5 | d | sim | ligada | 20261022 | 28 | 0,60 · 2 | 1 h 16 min |
| haiku-dados-r3 | Claude Haiku 5.5 | d | sim | ligada | 20261022 | 28 | 0,60 · 2 | 37 min 45 s |
| haiku-openrouter | Claude Haiku 5.5 pela OpenRouter | d | sim | ligada | 20261022 | 2 | 0,60 · 2 | 3 min 40 s |
| haiku-procedimento | Claude Haiku 5.5 com o playbook 4 | d | sim | ligada | 20261022 | 28 | 0,60 · 2 | 40 min 43 s |
| haiku-procedimento-r2 | Claude Haiku 5.5 com o playbook 4 | d | sim | ligada | 20261022 | 28 | 0,60 · 2 | 45 min 02 s |
| haiku-procedimento-r3 | Claude Haiku 5.5 com o playbook 4 | d | sim | ligada | 20261022 | 28 | 0,60 · 2 | 46 min 04 s |
| haiku-r2 | Claude Haiku 5.5 | d | sim | ligada | 20261022 | 28 | - | 49 min 40 s |
| haiku-r3 | Claude Haiku 5.5 | d | sim | ligada | 20261022 | 28 | - | 39 min 59 s |
| opus | Claude Opus 5.5 | d | sim | ligada | 20261022 | 28 | 2,50 · 55 | 1 h 40 min |
| opus-procedimento | Claude Opus 5.5 com o playbook 4 | d | sim | ligada | 20261022 | 14 | 3,00 · 19 | 29 min 45 s |
| oraculo-d | oráculo | d | não | ligada | 20261022 | 28 | - | 34 s |
| script2-d | script 2 | d | não | ligada | 20261022 | 28 | - | 17 s |
| script3-d | script 3 | d | não | ligada | 20261022 | 28 | - | 28 s |
| script3-fixo-a | script 3 fixo | a | não | ligada | 20261022 | 28 | - | 23 s |
| script3-fixo-b | script 3 fixo | b | não | ligada | 20261022 | 28 | - | 23 s |
| script3-fixo-c | script 3 fixo | c | não | ligada | 20261022 | 28 | - | 23 s |
| script3-fixo-d | script 3 fixo | d | não | ligada | 20261022 | 28 | - | 23 s |
| sonnet | Claude Sonnet 5.5 | d | sim | ligada | 20261022 | 28 | 1,50 · 30 | 52 min 02 s |
| sonnet-procedimento | Claude Sonnet 5.5 com o playbook 4 | d | sim | ligada | 20261022 | 14 | 1,50 · 7 | 17 min 20 s |

## A tabela da bíblia §13, lado a lado

| Métrica | script2-a | script2-b | script2-c | script3-a | script3-b | script3-c | oraculo-a | oraculo-b | oraculo-c | humano | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | oraculo-d | script2-d | script3-d | script3-fixo-a | script3-fixo-b | script3-fixo-c | script3-fixo-d | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dias completos | 28 | 28 | 28 | 28 | 28 | 28 | 28 | 28 | 28 | 15 | 28 | 28 | 14 | 2 | 2 | 14 | 28 | 2 | 14 | 12 | 2 | 1 | 28 | 28 | 28 | 28 | 28 | 28 | 28 | 2 | 28 | 28 | 28 | 28 | 28 | 28 | 14 | 28 | 28 | 28 | 28 | 28 | 28 | 28 | 28 | 14 |
| Moedas ao fim | 85 | 85 | 85 | 5 | 119 | 54 | 247 | 817 | 300 | 2 | 1 | 117 | 187 | 69 | 47 | 71 | 641 | 42 | 217 | 1 | 3 | 24 | 9 | 52 | 71 | 8 | 44 | 236 | 0 | 100 | 8 | 4 | 0 | 0 | 5 | 586 | 122 | 1113 | 85 | 84 | 82 | 82 | 82 | 82 | 401 | 62 |
| Colheitas (rio / fora) | 0 / 38 | 0 / 38 | 0 / 38 | 13 / 37 | 48 / 31 | 11 / 47 | 68 / 36 | 117 / 0 | 0 / 90 | 47 / 0 | 0 / 47 | 0 / 71 | 0 / 31 | 0 / 0 | 0 / 0 | 0 / 24 | 0 / 106 | 0 / 0 | 0 / 50 | 0 / 38 | 0 / 0 | 0 / 0 | 0 / 18 | 0 / 57 | 0 / 65 | 0 / 26 | 0 / 42 | 0 / 58 | 0 / 20 | 0 / 0 | 0 / 10 | 0 / 28 | 0 / 29 | 0 / 48 | 0 / 19 | 62 / 94 | 0 / 41 | 117 / 0 | 0 / 38 | 15 / 55 | 0 / 72 | 0 / 72 | 0 / 72 | 0 / 72 | 0 / 74 | 0 / 22 |
| Plantios (rio / fora) | 0 / 54 | 0 / 54 | 0 / 54 | 17 / 46 | 63 / 47 | 17 / 56 | 88 / 36 | 137 / 0 | 0 / 111 | 58 / 0 | 0 / 60 | 0 / 90 | 0 / 51 | 0 / 13 | 0 / 15 | 0 / 39 | 0 / 147 | 0 / 23 | 0 / 89 | 0 / 61 | 0 / 19 | 0 / 10 | 0 / 21 | 0 / 75 | 0 / 82 | 0 / 26 | 0 / 55 | 0 / 73 | 0 / 20 | 0 / 4 | 0 / 15 | 0 / 28 | 0 / 32 | 0 / 55 | 0 / 19 | 81 / 135 | 0 / 64 | 140 / 0 | 0 / 54 | 22 / 72 | 0 / 90 | 0 / 90 | 0 / 90 | 0 / 90 | 0 / 102 | 0 / 32 |
| Dias até amadurecer (rio / fora) | - / 5,5 | - / 5,5 | - / 5,5 | 3,1 / 5,4 | 3,1 / 4,9 | 3,2 / 5,4 | 3,0 / 4,4 | 3,5 / - | - / 4,2 | 4,0 / - | - / 5,3 | - / 5,4 | - / 5,6 | - / - | - / - | - / 5,6 | - / 4,6 | - / - | - / 5,2 | - / 4,2 | - / - | - / - | - / 5,7 | - / 5,5 | - / 5,3 | - / 3,9 | - / 5,5 | - / 5,5 | - / 5,7 | - / - | - / 5,8 | - / 5,6 | - / 5,5 | - / 5,3 | - / 5,6 | 3,4 / 4,7 | - / 5,4 | 3,6 / - | - / 5,5 | 3,0 / 5,2 | - / 5,5 | - / 5,5 | - / 5,5 | - / 5,5 | - / 5,0 | - / 5,5 |
| Canteiros cavados (rio / fora) | 0 / 16 | 0 / 16 | 0 / 16 | 10 / 13 | 14 / 21 | 8 / 18 | 60 / 16 | 64 / 0 | 0 / 73 | 24 / 1 | 0 / 14 | 0 / 23 | 0 / 20 | 0 / 13 | 0 / 15 | 0 / 16 | 0 / 70 | 0 / 23 | 0 / 48 | 0 / 35 | 0 / 19 | 0 / 10 | 0 / 6 | 0 / 19 | 0 / 18 | 0 / 8 | 0 / 13 | 0 / 16 | 0 / 10 | 0 / 4 | 0 / 7 | 0 / 9 | 0 / 7 | 0 / 17 | 0 / 7 | 19 / 38 | 0 / 23 | 64 / 0 | 0 / 16 | 6 / 25 | 0 / 18 | 0 / 18 | 0 / 18 | 0 / 18 | 0 / 30 | 0 / 11 |
| Ferramentas (dia da compra) | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande dia 12, arado - | regador grande dia 20, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande dia 25, arado - | regador grande -, arado - | regador grande -, arado - | regador grande dia 7, arado dia 12 | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande dia 20, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - | regador grande -, arado - |
| Plantios por cultura | rabanete 40, milho 14 | rabanete 40, milho 14 | rabanete 40, milho 14 | rabanete 55, batata 3, mandioca 2, milho 2, melancia 1 | rabanete 78, mandioca 9, batata 6, milho 6, couve 5, alho 3, tomate 3 | rabanete 65, batata 4, milho 2, alho 1, melancia 1 | rabanete 88, milho 15, mandioca 9, couve 5, tomate 4, alho 2, batata 1 | rabanete 72, milho 17, mandioca 14, tomate 13, alho 6, morango 6, batata 5, couve 4 | rabanete 79, mandioca 9, milho 9, alho 6, couve 6, morango 1, tomate 1 | rabanete 42, milho 7, couve 4, cenoura 3, mandioca 2 | rabanete 56, couve 4 | rabanete 90 | rabanete 51 | rabanete 13 | rabanete 15 | rabanete 39 | rabanete 104, milho 16, tomate 10, couve 9, batata 6, alho 2 | rabanete 18, melancia 2, tomate 2, milho 1 | rabanete 65, milho 18, tomate 6 | rabanete 46, milho 10, tomate 3, melancia 2 | rabanete 12, tomate 5, milho 2 | rabanete 10 | rabanete 21 | rabanete 63, milho 4, batata 3, tomate 3, mandioca 2 | rabanete 78, couve 2, milho 2 | rabanete 26 | rabanete 52, batata 3 | rabanete 64, batata 4, milho 3, couve 2 | rabanete 18, tomate 2 | rabanete 4 | rabanete 11, batata 2, milho 2 | rabanete 28 | rabanete 32 | rabanete 51, batata 2, tomate 2 | rabanete 19 | rabanete 166, couve 17, tomate 13, cenoura 10, milho 10 | rabanete 51, milho 7, tomate 6 | rabanete 70, mandioca 18, milho 15, tomate 13, alho 9, batata 5, couve 5, morango 5 | rabanete 40, milho 14 | rabanete 71, mandioca 8, alho 5, couve 5, milho 2, tomate 2, melancia 1 | rabanete 89, alho 1 | rabanete 89, alho 1 | rabanete 89, alho 1 | rabanete 89, alho 1 | rabanete 79, milho 10, tomate 7, cenoura 6 | rabanete 27, milho 5 |
| Refeições (por receita) | - | - | - | - | - | - | - | sopa_de_batata 2 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | sopa_de_batata 2 | - | - | - | - | - | - | - | - |
| Estragos (unidades, por item) | - | - | - | - | rabanete 2 | - | tomate 3, rabanete 1 | rabanete 3 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | couve 1 | - | - | - | - | - | - | - | - | - | rabanete 3, tomate 1 | - | - | - | - | - | - | rabanete 1 | rabanete 2 |
| Murchas da madura | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Vendas (unidades; abaixo de 80% do preço) | 19 (0) | 19 (0) | 19 (0) | 21 (0) | 19 (0) | 23 (0) | 51 (0) | 50 (2) | 44 (0) | 29 (0) | 11 (0) | 23 (0) | 6 (0) | 0 (0) | 0 (0) | 0 (0) | 32 (0) | 0 (0) | 19 (0) | 12 (0) | 0 (0) | 0 (0) | 1 (0) | 18 (0) | 23 (0) | 4 (0) | 3 (0) | 14 (0) | 2 (0) | 0 (0) | 0 (0) | 4 (0) | 5 (0) | 12 (0) | 0 (0) | 54 (0) | 12 (0) | 52 (2) | 19 (0) | 31 (0) | 30 (0) | 30 (0) | 30 (0) | 30 (0) | 33 (0) | 3 (0) |
| Recusas | 0 | 0 | 0 | 0 | 0 | 3 | 52 | 53 | 0 | 64 | 59 | 1 | 1 | 0 | 1 | 0 | 12 | 4 | 5 | 2 | 1 | 0 | 24 | 56 | 49 | 18 | 66 | 71 | 33 | 4 | 70 | 92 | 42 | 46 | 51 | 29 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 124 | 41 |
| Murchas | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pico de fome | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 69 | 100 | 100 | 100 | 92 | 100 | 56 | 38 | 100 | 100 | 67 | 100 | 100 | 70 | 43 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 41 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 69 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| Desmaios | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 6 | 2 | 1 | 3 | 3 | 2 | 2 | 1 | 5 | 6 | 5 | 3 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| Chamadas | - | - | - | - | - | - | - | - | - | - | 1130 | 1872 | 586 | 88 | 156 | 762 | 1731 | 141 | 855 | 648 | 136 | 59 | 742 | 1288 | 1338 | 721 | 1152 | 1215 | 733 | 70 | 763 | 922 | 903 | 1090 | 801 | 2020 | 657 | - | - | - | - | - | - | - | 1603 | 548 |
| Chamadas por dia | - | - | - | - | - | - | - | - | - | - | 40,4 | 66,9 | 41,9 | 44,0 | 78,0 | 54,4 | 61,8 | 70,5 | 61,1 | 54,0 | 68,0 | 59,0 | 26,5 | 46,0 | 47,8 | 25,8 | 41,1 | 43,4 | 26,2 | 35,0 | 27,2 | 32,9 | 32,2 | 38,9 | 28,6 | 72,1 | 46,9 | - | - | - | - | - | - | - | 57,2 | 39,1 |
| Chamadas que falharam | - | - | - | - | - | - | - | - | - | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 14 | 3 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | - | - | - | - | - | - | 0 | 0 |
| Custo (US$) | - | - | - | - | - | - | - | - | - | - | 0,81 | 27,32 | 10,42 | 1,50 | 2,11 | 11,76 | 70,12 | 5,08 | 36,75 | 3,30 | 0,64 | 0,28 | 0,55 | 0,90 | 4,08 | 0,60 | 0,84 | 0,92 | 0,57 | 0,11 | 0,62 | 0,73 | 0,73 | 0,79 | 0,59 | 35,07 | 11,91 | - | - | - | - | - | - | - | 12,14 | 4,40 |
| Custo por dia (US$) | - | - | - | - | - | - | - | - | - | - | 0,029 | 0,976 | 0,744 | 0,748 | 1,055 | 0,840 | 2,505 | 2,542 | 2,625 | 0,275 | 0,318 | 0,275 | 0,020 | 0,032 | 0,146 | 0,021 | 0,030 | 0,033 | 0,020 | 0,055 | 0,022 | 0,026 | 0,026 | 0,028 | 0,021 | 1,252 | 0,851 | - | - | - | - | - | - | - | 0,434 | 0,314 |
| Latência mediana (ms) | - | - | - | - | - | - | - | - | - | - | 1471 | 1966 | 3274 | 3763 | 2143 | 2473 | 2111 | 2036 | 2676 | 5295 | 5431 | 7131 | 1728 | 1602 | 1628 | 1487 | 1347 | 1359 | 1474 | 1881 | 1511 | 1368 | 1419 | 1559 | 1653 | 2358 | 2025 | - | - | - | - | - | - | - | 1694 | 1613 |
| Reflexões | - | - | - | - | - | - | - | - | - | - | 28 | 28 | 14 | 2 | 2 | 14 | 28 | 2 | 14 | 11 | 2 | 0 | 28 | 28 | 28 | 28 | 28 | 28 | 28 | 2 | 28 | 28 | 28 | 28 | 28 | 28 | 14 | - | - | - | - | - | - | - | 28 | 14 |
| Resumos com marcação de ferramenta (na fita) | - | - | - | - | - | - | - | - | - | - | 12 de 28 | 0 de 28 | 0 de 14 | 0 de 2 | 0 de 2 | 0 de 14 | 0 de 28 | 0 de 2 | 0 de 14 | 0 de 11 | 0 de 2 | 0 de 0 | 3 de 28 | 10 de 28 | 7 de 28 | 1 de 29 | 11 de 28 | 9 de 28 | 9 de 28 | 0 de 2 | 4 de 28 | 0 de 28 | 0 de 29 | 11 de 28 | 9 de 28 | 0 de 28 | 0 de 14 | - | - | - | - | - | - | - | 0 de 28 | 0 de 14 |
| Anotações | - | - | - | - | - | - | - | - | - | - | 642 | 95 | 72 | 8 | 5 | 35 | 252 | 26 | 131 | 70 | 13 | 1 | 558 | 606 | 637 | 410 | 652 | 580 | 527 | 35 | 406 | 569 | 527 | 596 | 614 | 277 | 77 | - | - | - | - | - | - | - | 177 | 99 |
| Crenças ao fim (formadas / revisadas / retiradas) | - | - | - | - | - | - | - | - | - | - | 46 (51 / 174 / 6) | 12 (12 / 26 / 0) | 12 (12 / 27 / 0) | 6 (6 / 3 / 0) | 8 (8 / 3 / 0) | 1 (1 / 1 / 0) | 13 (25 / 193 / 12) | 10 (10 / 7 / 0) | 12 (19 / 84 / 7) | 11 (11 / 19 / 0) | 5 (6 / 2 / 1) | 0 (0 / 0 / 0) | 42 (46 / 184 / 4) | 42 (43 / 193 / 1) | 35 (36 / 191 / 1) | 40 (42 / 111 / 2) | 51 (56 / 165 / 5) | 48 (48 / 186 / 0) | 35 (40 / 175 / 5) | 11 (12 / 7 / 1) | 34 (39 / 142 / 5) | 33 (34 / 141 / 1) | 36 (39 / 137 / 3) | 33 (36 / 167 / 3) | 48 (48 / 176 / 0) | 12 (24 / 139 / 13) | 14 (14 / 13 / 0) | - | - | - | - | - | - | - | 21 (21 / 95 / 0) | 8 (8 / 8 / 0) |
| Desistiu (três falhas seguidas) | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | sim, no dia 12 | não | sim, no dia 1 | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não |
| Parou no teto de orçamento | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não |
| Tempo real | 22 s | 22 s | 22 s | 21 s | 24 s | 20 s | 31 s | 34 s | 33 s | 275 h 56 min | 50 min 50 s | 1 h 11 min | 1 h 03 min | 6 min 12 s | 6 min 28 s | 50 min 01 s | 1 h 49 min | 7 min 29 s | 1 h 00 min | 2 h 02 min | 22 min 54 s | 46 min 25 s | 41 min 25 s | 58 min 38 s | 1 h 02 min | 38 min 22 s | 50 min 32 s | 1 h 16 min | 37 min 45 s | 3 min 40 s | 40 min 43 s | 45 min 02 s | 46 min 04 s | 49 min 40 s | 39 min 59 s | 1 h 40 min | 29 min 45 s | 34 s | 17 s | 28 s | 23 s | 23 s | 23 s | 23 s | 52 min 02 s | 17 min 20 s |

### Recusas por motivo

| Motivo | script2-a | script2-b | script2-c | script3-a | script3-b | script3-c | oraculo-a | oraculo-b | oraculo-c | humano | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | oraculo-d | script2-d | script3-d | script3-fixo-a | script3-fixo-b | script3-fixo-c | script3-fixo-d | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| already_there | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 4 | 0 | 0 | 0 | 0 | 0 | 3 | 2 | 0 | 0 | 0 | 0 | 4 | 4 | 7 | 2 | 11 | 6 | 1 | 0 | 2 | 4 | 0 | 3 | 6 | 6 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 27 | 6 |
| busy | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 28 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| can_empty | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| closed | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| insufficient_funds | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 2 | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 |
| invalid_params | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 2 | 2 | 2 | 3 | 0 | 2 | 1 | 6 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| machine_busy | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| missing_ingredients | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| missing_item | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 5 | 1 | 1 | 2 | 0 | 2 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| no_plant | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| not_adjacent | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 30 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 1 | 1 | 0 | 0 | 12 | 41 | 22 | 4 | 24 | 43 | 9 | 2 | 1 | 17 | 13 | 32 | 14 | 19 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 72 | 15 |
| not_grass | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 1 | 0 | 1 | 0 | 2 | 2 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 5 |
| not_passable | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| not_ripe | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 5 | 13 | 2 | 24 | 18 | 16 | 0 | 58 | 66 | 22 | 8 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 11 |
| not_tired | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 3 | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 1 |
| not_your_order | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| plot_occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| too_heavy | 0 | 0 | 0 | 0 | 0 | 0 | 52 | 53 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Quem descobriu o rio

| Sinal | script2-a | script2-b | script2-c | script3-a | script3-b | script3-c | oraculo-a | oraculo-b | oraculo-c | humano | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | oraculo-d | script2-d | script3-d | script3-fixo-a | script3-fixo-b | script3-fixo-c | script3-fixo-d | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Primeira anotação que cita o rio | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | nunca | dia 11, 09:36 | nunca | nunca | nunca | nunca | dia 5, 08:51 | nunca | dia 5, 15:16 | nunca | dia 2, 13:22 | nunca | nunca | nunca | nunca | dia 25, 20:08 | nunca | dia 1, 06:01 | nunca | nunca | dia 28, 19:06 | nunca | dia 1, 06:00 | nunca | dia 25, 06:02 | nunca | nunca | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | nunca | nunca |
| Primeira anotação que nota a vantagem do rio | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | nunca | nunca |
| Primeira crença sobre o rio | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | nunca | nunca | nunca | nunca | nunca | nunca | dia 3 (bel-0011, 0,80) | nunca | dia 9 (bel-0010, 0,45) | nunca | dia 2 (bel-0006, 0,95) | nunca | nunca | nunca | nunca | dia 26 (bel-0039, 0,60) | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | dia 25 (bel-0041, 0,60) | nunca | nunca | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | nunca | nunca |
| Crenças sobre o rio ao fim | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | nenhuma | nenhuma | nenhuma | nenhuma | nenhuma | nenhuma | 1, a mais confiante a 0,97 | nenhuma | 1, a mais confiante a 0,50 | nenhuma | 1, a mais confiante a 0,95 | nenhuma | nenhuma | nenhuma | nenhuma | 2, a mais confiante a 0,60 | nenhuma | nenhuma | nenhuma | nenhuma | nenhuma | nenhuma | nenhuma | nenhuma | 1, a mais confiante a 0,75 | nenhuma | nenhuma | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | sem memória | nenhuma | nenhuma |
| Canteiros cavados na faixa do rio, dias 1 a 3 | 0% (0 de 16) | 0% (0 de 16) | 0% (0 de 16) | 10% (1 de 10) | 50% (6 de 12) | 0% (0 de 10) | 0% (0 de 16) | 100% (16 de 16) | 0% (0 de 16) | 95% (18 de 19) | 0% (0 de 6) | 0% (0 de 10) | 0% (0 de 16) | 0% (0 de 13) | 0% (0 de 15) | 0% (0 de 10) | 0% (0 de 24) | 0% (0 de 23) | 0% (0 de 24) | 0% (0 de 33) | 0% (0 de 19) | 0% (0 de 10) | 0% (0 de 4) | 0% (0 de 14) | 0% (0 de 7) | 0% (0 de 5) | 0% (0 de 10) | 0% (0 de 4) | 0% (0 de 5) | 0% (0 de 4) | 0% (0 de 3) | 0% (0 de 3) | 0% (0 de 7) | 0% (0 de 7) | 0% (0 de 4) | 11% (3 de 28) | 0% (0 de 19) | 100% (16 de 16) | 0% (0 de 16) | 0% (0 de 10) | 0% (0 de 16) | 0% (0 de 16) | 0% (0 de 16) | 0% (0 de 16) | 0% (0 de 11) | 0% (0 de 11) |
| Canteiros cavados na faixa do rio, do dia 4 | - | - | - | 69% (9 de 13) | 35% (8 de 23) | 50% (8 de 16) | 100% (60 de 60) | 100% (48 de 48) | 0% (0 de 57) | 100% (7 de 7) | 0% (0 de 8) | 0% (0 de 13) | 0% (0 de 4) | - | - | 0% (0 de 6) | 0% (0 de 46) | - | 0% (0 de 24) | 0% (0 de 2) | - | - | 0% (0 de 2) | 0% (0 de 5) | 0% (0 de 11) | 0% (0 de 3) | 0% (0 de 3) | 0% (0 de 12) | 0% (0 de 5) | - | 0% (0 de 4) | 0% (0 de 6) | - | 0% (0 de 10) | 0% (0 de 3) | 55% (16 de 29) | 0% (0 de 4) | 100% (48 de 48) | - | 29% (6 de 21) | 0% (0 de 2) | 0% (0 de 2) | 0% (0 de 2) | 0% (0 de 2) | 0% (0 de 19) | - |
| Primeiro canteiro na faixa do rio | nunca | nunca | nunca | dia 1, 08:37 (plot-006) | dia 1, 06:47 (plot-002) | dia 13, 10:23 (plot-017) | dia 5, 09:37 (plot-017) | dia 1, 06:20 (plot-001) | nunca | dia 1, 06:47 (plot-002) | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | nunca | dia 2, 08:26 (plot-017) | nunca | dia 1, 06:20 (plot-001) | nunca | dia 14, 09:01 (plot-017) | nunca | nunca | nunca | nunca | nunca | nunca |
| Plantios na faixa do rio, dias 1 a 3 | 0% (0 de 16) | 0% (0 de 16) | 0% (0 de 16) | 10% (1 de 10) | 65% (11 de 17) | 0% (0 de 10) | 0% (0 de 16) | 100% (18 de 18) | 0% (0 de 16) | 100% (18 de 18) | 0% (0 de 6) | 0% (0 de 10) | 0% (0 de 16) | 0% (0 de 13) | 0% (0 de 15) | 0% (0 de 10) | 0% (0 de 16) | 0% (0 de 23) | 0% (0 de 18) | 0% (0 de 22) | 0% (0 de 19) | 0% (0 de 10) | 0% (0 de 4) | 0% (0 de 14) | 0% (0 de 7) | 0% (0 de 5) | 0% (0 de 10) | 0% (0 de 4) | 0% (0 de 5) | 0% (0 de 4) | 0% (0 de 3) | 0% (0 de 3) | 0% (0 de 7) | 0% (0 de 7) | 0% (0 de 4) | 11% (3 de 28) | 0% (0 de 19) | 100% (18 de 18) | 0% (0 de 16) | 0% (0 de 10) | 0% (0 de 16) | 0% (0 de 16) | 0% (0 de 16) | 0% (0 de 16) | 0% (0 de 11) | 0% (0 de 11) |
| Plantios na faixa do rio, do dia 4 | 0% (0 de 38) | 0% (0 de 38) | 0% (0 de 38) | 30% (16 de 53) | 56% (52 de 93) | 27% (17 de 63) | 81% (88 de 108) | 100% (119 de 119) | 0% (0 de 95) | 100% (40 de 40) | 0% (0 de 54) | 0% (0 de 80) | 0% (0 de 35) | - | - | 0% (0 de 29) | 0% (0 de 131) | - | 0% (0 de 71) | 0% (0 de 39) | - | - | 0% (0 de 17) | 0% (0 de 61) | 0% (0 de 75) | 0% (0 de 21) | 0% (0 de 45) | 0% (0 de 69) | 0% (0 de 15) | - | 0% (0 de 12) | 0% (0 de 25) | 0% (0 de 25) | 0% (0 de 48) | 0% (0 de 15) | 41% (78 de 188) | 0% (0 de 45) | 100% (122 de 122) | 0% (0 de 38) | 26% (22 de 84) | 0% (0 de 74) | 0% (0 de 74) | 0% (0 de 74) | 0% (0 de 74) | 0% (0 de 91) | 0% (0 de 21) |
| Colheitas na faixa do rio, do dia 4 | 0% (0 de 38) | 0% (0 de 38) | 0% (0 de 38) | 26% (13 de 50) | 58% (43 de 74) | 19% (11 de 58) | 65% (68 de 104) | 100% (104 de 104) | 0% (0 de 90) | 100% (40 de 40) | 0% (0 de 47) | 0% (0 de 71) | 0% (0 de 31) | - | - | 0% (0 de 24) | 0% (0 de 106) | - | 0% (0 de 50) | 0% (0 de 38) | - | - | 0% (0 de 18) | 0% (0 de 57) | 0% (0 de 65) | 0% (0 de 26) | 0% (0 de 42) | 0% (0 de 58) | 0% (0 de 20) | - | 0% (0 de 10) | 0% (0 de 28) | 0% (0 de 29) | 0% (0 de 48) | 0% (0 de 19) | 40% (62 de 156) | 0% (0 de 41) | 100% (104 de 104) | 0% (0 de 38) | 21% (15 de 70) | 0% (0 de 72) | 0% (0 de 72) | 0% (0 de 72) | 0% (0 de 72) | 0% (0 de 74) | 0% (0 de 22) |
| Regra oculta: o tomate murcha com um dia seco | sem memória; plantou 0, murcharam 0 | sem memória; plantou 0, murcharam 0 | sem memória; plantou 0, murcharam 0 | sem memória; plantou 0, murcharam 0 | sem memória; plantou 3, murcharam 0 | sem memória; plantou 0, murcharam 0 | sem memória; plantou 4, murcharam 0 | sem memória; plantou 13, murcharam 0 | sem memória; plantou 1, murcharam 0 | sem memória; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 10, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 2, murcharam 0 | anotação dia 14; nenhuma crença; plantou 6, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 3, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 5, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 3, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 2, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 2, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 13, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 6, murcharam 0 | sem memória; plantou 13, murcharam 0 | sem memória; plantou 0, murcharam 0 | sem memória; plantou 2, murcharam 0 | sem memória; plantou 0, murcharam 0 | sem memória; plantou 0, murcharam 0 | sem memória; plantou 0, murcharam 0 | sem memória; plantou 0, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 7, murcharam 0 | nenhuma anotação; nenhuma crença; plantou 0, murcharam 0 |
| Regra oculta: o alho não precisa de rega | sem memória; plantou 0, regou 0 vez(es) | sem memória; plantou 0, regou 0 vez(es) | sem memória; plantou 0, regou 0 vez(es) | sem memória; plantou 0, regou 0 vez(es) | sem memória; plantou 3, regou 11 vez(es) | sem memória; plantou 1, regou 3 vez(es) | sem memória; plantou 2, regou 4 vez(es) | sem memória; plantou 6, regou 24 vez(es) | sem memória; plantou 6, regou 33 vez(es) | sem memória; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 2, regou 10 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | sem memória; plantou 9, regou 36 vez(es) | sem memória; plantou 0, regou 0 vez(es) | sem memória; plantou 5, regou 21 vez(es) | sem memória; plantou 1, regou 5 vez(es) | sem memória; plantou 1, regou 5 vez(es) | sem memória; plantou 1, regou 5 vez(es) | sem memória; plantou 1, regou 5 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) | nenhuma anotação; nenhuma crença; plantou 0, regou 0 vez(es) |
| Regra oculta: o baú conserva | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 2 vez(es) | sem memória; guardou 1 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 2 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 2 vez(es) | nenhuma anotação; nenhuma crença; guardou 2 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 3 vez(es) | nenhuma anotação; nenhuma crença; guardou 3 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 2 vez(es) | nenhuma anotação; nenhuma crença; guardou 5 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 2 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | sem memória; guardou 2 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | sem memória; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) | nenhuma anotação; nenhuma crença; guardou 0 vez(es) |
| Regra oculta: o ensopado sacia por mais tempo | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | sem memória; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) | nenhuma anotação; nenhuma crença; cozinhou 0 ensopado(s) |
| Regra oculta: o adubo e o seu tamanho | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 4 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 2 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 1 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | anotação dia 7; crença dia 7 (0,50); adubou 4 vez(es) | nenhuma anotação; nenhuma crença; adubou 2 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 3 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | sem memória; adubou 0 vez(es) | nenhuma anotação; nenhuma crença; adubou 0 vez(es) | anotação dia 4; nenhuma crença; adubou 1 vez(es) |
| Veredito | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | não | não | não | não | não | não | não | não | não | não | descobriu (bel-0006) | não | não | não | não | não (controle: sem a regra) | não | não | não | não | não | não | não | não | não | não | não | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | só pelo comportamento | não | não |

### haiku: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (46 ativas):

- 0,99 **bel-0005** (dia 6): "O quiosque abre às 08:00 e fecha às 18:00."
- 0,99 **bel-0025** (dia 26): "Pedidos que não são entregues dentro do prazo somem do quadro sem pagamento."
- 0,98 **bel-0013** (dia 28): "Um rabanete tira cerca de 25 de fome, de uma vez."

### astra: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (12 ativas):

- 0,99 **bel-0001** (dia 25): "Cada rega observada consome uma carga sob sol e duas na seca, marcando o canteiro como regado."
- 0,99 **bel-0002** (dia 7): "Reabastecer no poço deixa o regador comum com dez cargas."
- 0,99 **bel-0003** (dia 1): "Plantar rabanete consome uma semente e deixa a cultura no estágio semente."

### astra-consertado: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (12 ativas):

- 0,99 **bel-0001** (dia 2): "Em dia de sol, cada rega observada gasta uma carga e marca o canteiro como regado."
- 0,99 **bel-0002** (dia 4): "Reabastecer no poço completa o regador até dez cargas, mesmo quando ele não está vazio."
- 0,99 **bel-0003** (dia 1): "Plantar rabanete consome uma semente e inicia a planta no estágio semente."

### astra-consertado-piloto: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (6 ativas):

- 0,99 **bel-0001** (dia 2): "Preparar um canteiro com pá, plantar e regar levou 25 minutos por canteiro, sem deslocamento, nos dois dias observados."
- 0,99 **bel-0002** (dia 1): "Cada plantio de rabanete consome uma semente e reduz o peso carregado em 0,1."
- 0,99 **bel-0003** (dia 2): "Em dia de sol, cada rega observada gasta uma carga e marca o canteiro como regado."

### astra-piloto: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (8 ativas):

- 0,99 **bel-0001** (dia 1): "Plantar rabanete em canteiro vazio consome uma semente e deixa a cultura no estágio semente."
- 0,99 **bel-0002** (dia 2): "Em dia ensolarado, cada rega consome uma carga e marca o canteiro como regado."
- 0,99 **bel-0003** (dia 2): "Reabastecer no poço completa o regador até dez cargas, esteja vazio ou parcialmente cheio."

### astra-procedimento: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (1 ativas):

- 0,30 **bel-0001** (dia 14): "Rabanete: a validade exibida de uma pilha misturada indica o vencimento mais próximo, sem encurtar a validade dos novos, quando ficam juntos no inventário; no baú isso ainda precisa de confirmação."

### fable: as crenças sobre o rio

- **bel-0011** (dia 3 a 7, retirada): "Andar custa quase nada; ao norte, sul, sudoeste, nordeste e leste (até x≈60-70) só há grama e árvores; ao sul de y≈30 e a leste de x≈60 não se passa.". Antes: "Andar custa quase nada; ao norte, sul e sudoeste só há grama e árvores, e ao sul de y≈30 (ex.: (20,40)) não se passa, provavelmente o rio.". dia 3 revisada 0,80 → dia 4 revisada 0,80 → dia 5 revisada 0,85 → dia 7 retirada 0,00.
- **bel-0003** (dia 7 a 28, confiança 0,97): "A linha y=22 (x=6-33) é caminho e desce ao quiosque; a grama em y=17-21 em volta do poço se cava (o poço ocupa (14,20)); os canteiros são pisáveis; ao sul de y≈30 e a leste de x≈60 não se passe.". Antes: "A linha y=22 (x=6-33) é caminho e desce ao quiosque; a grama em y=18-21 em volta do poço se cava; os canteiros são pisáveis e se pode cavar no tile onde se está; ao norte, sul e leste só há grama e árvores, e ao sul de y≈30 e a leste de x≈60 não se passa.". dia 7 revisada 0,95 → dia 8 revisada 0,95 → dia 9 revisada 0,95 → dia 14 revisada 0,95 → dia 15 revisada 0,96 → dia 17 revisada 0,96 → dia 19 revisada 0,97 → dia 22 revisada 0,97 → dia 23 revisada 0,97.

As crenças mais confiantes ao fim (13 ativas):

- 0,99 **bel-0001** (dia 23): "Cavar leva 16 minutos (2 de energia), plantar 6, regar 3, encher o regador 4, colher 4, adubar 4, comprar 3, vender 2, comer 11, carregar o tacho 6 e andar ~1 min por tile; plantar e regar gastam perto de 1 de energia cada."
- 0,99 **bel-0004** (dia 25): "Cada rega gasta 1 carga em dia de sol e 2 na seca; na chuva os canteiros com planta amanhecem regados e o plantado durante a chuva nasce com watered_today=true; o poço enche todos os regadores do inventário de uma vez."
- 0,99 **bel-0006** (dia 26): "O quiosque abre às 08:00 e fecha às 18:00; o estoque muda às 06:00 e nem toda semente vem todo dia; a semente de cultura parada some; o preço da semente sobe ~3% por unidade comprada e volta à tabela às 06:00; adubo, regador grande (150) e o resto são fixos."

### fable-piloto: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (10 ativas):

- 0,95 **bel-0002** (dia 2): "O regador tem 10 cargas, uma por canteiro, e enche todo no poço em ~4 minutos."
- 0,95 **bel-0003** (dia 2): "A linha y=22 é caminho, não grama: não dá para cavar nela."
- 0,90 **bel-0001** (dia 2): "Cavar leva ~16 minutos, plantar ~6 e regar ~3; um ciclo cavar+plantar+regar por canteiro gasta ~25 minutos."

### fable-procedimento: as crenças sobre o rio

- **bel-0010** (dia 9 a 14, confiança 0,50): "lugar: rabanete em canteiro novo leva os mesmos 3 dias colado ao poço, perto da casa, longe (20,25) ou no lote de (15,23) quando regado igual; a linha y=22 de x=6 a 31 é caminho e não se cava (not_grass); a fazenda explorada é só grama, árvores, rio e caminho.". Antes: "lugar: rabanete em canteiro novo leva os mesmos 3 dias colado ao poço, perto da casa, longe (20,25) ou no lote de (15,23) quando regado igual; a fazenda explorada (norte (30,8), leste (45,20), sul (20,36)) é só grama, árvores e caminho, sem nada de comer solto.". dia 9 revisada 0,45 → dia 12 revisada 0,45 → dia 14 revisada 0,50.

As crenças mais confiantes ao fim (12 ativas):

- 0,90 **bel-0002** (dia 8): "ferramentas sem arado: cavar leva 16 minutos, plantar 6, regar 3, colher 4 e reencher 4; um regador cheio rega 10 canteiros quando se vai ao poço."
- 0,85 **bel-0013** (dia 14): "semente no quiosque: o preço sobe cerca de 3% do preço base por unidade comprada no mesmo dia e não volta durante o dia; de manhã volta à tabela."
- 0,80 **bel-0004** (dia 14): "caderno: a tabela pode errar (plot-044 do dia 14 não aparece; 042 regado dia 14 aparece com 0 de 2; 'sumiu' em colheitas que eu fiz); o que vale é o que vejo no canteiro, no regador e no inventário."

### gemini: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (11 ativas):

- 0,99 **bel-0001** (dia 10): "Comprar sementes no quiosque encarece a semente progressivamente dentro do mesmo lote (+0,5 a +1 moeda por unidade comprada)."
- 0,99 **bel-0002** (dia 4): "Sem arado, cavar leva 16m, plantar 6m, regar 3m, encher no poço 4m, colher 4m e comer 11m."
- 0,99 **bel-0003** (dia 4): "O adubo aplicado antes do plantio não reduz os dias de maturação (3 dias) nem aumenta a quantidade colhida (1 unidade) no rabanete."

### gemini-piloto: as crenças sobre o rio

- **bel-0006** (dia 2 a 2, confiança 0,95): "O restante do mapa além das construções iniciais contém apenas grama, caminhos, árvores e o rio, sem construções ou recursos extras escondidos.". dia 2 formada 0,95.

As crenças mais confiantes ao fim (5 ativas):

- 0,98 **bel-0002** (dia 2): "Sem arado, cavar leva 16 minutos, plantar leva 6 minutos e regar leva 3 minutos por canteiro."
- 0,95 **bel-0004** (dia 2): "Comprar sementes no quiosque aumenta o preço em 1 moeda por unidade (para sementes de 20 e 30 moedas), cobrando a soma progressiva na compra em lote."
- 0,95 **bel-0005** (dia 2): "Entregar um pedido no quadro de encomendas paga as moedas imediatamente no inventário e rende bem mais que o preço base da caixa de vendas."

### gemini-procedimento: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (0 ativas):

- nenhuma

### haiku-comparar: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (42 ativas):

- 0,99 **bel-0034** (dia 25): "Preciso manter sempre pelo menos 10 moedas guardadas, o preço de uma semente de comida; sem elas não replanto."
- 0,98 **bel-0004** (dia 23): "A fome sobe cerca de 2 por hora acordado; um rabanete tira cerca de 25."
- 0,98 **bel-0009** (dia 16): "A planta só avança às 06:00; esperar parado durante o dia não faz crescer."

### haiku-comparar-r2: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (42 ativas):

- 0,99 **bel-0001** (dia 19): "Regar um canteiro leva cerca de 3 minutos, e encher o regador no poço, cerca de 4."
- 0,99 **bel-0009** (dia 12): "Cavar, plantar, colher, regar e comer exigem estar a até 1 tile do alvo; a 2 tiles a ação é recusada com not_adjacent."
- 0,98 **bel-0003** (dia 24): "Esperar 60 ticks avança uma hora; o quiosque abre às 08:00 e fecha às 18:00."

### haiku-conselheiro: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (35 ativas):

- 0,98 **bel-0005** (dia 13): "O quiosque abre às 08:00 e fecha às 18:00."
- 0,98 **bel-0019** (dia 28): "Sem comida guardada no inventário, a fome sobe cerca de 2 por hora e não dá para esperar a colheita de um dia para o outro."
- 0,97 **bel-0003** (dia 28): "Plantar uma semente leva cerca de 6 minutos e consome 1 semente do inventário."

### haiku-controle: as crenças sobre o rio

- **bel-0039** (dia 26 a 28, confiança 0,60): "Leste da fazenda (x 30 a 52, y 18 a 36): só grama e caminho, sem planta, árvore frutífera nem canteiro; a comida não está nessa faixa.". dia 26 formada 0,60.
- **bel-0040** (dia 26 a 28, confiança 0,60): "Caminho sul: (52,44) e (48,36) não são passáveis; a exploração do sul-leste acaba na faixa do quadro de encomendas.". dia 26 formada 0,60.

As crenças mais confiantes ao fim (40 ativas):

- 0,99 **bel-0004** (dia 26): "Fome: sobe cerca de 2 por hora acordado e cerca de 1 dormindo; sem comida ela chega a 100 e fica lá."
- 0,99 **bel-0006** (dia 21): "Rabanete: comê-lo tira 25 de fome quando ela está perto de 60 ou acima, sempre o mesmo valor."
- 0,99 **bel-0021** (dia 25): "Comida: sem colheita pronta e sem estoque, a fome sobe sem parar e o dia para sem moedas para replantar; esperar não resolve."

### haiku-dados: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (51 ativas):

- 0,99 **bel-0005** (dia 9): "O quiosque abre às 08:00 e fecha às 18:00."
- 0,99 **bel-0013** (dia 23): "O quiosque não vende comida: o estoque é só de sementes, adubo, espantalho, lanterna, tacho e ferramentas."
- 0,99 **bel-0021** (dia 28): "A feira abre às 06:00 e fecha às 14:00 nos dias 7, 14, 21 e 28; proxima_feira mostra o próximo dia de feira."

### haiku-dados-r2: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (48 ativas):

- 0,99 **bel-0026** (dia 20): "Colher, plantar e regar exigem estar a 1 tile do canteiro; a 2 tiles a ação é recusada com not_adjacent e um move resolve."
- 0,98 **bel-0005** (dia 6): "O quiosque abre às 08:00 e fecha às 18:00."
- 0,98 **bel-0014** (dia 15): "A chuva rega todos os canteiros do dia, inclusive os plantados na hora, sem gastar carga do regador."

### haiku-dados-r3: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (35 ativas):

- 0,99 **bel-0002** (dia 16): "O quiosque abre às 08:00 e fecha às 18:00."
- 0,99 **bel-0003** (dia 8): "Um wait de 60 ticks leva cerca de 61 minutos com a decisão."
- 0,99 **bel-0023** (dia 28): "O dinheiro é o gargalo: sem moedas não há semente, e sem colheita vendida não há moeda; o quiosque aberto não serve de nada sem dinheiro."

### haiku-openrouter: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (11 ativas):

- 0,95 **bel-0002** (dia 2): "Cada rega gasta uma carga do regador; o regador enche no poço até o máximo de 10 cargas."
- 0,95 **bel-0003** (dia 2): "Um canteiro regado num dia avança um estágio às 06:00 do dia seguinte, e o watered_today volta a false."
- 0,95 **bel-0005** (dia 2): "A fome sobe cerca de 2 por hora acordado."

### haiku-procedimento: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (34 ativas):

- 0,99 **bel-0022** (dia 23): "Comida: um único canteiro de comida é arriscado; se ele atrasar ou esvaziar, não há o que comer, e a fome sobe sem parar. Manter dois ou mais canteiros de comida escalonados."
- 0,99 **bel-0023** (dia 23): "Dinheiro: sem vender colheita, nenhuma moeda entra; com 8 moedas não se compra semente, já que a mais barata custa 10."
- 0,98 **bel-0003** (dia 25): "O quiosque abre às 08:00 e fecha às 18:00; a feira abre às 06:00 e fecha às 14:00 nos dias de feira (dias 7, 14, 21, 28)."

### haiku-procedimento-r2: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (33 ativas):

- 0,95 **bel-0003** (dia 25): "Energia: cai cerca de 1 por hora acordado com fome abaixo de 100, e cerca de 5 por hora com fome em 100."
- 0,95 **bel-0004** (dia 26): "Fome: rabanete comido tira cerca de 25; sem comida guardada a fome sobe até 100 e fica travada lá."
- 0,95 **bel-0007** (dia 27): "Colheita de rabanete: vence 4 dias depois da colheita, e a colheita de hoje (dia 27) vence no dia 31."

### haiku-procedimento-r3: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (36 ativas):

- 0,95 **bel-0002** (dia 12): "Plantar uma semente leva cerca de 6 minutos, sem arado."
- 0,95 **bel-0003** (dia 16): "Regar um canteiro gasta 1 carga do regador e cerca de 3 minutos, com o caminhar incluído."
- 0,95 **bel-0005** (dia 20): "O quiosque abre às 08:00 e fecha às 18:00."

### haiku-r2: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (33 ativas):

- 0,98 **bel-0007** (dia 13): "O comando wait aceita no máximo 60 ticks por vez, e cada 60 ticks são uma hora."
- 0,98 **bel-0015** (dia 26): "O quiosque abre às 08:00 e fecha às 18:00."
- 0,98 **bel-0017** (dia 28): "Nesta fazenda a comida depende de canteiros de ciclo curto plantados com antecedência; sem colheita guardada e sem sementes, a fome sobe até o próximo amadurecimento."

### haiku-r3: as crenças sobre o rio

- **bel-0041** (dia 25 a 28, confiança 0,75): "A área a leste e a sudoeste da casa, até cerca de 12 tiles, não tem planta silvestre nem item colhível ou vendável; só grama.". Antes: "A área a leste da casa, até cerca de 12 tiles, não tem planta silvestre nem item colhível ou vendável.". dia 25 formada 0,60 → dia 26 revisada 0,75.

As crenças mais confiantes ao fim (48 ativas):

- 0,99 **bel-0027** (dia 27): "Esperar em blocos sem renda nem comida guardada desperdiça o dia; é preciso sair procurando uma saída antes."
- 0,99 **bel-0028** (dia 24): "Sem moedas e sem colheita guardada, não há como comprar semente nem comida; guardar moedas antes de gastar."
- 0,98 **bel-0001** (dia 21): "A fome sobe cerca de 2 por hora acordado, e cerca de 1 dormindo."

### opus: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (12 ativas):

- 0,98 **bel-0002** (dia 26): "Regar leva 3 minutos por canteiro e gasta 1 carga (2 na seca); encher leva 4 minutos; sem arado, plantar leva 6 minutos e cavar uns 16."
- 0,97 **bel-0003** (dia 26): "Os canteiros em volta de (10–12, 22–32) ficam a uns 2 minutos a pé do poço, da cama, da caixa e do quiosque, e o quiosque fica ao lado do quadro; há árvores em x14–17, y27–33."
- 0,97 **bel-0005** (dia 21): "O registro às vezes não mostra o evento de uma ação que deu certo; o estado do canteiro e as cargas são a prova."

### opus-procedimento: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (14 ativas):

- 0,90 **bel-0001** (dia 1): "Mapa: a linha y=22 perto do poço é caminho e não aceita cavar (not_grass)."
- 0,90 **bel-0003** (dia 1): "Regador: 10 cargas regam 10 canteiros, e encher no poço leva uns 4 minutos."
- 0,75 **bel-0008** (dia 14): "Feira: abre nos dias 7 e 14 a partir das 06:00 e paga acima da caixa, mas o preço cai com o volume vendido."

### sonnet: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (21 ativas):

- 0,95 **bel-0003** (dia 28): "O regador tem 10 cargas, 1 por rega sem seca."
- 0,95 **bel-0004** (dia 28): "Planta regada num dia avança às 06:00 do dia seguinte."
- 0,95 **bel-0006** (dia 24): "Cada compra de semente sobe o preço; volta à tabela de manhã."

### sonnet-procedimento: as crenças sobre o rio

Nenhuma crença falou do rio.

As crenças mais confiantes ao fim (8 ativas):

- 0,70 **bel-0001** (dia 2): "Tiles em x=6, y=19..21: não são grama quando se tenta cavar, e cavar é recusado com not_grass."
- 0,70 **bel-0007** (dia 12): "Rabanete: demora 8 dias em vez de 3 quando a rega falha em quase metade dos dias."
- 0,50 **bel-0002** (dia 2): "Rabanete: chega a broto no dia 2 quando é regado no dia 1 (primavera)."

## Os experimentos da noite

Na reflexão de cada noite, a mente propõe um experimento barato para o dia seguinte (a hipótese, o teste e a previsão), e a reflexão da noite seguinte diz se a previsão se cumpriu. Com o caderno completo (ADR-0074, decisão 35), o experimento fica aberto até o veredito, que pode levar dias. O veredito é dela, não do avaliador.

### haiku: 28 experimentos (5 cumpriu, 11 falhou, 11 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Um canteiro sem rega no dia não cresce na manhã seguinte, mesmo com a mesma semente e sol. | inconclusivo |
| 2 | O plantio do plot-004 (rabanete, feito às 06:46 do dia 2) de fato aconteceu, e a planta está em semente, regada às 06:55. | cumpriu |
| 3 | O rabanete plot-001 (plantado no dia 1, regado pela chuva do dia 3) vira madura às 06:00 do dia 4. | cumpriu |
| 4 | O plot-001 não foi regado às 06:43 do dia 4, então não avança para broto no dia 5. | inconclusivo |
| 5 | A tempestade do dia 5 rega o plot-006, então ele avança para madura às 06:00 do dia 6. | cumpriu |
| 6 | A rega da chuva do dia 6 faz as plantas plantadas nele (plot-007 a 012) avançarem às 06:00 do dia 7, como o plot-006 avançou. | falhou |
| 7 | O cochilo na cama de dia dura até a energia encher, não até as 06:00 do dia seguinte. | inconclusivo |
| 8 | O cochilo na cama de dia dura até a energia encher, não até as 06:00 do dia seguinte. | inconclusivo |
| 9 | Os rabanetes 001-004 estavam em crescendo, e a chuva de hoje os regou, então às 06:00 do dia 10 pelo menos um deles vira maduro. | falhou |
| 10 | O plot-006, que chegou a crescendo às 06:00 do dia 10 e foi regado às 06:11, vira maduro às 06:00 do dia 11. | falhou |
| 11 | Plantar já marca watered_today como true, sem depender da chuva. | falhou |
| 12 | A chuva rega todos os canteiros do dia, então as plantas regadas hoje avançam amanhã sem que eu regue. | inconclusivo |
| 13 | A planta só avança se for regada no dia anterior; a chuva do dia 13 contou como rega, mas a rega do dia 14 é a que vale para o dia 15. | falhou |
| 14 | A chuva conta como rega até para a semente plantada sem rega à mão: o plot-004, plantado às 06:23 do dia 14 e sem rega própria, avança para broto às 06:00 do d… | inconclusivo |
| 15 | A chuva também faz avançar a semente plantada sem rega à mão: plot-004 (plantado no dia 14, só chuvas depois) vira broto às 06:00 do dia 16, e os recém-plantad… | falhou |
| 16 | A fome sobe cerca de 1 por hora dormindo, como diz a regra; dormir das 20:00 às 06:00 deve levar a fome de cerca de 35 para cerca de 45. | inconclusivo |
| 17 | A fome sobe cerca de 1 por hora dormindo, e não 2 por hora como acordado. | cumpriu |
| 18 | Uma semente plantada e regada no mesmo dia avança para broto na manhã seguinte; uma plantada sem rega fica em semente. | falhou |
| 19 | Uma semente plantada e regada no mesmo dia avança para broto na manhã seguinte, e a chuva do dia seguinte também conta como rega. | falhou |
| 20 | Uma semente plantada num dia de chuva, regada pela própria chuva, vira broto às 06:00 do dia seguinte. | inconclusivo |
| 21 | Um canteiro de semente que foi regado pelo regador no dia anterior vira broto às 06:00, mesmo sem chuva. | cumpriu |
| 22 | A leitura de fome de 60 às 15:01 do dia 22 estava errada, e a fome sobe 2 por hora acordado a partir de 67 às 06:00. | inconclusivo |
| 23 | O rabanete plantado na primavera leva 5 dias para amadurecer, não 3 como na tabela. | inconclusivo |
| 24 | Na seca, uma planta regada antes do meio-dia avança no dia seguinte, e uma não regada fica parada. | inconclusivo |
| 25 | Um canteiro plantado e não regado no dia fica sem avanço na manhã seguinte, enquanto os regados avançam. | falhou |
| 26 | Canteiros que ainda estão em semente precisam de mais de um dia regado para virar broto, enquanto os que já estão em broto ou crescendo avançam um estágio por… | falhou |
| 27 | Dormir gasta fome na metade do ritmo de acordado: a fome sobe cerca de 1 por hora durante o sono. | falhou |
| 28 | O rabanete plantado no inverno (dia 28) amadurece em cerca de 3 dias, no dia 31. | - |

### astra: 28 experimentos (15 cumpriu, 3 falhou, 9 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Rabanetes plantados e regados à tarde avançam na primeira manhã tanto quanto os plantados e regados antes do meio-dia, nas condições de hoje. | cumpriu |
| 2 | A chuva prevista rega os canteiros sem consumir cargas do meu regador. | cumpriu |
| 3 | Os dez rabanetes chegarão juntos à maturidade no próximo amanhecer após a rega pela chuva de hoje. | cumpriu |
| 4 | A tempestade também rega automaticamente os canteiros sem gastar cargas do meu regador. | inconclusivo |
| 5 | Rabanetes plantados de manhã e regados automaticamente pela tempestade apresentam avanço visível de estágio no amanhecer seguinte. | cumpriu |
| 6 | Canteiros de rabanete plantados em datas diferentes podem amadurecer em dias diferentes mesmo exibindo hoje o mesmo estágio de broto. | inconclusivo |
| 7 | Os dez canteiros antigos amadurecem antes de plot-011 a plot-013, apesar de ambos os lotes exibirem crescendo hoje. | inconclusivo |
| 8 | Os dez canteiros antigos amadurecem antes de plot-011 a plot-013, apesar de ambos os lotes ainda exibirem crescendo. | falhou |
| 9 | Entre os rabanetes plantados hoje sob chuva, canteiros recém-cavados e reutilizados avançam ao mesmo estágio na manhã seguinte. | cumpriu |
| 10 | Os rabanetes regados depois do meio-dia num dia de sol também podem avançar de estágio na manhã seguinte. | cumpriu |
| 11 | Após a mesma chuva, os rabanetes recém-plantados em terra nova avançam antes dos que seguem como sementes nos canteiros antigos. | falhou |
| 12 | A chuva também marca como regado um canteiro reutilizado que eu replanto depois do amanhecer. | cumpriu |
| 13 | Na feira, o preço oferecido pelo rabanete é maior que o preço simultâneo da caixa de vendas. | cumpriu |
| 14 | Comer um rabanete reduz minha fome em aproximadamente 25 pontos, descontada a fome acumulada durante a ação. | cumpriu |
| 15 | Colher um canteiro já regado apaga sua marca de rega, exigindo nova rega após o replantio num dia de sol. | inconclusivo |
| 16 | Colher um canteiro já regado apaga sua marca de rega, exigindo nova rega após o replantio num dia de sol. | inconclusivo |
| 17 | Replantar rabanete num canteiro cuja colheita apagou a rega não restaura essa marca em dia de sol. | cumpriu |
| 18 | Em dia de sol, regar um canteiro vazio antes de replantar preserva a marca de rega após o plantio. | inconclusivo |
| 19 | Em dia de chuva, replantar um canteiro recém-colhido restaura automaticamente sua marca de rega. | inconclusivo |
| 20 | No dia de sol seguinte, os rabanetes plantados sob chuva avançam de estágio sem terem recebido rega manual no dia do plantio. | falhou |
| 21 | Após mais um dia com água, os rabanetes dos canteiros 001 e 007 sairão do estágio semente na próxima manhã. | cumpriu |
| 22 | Os seis rabanetes ainda em semente e regados à tarde no primeiro dia de inverno passarão a broto na próxima manhã. | cumpriu |
| 23 | Em dia de chuva, replantar um canteiro recém-colhido restaura automaticamente sua marca de rega, ao contrário do observado sob sol. | inconclusivo |
| 24 | Na seca, cada rega de um canteiro plantado consome duas cargas do regador comum. | cumpriu |
| 25 | Rabanetes plantados e regados somente após o meio-dia na seca não avançam de estágio no amanhecer seguinte. | cumpriu |
| 26 | Em dia de sol, regar rabanetes pela manhã ou à tarde não altera seu avanço de estágio no amanhecer seguinte. | inconclusivo |
| 27 | Em dia de sol, regar rabanetes pela manhã ou à tarde não altera seu avanço de estágio no amanhecer seguinte. | cumpriu |
| 28 | No início da primavera, os rabanetes 021 e 023 plantados e regados juntos avançam de estágio de forma sincronizada. | - |

### astra-consertado: 14 experimentos (10 cumpriu, 3 falhou, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Os rabanetes plantados e regados hoje avançam de semente para broto na próxima manhã. | cumpriu |
| 2 | Os três rabanetes novos, plantados e regados em horários diferentes nesta manhã, chegarão juntos ao estágio broto na próxima virada das 06:00. | cumpriu |
| 3 | A rega da chuva no dia do plantio permite que o rabanete avance a broto na manhã seguinte, como a rega manual. | cumpriu |
| 4 | Depositar rabanetes no baú também retira primeiro o lote com vencimento mais próximo. | cumpriu |
| 5 | Os dez rabanetes plantados hoje sob chuva passarão de semente a broto na próxima manhã sem rega manual. | falhou |
| 6 | Os replantios recentes sob chuva mostram o primeiro broto na segunda manhã após o plantio, como ocorreu com os três replantios do dia 4. | cumpriu |
| 7 | A entrada no verão atrasará o primeiro broto dos rabanetes do dia 6 além da segunda manhã observada nos lotes da primavera. | cumpriu |
| 8 | Os rabanetes dos plots 014–016 mostrarão o primeiro broto na terceira manhã após o plantio, sob o ritmo mais lento observado na entrada do verão. | cumpriu |
| 9 | Os canteiros 019–020, plantados juntos sob chuva no verão, ainda estarão em semente na primeira manhã após o plantio. | cumpriu |
| 10 | Os rabanetes 019–020 passarão a broto na segunda manhã após o plantio no verão. | cumpriu |
| 11 | Os rabanetes 019–020 permanecerão em broto na manhã seguinte, apesar da chuva, se o avanço visível continuar espaçado no verão. | falhou |
| 12 | Os três rabanetes replantados hoje terão o primeiro broto apenas na segunda manhã após o plantio. | cumpriu |
| 13 | Os rabanetes de 001, 002 e 005 terão o primeiro broto na segunda manhã após o replantio. | falhou |
| 14 | Na entrada do outono, os rabanetes antigos de 001, 002 e 005 sairão de semente antes dos recém-plantados do dia 14. | - |

### astra-consertado-piloto: 2 experimentos (1 cumpriu, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Os rabanetes semeados e regados hoje avançam de semente para broto na próxima virada das 06:00. | cumpriu |
| 2 | Nas condições atuais, os rabanetes regados avançam de broto para crescendo na segunda manhã após o plantio. | - |

### astra-piloto: 2 experimentos (1 cumpriu, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Os rabanetes semeados e regados hoje avançam de estágio no próximo amanhecer, inclusive os regados à tarde. | cumpriu |
| 2 | A chuva prevista marca como regados também os canteiros com sementes recém-plantadas, sem rega manual. | - |

### astra-procedimento: 3 experimentos (2 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | [lugar] rabanete leva menos dias quando o canteiro fica perto do poço. | inconclusivo |
| 4 | [lugar] rabanete leva menos dias quando o canteiro fica perto do poço. | inconclusivo |
| 12 | [antes] rabanete leva mais dias quando o canteiro teve rabanete antes. | - |

### fable: 28 experimentos (10 cumpriu, 9 falhou, 8 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Toda planta regada no dia anterior avança exatamente um estágio às 06:00, independente da cultura. | cumpriu |
| 2 | Em dia de chuva todos os canteiros, inclusive os vazios, aparecem com watered_today=true sem eu regar, e as plantas avançam um estágio na manhã seguinte. | inconclusivo |
| 3 | O milho avança um estágio a cada 2 dias regados (6 dias para 3 transições), enquanto o rabanete avança um por dia. | cumpriu |
| 4 | O preço da caixa derrubado por venda se recupera devagar: sobe só uma fração (1-2 moedas) por dia, mais a oscilação. | falhou |
| 5 | Depois de uma tempestade as colheitas valem mais na caixa por alguns dias, e foi isso (não uma recuperação rápida) que levou o rabanete a 25 no dia 5. | cumpriu |
| 6 | A barraca da feira paga pelo rabanete acima do preço da caixa, e cada unidade vendida nela derruba seu preço como na caixa. | cumpriu |
| 7 | Na caixa de vendas, cada rabanete vendido derruba o preço do rabanete em ~1-3% (menos de 1 moeda por unidade), e a queda da caixa é parecida com a da barraca. | inconclusivo |
| 8 | Na estação fraca o rabanete avança um estágio a cada 2 dias regados: os que não avançaram no dia 8 avançam no dia 9, e o 016, que avançou no dia 8, fica parado… | falhou |
| 9 | No verão o avanço do rabanete regado é uma chance por manhã (~metade das plantas), não um ciclo fixo de 2 dias. | falhou |
| 10 | Na estação fraca cada dia regado soma meio estágio: 018/020/021 (regadas dia 9 pela chuva e dia 10 por mim) viram broto dia 11, e os 6 crescendo do dia 5 viram… | inconclusivo |
| 11 | O rabanete na estação fraca avança um estágio só a cada ~3 dias regados, então os 7 crescendo do dia 5 amadurecem por volta do dia 12-14, não antes. | cumpriu |
| 12 | O progresso acumula por canteiro: o rabanete 016, um degrau atrás dos seis que maduraram hoje, amadurece dia 13 ou 14 com rega diária, e os brotos 018/020/021… | inconclusivo |
| 13 | Na estação boa o milho sobe um estágio por manhã regada (broto→crescendo no dia 14) e o rabanete 016, um degrau atrás, amadurece com mais uma rega. | falhou |
| 14 | O milho na estação boa leva cerca de 2 manhãs regadas por estágio: broto→crescendo na 3ª manhã (dia 15) e maduro por volta do dia 18; o tomate e o rabanete rec… | falhou |
| 15 | A manhã da virada já usa a estação nova: no outono o tomate (boa) avança um estágio por manhã regada e o milho (fraca) só a cada duas, por isso os milhos trava… | falhou |
| 16 | Depois do broto, o milho em estação fraca precisa de 3 manhãs regadas por estágio, e o tomate em estação boa amadurece em 4 manhãs do plantio (1 por estágio e… | falhou |
| 17 | O crescimento acumula 1 por manhã regada na estação boa e 0,5 na fraca, e a planta amadurece quando o acumulado atinge os dias da tabela (tomate 4, milho 6). | cumpriu |
| 18 | Um canteiro vazio vira grama na 4ª manhã vazio (não na 3ª): o 023, vazio desde o dia 17, deve sumir na manhã do dia 21, não do 20. | inconclusivo |
| 19 | Um canteiro vazio vira grama na 4ª manhã vazio, não na 3ª: o 023, vazio desde o dia 17, ainda existe na manhã do 20 e some na do 21. | falhou |
| 20 | Dormindo de dia a fome sobe 1 por hora, não 2: as ~23 horas de sono de 07:01 do dia 20 até 06:00 do dia 21 devem somar uns 23 de fome, não 46. | cumpriu |
| 21 | No inverno o milho fica parado: mesmo regado, não muda de estágio de um dia para o outro, enquanto o rabanete (boa no inverno) avança 1 por manhã regada. | inconclusivo |
| 22 | O adubo faz o rabanete avançar mais de um estágio por manhã regada, amadurecendo em menos de 3 manhãs. | cumpriu |
| 23 | O efeito do adubo dura a vida toda da planta: ela amadurece na metade das manhãs regadas, em qualquer cultura. | falhou |
| 24 | O adubo dá um único estágio a mais na vida da planta, então a batata 059 amadurece uma manhã antes da 060, não duas. | inconclusivo |
| 25 | Depois de um dia de seca, os preços das colheitas na caixa sobem às 06:00 do dia seguinte, acima da oscilação normal. | inconclusivo |
| 26 | A subida de preço depois da seca dura pouco: no segundo dia o preço já não sobe mais e volta à oscilação normal. | cumpriu |
| 27 | A barraca da feira derruba o preço por unidade vendida no mesmo ritmo da caixa (~2-2,5% por unidade), e não mais. | cumpriu |
| 28 | Na virada de estação às 06:00 a caixa salta de uma vez: as culturas que saem da estação boa (batata, couve, alho, cenoura) sobem e as que entram nela (milho, t… | - |

### fable-piloto: 2 experimentos (1 cumpriu, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Toda planta regada no dia anterior avança exatamente um estágio às 06:00, e a que não foi regada fica no mesmo estágio. | cumpriu |
| 2 | O rabanete passa por um estágio por manhã de rega: semente, broto, crescendo e madura em 3 manhãs, como diz a tabela. | - |

### fable-procedimento: 5 experimentos (1 falhou, 3 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | [lugar] rabanete leva menos dias quando o canteiro fica colado ao poço do que quando fica longe dele. | falhou |
| 4 | [antes] rabanete leva mais dias quando o canteiro já teve rabanete antes do que quando é canteiro novo. | inconclusivo |
| 9 | [antes] milho leva mais dias quando o canteiro já teve rabanete antes do que quando é canteiro novo. | inconclusivo |
| 10 | [antes] milho leva mais dias quando o canteiro já teve rabanete antes do que quando é canteiro novo. | inconclusivo |
| 14 | [adubo] rabanete leva menos dias quando o canteiro foi adubado antes do plantio. | - |

### gemini: 11 experimentos (2 cumpriu, 6 falhou, 2 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | A sopa de batata feita no fogão com 2 batatas mata mais fome do que comer as 2 batatas cruas separadamente (70 de fome no total). | inconclusivo |
| 2 | O adubo faz o rabanete amadurecer em 2 dias (no dia 3) em vez de 3 dias (no dia 4). | falhou |
| 3 | O adubo aumenta o rendimento da colheita (dando 2 unidades em vez de 1) quando a planta não amadurece mais rápido. | falhou |
| 4 | Vender múltiplas unidades de uma vez na caixa de vendas paga o preço exibido no momento da venda para todas as unidades do lote (6 * 23 = 138 moedas), sem desc… | falhou |
| 5 | As batatas plantadas no Dia 1 (estação fraca na primavera) levarão o dobro do tempo normal (cerca de 10 dias em vez de 5) e portanto ainda não estarão maduras… | inconclusivo |
| 6 | A barraca da feira (fair_stall) no Dia 7 paga um prêmio percentual sobre o preço da caixa de vendas para colheitas frescas (tomate e milho). | cumpriu |
| 7 | No verão (estação fraca do rabanete), rabanetes que já estão no estágio crescendo ao virar a estação ainda amadurecem na manhã seguinte, enquanto rabanetes em… | falhou |
| 8 | Na estação fraca do rabanete (verão), os rabanetes que completaram o segundo dia regado no estágio 'crescendo' no Dia 8 amadurecerão às 06:00 do Dia 9, enquant… | falhou |
| 9 | Os 10 rabanetes que entraram no estágio 'crescendo' no Dia 8 (plot-014, 015, 016, 018, 019, 021, 022, 034) e no Dia 9 (plot-023) amadurecerão às 06:00 do Dia 1… | falhou |
| 10 | Após completarem o 3º dia regado no estágio 'crescendo' no verão (totalizando 1 dia na primavera + 4 dias no verão = 5 dias totais), os rabanetes plantados no… | cumpriu |
| 11 | Com o arado no inventário (comprado por 300 moedas, peso 12), plantar num canteiro leva 1 minuto (em vez de 6m) e cavar um canteiro na grama leva 5 minutos (em… | - |

### gemini-piloto: 2 experimentos (1 cumpriu, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Explorar o mapa além da área inicial pode revelar recursos ou terrenos especiais, gastando apenas 1 de energia a cada 60 tiles. | cumpriu |
| 2 | Plantas de rabanete levam 3 manhãs para amadurecer na primavera, ou se amadurecerem no Dia 3 (após 2 manhãs), renderão colheita imediata e a chuva regará novos… | - |

### haiku-comparar: 28 experimentos (8 cumpriu, 9 falhou, 10 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Um canteiro regado hoje avança de estágio às 06:00 de amanhã, e um canteiro não regado hoje não avança. | inconclusivo |
| 2 | Um canteiro semeado e regado no mesmo dia (plot-003, plantado às 06:30 do dia 2) avança de semente para broto às 06:00 do dia seguinte, como os canteiros que j… | cumpriu |
| 3 | Os canteiros regados pela chuva do dia 3 (plot-001, 002, 003 e 004) avançam às 06:00 do dia 4 sem nenhuma rega minha no dia 4, pois a rega do dia anterior bast… | cumpriu |
| 4 | Um rabanete tira cerca de 25 da fome. | cumpriu |
| 5 | A chuva rega todos os canteiros do dia, sem que eu precise regar nenhum. | inconclusivo |
| 6 | Um canteiro semeado num dia de chuva, sem nenhuma rega manual, avança de semente para broto às 06:00 do dia seguinte. | falhou |
| 7 | Um canteiro semeado e regado à mão no dia (sol), sem chuva, avança de semente para broto no 06:00 do dia seguinte. | falhou |
| 8 | Um canteiro regado pela chuva do dia 9 avança no 06:00 do dia 10 tanto quanto um regado à mão, e o plot-004 (semente) avança para broto nesse ciclo. | inconclusivo |
| 9 | Um canteiro regado pela chuva avança no 06:00 tanto quanto um regado à mão, e o plot-004 sai de semente para broto nesse ciclo. | falhou |
| 10 | Rabanete plantado no verão (estação fraca) leva cerca de 6 dias para amadurecer, o dobro dos 3 da primavera. | inconclusivo |
| 11 | Um canteiro semeado e regado no mesmo dia (dia 11) passa de semente a broto no 06:00 do dia 12, sem nova rega. | falhou |
| 12 | Um canteiro plantado e regado no dia N só avança no 06:00 de N+2, não no de N+1: a rega do dia N+1 é necessária para o primeiro avanço. | cumpriu |
| 13 | Um canteiro plantado e regado no dia 12 e regado de novo no dia 13 (pela chuva) avança no 06:00 do dia 14: a rega do dia N+1 conta para o primeiro avanço. | falhou |
| 14 | Um canteiro em semente só vira broto depois de duas manhãs seguidas regado (dia N e N+1); a rega de um único dia não basta. | inconclusivo |
| 15 | Um rabanete plantado num dia de chuva avança para broto às 06:00 do dia seguinte só se for regado manualmente no dia seguinte; sem rega, ele fica em semente. | inconclusivo |
| 16 | Quando o quiosque abre às 08:00, a semente de rabanete sobe de preço a cada unidade comprada, e o aumento é de cerca de 1 moeda por unidade. | inconclusivo |
| 17 | Cada semente de rabanete comprada no quiosque sobe o preço da próxima em cerca de 1 moeda. | inconclusivo |
| 18 | Um plantio regado no dia N avança para broto às 06:00 do dia N+1, desde que regado no dia N (e não só N+1). | falhou |
| 19 | Um plantio regado no dia N e de novo no dia N+1 avança para broto no 06:00 do dia N+2 (regra de dois dias), e não no N+1. | cumpriu |
| 20 | Dormindo, a fome sobe cerca de 1 por hora, metade do ritmo acordado. | inconclusivo |
| 21 | Um rabanete já crescendo e regado no dia anterior vira madura na manhã seguinte, em um só passo. | falhou |
| 22 | Dormir na cama às 20:00 evita o desmaio das 02:00 e acorda com a energia alta. | cumpriu |
| 23 | O quiosque cobra mais caro a cada semente de rabanete que eu compro no mesmo dia. | falhou |
| 24 | Um rabanete plantado no inverno e regado todo dia amadurece em 3 dias, sem atraso. | inconclusivo |
| 25 | Na seca, cada rega gasta 2 cargas; em dia de sol, gasta 1. | cumpriu |
| 26 | Com a fome em 100, a fome não mata de imediato: só a energia cai, e o sono na cama a recupera. | cumpriu |
| 27 | O canteiro 004, regado no dia 27, vira madura às 06:00 do dia 28; o 005, sem rega confirmada, fica em crescendo. | falhou |
| 28 | Canteiros de rabanete no inverno avançam um estágio por dia regado, então 004 e 005, regados hoje, devem avançar no 06:00 de amanhã. | - |

### haiku-comparar-r2: 28 experimentos (4 cumpriu, 8 falhou, 15 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | O rabanete plantado e regado no dia 1 avança de estágio no 06:00 de cada manhã seguinte à rega, e fica maduro cerca de três dias depois do plantio. | inconclusivo |
| 2 | O rabanete plantado no dia 1 fica maduro cerca de três dias depois do plantio, então os canteiros 001 a 004 devem estar maduros às 06:00 do dia 3 ou do dia 4. | inconclusivo |
| 3 | O rabanete plantado no dia 1 fica maduro no 06:00 do dia 4, e o plantado no dia 2 (005-009) fica maduro um dia depois. | cumpriu |
| 4 | A chuva da tempestade de amanhã conta como rega: os canteiros amanhecem com watered_today true sem eu regar. | inconclusivo |
| 5 | Os rabanetes plantados no dia 5 ficam maduros 3 dias depois do plantio, se regados pela chuva ou pela minha rega. | inconclusivo |
| 6 | Os pedidos do quadro de encomendas pagam mais que a caixa de vendas para a mesma cultura, e aparecem com frequência para as culturas que eu planto. | falhou |
| 7 | Um canteiro sem rega no dia não cresce no dia seguinte, mesmo estando no mesmo estágio que um canteiro regado. | falhou |
| 8 | Dormir na cama sobe a fome só cerca de 1 por hora, e não 2 como acordado. | cumpriu |
| 9 | Milho plantado no verão (estação boa para ele) amadurece em cerca de 6 dias, ao contrário do rabanete, que no verão leva o dobro. | inconclusivo |
| 10 | Um canteiro só avança às 06:00 do dia seguinte se foi regado no dia anterior; um canteiro não regado não avança. | inconclusivo |
| 11 | Um canteiro só avança às 06:00 se foi regado no dia anterior; um canteiro não regado fica no mesmo estágio. | inconclusivo |
| 12 | Chuva conta como rega: um canteiro que não recebi rega no dia 13, mas que choveu, avança às 06:00 do dia 14. | inconclusivo |
| 13 | Planta que foi regada no dia anterior (por mim ou pela chuva) avança de estágio às 06:00 do dia seguinte, e o plantio conta como rega do primeiro dia. | falhou |
| 14 | Um canteiro só avança de estágio às 06:00 se foi regado por mim naquele mesmo dia (a chuva não basta). | inconclusivo |
| 15 | Um canteiro só avança de estágio às 06:00 se foi regado por mim naquele mesmo dia; a chuva não basta. | inconclusivo |
| 16 | x | inconclusivo |
| 17 | Os rabanetes 005-009, que avançaram para crescendo às 06:00 do dia 17 e foram regados no dia 17, ficam maduros às 06:00 do dia 18. | falhou |
| 18 | Os rabanetes 005-010 e 012, regados no dia 18 e ainda em crescimento, viram maduros às 06:00 do dia 19. | cumpriu |
| 19 | Um rabanete plantado e regado todo dia, sem falhas, amadurece no tempo da tabela (cerca de 3 dias na primavera, ou seja, 2 a 3 avanços às 06:00). | falhou |
| 20 | O pagamento da caixa de hoje cai às 06:00 do dia 21 ao preço registrado às 06:10 do dia 20 (cerca de 22 por rabanete), ou seja cerca de 44 no total. | cumpriu |
| 21 | Os canteiros plantados e regados hoje (006, 009, 010, 012) avançam para broto às 06:00 de amanhã, como os de ontem. | falhou |
| 22 | Um canteiro em semente só vira broto se foi regado em dois dias seguidos, e não com uma só rega. | falhou |
| 23 | Rabanete plantado no inverno (estação boa) fica maduro em 3 dias, se regado. | inconclusivo |
| 24 | Na seca, a planta regada no dia 25 avança às 06:00 do dia 26; a planta não regada fica parada. | inconclusivo |
| 25 | Milho plantado no inverno (estação parada) não avança de estágio mesmo quando é regado todos os dias. | inconclusivo |
| 26 | O milho de inverno avança às 06:00 quando é regado no dia anterior, mesmo na estação parada. | inconclusivo |
| 27 | Milho de inverno avança às 06:00 quando é regado no dia anterior, mesmo na estação parada. | falhou |
| 28 | O milho 013, parado no inverno, avança de estágio às 06:00 do dia 29 porque a estação passa a primavera (boa), e não por causa da rega. | - |

### haiku-conselheiro: 28 experimentos (9 cumpriu, 4 falhou, 14 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | O rabanete cresce uma etapa por manhã, após ter sido regado no dia anterior, então os canteiros plantados e regados no dia 1 devem estar em 'broto' às 06:00 do… | cumpriu |
| 2 | A chuva rega todos os canteiros de graça: no dia 3 o watered_today fica true sem nenhuma ação minha. | cumpriu |
| 3 | Os rabanetes plot-001 a 004 amadurecem ao amanhecer do dia 4, três manhãs depois de plantados e regados, e a colheita rende 1 cada. | cumpriu |
| 4 | O adubo faz o rabanete seguinte amadurecer mais cedo do que os 3 dias de sempre. | inconclusivo |
| 5 | O adubo não acelera o rabanete: o plot-011 (adubado, plantado às 08:33 do dia 5) amadurece no dia 8, como o plot-005 replantado sem adubo às 06:12. | inconclusivo |
| 6 | Um rabanete reduz a fome em cerca de 25 pontos. | cumpriu |
| 7 | Adubo faz o rabanete amadurecer mais cedo do que o canteiro sem adubo plantado no mesmo dia. | inconclusivo |
| 8 | x | inconclusivo |
| 9 | Adubo faz o rabanete madurar em menos dias do que o sem adubo, no mesmo dia de plantio. | inconclusivo |
| 10 | O rabanete adubado amadurece antes do rabanete sem adubo, plantados no mesmo dia. | inconclusivo |
| 11 | Um rabanete plantado no dia 11 e regado todos os dias amadurece em 4 a 5 dias, no dia 15 ou 16. | falhou |
| 12 | Um canteiro de rabanete regado no dia anterior avança para broto às 06:00 do dia seguinte, e a chuva conta como rega. | inconclusivo |
| 13 | Adubo acelera o amadurecimento do rabanete (bel-0017). | inconclusivo |
| 14 | A chuva conta como rega: nos dias de chuva, os canteiros avançam às 06:00 seguinte sem que eu regue, e o watered_today já aparece marcado. | inconclusivo |
| 15 | A chuva de hoje (dia 15) conta como rega: o plot-018, plantado às 06:27 sem eu regar, avança para broto às 06:00 do dia 16 (dia de sol), sem rega minha. | falhou |
| 16 | Um canteiro plantado e regado no mesmo dia (sem chuva) avança para broto às 06:00 do dia seguinte, pela regra da rega do dia anterior. | cumpriu |
| 17 | Um canteiro adubado antes do plantio de rabanete amadurece em menos dias que um vizinho não adubado plantado no mesmo dia. | inconclusivo |
| 18 | Um canteiro adubado antes do plantio de rabanete amadurece em menos dias que um vizinho não adubado plantado no mesmo dia. | inconclusivo |
| 19 | A chuva marca watered_today em todos os canteiros já plantados, sem nenhuma rega minha, e as plantas avançam na manhã seguinte. | cumpriu |
| 20 | O adubo faz o rabanete amadurecer mais rápido: o plot-016 adubado e o plot-017 sem adubo, plantados no dia 20, não amadurecem no mesmo dia. | inconclusivo |
| 21 | Um rabanete mata cerca de 25 de fome, mais do que uma couve (cerca de 12). | cumpriu |
| 22 | Um rabanete plantado no inverno (estação boa) amadurece em 3 dias, e as plantas de 22 viram maduras na manhã do dia 25. | falhou |
| 23 | Adubo acelera o amadurecimento do rabanete em pelo menos um dia na estação atual. | inconclusivo |
| 24 | Plantar conta como rega do dia: 014 e 015, plantados no dia 24, avançam para broto às 06:00 do dia 25, mesmo sem regar no dia 25. | falhou |
| 25 | Em dia de sol, cada rega gasta 1 carga do regador, não 2 como na seca. | cumpriu |
| 26 | Adubo encurta o tempo até o rabanete amadurecer (mais rápido que o não adubado). | inconclusivo |
| 27 | A feira paga mais por rabanete do que a caixa de vendas. | cumpriu |
| 28 | O adubo encurta o tempo de maturação do rabanete em pelo menos 1 dia. | - |

### haiku-controle: 10 experimentos (2 cumpriu, 3 falhou, 3 inconclusivo, 2 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | [adubo] rabanete leva menos dias quando o canteiro foi adubado antes do plantio. | inconclusivo |
| 4 | [adubo] rabanete leva menos dias quando o canteiro foi adubado antes do plantio. | - |
| 8 | [estação] rabanete plantado na primavera e amadurecido no verão leva cerca de 6 dias. | inconclusivo |
| 14 | [chuva] a chuva conta como rega: canteiro que não foi regado no dia de chuva sai do amanhecer seguinte com watered_today true, sem regador. | falhou |
| 16 | [chuva] o dia de chuva conta como rega do dia: watered_today fica true durante o dia da chuva e zera às 06:00 do dia seguinte. | inconclusivo |
| 20 | [fome] Dormir na cama com fome 100 recupera energia do mesmo jeito: 12,5 por hora. | cumpriu |
| 23 | [estação] rabanete plantado no inverno (boa) amadurece em cerca de 3 dias quando regado todo dia. | cumpriu |
| 25 | [comida] Há algo comestível (mato, fruta, planta de outro dono) na parte leste da fazenda, fora da área já vista (x acima de 26). | falhou |
| 26 | [baú] Há comida ou semente guardada no baú (9,16) que eu não contei no dia 26. | falhou |
| 28 | [comida] Há algo comestível (mato, fruta ou planta de outro dono) na faixa sudoeste da fazenda, ainda não vista (x 0 a 20, y 29 a 36). | - |

### haiku-dados: 18 experimentos (4 cumpriu, 7 falhou, 2 inconclusivo, 5 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Os rabanetes regados no dia 1 passam de semente para broto às 06:00 do dia 2. | cumpriu |
| 2 | Um canteiro não regado no dia de plantio (plot-005) não avança às 06:00 do dia seguinte, enquanto os regados avançam; a chuva do dia 3 também conta como rega,… | falhou |
| 3 | Comer um rabanete tira cerca de 25 de fome, como diz a tabela. | cumpriu |
| 4 | Dormindo, a fome sobe cerca de 1 por hora, metade do ritmo de quando estou acordado. | - |
| 5 | Feira paga mais por rabanete do que a caixa de vendas. | inconclusivo |
| 6 | A chuva do dia 6 regou os canteiros 003 a 010, então às 06:00 do dia 7 eles avançam de semente para broto, como 001 e 002 avançaram hoje. | falhou |
| 7 | Dormindo na cama de noite, a fome não sobe, ou sobe menos que 1 por hora; a queda de 67 para 63,7 pode ser um efeito real ou uma leitura errada. | - |
| 8 | Rabanete plantado na primavera e regado no verão (estação fraca) leva o dobro do tempo: os canteiros 003 a 010, que viraram crescendo às 06:00 do dia 8, amadur… | falhou |
| 11 | Os canteiros 004 a 008 (plantados no dia 5, regados às vezes) amadurecem na estação fraca só depois de cerca de 6 dias, ou seja, às 06:00 do dia 14. | cumpriu |
| 14 | A chuva do dia 15 conta como rega: os canteiros plantados no dia 14 (003, 005, 006, 007, 009, 010), que estão em semente, avançam para broto às 06:00 do dia 16… | - |
| 16 | Rabanete regado todo dia no outono (estação boa) passa de broto a crescendo e a madura em um dia por estágio, sem atraso. | falhou |
| 18 | A rega do dia anterior é condição para o avanço: o canteiro regado no dia 19 avança às 06:00 do dia 20 e o não regado fica parado. | - |
| 19 | A rega do dia anterior é condição para o avanço: 002 (regado no dia 19) avança às 06:00 do dia 20, e 001 (sem rega no dia 19) fica parado. | inconclusivo |
| 20 | A rega do dia anterior é condição para o avanço de estágio às 06:00: o canteiro regado hoje (dia 21, sol) avança às 06:00 do dia 22, e o não regado hoje fica p… | falhou |
| 22 | Rabanete em crescendo vira madura às 06:00 quando foi regado no dia anterior, e 001 e 002 estão perto disso. | falhou |
| 23 | 001 e 002, regados às 06:05 e 06:10 do dia 23 e em crescendo desde o dia 18, viram madura às 06:00 do dia 24. | cumpriu |
| 24 | Rabanete plantado no inverno (estação boa) leva 5 a 6 dias para madurar, então 001 e 002, plantados às 08:14 e 08:20 do dia 24, viram madura às 06:00 do dia 29… | falhou |
| 27 | Um espantalho ao lado de um canteiro maduro impede o corvo de comer a planta às 06:00. | - |

### haiku-dados-r2: 22 experimentos (6 cumpriu, 7 falhou, 6 inconclusivo, 3 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Uma planta de rabanete regada no dia 1 avança de semente para broto às 06:00 do dia 2, sem precisar de nada além da rega do dia anterior. | cumpriu |
| 2 | A chuva do dia 3 rega todos os canteiros sem gastar carga do regador. | inconclusivo |
| 3 | Comer um rabanete tira cerca de 25 pontos de fome, como diz a tabela. | inconclusivo |
| 4 | Um canteiro replantado sem rega no dia não avança na manhã seguinte. | cumpriu |
| 5 | Uma planta regada só pela chuva ou pela tempestade avança um estágio na manhã seguinte, como uma regada à mão. | falhou |
| 6 | Canteiros plantados de manhã e regados pela chuva do mesmo dia (006 a 016) avançam para broto às 06:00 do dia 7. | - |
| 7 | O plot-005, regado às 06:05 do dia 7 quando estava em crescendo, chega a madura às 06:00 do dia 8. | falhou |
| 8 | Na estação fraca do verão, o rabanete que está em crescendo e é regado todo dia chega a madura em 2 manhãs, não em 1. | falhou |
| 9 | Canteiro regado menos vezes (plot-011, 1 de 4) fica para trás dos outros plantados no mesmo dia (2 de 4). | falhou |
| 10 | Um canteiro de rabanete que não foi regado no dia 10 (plot-002) não avança na manhã do dia 11, enquanto os regados avançam. | inconclusivo |
| 11 | Enquanto dormo a fome sobe mais devagar, cerca de 1 por hora, metade do ritmo acordado. | falhou |
| 12 | A chuva de amanhã rega todos os canteiros, inclusive o 014, sem gastar carga do regador. | cumpriu |
| 13 | Dormindo, a fome sobe cerca de 1 por hora; acordado, cerca de 2 por hora. | cumpriu |
| 15 | Rabanete plantado na estação boa (outono) amadurece em 3 dias, como diz a tabela, e não nos 6 da estação fraca. | inconclusivo |
| 19 | O dinheiro de 3 rabanetes vendidos às 07:13 entra às 06:00 do dia 20 como moedas no meu inventário. | - |
| 20 | Milho vendido na caixa rende bem mais do que as 25 de fome que daria comendo, perto do preço de 64 da caixa de hoje. | inconclusivo |
| 21 | Um canteiro plantado no dia 20 e regado uma vez no dia 21 de manhã avança para broto às 06:00 do dia 22, como o plot-016 avançou, e não como os plot-012, 013 e… | cumpriu |
| 22 | Um canteiro plantado às 08:14 do dia 22 e regado às 08:23 avança para broto às 06:00 do dia 23, como os plantados de manhã nos dias anteriores. | cumpriu |
| 23 | Dormindo na cama das 18:03 às 06:00, a fome sobe cerca de 1 por hora, ou seja, cerca de 12 pontos na noite. | inconclusivo |
| 24 | Um canteiro regado à mão antes do meio-dia de uma seca avança um estágio às 06:00 do dia seguinte, enquanto um canteiro não regado no mesmo dia fica parado. | falhou |
| 26 | Canteiros regados hoje (dia 26) avançam para broto às 06:00 do dia 27, inclusive os plantados no dia 25 (012 a 015) e o 009, que não avançaram na manhã de hoje. | falhou |
| 27 | Um canteiro plantado no dia 28 e regado no mesmo dia avança para broto às 06:00 do dia 29, e um canteiro plantado no mesmo dia mas regado só no dia 29 não avan… | - |

### haiku-dados-r3: 19 experimentos (7 cumpriu, 6 falhou, 4 inconclusivo, 2 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Uma planta regada hoje avança de estágio às 06:00 de amanhã, mesmo sem ser regada de novo. | cumpriu |
| 2 | Um rabanete comido tira cerca de 25 de fome, como diz a tabela, e não 9. | cumpriu |
| 3 | Cavar gasta 2 de energia e plantar gasta 0,5, como diz a tabela da fazenda. | falhou |
| 4 | Cavar um canteiro gasta cerca de 2 de energia e leva cerca de 15 minutos. | cumpriu |
| 5 | Dormir na cama recupera cerca de 12,5 de energia por hora, então de 83 às 18:15 a energia chega a 100 por volta de 19:40, e o cochilo acaba antes das 20:00. | inconclusivo |
| 8 | Na chuva do dia 9, todos os canteiros ficam regados sem eu regar, e o watered_today vira true sozinho. | inconclusivo |
| 10 | Os canteiros regados hoje (dia 10) avançam de estágio às 06:00 do dia 11, e os que não foram regados ficam parados. | falhou |
| 11 | Os canteiros regados pela chuva do dia 11 (007 a 010, plantados no dia 9 e nunca regados por mim) avançam de estágio às 06:00 do dia 12, mesmo sem nenhuma rega… | cumpriu |
| 12 | Um rabanete plantado no verão (fraca) leva cerca de 6 dias de broto até madura, e a colheita sai às 06:00 do dia 18. | inconclusivo |
| 13 | Um rabanete plantado no verão (fraca) leva cerca de 6 dias de broto até madura, e a colheita sai às 06:00 do dia 18. | falhou |
| 15 | Rabanete plantado na outono (estação boa) amadurece em 3 dias, e não em 6 como no verão. | - |
| 16 | Rabanete plantado no outono (estação boa) amadurece em 3 dias, e não em 6 como no verão. | falhou |
| 19 | Os rabanetes de outono que estavam em crescendo no dia 19 (007 a 010, regados hoje) ficam maduros às 06:00 do dia 20, um estágio depois do crescendo. | falhou |
| 20 | Os rabanetes de outono regados hoje (dia 20) ficam maduros às 06:00 do dia 21, um dia depois de estarem em crescendo. | inconclusivo |
| 21 | Dormindo na cama, a fome sobe cerca de 1 por hora, metade da taxa de quando estou acordado (2 por hora). | cumpriu |
| 22 | O plot-009 (rabanete plantado no dia 21, outono ou inverno) fica madura só depois de 5 dias, às 06:00 do dia 26, e não amanhã. | cumpriu |
| 26 | Dormir na cama recupera a energia de 55 até cerca de 100 às 06:00, mesmo com fome 100. | cumpriu |
| 27 | O baú (chest, em 9,16) guarda alguma semente, colheita ou moeda que deixei lá antes, e é o único recurso que sobrou. | falhou |
| 28 | A fazenda não entrega dinheiro sozinha: a caixa de vendas e o baú ficam vazios até eu colocar algo neles, e não há um pagamento por dia parado. | - |

### haiku-openrouter: 2 experimentos (1 cumpriu, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Um canteiro regado no dia 1 cresce às 06:00 do dia 2, então os rabanetes que plantei às 06:18 saem de semente para broto. | cumpriu |
| 2 | A chuva do dia 3 conta como rega para todos os canteiros, inclusive os que estão fora da minha vista, e eles avançam às 06:00 do dia 4. | - |

### haiku-procedimento: 16 experimentos (2 cumpriu, 3 falhou, 7 inconclusivo, 4 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | [comida] Um rabanete comido com fome acima de 60 mata cerca de 25 de fome, como o manual diz. | - |
| 2 | [sono] Dormir na cama às 18:18 recupera a energia até 06:00, sem desmaiar e sem chegar a 0, quando a energia está baixa (cerca de 40). | falhou |
| 3 | [sono] Dormir na cama às 20:00, de noite, com energia abaixo de 50, sustenta o sono até as 06:00 sem desmaio às 02:00. | inconclusivo |
| 5 | [sono] Dormir na cama às 19:53 com energia cerca de 81 recupera a energia até 100 às 06:00. | cumpriu |
| 6 | [lugar] Rabanete plantado perto do poço amadurece pelo menos 2 dias antes do plantado perto da casa. | inconclusivo |
| 13 | [fome] Dormindo, a fome sobe cerca de 1 por hora, metade do ritmo acordado. | - |
| 14 | [fome] Dormindo de 18:48 até as 06:00, a fome sobe cerca de 1 por hora, como na noite de 13 para 14. | cumpriu |
| 15 | [estação] Rabanete plantado no verão (fraca) e colhido na virada para o outono (boa) amadurece em cerca de 3 dias depois da virada. | - |
| 18 | [rega] Um canteiro murcho não volta a crescer quando regado; só a limpeza o libera para plantar de novo. | inconclusivo |
| 20 | [quiosque] A semente de rabanete volta ao preço da tabela (10) às 06:00 de cada dia, mesmo depois de uma compra no dia anterior. | inconclusivo |
| 21 | [caixa] Adubo, produto da composteira, não é aceito na caixa de vendas: a caixa só aceita colheita e produto. | inconclusivo |
| 22 | [composteira] A composteira não começa com 2 restos; exige 3 para fazer 1 adubo. | inconclusivo |
| 23 | [composteira] A composteira não começa com 2 restos; exige 3 para fazer 1 adubo. | inconclusivo |
| 26 | [estoque] O quiosque no inverno repete alho, cenoura, couve e rabanete no estoque de cada dia, sem comida. | falhou |
| 27 | [baú] O baú guarda comida ou sementes que eu deixei lá e esqueci. | falhou |
| 28 | [mapa] Na parte nunca vista do mapa, a leste (x acima de 26), há comida, sementes ou canteiros já prontos para aproveitar. | - |

### haiku-procedimento-r2: 8 experimentos (7 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | [lugar] rabanete leva 3 dias quando plantado perto do poço, mais rápido que perto da porta. | inconclusivo |
| 4 | [lugar] rabanete leva 3 dias quando plantado perto do poço, mais rápido que perto da porta. | inconclusivo |
| 7 | [antes] rabanete leva 3 dias quando plantado em canteiro novo (grama), e mais de 3 quando plantado num canteiro que já teve rabanete. | inconclusivo |
| 9 | [antes] rabanete leva cerca de 6 dias no verão quando plantado em canteiro novo (grama), e mais quando plantado num canteiro que já teve rabanete. | inconclusivo |
| 10 | [rega] A chuva do dia 11 rega os canteiros sem gastar carga e sem atrasar os que não rego à mão. | inconclusivo |
| 12 | [rega] A chuva do dia 13 rega os canteiros sem gastar carga do regador. | inconclusivo |
| 13 | [rega] Regar à tarde (depois das 12:00) conta para o avanço da manhã seguinte tanto quanto regar de manhã. | inconclusivo |
| 14 | [adubo] Rabanete plantado em canteiro adubado amadurece mais rápido que em canteiro sem adubo, na mesma estação. | - |

### haiku-procedimento-r3: 4 experimentos (3 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | [lugar] rabanete leva 3 dias perto do poço e mais dias longe dele. | inconclusivo |
| 5 | [lugar] rabanete plantado perto do poço (13,19) amadurece antes do que longe dele (4,20), quando os dois são regados todo dia. | inconclusivo |
| 14 | [lugar] rabanete plantado perto do poço (13,19) amadurece antes do que longe dele (4,20), quando os dois são regados todo dia. | inconclusivo |
| 15 | [adubo] rabanete adubado amadurece antes do que o sem adubo quando plantado no mesmo dia e regado todo dia. | - |

### haiku-r2: 28 experimentos (8 cumpriu, 6 falhou, 13 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | A planta só avança de estágio na virada das 06:00 se o canteiro foi regado no dia anterior. | falhou |
| 2 | Um canteiro avança na virada das 06:00 só se foi regado no dia anterior. | inconclusivo |
| 3 | O rabanete do plot-001, que está crescendo, vira madura na virada das 06:00 do dia 4, porque foi regado pela chuva do dia 3. | cumpriu |
| 4 | Um canteiro não regado no dia 4 não avança no dia 5, mesmo com a tempestade do dia 5 regando tudo, porque o crescimento de 06:00 depende da rega do dia anterio… | inconclusivo |
| 5 | Rabanete plantado no dia 5 leva 1 dia por estágio: broto no dia 6, crescendo no dia 7 e madura no dia 8. | falhou |
| 6 | A rega no dia anterior não é o que faz o canteiro avançar: o avanço depende do tempo de plantio e talvez da chuva, e canteiros plantados no mesmo dia andam jun… | inconclusivo |
| 7 | Uma rega em dia de sol gasta 1 carga do regador; a queda de 2 cargas na rega do plot-002 foi exceção, talvez por a planta estar no estágio de broto ou por um e… | cumpriu |
| 8 | A chuva conta como rega: nos canteiros regados pela chuva do dia 9 o estágio avança às 06:00 do dia 10 sem gastar carga do regador. | inconclusivo |
| 9 | O preço da semente no quiosque volta para a tabela no 06:00 seguinte, mesmo depois de eu comprar uma unidade. | inconclusivo |
| 10 | Os canteiros regados no dia 10 avançam um estágio às 06:00 do dia 11 (bel-0001). | inconclusivo |
| 11 | Rabanete plantado no verão (estação fraca) leva perto de 6 a 8 dias para amadurecer, mais que os 3 da primavera. | inconclusivo |
| 12 | Rabanete plantado no verão e regado amadurece em cerca de 6 dias, e avança um estágio a cada 06:00 em que foi regado no dia anterior. | falhou |
| 13 | Uma planta recém-plantada passa uma manhã em semente e só depois avança de broto em diante, uma vez por 06:00 com rega do dia anterior. | cumpriu |
| 14 | Dormir de dia (cochilo) gasta menos fome: cerca de 1 por hora, metade do ritmo acordado. | inconclusivo |
| 15 | A batata plantada no dia 15 (regada pela chuva do mesmo dia) avança para broto às 06:00 do dia 16, sem uma manhã parada em semente. | cumpriu |
| 16 | O preço de venda de um item derrubado pela minha venda se recupera só aos poucos, então o rabanete da caixa fica abaixo de 23 na manhã seguinte. | inconclusivo |
| 17 | O preço do rabanete na caixa de vendas fica perto de 21 a 22 na primavera, e a leitura de 36 foi outra coisa, talvez da feira ou de outro item. | cumpriu |
| 18 | Os canteiros de rabanete plantados no dia 17 (plots 009 a 017) levam 6 dias para madurar na primavera, como os plots 001 a 004 de hoje. | inconclusivo |
| 19 | A chuva de amanhã (dia 20) marca watered_today como true em todos os canteiros sem gastar carga do regador. | cumpriu |
| 20 | Um canteiro de rabanete regado com o regador amanhã avança de estágio às 06:00 do dia 22, mas um canteiro igual deixado sem rega não avança (a rega de hoje é o… | inconclusivo |
| 21 | Canteiros de rabanete já crescendo e regados hoje (dia 21) viram madura às 06:00 do dia 22, mais rápido que os 3 a 7 dias da tabela; os sem rega (003 e 004) fi… | cumpriu |
| 22 | A caixa de vendas paga às 06:00 do dia 23 pelos 3 rabanetes vendidos a 21 cada, somando 63, e com as 9 moedas dá 72. | falhou |
| 23 | No inverno o rabanete precisa de 3 manhãs regadas para madurar (semente, broto, crescendo, madura), não de 5 como eu achava. | falhou |
| 24 | Uma rega feita de manhã na seca, antes do meio-dia, conta como rega do dia e faz o canteiro 009 avançar na manhã seguinte, mesmo que a rega do dia 23 não tenha… | falhou |
| 25 | Uma planta só avança se for regada no dia anterior: sem rega no dia 26, o canteiro não sobe no 06:00 do dia 27. | inconclusivo |
| 26 | Rabanete plantado e regado no dia 27 (primavera, boa) chega a madura em 3 manhãs: broto no dia 28, crescendo no dia 29 e madura no dia 30. | inconclusivo |
| 27 | Os canteiros em crescendo regados hoje (009, 010, 013, 014, 016, 017) viram madura às 06:00 do dia 28, e colher um deles rende 1 rabanete que tira cerca de 25… | cumpriu |
| 28 | A rega do plot-010 às 06:38 de hoje aconteceu, mesmo sem registro, e por isso o canteiro deve avançar de semente para broto às 06:00 de amanhã. | - |

### haiku-r3: 28 experimentos (7 cumpriu, 14 falhou, 6 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Só a rega faz a planta avançar de estágio na manhã seguinte; o canteiro sem rega fica parado. | inconclusivo |
| 2 | O plot-004 já tem uma planta de rabanete plantada no dia 2 às 08:23, e ela avança para broto na manhã do dia 3, porque foi regada no dia 2. | cumpriu |
| 3 | Um canteiro que não foi regado no dia anterior fica no mesmo estágio na manhã seguinte, em vez de avançar. | falhou |
| 4 | A planta só avança se foi regada no dia anterior: a que fica sem rega no dia fica parada na manhã seguinte. | inconclusivo |
| 5 | A chuva e a tempestade regam os canteiros e contam para o avanço do crescimento como a rega com o regador. | falhou |
| 6 | Cavar um canteiro leva cerca de 15 a 16 minutos com a pá, e plantar um rabanete cerca de 6 minutos. | cumpriu |
| 7 | Os canteiros regados hoje (001 a 003) passam direto de crescendo para madura às 06:00 de amanhã, e os plantados hoje (005 e 006) vão a broto. | falhou |
| 8 | A rega do dia 8 (feita entre 06:08 e 06:29 nos plots 001 a 006) faz o plot-005 e o plot-006 avançarem de semente para broto no 06:00 do dia 9, e os plot-001 a… | falhou |
| 9 | O avanço de estágio depende da rega do dia anterior: plot-001 e plot-002 regados no dia 10 avançam de crescendo para madura no dia 11, e plot-003 não regado nã… | inconclusivo |
| 10 | A chuva conta como rega para a avanço: canteiros que não foram regados à mão também avançam na manhã seguinte. | inconclusivo |
| 11 | Dormir na cama recupera energia mesmo com a fome em 100, na mesma taxa de 12,5 por hora. | inconclusivo |
| 12 | Os canteiros 004 a 006, plantados no dia 5 e regados à mão no dia 12, amadurecem às 06:00 do dia 13, em 8 dias como os 001 a 003. | falhou |
| 13 | O 004 está parado porque não foi regado nos dias anteriores; com rega diária ele avança e amadurece. | falhou |
| 14 | A chuva rega todos os canteiros e avança as plantas como a rega manual, sem gastar regador. | inconclusivo |
| 15 | A chuva de ontem avançou os canteiros como a rega manual faria, e sem gastar regador: os que estão em broto e crescendo avançam mais um estágio no dia 16. | falhou |
| 16 | Uma planta que não foi regada no dia (como o plot-005 hoje) não avança de estágio na manhã seguinte, enquanto as regadas avançam. | falhou |
| 17 | O canteiro 007, que estava em semente e foi regado hoje, sobe para broto na manhã de amanhã. | cumpriu |
| 18 | O rabanete plantado hoje (plot-002, semente às 06:27 e regado às 07:09) segue o ritmo observado: broto amanhã e madura só depois de 6 dias, não 3. | falhou |
| 19 | O plot-002, regado nos dias 18 e 19, avança para broto na manhã do dia 20, mesmo sem a regra simples de um dia. | cumpriu |
| 20 | O plot-007 vira madura no amanhecer do dia 21, porque foi regado às 06:06 do dia 20, depois do último avanço. | cumpriu |
| 21 | O plot-002 vira madura no amanhecer do dia 22, pois foi regado às 06:20 do dia 21 e está em crescendo. | falhou |
| 22 | O plot-002 só vira madura depois de dois dias seguidos de rega (dias 21 e 22), e isso acontece às 06:00 do dia 23. | cumpriu |
| 23 | Tenho algum item guardado no baú (semente ou colheita) que não vi, e que daria para vender ou plantar. | falhou |
| 24 | Há algo na fazenda, fora do baú e da caixa, que dá para colher ou vender sem gastar moedas (planta silvestre, item no chão ou recompensa), e eu ainda não vi. | falhou |
| 25 | Há algo na fazenda, fora do leste, que dá para colher ou vender sem gastar moedas. | falhou |
| 26 | Há uma abertura no norte, mais a leste ou oeste de x=10, por onde se chega ao resto da fazenda. | cumpriu |
| 27 | O baú da casa guarda alguma reserva de comida ou moedas deixada antes, e é a única saída para o dia 28 sem renda. | falhou |
| 28 | Há planta silvestre ou item colhível na área ainda não vista a oeste da casa, que eu possa colher como comida sem gastar moedas. | - |

### opus: 28 experimentos (14 cumpriu, 7 falhou, 6 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Um rabanete regado avança um estágio por manhã na primavera e amadurece em uns 3 dias. | cumpriu |
| 2 | Na primavera, o rabanete regado sobe um estágio por dia e amadurece na 3ª manhã depois do plantio. | cumpriu |
| 3 | A chuva do dia 3 conta como rega para todos os canteiros, sem eu usar o regador. | cumpriu |
| 4 | Na manhã de tempestade, as plantas que amadurecem naquela mesma manhã podem ser derrubadas, e não só as que já estavam maduras na véspera. | falhou |
| 5 | Na primavera o tomate leva 4 manhãs da semente até madura, uma a mais que o rabanete. | inconclusivo |
| 6 | Na feira, a barraca paga pelo rabanete bem mais que a caixa (uns 30% a mais). | cumpriu |
| 7 | Com o fim da primavera, os tomates regados no dia 7 ainda amadurecem às 06:00 do dia 8, mesmo com o verão sendo estação fraca para o tomate. | falhou |
| 8 | No verão (estação fraca), os tomates em crescendo regados no dia 8 amadurecem na segunda manhã, às 06:00 do dia 9. | falhou |
| 9 | Os tomates de 021-024 e 001/009, em crescendo e regados pela chuva do dia 9, amadurecem às 06:00 do dia 10. | falhou |
| 10 | Os tomates em crescendo e regados nos dias 9 e 10 amadurecem às 06:00 do dia 11, depois de duas manhãs em crescendo. | cumpriu |
| 11 | O rabanete no verão (estação fraca) sai de semente para broto na primeira manhã, como o tomate, e só atrasa mais adiante. | falhou |
| 12 | No verão, o rabanete plantado e regado no regador (017, 018, 001, 009, plantados no dia 12) também fica em semente na primeira manhã, como os plantados com chu… | cumpriu |
| 13 | Na feira, a barraca paga mais por unidade do que a caixa pelo mesmo item no mesmo dia. | cumpriu |
| 14 | No verão, o milho, que está na estação boa, sai de semente para broto depois de uma única manhã regada. | inconclusivo |
| 15 | No outono, que é a estação fraca dele, o milho leva cerca de 2 manhãs regadas para sair de semente para broto. | inconclusivo |
| 16 | A couve, que está na estação boa no outono, sai de semente para broto em 1 manhã regada, mais rápido que o milho. | falhou |
| 17 | O rabanete no outono leva 2 manhãs regadas para sair de semente, mas depois avança 1 estágio por manhã. | falhou |
| 18 | O comprador paga às 06:00 pelo preço da caixa no momento em que pus os 2 rabanetes, perto dos 25 da tabela cada um. | cumpriu |
| 19 | Vender 6 rabanetes de uma vez derruba o preço cerca de 1 moeda por unidade, e ele só se recupera em parte de um dia para o outro. | cumpriu |
| 20 | A feira paga cerca de 20% acima da caixa, e cada unidade vendida derruba o preço dela uns 2–3%. | cumpriu |
| 21 | A virada para o inverno não atrasa rabanete, couve e cenoura: os canteiros regados no dia 21 avançam um estágio na manhã do dia 22, como no outono. | cumpriu |
| 22 | Milho parado no inverno, sem rega, não murcha nem perde estágio enquanto não houver seca. | cumpriu |
| 23 | O adubo faz o rabanete amadurecer pelo menos um dia antes. | inconclusivo |
| 24 | O adubo faz o rabanete amadurecer pelo menos um dia antes. | inconclusivo |
| 25 | O adubo faz o rabanete amadurecer pelo menos um dia antes. | inconclusivo |
| 26 | O adubo faz o rabanete amadurecer pelo menos um dia antes. | cumpriu |
| 27 | Na feira, o preço do rabanete na barraca cai cerca de 1 moeda a cada unidade vendida, como na caixa. | cumpriu |
| 28 | O adubo comprado no quiosque faz o rabanete amadurecer em 2 dias, mais rápido que os plantados hoje sem adubo. | - |

### opus-procedimento: 4 experimentos (3 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | [lugar: perto do poço] rabanete leva menos dias quando o canteiro fica ao lado do poço. | inconclusivo |
| 4 | [lugar: perto do poço] rabanete leva menos dias quando o canteiro fica ao lado do poço. | inconclusivo |
| 7 | [antes] rabanete leva mais dias quando o canteiro já teve rabanete antes do que num canteiro novo. | inconclusivo |
| 8 | [antes] milho leva mais dias quando o canteiro já teve rabanete antes do que num canteiro novo. | - |

### sonnet: 28 experimentos (8 cumpriu, 1 falhou, 18 inconclusivo, 1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | Um rabanete plantado e regado no dia 1 chega a broto ou crescendo no dia 2 às 06:00. | cumpriu |
| 2 | Rabanetes regados nos dias 1 e 2 estarão maduros ou crescendo no dia 3 às 06:00. | cumpriu |
| 3 | Rabanetes dos plots 001-005 estarão maduros no dia 4 às 06:00. | cumpriu |
| 4 | A chuva da tempestade do dia 5 rega todos os canteiros e as plantas avançam sem eu regar. | cumpriu |
| 5 | Plantar uma segunda leva de rabanete em canteiros vazios dá comida e moedas em cerca de 3 dias. | inconclusivo |
| 6 | A feira paga mais que a caixa de vendas pelo mesmo item. | cumpriu |
| 7 | Rabanete plantado hoje amadurece em cerca de 3 dias na primavera. | inconclusivo |
| 8 | Colher logo às 06:00 e comer evita a fome alta. | falhou |
| 9 | Plantar milho num canteiro vazio logo ao acordar dá colheita em cerca de 6 dias, no verão. | inconclusivo |
| 10 | Plantar milho num canteiro vazio logo ao acordar dá colheita em cerca de 6 dias, no verão. | inconclusivo |
| 11 | Milho plantado no dia 11 amadurece por volta do dia 17, no verão. | inconclusivo |
| 12 | O milho plantado no dia 11 amadurece por volta do dia 17. | inconclusivo |
| 13 | O milho plantado no dia 11 amadurece por volta do dia 17. | inconclusivo |
| 14 | O milho plantado no dia 11 amadurece por volta do dia 17. | inconclusivo |
| 15 | Plantas plantadas em dia de chuva já aparecem como regadas e crescem normalmente no outono. | inconclusivo |
| 16 | Comprar sementes às 08:00 e plantar em 013 evita canteiro vazio e rende mais que esperar. | inconclusivo |
| 17 | O rabanete plantado no plot-013 no dia 17 amadurece junto com os outros de plantio semelhante, em cerca de 5-6 dias (estação fraca). | inconclusivo |
| 18 | Os rabanetes plantados no dia 17 amadurecem entre os dias 22 e 23. | inconclusivo |
| 19 | Os rabanetes plantados hoje em 001, 004 e 005 amadurecem em cerca de 3 a 4 dias. | cumpriu |
| 20 | Vender os milhos na caixa rende bem mais que o rabanete por unidade (milho a 64). | cumpriu |
| 21 | O pagamento do comprador às 06:00 chega todo em moedas e cobre as sementes dos 3 canteiros vazios. | cumpriu |
| 22 | Com 315 moedas, um tacho e colheitas de inverno rendem mais que vender cru. | inconclusivo |
| 23 | Com 295 moedas, um tacho e morangos de inverno rendem mais que vender cru. | inconclusivo |
| 24 | Geleia de morango rende mais que morango cru, mesmo com o custo do tacho. | inconclusivo |
| 25 | Geleia de morango rende mais por morango que a venda crua. | inconclusivo |
| 26 | Geleia de morango rende mais por morango que a venda crua. | inconclusivo |
| 27 | Geleia de morango rende mais por morango que a venda crua. | inconclusivo |
| 28 | Geleia de morango rende mais por morango que a venda crua. | - |

### sonnet-procedimento: 1 experimentos (1 sem veredito)

| Dia | Hipótese | Veredito |
|---|---|---|
| 1 | [adubo] rabanete leva menos dias quando o canteiro é adubado antes de plantar. | - |

## A aderência ao procedimento

Contada por código a partir dos formatos fixos do procedimento (ADR-0074, decisão 35). As suspeitas da lista são o lugar do canteiro, `antes`, `adubo` e `estação`, lidas do que está entre os colchetes da hipótese. Um par são os dois canteiros citados no teste, plantados depois da noite do experimento no mesmo dia, com a mesma semente, e regados pelo avatar nos mesmos dias até o primeiro dos dois amadurecer ou se perder. As corridas sem o procedimento não conhecem os formatos e ficam como referência.

| Medida | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Procedimento | não | não | não | não | não | sim | não | não | sim | não | não | sim | não | não | não | sim | não | não | não | não | sim | sim | sim | não | não | não | sim | não | sim |
| Experimentos | 28 | 28 | 14 | 2 | 2 | 3 | 28 | 2 | 5 | 11 | 2 | 0 | 28 | 28 | 28 | 10 | 18 | 22 | 19 | 2 | 16 | 8 | 4 | 28 | 28 | 28 | 4 | 28 | 1 |
| Hipóteses com a [suspeita] no começo | 0 de 28 | 0 de 28 | 0 de 14 | 0 de 2 | 0 de 2 | 3 de 3 | 0 de 28 | 0 de 2 | 5 de 5 | 0 de 11 | 0 de 2 | 0 de 0 | 0 de 28 | 0 de 28 | 0 de 28 | 10 de 10 | 0 de 18 | 0 de 22 | 0 de 19 | 0 de 2 | 16 de 16 | 8 de 8 | 4 de 4 | 0 de 28 | 0 de 28 | 0 de 28 | 4 de 4 | 0 de 28 | 1 de 1 |
| Suspeitas da lista testadas | 0 de 4 | 0 de 4 | 0 de 4 | 0 de 4 | 0 de 4 | 2 de 4 (lugar, antes) | 0 de 4 | 0 de 4 | 3 de 4 (lugar, antes, adubo) | 0 de 4 | 0 de 4 | 0 de 4 | 0 de 4 | 0 de 4 | 0 de 4 | 2 de 4 (adubo, estação), 6 fora da lista | 0 de 4 | 0 de 4 | 0 de 4 | 0 de 4 | 2 de 4 (lugar, estação), 14 fora da lista | 3 de 4 (lugar, antes, adubo), 3 fora da lista | 2 de 4 (lugar, adubo) | 0 de 4 | 0 de 4 | 0 de 4 | 2 de 4 (lugar, antes) | 0 de 4 | 1 de 4 (adubo) |
| Pares plantados depois da noite | 9 de 28 | 8 de 28 | 3 de 14 | 0 de 2 | 0 de 2 | 2 de 3 | 1 de 28 | 0 de 2 | 3 de 5 | 2 de 11 | 0 de 2 | 0 de 0 | 9 de 28 | 9 de 28 | 7 de 28 | 2 de 10 | 2 de 18 | 6 de 22 | 1 de 19 | 0 de 2 | 1 de 16 | 4 de 8 | 2 de 4 | 6 de 28 | 3 de 28 | 0 de 28 | 1 de 4 | 0 de 28 | 0 de 1 |
| Pares no mesmo dia, mesma semente, mesma rega | 4 de 28 | 5 de 28 | 2 de 14 | 0 de 2 | 0 de 2 | 2 de 3 | 0 de 28 | 0 de 2 | 3 de 5 | 0 de 11 | 0 de 2 | 0 de 0 | 3 de 28 | 3 de 28 | 2 de 28 | 2 de 10 | 2 de 18 | 5 de 22 | 1 de 19 | 0 de 2 | 0 de 16 | 2 de 8 | 0 de 4 | 3 de 28 | 2 de 28 | 0 de 28 | 0 de 4 | 0 de 28 | 0 de 1 |
| Vereditos | 27 (5 cumpriu, 11 falhou, 11 inconclusivo) | 27 (15 cumpriu, 3 falhou, 9 inconclusivo) | 13 (10 cumpriu, 3 falhou) | 1 (1 cumpriu) | 1 (1 cumpriu) | 2 (2 inconclusivo) | 27 (10 cumpriu, 9 falhou, 8 inconclusivo) | 1 (1 cumpriu) | 4 (1 falhou, 3 inconclusivo) | 10 (2 cumpriu, 6 falhou, 2 inconclusivo) | 1 (1 cumpriu) | 0 | 27 (8 cumpriu, 9 falhou, 10 inconclusivo) | 27 (4 cumpriu, 8 falhou, 15 inconclusivo) | 27 (9 cumpriu, 4 falhou, 14 inconclusivo) | 8 (2 cumpriu, 3 falhou, 3 inconclusivo) | 13 (4 cumpriu, 7 falhou, 2 inconclusivo) | 19 (6 cumpriu, 7 falhou, 6 inconclusivo) | 17 (7 cumpriu, 6 falhou, 4 inconclusivo) | 1 (1 cumpriu) | 12 (2 cumpriu, 3 falhou, 7 inconclusivo) | 7 (7 inconclusivo) | 3 (3 inconclusivo) | 27 (8 cumpriu, 6 falhou, 13 inconclusivo) | 27 (7 cumpriu, 14 falhou, 6 inconclusivo) | 27 (14 cumpriu, 7 falhou, 6 inconclusivo) | 3 (3 inconclusivo) | 27 (8 cumpriu, 1 falhou, 18 inconclusivo) | 0 |
| Dias com a anotação HOJE: | 0 de 28 | 0 de 28 | 0 de 14 | 0 de 2 | 0 de 2 | 14 de 14 | 0 de 28 | 0 de 2 | 14 de 14 | 0 de 12 | 0 de 2 | 1 de 1 | 0 de 28 | 0 de 28 | 0 de 28 | 13 de 28 | 0 de 28 | 0 de 28 | 0 de 28 | 0 de 2 | 14 de 28 | 20 de 28 | 11 de 28 | 0 de 28 | 0 de 28 | 0 de 28 | 14 de 14 | 0 de 28 | 14 de 14 |
| Anotações VI: | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 40 | 0 | 0 | 0 | 0 | 0 | 0 | 299 | 0 | 0 | 0 | 0 | 308 | 454 | 368 | 0 | 0 | 0 | 14 | 0 | 25 |

## O valor de saber

As três réguas em cada mapa: o script 2 não sabe as regras ocultas e não aprende, o script 3 aprende pelo caderno de campo e o oráculo é o mesmo código sabendo as regras. Cada célula traz as moedas no fim, as colheitas e os dias com a fome em 100, uma corrida depois da outra quando há repetições. A distância entre o oráculo e o script 2 é o que saber vale naquele mapa; onde o script 3 fica nessa distância é o que aprender captou.

| Quem | Mapa a | Mapa b | Mapa c | Mapa d |
|---|---|---|---|---|
| script 2 (não sabe) | 85 moedas · 38 colheitas · 19 dias | 85 moedas · 38 colheitas · 19 dias | 85 moedas · 38 colheitas · 19 dias | 85 moedas · 38 colheitas · 19 dias |
| script 3 (aprende) | 5 moedas · 50 colheitas · 9 dias | 119 moedas · 79 colheitas · 2 dias | 54 moedas · 58 colheitas · 8 dias | 84 moedas · 70 colheitas · 6 dias |
| oráculo (sabe) | 247 moedas · 104 colheitas · 5 dias | 817 moedas · 117 colheitas · 0 dias | 300 moedas · 90 colheitas · 3 dias | 1113 moedas · 117 colheitas · 0 dias |
| humano, que sabe as regras e não o mapa (15 dias) | - | - | - | 2 moedas · 47 colheitas · 1 dias |
| Claude Haiku 5.5 com memória | - | - | - | 1 e 0 e 5 moedas · 47 e 48 e 19 colheitas · 7 e 12 e 15 dias |
| GPT-6 Astra (flex) com memória | - | - | - | 117 moedas · 71 colheitas · 0 dias |
| GPT-6 Astra (flex) com memória (14 dias) | - | - | - | 187 moedas · 31 colheitas · 3 dias |
| GPT-6 Astra (flex) com memória (2 dias) | - | - | - | 69 e 47 moedas · 0 e 0 colheitas · 0 e 0 dias |
| GPT-6 Astra (flex) com memória e o playbook 4 (14 dias) | - | - | - | 71 moedas · 24 colheitas · 3 dias |
| Claude Fable 5.1 com memória | - | - | - | 641 moedas · 106 colheitas · 4 dias |
| Claude Fable 5.1 com memória (2 dias) | - | - | - | 42 moedas · 0 colheitas · 0 dias |
| Claude Fable 5.1 com memória e o playbook 4 (14 dias) | - | - | - | 217 moedas · 50 colheitas · 2 dias |
| Gemini 4 Argon (flex) com memória (12 dias) | - | - | - | 1 moedas · 38 colheitas · 2 dias |
| Gemini 4 Argon (flex) com memória (2 dias) | - | - | - | 3 moedas · 0 colheitas · 0 dias |
| Gemini 4 Argon (flex) com memória e o playbook 4 (1 dia) | - | - | - | 24 moedas · 0 colheitas · 0 dias |
| Claude Haiku 5.5 com memória e a comparação | - | - | - | 9 e 52 moedas · 18 e 57 colheitas · 20 e 7 dias |
| Claude Haiku 5.5 com memória e o conselheiro | - | - | - | 71 moedas · 65 colheitas · 5 dias |
| Claude Haiku 5.5 com memória e o caderno completo | - | - | - | 44 e 236 e 0 moedas · 42 e 58 e 20 colheitas · 11 e 8 e 16 dias |
| Claude Haiku 5.5 pela OpenRouter com memória (2 dias) | - | - | - | 100 moedas · 0 colheitas · 0 dias |
| Claude Haiku 5.5 com memória e o playbook 4 | - | - | - | 8 e 4 e 0 moedas · 10 e 28 e 29 colheitas · 19 e 15 e 13 dias |
| Claude Opus 5.5 com memória | - | - | - | 586 moedas · 156 colheitas · 2 dias |
| Claude Opus 5.5 com memória e o playbook 4 (14 dias) | - | - | - | 122 moedas · 41 colheitas · 3 dias |
| Claude Sonnet 5.5 com memória | - | - | - | 401 moedas · 74 colheitas · 6 dias |
| Claude Sonnet 5.5 com memória e o playbook 4 (14 dias) | - | - | - | 62 moedas · 22 colheitas · 4 dias |
| o valor de saber (oráculo menos script 2) | +162 moedas, +14 dias sem fome | +732 moedas, +19 dias sem fome | +215 moedas, +16 dias sem fome | +1028 moedas, +19 dias sem fome |

## A fração do valor de saber capturada, no mapa d

No ano do mapa d, planejar (o script 3 fixo menos o script 2) vale -3 moedas e +34 colheitas; saber (o oráculo menos o script 3 fixo) vale +1031 moedas e +45 colheitas. A fração capturada é o controlador menos o script 3 fixo, dividido por esse valor de saber: 0% é não aprender nada, 100% é saber as regras, e abaixo de zero o controlador foi pior que o script que não aprende. Cada corrida é comparada com as réguas no dia em que parou; no começo do ano, saber ainda vale pouco em moedas, e a fração oscila mais.

| Corrida | Dias | Moedas (fração) | Colheitas (fração) |
|---|---|---|---|
| humano | 15 | 2 (-257%) | 47 (78%) |
| haiku | 28 | 1 (-8%) | 47 (-56%) |
| astra | 28 | 117 (3%) | 71 (-2%) |
| astra-consertado | 14 | 187 (183%) | 31 (-11%) |
| astra-consertado-piloto | 2 | 69 (-) | 0 (-) |
| astra-piloto | 2 | 47 (-) | 0 (-) |
| astra-procedimento | 14 | 71 (-93%) | 24 (-50%) |
| fable | 28 | 641 (54%) | 106 (76%) |
| fable-piloto | 2 | 42 (-) | 0 (-) |
| fable-procedimento | 14 | 217 (255%) | 50 (94%) |
| gemini | 12 | 1 (-29%) | 38 (75%) |
| gemini-piloto | 2 | 3 (-) | 0 (-) |
| gemini-procedimento | 1 | 24 (-) | 0 (-) |
| haiku-comparar | 28 | 9 (-7%) | 18 (-120%) |
| haiku-comparar-r2 | 28 | 52 (-3%) | 57 (-33%) |
| haiku-conselheiro | 28 | 71 (-1%) | 65 (-16%) |
| haiku-dados | 28 | 44 (-4%) | 42 (-67%) |
| haiku-dados-r2 | 28 | 236 (15%) | 58 (-31%) |
| haiku-dados-r3 | 28 | 0 (-8%) | 20 (-116%) |
| haiku-openrouter | 2 | 100 (-) | 0 (-) |
| haiku-procedimento | 28 | 8 (-7%) | 10 (-138%) |
| haiku-procedimento-r2 | 28 | 4 (-8%) | 28 (-98%) |
| haiku-procedimento-r3 | 28 | 0 (-8%) | 29 (-96%) |
| haiku-r2 | 28 | 0 (-8%) | 48 (-53%) |
| haiku-r3 | 28 | 5 (-7%) | 19 (-118%) |
| opus | 28 | 586 (49%) | 156 (187%) |
| opus-procedimento | 14 | 122 (29%) | 41 (44%) |
| script3-d | 28 | 84 (0%) | 70 (-4%) |
| sonnet | 28 | 401 (31%) | 74 (4%) |
| sonnet-procedimento | 14 | 62 (-114%) | 22 (-61%) |

## O que o script 3 aprendeu

O efeito de cada atributo no ritmo da planta, em vezes, com o intervalo de 90% e quantos plantios o mediram. A verdade: a até 4 tiles da água, 1,5 (R-001); repetir a cultura, 0,6 (R-003); o adubo, 1,5. A mata, o caminho e a porta são distratores: o efeito verdadeiro é 1. Um efeito conta como aprendido (✓) quando o intervalo, corrigido pelas comparações múltiplas (o erro de 10% repartido entre os atributos do modelo: uns 99,5% em vez de 90%), não inclui o 1 (ADR-0074).

| Atributo | script3-a | script3-b | script3-c | script3-d |
|---|---|---|---|---|
| agua<=2 | 1,19 (0,92 a 1,53) · 3 | 1,33 (1,08 a 1,63) · 16 | 1,28 (0,97 a 1,69) · 1 | 1,37 (1,16 a 1,63) · 7 ✓ |
| agua<=4 | 1,40 (1,08 a 1,82) · 3 | 1,32 (1,08 a 1,61) · 10 | 1,24 (1,02 a 1,51) · 5 | 1,43 (1,20 a 1,69) · 8 ✓ |
| agua<=8 | 0,90 (0,71 a 1,15) · 8 | 0,88 (0,71 a 1,08) · 16 | 0,80 (0,63 a 1,03) · 3 | 0,98 (0,83 a 1,16) · 15 |
| agua<=16 | 0,95 (0,74 a 1,23) · 16 | 0,89 (0,72 a 1,10) · 15 | 0,89 (0,76 a 1,04) · 14 | 0,85 (0,70 a 1,03) · 22 |
| mata<=2 | 1,13 (0,87 a 1,48) · 8 | 1,08 (0,88 a 1,33) · 12 | 1,19 (0,95 a 1,48) · 8 | 1,09 (0,89 a 1,33) · 22 |
| caminho<=2 | 1,07 (0,83 a 1,37) · 11 | 1,16 (0,94 a 1,43) · 20 | 1,04 (0,86 a 1,27) · 15 | 1,04 (0,85 a 1,29) · 16 |
| porta<=2 | 0,96 (0,73 a 1,26) · 1 | 1,03 (0,82 a 1,29) · 3 | 1,00 (0,66 a 1,51) · 0 | 1,00 (0,66 a 1,51) · 0 |
| repetida | 0,56 (0,51 a 0,63) · 18 ✓ | 0,49 (0,46 a 0,54) · 18 ✓ | 0,61 (0,55 a 0,69) · 21 ✓ | 0,55 (0,51 a 0,59) · 23 ✓ |
| adubada | 1,00 (0,66 a 1,51) · 0 | 1,00 (0,66 a 1,51) · 0 | 1,00 (0,66 a 1,51) · 0 | 1,00 (0,66 a 1,51) · 0 |

## Os juízes

Os juízes (Claude Opus 5.5, GPT-6 Astra) leem as crenças do fim de cada corrida com memória, sem saber de quem são, e dão um veredito por regra oculta: **a causa** (a crença diz o mecanismo e serviria num mapa novo), **só o lugar** (um lugar é melhor, sem o porquê) ou **não**. Numa corrida com a regra desligada, "a causa" é uma descoberta falsa. A célula traz o veredito de referência: o do Claude Opus 5.5, e, na corrida da família dele, o do outro juiz, marcado entre colchetes (ADR-0074, decisão 12). Quando o outro discorda, o veredito dele vem depois do ponto. A rubrica fica em `cartridges/<cartucho>/eval/juiz.yaml`, e cada chamada na fita `juiz.jsonl` da corrida. Os dois concordam em 250 de 252 vereditos. Custo: Claude Opus 5.5, US$ 1,65; GPT-6 Astra, US$ 2,83.

| Regra | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agua | não | não | não | não | não | não | não | não | não · GPT-6 Astra: só o lugar | não | não | não | não | não | não (regra desligada) | não | não | não | não | não | não | não | não | não | não [GPT-6 Astra] | não [GPT-6 Astra] | não | não |
| corvos | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não · GPT-6 Astra: só o lugar | não | não | não | não | não | não | não | não | não [GPT-6 Astra] | não [GPT-6 Astra] | não | não |
| fadiga | não | não | não | não | não | não | não | não | só o lugar (bel-0009) | não | não | não | não | não | não | não | não | não | não | não | a causa (bel-0013) | não | não | não | não [GPT-6 Astra] | não [GPT-6 Astra] | não | não |
| reputacao | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não [GPT-6 Astra] | não [GPT-6 Astra] | não | não |
| tomate | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não [GPT-6 Astra] | não [GPT-6 Astra] | não | não |
| alho | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não [GPT-6 Astra] | não [GPT-6 Astra] | não | não |
| bau | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não [GPT-6 Astra] | não [GPT-6 Astra] | não | não |
| ensopado | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não | não [GPT-6 Astra] | não [GPT-6 Astra] | não | não |
| adubo | não | não | não | não | não | não | a causa (bel-0024) | não | não | não | não | não | não | não | a causa (bel-0012) | não | não | não | não | não | não | não | não | não | a causa (bel-0023) [GPT-6 Astra] | não [GPT-6 Astra] | não | não |

## A exploração

Lida do arquivo: o que o avatar viu (as fotos e os deltas da percepção) e onde cavou e plantou. As zonas usam a verdade das regras ocultas, que o avaliador pode saber: a várzea fica a até 4 tiles da água (R-001) e longe é a mais de 18 tiles da porta, onde os corvos comem sem espantalho a até 6 tiles (R-002); repetir a cultura do canteiro é a fadiga do solo (R-003).

| Métrica | script2-a | script2-b | script2-c | script3-a | script3-b | script3-c | oraculo-a | oraculo-b | oraculo-c | humano | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | oraculo-d | script2-d | script3-d | script3-fixo-a | script3-fixo-b | script3-fixo-c | script3-fixo-d | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tiles vistos | 2500 (98%) | 2500 (98%) | 2494 (97%) | 2560 (100%) | 2560 (100%) | 2551 (100%) | 2533 (99%) | 2548 (100%) | 2545 (99%) | 2543 (99%) | 1245 (49%) | 1593 (62%) | 1397 (55%) | 1181 (46%) | 1183 (46%) | 1373 (54%) | 2466 (96%) | 1322 (52%) | 2260 (88%) | 1284 (50%) | 2137 (83%) | 1255 (49%) | 1192 (47%) | 1292 (50%) | 1363 (53%) | 2179 (85%) | 1451 (57%) | 1269 (50%) | 1103 (43%) | 732 (29%) | 1269 (50%) | 1213 (47%) | 1160 (45%) | 1370 (54%) | 1398 (55%) | 1347 (53%) | 1379 (54%) | 2495 (97%) | 2500 (98%) | 2560 (100%) | 2533 (99%) | 2551 (100%) | 2545 (99%) | 2551 (100%) | 1262 (49%) | 1171 (46%) |
| Viu 90% do mapa no dia | 2 | 2 | 2 | 1 | 1 | 1 | 2 | 2 | 2 | 1 | - | - | - | - | - | - | 11 | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | 2 | 2 | 1 | 2 | 2 | 2 | 2 | - | - |
| A primeira água à vista | dia 2, 08:16 | dia 1, 06:02 | dia 1, 11:59 | dia 1, 06:04 | dia 1, 06:02 | dia 1, 10:34 | dia 2, 10:03 | dia 1, 06:02 | dia 1, 10:23 | dia 1, 06:02 | dia 1, 06:18 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 8, 06:02 | dia 2, 06:18 | dia 2, 06:16 | dia 6, 08:07 | dia 2, 09:21 | dia 2, 08:07 | dia 5, 06:47 | dia 1, 06:02 | dia 2, 06:15 | dia 1, 06:02 | dia 2, 06:13 | dia 2, 09:02 | dia 2, 08:34 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 1, 06:02 | dia 2, 10:03 | dia 1, 06:02 | dia 1, 10:23 | dia 1, 06:02 | dia 1, 06:03 | dia 1, 06:03 |
| Canteiros cavados (várzea / várzea longe / longe / resto) | 0 / 0 / 0 / 16 | 0 / 0 / 0 / 16 | 0 / 0 / 0 / 16 | 3 / 7 / 2 / 11 | 10 / 4 / 5 / 16 | 0 / 8 / 5 / 13 | 60 / 0 / 0 / 16 | 64 / 0 / 0 / 0 | 0 / 0 / 0 / 73 | 25 / 0 / 0 / 1 | 0 / 0 / 0 / 14 | 0 / 0 / 0 / 23 | 0 / 0 / 0 / 20 | 0 / 0 / 0 / 13 | 0 / 0 / 0 / 15 | 0 / 0 / 0 / 16 | 0 / 0 / 0 / 70 | 0 / 0 / 0 / 23 | 0 / 0 / 0 / 48 | 0 / 0 / 0 / 35 | 0 / 0 / 0 / 19 | 0 / 0 / 0 / 10 | 0 / 0 / 0 / 6 | 0 / 0 / 0 / 19 | 0 / 0 / 0 / 18 | 0 / 0 / 0 / 8 | 0 / 0 / 2 / 11 | 0 / 0 / 0 / 16 | 0 / 0 / 0 / 10 | 0 / 0 / 0 / 4 | 0 / 0 / 0 / 7 | 0 / 0 / 0 / 9 | 0 / 0 / 0 / 7 | 0 / 0 / 0 / 17 | 0 / 0 / 0 / 7 | 19 / 0 / 0 / 38 | 0 / 0 / 0 / 23 | 64 / 0 / 0 / 0 | 0 / 0 / 0 / 16 | 5 / 1 / 3 / 22 | 0 / 0 / 0 / 18 | 0 / 0 / 0 / 18 | 0 / 0 / 0 / 18 | 0 / 0 / 0 / 18 | 0 / 0 / 0 / 30 | 0 / 0 / 0 / 11 |
| Plantios (várzea / várzea longe / longe / resto) | 0 / 0 / 0 / 54 | 0 / 0 / 0 / 54 | 0 / 0 / 0 / 54 | 7 / 10 / 6 / 40 | 48 / 15 / 5 / 42 | 0 / 17 / 9 / 47 | 88 / 0 / 0 / 36 | 137 / 0 / 0 / 0 | 0 / 0 / 0 / 111 | 58 / 0 / 0 / 0 | 0 / 0 / 0 / 60 | 0 / 0 / 0 / 90 | 0 / 0 / 0 / 51 | 0 / 0 / 0 / 13 | 0 / 0 / 0 / 15 | 0 / 0 / 0 / 39 | 0 / 0 / 0 / 147 | 0 / 0 / 0 / 23 | 0 / 0 / 0 / 89 | 0 / 0 / 0 / 61 | 0 / 0 / 0 / 19 | 0 / 0 / 0 / 10 | 0 / 0 / 0 / 21 | 0 / 0 / 0 / 75 | 0 / 0 / 0 / 82 | 0 / 0 / 0 / 26 | 0 / 0 / 6 / 49 | 0 / 0 / 0 / 73 | 0 / 0 / 0 / 20 | 0 / 0 / 0 / 4 | 0 / 0 / 0 / 15 | 0 / 0 / 0 / 28 | 0 / 0 / 0 / 32 | 0 / 0 / 0 / 55 | 0 / 0 / 0 / 19 | 81 / 0 / 0 / 135 | 0 / 0 / 0 / 64 | 140 / 0 / 0 / 0 | 0 / 0 / 0 / 54 | 18 / 4 / 6 / 66 | 0 / 0 / 0 / 90 | 0 / 0 / 0 / 90 | 0 / 0 / 0 / 90 | 0 / 0 / 0 / 90 | 0 / 0 / 0 / 102 | 0 / 0 / 0 / 32 |
| Plantios na várzea depois de ver a água | 0 de 38 | 0 de 54 | 0 de 44 | 17 de 63 | 63 de 110 | 17 de 63 | 88 de 108 | 137 de 137 | 0 de 101 | 58 de 58 | 0 de 60 | 0 de 90 | 0 de 51 | 0 de 13 | 0 de 15 | 0 de 39 | 0 de 147 | 0 de 23 | 0 de 89 | 0 de 61 | 0 de 19 | 0 de 10 | 0 de 12 | 0 de 71 | 0 de 78 | 0 de 14 | 0 de 50 | 0 de 71 | 0 de 11 | 0 de 4 | 0 de 12 | 0 de 28 | 0 de 29 | 0 de 50 | 0 de 15 | 81 de 216 | 0 de 64 | 140 de 140 | 0 de 54 | 22 de 94 | 0 de 74 | 0 de 90 | 0 de 80 | 0 de 90 | 0 de 102 | 0 de 32 |
| Plantios longe sem espantalho | 0 | 0 | 0 | 16 | 20 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| Distância média dos canteiros à porta | 7,9 | 7,9 | 7,9 | 22,9 | 14,0 | 31,6 | 14,2 | 11,7 | 12,7 | 14,3 | 4,4 | 6,9 | 5,5 | 6,8 | 7,1 | 4,8 | 8,6 | 7,0 | 8,9 | 8,2 | 6,3 | 6,5 | 5,3 | 7,8 | 7,6 | 5,4 | 12,5 | 5,8 | 4,9 | 2,2 | 5,6 | 4,8 | 4,9 | 7,5 | 6,3 | 8,8 | 8,0 | 9,7 | 7,9 | 12,5 | 7,4 | 7,4 | 7,4 | 7,4 | 4,3 | 3,3 |
| Repetiram a cultura do canteiro | 24 de 38 | 24 de 38 | 24 de 38 | 31 de 40 | 29 de 75 | 36 de 47 | 8 de 48 | 3 de 73 | 8 de 38 | 22 de 34 | 40 de 46 | 67 de 67 | 31 de 31 | 0 de 0 | 0 de 0 | 23 de 23 | 52 de 88 | 0 de 0 | 28 de 50 | 19 de 31 | 0 de 0 | 0 de 0 | 15 de 15 | 46 de 56 | 58 de 64 | 18 de 18 | 39 de 42 | 42 de 57 | 9 de 10 | 0 de 0 | 5 de 8 | 19 de 19 | 25 de 25 | 35 de 38 | 12 de 12 | 94 de 159 | 31 de 41 | 4 de 76 | 24 de 38 | 34 de 63 | 71 de 72 | 71 de 72 | 71 de 72 | 71 de 72 | 50 de 72 | 16 de 21 |

## A prova do mundo

Perguntas fechadas sobre as regras ocultas, com "não sei" (que não conta contra). A mente faz a prova antes de o mundo começar, com a memória vazia (o que o modelo supõe), e no fim, com o que lembra: antes → depois. O script 3 e o oráculo não respondem: o avaliador lê a crença deles e escolhe a opção que ela sustenta, só nas perguntas que o modelo deles cobre; o oráculo, com a verdade no lugar da crença, confere o gabarito. As perguntas e o gabarito ficam em `cartridges/<cartucho>/eval/prova.yaml`.

| Pergunta | Gabarito | script2-a | script2-b | script2-c | script3-a | script3-b | script3-c | oraculo-a | oraculo-b | oraculo-c | humano | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | oraculo-d | script2-d | script3-d | script3-fixo-a | script3-fixo-b | script3-fixo-c | script3-fixo-d | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| agua | perto | - | - | - | não sei | não sei | não sei | perto ✓ | perto ✓ | perto ✓ | - | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | perto ✓ | - | perto ✓ | não sei | não sei | não sei | não sei | perto ✓ → não sei | não sei → não sei |
| agua_alcance | quatro | - | - | - | não sei | não sei | não sei | quatro ✓ | quatro ✓ | quatro ✓ | - | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | quatro ✓ | - | quatro ✓ | não sei | não sei | não sei | não sei | não sei → não sei | não sei → não sei |
| corvos_longe | comida | - | - | - | comida ✓ | não sei | comida ✓ | comida ✓ | comida ✓ | comida ✓ | - | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → comida ✓ | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | comida ✓ | - | não sei | não sei | não sei | não sei | não sei | comida ✓ → comida ✓ | comida ✓ → comida ✓ |
| corvos_perto | sem_risco | - | - | - | sem_risco ✓ | sem_risco ✓ | não sei | sem_risco ✓ | sem_risco ✓ | sem_risco ✓ | - | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | sem_risco ✓ | - | sem_risco ✓ | não sei | não sei | não sei | não sei | não sei → maior ✗ | não sei → não sei |
| espantalho | seis | - | - | - | não sei | não sei | não sei | seis ✓ | seis ✓ | seis ✓ | - | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | seis ✓ | - | não sei | não sei | não sei | não sei | não sei | não sei → seis ✓ | não sei → não sei |
| fadiga | devagar | - | - | - | devagar ✓ | devagar ✓ | devagar ✓ | devagar ✓ | devagar ✓ | devagar ✓ | - | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → devagar ✓ | devagar ✓ | - | devagar ✓ | não sei | não sei | não sei | não sei | devagar ✓ → devagar ✓ | não sei → não sei |
| reputacao | mais | - | - | - | não sei | não sei | não sei | não sei | não sei | não sei | - | mais ✓ → mais ✓ | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → mais ✓ | não sei → não sei | não sei → não sei | não sei → mais ✓ | não sei → mais ✓ | não sei → não sei | não sei → não sei | não sei → mais ✓ | não sei → mais ✓ | não sei → não sei | não sei → mais ✓ | não sei → não sei | não sei → não sei | não sei → não sei | não sei | - | não sei | não sei | não sei | não sei | não sei | não sei → mais ✓ | não sei → não sei |
| tomate | murcha | - | - | - | não sei | não sei | não sei | não sei | não sei | não sei | - | não sei → para ✗ | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → para ✗ | não sei → não sei | não sei → para ✗ | para ✗ → não sei | para ✗ → para ✗ | não sei → para ✗ | para ✗ → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei | - | não sei | não sei | não sei | não sei | não sei | não sei → murcha ✓ | não sei → não sei |
| alho | cresce | - | - | - | não sei | não sei | não sei | não sei | não sei | não sei | - | não sei → para ✗ | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → para ✗ | não sei → não sei | não sei → não sei | para ✗ → não sei | para ✗ → para ✗ | não sei → para ✗ | para ✗ → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei | - | não sei | não sei | não sei | não sei | não sei | não sei → para ✗ | não sei → não sei |
| bau | inventario | - | - | - | não sei | não sei | não sei | não sei | não sei | não sei | - | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | inventario ✓ → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | inventario ✓ → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei | - | não sei | não sei | não sei | não sei | não sei | não sei → não sei | não sei → não sei |
| ensopado | segura | - | - | - | não sei | não sei | não sei | não sei | não sei | não sei | - | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei → não sei | não sei | - | não sei | não sei | não sei | não sei | não sei | não sei → não sei | não sei → não sei |
| Acertos / erros / não sei |  | - | - | - | 3 / 0 / 8 | 2 / 0 / 9 | 2 / 0 / 9 | 6 / 0 / 5 | 6 / 0 / 5 | 6 / 0 / 5 | - | 1 / 0 / 10 → 1 / 2 / 8 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 1 / 0 / 10 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 1 / 2 / 8 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 1 / 10 | 0 / 2 / 9 → 2 / 0 / 9 | 0 / 2 / 9 → 1 / 2 / 8 | 0 / 0 / 11 → 0 / 2 / 9 | 1 / 2 / 8 → 0 / 0 / 11 | 0 / 0 / 11 → 1 / 0 / 10 | 0 / 0 / 11 → 1 / 0 / 10 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 1 / 0 / 10 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 0 / 0 / 11 | 0 / 0 / 11 → 1 / 0 / 10 | 6 / 0 / 5 | - | 4 / 0 / 7 | 0 / 0 / 11 | 0 / 0 / 11 | 0 / 0 / 11 | 0 / 0 / 11 | 3 / 0 / 8 → 5 / 2 / 4 | 1 / 0 / 10 → 1 / 0 / 10 |
| Custo da prova (US$) |  | - | - | - | - | - | - | - | - | - | - | 0,0032 | 0,1924 | 0,1234 | 0,1290 | 0,1294 | 0,2378 | 0,3324 | 0,3132 | 0,4039 | 0,0333 | 0,0341 | 0,0390 | 0,0030 | 0,0032 | 0,0031 | 0,0038 | 0,0034 | 0,0033 | 0,0030 | 0,0031 | 0,0035 | 0,0039 | 0,0036 | 0,0031 | 0,0029 | 0,1189 | 0,1421 | - | - | - | - | - | - | - | 0,0519 | 0,0624 |

## O custo por resultado

O que cada corrida de modelo gastou para chegar onde chegou (ADR-0074, decisão 28). O custo inclui o conselheiro e é o que o provedor cobrou (na OpenRouter, o que a resposta disse). "Acima do fixo" compara com o script 3 fixo do mesmo mapa, a régua do meio; abaixo dele, o custo por moeda fica vazio. "Regras achadas" conta os vereditos "a causa" do juiz de referência. As chamadas repetidas são as que o adaptador tentou de novo até responder (o flex às vezes fica indisponível); as da reserva, as que o flex não atendeu e o provedor normal sim, pelo preço normal (decisão 31). A latência p95 é a espera das chamadas lentas. As respostas sem ação são as que não escolheram nenhuma ferramenta: a mente as transforma em esperar 15 minutos, e o avatar fica parado (o Astra do M21 respondeu assim em quase metade das chamadas; plano do M22, §3).

| Medida | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Modelo | Claude Haiku 5.5 | GPT-6 Astra (flex) | GPT-6 Astra (flex) | GPT-6 Astra (flex) | GPT-6 Astra (flex) | GPT-6 Astra (flex) | Claude Fable 5.1 | Claude Fable 5.1 | Claude Fable 5.1 | Gemini 4 Argon (flex) | Gemini 4 Argon (flex) | Gemini 4 Argon (flex) | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Haiku 5.5 pela OpenRouter | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Haiku 5.5 | Claude Opus 5.5 | Claude Opus 5.5 | Claude Sonnet 5.5 | Claude Sonnet 5.5 |
| Custo (US$) | 0,81 | 27,32 | 10,42 | 1,50 | 2,11 | 11,76 | 70,12 | 5,08 | 36,75 | 3,30 | 0,64 | 0,28 | 0,55 | 0,90 | 4,08 | 0,60 | 0,84 | 0,92 | 0,57 | 0,11 | 0,62 | 0,73 | 0,73 | 0,79 | 0,59 | 35,07 | 11,91 | 12,14 | 4,40 |
| Custo por chamada (US$) | 0,0007 | 0,0146 | 0,0178 | 0,0170 | 0,0135 | 0,0154 | 0,0405 | 0,0361 | 0,0430 | 0,0051 | 0,0047 | 0,0047 | 0,0007 | 0,0007 | 0,0030 | 0,0008 | 0,0007 | 0,0008 | 0,0008 | 0,0016 | 0,0008 | 0,0008 | 0,0008 | 0,0007 | 0,0007 | 0,0174 | 0,0181 | 0,0076 | 0,0080 |
| Tokens por dia, em mil (entrada / saída / cache lido) | 8 / 17 / 1348 | 0 / 3 / 1215 | 5 / 4 / 811 | 6 / 3 / 767 | 0 / 3 / 1274 | 2 / 2 / 1065 | 9 / 15 / 2210 | 9 / 15 / 2215 | 13 / 16 / 2315 | 194 / 5 / 1120 | 234 / 5 / 1223 | 193 / 3 / 1086 | 6 / 13 / 872 | 12 / 17 / 1556 | 9 / 16 / 1651 | 10 / 14 / 943 | 13 / 17 / 1364 | 14 / 19 / 1482 | 9 / 14 / 866 | 393 / 12 / 643 | 8 / 15 / 982 | 9 / 16 / 1188 | 10 / 17 / 1178 | 8 / 16 / 1324 | 6 / 14 / 939 | 9 / 12 / 2505 | 11 / 9 / 1697 | 7 / 8 / 1832 | 8 / 6 / 1315 |
| Cache lido (da entrada) | 96% | 96% | 95% | 94% | 96% | 96% | 96% | 96% | 96% | 85% | 84% | 85% | 96% | 96% | 95% | 96% | 96% | 95% | 96% | 61% | 96% | 96% | 96% | 96% | 96% | 96% | 96% | 96% | 96% |
| Custo por colheita (US$) | 0,02 | 0,38 | 0,34 | - | - | 0,49 | 0,66 | - | 0,73 | 0,09 | - | - | 0,03 | 0,02 | 0,06 | 0,02 | 0,02 | 0,02 | 0,03 | - | 0,06 | 0,03 | 0,03 | 0,02 | 0,03 | 0,22 | 0,29 | 0,16 | 0,20 |
| Moedas acima do script 3 fixo do mesmo mapa | -81 | 35 | 105 | -13 | -35 | -11 | 559 | -40 | 135 | -81 | -79 | -58 | -73 | -30 | -11 | -74 | -38 | 154 | -82 | 18 | -74 | -78 | -82 | -82 | -77 | 504 | 40 | 319 | -20 |
| Custo por moeda acima do fixo (US$) | - | 0,780 | 0,099 | - | - | - | 0,125 | - | 0,272 | - | - | - | - | - | - | - | - | 0,006 | - | 0,006 | - | - | - | - | - | 0,070 | 0,298 | 0,038 | - |
| Regras achadas pela causa (juiz de referência) | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | - | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| Custo por regra achada (US$) | - | - | - | - | - | - | 70,12 | - | - | - | - | - | - | - | - | 0,60 | - | - | - | - | - | 0,73 | - | - | - | 35,07 | - | - | - |
| Latência mediana / p95 (s) | 1,5 / 4,4 | 2,0 / 3,2 | 3,3 / 8,1 | 3,8 / 8,2 | 2,1 / 3,7 | 2,5 / 10,5 | 2,1 / 8,0 | 2,0 / 7,6 | 2,7 / 7,9 | 5,3 / 22,1 | 5,4 / 20,5 | 7,1 / 193,9 | 1,7 / 8,8 | 1,6 / 5,5 | 1,6 / 5,3 | 1,5 / 5,1 | 1,3 / 4,3 | 1,4 / 4,1 | 1,5 / 4,7 | 1,9 / 6,1 | 1,5 / 4,9 | 1,4 / 4,5 | 1,4 / 4,9 | 1,6 / 4,4 | 1,7 / 4,9 | 2,4 / 4,9 | 2,0 / 4,5 | 1,7 / 3,0 | 1,6 / 2,7 |
| Chamadas repetidas / na reserva / que falharam | 0 / 0 / 0 | 0 / 0 / 0 | 2 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 19 / 1 / 14 | 4 / 0 / 3 | 7 / 4 / 4 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| Respostas sem ação | 4 de 1130 (0%) | 878 de 1872 (47%) | 0 de 586 (0%) | 0 de 88 (0%) | 73 de 156 (47%) | 326 de 762 (43%) | 4 de 1731 (0%) | 0 de 141 (0%) | 2 de 855 (0%) | 62 de 648 (10%) | 9 de 136 (7%) | 18 de 59 (31%) | 3 de 742 (0%) | 1 de 1288 (0%) | 3 de 1338 (0%) | 2 de 721 (0%) | 4 de 1152 (0%) | 5 de 1215 (0%) | 4 de 733 (1%) | 1 de 70 (1%) | 80 de 763 (10%) | 1 de 922 (0%) | 1 de 903 (0%) | 1 de 1090 (0%) | 36 de 801 (4%) | 7 de 2020 (0%) | 5 de 657 (1%) | 55 de 1603 (3%) | 35 de 548 (6%) |

## Lado a lado no dia 14

As corridas de 14 dias ao lado das mais longas, nos mesmos dias: os totais dos dias 1 a 14 de cada uma, e o que ela tinha no fim do dia 14. A corrida que parou antes mostra o último dia dela. As crenças, a prova e o juiz continuam sendo os do fim de cada corrida.

| Medida | script2-a | script2-b | script2-c | script3-a | script3-b | script3-c | oraculo-a | oraculo-b | oraculo-c | humano | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | oraculo-d | script2-d | script3-d | script3-fixo-a | script3-fixo-b | script3-fixo-c | script3-fixo-d | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Até o dia | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 2 | 2 | 14 | 14 | 2 | 14 | 12 | 2 | 1 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 2 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 | 14 |
| Moedas no fim | 145 | 145 | 145 | 84 | 97 | 89 | 119 | 117 | 134 | 2 | 2 | 8 | 187 | 69 | 47 | 71 | 13 | 42 | 217 | 1 | 3 | 24 | 27 | 18 | 0 | 3 | 165 | 4 | 8 | 100 | 8 | 21 | 97 | 8 | 5 | 64 | 122 | 152 | 145 | 84 | 110 | 110 | 110 | 110 | 215 | 62 |
| Colheitas | 32 | 32 | 32 | 25 | 32 | 25 | 39 | 51 | 32 | 39 | 15 | 23 | 31 | 0 | 0 | 24 | 38 | 0 | 50 | 38 | 0 | 0 | 7 | 28 | 20 | 16 | 20 | 20 | 10 | 0 | 9 | 12 | 11 | 13 | 10 | 50 | 41 | 51 | 32 | 26 | 33 | 33 | 33 | 33 | 21 | 22 |
| Plantios | 48 | 48 | 48 | 40 | 45 | 41 | 56 | 68 | 50 | 58 | 28 | 43 | 51 | 13 | 15 | 39 | 59 | 23 | 89 | 61 | 19 | 10 | 13 | 46 | 38 | 22 | 30 | 33 | 15 | 4 | 14 | 21 | 18 | 29 | 17 | 79 | 64 | 69 | 48 | 43 | 50 | 50 | 50 | 50 | 36 | 32 |
| Desmaios | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 2 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 3 | 3 | 3 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dias com a fome em 100 | 6 | 6 | 6 | 6 | 2 | 6 | 3 | 0 | 1 | 1 | 7 | 0 | 3 | 0 | 0 | 3 | 2 | 0 | 2 | 2 | 0 | 0 | 7 | 5 | 4 | 4 | 9 | 8 | 6 | 0 | 5 | 8 | 6 | 8 | 5 | 2 | 3 | 0 | 6 | 6 | 6 | 6 | 6 | 6 | 6 | 4 |
| Chamadas | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 504 | 833 | 586 | 88 | 156 | 762 | 671 | 141 | 855 | 648 | 136 | 59 | 382 | 586 | 582 | 403 | 535 | 528 | 396 | 70 | 403 | 526 | 437 | 489 | 427 | 733 | 657 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 559 | 548 |
| Custo do modelo (US$) | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,36 | 12,05 | 10,42 | 1,50 | 2,11 | 11,76 | 27,52 | 5,08 | 36,75 | 3,30 | 0,64 | 0,28 | 0,27 | 0,41 | 1,87 | 0,32 | 0,39 | 0,39 | 0,30 | 0,11 | 0,32 | 0,40 | 0,35 | 0,36 | 0,31 | 12,53 | 11,91 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 4,20 | 4,40 |

## Moedas por dia

A barra vai de 0 a 1113 moedas, um caractere por dia.

```
script2-a                ▁▁▁▁▂▂▂▂▂▂▂▁▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂
script2-b                ▁▁▁▁▂▂▂▂▂▂▂▁▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂
script2-c                ▁▁▁▁▂▂▂▂▂▂▂▁▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂
script3-a                ▂▂▂▁▂▂▁▁▁▁▁▁▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script3-b                ▂▂▁▁▁▁▂▂▂▂▂▁▁▂▂▁▁▂▂▂▁▁▁▂▁▂▁▂
script3-c                ▂▂▂▁▂▂▁▁▁▁▁▁▁▂▂▂▂▁▁▂▂▂▁▁▁▁▁▁
oraculo-a                ▁▁▁▁▁▁▁▁▁▁▁▂▂▂▂▂▁▁▁▁▁▁▁▂▂▂▂▃
oraculo-b                ▁▁▁▁▁▂▁▁▂▂▂▂▂▂▂▂▂▃▂▃▃▃▃▃▃▄▆▆
oraculo-c                ▁▁▁▁▁▁▁▁▁▁▁▂▂▂▂▁▁▂▁▁▂▂▁▂▂▂▂▃
humano                   ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku                    ▂▂▂▂▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
astra                    ▂▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▂
astra-consertado         ▂▁▁▁▁▂▂▁▁▁▁▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁
astra-consertado-piloto  ▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
astra-piloto             ▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
astra-procedimento       ▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
fable                    ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▃▁▁▁▁▁▁▅
fable-piloto             ▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
fable-procedimento       ▁▁▁▁▁▁▂▁▁▁▁▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁
gemini                   ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
gemini-piloto            ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
gemini-procedimento      ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-comparar           ▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-comparar-r2        ▂▂▂▂▁▂▂▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-conselheiro        ▂▂▁▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-controle           ▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-dados              ▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁
haiku-dados-r2           ▂▂▂▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▂▂▂▁▁▁▂▂
haiku-dados-r3           ▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-openrouter         ▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-procedimento       ▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-procedimento-r2    ▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-procedimento-r3    ▂▂▂▂▁▂▂▂▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-r2                 ▂▂▂▂▂▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-r3                 ▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
opus                     ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▃▃▂▁▂▁▂▅
opus-procedimento        ▁▁▁▁▁▁▁▁▁▁▁▁▁▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁
oraculo-d                ▁▁▁▁▁▂▁▁▂▂▂▂▂▂▂▂▂▃▃▃▃▃▃▄▄▃▆█
script2-d                ▁▁▁▁▂▂▂▂▂▂▂▁▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂
script3-d                ▂▂▂▁▂▂▁▁▁▁▁▁▁▂▁▁▁▁▁▂▂▁▁▂▂▂▁▂
script3-fixo-a           ▁▁▁▁▁▁▁▁▁▁▁▁▁▂▂▂▂▁▁▂▂▂▂▁▁▂▂▂
script3-fixo-b           ▁▁▁▁▁▁▁▁▁▁▁▁▁▂▂▂▂▁▁▂▂▂▂▁▁▂▂▂
script3-fixo-c           ▁▁▁▁▁▁▁▁▁▁▁▁▁▂▂▂▂▁▁▂▂▂▂▁▁▂▂▂
script3-fixo-d           ▁▁▁▁▁▁▁▁▁▁▁▁▁▂▂▂▂▁▁▂▂▂▂▁▁▂▂▂
sonnet                   ▂▁▁▁▁▁▂▂▁▁▁▁▂▂▂▂▁▂▂▁▁▃▃▂▃▃▂▄
sonnet-procedimento      ▂▁▁▂▂▂▂▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
```

| Dia | script2-a | script2-b | script2-c | script3-a | script3-b | script3-c | oraculo-a | oraculo-b | oraculo-c | humano | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | oraculo-d | script2-d | script3-d | script3-fixo-a | script3-fixo-b | script3-fixo-c | script3-fixo-d | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 35 | 35 | 35 | 100 | 100 | 100 | 69 | 58 | 69 | 47 | 100 | 100 | 100 | 100 | 100 | 100 | 7 | 80 | 27 | 0 | 0 | 24 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 35 | 47 | 58 | 35 | 100 | 69 | 69 | 69 | 69 | 100 | 100 |
| 2 | 35 | 35 | 35 | 100 | 100 | 100 | 27 | 27 | 27 | 1 | 233 | 58 | 69 | 69 | 47 | 100 | 7 | 42 | 7 | 2 | 3 | - | 100 | 101 | 100 | 85 | 182 | 169 | 39 | 100 | 100 | 100 | 100 | 180 | 58 | 24 | 5 | 27 | 35 | 100 | 27 | 27 | 27 | 27 | 53 | 32 |
| 3 | 35 | 35 | 35 | 100 | 23 | 100 | 27 | 7 | 27 | 1 | 233 | 16 | 38 | - | - | 100 | 7 | - | 7 | 2 | - | - | 100 | 101 | 47 | 85 | 182 | 169 | 39 | - | 100 | 100 | 100 | 180 | 58 | 24 | 5 | 7 | 35 | 100 | 27 | 27 | 27 | 27 | 53 | 32 |
| 4 | 21 | 21 | 21 | 11 | 47 | 11 | 7 | 34 | 7 | 6 | 233 | 179 | 7 | - | - | 101 | 5 | - | 8 | 2 | - | - | 100 | 101 | 16 | 85 | 182 | 169 | 39 | - | 100 | 100 | 100 | 180 | 58 | 4 | 6 | 34 | 21 | 11 | 7 | 7 | 7 | 7 | 11 | 126 |
| 5 | 235 | 235 | 235 | 109 | 72 | 109 | 3 | 24 | 3 | 6 | 233 | 65 | 27 | - | - | 101 | 3 | - | 6 | 0 | - | - | 100 | 59 | 1 | 50 | 117 | 169 | 39 | - | 59 | 116 | 35 | 139 | 58 | 15 | 15 | 24 | 235 | 109 | 53 | 53 | 53 | 53 | 11 | 126 |
| 6 | 235 | 235 | 235 | 109 | 72 | 109 | 6 | 80 | 6 | 6 | 144 | 0 | 179 | - | - | 48 | 3 | - | 2 | 12 | - | - | 58 | 132 | 131 | 8 | 117 | 169 | 39 | - | 59 | 116 | 139 | 139 | 58 | 2 | 15 | 80 | 235 | 109 | 66 | 66 | 66 | 66 | 1 | 126 |
| 7 | 235 | 235 | 235 | 58 | 106 | 58 | 74 | 60 | 6 | 1 | 144 | 0 | 126 | - | - | 48 | 2 | - | 99 | 3 | - | - | 58 | 193 | 66 | 8 | 218 | 169 | 39 | - | 59 | 74 | 97 | 139 | 5 | 2 | 15 | 60 | 235 | 58 | 66 | 66 | 66 | 66 | 181 | 126 |
| 8 | 235 | 235 | 235 | 58 | 86 | 58 | 74 | 7 | 6 | 1 | 144 | 0 | 73 | - | - | 48 | 2 | - | 15 | 3 | - | - | 58 | 193 | 66 | 8 | 218 | 169 | 8 | - | 59 | 74 | 97 | 97 | 5 | 2 | 15 | 7 | 235 | 58 | 66 | 66 | 66 | 66 | 181 | 126 |
| 9 | 235 | 235 | 235 | 48 | 86 | 58 | 74 | 86 | 6 | 22 | 144 | 0 | 73 | - | - | 48 | 2 | - | 5 | 3 | - | - | 58 | 193 | 25 | 8 | 218 | 87 | 8 | - | 59 | 74 | 97 | 97 | 5 | 2 | 15 | 86 | 235 | 48 | 66 | 66 | 66 | 66 | 75 | 126 |
| 10 | 235 | 235 | 235 | 48 | 86 | 58 | 64 | 90 | 33 | 22 | 144 | 0 | 73 | - | - | 48 | 2 | - | 5 | 3 | - | - | 58 | 193 | 25 | 44 | 218 | 67 | 8 | - | 59 | 74 | 97 | 97 | 5 | 2 | 15 | 90 | 235 | 48 | 66 | 66 | 66 | 66 | 75 | 20 |
| 11 | 235 | 235 | 235 | 48 | 86 | 58 | 11 | 112 | 2 | 2 | 55 | 0 | 73 | - | - | 48 | 1 | - | 5 | 0 | - | - | 58 | 193 | 5 | 13 | 218 | 14 | 8 | - | 59 | 74 | 97 | 97 | 5 | 73 | 15 | 112 | 235 | 48 | 56 | 56 | 56 | 56 | 75 | 20 |
| 12 | 13 | 13 | 13 | 6 | 76 | 5 | 119 | 108 | 134 | 2 | 55 | 0 | 31 | - | - | 17 | 16 | - | 4 | 1 | - | - | 27 | 193 | 5 | 13 | 218 | 14 | 8 | - | 18 | 21 | 97 | 8 | 5 | 31 | 12 | 108 | 13 | 6 | 25 | 25 | 25 | 25 | 75 | 0 |
| 13 | 145 | 145 | 145 | 115 | 76 | 3 | 119 | 116 | 134 | 2 | 2 | 8 | 11 | - | - | 7 | 6 | - | 38 | - | - | - | 27 | 101 | 20 | 13 | 218 | 14 | 8 | - | 8 | 21 | 97 | 8 | 5 | 11 | 12 | 116 | 145 | 41 | 25 | 25 | 25 | 25 | 215 | 0 |
| 14 | 145 | 145 | 145 | 84 | 97 | 89 | 119 | 117 | 134 | 2 | 2 | 8 | 187 | - | - | 71 | 13 | - | 217 | - | - | - | 27 | 18 | 0 | 3 | 165 | 4 | 8 | - | 8 | 21 | 97 | 8 | 5 | 64 | 122 | 152 | 145 | 84 | 110 | 110 | 110 | 110 | 215 | 62 |
| 15 | 145 | 145 | 145 | 74 | 97 | 89 | 119 | 117 | 134 | 2 | 2 | 8 | - | - | - | - | 3 | - | - | - | - | - | 27 | 64 | 0 | 3 | 145 | 47 | 8 | - | 8 | 21 | 66 | 8 | 5 | 11 | - | 152 | 145 | 64 | 110 | 110 | 110 | 110 | 215 | - |
| 16 | 145 | 145 | 145 | 64 | 44 | 89 | 99 | 93 | 55 | - | 2 | 7 | - | - | - | - | 3 | - | - | - | - | - | 27 | 64 | 0 | 3 | 145 | 47 | 10 | - | 8 | 21 | 66 | 8 | 5 | 6 | - | 102 | 145 | 64 | 110 | 110 | 110 | 110 | 215 | - |
| 17 | 145 | 145 | 145 | 44 | 60 | 89 | 68 | 96 | 59 | - | 2 | 7 | - | - | - | - | 6 | - | - | - | - | - | 17 | 64 | 24 | 3 | 83 | 47 | 10 | - | 8 | 1 | 66 | 7 | 5 | 20 | - | 93 | 145 | 64 | 110 | 110 | 110 | 110 | 75 | - |
| 18 | 125 | 125 | 125 | 24 | 82 | 10 | 37 | 263 | 98 | - | 2 | 4 | - | - | - | - | 7 | - | - | - | - | - | 7 | 22 | 4 | 5 | 52 | 5 | 0 | - | 8 | 1 | 35 | 7 | 5 | 0 | - | 247 | 125 | 77 | 68 | 68 | 68 | 68 | 142 | - |
| 19 | 125 | 125 | 125 | 4 | 106 | 55 | 6 | 224 | 65 | - | 14 | 4 | - | - | - | - | 5 | - | - | - | - | - | 7 | 2 | 3 | 5 | 10 | 5 | 0 | - | 8 | 1 | 35 | 9 | 5 | 0 | - | 290 | 125 | 64 | 3 | 3 | 3 | 3 | 111 | - |
| 20 | 125 | 125 | 125 | 72 | 106 | 96 | 54 | 308 | 72 | - | 4 | 11 | - | - | - | - | 5 | - | - | - | - | - | 7 | 2 | 0 | 5 | 10 | 6 | 0 | - | 8 | 1 | 4 | 9 | 5 | 18 | - | 329 | 125 | 146 | 138 | 138 | 138 | 138 | 22 | - |
| 21 | 125 | 125 | 125 | 7 | 72 | 96 | 54 | 309 | 98 | - | 4 | 34 | - | - | - | - | 272 | - | - | - | - | - | 7 | 5 | 22 | 5 | 67 | 222 | 0 | - | 8 | 1 | 4 | 9 | 5 | 328 | - | 311 | 125 | 95 | 138 | 138 | 138 | 138 | 2 | - |
| 22 | 125 | 125 | 125 | 7 | 52 | 96 | 1 | 309 | 88 | - | 4 | 3 | - | - | - | - | 75 | - | - | - | - | - | 7 | 39 | 2 | 8 | 67 | 169 | 0 | - | 8 | 4 | 4 | 9 | 5 | 318 | - | 311 | 125 | 53 | 138 | 138 | 138 | 138 | 315 | - |
| 23 | 105 | 105 | 105 | 7 | 21 | 2 | 76 | 266 | 54 | - | 0 | 3 | - | - | - | - | 19 | - | - | - | - | - | 7 | 8 | 2 | 8 | 25 | 108 | 0 | - | 8 | 4 | 4 | 9 | 5 | 135 | - | 249 | 105 | 30 | 96 | 96 | 96 | 96 | 295 | - |
| 24 | 105 | 105 | 105 | 8 | 90 | 65 | 101 | 391 | 205 | - | 23 | 34 | - | - | - | - | 11 | - | - | - | - | - | 9 | 8 | 11 | 8 | 5 | 19 | 0 | - | 8 | 4 | 4 | 9 | 5 | 37 | - | 419 | 105 | 88 | 19 | 19 | 19 | 19 | 168 | - |
| 25 | 105 | 105 | 105 | 5 | 25 | 34 | 106 | 357 | 170 | - | 2 | 3 | - | - | - | - | 11 | - | - | - | - | - | 9 | 10 | 1 | 8 | 5 | 19 | 0 | - | 8 | 4 | 4 | 31 | 5 | 123 | - | 421 | 105 | 88 | 18 | 18 | 18 | 18 | 255 | - |
| 26 | 105 | 105 | 105 | 5 | 162 | 14 | 162 | 469 | 97 | - | 2 | 22 | - | - | - | - | 32 | - | - | - | - | - | 9 | 0 | 30 | 8 | 5 | 19 | 0 | - | 8 | 4 | 10 | 31 | 5 | 9 | - | 344 | 105 | 81 | 134 | 134 | 134 | 134 | 255 | - |
| 27 | 105 | 105 | 105 | 5 | 69 | 14 | 137 | 817 | 100 | - | 1 | 64 | - | - | - | - | 1 | - | - | - | - | - | 9 | 21 | 10 | 8 | 64 | 143 | 0 | - | 8 | 4 | 0 | 0 | 5 | 152 | - | 852 | 105 | 64 | 124 | 124 | 124 | 124 | 128 | - |
| 28 | 85 | 85 | 85 | 5 | 119 | 54 | 247 | 817 | 300 | - | 1 | 117 | - | - | - | - | 641 | - | - | - | - | - | 9 | 52 | 71 | 8 | 44 | 236 | 0 | - | 8 | 4 | 0 | 0 | 5 | 586 | - | 1113 | 85 | 84 | 82 | 82 | 82 | 82 | 401 | - |

## Colheitas por dia

As colheitas no leste, de 0 a 0 por dia, um caractere por dia:

```
script2-a                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script2-b                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script2-c                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script3-a                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script3-b                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script3-c                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
oraculo-a                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
oraculo-b                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
oraculo-c                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
humano                   ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku                    ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
astra                    ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
astra-consertado         ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
astra-consertado-piloto  ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
astra-piloto             ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
astra-procedimento       ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
fable                    ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
fable-piloto             ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
fable-procedimento       ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
gemini                   ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
gemini-piloto            ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
gemini-procedimento      ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-comparar           ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-comparar-r2        ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-conselheiro        ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-controle           ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-dados              ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-dados-r2           ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-dados-r3           ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-openrouter         ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-procedimento       ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-procedimento-r2    ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-procedimento-r3    ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-r2                 ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
haiku-r3                 ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
opus                     ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
opus-procedimento        ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
oraculo-d                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script2-d                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script3-d                ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script3-fixo-a           ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script3-fixo-b           ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script3-fixo-c           ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
script3-fixo-d           ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
sonnet                   ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
sonnet-procedimento      ▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁
```

Oeste / leste, por dia:

| Dia | script2-a | script2-b | script2-c | script3-a | script3-b | script3-c | oraculo-a | oraculo-b | oraculo-c | humano | haiku | astra | astra-consertado | astra-consertado-piloto | astra-piloto | astra-procedimento | fable | fable-piloto | fable-procedimento | gemini | gemini-piloto | gemini-procedimento | haiku-comparar | haiku-comparar-r2 | haiku-conselheiro | haiku-controle | haiku-dados | haiku-dados-r2 | haiku-dados-r3 | haiku-openrouter | haiku-procedimento | haiku-procedimento-r2 | haiku-procedimento-r3 | haiku-r2 | haiku-r3 | opus | opus-procedimento | oraculo-d | script2-d | script3-d | script3-fixo-a | script3-fixo-b | script3-fixo-c | script3-fixo-d | sonnet | sonnet-procedimento |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 2 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 3 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 4 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 5 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 6 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 7 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 8 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 9 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 10 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 11 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 12 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 13 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 14 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | 0 / 0 | 0 / 0 | - | 0 / 0 | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 15 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 16 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 17 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 18 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 19 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 20 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 21 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 22 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 23 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 24 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 25 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 26 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 27 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |
| 28 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | - | - | - | - | 0 / 0 | - | - | - | - | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | - |

## A ficha de cada corrida

O modelo pedido e o id que as respostas trouxeram, a rota (o provedor de cada chamada), o esforço por tipo de chamada e o harness: o commit, o SDK, a mente, o hash do prompt de sistema e o das ferramentas, e os braços. Corridas começadas em 2026-10-30.

| Corrida | Modelo | Rota | Esforço | Harness |
|---|---|---|---|---|
| script2-a | script `farmer2` | - | - | `f985d98` (com mudança) |
| script2-b | script `farmer2` | - | - | `f985d98` (com mudança) |
| script2-c | script `farmer2` | - | - | `f985d98` (com mudança) |
| script3-a | script `farmer3` | - | - | `f985d98` (com mudança) |
| script3-b | script `farmer3` | - | - | `f985d98` (com mudança) |
| script3-c | script `farmer3` | - | - | `f985d98` (com mudança) |
| oraculo-a | script `oracle` | - | - | `f985d98` (com mudança) |
| oraculo-b | script `oracle` | - | - | `f985d98` (com mudança) |
| oraculo-c | script `oracle` | - | - | `f985d98` (com mudança) |
| haiku | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `09e196f`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| astra | openai/gpt-6-astra → openai/gpt-6-astra | openrouter: OpenAI (flex) | decision low; reflection medium | `7339133`, httpx2 2.13.1, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| astra-consertado | openai/gpt-6-astra → openai/gpt-6-astra | openrouter: OpenAI (flex) | decision low; reflection medium | `41964f6` (com mudança), httpx2 2.13.1, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| astra-consertado-piloto | openai/gpt-6-astra → openai/gpt-6-astra | openrouter: OpenAI (flex) | decision low; reflection medium | `41964f6` (com mudança), httpx2 2.13.1, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| astra-piloto | openai/gpt-6-astra → openai/gpt-6-astra | openrouter: OpenAI (flex) | decision low; reflection medium | `ce028f5`, httpx2 2.13.1, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| astra-procedimento | openai/gpt-6-astra → openai/gpt-6-astra | openrouter: OpenAI (flex) | decision low; reflection medium | `ccf853a` (com mudança), httpx2 2.13.1, mente camps_morada, prompt `455d963f`, 29 ferramentas `8d449805`, playbook 4, memória |
| fable | claude-fable-5-1 → claude-fable-5-1 | anthropic | decision low; reflection medium | `87a7fd2`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| fable-piloto | claude-fable-5-1 → claude-fable-5-1 | anthropic | decision low; reflection medium | `67fd9ee` (com mudança), anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| fable-procedimento | claude-fable-5-1 → claude-fable-5-1 | anthropic | decision low; reflection medium | `ccf853a` (com mudança), anthropic 1.15.0, mente camps_morada, prompt `455d963f`, 29 ferramentas `8d449805`, playbook 4, memória |
| gemini | google/gemini-4-argon → google/gemini-4-argon | openrouter: Google AI Studio (flex) | decision low; reflection medium | `011f3f6`, httpx2 2.13.1, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| gemini-piloto | google/gemini-4-argon → google/gemini-4-argon | openrouter: Google AI Studio (flex) | decision low; reflection medium | `9bbc14d` (com mudança), httpx2 2.13.1, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| gemini-procedimento | google/gemini-4-argon → google/gemini-4-argon | openrouter: Google AI Studio (flex) | decision low | `ccf853a`, httpx2 2.13.1, mente camps_morada, prompt `455d963f`, 29 ferramentas `8d449805`, playbook 4, memória |
| haiku-comparar | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `a872f8f`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, comparação, memória |
| haiku-comparar-r2 | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `a872f8f`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, comparação, memória |
| haiku-conselheiro | claude-haiku-5-5 → claude-haiku-5-5, claude-opus-4-8; conselheiro claude-opus-4-8 | anthropic | decision low; reflection medium | `a872f8f`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| haiku-controle | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `0dfcc0c` (com mudança), anthropic 1.15.0, mente camps_morada, prompt `455d963f`, 29 ferramentas `8d449805`, playbook 4, memória |
| haiku-dados | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `ccf853a`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| haiku-dados-r2 | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `ccf853a`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| haiku-dados-r3 | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `0dfcc0c` (com mudança), anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| haiku-openrouter | anthropic/claude-haiku-5.5 → anthropic/claude-haiku-5.5 | openrouter: Anthropic | decision low; reflection medium | `41964f6` (com mudança), httpx2 2.13.1, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| haiku-procedimento | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `0dfcc0c` (com mudança), anthropic 1.15.0, mente camps_morada, prompt `455d963f`, 29 ferramentas `8d449805`, playbook 4, memória |
| haiku-procedimento-r2 | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `ccf853a`, anthropic 1.15.0, mente camps_morada, prompt `455d963f`, 29 ferramentas `8d449805`, playbook 4, memória |
| haiku-procedimento-r3 | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `ccf853a`, anthropic 1.15.0, mente camps_morada, prompt `455d963f`, 29 ferramentas `8d449805`, playbook 4, memória |
| haiku-r2 | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `09e196f`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| haiku-r3 | claude-haiku-5-5 → claude-haiku-5-5 | anthropic | decision low; reflection medium | `09e196f`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| opus | claude-opus-5-5 → claude-opus-5-5 | anthropic | decision low; reflection medium | `67fd9ee`, anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| opus-procedimento | claude-opus-5-5 → claude-opus-5-5 | anthropic | decision low; reflection medium | `ccf853a`, anthropic 1.15.0, mente camps_morada, prompt `455d963f`, 29 ferramentas `8d449805`, playbook 4, memória |
| oraculo-d | script `oracle` | - | - | `f985d98` (com mudança) |
| script2-d | script `farmer2` | - | - | `f985d98` (com mudança) |
| script3-d | script `farmer3` | - | - | `f985d98` (com mudança) |
| script3-fixo-a | script `farmer3-fixo` | - | - | `f985d98` (com mudança) |
| script3-fixo-b | script `farmer3-fixo` | - | - | `f985d98` (com mudança) |
| script3-fixo-c | script `farmer3-fixo` | - | - | `f985d98` (com mudança) |
| script3-fixo-d | script `farmer3-fixo` | - | - | `f985d98` (com mudança) |
| sonnet | claude-sonnet-5-5 → claude-sonnet-5-5 | anthropic | decision low; reflection medium | `958c018` (com mudança), anthropic 1.15.0, mente camps_morada, prompt `9d37ac02`, 29 ferramentas `8d449805`, memória |
| sonnet-procedimento | claude-sonnet-5-5 → claude-sonnet-5-5 | anthropic | decision low; reflection medium | `ccf853a`, anthropic 1.15.0, mente camps_morada, prompt `455d963f`, 29 ferramentas `8d449805`, playbook 4, memória |

O juiz: claude-opus-5-5 → claude-opus-5-5, pela rota anthropic, com a rubrica `c4e00740`, no commit `09e196f` (anthropic 1.15.0), em 2026-10-31.

O juiz: openai/gpt-6-astra → openai/gpt-6-astra, pela rota openrouter, com a rubrica `c4e00740`, no commit `09e196f` (httpx2 2.13.1), em 2026-10-31.

## Os arquivos

- **script2-a**: `data/arena/m21-terceira-energia/script2-a/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `progresso.txt`, `summary.json`
- **script2-b**: `data/arena/m21-terceira-energia/script2-b/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `progresso.txt`, `summary.json`
- **script2-c**: `data/arena/m21-terceira-energia/script2-c/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `progresso.txt`, `summary.json`
- **script3-a**: `data/arena/m21-terceira-energia/script3-a/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **script3-b**: `data/arena/m21-terceira-energia/script3-b/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **script3-c**: `data/arena/m21-terceira-energia/script3-c/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **oraculo-a**: `data/arena/m21-terceira-energia/oraculo-a/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **oraculo-b**: `data/arena/m21-terceira-energia/oraculo-b/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **oraculo-c**: `data/arena/m21-terceira-energia/oraculo-c/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **humano**: `data/arena/m21-terceira-energia/humano/` com `archive.jsonl`, `summary.json`
- **haiku**: `data/arena/m21-terceira-energia/haiku/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **astra**: `data/arena/m21-terceira-energia/astra/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **astra-consertado**: `data/arena/m21-terceira-energia/astra-consertado/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **astra-consertado-piloto**: `data/arena/m21-terceira-energia/astra-consertado-piloto/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **astra-piloto**: `data/arena/m21-terceira-energia/astra-piloto/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **astra-procedimento**: `data/arena/m21-terceira-energia/astra-procedimento/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **fable**: `data/arena/m21-terceira-energia/fable/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **fable-piloto**: `data/arena/m21-terceira-energia/fable-piloto/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **fable-procedimento**: `data/arena/m21-terceira-energia/fable-procedimento/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **gemini**: `data/arena/m21-terceira-energia/gemini/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **gemini-piloto**: `data/arena/m21-terceira-energia/gemini-piloto/` com `archive.jsonl`, `estado.json`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **gemini-procedimento**: `data/arena/m21-terceira-energia/gemini-procedimento/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-comparar**: `data/arena/m21-terceira-energia/haiku-comparar/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-comparar-r2**: `data/arena/m21-terceira-energia/haiku-comparar-r2/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-conselheiro**: `data/arena/m21-terceira-energia/haiku-conselheiro/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-controle**: `data/arena/m21-terceira-energia/haiku-controle/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-dados**: `data/arena/m21-terceira-energia/haiku-dados/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-dados-r2**: `data/arena/m21-terceira-energia/haiku-dados-r2/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-dados-r3**: `data/arena/m21-terceira-energia/haiku-dados-r3/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-openrouter**: `data/arena/m21-terceira-energia/haiku-openrouter/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-procedimento**: `data/arena/m21-terceira-energia/haiku-procedimento/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-procedimento-r2**: `data/arena/m21-terceira-energia/haiku-procedimento-r2/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-procedimento-r3**: `data/arena/m21-terceira-energia/haiku-procedimento-r3/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-r2**: `data/arena/m21-terceira-energia/haiku-r2/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **haiku-r3**: `data/arena/m21-terceira-energia/haiku-r3/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **opus**: `data/arena/m21-terceira-energia/opus/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **opus-procedimento**: `data/arena/m21-terceira-energia/opus-procedimento/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **oraculo-d**: `data/arena/m21-terceira-energia/oraculo-d/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **script2-d**: `data/arena/m21-terceira-energia/script2-d/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `progresso.txt`, `summary.json`
- **script3-d**: `data/arena/m21-terceira-energia/script3-d/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **script3-fixo-a**: `data/arena/m21-terceira-energia/script3-fixo-a/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **script3-fixo-b**: `data/arena/m21-terceira-energia/script3-fixo-b/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **script3-fixo-c**: `data/arena/m21-terceira-energia/script3-fixo-c/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **script3-fixo-d**: `data/arena/m21-terceira-energia/script3-fixo-d/` com `archive.jsonl`, `estado.json`, `metrics.txt`, `modelo.json`, `progresso.txt`, `prova.json`, `summary.json`
- **sonnet**: `data/arena/m21-terceira-energia/sonnet/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
- **sonnet-procedimento**: `data/arena/m21-terceira-energia/sonnet-procedimento/` com `archive.jsonl`, `estado.json`, `juiz-gpt-6-astra.json`, `juiz.json`, `juiz.jsonl`, `llm.jsonl`, `memory.sqlite`, `metrics.txt`, `progresso.txt`, `prova.json`, `summary.json`
