# ADR-0032 — Ferramentas TypeScript: Node 24 no projeto, pnpm 12, TypeScript 6.0

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0
**Complementa:** CLAUDE.md, tabela de stack (linha Frontend)

## Contexto

Três achados ao montar o lado TypeScript:

- O Node do sistema (22.11) é velho demais para o Vite, que exige `^20.19.0 || >=22.12.0`. Atualizá-lo globalmente pediria senha de administrador e mexeria em outros projetos da máquina.
- O `corepack` que veio com esse Node falha na verificação de assinatura do registro npm.
- O TypeScript 7.0 (a reescrita nativa) é a versão mais nova, mas o `typescript-eslint` 8.71 aceita até a 6.0.

## Decisão

- **pnpm 12**, instalado em `~/.local` a partir de `@pnpm/exe`, que traz o próprio runtime.
- **Node 24 LTS fixado só neste projeto** pelo `devEngines.runtime` do `package.json`. O pnpm baixa a versão e a usa nos scripts; o Node global fica intocado.
- **TypeScript 6.0** (`~6.0.0`) até o `typescript-eslint` suportar o 7.
- **Scripts de instalação bloqueados por padrão** (comportamento do pnpm 12). Cada exceção fica explícita em `pnpm-workspace.yaml` (`allowBuilds`). O primeiro caso é negativo: `@scarf/scarf`, um pacote de telemetria de downloads que vem com o `@asyncapi/parser`.

## Consequências

- `pnpm` é o único comando necessário do lado TS; quem clona o repositório recebe o Node certo automaticamente.
- Migrar para o TypeScript 7 é uma troca de versão quando o ecossistema de lint acompanhar.
