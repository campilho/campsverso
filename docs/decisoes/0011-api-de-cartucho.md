# ADR-0011 — API de cartucho em biblioteca própria; cartucho dividido em `sim` e `script`

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0 (estrutura), M1 (implementação)
**Complementa:** CLAUDE.md, princípios 1 e 8; estrutura do repositório

## Contexto

O kernel nunca importa um cartucho (princípio 8) e nenhum serviço importa código de outro (princípio 1). Mas `cartridges/farm/` contém duas coisas executadas por processos diferentes:

- mapa, itens, culturas, ações, sistemas e regras, executados pelo **kernel**;
- o fazendeiro-script, executado pelo **controller-runner**.

Os documentos não dizem como o kernel carrega um cartucho. Se o controller-runner importasse o cartucho inteiro, levaria junto o código que depende do kernel, quebrando o princípio 1 por tabela.

## Decisão

1. Criar a biblioteca **`libs/cartridge-api`**, só com interfaces (protocolos) e tipos: sistema, ação, regra, visão somente-leitura do estado, RNG nomeado e emissão de eventos. Nenhuma implementação do kernel, nenhum SDK externo.
2. Dividir cada cartucho em dois pacotes:
   - **`cartridges/farm/sim`**: dados (mapa Tiled, itens, culturas, preços, `rules.yaml`) e código de sistemas, ações e regras. Depende de `cartridge-api` e dos contratos.
   - **`cartridges/farm/script`**: fazendeiro-script. Depende **só** dos contratos (consome percepção, emite comandos).
3. O kernel descobre o cartucho **pelo nome, na configuração**, via *entry points* Python (grupo `campsverso.cartridges`). O controller-runner carrega controladores do mesmo jeito (grupo `campsverso.controllers`). Nenhum `import` estático de cartucho nos serviços.
4. O teste de arquitetura (`import-linter`) garante: kernel ↛ cartuchos; `cartridges/*/script` ↛ `cartridge-api` e kernel; serviço ↛ serviço.

## Consequências

- Kernel e cartuchos passam a se encontrar só por `cartridge-api`. Assim como `libs/ports`, é uma biblioteca de interfaces, não código de serviço. Nenhum outro serviço a importa.
- A API do cartucho vira um contrato interno: mudanças incompatíveis exigem nova versão maior da biblioteca.
- Um cartucho novo (estúdio, Patagônia, um RPG) é um par de pacotes que implementa a API, mais uma linha de configuração.
