# Plano do M8 — Mundo pronto para o LLM

**Status:** aprovado em 17/out/2026, com ajustes (ADR-0056). Primeiro marco da v0.2 (`v0.2-macro.md`). Nenhum LLM entra aqui: o M8 prepara o mundo e a percepção para o controlador que chega no M10, e mede quanto a percepção custaria em tokens.

**Pronto quando:** o fazendeiro-script continua sobrevivendo 30 dias com as regras novas (com e sem a regra oculta), e a foto e o delta da percepção têm o tamanho medido em bytes e tokens estimados por dia, por um comando que qualquer um roda sobre um arquivo de eventos.

## O que o levantamento mostrou

- **A foto de hoje:** 4,5 KB por decisão no mundo oficial (25 entidades; a lista de entidades é 3,6 KB dos 4,5). O script decide de 82 a 115 vezes por dia simulado. Se um LLM recebesse a mesma foto a cada decisão, seriam uns 100 a 170 mil tokens por dia só de percepção, antes do prompt e das ferramentas. O delta é o que torna o M10 pagável.
- **A foto não traz o mapa.** O `session.started` publica só `map: {id, width, height}`; o script se vira com `move {near}` (ADR-0047). O kernel conhece o terreno (`tiles_with("water")` é o que a R-001 usa), então pode publicá-lo.
- **O mapa da fazenda tem 32 × 18 = 576 tiles.** Como linhas de códigos ("GGGGWW…") mais uma legenda, cabe em uns 250 tokens.
- **Acrescentar `delta` ao enum `kind` é incompatível** pelas nossas próprias regras (`make compat`: os modelos gerados usam `Literal`). O delta precisa de um tipo próprio.
- **Taxas negativas funcionam:** a escala é 120 unidades por ponto e o tick é 1 minuto, então "−1 por hora acordado" vira −2 unidades por tick, inteiro. É só dado no `farm.yaml`.
- **Regra de hora em hora sem mexer no kernel:** o gatilho `DailyAt` aceita uma lista de horários; um sistema do gênero com as 24 horas cheias roda de hora em hora, determinístico.
- **Python 3.15.0** está instalado na máquina e o `datamodel-code-generator` 0.85 roda nele. Das dependências compiladas, só o PyYAML 6.0.3 ainda não tem wheel para o 3.15 (compila do fonte). O gatilho da ADR-0034 ("todas com suporte oficial") ainda não fechou.

## 1. Enxergar o mapa (decisões 1 e 2)

- **O kernel publica o terreno no `session.started`**, em campos opcionais do `map`: `rows` (uma string por linha, um caractere por tile) e `legend` (código → nome do tile e propriedades do tileset: `passable`, `water`…). Vem do mesmo lugar de onde a R-001 lê a água. Compatível: só campos novos no v1.
- **O cartucho declara o raio de percepção** (`perception: {radius: null}` no `farm.yaml`; `null` é a propriedade inteira, como hoje), publicado no `session.started` junto das afordâncias e das métricas. A percepção filtra entidades e tiles pela distância de Chebyshev até o avatar; com `null`, não filtra.
- **A foto ganha `view.map`** (as mesmas `rows` e `legend`, recortadas ao raio), opcional. O delta nunca traz o mapa: ele não muda.
- O script não muda: continua com `move {near}`. Quem ganha é o LLM, que passa a saber onde pode pisar e onde está a água, como quem joga na tela.
- **O raio vale para todos os atores** (humano, script e LLM). Na v0.2 ele é a propriedade inteira; um raio menor que o mapa (o resto da tela ofuscado para quem joga, a foto recortada para script e LLM) fica no `futuro.md`.
- **Até onde o mapa pode crescer.** O terreno viaja uma vez, no `session.started`: um byte por tile, então 100 × 100 são 10 KB e 1.000 × 1.000 chegam ao limite de 1 MB de uma mensagem do NATS. O que pesa é a foto, que repete o mapa dentro do raio: 32 × 18 custam uns 250 tokens por foto; 100 × 100, uns 3.000, ainda aceitável com uma foto a cada 20 deltas; 300 × 300 passam de 25.000 por foto e exigem raio menor que o mapa ou o mapa fora da foto (publicado uma vez e guardado pelo controlador). Regra prática: até uns 100 × 100 tiles o desenho de agora serve; acima disso, o raio deixa de ser opcional. Nenhum mundo previsto (fazenda, escritório, estúdio, vilarejo) passa disso.

## 2. Percepção por deltas (decisões 3, 4 e 5)

- **Um tipo novo, `campsverso.perception.updated.v1`**, em vez de `kind: delta` no `delivered.v1` (ADR-0028 deixou a escolha para cá; o `make compat` decidiu). Os dois respondem a um `avatar.decision_requested`, com o mesmo `decision` dentro.
- **O que o delta leva:** `since_tick` (o tick da foto ou do delta anterior), `as_of_tick`, `self` inteiro (é pequeno e é o que mais muda), `clock`, `weather` só se mudou, `containers` que mudaram, `entities` que mudaram (o registro inteiro de cada uma, não a diferença campo a campo), `gone` (ids que sumiram) e `events`: o que aconteceu desde a última entrega, como lista de `{tick, type, data}` dos eventos `world` e `agent` que a percepção aplicou, sem os próprios eventos de percepção. É o "o que aconteceu enquanto eu fazia outra coisa" que alimenta a memória do M11.
- **A política, por tipo de controlador,** configurada na percepção (`config/env/local.yaml`): `script` e `replay` recebem sempre a foto (a linha de base e o replay das sessões da v0.1 não mudam); `llm` recebe a foto na primeira decisão da sessão, ao assumir a posse (`possessed`) e a cada N deltas (proposta: 20), e deltas no resto. `human` não muda (a tela usa o gateway).
- **Estado:** a percepção guarda, por avatar, a última visão entregue e o tick dela, no mesmo arquivo da projeção (ADR-0047). Depois de uma queda, a primeira entrega é uma foto.
- **Como testar sem LLM:** o testkit (ADR-0040) ganha um controlador de teste do tipo `llm` que só grava o que recebe. Os testes conferem foto, deltas, a foto a cada N, a foto depois de uma troca de posse e a reconstrução: aplicar os deltas sobre a foto dá a foto seguinte.

## 3. Fome em 100 e ficar acordado (decisões 6 e 7)

- **Ficar acordado custa 1 de energia por hora** (`energia.rates_per_hour.awake: -1`). Só dado; 16 horas acordado dão −16, que a cama repõe com folga. Parado o dia inteiro deixa de ser de graça, como pede o `futuro.md`. O usuário acha pouco: o número fica no gênero (`farm.yaml`) e o cenário pode sobrescrever (ADR-0031), para calibrar nos testes com o script.
- **Passar fome drena energia:** com a fome em 100, um sistema do gênero (`starving`, de hora em hora, pelo `DailyAt` com as 24 horas) tira 4 de energia por hora acordado, até comer. Soma-se ao dobro de energia por ação acima de 80, que já existe. Um dia inteiro passando fome termina em desmaio; a fome não mata (ninguém morre na v0.2). Números no `farm.yaml`: `starving_at: 100`, `starving_energy_per_hour: 4`, com o mesmo override pelo cenário. Equilíbrio é dado do cartucho, nunca do kernel nem do arquivo do mundo (`config/worlds/`), que só guarda seed, data, relógio e controladores.
  - A alternativa seria desmaiar na hora em que a fome chega a 100 (`OnThreshold` e `ops.faint`, nada novo). É mais dramático e menos pedagógico: o LLM aprende mais com "estou perdendo energia porque estou com fome" do que com um apagão.
- **Fica no futuro:** a necessidade "sono" (ADR-0041), correr e andar gastando energia. A bíblia §7 ganha as duas linhas novas.
- **O script continua sem mudar:** ele come a partir de 70 quando tem comida. Sem a regra oculta, o pico de fome dele nos soaks era 100; com a drenagem, ele pode desmaiar algumas vezes em 30 dias, e é isso que os soaks vão mostrar.

## 4. O orçamento de tokens (decisão 8)

- **`make percepcao ARCHIVE=pasta`:** lê um arquivo de eventos e imprime, por dia, quantas fotos e deltas saíram, os bytes de cada um e os tokens estimados (bytes ÷ 3,5, a conta de ordem de grandeza para JSON), para duas políticas: só fotos, e fotos a cada 20 deltas. O mesmo código entra nos testes.
- **A contagem de verdade** chega com a `ModelPort` no M9 (a API de contar tokens do provedor); aqui fica a estimativa, documentada como tal.
- **Números a registrar no diário:** o mundo oficial (12 dias, fotos só) e um soak de 30 dias com o controlador de teste `llm`.

## 5. Python 3.15 (decisão 9)

Ficar no **3.14**. O PyYAML ainda não tem wheel para o 3.15, que é exatamente o gatilho que a ADR-0034 fixou. Revisitar no M13 (fechamento da v0.2), ou antes, se o wheel sair. O `datamodel-code-generator` 0.85 já roda no 3.15, então o outro contorno sumiu.

## 6. Ordem do trabalho

1. **Contratos:** `session.started.map.rows/legend` e `session.started.perception`, `delivered.view.map`, o tipo `perception.updated.v1`; exemplos válidos e inválidos; CHANGELOG; catálogo §3.7; `make contracts` e `make compat`.
2. **Kernel:** publicar o terreno e o raio no `session.started`; teste.
3. **Projeção comum e percepção:** guardar o mapa; `view(avatar, radius)`; a visão entregue por avatar; o diff e a lista de eventos; a política por tipo de controlador; o controlador de teste `llm` no testkit; testes.
4. **Gênero farm:** `awake: -1`, o sistema `starving` e os dados; testes; bíblia §7.
5. **`make percepcao`** e os números do mundo oficial.
6. **Soaks de 30 dias** com e sem a regra, comparados com os do M7 (1.175 e 750 moedas; pico de fome 79,1 e 100).
7. **Fechamento:** ADR-0056 com as decisões, diário, `futuro.md`, `make sessoes MARCO=M8`, custos.

## 7. Decisões (aprovadas em 17/out, com os ajustes em itálico)

1. **O kernel publica o terreno** (`rows` + `legend`) no `session.started`, campos opcionais. *Sim, com o limite de tamanho mapeado acima: até uns 100 × 100 tiles sem mudar nada.*
2. **O raio de percepção é dado do cartucho** (`null` = tudo) e a foto ganha `view.map` recortado. *Sim; vale para todos os atores; raio menor que o mapa vai para o `futuro.md`, sem implementar agora.*
3. **O delta é um tipo novo, `perception.updated.v1`.** *Recomendação: sim, pelo `make compat`.*
4. **O delta leva `self` inteiro, as entidades que mudaram inteiras, `gone` e `events`.** *Recomendação: sim; registro inteiro é mais simples de aplicar do que diferença campo a campo.*
5. **Política por tipo de controlador:** script e replay só fotos; llm foto na primeira, na posse e a cada 20 deltas. *Sim, com o 20 configurável, para medir o desempenho depois.*
6. **Acordado custa 1 de energia por hora.** *Sim, configurável no cartucho; o valor é um ponto de partida.*
7. **Fome em 100 drena 4 de energia por hora, sem morte.** *Sim, configurável no cartucho (gênero, com override do cenário), não no mundo.*
8. **Tokens estimados por bytes ÷ 3,5, com `make percepcao`;** a contagem real fica para o M9. *Sim.* Em outras palavras: queremos saber quanto a percepção custaria por dia antes de ligar um modelo; o número exato depende do tokenizador do provedor, que só o M9 consulta; até lá, uma estimativa por tamanho de texto basta para comparar as políticas e dimensionar o orçamento, e o M9 calibra o fator.
9. **Python 3.14 continua;** revisitar no M13. *Sim.*
