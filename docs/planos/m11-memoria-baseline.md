# Plano do M11 — Memória baseline

**Status:** aprovado em 18/out/2026 (ADR-0060), com uma ressalva na decisão 7: a reflexão é uma por dia, na hora em que dormir, seja qual for; no futuro ela pode depender de quanto se dormiu. Quarto marco da v0.2 (`v0.2-macro.md`). O código começou com os 7 dias do M10 ainda rodando; a comparação da §9 espera os dois.

**Pronto quando (macro):** `MemoryPort` com registrar, lembrar e refletir; crenças com confiança e origem; Hindsight avaliado como camada de crenças; **a memória sobrevive a um reinício; uma reflexão cita fatos do arquivo de eventos.** Em testes: **(a)** o pipeline em memória reproduz dois dias do Camps pela fita; à noite do dia 1 a reflexão produz um resumo e crenças cujas evidências (ticks e fatos) existem no arquivo de eventos do próprio pipeline; a primeira janela do dia 2 abre com o resumo de ontem e as crenças; **(b)** o mesmo arquivo de memória, fechado e reaberto por um processo novo, devolve as mesmas crenças, e a mente reiniciada no meio do dia 2 abre a janela com o que anotou de manhã; **(c)** no sandbox, 7 dias com memória, comparados com os 7 dias do M10: recusas por dia e por motivo, colheitas e moedas, lado a lado, na §9.

## O que o levantamento mostrou

- **O M10 deixou o buraco no lugar certo.** Sem memória, a cada foto (a cada 20 deltas, uns 5 por dia) a conversa recomeça do zero: o Camps perde a manhã ao meio-dia e o dia inteiro ao acordar. A janela de conversa já carrega o que aconteceu no meio-tempo (`events` do delta, "alimenta a memória e a narrativa (M11)", diz o contrato), e as intenções já são um diário em primeira pessoa. Falta guardar, escolher e devolver.
- **O desenho de origem é mais ambicioso do que o marco precisa.** O documento de contratos previa um *serviço* de memória, com `cmd.memory.recall` em request-reply pelo NATS, eventos `memory.recorded`, `memory.belief.formed/updated/retracted` e `memory.skill.*`, consolidação durante o sono (`maintenance.consolidation.completed`) e as portas `MemoryPort` (própria: SQLite + sqlite-vec) e `EmbeddingPort`. O tempo (§9.1) decidiu que a consolidação é individual, quando o agente dorme, e que o padrão da fazenda é "acordar sonolento" se ela atrasar. A pesquisa (§7) recomendou **o memory stream simples como linha de base** (recência × importância × relevância, Generative Agents) e **avaliar o Hindsight** como camada de crenças.
- **Hindsight, avaliado.** É o candidato nº 1 da pesquisa: quatro redes (fatos do mundo, experiências, observações consolidadas, opiniões com confiança), operações *retain / recall / reflect*, grafo temporal de entidades, recuperação por vetor + BM25 + grafo + tempo ([paper](https://arxiv.org/pdf/2512.12818v1.pdf); [blog da Vectorize](https://vectorize.io/blog/hindsight-building-ai-agents-that-actually-learn)). Três razões para **não adotá-lo agora**: roda sobre PostgreSQL com pgvector (o projeto é local, em SQLite, sem containers até a AWS, ADR-0024); as operações *reflect* fazem as próprias chamadas de modelo, fora da `ModelPort`, do medidor, da guarda e da fita (o CI não reproduziria); e o experimento de ablação (M12) precisa de uma linha de base que seja nossa e pequena. O que vale emprestar: a separação entre o que o agente **viu** e o que **acredita**, a confiança que evolui com evidência, e os nomes das três operações. A `MemoryPort` deixa a porta aberta para um adaptador Hindsight na v0.5 ("memória completa", escopo §2).
- **Quando refletir.** A percepção só entrega quando o kernel pede decisão, e dormindo não se pede: o `sleep.started` chegaria no delta das 06:00, tarde demais para "refletir à noite". Mas a mente sabe quando propôs dormir: pode refletir logo depois, durante a noite real (8 h de sono são 6,7 min a 72×; a reflexão leva segundos), e acordar com a memória pronta. Se a noite chegar sem proposta de sono (desmaio às 02:00), a reflexão roda na primeira entrega da manhã, e o Camps "acorda sonolento" por uns minutos simulados, como o documento do tempo previu.
- **Uma anotação não pode custar uma chamada.** Uma ferramenta `anotar` separada gastaria um turno sem ação (e uma segunda chamada para agir). Um parâmetro `note` obrigatório em toda ferramenta, com "ou vazio", custa de 5 a 30 tokens de saída por decisão e nenhum turno a mais.
- **Custos.** A reflexão lê o dia (uns 100 episódios de uma linha, ~3 mil tokens), as anotações e as crenças, e escreve ~1 mil tokens: uns US$ 0,001 por noite no Haiku. O bloco de memória na abertura de cada janela (~1 mil tokens, 5 vezes por dia) entra no prefixo cacheado. O M11 inteiro, com duas fitas e os 7 dias, fica abaixo de US$ 0,50.
- **O escritório (ADR-0055) depende disto.** "A memória que sobrevive a um reinício" é o que dá sentido a um mundo que reinicia na versão que ele mesmo publicou: a memória precisa ser um arquivo por avatar, fora do snapshot do mundo, que o supervisor copia.

## 1. A porta e o adaptador (decisões 1 a 3)

- **`MemoryPort` em `libs/ports/memory.py`,** com três operações e os tipos que elas movem:
  - **registrar:** `record(episode)` (um episódio: tick, dia, hora, tipo, texto de uma linha, tags com os ids envolvidos, importância 1 a 10) e `note(note)` (uma anotação do próprio agente, com o tick);
  - **lembrar:** `episodes(day, limit)`, `notes(day)`, `beliefs()`, `last_reflection()`, e `salient(limit)` (os episódios mais marcantes pela conta recência × importância, a do memory stream);
  - **refletir:** `save_reflection(reflection)`, que guarda o resumo do dia, o plano para amanhã e a lista inteira de crenças revisadas, e devolve a diferença (formadas, atualizadas, retiradas).
- **Um adaptador, `SqliteMemory` em `libs/adapters`:** um arquivo por avatar e por mundo (`data/<mundo>/memory/<avatar>.sqlite`), com as tabelas `episodes`, `notes`, `beliefs` e `reflections`; em testes, `:memory:`. SQLite porque o resto do estado local já é SQLite, e porque um arquivo é o que o supervisor da v0.3 copia. **Sem vetores no M11:** a fazenda tem vinte entidades e as crenças cabem em vinte linhas; a relevância por embeddings (sqlite-vec e uma `EmbeddingPort`) fica para quando a memória não couber no bloco.
- **A memória mora no processo da mente,** não num serviço com request-reply: o recall a cada janela é uma leitura local, e a mente já segura a conversa. O que o operador precisa ver sai por eventos. Um serviço de memória, com `cmd.memory.recall`, só quando houver um segundo consumidor (o supervisor migrando memória, ou dois agentes que compartilham o que ouviram).

## 2. Registrar: episódios e anotações (decisões 4 e 5)

- **Todo delta vira episódios, sem chamada ao modelo:** cada evento dos `events` (o que o agente viu) e cada proposta da própria mente (ação, parâmetros e intenção) vira uma linha legível, com tags (os ids de entidade citados) e uma **importância por tabela**, não por LLM: desmaio 10; colheita, planta madura e planta murcha 7; recusa 6; comprar, vender, comer 4; plantar, regar, encher 3; fase do dia e clima 2; andar e esperar 1. É a importância do memory stream, barata e determinística; a pontuada por modelo fica no `futuro.md`.
- **A anotação é um parâmetro de toda ferramenta:** `note` (obrigatório nos esquemas estritos, com a instrução "algo que vale lembrar amanhã, ou vazio"). Vazio não guarda nada; o resto vira uma anotação com o tick e publica `memory.noted`. É o caderno do avatar, em primeira pessoa: "o canteiro e-01 amadureceu em dois dias; o w-01 ainda não".

## 3. Lembrar: o bloco de memória (decisão 6)

- **Toda janela abre com o que o agente lembra,** antes da foto, num bloco de texto com partes fixas e capadas (uns mil tokens): o resumo de ontem e o plano para hoje (da última reflexão); as crenças, por confiança (até 20); as anotações de hoje (até 20); os episódios marcantes de hoje (até 10, por recência × importância); e a última ação e intenção, para a janela não recomeçar sem fio. Nada de busca por relevância ainda: a lista é curta e o custo é do prefixo cacheado.
- **Sem memória, nada muda:** `minds.<avatar>.memory.enabled: false` devolve o comportamento do M10, que é a linha de base da arena (M12).

## 4. Refletir: a noite e as crenças (decisões 7 a 9)

- **A reflexão roda uma vez por dia, logo depois de a mente propor dormir** (`sleep` ou `sleep_here`), durante a noite real, sem bloquear o laço: uma chamada com `purpose: reflection`, modelo e esforço próprios (`minds.<avatar>.reflection: {model, effort: medium, max_tokens: 2048}`), medida e gravada como qualquer outra. Se o dia virar sem proposta de sono (desmaio), ela roda na primeira entrega da manhã, antes da decisão, e o Camps acorda sonolento por uns minutos. Síncrona, nunca por lote: o sono é longo o bastante.
- **A reflexão é uma ferramenta estrita, `reflect`:** entra o dia (episódios de uma linha, anotações, as crenças atuais com ids) e sai `summary` (o dia em 3 a 5 linhas), `plan` (amanhã, em 1 a 3 linhas) e `beliefs`, a lista inteira revisada: cada crença com `id` (o existente, ou novo), `statement`, `confidence` (0 a 1), `evidence` (ticks ou fatos de uma linha, do que o agente viu), `status` (`new`, `confirmed`, `weakened`, `retracted`) e `reason`. O adaptador compara com as crenças guardadas e produz a diferença.
- **Crença tem origem e evidência desde o primeiro dia.** `source: {kind: observation}` agora; `told`, com `by`, quando houver quem conte (v0.5, a camada social). As evidências citam ticks do que o agente percebeu, nunca o `internal`: a regra oculta continua oculta, e o que a reflexão pode descobrir é o efeito ("os canteiros do leste amadurecem em dois dias"). O teste (a) confere que cada tick citado existe no arquivo de eventos do pipeline.

## 5. Eventos, estado e a tela (decisões 10 e 11)

- **Cinco eventos `observer`, produtor `controller` (a mente),** no domínio `memory`, que já é reservado: `memory.noted.v1` (tick, texto), `memory.reflected.v1` (dia, resumo, plano, contagens de crenças formadas, atualizadas e retiradas, e o `prompt_sha256` da chamada), `memory.belief.formed.v1`, `memory.belief.updated.v1` (`confidence: {before, after}`, `evidence`, `source`, `reason`, como o §8.4 do documento de contratos, que dizia `from`/`to`; a convenção de campos reserva os dois) e `memory.belief.retracted.v1`. Os episódios **não** viram evento: já estão no arquivo, e `memory.recorded` seria ruído. O `maintenance.consolidation.completed` fica para quando houver manutenção; `memory.reflected` diz o mesmo para um avatar.
- **O caderno do avatar na tela do operador:** o `ObserverState` ganha `memory?` (por avatar: as crenças atuais, as últimas anotações e o último resumo), projetado pelo `libs/world-view` a partir dos eventos `memory.*`; o painel do operador ganha a seção "Caderno". A visão do jogador não muda: o caderno é do LLM.

## 6. Testes e fitas (decisão 12)

- **Unidade:** a porta falsa e o adaptador SQLite (ida e volta, reabrir o arquivo, a diferença das crenças); a mente com uma porta falsa (episódios e importância, a anotação que vira evento, o bloco na abertura da janela, a reflexão depois do `sleep`, a reflexão da manhã após desmaio, memória desligada = M10).
- **A fita, de dois dias:** `make fita DIAS=2` regrava o dia 1 (o prompt mudou: bloco de memória e `note` nas ferramentas) e grava o dia 2, com a reflexão da primeira noite; `tests/e2e/test_mente.py` ganha o teste (a) e o de reinício (b). Uns US$ 0,04.
- **O CI nunca chama a API** (ADR-0058).

## 7. Ordem do trabalho

1. **ADR-0060 e o plano aprovado;** contratos (os cinco eventos, `memory?` no estado, CHANGELOG, catálogo §3.14); `CLAUDE.md` e `README.md`.
2. **A porta e o adaptador:** `libs/ports/memory.py`, `libs/adapters/memory_sqlite.py`, testes.
3. **A mente lembra:** episódios com importância, `note` nas ferramentas, o bloco de memória na janela, a chave `memory.enabled`; testes com a porta falsa.
4. **A mente reflete:** a ferramenta `reflect`, o gatilho depois do sono e o da manhã, a diferença das crenças, os eventos; testes.
5. **O runner e a configuração:** `minds.<avatar>.memory` e `.reflection` nas settings, o arquivo SQLite por avatar, os eventos publicados pelo runner com o usuário `mind` (`observer.memory.>` no `nats.conf`).
6. **O caderno:** a projeção, o estado `realtime`, o painel do operador.
7. **As fitas e os testes de ponta a ponta:** `make fita DIAS=2`, os testes (a) e (b).
8. **Os 7 dias com memória** no sandbox, e a comparação com os 7 dias do M10.
9. **Fechamento:** §9, diário, `futuro.md` (importância por modelo, relevância por vetores e a `EmbeddingPort`, adaptador Hindsight, serviço de memória com request-reply, origem `told`, reflexão por lote), `make sessoes MARCO=M11`, custos.

## 8. Decisões

1. **`MemoryPort` com registrar, lembrar e refletir,** nos tipos episódio, anotação, crença e reflexão. *Recomendação: sim.*
2. **Adaptador SQLite, um arquivo por avatar e por mundo,** fora do snapshot; sem vetores no M11. *Recomendação: sim.*
3. **A memória mora no processo da mente;** o serviço com request-reply fica para um segundo consumidor. *Recomendação: sim.*
4. **Todo delta vira episódios sem chamada ao modelo,** com importância por tabela. *Recomendação: sim.*
5. **A anotação é o parâmetro `note` de toda ferramenta,** "ou vazio". *Recomendação: sim; a alternativa, uma ferramenta `anotar`, custaria um turno por anotação.*
6. **Toda janela abre com o bloco de memória** (resumo e plano de ontem, crenças, anotações e episódios marcantes de hoje, a última ação), capado em uns mil tokens; `memory.enabled: false` devolve o M10. *Recomendação: sim.*
7. **A reflexão roda uma vez por dia, logo depois de propor dormir,** seja a hora que for, síncrona, com modelo e esforço próprios; sem sono, na primeira entrega da manhã. *Recomendação: sim.* Ressalva do usuário: a reflexão proporcional ao sono (dormir bem reflete melhor) fica para o futuro.
8. **A reflexão é a ferramenta estrita `reflect`,** que devolve resumo, plano e a lista inteira de crenças revisadas; o adaptador calcula a diferença. *Recomendação: sim.*
9. **Crença com `confidence`, `evidence` (ticks do que o agente viu) e `source`** (`observation` agora; `told` na camada social). *Recomendação: sim.*
10. **Cinco eventos `observer` no domínio `memory`** (`noted`, `reflected`, `belief.formed`, `belief.updated`, `belief.retracted`); os episódios não viram evento. *Recomendação: sim.*
11. **O caderno na tela do operador,** projetado dos eventos para o `ObserverState`. *Recomendação: sim.*
12. **Hindsight avaliado e não adotado no M11:** PostgreSQL, chamadas fora da porta, e a linha de base precisa ser nossa; o que vale é a separação ver/acreditar e a confiança com evidência. Um adaptador Hindsight pela `MemoryPort` fica para a v0.5. *Recomendação: sim.*

## 9. Como ficou

Fica para o fim do marco: o que a reflexão escreveu nas noites da fita, as crenças do Camps ao fim dos 7 dias (e se alguma fala do leste), recusas por dia com e sem memória, colheitas e moedas contra o M10, o custo das reflexões.
