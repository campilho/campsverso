# Diário de bordo

O registro de cada sessão de trabalho: o que foi feito, o que deu errado, as decisões, os números e uma frase para o LinkedIn (escopo §10).

## Índice da v0.1

| Data | Entradas |
|---|---|
| [11/out/2026](2026-10-11.md) | preparação (documentos e as 12 primeiras decisões), M0 fundação, M1 kernel sem barramento, M2 durabilidade, M3 controladores headless |
| [12/out/2026](2026-10-12.md) | revisão do M3, M4 UI de depuração, o relógio da tela, M5 controlador humano, M6 renderer Phaser, M7 fechamento |

## Entre a v0.1 e a v0.2

| Data | Entradas |
|---|---|
| [17/out/2026](2026-10-17.md) | a ideia do escritório que constrói a si mesmo (14/out), as referências visuais do escritório e do estúdio, ADR-0055; o plano do M8, o passo zero (tick antecipado, 30 tiles por minuto) e o M8 inteiro |
| [18/out/2026](2026-10-18.md) | o plano do M9 com o item 1 aprofundado (créditos da assinatura, CLIs headless, OpenRouter), ADR-0058, e o M9: porta de modelo, fita, medidor, guarda de orçamento, `make llm-smoke`; à noite, o M10 (a mente, ADR-0059) com 7 dias no sandbox; de madrugada, o M11 (a memória, ADR-0060) com a comparação de 7 dias com e sem memória |
| [19/out/2026](2026-10-19.md) | o plano do M12 aprovado com três mudanças (ADR-0061), `make arena` e `make arena-report`, as corridas de 30 dias e o relatório em `docs/arena/`; a proposta da fazenda mais rica para o M13 |

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
