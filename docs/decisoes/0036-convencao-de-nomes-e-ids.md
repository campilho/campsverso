# ADR-0036 — Convenção de nomes e ids

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M1
**Consolida:** catálogo §1.3 e §1.4; ADR-0030, ADR-0031

## Contexto

Com cartuchos em camadas (ADR-0031) e, no futuro, vários mundos e muitos agentes, apareceu a pergunta: os nomes precisam ser únicos em todos os cartuchos? As regras estavam espalhadas pelo catálogo e pelas ADRs.

## Decisão

| O quê | Formato | Exemplos | Único dentro de |
|---|---|---|---|
| Mundo (`worldid`) | kebab-case | `farm-camps-01` | todo o sistema |
| Cartucho | snake_case (também é domínio de evento) | `farm`, `farm_camps` | todo o sistema |
| Controlador | `<tipo>/<nome>` | `script/farmer-v1`, `human/camps-browser` | todo o sistema |
| Entidade | kebab-case, em inglês; instâncias numeradas com 2 dígitos | `plot-e-03`, `sell-box`, `watering-can` | o mundo |
| Avatar | nome do personagem, minúsculas, sem acento | `camps`, `tomas` | o mundo |
| Instância de regra | snake_case | `river_proximity_bonus` | o mundo |
| Tipo de entidade, ação, sistema, implementação de regra | snake_case, em inglês | `sell_box`, `plant`, `crop_growth`, `water_proximity_bonus` | a cadeia de cartuchos |
| Item, cultura, necessidade, fase, estágio | snake_case, em português, sem acento | `semente_rabanete`, `fome`, `meio_dia`, `crescendo` | a cadeia de cartuchos |
| Atributo de entidade | snake_case | `watered_today` | o tipo de entidade |

Regras:

- **Não é preciso unicidade entre cartuchos que não se combinam.** Dois mundos podem ter um `bed` cada um, porque o envelope já traz `worldid` e `cartridge`. Os ids não repetem essa informação.
- **Dentro da cadeia de um mundo** (gênero + cenário), repetir um nome é erro de carga, a menos que a camada de cima declare `override` (ADR-0031).
- **Ids são estáveis.** Renomear um id já publicado é uma migração e pede ADR, porque o arquivo de eventos guarda os ids antigos.
- **Idioma:** estrutura em inglês e conteúdo do cartucho em português (CLAUDE.md, Convenções).

## Consequências

- O kernel valida a unicidade ao montar a cadeia de cartuchos e falha cedo, com o nome repetido na mensagem.
- Os padrões de formato já são conferidos pelos schemas dos contratos (`entity_id`, `item_id`, `token`).
