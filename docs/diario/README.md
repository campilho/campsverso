# Diário de bordo

O registro de cada sessão de trabalho: o que foi feito, o que deu errado, as decisões, os números e uma frase para o LinkedIn (escopo §10).

## Índice da v0.1

| Data | Entradas |
|---|---|
| [11/out/2026](2026-10-11.md) | preparação (documentos e as 12 primeiras decisões), M0 fundação, M1 kernel sem barramento, M2 durabilidade, M3 controladores headless |
| [12/out/2026](2026-10-12.md) | revisão do M3, M4 UI de depuração, o relógio da tela, M5 controlador humano, M6 renderer Phaser, M7 fechamento |

## Índice da v0.2

| Data | Entradas |
|---|---|
| [17/out/2026](2026-10-17.md) | a ideia do escritório que constrói a si mesmo (14/out), as referências visuais do escritório e do estúdio, ADR-0055; o plano do M8, o passo zero (tick antecipado, 30 tiles por minuto) e o M8 inteiro |
| [18/out/2026](2026-10-18.md) | o plano do M9 com o item 1 aprofundado (créditos da assinatura, CLIs headless, OpenRouter), ADR-0058, e o M9: porta de modelo, fita, medidor, guarda de orçamento, `make llm-smoke`; à noite, o M10 (a mente, ADR-0059) com 7 dias no sandbox; de madrugada, o M11 (a memória, ADR-0060) com a comparação de 7 dias com e sem memória |
| [19/out/2026](2026-10-19.md) | o plano do M12 aprovado com três mudanças (ADR-0061), `make arena` e `make arena-report`, as corridas de 30 dias e o relatório em `docs/arena/`; a proposta da fazenda mais rica para o M13; à noite e de madrugada, o M13 (ADR-0062): as primitivas do kernel, o gênero estendido por dados, a Fazenda Boa Vista com o fazendeiro-script 2, a mente, a fita e o soak |
| [20/out/2026](2026-10-20.md) | o M13 revisto: cavar ao lado como regar, o canteiro sem grupo (a faixa do rio é do analista), as métricas da bíblia 2 §13, a fita regravada, o soak de 30 dias repetido, os e2e nos dois mundos, a tela da Boa Vista conferida e o fechamento do M13; à tarde e à noite, o M14 (ADR-0063): o corredor e o relatório da segunda rodada, a arte da Boa Vista e a rodada de 30 dias (o Opus com 1.143 moedas contra 220 do script; ninguém cavou no rio) |
| [21/out/2026](2026-10-21.md) | a ordem das versões confirmada (a fazenda sofisticada na v0.3, o escritório na v0.4, o estúdio na v0.5; ADR-0064) e o plano macro da v0.3 com a pesquisa na web; à noite, o M15 (ADR-0065): os soaks finais, a chamada real, o aceite da v0.2, o `futuro.md` revisto e a v0.2 em números; depois da tag, o README por versão com os prints e as decisões da v0.3 (ADR-0066) |

## Índice da v0.3

| Data | Entradas |
|---|---|
| [22/out/2026](2026-10-22.md) | o plano do M16 e a rodada do humano preparada; à noite, a aprovação (ADR-0067) e o kernel, o cenário, o script e a câmera da Fazenda Morada do Sol |
| [23/out/2026](2026-10-23.md) | a arte (árvores por estação, culturas novas, espantalho), a lembrança do que se viu, a mente e a bíblia 3: o fechamento do M16; à noite, o plano do M17 (ADR-0068) |
| [24/out/2026](2026-10-24.md) | o M17, ver e assistir: a noite e a lanterna na percepção, a névoa na tela, o modo de assistir e a página da arena, os menus do humano com a fila e o teclado, os rótulos da linha do tempo, a lanterna desenhada; depois, o M18, a economia: as bibliotecas `libs/economy` e `libs/climate`, o mercado nos dois sentidos, as encomendas com a reputação, a feira, o tacho e a composteira, a previsão com tempestade e seca |
| [25/out/2026](2026-10-25.md) | o M19, os controladores e a medição (ADR-0070): as variantes do mapa por receita, o fazendeiro-script 3 que aprende com um caderno de campo e o oráculo que sabe, a fome da Morada do Sol em 2 por hora com as regras de sobrevivência, o caderno de campo e o experimento da noite na mente, as métricas de exploração, a prova do mundo, o juiz conferido contra o gabarito e contra controles, e a rodada de verificação; à noite, o agricultor treinado (ADR-0071): o playbook de método para qualquer modelo e a primeira rodada do Haiku, e o conselheiro (o advisor tool) no `futuro.md` |
| [26/out/2026](2026-10-26.md) | o playbook 2 do agricultor treinado, de madrugada: o procedimento e o exemplo, quatro corridas do Haiku com repetições, nenhuma descoberta e nenhum experimento sobre o lugar; o Sonnet não roda (ADR-0071); e o M20, os ajudantes (ADR-0072): vários avatares no kernel, na percepção, no runner, no gateway e na tela, cinco ajudantes contratáveis com a arte do gerador LPC, e a medida que mostrou que nesta Morada o ajudante não paga e virou um teste de julgamento (ADR-0073) |
| [12/nov/2026](2026-11-12.md) | o M21, a terceira arena (ADR-0074): o mapa d às cegas, a régua do meio, os braços do Haiku, a OpenRouter com o Gemini e o Astra, dois juízes, o procedimento e o caderno completo, e o humano em 15 dias; ninguém achou a água pela causa, e os maiores capturaram metade do valor de saber jogando a economia visível ([o relatório](../arena/m21-terceira-energia.md)) |
| [14/nov/2026](2026-11-14.md) | o M22, o fechamento da v0.3 (ADR-0076): o Astra do M21 respondia vazio em 47% das chamadas, por uma tradução nossa; a ferramenta obrigatória na OpenRouter o consertou, e ele rodou de novo em 14 dias; o Haiku pela OpenRouter; os soaks, a tela e as chamadas reais; o aceite, as notas, o print e a tag `v0.3.0` |

## A v0.1 em números

Do primeiro commit (11/out/2026, 12h15) à tag `v0.1.0` (12/out/2026), em dois dias de trabalho com o Claude Code.

| | |
|---|---|
| **Marcos** | 8 (M0 a M7), cada um com plano aprovado antes do código |
| **Decisões registradas** | 44 ADRs (0011 a 0054) |
| **Commits** | cerca de 100 |
| **Código** | cerca de 15.800 linhas de Python (serviços, bibliotecas, cartuchos, ferramentas e testes) e 3.200 de TypeScript na tela, fora os pacotes gerados dos contratos |
| **Contratos** | 49 tipos (eventos, comandos e mensagens da tela), validados em Python e em TypeScript com os mesmos códigos de erro |
| **Testes** | 223 em Python, 40 da tela (Vitest), 3 dos contratos e 3 no navegador (Playwright) |
| **Critérios de aceite** | 11 de 11 ([aceite-v0.1.md](../aceite-v0.1.md)) |
| **Velocidade** | um dia simulado em cerca de 1,1 s no modo máximo; 30 dias em 35 s num MacBook Pro M3 |
| **A regra oculta** | com ela, o leste amadurece em 2 dias e o oeste em 3; o fazendeiro-script termina 30 dias com 1.175 moedas (sem ela, 750) |
| **Arte** | cerca de 100 KB de pixel art LPC, de 4 pacotes do OpenGameArt e do gerador de personagens, com cada autor creditado |
| **Tempo e tokens** | por marco, em [docs/custos](../custos/README.md) |

Os números de tempo e tokens de M2 e M3 parecem baixos. Parte das conversas dessas sessões pode ter ficado em arquivos que o `make sessoes` não associou ao marco. Fica como pendência conferir.

## A v0.2 em números

Do plano do M8 (17/out/2026) à tag `v0.2.0` (21/out/2026), em cinco dias de trabalho com o Claude Code.

| | |
|---|---|
| **Marcos** | 8 (M8 a M15), cada um com plano aprovado antes do código |
| **Decisões registradas** | 11 ADRs (0055 a 0065), 54 no total |
| **Commits** | cerca de 95 desde a `v0.1.0` |
| **Código** | cerca de 28.400 linhas de Python (12 mil a mais que na v0.1) e 3.500 de TypeScript na tela, fora os pacotes gerados dos contratos |
| **Contratos** | 60 tipos (51 eventos e 9 comandos) e 5 mensagens da tela e do pulso; 11 eventos novos, nenhuma mudança incompatível |
| **Testes** | 381 em Python, 44 da tela (Vitest), 3 dos contratos e 3 no navegador (Playwright), estes nos dois mundos |
| **Critérios de aceite** | 8 de 8 ([aceite-v0.2.md](../aceite-v0.2.md)) |
| **Mundos** | 2: a Fazenda do Camps e a Fazenda Boa Vista, em três camadas de cartucho (`farm` → `farm_camps` → `farm_boavista`) |
| **Corridas com modelo** | 13 de 30 dias nas duas arenas, mais de 17 mil chamadas, nenhuma desistência |
| **Velocidade** | um dia simulado em cerca de 1 s no modo máximo, nos dois mundos; 30 dias com modelo levam de 40 min (Haiku) a 1 h 37 min (Opus) |
| **A pergunta** | o LLM vive e prospera (o Opus fez cinco vezes as moedas do script na Boa Vista), mas ninguém descobriu a regra oculta |

### Por marco

O tempo ativo e os tokens de saída são do Claude Code (`make sessoes`, em [docs/custos](../custos/README.md)). O custo de API é o das chamadas dos modelos do Campsverso, pelo medidor da porta de modelo, a preço de tabela.

| Marco | O que entregou | Minutos ativos | Saída (mil tokens) | API |
|---|---|---|---|---|
| M8 | o mundo pronto para o LLM | 82 | 365 | — |
| M9 | a porta de modelo e a guarda de orçamento | 34 | 147 | US$ 0,0001 (a primeira chamada) |
| M10 + M11 | a mente e a memória (as duas na mesma noite) | 120 | 528 | cerca de US$ 1,25 (as fitas, os 7 dias no sandbox e as corridas de 7 dias) |
| M12 | a arena | 54 | 213 | US$ 4,86 |
| M13 | a Fazenda Boa Vista | 158 | 477 | cerca de US$ 0,15 (as fitas) |
| M14 | a segunda rodada | 50 | 230 | US$ 40,41 (a rodada e as corridas duplicadas) |
| M15 | o fechamento | 34 | 114 | US$ 0,0001 (a chamada real) |
| **v0.2** | | **532** (cerca de 9 horas) | **2.074** | **cerca de US$ 47** |

- **Dois terços do custo de API vieram de uma corrida só:** o Opus custou US$ 26,35 por 30 dias, US$ 0,88 por dia simulado. O Haiku custou de US$ 0,45 a 0,91 por corrida de 30 dias.
- **Os créditos da assinatura cobriram tudo:** US$ 100 por mês na Console, sem cartão.
- **O tempo do Claude Code** foi parecido com o da v0.1 (cerca de 7 horas ativas, também em oito marcos). Os números do M10+M11 e do M14 podem estar abaixo do real: compactar a sessão apaga chamadas antigas da transcrição, e o mesmo explica os números baixos de M2 e M3 na v0.1.

## A v0.3 em números

Do plano do M16 (22/out/2026) à tag `v0.3.0` (14/nov/2026), em 24 dias de calendário, com uma semana parada esperando a partida do humano.

| | |
|---|---|
| **Marcos** | 7 (M16 a M22), mais o agricultor treinado, cada um com plano aprovado antes do código |
| **Decisões registradas** | 11 ADRs (0066 a 0076), 65 no total |
| **Commits** | cerca de 120 desde a `v0.2.0` |
| **Código** | cerca de 47.600 linhas de Python (19 mil a mais que na v0.2) e 6.600 de TypeScript na tela, fora os pacotes gerados dos contratos |
| **Contratos** | 73 tipos (64 eventos e 9 comandos) e 5 mensagens da tela e do pulso; 13 eventos novos, nenhuma mudança incompatível |
| **Testes** | 655 em Python, 90 da tela (Vitest), 3 dos contratos e 6 no navegador (Playwright), em três servidores |
| **Critérios de aceite** | 8, sete ok e um em parte ([aceite-v0.3.md](../aceite-v0.3.md)) |
| **Mundos** | 3 fazendas em quatro camadas de cartucho (`farm` → `farm_camps` → `farm_boavista` → `farm_morada_do_sol`), e a Morada do Sol em quatro variantes do mapa; as bibliotecas `economy` e `climate` |
| **Corridas com modelo** | 37 de um ano, 14 ou 2 dias, de seis modelos de três famílias, com uns 31,5 mil chamadas; mais as corridas dos scripts e do oráculo, de graça |
| **Velocidade** | um dia simulado em cerca de 1,1 s no modo máximo, nos três mundos; um ano da Morada do Sol com modelo leva de 38 min (Haiku) a 1 h 50 min (Fable) |
| **A pergunta** | aprender e lucrar saíram separados: o script 3 aprende e não lucra; os modelos grandes capturam até metade do valor de saber sem descobrir a água; o humano, que sabia as regras, foi ao lugar certo e não fez caixa |

### Por marco

O tempo ativo e os tokens de saída são do Claude Code (`make sessoes`, em [docs/custos](../custos/README.md)). O custo de API é o das chamadas dos modelos do Campsverso, pelo medidor da porta de modelo; na OpenRouter, o que a resposta disse.

| Marco | O que entregou | Minutos ativos | Saída (mil tokens) | API |
|---|---|---|---|---|
| M16 | a Fazenda Morada do Sol | 151 | 428 | US$ 0,03 (a fita) |
| M17 | ver e assistir | 84 | 249 | US$ 0,03 (a fita) |
| M18 | a economia e o clima | 98 | 277 | US$ 0,16 (a fita e a corrida de verificação) |
| M19 | os controladores e a medição (com o agricultor treinado) | 254 | 735 | cerca de US$ 6,60 (as fitas, o juiz, a corrida do Haiku e as sete corridas do playbook) |
| M20 | os ajudantes | 237 | 608 | US$ 0,10 (as fitas) |
| M21 | a terceira arena | 426 | 1.882 | cerca de US$ 247 |
| M22 | o fechamento e o Astra consertado | 40 | 171 | cerca de US$ 12,40 (o Astra consertado, o Haiku pela OpenRouter, os juízes e as chamadas reais) |
| **v0.3** | | **1.290** (cerca de 21 horas e meia) | **4.350** | **cerca de US$ 266** |

- **Quase todo o custo de API foi da terceira arena,** e dentro dela, de duas corridas: o ano do Fable (US$ 70) e a rodada com o procedimento (US$ 73). O ano do Haiku custou menos de US$ 1.
- **Os créditos:** US$ 200 vieram do plano Max (os créditos de 18/out e de 7/nov), e US$ 280 foram comprados em cinco cargas, entre a Console e a OpenRouter, por R$ 1.659,55 no cartão, com o IOF ([creditos.csv](../custos/creditos.csv)).
- **O tempo do Claude Code** foi mais que o dobro do da v0.2 (532 minutos), puxado pelo M21, uma sessão longa de três semanas com várias compactações, a operação das corridas e a partida do humano.
