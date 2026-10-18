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

## O estúdio (depois do escritório)

Duas propostas do Claude Design para o estúdio do podcast, guardadas para quando ele chegar (ADR-0055 o põe depois do escritório, sobre a porta de efeitos externos que o escritório constrói).

| Tela | Arquivo | O que ensina |
|---|---|---|
| Estúdio em 3D isométrico no navegador (câmera que gira), cinco papéis com crachá, cabine "on air", pauta do dia na lousa, "episódio de amanhã 45%", custo e tokens do dia | [estudio-3d-claude-design.webp](estudio-3d-claude-design.webp) | o renderer 3D do `futuro.md` sobre o mesmo contrato `realtime`; o balão de pensamento do jornalista ("confirmar na fonte oficial") é um evento `agent` com a intenção; custo e tokens no HUD são a guarda de orçamento do M9 |
| Painel de produção: lista de agentes com produzir, aguardar e desligar; pipeline noturno; etapas (pesquisa, roteiro, gravação, edição, arte, publicação); onde foi publicado; e um chat com um "diretor de produção" que comanda tudo por mensagem | [estudio-painel-claude-design.webp](estudio-painel-claude-design.webp) | o cliente por chat: o humano fala com o mundo por um painel de conversa que vira comandos, em vez de só andar com um avatar; o estado por agente e as etapas do método visíveis; "publicado em" é a lista de efeitos externos, que no escritório são os PRs e o CI |

Os nomes dos agentes e do diretor nas imagens foram inventados pela ferramenta. O painel não é uma tela de jogo; vale pelo padrão de interação, que serve ao escritório antes do estúdio.
