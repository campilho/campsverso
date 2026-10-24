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
