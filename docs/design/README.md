# Referências visuais

Telas propostas por ferramentas de desenho (Claude Design e geradores de imagem) antes de construir a interface. Servem de referência de layout, paleta e clima; não são especificação: a UI desenha o que os eventos dizem e nunca decide nada (escopo §9).

## A fazenda (v0.1)

| Tela | Arquivo | Origem |
|---|---|---|
| Operador, manhã: menu de ações no canteiro, recusa `not_adjacent`, linha do tempo | [v0-operador-dia.webp](v0-operador-dia.webp) | Claude Design, 11/out/2026 |
| Operador, noite: avatar dormindo, controles do relógio, métricas do dia | [v0-operador-noite.webp](v0-operador-noite.webp) | Claude Design, 11/out/2026 |
| Operador, manhã, uma segunda proposta: "caderno do Camps", colhidos hoje, terra úmida | [fazenda-operador-image2.webp](fazenda-operador-image2.webp) | Image2 (ChatGPT), 17/out/2026 |

A visão do jogador é a mesma tela, sem o painel da direita. A tela construída nos marcos M4 a M6 ficou próxima da primeira proposta.

### Notas da proposta original (11/out)

Já de acordo com os contratos: o mapa segue a bíblia §4 (casa, canteiros oeste e leste, poço, quiosque, rio); o relógio tem pausar, avançar 1 tick, 1×, 72× e máximo, com a pausa como estado (ADR-0026); a linha do tempo é marcada pela visibilidade (`world`, `agent`, `internal`); as métricas são as da bíblia §13; o regador tem cargas (atributo `charges`) e o menu de ações mostra o motivo da recusa.

A ajustar: (1) `farm.buyer.collected` não existe; a coleta das 22:00 é `world.item.consumed` (motivo `buyer_collect`) e o pagamento das 06:00 é `farm.buyer.paid`; (2) a energia no sono sobe 12,5 por hora na cama (bíblia §7), não 6; (3) a tela da noite mostra ao mesmo tempo o avatar dormindo e "desmaiado às 02:00"; o operador veria um ou outro; (4) "avançar 1 tick" só vale com o relógio pausado (ADR-0026).

### O que a segunda proposta acrescenta (17/out)

- **O "caderno do Camps":** um painel com o que o avatar anotou ("terra escura indica canteiro regado hoje"). Hoje o script não anota nada; na v0.2, com memória (M11), é o lugar natural das crenças do agente, com confiança e origem.
- **"Terra úmida 5/16" e "colhidos hoje"** como contadores do mundo: cabem no catálogo de métricas da ADR-0054.
- O que não bate: os seletores de período, clima e regra oculta na barra de cima. Na tela real, período e clima são estado do mundo, e a regra oculta só aparece na linha do tempo do operador, como evento `internal`.

## O escritório (v0.3, a ideia)

A ideia está em [ideia-escritorio-que-se-constroi.md](../planos/ideia-escritorio-que-se-constroi.md) e a direção, na ADR-0055. Os prompts usados estão em [prompts-escritorio-v0.3.md](prompts-escritorio-v0.3.md): dois estilos (um cubículo dos anos 80 em pixel art 16 bits; um co-work preto e vidro) para quatro ferramentas.

| Tela | Arquivo | Origem | Veredito |
|---|---|---|---|
| **Operador, dia 3, 10:30:** um cubículo, dois lugares demarcados para os próximos, cliente na porta, CI pendente | [escritorio-dia.png](escritorio-dia.png) | Claude Design, 17/out/2026 | **a referência da v0.3** |
| **Operador, dia 3, 23:00:** hora extra, foco 20, custo perto do teto, CI falhando | [escritorio-noite.png](escritorio-noite.png) | Claude Design, 17/out/2026 | **a referência da v0.3** |
| Cubículo, dia, HUD completo em português correto, dois cubículos vazios | [escritorio-retro-image2.webp](escritorio-retro-image2.webp) | Image2 (ChatGPT) | referência de layout |
| Co-work preto e vidro, bancada com um lugar ocupado e cinco vazios, minimapa com legenda | [escritorio-moderno-image2.webp](escritorio-moderno-image2.webp) | Image2 (ChatGPT) | o escritório que cresceu |
| Cubículo isométrico, o visual mais fiel ao Mega Drive, texto do histórico inventado | [escritorio-retro-nano-banana.webp](escritorio-retro-nano-banana.webp) | Nano Banana (Google) | referência de paleta e tipografia do HUD |
| Co-work isométrico, barra de progresso duplicada, kanban sem a coluna "fazendo" | [escritorio-moderno-nano-banana.webp](escritorio-moderno-nano-banana.webp) | Nano Banana (Google) | só clima |
| Ilustração de perto, sem HUD: o melhor Camps (barba, óculos, camisa vermelha, jeans) | [escritorio-retro-midjourney.webp](escritorio-retro-midjourney.webp) | MidJourney | referência de retrato e capa |

### O protótipo navegável (Claude Design, 08/11)

Em [escritorio/](escritorio/): o escritório em página, na mesma linha do estúdio do CampsCast — dois andares em corte em pixel art, o Camps e os robôs (Revisor, Integrador, Pesquisador, Mensageiro e o Vigia do estúdio), os estados pelo relógio de São Paulo, o replay do dia, o painel do operador, as fichas e o "abra um ticket". Tudo é demonstração: a equipe, os modelos e o dia 06/11 foram inventados para desenhar. Os dados vêm de dois JSON no contrato `campsverso.escritorio/1` ([CONTRATO.md](escritorio/CONTRATO.md)); como abrir e o que falta, no [LEIAME.md](escritorio/LEIAME.md).

- **Origem:** o Claude Design entregou os arquivos em 08/11/2026, às 22:31, na pasta do CampsCast (`~/CampsCast/prototipos/escritorio/`), por engano. Movidos para cá em 14/11/2026, sem alteração além do caminho no LEIAME. O projeto no Claude Design não aponta para a pasta local: ela é uma cópia.
- **Fora do lint:** a pasta está nos `ignores` do `eslint.config.js`. É JavaScript de navegador, sem os tipos e as regras do projeto, e o `make check` não deve julgar referência visual.
- **Relação com a v0.4:** é a referência mais completa do escritório até aqui, mas não é especificação. Pela ADR-0077, o cartucho do escritório usa a vista de cima com arte LPC, como a fazenda, e os robôs do protótipo não entram como estão (no Campsverso, robôs são ferramentas e nunca LLM). O corte em dois andares fica como referência do site, o replay de um dia, para depois da v0.4.

### Por que o par do Claude Design é a referência

Vista de cima em 3/4 ortogonal, como a fazenda e a arte LPC (as isométricas não servem de referência de mapa); HUD em grade fixa; o painel do operador completo; todo o texto em português correto; os dois cubículos futuros demarcados em linha tracejada, que contam a história do "vamos colocando mais mesas"; e a noite com o orçamento perto do teto, três CIs vermelhos e "foco 20: avalia encerrar o dia", que é um dia ruim inteiro contado pela linha do tempo. O estilo é pixel art de 16 bits de verdade, com paleta curta.

### O que as referências ensinaram

- **A linha do tempo em linguagem natural** ("abriu o PR #41 (ticket 12)", "vai atender após os testes", "custo perto do limite diário") é muito mais legível que `action.accepted · water plot-e-03`. O rótulo de cada evento pode ser declarado pelo cartucho, como as métricas (tarefa no `futuro.md`).
- **Os pensamentos do agente** ("plano: ticket 12 em 3 passos", "replanejou o ticket 12") aparecem como `interno` nas imagens. No nosso modelo são `agent`: a intenção do controlador é um evento do agente; `internal` é regra oculta. O aviso de orçamento é `ops.*`, do operador.
- **Os lugares demarcados** para os próximos cubículos e as cadeiras vazias na bancada moderna são a forma de mostrar crescimento sem construir nada antes da hora.
- **O minimapa com legenda** (proposta moderna do Image2) será necessário quando o escritório ficar maior que a tela, e serve ao vilarejo.
- **O retrato:** o Camps de óculos do MidJourney é o candidato a retrato do dev no HUD, no lugar do recorte do sprite.
- **A noite** mostra o que o orçamento e as necessidades significam no escritório: a barra de custo em vermelho, energia 25, foco 20, café 5/5.

### Já de acordo com o que existe

- HUD em grade com posições fixas (M6) e a barra de progresso sobre o avatar (M5), com o nome da ação e o percentual.
- A linha do tempo por visibilidade, com três cores.
- Necessidades genéricas do kernel: energia, foco e café são dados do cartucho, como fome e energia na fazenda (ADR-0025).
- As métricas do dia declaradas pelo cartucho (ADR-0054): tickets entregues, PRs mesclados, CI verde, rodadas de revisão, custo de hoje.
- A arte em camadas com manifesto (ADR-0053): o gênero `office` traz os móveis; o cenário traz o Camps programador.
- O kernel já itera vários avatares e aceita um controlador por avatar na configuração do mundo.

### A ajustar ou decidir no plano da v0.3

1. **O relógio a 1× e 6×,** em vez dos 72× da fazenda, e a ação que dura "até" a oficina terminar (decisão 4 da ideia; pede ADR porque toca o princípio 7).
2. **Tickets como itens do mundo** com o atributo `status` (a fazer, fazendo, revisão, publicado); o quadro desenha os itens.
3. **O cliente:** o balão "novo ticket" nasce de um comando (`cmd.office.ticket.create`, por exemplo) e do evento correspondente. O humano pode entrar como avatar ou por um painel de conversa (ver o estúdio, abaixo).
4. **`publicar`** é uma ação validada pelo kernel: recusada com o CI vermelho.
5. **"Hora extra"** é uma regra visível do mundo (depois das 18:00 o foco cai mais rápido), não um aviso da tela.
6. **"CI do PR #41 pendente"** marcado como `interno` nas imagens seria `world`: o CI é um fato externo, não uma regra oculta.
7. **Vários avatares** na percepção, no gateway (posse por avatar) e na tela, antes do segundo agente.

## O escritório depois do M23 (15/11)

O M23 entregou o escritório em arte LPC. Na partida dele, o usuário achou que o LPC "ficou com uma cara estranha": serve para uma primeira versão, mas o alvo é outro. O alvo de agora é a `escritorio-retro-image2.webp`, acima. O alvo maior é a mesma sala crescendo, de um dev ao squad. Estas referências se juntaram às de cima:

| Tela | Arquivo | Origem | O que ensina |
|---|---|---|---|
| O escritório que cresce em três quadros: um dev; o dev e o revisor; o squad, com a mesa de reunião | [escritorio-crescimento.webp](escritorio-crescimento.webp) | não registrada; o mesmo estilo da `escritorio-retro-image2.webp` | o crescimento por peças: cubículos novos no mesmo chão, o quadro com uma coluna a mais |
| O prédio em quatro salas (pesquisa, roteiro, estúdio, arte) e a recepção com o vigia, em vista de cima | [escritorio-quatro-salas-image2.webp](escritorio-quatro-salas-image2.webp) | Image2 (ChatGPT) | a planta com várias salas e um corredor, o vigia na recepção, a luz quente das luminárias; serve ao estúdio do CampsCast |
| O Campsverso Companion: o escritório num aparelho de mesa, com o toque num agente, os detalhes da tarefa, os comandos simples e o PR até a entrega | [companion-replay.webp](companion-replay.webp) | não registrada | uma vertente possível: o replay e o acompanhamento do mundo num aparelho à parte, só com o que o contrato `realtime` já entrega |

**O teste de arte.** O pedido está em [briefing-arte-escritorio.md](briefing-arte-escritorio.md), agora na v2: duas fases, a imagem-alvo só para cores e materiais (a perspectiva dela não cabe na grade), as regras de encaixe (âncora, pegada, camadas), o mapa das folhas e a API de exportação.

### A arte da fase 1 (15/11)

Em [escritorio-arte/](escritorio-arte/): a fatia que basta para decidir entre a arte nova e a LPC, desenhada em código na vista de cima em 3/4, com uma paleta de 45 cores.

- **O que tem:** o chão, as paredes e a porta; a janela de dia e de noite; o relógio; o quadro dos pedidos em módulos e as fichas soltas; o cubículo (a mesa com a tela animada, a cadeira em duas camadas, a divisória em 16 peças, o rack com o botão de publicar); o arquivo, a planta e a lixeira; o Camps, o gerente e o vigia andando e parados, e o Camps sentado e digitando.
- **A planta nova (15/11, à noite):** quatro cubículos em duas fileiras, à esquerda; o quadro dos pedidos à esquerda na parede; a sala de descompressão em cima à direita (o sofá virado para a TV com o videogame, puffs e tapete); a copa embaixo à direita (máquina de café, balcão com pia e micro-ondas, geladeira, bebedouro e duas mesinhas); e o banheiro com teto colado à parede de baixo, com as duas portas no corredor, fora da sala. O rack do servidor e o sofá de lado ficaram para depois. As coordenadas estão no pedido, em "A planta proposta"; elas diferem da bíblia §3 e do `map.tmj` de hoje (ADR-0080), e quem cuida do mapa decide.
- **As animações e a luz (15/11, à noite):** usar, beber, comer sentado, carregar a marmita e sentar no sofá para ver TV ou jogar, para o Camps e o gerente; o relógio com as 12 horas; o arquivo com duas gavetas abertas; a TV com jogo e telejornal; a marmita; o quadro dos pedidos com três colunas, que começa vazio e anda com as fichas; e a luz da noite (as luminárias das 18h às 21h, o escuro depois das 21h com a lanterna do vigia, o corredor sempre aceso), com as tabelas em `metadados.json`. A prévia ficou em cinco cenas, com um GIF cada em [previa/](escritorio-arte/previa/). As folhas só cresceram no fim: as linhas e os quadros que o manifesto usa não mudaram, menos o quadro 0 do relógio, que agora marca 12h.
- **A oficina dos robôs (16/11):** a bancada no cubículo ao lado do dev, no lugar da mesa vaga, com o painel de ferramentas, o multímetro, o osciloscópio e os `apoios` dos robôs no tampo; o robô de mesa de um corpo-base (o testador, o revisor e o publicador), com parado, trabalhando, passou e falhou; e três quadros novos no monitor do dev (lendo, testes verdes, testes vermelhos). Entram duas cores emissivas, `ledVerm` e `ledCiano`: a paleta vai a 47.
- **Os ajustes finos (18/11, o pedido):** em [briefing-arte-baloes.md](briefing-arte-baloes.md), com os recortes de [rotulos-antes.png](rotulos-antes.png): o balão de ação com um ícone por ação, no lugar do texto sobre a cabeça; a etiqueta e o balão de fala em nove fatias; uma fonte pixel com os acentos do português; o corredor mais discreto; e duas plantas novas. Chegou na mesma noite e entrou na tela em 19/11 (o adendo da ADR-0082).
- **Os ajustes finos, a arte (18/11):**
  - **o balão de ação** (24 × 24, âncora (12, 24)), claro, com a ponta no meio, o `miolo` do ícone e o fio do `progresso` na base; sentado à mesa, de costas, ele vai para o lado da cabeça (`naMesa`), para não cobrir o monitor;
  - **25 ícones** de 16 × 16 em `icones.png`: 14 do escritório e 11 da fazenda, sem texto além do "Zz";
  - **a etiqueta escura e o balão de fala** em nove fatias de 8 × 8, com a ponta da fala à parte (`baloes.png`, com as `pecas` e a cor do texto de cada moldura);
  - **uma fonte pixel** de 8 × 12 (`fonte.png`), com 109 glifos e os acentos do português, desenhada no branco da paleta;
  - **o corredor** num granilite escuro, na penumbra à noite com as faces que dão para ele (a porta aberta mostra o piso novo);
  - **duas plantas** na `planta.png`: a espada-de-são-jorge no vaso de cerâmica e a costela-de-adão no cesto de palha.

  A paleta continua com 47 cores. As outras folhas não mudaram um pixel; a coluna 0 da planta e os quadros 0 e 1 da parede de baixo também não. Os balões, a fonte e os ícones ficam acima da luz. A prévia (20 × 16) mostra os balões em todas as cenas, a fala longa no pedido e a etiqueta "Jogando videogame" sobre os dois no sofá; passar o mouse sobre alguém mostra o nome da ação.
- **Como abrir:** [escritorio-arte.html](escritorio-arte/escritorio-arte.html), no navegador, mostra a sala animada, a paleta e a prancha, com um "baixar PNG" por folha. As folhas já exportadas estão em [folhas/](escritorio-arte/folhas/), com o [metadados.json](escritorio-arte/folhas/metadados.json) para o manifesto, e a prévia em [previa/](escritorio-arte/previa/).
- **Exportar de novo:** da raiz, `NODE_PATH=apps/ui/node_modules node docs/design/escritorio-arte/ferramentas/exportar-folhas.js docs/design/escritorio-arte/escritorio-arte.html <pasta>`, com o Playwright do `apps/ui`.
- **Origem:** o Claude desenhou numa sessão do Cowork, em 15/11/2026, e não no Claude Design; o pedido serviu igual. O desenho é original: nada vem da LPC nem de outros pacotes.
- **Fora do lint:** a pasta está nos `ignores` do `eslint.config.js`, como o protótipo.
- **O que falta:** as decisões em aberto do pedido (os agentes humanos ou robôs; a altura da parede do fundo) e o passo 2 em diante: o manifesto de teste e as capturas lado a lado com a LPC.

Uma quarta referência fica fora do repositório: a capa de um vídeo do YouTube sobre jogos de Mega Drive, que não é nossa. Ela mostra o clima de 16 bits que se quer: vista de cima em 3/4, folhagem densa, sombras marcadas e um personagem pequeno num cenário rico.

## O estúdio (depois do escritório)

Duas propostas do Claude Design para o estúdio do podcast, guardadas para quando ele chegar (ADR-0055 o põe depois do escritório, sobre a porta de efeitos externos que o escritório constrói).

| Tela | Arquivo | O que ensina |
|---|---|---|
| Estúdio em 3D isométrico no navegador (câmera que gira), cinco papéis com crachá, cabine "on air", pauta do dia na lousa, "episódio de amanhã 45%", custo e tokens do dia | [estudio-3d-claude-design.webp](estudio-3d-claude-design.webp) | o renderer 3D do `futuro.md` sobre o mesmo contrato `realtime`; o balão de pensamento do jornalista ("confirmar na fonte oficial") é um evento `agent` com a intenção; custo e tokens no HUD são a guarda de orçamento do M9 |
| Painel de produção: lista de agentes com produzir, aguardar e desligar; pipeline noturno; etapas (pesquisa, roteiro, gravação, edição, arte, publicação); onde foi publicado; e um chat com um "diretor de produção" que comanda tudo por mensagem | [estudio-painel-claude-design.webp](estudio-painel-claude-design.webp) | o cliente por chat: o humano fala com o mundo por um painel de conversa que vira comandos, em vez de só andar com um avatar; o estado por agente e as etapas do método visíveis; "publicado em" é a lista de efeitos externos, que no escritório são os PRs e o CI |

Os nomes dos agentes e do diretor nas imagens foram inventados pela ferramenta. O painel não é uma tela de jogo; vale pelo padrão de interação, que serve ao escritório antes do estúdio.
