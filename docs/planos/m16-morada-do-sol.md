# Plano do M16 — A Fazenda Morada do Sol

*Proposto em 22/out/2026, depois da ADR-0066. Aprovado em 22/out/2026 (ADR-0067): as treze decisões como recomendado, com quatro notas do usuário (a §8), e a decisão 14, nova, da pergunta dele sobre lembrar do que saiu da vista. É o primeiro marco da v0.3 e o primeiro dos dois marcos de visual (o M17 traz a névoa, a noite e a visão arena).*

**Pronto quando:**
- existe um terceiro mundo, `farm-morada-do-sol-01`, maior que a tela, com a câmera que segue o Camps e deixa olhar o resto;
- os canteiros podem ser cavados em qualquer grama e voltam a ser grama quando ficam vazios;
- o relógio tem um ano acelerado com as quatro estações, e cada cultura tem a sua estação no manual;
- as regras ocultas novas estão na bíblia 3 e são conferidas por teste;
- o fazendeiro-script 2 adaptado vive um ano inteiro em modo máximo;
- a mente joga com o manual novo, e uma fita reproduz sem rede;
- a fazenda 1 e a Boa Vista continuam intactas, com os mesmos números (1.175 e 220 moedas nos soaks).

## O que o levantamento mostrou

Dois levantamentos do código (kernel e tela) em 22/out:

- **A tela desenha o mapa inteiro, sem câmera.** O canvas tem o tamanho do mapa (32 × 18 tiles de 32 px), e o CSS o encolhe para caber. Não há `cameras.main`, nem limites, nem seguir o avatar. O clique converte pixel em tile pelo tamanho do canvas, e o teste do Playwright clica em pixels fixos. A noite é um retângulo escuro do tamanho da tela.
- **O kernel tem um `Calendar`** (o tick, o dia e a hora), mas não tem data do ano nem estação. Os cartuchos só veem `day`, `minute_of_day` e o clima do dia. O `simtime` de cada evento anda junto com o tick, e os scripts e a memória dependem disso: a data acelerada tem de ser um valor à parte.
- **Não existe primitiva de remover entidade.** O `entity.despawned` aparece só como trabalho futuro na ADR-0025 e no catálogo. O caminho de remoção é simples:
  - a percepção já calcula o que sumiu (`gone`) pela diferença entre as vistas;
  - a tela já apaga o sprite de quem deixou de existir;
  - falta o kernel, o contrato e a projeção.
- **O id do canteiro cavado colide quando um canteiro some.** Ele é `plot-{quantos existem + 1}`; depois de uma remoção, o próximo `dig` repetiria um id vivo.
- **O raio da percepção é `null`** (o mapa inteiro em toda foto) e vem só do gênero. Num mapa de 64 × 40 tiles, cada foto levaria uns 1.200 tokens só de terreno. O cenário pode definir o próprio raio.
- **Um cenário que estende `farm` direto** precisa trazer o avatar, o regador e os itens iniciais, como a fazenda 1 faz. Estendendo a Boa Vista, herda tudo isso e as mecânicas dela.
- **O pacote LPC de culturas que já baixamos no M14** tem dezenas de plantas além das sete em uso: milho, melancia, mandioca, couve, alface, abacaxi, café, vagem e outras. Não precisa de download novo.

## 1. O mundo (bíblia 3)

A bíblia da Morada do Sol (`docs/arquitetura/fazenda-morada-do-sol-biblia.md`) traz os números e as regras, como as bíblias 1 e 2. O esboço:

### 1.1 O mapa

São **64 × 40 tiles**, quatro vezes a área da Boa Vista, desenhados no Tiled como os outros:

- **O centro, a oeste:** a casa (cama, mesa, baú, fogão), o poço, a caixa de vendas e o quiosque, ligados por caminhos de terra.
- **O leste:** o rio descendo de norte a sul, com a várzea ao lado: grama larga e plana.
- **O norte:** o morro, uma faixa de árvores com uma trilha que leva a uma lagoa pequena.
- **O sul:** a clareira, grama cercada de bosque, longe da casa.
- **Entre eles:** a grama aberta, onde se pode cavar.

O terreno usa os nove tipos que o tileset já tem (grama, caminho, árvore, rio, parede, porta, terra, piso, entrada). Uma ponte, se o desenho pedir, entra como tipo novo.

### 1.2 Os canteiros

- **Sem teto,** e em qualquer grama. A estrada, o rio, as árvores e o resto não aceitam canteiro. Um teto técnico alto (400) protege o desempenho, sem pesar no jogo.
- **O canteiro vazio volta a ser grama** depois de 3 dias sem planta. Isso é regra visível, no manual. O kernel remove a entidade e publica o fato.
- **O id é sequencial e nunca se repete:** `plot-001`, `plot-002`…

### 1.3 O ano e as estações

- **O ano dura 28 dias simulados, 7 por estação.** Uma corrida da arena passa a ser um ano.
- **O ano começa na primavera, em 22 de setembro.** As estações seguem as datas do hemisfério sul: o verão em 21/dez, o outono em 20/mar e o inverno em 21/jun. Cada dia simulado avança uns 13 dias do calendário, e as contas fecham em exatos 7 dias por estação.
- **O agente sabe a data e a estação.** Elas aparecem no relógio da percepção e no cartão do mundo; não são regra oculta.
- **A afinidade de cada cultura com cada estação** tem três níveis, todos no manual:
  - **boa:** cresce como hoje;
  - **fraca:** cresce na metade do ritmo;
  - **parada:** não cresce, mas também não morre.

  A murcha por falta de água continua como na Boa Vista.
- **O calendário de plantio**, próximo do calendário real do Sudeste, com as sete culturas de hoje e quatro novas do pacote LPC (a proposta):

| Cultura | Primavera | Verão | Outono | Inverno |
|---|---|---|---|---|
| milho (novo) | boa | boa | fraca | parada |
| melancia (nova) | boa | boa | parada | parada |
| mandioca (nova; lenta, dura muito, vale bem) | boa | boa | fraca | fraca |
| abóbora | boa | boa | fraca | parada |
| tomate | boa | fraca | boa | parada |
| batata | fraca | parada | boa | boa |
| cenoura | fraca | parada | boa | boa |
| rabanete | boa | fraca | boa | boa |
| alho | parada | parada | boa | boa |
| morango | fraca | parada | boa | boa |
| couve (nova) | fraca | parada | boa | boa |

O quiosque vende mais as sementes da estação. Preço por estação, demanda e encomendas ficam para a economia, no M18.

### 1.4 As regras ocultas

São verdades do mundo, como decidido na ADR-0066. Elas seguem os quatro critérios do plano macro (frequente, descobrível por experimento, valiosa e sistêmica):

- **R-001, a várzea:** água perto faz crescer mais rápido. É a mesma verdade das fazendas 1 e 2. Aqui a faixa fértil é larga e fica longe da casa, e para chegar lá é preciso andar.
- **R-002, os corvos:**
  - todo amanhecer, um canteiro maduro longe da casa e sem espantalho por perto pode amanhecer comido;
  - o efeito é visível (o canteiro vazio e um evento "comido por um corvo");
  - a distância e o raio do espantalho são ocultos;
  - o espantalho se compra no quiosque e se finca no chão.
- **R-003, a fadiga do solo:** plantar a mesma cultura duas vezes seguidas no mesmo canteiro faz a planta crescer mais devagar, e trocar de cultura recupera o canteiro. Essa regra premia a rotação, e nada no manual fala dela.
- **As verdades da Boa Vista continuam:** o tomate murcha com um dia seco, o alho dispensa rega, o baú conserva, o ensopado sustenta e o adubo vale para o próximo plantio.

### 1.5 A arte

- **As quatro culturas novas** saem do pacote LPC que já temos, com os mesmos cinco estágios.
- **O mapa visual** é gerado do mapa lógico, como hoje (`make mapa-visual`).
- **Cada estação tinge a grama** (um verde mais claro na primavera, o seco do inverno). É barato e muda a tela inteira.
- **Objetos novos:** as árvores do bosque e o espantalho. Se o pacote LPC que já temos não tiver espantalho, eu desenho um no estilo, como o fogão; qualquer download novo passa pelo seu ok, com o nome, a fonte e o tamanho do arquivo.

## 2. O kernel e os contratos

- **A primitiva `despawn`:**
  - `WorldOps.despawn(entity_id, reason)` remove a entidade e publica o evento novo `campsverso.world.entity.despawned.v1` (`entity_id`, `kind`, `reason`, `action_id?`);
  - o kernel recusa remover um avatar, um contêiner com itens ou o alvo de uma ação em andamento;
  - o snapshot e o replay seguem iguais, porque a entidade sai do mapa de entidades;
  - na projeção da tela, `world-view` ganha o tratamento do evento novo.
- **O calendário:**
  - o cartucho declara o ano como dado, junto do relógio: os dias simulados do ano, a data de início e as estações com o dia em que começam;
  - o `Calendar` do kernel calcula a data e a estação de cada dia, sem tocar no `simtime`;
  - os cartuchos as leem pelo `WorldView` (`season(day)`, `date(day)`);
  - o kernel publica `campsverso.world.clock.season_changed.v1` na troca de estação;
  - campos opcionais novos: `date` e `season` no relógio da percepção (`seen_clock`), no `phase_changed` e no estado da tela.

  É física genérica, como o clima: o escritório da v0.4 pode ter um ano fiscal com trimestres.
- **O raio da percepção por cenário:** a Morada do Sol declara o próprio raio. A névoa na tela fica para o M17.
- **O CHANGELOG** dos contratos ganha a seção do M16, e o `make compat` confere que tudo é compatível.

## 3. O gênero `farm` e o cenário

- **O gênero:**
  - a afinidade cultura × estação entra no crescimento diário (o multiplicador do nível);
  - o canteiro vazio volta a ser grama por um sistema novo, ligado por dados;
  - as regras R-002 e R-003 entram como sistemas e regras do cenário, só com as primitivas;
  - o `dig` passa a usar um contador para o id, e o teto vem dos dados (400 na Morada do Sol, 32 na Boa Vista, que não muda).
- **O cenário `farm_morada_do_sol`:**
  - o mapa, o `morada.yaml` (culturas, estações, afinidades, espantalho, corvos, fadiga), as regras ocultas, o mundo `config/worlds/farm-morada-do-sol-01.yaml` e a arte;
  - ele estende a Boa Vista (decisão 1).
- **O fazendeiro-script 2 adaptado:**
  - planta só a cultura da estação;
  - cava perto do poço e repõe os canteiros que voltaram a ser grama;
  - não conhece nenhuma regra oculta;
  - é a linha de base do ano até o script 3 chegar, no M19.

## 4. A tela

- **A câmera da Phaser:**
  - segue o Camps dentro dos limites do mapa;
  - arrastar com o mouse olha o resto, e um botão volta a seguir o Camps;
  - na visão do operador, um botão mostra o mapa inteiro (o zoom que cabe na tela);
  - o clique passa a converter pela câmera (`getWorldPoint`);
  - a noite e a chuva ficam presas à tela (`setScrollFactor(0)`).
- **O canvas de depuração** rola dentro de uma caixa com barras de rolagem, sem câmera.
- **O HUD** mostra a data e a estação ("Dia 5 · 08:24 · 15 de nov · primavera").
- **O teste do Playwright:**
  - deixa de clicar em pixel fixo e usa um ajudante que converte tile em ponto da tela;
  - roda nos três mundos (`MUNDO=farm-morada-do-sol-01`).

## 5. A mente

- **O manual da Morada do Sol:**
  - o calendário de plantio, o ano e as estações;
  - cavar em qualquer grama, e o canteiro vazio que volta a ser grama;
  - o espantalho "que protege a lavoura", sem dizer de quê nem até onde.
- **O catálogo** ganha a ação de fincar o espantalho.
- **O teste de palavras proibidas** cobre as regras novas: várzea, corvo, distância, rotação, fadiga e as variantes.
- **Uma fita de dois dias da Morada do Sol** (`make fita CARTUCHO=farm_morada_do_sol`) custa uns US$ 0,05.

## 6. Testes do marco

- **Kernel:**
  - o `despawn` com as recusas, no snapshot e no replay;
  - o calendário: as fronteiras das estações em 28 dias, a data, e o determinismo pela seed.
- **Gênero e cenário:**
  - a afinidade nos três níveis;
  - o canteiro que volta a ser grama no terceiro dia;
  - o id que não se repete;
  - os corvos com e sem espantalho, pelo RNG nomeado;
  - a fadiga e a rotação.
- **E2E:**
  - um soak de 28 dias na Morada do Sol;
  - determinismo e replay nos três mundos;
  - os soaks das fazendas 1 e 2 com os números de sempre.
- **Tela:** a câmera e a conversão do clique (Vitest), e o Playwright nos três mundos.
- **Antes de tudo, o teste A6 da percepção,** que falhou uma vez sob carga em 22/out (no `futuro.md`). Ele é investigado antes de mexer na percepção.

## 7. Ordem do trabalho

1. O teste A6 intermitente.
2. O kernel e os contratos: o `despawn` e o calendário.
3. O mapa da Morada do Sol e a bíblia 3.
4. O gênero e o cenário:
   - as estações e as afinidades;
   - o canteiro que volta a ser grama;
   - as regras ocultas;
   - o script 2 adaptado;
   - o soak.
5. A tela: a câmera, o HUD com a data, a grama por estação, a arte nova e o Playwright.
6. A mente: o manual, o catálogo e a fita.
7. O fechamento: a §9 deste plano, o diário, os custos e um print.

**Estimativa:** duas a três sessões, como o M13. **Custo de API:** uns US$ 0,05 da fita.

## 8. Decisões

1. **O cartucho `farm_morada_do_sol`,** com o mundo `farm-morada-do-sol-01`, **estendendo a Boa Vista** e não o gênero direto. Ele herda o Camps, as ferramentas, o fogão, o baú, o mercado e a arte, e só acrescenta ou troca o que é dele. A Boa Vista não muda: quem estende só lê. Isso ajusta a letra da ADR-0066 ("estende `farm`"), mantendo a intenção. *Recomendação: sim.*
2. **O mapa de 64 × 40 tiles,** com as regiões da §1.1. *Recomendação: sim. É grande o bastante para explorar e pequeno para o soak continuar em segundos.*
3. **O raio da percepção da Morada do Sol já no M16:** script e LLM veem 12 tiles em volta. A névoa na tela vem no M17. *Recomendação: sim. Sem raio, cada foto leva o mapa inteiro, e o M17 só desenha o que o raio já faz.*
4. **A câmera:** segue o Camps, arrastar olha o resto, e o operador tem o "mapa inteiro". *Recomendação: sim. As setas do teclado ficam para os menus do humano, no M17.*
5. **A primitiva `despawn`** e o evento `world.entity.despawned.v1`, com as recusas da §2. *Recomendação: sim. O escritório vai precisar dela, como pediu a ADR-0064.*
6. **Os canteiros sem teto,** só na grama, voltando a ser grama depois de 3 dias vazios, com o id sequencial e um teto técnico de 400. *Recomendação: sim.*
7. **O calendário no kernel,** declarado pelo cartucho, com a data e a estação em campos opcionais e o evento `season_changed`. *Recomendação: sim. É física genérica, como o clima. A alternativa, só no cartucho, esconderia a data da percepção e da tela, ou a mandaria por um evento da fazenda.*
8. **O ano de 28 dias simulados,** 7 por estação, começando na primavera (22/set). A corrida da arena vira um ano. *Recomendação: sim. A alternativa de 40 dias encarece a arena em um terço.*
9. **A afinidade em três níveis** (boa, fraca, parada), visível no manual. Fora da estação a planta desacelera ou para, mas não morre. *Recomendação: sim.*
10. **As quatro culturas novas** (milho, melancia, mandioca e couve), do pacote LPC que já temos, e o calendário da §1.3. *Recomendação: sim. A mandioca é a cultura lenta e valiosa do ano; a couve, a do inverno.*
11. **As regras ocultas R-001 (a várzea), R-002 (os corvos e o espantalho) e R-003 (a fadiga do solo),** com as verdades da Boa Vista mantidas. *Recomendação: sim. A R-002 pune quem planta longe sem pensar; a R-003 premia quem experimenta.*
12. **A grama tingida por estação e o espantalho desenhado no estilo LPC,** se o pacote não tiver um. *Recomendação: sim. Downloads novos só com o seu ok.*
13. **O fazendeiro-script 2 adaptado** como a linha de base do ano até o script 3. *Recomendação: sim.*

- **14. A lembrança do que se viu** *(nova, da pergunta do usuário na aprovação).* Com o raio de 12 tiles, o LLM precisa lembrar do canteiro que plantou lá embaixo, como um humano lembra. Hoje ele só tem a conversa recente, as próprias anotações e as crenças; e o delta da percepção chama de `gone` tanto o que foi removido quanto o que só saiu da vista. A proposta tem três partes:
  - **na percepção,** o delta separa `out_of_view` (saiu do raio e continua existindo) de `gone` (foi removido), num campo opcional;
  - **na `MemoryPort`,** a mente guarda o último estado visto de cada entidade (posição, atributos visíveis, quando viu), no mesmo SQLite do caderno;
  - **no bloco de abertura de cada janela,** entra uma lista curta: "fora de vista, pelo que você lembra: plot-007 em (40,30), rabanete em broto, visto no dia 3 às 06:10".

  É memória do que o avatar viu, nunca do mundo, então não vaza regra oculta. É também a primeira peça do caderno de campo do M19. *Recomendação: sim.*

- **15. Os marcos** *(nova, durante a implementação, a confirmar).*
  - **O problema:** com o raio de 12 tiles, o fazendeiro-script nunca encontrou o quiosque, que fica a 25 tiles da casa e longe do caminho dele. O soak do ano mostrou isso: sem comprar sementes, ele plantou 10 vezes no ano. O LLM teria o mesmo problema.
  - **A proposta:** o cenário declara como marcos as construções fixas (cama, porta, baú, fogão, poço, caixa de vendas e quiosque), que todo avatar enxerga além do raio, como quem conhece a própria fazenda. Os canteiros e o resto continuam limitados ao raio e à lembrança.
  - **Como entra:** um campo opcional na configuração da percepção (`landmarks`).
  - **O resultado no soak:** o script 2 adaptado fecha o ano com 74 plantios, 66 colheitas e nenhum desmaio.
  - *Recomendação: sim. Se o usuário preferir que o avatar descubra o quiosque andando, os marcos saem dos dados e o script ganha um passeio de reconhecimento.*

**As notas do usuário na aprovação (22/out):**
- **1:** as fazendas anteriores ficam guardadas como estão.
- **2:** o tamanho do mapa se ajusta depois de jogar.
- **5:** o `despawn` fica no kernel e no `cartridge-api`, não no cartucho, para o escritório não precisar herdar da fazenda.
- **7:** o mecanismo do calendário é genérico, no kernel, mas só a Morada do Sol declara um ano; as fazendas 1 e 2 ficam sem estações. Um mundo que quiser estações declara o seu sem herdar a fazenda.
- **8:** a 72×, um dia simulado leva 20 minutos e o ano, umas 9 horas e 20 minutos de jogo.
- **11:** a saturação do preço não é regra oculta; é a economia. Vender muito baixar o preço já vale desde a Boa Vista, e comprar muito subir o preço vem no M18.
- **12:** o download de arte está autorizado se precisar.
- **13:** o script 2 adaptado fica mais sofisticado, com regras condicionais (comprar pela conta da estação, cozinhar com fome e ingredientes, espalhar as vendas para não saturar, guardar o que dura), sem nenhuma regra oculta.

## 9. Como ficou

*(a preencher no fechamento)*
