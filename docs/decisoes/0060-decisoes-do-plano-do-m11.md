# ADR-0060 — Decisões do plano do M11 (memória baseline)

**Status:** aceita · **Data:** 2026-10-18 · **Marco:** M11
**Complementa:** `docs/planos/m11-memoria-baseline.md`; `docs/planos/v0.2-macro.md`; contratos §8.4 e §12.1; tempo §9.1; pesquisa §7; ADR-0055, ADR-0056, ADR-0058, ADR-0059
**Altera:** contratos §12.1 (a memória mora na mente, não num serviço; sem `cmd.memory.recall` por enquanto)

## Decisão

As decisões do plano, aprovadas pelo usuário em 18/out/2026:

1. **`MemoryPort` com três operações:** registrar (`record`, `note`), lembrar (`episodes`, `notes`, `beliefs`, `last_reflection`, `salient`) e refletir (`save_reflection`, que devolve a diferença das crenças), sobre os tipos episódio, anotação, crença e reflexão.
2. **Adaptador SQLite (`SqliteMemory`), um arquivo por avatar e por mundo** (`data/<mundo>/memory/<avatar>.sqlite`), fora do snapshot do mundo: é o que o supervisor da v0.3 copia. Sem vetores no M11; a relevância por embeddings (sqlite-vec, `EmbeddingPort`) fica para quando a memória não couber no bloco.
3. **A memória mora no processo da mente.** O recall é uma leitura local a cada janela; o operador vê o que precisa por eventos. Um serviço de memória com `cmd.memory.recall` só quando houver um segundo consumidor.
4. **Todo delta vira episódios sem chamada ao modelo,** uma linha por evento percebido e por proposta própria, com tags (ids de entidade) e importância por tabela (desmaio 10; colheita, madura e murcha 7; recusa 6; comprar, vender, comer 4; plantar, regar, encher 3; fase e clima 2; andar e esperar 1).
5. **A anotação é o parâmetro `note`, obrigatório em toda ferramenta,** com "ou vazio"; vazio não guarda; o resto vira anotação com o tick e o evento `memory.noted`.
6. **Toda janela abre com o bloco de memória,** antes da foto: o resumo de ontem e o plano para hoje, as crenças por confiança (até 20), as anotações de hoje (até 20), os episódios marcantes de hoje (até 10, por recência × importância) e a última ação com a intenção; capado em uns mil tokens. `minds.<avatar>.memory.enabled: false` devolve o M10, a linha de base da arena.
7. **A reflexão roda uma vez por dia, na hora em que a mente propõe dormir,** seja a hora que for (o Camps pode dormir a qualquer hora, de dia ou de noite), síncrona, com modelo e esforço próprios (`minds.<avatar>.reflection`), medida e gravada como qualquer chamada; se o dia virar sem proposta de sono (desmaio), ela roda na primeira entrega da manhã, antes da decisão. **Ressalva do usuário:** no futuro a reflexão pode depender de quanto se dormiu (dormir bem reflete melhor; dormir pouco, pior), como num humano; fica no `futuro.md`.
8. **A reflexão é a ferramenta estrita `reflect`:** entra o dia (episódios, anotações, crenças atuais com ids) e sai `summary`, `plan` e a lista inteira de crenças revisadas (`id`, `statement`, `confidence`, `evidence`, `status: new|confirmed|weakened|retracted`, `reason`); o adaptador calcula a diferença.
9. **Crença com `confidence` (0 a 1), `evidence` (ticks e fatos do que o agente viu) e `source`** (`observation` agora; `told`, com `by`, na camada social). As evidências nunca citam o `internal`; o teste confere que cada tick citado existe no arquivo do pipeline.
10. **Cinco eventos `observer` no domínio `memory`, produtor `controller`:** `memory.noted.v1`, `memory.reflected.v1`, `memory.belief.formed.v1`, `memory.belief.updated.v1`, `memory.belief.retracted.v1`. Os episódios não viram evento: já estão no arquivo.
11. **O caderno do avatar na tela do operador:** o `ObserverState` ganha `memory` (opcional, por avatar: crenças, últimas anotações, último resumo e plano), projetado dos eventos `memory.*`; o painel do operador ganha a seção "Caderno". A visão do jogador não muda.
12. **Hindsight avaliado e não adotado no M11:** PostgreSQL com pgvector num projeto local em SQLite, reflexão com chamadas próprias fora da porta, do medidor, da guarda e da fita, e a ablação precisa de uma linha de base nossa. O que vale emprestar é a separação entre o que o agente viu e o que acredita, e a confiança com evidência. Um adaptador Hindsight pela `MemoryPort` fica para a v0.5.

## Consequências

- `libs/ports` ganha `MemoryPort`; `libs/adapters`, o `SqliteMemory`; `libs/mind`, os episódios, o bloco, a reflexão e os eventos; o runner publica os eventos de memória com o usuário `mind` (`observer.memory.>`).
- Contratos: cinco tipos novos no domínio `memory` (já reservado), `belief_id`, `confidence` e `belief_source` nas definições comuns, e `memory` opcional no `ObserverState`. Nenhum tipo muda.
- O prompt muda (bloco de memória, `note` nas ferramentas): a fita do dia 1 é regravada, e a de dois dias (`make fita DIAS=2`) passa a ser a fixture.
- Fora do M11: vetores e relevância, importância pontuada por modelo, serviço de memória com request-reply, origem `told`, reflexão por lote, reflexão proporcional ao sono, adaptador Hindsight.
