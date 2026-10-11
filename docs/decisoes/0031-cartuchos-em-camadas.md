# ADR-0031 — Cartuchos em camadas: gênero, cenário, mundo

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0 (estrutura, nome do cartucho), M1 (carregamento)
**Complementa:** ADR-0011 (API de cartucho) e ADR-0025 (modelo de mundo)
**Refina:** ADR-0012 (padrão do nome do cartucho)
**Esclarece:** `fazenda-camps-biblia-v0.1.md` §1 ("este mesmo cartucho com outro mapa, outros personagens")

## Contexto

A pergunta na revisão: os cartuchos podem ser incrementais? Por exemplo, um cartucho macro de "fazenda", e o vilarejo remoto na Patagônia como uma especialização dele. Assim o mundo se expande com cartuchos novos conforme a necessidade, e o kernel fica só com o que é genérico de verdade.

## Decisão

### Três níveis

| Nível | O que é | Exemplos |
|---|---|---|
| **Kernel** | a física genérica (ADR-0025) | tempo, espaço, entidades, itens, necessidades, ações, regras |
| **Cartuchos** | pacotes de conteúdo e comportamento que podem **depender de outros cartuchos e estendê-los** | `farm` (gênero: cultivo, rega, crescimento, comprador, quiosque, sono na cama, fazendeiro-script); `farm_camps` (cenário: mapa, avatar `camps`, preços, R-001); no futuro, `vilarejo` (cenário na Patagônia: mapa, moradores, regras próprias) |
| **Mundo** | uma instância, definida na configuração | `farm-camps-01`: cartucho do topo `farm_camps`, seed, relógio |

"Gênero" e "cenário" são convenções de uso, não tipos diferentes: tudo é cartucho.

### Mecanismo mínimo da v0.1

1. **Manifesto:** cada cartucho declara `id`, `version` e `extends`, a lista dos cartuchos sobre os quais se apoia, em ordem.
   - Na v0.1, uma cadeia simples: `farm_camps` estende `farm`.
   - A lista permite, mais tarde, compor vários cartuchos pequenos (ex.: um vilarejo = `farm` + comércio + social), como a ordem de carga de mods num jogo.
2. **Montagem:** o kernel resolve a cadeia da base para o topo.
   - Dados são mesclados por chave: camadas de cima acrescentam ou substituem itens, culturas, preços, tipos de entidade, ações.
   - Os registros de código (sistemas, ações, regras) acrescentam ou substituem por nome.
   - Substituir exige marcação explícita (`override`), para não esconder algo da base sem querer.
3. **Isolamento:** o kernel continua sem importar cartuchos. Carrega a cadeia pelo nome, via *entry points* (ADR-0011).
4. **Eventos:**
   - um tipo de evento pertence ao cartucho que o **declara**: `campsverso.farm.crop.matured.v1` mantém o domínio `farm` mesmo num mundo que roda `farm_camps`;
   - o campo `cartridge` do envelope traz o cartucho do **topo** do mundo (`farm_camps`).
5. **Nome do cartucho:** precisa servir como domínio de evento, então o padrão passa a ser `^[a-z][a-z0-9_]*$` (sem hífen). Isso refina a ADR-0012; o `worldid` continua aceitando hífen (`farm-camps-01`).
6. **A v0.1 já nasce com duas camadas:** `farm` e `farm_camps`. Isso prova o mecanismo cedo; adaptar depois mexeria em ids, dados e testes.

## Consequências

- **Estrutura:** `cartridges/farm/{sim,script}` e `cartridges/farm_camps/sim`. O script é do gênero: um fazendeiro genérico, que serve a qualquer fazenda.
- **A bíblia se divide em duas partes no M1:**
  - genérico da fazenda: mecânicas de cultivo, necessidades, sono, comprador, quiosque, catálogo de ações, valores padrão;
  - específico do Camps: mapa, avatar, ajustes de números, R-001.
  - Se a R-001 vira uma regra genérica do gênero ("bônus por proximidade de água", ligada por cenário) ou fica no cenário, decide-se no M1.
- **Risco conhecido:** cadeias de herança profundas ficam confusas (o problema clássico da orientação a objetos). Regra prática: no máximo 2 ou 3 níveis, e preferir compor cartuchos pequenos quando o vilarejo chegar.
- **Contratos:** eventos do gênero ficam em `contracts/events/farm/`; os de um cenário, se houver, em `contracts/events/farm_camps/`.
