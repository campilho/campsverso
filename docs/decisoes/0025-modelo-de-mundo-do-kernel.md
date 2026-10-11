# ADR-0025 — Modelo de mundo do kernel: a "física" genérica

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0 (contratos), M1 (kernel)
**Complementa:** CLAUDE.md, princípio 8; ADR-0011
**Altera:** `contratos-eventos-v0.md` §14.3 (lista de eventos do cartucho `farm`)

## Contexto

O princípio 8 diz o que o kernel **não** conhece (fazendas), mas não diz o que ele **conhece**. A direção dada na revisão do catálogo (P1 e P5):

- como uma engine de jogo, o kernel deve conhecer a física básica de um mundo simulado;
- uma casa num mundo e uma casa noutro podem ser diferentes, mas ambas obedecem às mesmas regras;
- o mesmo kernel precisa servir uma fazenda, um escritório, uma vila e, um dia, um mundo inteiro com centenas de agentes e humanos.

## Decisão

1. O kernel implementa um **modelo de mundo genérico**: as primitivas da tabela abaixo. Cartuchos fornecem **conteúdo** (dados) e **comportamento específico** (sistemas, ações e regras), sempre compostos a partir dessas primitivas.
2. **Cartuchos só mudam o mundo pelas primitivas**, através de `libs/cartridge-api`. Não acessam o estado diretamente. Toda mudança de estado vira automaticamente um **evento genérico** publicado pelo kernel. Por isso percepção, UI, arquivo e métricas genéricas funcionam com qualquer cartucho sem conhecê-lo.
3. **Evento próprio do cartucho só quando carrega significado** que os genéricos não carregam (ex.: "a planta amadureceu em 2 dias"). Nunca para repetir uma mudança de estado que já saiu num evento genérico.
4. **O modelo cresce por adição.** Uma primitiva nova entra quando um cartucho real precisar dela, com ADR e eventos genéricos próprios.

### Primitivas da v0.1

| Primitiva | O que o kernel garante | Eventos genéricos | O que o cartucho fornece (fazenda) |
|---|---|---|---|
| **Tempo** | tick fixo, escala, modos, pausa, fases do dia, agenda de sistemas por horário | `world.session.started`, `world.clock.*` | duração do tick, nomes e horários das fases, horário de cada sistema |
| **Espaço** | grade de tiles, passável ou bloqueado, vizinhança, pathfinding, movimento como trajeto | `world.entity.moved`, `world.entity.move_interrupted` | mapa Tiled, velocidade de deslocamento |
| **Entidades** | id, tipo, posição ou contêiner, atributos visíveis e ocultos | `world.entity.spawned`, `world.entity.state_changed` | tipos (`plot`, `kiosk`, `bed`…) e seus atributos (`stage`, `open`…) |
| **Itens e contêineres** | itens empilháveis, contêineres, transferência atômica; moeda é item | `world.item.created`, `.transferred`, `.consumed` | catálogo de itens e conteúdo inicial |
| **Necessidades** | medidores 0–100 com taxas por estado (acordado, dormindo) e limiares | `world.need.changed`, `.threshold_crossed` | fome e energia, taxas e limiares |
| **Ações** | ciclo propor → validar → aceitar → executar com duração → concluir, falhar ou cancelar; custo; adjacência | `action.*` | catálogo de ações, pré-condições e efeitos |
| **Avatares e posse** | corpo com um controlador plugável; pedido de decisão; sono e desmaio | `avatar.*` | avatar `camps` e seu controlador padrão |
| **Clima** | condição do dia sorteada num fluxo de RNG próprio | `world.weather.changed` | condições e probabilidades |
| **Regras** | registro versionado de regras visíveis e ocultas, com alternância a quente | `rules.*` | R-001 e seus parâmetros |
| **Aleatoriedade** | fluxos de RNG nomeados, com seed registrada | (seed em `world.session.started`) | nomes dos fluxos |
| **Visibilidade** | todo atributo e todo evento têm visibilidade; o serviço de percepção monta a visão filtrada | `perception.delivered` | quais atributos são visíveis |

## Consequências

- **Nada muda na arquitetura de processos nem nos princípios.** O princípio 8 ganha o lado positivo: o kernel conhece a física, não as fazendas.
- `libs/cartridge-api` expõe as **operações** das primitivas (mover, transferir item, alterar atributo, ajustar necessidade, agendar sistema, emitir evento semântico), não o armazenamento de estado.
- Os eventos do cartucho `farm` caem de 8 para 3: `farm.crop.matured`, `farm.crop.withered` e `farm.buyer.paid`.
  - `crop.planted`, `crop.stage_changed`, `plot.watered`, `kiosk.opened` e `kiosk.closed` saem: essas mudanças já aparecem em `world.entity.state_changed` e `action.completed`.
- **Exemplos de adições futuras (não agora):**
  - vários mapas ou zonas (o interior de uma casa);
  - entrar e sair de cena (§14.5);
  - proximidade entre avatares;
  - raio de percepção;
  - entidades criadas e removidas durante a execução (`entity.despawned`);
  - particionamento espacial para centenas de agentes.
- O paralelo com engines de jogo (física e cena genéricas, jogo como conteúdo) serve de material para os posts.
