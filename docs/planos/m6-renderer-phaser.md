# Plano do M6 — Renderer Phaser

**Status:** implementado em 12/out/2026 e jogado pelo usuário (ADR-0052 e ADR-0053). O que mudou está na seção 10.
**Escopo** (escopo §7): mapa Tiled da bíblia, tiles LPC, sprite LPC do Camps, animações de andar, agir e dormir, retrato no HUD.
**Pronto quando:** a mesma partida do M5, agora com visual de jogo.

## 0. Passo zero: ações que não se interrompem (ADR-0052)

Jogando o M5, um segundo "plantar" cancelava o primeiro, como mandava a bíblia §8. Agora cada ação declara a sua política de interrupção:

| Política | Um comando novo durante a ação | Ações da fazenda |
|---|---|---|
| `never` | recusado com `busy` ("ocupado: plantando, faltam 3 min") | plantar, regar, encher, colher, limpar, comer, guardar, pegar, vender, comprar, dormir |
| `cancel` | cancela a atual e começa a nova | andar, esperar (do kernel) |
| `partial` | interrompe, e o cartucho grava o trabalho feito | nenhuma na v0.1 (no futuro, cortar árvore) |

- **Cartucho:** `interrupt` em cada ação do `farm.yaml`. A interface `ActionSpec` troca `cancellable` por `interrupt` e ganha o gancho `interrupted(ctx, ops, elapsed_ticks)`.
- **Kernel:** recusa com `busy` (com a ação e o tick de fim); cancela; ou interrompe e chama o gancho. Uma ação de teste exercita o `partial`.
- **Contratos (campos opcionais):** `action.accepted.interrupt`, `action.failed.elapsed_ticks`, e no estado da tela o início da ação, a política e o sono (início e hora de acordar).
- **Tela:** barra de progresso sobre o Camps em qualquer ação e no sono, e a recusa `busy` legível. Entra no canvas agora e no Phaser depois.
- **Versão:** os cartuchos sobem para 0.2.0. A bíblia §8 e o catálogo de eventos mudam junto.

## 1. O que muda e o que não muda

- **Muda só a área do mapa.** O Phaser lê o mesmo `ObserverState` que o canvas lê hoje.
- **Não mudam:** kernel, eventos, HUD em DOM, painel do operador, menu de ações e botões.
- **O gateway** ganha uma rota para servir a arte, `/content/art/...`, ao lado de `/content/maps/...`.
- **O canvas de depuração continua** em `?render=debug`, com ids e rótulos. O Phaser vira o padrão.

## 2. A arte mora no cartucho, em camadas (decisão 2)

- **Como os dados (ADR-0031):**
  - o que serve a qualquer fazenda fica no gênero, em `cartridges/farm/art/`: terreno, culturas, poço, baú, cama e quiosque;
  - o que é do Camps fica no cenário, em `cartridges/farm_camps/art/`: o personagem e o mapa visual.
- **Um manifesto por camada** (`art.json`) diz como desenhar cada coisa:
  - cada tipo de tile do mapa lógico;
  - cada `kind`, com variações por atributo (o canteiro com `crop: batata` e `stage: broto`);
  - as animações do avatar por ação (`move` → andar; `water` → regar; o resto → agir);
  - o retrato.
- **A tela junta as camadas** na ordem (o cenário cobre o gênero) e não sabe o que é uma fazenda. Um cartucho novo traz a própria arte sem mexer na UI.
- **No futuro:** cartuchos só de arte, genéricos e sem mapa, reaproveitados por vários mundos (`futuro.md`).

## 3. De onde vem a arte (decisão 3)

Tudo em LPC (Liberated Pixel Cup), em 32 px, o mesmo tamanho dos tiles do mapa.

- **O Camps:**
  - quem monta é o usuário, no gerador de personagens LPC, seguindo a aparência da bíblia;
  - exporta um ZIP com uma imagem por animação, os créditos (CSV) e o JSON para refazer depois;
  - animações usadas: andar, parado, regar, agir (`thrust`) e deitado (`hurt`, para dormir e desmaiar).
- **Terreno, construções e culturas:**
  - pacotes LPC do OpenGameArt;
  - antes de cada download, eu digo o arquivo, a origem, o tamanho e a licença, e espero o ok;
  - a planta murcha é a madura escurecida pelo renderer, sem arte nova.
- **Licenças:**
  - o código continua MIT;
  - a arte é CC-BY-SA, GPL ou OGA-BY e exige crédito a cada autor;
  - cada pasta `art/` tem o seu `CREDITS.csv`, e a tela tem um link "Créditos";
  - o "compartilha igual" vale só para a arte.
- **Até a arte chegar,** uma arte provisória gerada (quadrados com cor e rótulo) segue o mesmo manifesto. Assim o motor troca primeiro e a arte entra depois.

## 4. Mapa visual num arquivo à parte (decisão 4)

- **O mapa lógico** (`map.tmj`, 32×18, 9 tipos de tile) continua a verdade do kernel e não muda.
- **O mapa visual** é outro arquivo Tiled, no `art/` do cenário:
  - feito por mim a partir do mapa lógico: bordas do rio e do caminho, terra dos canteiros, chão e paredes da casa sem telhado, árvores e alguma decoração;
  - o kernel nunca o lê;
  - um teste confere que ele tem o tamanho do lógico e que cada tile desenhado combina com o tipo lógico embaixo (água sobre rio, chão sobre passável).
- **Ajustes:** você pede, eu mudo. O editor de mapas continua no futuro.

## 5. Renderer Phaser

- **Phaser 4.2.1** (decisão 1), em modo pixel art, com zoom inteiro que cabe na tela. O mapa inteiro aparece, então não há câmera seguindo o avatar.
- **Camadas:**
  - mapa visual;
  - entidades (canteiros com plantas, baú, cama…);
  - avatar;
  - efeitos (noite, chuva);
  - barra de progresso e balões ("zZ", "!").
- **Andar:**
  - o trajeto continua interpolado pela tela (`motion.ts`), com a direção tirada do segmento atual;
  - o passo da animação acompanha a velocidade na tela, para não patinar a 720×.
- **Agir:** o Camps vira para o alvo e repete a animação da ação até o fim. **Dormir e desmaiar:** deitado, com "zZ" ou com um sinal de desmaio.
- **Clique:** o mesmo do M5 (esquerdo anda, direito abre o menu). O Phaser só converte o ponto da tela em tile.
- **Dia, noite e chuva (decisão 5):** uma camada escura que acompanha a fase do dia, e gotas quando chove. Sem luzes nem sombras.
- **O relógio de exibição** (`DisplayClock`) continua o mesmo: o Phaser desenha no tick mostrado.

## 6. HUD

- **Retrato (decisão 7):** a cabeça do Camps recortada da folha de sprites e ampliada, com um selo de estado (dormindo, cansado, com fome).
- **Troca futura:** o retrato é uma entrada do manifesto, então trocar por um retrato próprio de fazendeiro é trocar um arquivo.

## 7. Testes

| O quê | Como |
|---|---|
| **Interrupção** | unidade no kernel: `never` recusa com `busy`; `cancel` cancela; `partial` chama o gancho com os ticks feitos; o desmaio interrompe todas; e2e: plantar durante um plantio é recusado |
| **Contratos** | exemplos válidos e inválidos dos campos novos; projeção com início da ação e sono |
| **Manifesto** | Vitest: qual quadro desenhar para cada tile, `kind` e atributo; camadas na ordem; fallback para o que o manifesto não conhece |
| **Animação** | Vitest: direção pelo trajeto, animação por ação, fração da barra |
| **Mapa visual** | Python: mesmo tamanho do lógico e tiles coerentes com os tipos |
| **Gateway** | a rota da arte serve as camadas e recusa caminhos fora da pasta |
| **Playwright (decisão 8)** | teste de fumaça `make ui-e2e`: sobe o sandbox, abre as duas visões, assume, anda, planta, vê a barra e guarda prints. Roda no CI (que baixa o Chromium); na máquina local usa o Chrome instalado |
| **Pronto quando** | você joga a partida do M5 com o visual novo; antes, eu faço o mesmo roteiro no navegador embutido do app |

## 8. Ordem do trabalho

1. **Passo zero:** interrupção e barra no canvas (ADR-0052).
2. **Phaser com a arte provisória,** já lendo o manifesto e a rota da arte. O motor troca sem depender da arte.
3. **Arte:** os pacotes LPC (com ok por download), o mapa visual, os manifestos e os créditos. O Camps entra quando o usuário mandar.
4. **Acabamento:** animações, retrato, noite e chuva.
5. **Fechamento:** Playwright no CI, "Como ficou", diário, README e custos.

## 9. Decisões

| # | Decisão | Aprovado |
|---|---|---|
| 1 | Versão do Phaser | **Phaser 4, na 4.2.1** (estável atual). O 4.0 saiu em abril de 2026; a série 3 terminou na 3.90, de maio de 2025 |
| 2 | Onde mora a arte | **No cartucho, em camadas:** gênero com o que serve a qualquer fazenda, cenário com o Camps e o mapa visual. Explorar reuso: no futuro, cartuchos só de arte, sem mapa |
| 3 | De onde vem a arte | **LPC.** O usuário monta o Camps no gerador; os pacotes vêm do OpenGameArt, com ok por download; créditos na pasta e na tela |
| 4 | Mapa | **Mapa visual num arquivo à parte,** feito por mim a partir do lógico, ajustado a pedido. O lógico continua a verdade do kernel. Sem editor por enquanto |
| 5 | Dia, noite e chuva | **Simples:** camada escura pela fase do dia e gotas na chuva |
| 6 | Canvas de depuração | **Continua em `?render=debug`** |
| 7 | Retrato no HUD | **Cabeça recortada do sprite;** depois o usuário troca por um retrato próprio de fazendeiro |
| 8 | Playwright | **Teste de fumaça, principalmente pelo CI.** Localmente usa o Chrome instalado, e no dia a dia eu confiro a tela no navegador embutido do app |

## 10. Como ficou

| Item | Resultado |
|---|---|
| **Interrupção** | plantar durante um plantio é recusado com `busy` ("Camps está ocupado: plantar, faltam 3 min"), conferido no navegador e num teste da fazenda; o `partial` está no kernel, testado com uma ação de laboratório (cavar 4 palmos e continuar de onde parou) |
| **Arte** | só os recortes usados, cerca de 100 KB de imagens: 43 tiles de terreno, 6 objetos, 3 culturas em 5 estágios e o Camps em 13 linhas de animação; `CREDITS.csv` por pasta e os textos de atribuição originais |
| **Mapa visual** | gerado do mapa lógico por `make mapa-visual`; testes conferem que o arquivo está em dia e que cada tile combina com o tipo lógico |
| **Phaser 4.2.1** | mapa em camadas, objetos e culturas por atributo, o Camps andando nas 4 direções, agindo, regando e dormindo na cama; retrato no HUD; noite e chuva; créditos na tela; `?render=debug` com o canvas antigo |
| **Playwright** | `make ui-e2e`, 3 testes em cerca de 12 s na máquina local (Chrome instalado); no CI, com o Chromium do Playwright e as telas como artefato |
| **Pronto quando** | o usuário jogou a partida com o visual novo e pediu quatro ajustes visuais, todos feitos (abaixo) |

**O que mudou em relação ao plano:**

- **O Camps veio do gerador, com outra roupa.** Camisa vermelha, chapéu bordô, calça azul, botas e o regador na mão. A bíblia §2 foi atualizada para o sprite.
- **A política de interrupção vem na validação.** Em vez de um campo fixo na ação, o `Accepted` devolvido pelo cartucho traz `interrupt`, lido do `farm.yaml` já juntado com o cenário. Assim um cenário pode trocar a política.
- **Não há poço LPC nos pacotes.** O poço é uma bomba d'água com bacia.
- **Os canteiros usam a terra arada inteira.** As bordas do pacote têm grama dentro do tile, e as sementes apareciam em cima da grama.
- **Ajustes depois da partida do usuário:**
  - o HUD virou uma grade de lugares fixos, e o aviso de recusa flutua sobre o mapa;
  - a caminhada começa da origem e alcança o kernel até a chegada (o trajeto chega à tela uma fração de tick atrasado, e a 3 tiles por tick isso virava um pulo);
  - dormindo, o Camps aparece na cama, com a cabeça no travesseiro (o sono passou a trazer a cama, `bed_id`);
  - as paredes da casa são uma faixa fina de pedra, com assoalho contínuo.
- **O CI estava verde por engano** desde a noite de 11/out: o `.gitignore` ignorava toda pasta `data/` (os dados dos cartuchos nunca foram publicados), e o `make check | tee` sem `pipefail` escondia a falha. Corrigido com `/data/` no `.gitignore`, os dados no git e `shell: bash` no job, conferido num clone limpo.
- **Sem WebGL, o Phaser usa o Canvas.** No modo AUTO ele abortava quando o WebGL parecia disponível e falhava depois.
