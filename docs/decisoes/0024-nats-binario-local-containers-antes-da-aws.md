# ADR-0024 — NATS como binário local agora; containers antes da AWS

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M2
**Altera:** CLAUDE.md, tabela de stack ("`docker compose` para o NATS") e estrutura (`docker-compose.yml`)

## Contexto

- A máquina de desenvolvimento não tem Docker nem Homebrew.
- O NATS só é necessário a partir do M2.
- O futuro é a AWS (ECS Fargate), que executa containers.

## Decisão

1. **Até a ida para a AWS:** `nats-server` como binário.
   - Versão fixa (linha 2.14, a estável atual), baixada por `make tools` para `.tools/` dentro do repositório, com conferência de checksum.
   - `make up` sobe o servidor com `config/nats/nats.conf`, que guarda JetStream, usuários e permissões.
2. **Antes da AWS** (depois da v0.1, ou quando gerenciar os processos em terminais ficar trabalhoso):
   - um Dockerfile por serviço;
   - `docker-compose.yml` com a imagem oficial do NATS, usando o **mesmo** `nats.conf`.
   - As mesmas imagens vão para o ECS. No Mac, OrbStack ou Docker Desktop, decidido nessa hora.

## Consequências

- A migração para a AWS não depende de como o NATS roda localmente. Ela depende da porta `EventBus` (o código não sabe onde o NATS está) e de os serviços virarem imagens de container.
- `make up` continua sendo o ponto de entrada; só muda o que ele executa.
- O `docker-compose.yml` sai da estrutura inicial e volta quando os containers entrarem, para não manter um arquivo que ninguém testa.
