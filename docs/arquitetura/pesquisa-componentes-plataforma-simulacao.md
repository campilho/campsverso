# Pesquisa de componentes públicos — Plataforma de Simulação com Agentes

**Data:** 07/out/2026
**Objetivo:** mapear projetos públicos (open source ou source-available) que possam ser **adotados**, **adaptados** ou usados como **inspiração** para cada subsistema da arquitetura macro da plataforma (vilarejo remoto na Patagônia → estúdio do podcast → startup → simulação econômica/mini-Brasil).
**Uso previsto:** insumo para a etapa de especificação técnica (spec) e decisões build-vs-reuse.

> Convenções: **[ADOTAR]** candidato forte a uso direto · **[ADAPTAR]** usar parcialmente ou forkar · **[INSPIRAR]** só o padrão/ideia · **[EVITAR]** não recomendado para este projeto · **(a verificar)** dado que vale confirmar na fonte antes de decidir.

---

## 0. Resumo executivo

1. **Não existe um "kernel pronto" para o nosso caso.** Os projetos de simulação com agentes LLM se dividem em dois grupos: (a) *mundos visuais 2D* com loop de agente simples (AI Town, Generative Agents original) e (b) *bibliotecas de simulação social* sem mundo físico/visual (Concordia, TinyTroupe, OASIS, AgentSociety). Nenhum combina mundo determinístico + regras ocultas + event sourcing + renderer + ponte com a realidade. **O kernel será nosso**, mas pequeno, e vários módulos em volta podem ser reaproveitados.
2. **O que mais vale reaproveitar:** memória (Hindsight é um achado — separa fato de crença, com confiança), roteamento de modelos (LiteLLM ou Bedrock Converse), observabilidade (Langfuse + OpenTelemetry GenAI), renderer (Phaser 3 + Tiled + assets LPC/Kenney), regras (ZEN Engine se quisermos regras editáveis por não-dev; senão funções puras), sandbox de código (E2B/Daytona/Docker ou AgentCore Code Interpreter).
3. **O que mais vale estudar como referência de design:** o padrão *Game Master* do Concordia, o *memory stream* do Generative Agents, a *skill library* do Voyager, a arquitetura concorrente PIANO (Project Sid) e o modelo de personas do TinyTroupe (para a simulação econômica).
4. **Três decisões a fechar na spec:** linguagem do kernel (Python vs TypeScript — a escolha arrasta o resto), memória própria vs Hindsight, e Phaser vs Godot para o renderer.

---

## 1. Plataformas completas de simulação com agentes LLM

Candidatas a "kernel pronto". Nenhuma é drop-in, mas todas ensinam algo.

| Projeto | Origem / licença | O que é | Fit com o nosso caso | Veredito |
|---|---|---|---|---|
| **Generative Agents** (Smallville) | Stanford, Park et al. 2023 — repo `joonspk-research/generative_agents` | Código do paper original: 25 agentes numa vila 2D (Phaser), com memory stream, reflexão e planejamento | É a referência conceitual da nossa camada de cognição. Código acadêmico, pouco mantido, acoplado ao OpenAI da época | **[INSPIRAR]** — arquitetura de memória e ciclo observe→reflect→plan |
| **AI Town** | a16z-infra + Convex — ~8,6k estrelas, TypeScript, MIT (a verificar) | Starter kit de vila com agentes que conversam; Convex como engine/DB/vector search em tempo real, PixiJS no front, Llama/Ollama ou OpenAI; suporta jogador humano entrando no mundo | É o projeto **mais próximo visualmente** do que queremos (mundo 2D pixel art, agentes andando e conversando, tempo real no browser). Limitações: acoplado ao Convex (BaaS proprietário com versão local), sem regras de mundo nem economia, memória simplista | **[ADAPTAR / INSPIRAR]** — vale rodar localmente para sentir o loop e estudar `engine.ts` (tick, agendamento, conversas). Se escolhermos TS, é um fork plausível para a fase 0 |
| **Concordia** | Google DeepMind — Python, `pip install gdm-concordia`, Apache 2.0 (a verificar) | Biblioteca de *generative agent-based modeling*. Padrão de RPG de mesa: um **Game Master** (também um LLM) valida a plausibilidade das ações dos agentes e narra os efeitos. v2 usa padrão Entity-Component, "prefabs" e um "engine" de interação | Oposto do nosso kernel determinístico (o GM é um LLM, não código). Mas o padrão é excelente para a camada de **Diretor** e para "mundos de linguagem" (negociações, reuniões da startup). Sem renderer | **[ADAPTAR]** componentes de agente + **[INSPIRAR]** o GM como "narrador" opcional sobre o kernel |
| **TinyTroupe** | Microsoft — Python, MIT (a verificar) | Toolkit de simulação de **personas** detalhadas (nacionalidade, idade, profissão, personalidade, crenças), com amostragem de população, experimentos e validação | Ferramenta ideal para a **simulação econômica / mini-Brasil**: gerar e amostrar populações sintéticas de consumidores. Não tem mundo espacial | **[ADOTAR]** na fase da simulação econômica para personas; **[INSPIRAR]** o formato de "cartão de identidade" do personagem |
| **OASIS** | CAMEL-AI — Python, Apache 2.0 (a verificar) | Simulador de redes sociais com até 1 milhão de agentes (X/Reddit), recsys, rede dinâmica | Escala e propagação de informação. Útil como referência para a **rádio da Renata** e para difusão de crenças em larga escala | **[INSPIRAR]** |
| **AgentSociety** | Tsinghua — Python, licença (a verificar) | Simulador urbano de larga escala; agentes LLM + ambiente social realista + engine distribuído com mensageria **MQTT** | Referência de arquitetura para o **mini-Brasil** (milhares de agentes, ambiente econômico, choques externos como furacão/UBI). Pesado demais para a fazenda | **[INSPIRAR]** — especialmente a separação engine/agentes via mensageria |
| **Project Sid / PIANO** | Altera.AL — apenas paper + relatório técnico (sem código) | 10–1000+ agentes no Minecraft; arquitetura **PIANO**: módulos concorrentes (percepção, memória, ação, fala) com um gargalo de decisão central que mantém coerência | Exatamente o problema do nosso "escalonador cognitivo": como reagir em tempo real e planejar a longo prazo ao mesmo tempo sem perder coerência. Só ideias, sem código | **[INSPIRAR]** — PIANO como modelo para o nível tático/estratégico concorrente |
| **Voyager** | MineDojo/NVIDIA — Python+JS, MIT | Agente de aprendizado contínuo no Minecraft: currículo automático, **skill library** de código executável, prompting iterativo com feedback de execução | A skill library é o modelo da nossa memória procedural e do "Tomás programa o robô mech". Código preso ao Minecraft/GPT-4 | **[INSPIRAR]** — padrão de skill = código + descrição + embedding + taxa de sucesso |
| **Mindcraft** | comunidade — JS (a verificar) | Agentes LLM no Minecraft, multi-modelo, mais mantido que o Voyager | Alternativa ao Voyager como referência de "agente escreve código para agir" | **[INSPIRAR]** |
| **PRAISELab GABM framework** | acadêmico — Python | Framework GABM com fases, RAG e memória | Pequeno; útil só como exemplo de estrutura por fases | **[INSPIRAR]** (baixa prioridade) |
| MetaGPT / ChatDev | OSS, Python | "Empresa de software simulada" (PM, arquiteto, engenheiro) que produz código real a partir de um requisito | Referência direta para a **startup**: papéis + SOPs + artefatos reais | **[INSPIRAR / ADAPTAR]** para o cartucho startup |

**Nota sobre frameworks genéricos de agentes:** AutoGen está em modo de manutenção (sem novas features) e Flowise foi arquivado em ago/2026 — evitar dependências nesses dois. LangGraph, CrewAI e Strands seguem ativos.

---

## 2. Kernel de simulação (relógio, ECS, espaço, event log)

| Componente | Candidatos | Avaliação |
|---|---|---|
| **ECS (entidades/componentes)** | `esper` (Python, minimalista); `bitecs`/`miniplex` (TS); `hecs`/Bevy ECS (Rust) | ECS puro em Python resolve. Exemplo de referência: o repo `spaceprojectsim` separa `sim_core` (Rust puro, síncrono, sem IO, com GOAP e economia) do cliente Bevy — **exatamente a separação que queremos**, mesmo que em outra linguagem |
| **ABM clássico** | **Mesa** (Python, ativo, Mesa 3 com visualização Solara); AgentPy; Agents.jl | Mesa oferece grid/space, scheduler, `batch_run` para experimentos e DataCollector. Pode ser o esqueleto do mundo na fase 0 e, sobretudo, dos **agentes estatísticos do mini-Brasil**. Não traz renderer de jogo nem event sourcing — **[ADAPTAR]** |
| **Engine de jogo headless** | Godot 4 (`--headless`, GDScript/C#, exporta web); Bevy (Rust); Defold (Lua) | Godot headless funciona como servidor autoritativo, mas o modelo de nós/cenas puxa a lógica para dentro da engine; a comunidade recomenda manter simulação separada da renderização. Bevy é ECS-first, mas Rust aumenta o custo de aprendizado. **Veredito: não usar engine de jogo como kernel**; usar só como renderer, se tanto |
| **Backend reativo tipo AI Town** | Convex (self-host disponível) | Resolve DB + tempo real + scheduler + vector search num pacote. Lock-in e modelo mental diferente (funções serverless). **[EVITAR]** como kernel; **[INSPIRAR]** a modelagem de "world state + inputs + engine tick" |
| **Event sourcing** | `eventsourcing` (Python, John Bywater); EventStoreDB/Kurrent; NATS JetStream; Redis Streams; ou tabela append-only em SQLite/Postgres | Para a fase 0, **tabela append-only + snapshots** basta. Migrar para NATS/Redis Streams quando houver vários processos (estúdio na nuvem, multi-agente). A lib `eventsourcing` dá aggregates/snapshots prontos, mas é opinativa — avaliar antes de adotar |
| **Pathfinding** | `pathfinding` (Python A*), `EasyStar.js`, `pathfinding.js` | Trivial, qualquer um serve |
| **Mensageria interna** | asyncio queues → Redis Streams/NATS | AgentSociety usa MQTT para escalar; para nós, in-process na fase 0 |

**Decisão a fechar:** Python (Mesa + esper + FastAPI) ou TypeScript (AI Town-like + Phaser no mesmo repo). Python favorece Mesa, Concordia, TinyTroupe, Hindsight, Strands, Claude Agent SDK. TypeScript favorece reuso do AI Town e um único runtime front/back. **Tendência: Python no kernel, TypeScript só no renderer.**

---

## 3. Motor de regras (visíveis e ocultas)

| Candidato | Tipo | Avaliação |
|---|---|---|
| **GoRules ZEN Engine** | BRE open source em Rust com bindings Python/Node/Go; modelo **JDM** (JSON Decision Model) com tabelas de decisão, expressões e funções JS; editor React open source | Permite regras do mundo em JSON editáveis fora do código, com editor visual. Ótimo se quisermos que não-devs (ou o "dono do mundo") editem regras. Para regras ocultas versionadas, é um bom formato. **[ADOTAR]** se regras forem editáveis; senão é overkill |
| `json-rules-engine` (JS), `durable_rules`/`experta` (Python) | Rule engines leves | `experta` é pouco mantido; `durable_rules` idem (a verificar). Para Python, **funções puras + registry** tendem a ser mais simples e testáveis |
| **Feature flags**: OpenFeature (padrão), Flipt, Unleash | Flags para ligar/desligar regras ocultas com histórico | Resolve o "ativar/desativar regra via config com timestamp" de forma padronizada. Flipt é leve e self-hosted. **[ADOTAR]** Flipt ou um YAML versionado no git — ambos geram evento no log |
| Modelos de cultivo (DSSAT, APSIM, PCSE) | Simuladores agronômicos reais | Pesados demais. Usar crescimento logístico simples com modificadores (água, solo, proximidade do rio). **[EVITAR]** |

**Recomendação:** regras como funções puras Python registradas por nome, com metadados (`visível/oculta`, `versão`, `flag`), carregadas do cartucho. ZEN só se a edição por não-devs virar requisito (provável na simulação econômica).

---

## 4. Física e espaço

Não precisamos de motor de física. O mundo é um grid de tiles com colisão, caminhos e tempo discreto.

| Necessidade | Solução |
|---|---|
| Colisão/movimento | grid + A*; sem física contínua |
| Crescimento, clima, necessidades | modelos discretos simples por tick, com RNG com seed registrada |
| Se um dia precisar de física 2D | `pymunk` (Chipmunk), `Box2D`, `Matter.js`, `Rapier` |

Os projetos de "mundo físico com LLM" encontrados (ChronoAgentic, SimWorld, EmbodiedGen) são 3D/robótica e **fora de escopo**.

---

## 5. Cognição: runtime do agente

| Candidato | Avaliação |
|---|---|
| **Anthropic SDK + tool use nativo** (loop próprio) | Recomendado para o núcleo: controle total do escalonador em três níveis, cache de prompt, batch. É o conhecimento que o projeto quer gerar |
| **Claude Agent SDK** | Loop de agente pronto com ferramentas, sessões e hooks. Melhor uso: cartucho **startup** (agentes que escrevem código real) e efetores |
| **Strands Agents SDK** (AWS, OSS, Python e TypeScript) | Framework model-driven, integra com Bedrock e AgentCore; útil na versão nuvem |
| Pydantic AI, LangGraph | Alternativas sólidas em Python; LangGraph para grafos de estado explícitos. Não necessárias no núcleo |
| **Concordia components** | Componentes de agente (memória associativa, planos, identidade) reutilizáveis em Python |
| **Behavior trees / GOAP / Utility AI**: `py_trees` (Python), `behavior3`, GOAP libs | Para o **nível reflexo** (sem LLM) e para o **robô mech** (sem LLM): máquina de estados/behavior tree é o padrão de NPC de jogo. `py_trees` é maduro (origem em robótica ROS). **[ADOTAR]** |
| **PIANO** (Project Sid) | Modelo de módulos concorrentes com gargalo de decisão — referência para rodar tático e estratégico em paralelo sem perder coerência |

---

## 6. Roteador de modelos (um LLM por personagem)

| Candidato | Avaliação |
|---|---|
| **LiteLLM** (OSS, Python SDK + proxy) | API única para 100+ provedores, **budgets por chave/time**, fallback, rate limit, spend tracking. Resolve "modelo por personagem + teto de custo" quase sem código. **[ADOTAR]** na versão local |
| **Amazon Bedrock Converse API** | Uma API para Claude, Nova, Llama, Mistral etc. dentro da AWS; modelo de custo unificado. **[ADOTAR]** na versão nuvem |
| **OpenRouter** (hosted) | Máxima variedade de modelos, zero operação, markup e dependência externa. Bom para experimentos rápidos de "cérebros diferentes" |
| Portkey (gateway, tem versão OSS), TokenMix etc. | Alternativas de gateway; não necessárias |
| **Vercel AI SDK** (TS) | Se o kernel fosse TS; tem suporte a provedores e streaming |
| **Ollama / LM Studio** | Modelos locais no M3 para o nível tático barato (8–14B quantizados) — plugam no LiteLLM |

**Importante:** o roteador deve registrar tokens/custo **por personagem e por nível cognitivo** no event log, não só no proxy.

---

## 7. Memória de longo prazo

Esta é a camada com mais oferta pública. Critério: o que serve a **crenças com confiança**, **reflexão/consolidação** e **proveniência** (quem me contou).

| Candidato | Modelo | Fit | Veredito |
|---|---|---|---|
| **Hindsight** (Vectorize) — MIT, `pip install hindsight-all`, Docker, ~13k estrelas | Quatro redes: **fatos do mundo, experiências, observações (consolidadas), opiniões/crenças com confiança**; operações *retain / recall / reflect*; grafo temporal; perfis comportamentais | É quase exatamente o nosso "belief store": separa o que o agente **sabe** do que **acredita**, com confiança que evolui, e tem a operação de **reflexão**. Benchmarks fortes (LongMemEval 91,4% com modelo de fronteira; >83% com modelo 20B open) | **[ADOTAR / AVALIAR PRIMEIRO]** — candidato nº 1. Riscos: dependência de serviço Docker; verificar se a reflexão permite nosso ciclo de "sono" e se expõe evidências a favor/contra |
| **Letta** (ex-MemGPT) — OSS, Postgres+pgvector | Runtime "memory-first": o agente gerencia blocos de memória core + arquivo | Ótimo para agentes de longa duração, mas é um **runtime inteiro**, não uma biblioteca; conflita com nosso escalonador próprio | **[INSPIRAR]** (memória gerida pelo próprio agente) |
| **Mem0** — OSS + managed | Extração/dedup de fatos + retrieval multi-sinal | Boa para personalização de usuário; menos para crenças e consolidação | **[EVITAR]** no núcleo |
| **Zep / Graphiti** — Graphiti OSS | Grafo de conhecimento **temporal** com validade de fatos | Interessante para "a regra do rio foi verdade de X a Y". Mais infra (Neo4j/FalkorDB) | **[ADAPTAR]** se Hindsight não cobrir temporalidade |
| **Cognee** — OSS | Pipeline grafo+vetor com proveniência | Mais para "memória organizacional"; relevante no **brain pessoal**, não aqui | **[EVITAR]** aqui |
| **LangMem** | Memória para LangGraph | Só se usarmos LangGraph | **[EVITAR]** |
| **Bedrock AgentCore Memory** | Curto prazo + longo prazo com estratégias (semântica, episódica — adicionada em 2026 —, procedural); ingestão direta e payloads JSON | Gerenciado, bom para a versão nuvem; menos transparente para o experimento de regras ocultas | **[ADAPTAR]** como comparação na fase AWS |
| **Memory stream original** (Generative Agents) | Score = recência·importância·relevância | Simples, 200 linhas, totalmente nosso | **[ADOTAR]** como baseline para o ablation |
| Vetores: `sqlite-vec`, `pgvector`, LanceDB, Chroma, Qdrant | Armazenamento | `sqlite-vec` local → `pgvector` nuvem. LanceDB é boa opção embarcada em Python |
| Embeddings locais: `bge`, `nomic` via Ollama/sentence-transformers; Titan no Bedrock | — | Local no M3 para custo zero |

**Recomendação:** implementar o memory stream simples como baseline (necessário para o experimento de ablation) e **avaliar Hindsight** como camada de crenças/reflexão. Se Hindsight servir, nossa memória vira uma fachada sobre ele.

---

## 8. Camada social

Não há biblioteca standalone. Padrões a reaproveitar:
- **Concordia**: conversas mediadas pelo GM, "componentes" de relacionamento.
- **OASIS / AgentSociety**: propagação de informação em rede, recsys como "rádio".
- **AI Town**: máquina de estados de conversa (convite → aceite → turnos → despedida) com limite de turnos e cooldown — simples e funciona.
- **Project Sid**: regras coletivas e transmissão cultural como métricas.

Nossa adição específica: **proveniência de crença** (`fonte: Esteban`, confiança reduzida) — não encontrada pronta em nenhum projeto, exceto parcialmente no Hindsight (observações consolidadas com evidência).

---

## 9. Ponte com a realidade (efetores)

| Necessidade | Candidatos |
|---|---|
| Instrumentar o pipeline do podcast | **Hooks do Claude Code** (`PreToolUse`/`PostToolUse` etc.) postando eventos; AgentCore harness também expõe hooks `before/after_tool_call` (set/2026) |
| Agentes que escrevem código real (startup) | **Claude Agent SDK** ou Claude Code headless; sandboxes **E2B**, **Daytona**, Docker/Firecracker; **AgentCore Code Interpreter** na nuvem |
| Expor o mundo como ferramenta | **MCP server** (FastMCP em Python / SDK oficial TS) — o catálogo de ações do kernel vira tools; permite Claude Code, Kiro e Agent SDK controlarem avatares |
| TTS / STT para retakes reais | ElevenLabs (já em uso); STT para comparar com roteiro: Whisper/faster-whisper local ou ElevenLabs Scribe |
| Publicação | S3 + CloudFront (já previsto) |

---

## 10. Diretor (dramaturgia)

Nada pronto para "expandir log real em expediente de 8h". Referências:
- **Concordia Game Master**: um LLM narrador que transforma eventos em cenas — pode ser o Diretor "com voz".
- **ink** (Inkle, OSS) e **Yarn Spinner**: linguagens de roteiro ramificado para jogos; úteis para cenas-template (chegada, café, almoço) com variação controlada.
- **Inworld / Convai**: NPCs comerciais com memória e voz — só como referência de produto.

**Recomendação:** Diretor = escalonador de templates (YAML) + modelo barato para falas; sem dependência externa.

---

## 11. Portal humano

| Necessidade | Candidatos |
|---|---|
| Humano entra no mundo | AI Town já implementa "player joins and talks" — referência direta |
| Auth / rate limit | Clerk/Auth.js (web), Cognito (AWS); rate limit por sessão no backend |
| Moderação de fãs conversando com personagens | Bedrock Guardrails, Llama Guard (local), filtros do próprio modelo; teto de custo por sessão |

---

## 12. Apresentação (renderer, replay, broadcast)

| Componente | Candidatos | Avaliação |
|---|---|---|
| **Renderer 2D** | **Phaser 3** (tilemaps Tiled nativos, câmera, animação; usado pelo Generative Agents e no POC do AI Town); **PixiJS** (renderer puro, usado pelo AI Town final); Excalibur (TS, ECS-ish); Godot web export | **Phaser 3** é o melhor custo-benefício para top-down pixel art e isométrico (plugin/isometric tilemaps). PixiJS se quisermos controle total. Godot só se o time quiser editor visual |
| **Editor de mapas** | **Tiled** (padrão de fato, exporta JSON para Phaser); **LDtk** | Tiled |
| **Assets** | **LPC** (Liberated Pixel Cup, CC-BY-SA, enorme coleção de fazenda/vila/personagens com animações compatíveis — projetos como *Hortica Botanica* usam); **Kenney** (CC0); **Sprout Lands** (Cup Nooble, itch, licença própria — a verificar); **Hana Caraka** (Otterisk, pago/custom) | LPC + Kenney cobrem fazenda e escritório na fase 0 sem risco de licença. Nada de assets do Stardew/Game Dev Tycoon |
| **Projetos-referência de fazenda** | *Hortica Botanica* (Godot + LPC, OSS), *Sunset Valley* (Godot 4.6, OSS, template), *Farm prototype* (Godot, "helpers" com state machine — "serve de base para projetos de simulação com IA") | Mecânicas de cultivo/colheita/loja prontas para **[INSPIRAR]**; código Godot não reutilizável diretamente em Phaser |
| **Tempo real** | WebSocket (FastAPI), Convex realtime, Supabase Realtime, Ably | FastAPI WS local; API Gateway WebSocket na AWS |
| **Replay** | nenhum pronto — JSON do event log + player no browser | Construir (pequeno) |

---

## 13. Observabilidade e experimentos

| Candidato | Avaliação |
|---|---|
| **Langfuse** — MIT, self-host (multi-serviço) ou cloud (free tier 50k observações/mês) | Traces, sessões, custo por trace, prompt management, ingestão **OpenTelemetry**. **[ADOTAR]** |
| **Arize Phoenix** — licença Elastic 2.0 (fontes divergem; a verificar), single container | Excelente para avaliação e OpenInference; licença não-OSI pode incomodar. Alternativa |
| **Opik** (Comet) — Apache 2.0 | Alternativa leve |
| **OpenTelemetry GenAI semantic conventions** (`gen_ai.*`) + **OpenInference** | Instrumentar o kernel direto em OTel desde o início evita lock-in de ferramenta |
| **LiteLLM spend tracking** | Custo por chave/personagem complementa |
| **Experimentos**: Mesa `batch_run`, Hydra (configs), MLflow / W&B (métricas) | Para ablations e toggles de regras com mesma seed. MLflow local basta |

---

## 14. Operação

| Necessidade | Local (Mac M3) | AWS |
|---|---|---|
| Processo contínuo | `launchd` + `caffeinate`, Docker Compose | ECS Fargate ou EC2/Lightsail pequena; AgentCore Runtime para agentes isolados |
| Agendamento (sono, batch) | cron/launchd | EventBridge Scheduler |
| Watchdog | padrão do "vigia" já existente | CloudWatch alarms |
| Budget guard | LiteLLM budgets + guard no kernel | idem + AWS Budgets |

---

## 15. Matriz build vs reuse (síntese)

| Subsistema | Decisão proposta | Reuso |
|---|---|---|
| Relógio / ECS / event log | **Construir** (pequeno) | esper, Mesa (space/scheduler), tabela append-only |
| Regras | **Construir** (funções puras + flags) | Flipt/OpenFeature; ZEN se edição por não-dev |
| Ações / catálogo | **Construir** | expor via MCP (FastMCP) |
| Cognição (escalonador 3 níveis) | **Construir** | Anthropic SDK; py_trees para reflexo; PIANO como referência |
| Roteador de modelos | **Reusar** | LiteLLM (local) → Bedrock Converse (nuvem) |
| Memória | **Baseline própria + avaliar Hindsight** | memory stream simples; Hindsight; sqlite-vec/pgvector |
| Social | **Construir** | padrões de AI Town/Concordia |
| Efetores | **Reusar** | Claude Agent SDK, hooks do Claude Code, E2B/Daytona/Docker, MCP |
| Diretor | **Construir** | ink/Yarn como referência; Concordia GM opcional |
| Portal humano | **Reusar parcialmente** | padrão AI Town; Clerk/Cognito; guardrails |
| Renderer | **Reusar** | Phaser 3 + Tiled + LPC/Kenney |
| Replay / broadcast | **Construir** (pequeno) | FastAPI WS; S3+CloudFront |
| Observabilidade | **Reusar** | Langfuse + OTel GenAI; MLflow para experimentos |
| Personas (simulação econômica) | **Reusar** | TinyTroupe; Mesa para agentes estatísticos |

---

## 16. Riscos e pontos de atenção

- **Licenças**: confirmar antes de forkar: AI Town (MIT?), Concordia (Apache 2.0?), TinyTroupe (MIT?), Phoenix (ELv2 vs Apache — fontes conflitam), Sprout Lands (licença própria de itch). LPC é CC-BY-SA (atribuição obrigatória, share-alike nos derivados de arte).
- **Manutenção**: Generative Agents original e Voyager são código de paper (pouco mantidos); AutoGen em manutenção; Flowise arquivado. Não depender deles em runtime.
- **Acoplamento**: AI Town ↔ Convex; Letta é runtime, não lib; Hindsight exige serviço próprio (verificar footprint).
- **Validade científica** (simulação econômica): personas LLM precisam de calibração com dados reais; TinyTroupe tem facilidades de validação, mas não substitui dados.
- **Custo**: multi-agente + conversas cresce superlinearmente; o roteador e o budget guard precisam existir desde a fase 0.

---

## 17. Próximos passos sugeridos (antes da spec)

1. **Spike de 1 tarde com AI Town local** (Convex local + Ollama): sentir o loop, ler `engine.ts` e a máquina de conversa.
2. **Spike de 1 tarde com Hindsight** (Docker): inserir 20 observações da "fazenda", rodar `reflect`, ver se forma uma opinião sobre o rio com confiança, e se dá para contradizê-la.
3. **Spike de 2 horas com Phaser 3 + Tiled + LPC**: um mapa de fazenda com um sprite andando por A*.
4. Fechar na spec: Python no kernel; memória baseline + Hindsight; Phaser; LiteLLM; Langfuse + OTel; Flipt ou YAML para flags.

---

### Fontes principais consultadas
- Generative Agents (Park et al., 2023) — arXiv 2304.03442
- AI Town — github.com/a16z-infra/ai-town; convex.dev/ai-town
- Concordia — github.com/google-deepmind/concordia; arXiv 2312.03664; nota de lançamento da v2.0 (Cooperative AI Foundation)
- TinyTroupe — github.com/microsoft/tinytroupe; arXiv 2507.09788
- OASIS — github.com/camel-ai/oasis; arXiv 2411.11581
- AgentSociety — arXiv 2502.08691
- Project Sid / PIANO — github.com/altera-al/project-sid; arXiv 2411.00114
- Voyager — github.com/MineDojo/Voyager
- Hindsight — github.com/vectorize-io/hindsight; demo ACL 2026
- GoRules ZEN — github.com/gorules/zen; pypi zen-engine
- Comparativos de memória de agentes 2026 (Atlan, Braintrust, Graphlit, Stork)
- Comparativos de observabilidade (Langfuse docs, FutureAGI, Laminar)
- AWS AgentCore release notes (ago–set/2026); Strands Agents SDK
- Projetos de fazenda em Godot/LPC (Hortica Botanica, Sunset Valley, Farm prototype)
