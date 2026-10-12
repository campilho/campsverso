# Campsverso

[![check](https://github.com/campilho/campsverso/actions/workflows/check.yml/badge.svg)](https://github.com/campilho/campsverso/actions/workflows/check.yml)

Plataforma de simulação orientada a eventos para agentes autônomos que vivem em mundos 2D. Os avatares podem ser controlados por humanos, por scripts e, a partir da v0.2, por LLMs.

Cada mundo é um **cartucho** (fazenda, estúdio, vilarejo…) rodando sobre um **kernel** genérico. O kernel conhece a "física" de um mundo simulado: tempo, espaço, entidades, itens, necessidades, ações e regras. Isso inclui **regras ocultas**, que os agentes precisam descobrir observando o mundo.

Projeto pessoal de aprendizado, construído em público com a ajuda do Claude Code e documentado passo a passo.

## Status

**v0.1 "Fazenda do Camps"**, em construção. Um avatar, nenhum LLM; controladores humano, script e replay. Detalhes no [escopo da v0.1](docs/arquitetura/escopo-v0.1.md).

| Marco | Situação |
|---|---|
| M0: fundação (monorepo, contratos, codegen, CI) | concluído |
| M1: kernel sem barramento (modelo de mundo, relógio, ações, regras, cartuchos farm e farm_camps) | concluído |
| M2: durabilidade (NATS, outbox, arquivo JSONL, snapshots, retomada) | concluído |
| M3: controladores headless (percepção, fazendeiro-script, replay, modo máximo) | concluído |
| M4: UI de depuração (gateway WebSocket, canvas, visões jogador/operador, controles do relógio) | próximo |

## Como começar

Requisitos: [uv](https://docs.astral.sh/uv/) e [pnpm](https://pnpm.io/). O uv instala o Python 3.14; o pnpm usa o Node 24 fixado no projeto.

```bash
make setup   # dependências Python e TypeScript, e o nats-server com versão fixa
make check   # lint, tipos, testes, arquitetura e contratos
make run     # sobe o NATS, o kernel, a percepção, o fazendeiro-script e o arquivador
make stop    # derruba o NATS
make soak DAYS=30   # 30 dias simulados em modo máximo, com processos e NATS próprios
make metrics        # métricas do mundo a partir do arquivo de eventos
make help    # todos os alvos
```

O `make run` gera as senhas locais do NATS em `.env`, fora do git. O mundo fica em `data/farm-camps-01/` (estado e snapshots) e o histórico de eventos em `data/archive/`.

## Documentação

- [Arquitetura](docs/arquitetura/): escopo, bíblia do mundo, contratos de eventos, gestão do tempo, catálogo de eventos e pesquisa de componentes. A ordem de leitura está no escopo.
- [Contratos](contracts/): os JSON Schemas de todos os eventos e comandos (fonte da verdade) e o [changelog](contracts/CHANGELOG.md).
- [Decisões (ADRs)](docs/decisoes/README.md)
- [Diário de bordo](docs/diario/)

## Licença

[MIT](LICENSE)
