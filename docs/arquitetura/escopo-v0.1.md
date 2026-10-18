# Campsverso — Escopo da v0.1 "Fazenda do Camps"

**Status:** aprovado para construção · **Data:** 10/out/2026
**Documentos de referência (ler nesta ordem):**
1. `escopo-v0.1.md` (este)
2. `fazenda-camps-biblia-v0.1.md` — o mundo
3. `contratos-eventos-v0.md` — envelope, eventos, barramento, portas
4. `kernel-gestao-do-tempo.md` — relógio e políticas de tempo
5. `pesquisa-componentes-plataforma-simulacao.md` — o que reaproveitar

---

## 1. Objetivo

Construir o **esqueleto andante** do Campsverso: o menor sistema que atravessa todas as camadas de ponta a ponta — kernel, contratos, barramento, controladores, arquivo de eventos e UI — usando uma fazenda genérica com **um avatar e nenhum LLM**.

A pergunta que a v0.1 responde: *a arquitetura orientada a eventos, com módulos totalmente independentes, funciona e aguenta rodar dias seguidos?* As perguntas sobre agentes ficam para a v0.2.

---

## 2. Roteiro de versões (contexto)

| Versão | Entrega |
|---|---|
| **v0.1** | Fazenda genérica + avatar Camps; controladores humano, script e replay; sem LLM |
| v0.2 | Controlador LLM (a "possessão"); memória baseline; arena humano × script × Haiku × Sonnet |
| v0.3 | Estúdio como segundo cartucho (simulado): presença, relógio ancorado, artefatos, 3 personagens |
| v0.4 | Estúdio ligado ao pipeline real do podcast; replay público |
| v0.5+ | Patagônia: Tomás, memória completa, crenças, experimentos com regras ocultas |

Revisão de 17/out/2026 (ADR-0055): a v0.3 passa a ser o escritório que constrói a si mesmo, o primeiro cartucho com efeitos externos; o estúdio vem depois, sobre a porta que o escritório constrói.

---

## 3. Dentro e fora da v0.1

| Dentro | Fora (não construir, nem "de leve") |
|---|---|
| Contratos `campsverso` (JSON Schema + AsyncAPI) com codegen Pydantic e TypeScript | LLM, `ModelPort`, OpenRouter, Bedrock |
| Kernel: relógio, ECS, grid, pathfinding, sistemas, ações, regras (visíveis + R-001 oculta), outbox, snapshots | Memória de agente, sono cognitivo, consolidação |
| NATS JetStream local com permissões por assunto | Forks, dilatação por agente |
| Filtro de percepção (fazenda inteira, sem `internal`) | Social, conversas, múltiplos avatares |
| Controladores: **humano**, **script**, **replay**; posse e troca de posse | Controladores LLM, MCP e supervisionado |
| Arquivador JSONL | AWS, Langfuse, deploy remoto |
| Gateway WebSocket + UI: debug canvas e depois Phaser top-down com LPC | Portal público, autenticação, replay no site |
| Modos de relógio: contínuo, pausado/passo, máximo (lockstep) | Relógio ancorado ao real (é da v0.3) |
| Métricas da bíblia (seção 13) e diário de bordo | Guarda de orçamento de LLM (não há LLM) |

---

## 4. Arquitetura de processos da v0.1

```
                     ┌───────────────────────────┐
                     │        NATS JetStream      │
                     │  streams: WORLD AGENT      │
                     │  OBSERVER INTERNAL COMMANDS│
                     └─▲──────▲──────▲──────▲─────┘
                       │      │      │      │
   ┌───────────────────┴┐ ┌───┴────┐ │ ┌────┴─────────────┐
   │ kernel (farm-camps)│ │percepção│ │ │ controller-runner│
   │ relógio, ECS, regras│ │ (filtro)│ │ │ script | replay  │
   │ SQLite + outbox     │ └────────┘ │ └──────────────────┘
   └────────────────────┘            │
             ┌───────────────────────┴──┐     ┌───────────┐
             │ gateway (FastAPI + WS)   │◄───►│ UI (TS)   │
             │ controlador humano entra │     │ Phaser    │
             └──────────────────────────┘     └───────────┘
                       ┌──────────────┐
                       │ arquivador    │──► data/archive/*.jsonl
                       └──────────────┘
```

Cada caixa é um **processo separado**, iniciado de forma independente. Nenhum importa código de outro, exceto o pacote gerado de contratos.

### 4.1 Portas usadas na v0.1

| Porta | Adaptador v0.1 |
|---|---|
| `EventBus` | NATS JetStream; **InMemoryBus** para testes |
| `EventArchive` | JSONL em disco, um arquivo por dia simulado |
| `WorldStore` | SQLite (estado + outbox) |
| `BlobStore` | disco local (snapshots) |
| `RulesPort` | registro Python de funções puras |
| `FlagPort` | YAML versionado (`cartridges/farm/rules.yaml`) |
| `ClockPort` | relógio do sistema (injetável nos testes) |
| `RealtimeGateway` | FastAPI WebSocket |
| `TelemetryPort` | logs estruturados JSON + métricas simples |

As demais portas do contrato (`ModelPort`, `MemoryPort`, `EffectorPort`, `SandboxPort`, `IdentityPort`, `SecretsPort`) **não** são criadas na v0.1.

---

## 5. Controladores e posse

| Controlador | Onde roda | Como recebe o mundo | Como age |
|---|---|---|---|
| `human` | browser, via gateway | eventos `world` (e `internal` no modo operador, só na UI) | clique no tile → `move`; clique no objeto → menu com as ações disponíveis |
| `script` | controller-runner | eventos `agent.camps.*` (percepção) | regras da bíblia, seção 11 |
| `replay` | controller-runner | arquivo de eventos | reemite os comandos gravados no mesmo tick de aplicação |

**Ciclo de decisão:** quando o avatar fica ocioso (ação concluída, rejeitada ou interrompida, fase do dia, limiar de necessidade), o kernel emite `campsverso.avatar.decision_requested.v1`. O controlador com a posse responde com `campsverso.cmd.action.propose.v1`, levando o mesmo `correlationid`. O humano pode ignorar pedidos e agir quando quiser.

**Posse:** um controlador por avatar. A troca é feita por `campsverso.cmd.avatar.possess.v1` e gera `campsverso.avatar.possessed.v1` / `.released.v1`. Comandos de quem não tem a posse são rejeitados com `not_in_control`. Na UI, um botão "Assumir / Devolver ao script".

**Relógio por modo:**
- **Contínuo (72×)**: o mundo não espera ninguém; usado para assistir e para jogar.
- **Máximo (lockstep)**: o kernel só avança depois que o controlador com a posse respondeu ao pedido de decisão. Com o script, 30 dias simulados rodam em minutos. Só permitido com controladores `script` ou `replay`.
- **Pausado / passo a passo**: depuração.

O kernel registra o **tick em que cada comando foi aplicado** (`action.accepted`). É isso que torna o replay exato mesmo para comandos gerados no modo contínuo.

---

## 6. UI da v0.1

Duas visões sobre os mesmos eventos:

| Visão | Mostra | Para quem |
|---|---|---|
| **Jogador** | mapa, avatar, inventário, fome, energia, relógio, clima | quem joga |
| **Operador** | tudo da visão jogador + linha do tempo de eventos (com filtro por tipo e visibilidade), eventos `internal` (efeitos da regra oculta), controles do relógio (pausa, passo, escala, modo), seletor de controlador, métricas do dia | você |

A UI é feita em duas etapas: primeiro um **canvas de depuração** (quadrados coloridos, marco M4); depois o **renderer Phaser top-down** com tiles e personagem LPC (marco M6). Ambos consomem exatamente os mesmos eventos.

---

## 7. Marcos

Cada marco é pequeno, testável e termina com commit, testes verdes e uma entrada no diário de bordo.

| Marco | Entrega | Pronto quando |
|---|---|---|
| **M0 — Fundação** | monorepo, ferramentas, `contracts/` com envelope e os eventos da v0.1, codegen Python/TS, CI local (lint, tipos, testes, validação de schemas, teste de arquitetura) | `make check` verde; um exemplo inválido quebra o CI |
| **M1 — Kernel sem barramento** | relógio (passo fixo, escala, salto), ECS, grid, pathfinding, sistemas da bíblia, catálogo de ações, regras + R-001, usando `InMemoryBus` | testes de unidade de cada sistema e ação; 1 dia simulado roda em teste |
| **M2 — Durabilidade** | adaptador NATS, outbox, arquivador JSONL, snapshots, retomada após queda | `kill -9` no kernel no meio de um dia → reinício sem lacunas nem duplicatas de `seq` |
| **M3 — Controladores headless** | percepção, `decision_requested`, controller-runner com script e replay, posse, modo máximo | 30 dias simulados com o script, sem intervenção; teste de determinismo e de replay passam |
| **M4 — UI de depuração** | gateway WebSocket, canvas simples, visões jogador/operador, controles do relógio | assistir um dia ao vivo no browser; pausar, acelerar, avançar passo a passo |
| **M5 — Controlador humano** | clique para mover, menu de ações, assumir e devolver a posse | você joga meio dia e devolve ao script sem quebrar nada |
| **M6 — Renderer Phaser** | mapa Tiled da bíblia, tiles LPC/Kenney, sprite LPC do Camps, animações andar/agir/dormir, retrato no HUD | a mesma partida do M5, agora com visual de jogo |
| **M7 — Fechamento** | métricas da bíblia no painel do operador, README, diário de bordo consolidado | critérios de aceite da seção 8 conferidos |

Estimativa grosseira, com Claude Code: M0–M3 em 2 a 3 fins de semana; M4–M7 em mais 2 a 3. Os spikes visuais (Phaser vs Three.js) podem correr em paralelo e só precisam estar decididos antes do M6.

---

## 8. Critérios de aceite da v0.1

| # | Critério | Como verificar |
|---|---|---|
| A1 | Contratos são a única dependência compartilhada | teste de arquitetura (`import-linter` / `dependency-cruiser`) no CI |
| A2 | Todo evento publicado valida contra seu schema | validação no publicador em modo de desenvolvimento + testes |
| A3 | **Resistência:** 30 dias simulados com o script, em modo máximo, sem erro e sem intervenção | teste automatizado; registrar tempo real gasto e memória |
| A4 | **Determinismo:** mesma seed + mesmos comandos → mesmo resultado | hash do conteúdo dos eventos (ignorando `id`, `time` e campos de parede) idêntico em duas execuções |
| A5 | **Replay:** reexecutar um dia gravado a partir do snapshot inicial reproduz os mesmos eventos de mundo | hash igual ao da execução original |
| A6 | **Independência:** derrubar gateway, arquivador ou percepção não derruba o kernel; ao voltarem, retomam do ponto certo | teste manual roteirizado + teste automatizado do arquivador |
| A7 | **Recuperação:** queda do kernel não perde nem duplica eventos | `kill -9` + reinício; `seq` contínuo |
| A8 | **Isolamento da regra oculta:** o processo do controlador não consegue assinar `internal` | teste com credencial do controlador tentando assinar → negado |
| A9 | **Posse:** humano assume, joga, devolve; comandos de quem não tem a posse são rejeitados | teste automatizado + demonstração |
| A10 | **Economia sustentável:** o script sobrevive 30 dias e termina com mais moedas do que começou | resultado do A3 |
| A11 | **Evidência da regra:** as métricas mostram o grupo leste amadurecendo mais rápido | painel do operador / consulta ao arquivo |

---

## 9. Armadilhas a evitar

- **Construir a v0.2 antes da hora.** Nada de `ModelPort` "já que estamos aqui". A interface de controlador é o ponto de extensão; o LLM entra por ela na v0.2.
- **Lógica de jogo no renderer.** A UI nunca decide nada: ela interpola trajetos e desenha estados.
- **Relógio de parede dentro de sistemas.** Quebra o determinismo. Sistemas recebem tick e RNG nomeado.
- **Iteração em ordem não determinística** (dicionários por inserção variável, `set`). Ordenar por id sempre que a ordem afetar o resultado.
- **Regras da bíblia escritas no kernel.** Culturas, preços, horários e ações são configuração do cartucho.

---

## 10. Diário de bordo (material para os posts)

Manter `docs/diario/AAAA-MM-DD.md` a cada sessão de trabalho, com:
- o que foi construído e o que deu errado;
- decisões tomadas (e por quê);
- números: linhas de código, tempo de execução, eventos por dia simulado, tamanho do arquivo;
- uma frase "o que eu contaria no LinkedIn".

---

## 11. Como iniciar no Claude Code

1. Criar um repositório vazio (ex. `campsverso`) e copiar para `docs/arquitetura/` todos os documentos listados no topo; colocar o `CLAUDE.md` na raiz.
2. Abrir o Claude Code na pasta e usar o **modo de planejamento** para o primeiro marco.
3. Primeiro prompt sugerido:

```
Leia o CLAUDE.md e os documentos em docs/arquitetura/ na ordem indicada no escopo-v0.1.md.
Depois, proponha o plano detalhado apenas do marco M0 (Fundação): estrutura de pastas,
ferramentas, os schemas de contratos necessários para a v0.1 e o pipeline de codegen e CI.
Não escreva código ainda. Liste dúvidas ou conflitos que encontrar entre os documentos.
```

4. Um marco por sessão (ou por dia). Ao fim de cada marco: testes verdes, commit, entrada no diário.
5. Ao encontrar conflito entre documentos ou uma decisão não prevista, o Claude Code deve **parar e perguntar**, registrando a decisão em `docs/decisoes/` (ADR curto).
