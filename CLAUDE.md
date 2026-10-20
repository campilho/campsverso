# CLAUDE.md — Campsverso

Campsverso é uma plataforma de simulação orientada a eventos para agentes de IA autônomos que vivem em mundos 2D. Cada mundo é um **cartucho** (fazenda, estúdio, startup…) rodando sobre um **kernel** genérico. A versão publicada é a **v0.1.0 "Fazenda do Camps"**: um avatar, nenhum LLM, controladores humano, script e replay. A **v0.2, a possessão** (`docs/planos/v0.2-macro.md`), está em construção: M8 a M12 feitos (o controlador LLM, ADR-0059; a memória baseline, ADR-0060; a arena, ADR-0061) e o M13, a Fazenda Boa Vista (a fazenda 2), em curso (ADR-0062); depois vêm o M14 (a segunda rodada da arena) e o M15 (fechamento).

O projeto também é material de aprendizado e de publicações. Clareza, testes e registro das decisões importam tanto quanto o código.

## Documentos de referência

Leia antes de qualquer tarefa não trivial, nesta ordem:

1. `docs/arquitetura/escopo-v0.1.md` — o que construir agora, marcos e critérios de aceite
2. `docs/arquitetura/fazenda-camps-biblia-v0.1.md` — regras e números do mundo
3. `docs/arquitetura/contratos-eventos-v0.md` — envelope, eventos, barramento, portas
4. `docs/arquitetura/kernel-gestao-do-tempo.md` — relógio e políticas de tempo
5. `docs/arquitetura/pesquisa-componentes-plataforma-simulacao.md` — bibliotecas avaliadas
6. `docs/arquitetura/catalogo-eventos-v0.1.md` — eventos e comandos da v0.1 (depois do M0, guia de leitura dos schemas em `contracts/`)
7. `docs/arquitetura/fazenda-boa-vista-biblia.md` — a fazenda 2 do M13: números, regras visíveis e ocultas, o fazendeiro-script 2
8. `docs/decisoes/README.md` — índice das ADRs. **Uma ADR aceita prevalece sobre o texto dos documentos acima.**

Se dois documentos conflitarem, ou se faltar uma decisão: **pare e pergunte**. Depois registre a decisão como ADR curto em `docs/decisoes/NNNN-titulo.md`.

## Princípios inegociáveis

1. **Módulos só se conhecem por contrato.** Nenhum serviço importa código de outro serviço. A única dependência compartilhada é o pacote gerado de contratos (`packages/contracts-py`, `packages/contracts-ts`).
2. **O kernel é o único escritor da verdade do mundo.** Controladores *propõem* (`campsverso.cmd.*`); o kernel valida, aplica e publica fatos.
3. **Todo recurso externo passa por uma porta.** SDKs de terceiros (NATS, SQLite, FastAPI etc.) só podem ser importados dentro de adaptadores ou da raiz de composição (`main.py` de cada serviço). O CI verifica isso.
4. **Determinismo.** Sistemas e regras são funções puras de (estado, tick, RNG nomeado). Nunca ler o relógio de parede dentro do kernel de simulação; nunca usar `random` global; ordenar por id sempre que a ordem de iteração afetar o resultado.
5. **Visibilidade é arquitetura.** Regras ocultas e eventos `internal` nunca chegam a controladores. A garantia vem das permissões de assunto do NATS, não de filtros no código.
6. **Eventos são imutáveis e versionados.** Dentro de uma versão maior, só campos opcionais novos. Mudança incompatível = novo tipo `...v2`.
7. **O mundo nunca espera ninguém**, exceto no modo máximo (lockstep), que é exclusivo de controladores `script` e `replay`.
8. **O kernel conhece a física de um mundo, não as fazendas.** O kernel implementa um modelo de mundo genérico: tempo, espaço, entidades, itens, necessidades, ações, avatares, clima e regras (ADR-0025). Culturas, preços, horários, ações e o mapa são dados e código do cartucho em `cartridges/farm/`, compostos a partir dessas primitivas. Cartuchos mudam o mundo só pelas primitivas, então toda mudança de estado vira um evento genérico. Cartuchos podem estender outros cartuchos, do gênero (`farm`) ao cenário (`farm_camps`) (ADR-0031). O kernel nunca importa um cartucho: os dois se encontram só pelas interfaces de `libs/cartridge-api`, e o kernel carrega o cartucho pelo nome definido na configuração (ADR-0011).

## Stack

| Camada | Escolha |
|---|---|
| Backend | Python 3.14 (ADR-0034), `uv` workspaces, asyncio, Pydantic v2, FastAPI |
| Barramento | NATS JetStream (`nats-py`); `InMemoryBus` para testes |
| Modelos | API da Anthropic pelo SDK oficial, só dentro de `libs/adapters` (ADR-0058); respostas gravadas em fitas JSONL para testar sem custo; o CI nunca chama a API |
| Estado | SQLite (estado + outbox); snapshots em disco; arquivo JSONL |
| Contratos | JSON Schema 2020-12 (fonte da verdade) + AsyncAPI 3.1 (gerado); codegen com `datamodel-code-generator` (Python) e `json-schema-to-typescript` (TS); validação com `jsonschema` e `ajv` com os mesmos códigos de erro (ADR-0033) |
| Frontend | TypeScript 6.0 estrito, `pnpm` 12, Node 24 fixado no projeto, Vite, Phaser 4 (ADR-0053), Vitest (ADR-0032) |
| Qualidade | `ruff`, `pyright` em modo estrito, `pytest` + `hypothesis`, `import-linter`; `eslint`, `dependency-cruiser` |
| CI | GitHub Actions roda `make setup` e `make check` a cada push e pull request (ADR-0035) |
| Infra local | `nats-server` como binário em `.tools/` (ADR-0024; containers antes da AWS); `make` como ponto de entrada |

## Estrutura do repositório

```
campsverso/
  CLAUDE.md
  Makefile
  contracts/                  # FONTE DA VERDADE dos contratos
    common/  envelope/  events/  commands/  realtime/  live/  examples/{valid,invalid}/  domains.json
    asyncapi.yaml             # GERADO a partir dos schemas
    CHANGELOG.md
  packages/
    contracts-py/             # GERADO — não editar à mão
    contracts-ts/             # GERADO — não editar à mão
  libs/
    ports/                    # interfaces das portas (Python)
    cartridge-api/            # interfaces que um cartucho implementa (ADR-0011)
    adapters/                 # nats, inmemory, sqlite, jsonl, blob-local, fastapi (WebSocket), a porta de modelo (Anthropic, fita, medidor), a memória em SQLite...
    world-view/               # projeção genérica do mundo a partir dos eventos (percepção e gateway; ADR-0050)
    mind/                     # a mente genérica do controlador LLM: janela de conversa, ferramentas do catálogo, proposta (ADR-0059); a memória: episódios, caderno, reflexão (ADR-0060)
  services/
    kernel/                   # relógio, ECS, grid, ações, regras, outbox
    perception/               # filtro de percepção
    controller-runner/        # controladores script e replay
    gateway/                  # FastAPI + WebSocket; entrada do controlador humano
    archiver/                 # JetStream -> JSONL
    budget/                   # guarda de orçamento: soma o custo das chamadas de modelo e pausa o mundo no teto (ADR-0058)
  cartridges/                 # em camadas: gênero → cenário (ADR-0031)
    farm/                     # gênero: mecânicas genéricas de fazenda
      sim/                    # itens, culturas, ações, sistemas, regras (carregado pelo kernel)
      script/                 # fazendeiro-script; depende só dos contratos (carregado pelo controller-runner)
      mind/                   # o que a mente sabe da fazenda: notas do mundo e descrições das ferramentas (ADR-0059)
      art/                    # arte LPC do gênero e o manifesto art.json, com CREDITS.csv (ADR-0053)
    farm_camps/               # cenário da v0.1: estende farm
      sim/                    # mapa (Tiled), avatar camps, ajustes de números, R-001
      art/                    # o Camps (sprite LPC), o mapa visual e o manifesto do cenário
      mind/                   # o cartão de identidade do Camps; entry point campsverso.minds (ADR-0059)
    farm_boavista/            # a Fazenda Boa Vista, a fazenda 2 do M13 (ADR-0062): estende farm_camps
      sim/                    # mapa sem canteiros com o fogão, boavista.yaml (as mecânicas ligadas por dados), R-001
      art/                    # o mapa visual; o resto vem das camadas farm e farm_camps
      mind/                   # o manual e o catálogo da fazenda 2 sobre o cartão do Camps; entry point camps_boavista
  apps/
    ui/                       # Vite + Phaser
  tools/
    contracts/                # validação, codegen e compatibilidade (Python)
    contracts-ts/             # validação com ajv e codegen TypeScript
  config/
    env/local.yaml            # retenção dos streams, snapshots, arquivo, caminhos
    worlds/                   # um arquivo por mundo: cartucho, seed, data-base, relógio inicial
    nats/                     # usuários e permissões por processo (senhas em .env, fora do git)
  data/                       # gitignored: sqlite, snapshots, archive
  docs/
    arquitetura/  decisoes/  diario/   # diario/README.md: índice e "a v0.1 em números"
    planos/                   # plano de cada marco, aprovado antes do código; futuro.md: tarefas sem marco
    design/                   # referências visuais (Claude Design)
    custos/                   # tempo e tokens por marco (make sessoes), só números
    arena/                    # os relatórios da arena (make arena-report), um por data (ADR-0061)
    versoes/                  # notas de cada versão (v0.1.0)
  tests/
    e2e/                      # resistência, determinismo, replay, recuperação
    support/                  # campsverso_testkit: mundos e roteiros para testes (ADR-0040)
    fixtures/llm/           # fitas de teste do controlador LLM, magras: hash do pedido e resposta (ADR-0059)
```

## Convenções

- **Idioma:** código, identificadores e nomes de eventos em inglês; documentação, ADRs, diário e textos de UI em português; dados de conteúdo do cartucho (nomes de itens como `rabanete`) em português.
- **Eventos:** `campsverso.<dominio>.<nome_no_passado>.v<major>`. **Comandos:** `campsverso.cmd.<dominio>.<verbo>.v<major>`. Domínios do kernel são reservados; eventos próprios de um cartucho usam como domínio o nome do cartucho que os declara (ex. `campsverso.farm.crop.matured.v1`, mesmo num mundo `farm_camps`).
- **Campos:** payloads em `snake_case` (`applied_tick`, `avatar_id`); atributos do envelope seguem o CloudEvents (`correlationid`) (ADR-0030).
- **IDs:** UUIDv7 para eventos; ids legíveis e estáveis para entidades (`plot-e-03`, `camps`).
- **Envelope:** CloudEvents 1.0 com as extensões definidas no contrato; todo evento publicado é validado contra o schema em desenvolvimento e nos testes.
- **Testes:** escreva o teste junto com o código. Sistemas e ações têm testes de unidade; o fluxo completo tem testes e2e com `InMemoryBus` e com NATS.
- **Commits:** pequenos, um assunto por commit, mensagens em português no formato `tipo: descrição` (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).

## Comandos

```
make help         # lista os alvos
make setup        # instala dependências Python e TS e o nats-server (make tools)
make contracts    # valida schemas e regenera packages/contracts-*
make check        # lint + tipos + testes + teste de arquitetura + validação de contratos
make tools        # baixa o nats-server com versão e sha256 fixados (.tools/)
make secrets      # gera em .env (fora do git) as senhas do NATS que faltam
make up           # sobe o NATS em segundo plano
make stop         # derruba o NATS
make run          # sobe o NATS e o Procfile (honcho): kernel, percepção, script, arquivador e gateway
make sandbox      # mundo descartável com tudo ligado, em data/sandbox/<data-hora> (não toca no oficial); MENTE=camps põe o LLM no Camps (ADR-0059)
make ui-build     # compila a UI em apps/ui/dist; o gateway a serve em http://127.0.0.1:8765
make ui           # a UI em modo desenvolvimento (Vite), com proxy para o gateway
make ui-e2e       # fumaça da tela no navegador (Playwright), com um sandbox próprio (porta 8799)
make soak DAYS=30 # resistência em modo máximo, com processos e NATS próprios (SEM_REGRA=1); MUNDO=farm-boavista-01 escolhe o mundo (também em sandbox, run, replay e metrics)
make replay DAY=N # reexecuta um dia a partir do snapshot e do diário e compara com o arquivo
make metrics      # métricas da bíblia §13 a partir do arquivo (ARCHIVE=pasta do mundo)
make percepcao    # fotos e deltas da percepção por dia, em bytes e tokens estimados (ADR-0056); CONTAR=20 calibra com count_tokens
make llm-smoke    # uma chamada real pela porta de modelo, medida e publicada pelo contrato (ADR-0058); pede ANTHROPIC_API_KEY no .env
make fita DIAS=2  # grava em processo a fita de teste do controlador LLM, chamando a API (ADR-0059); o CI só a reproduz; CARTUCHO=farm_boavista grava a da fazenda 2
make corrida DIAS=7   # N dias em processo com a mente sobre a API, com ou sem memória (ADR-0060); o mundo espera o modelo
make arena DIAS=30    # as corridas da arena, em sequência, em data/arena/<data-hora> (ADR-0061); SO=nome roda uma só
make arena-report     # o relatório da arena (tabela da bíblia lado a lado, o leste pela memória) em docs/arena/
make mapa-visual  # regrava o mapa visual da fazenda a partir do mapa lógico (ADR-0053)
make sessoes      # tempo e tokens do Claude Code por turno e por marco em docs/custos (MARCO=M5)
```

Os alvos de marcos futuros já existem e avisam "ainda não implementado (marco Mx)". `make check` inclui `make contracts-check` (validação nos dois validadores e codegen sem diferenças) e `make compat` (compatibilidade com `COMPAT_BASE`, padrão `HEAD`).

## Como trabalhar neste repositório

1. **Um marco por vez** (ver `escopo-v0.1.md`, seção 7). Comece pelo plano, peça confirmação, depois implemente.
2. Ao fim de cada marco: `make check` verde (local e no CI), commit, e uma entrada em `docs/diario/AAAA-MM-DD.md` (o que foi feito, o que deu errado, decisões, números, uma frase "para o LinkedIn").
3. Mudou um contrato? Atualize o schema em `contracts/`, os exemplos, o `CHANGELOG.md` e rode `make contracts`. Nunca edite os pacotes gerados.
4. Ajustes de equilíbrio do mundo (preços, tempos, probabilidades) vão na configuração do cartucho, nunca no kernel.

## Nunca faça

- Importar NATS, SQLite, FastAPI ou qualquer SDK fora de `libs/adapters/` ou da raiz de composição.
- Ler `datetime.now()`/`time.time()` dentro de sistemas, regras ou ações do kernel.
- Escrever estado do mundo fora do kernel, ou decidir regra de jogo na UI.
- Expor pontos de crescimento, regras ocultas ou eventos `internal` à percepção ou aos controladores.
- Chamar um modelo fora da `ModelPort` (ADR-0058), ou deixar o CI chamar a API: os testes usam o transporte falso do SDK e as fitas.
- Escrever a regra oculta, ou uma dica dela, no cartão de identidade ou nas notas da mente (princípio 5): o LLM só vê os efeitos.
- Dar à mente mais memória do que a `MemoryPort` (ADR-0060) guarda, ou qualquer item marcado "fora" no escopo da v0.2.
- Apagar ou reescrever arquivos em `data/archive/` (são o registro histórico dos experimentos).
- Publicar evento sem schema, ou criar tipo de evento não declarado em `contracts/`.
