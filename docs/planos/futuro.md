# Tarefas futuras

Ideias e pendências que ainda não têm marco. Cada uma vira plano, ou ADR, quando chegar a hora. As mais novas ficam no fim.

| Tarefa | Origem | Quando decidir |
|---|---|---|
| **Enxergar o mapa.** O script e o LLM recebem os tiles num raio N, declarado pelo cartucho, como já recebe quem joga na tela | ADR-0047 | antes do LLM (v0.2) |
| **Salto de tempo no modo máximo.** Hoje ele anda tick a tick; o salto exigiria entrar no diário de entradas | ADR-0047 | se algum soak ficar lento |
| **A necessidade "sono".** Pressão de sono que sobe acordado e só baixa dormindo. Uma noite que acabou tarde deixa o avatar com sono no dia seguinte | ADR-0041, ADR-0049 | quando houver quem vire a noite (LLM ou humano) |
| **Andar gasta energia?** Talvez sim, para abrir espaço para correr | revisão do M3 (12/out) | depois do M5, jogando |
| **Correr.** Movimento mais rápido que gasta mais energia que andar | revisão do M3 (12/out) | depois de decidir o custo de andar |
| **Formato de mapa próprio e editor.** Um arquivo JSON ou binário com todos os detalhes do mapa (terreno, camadas, objetos, propriedades), feito num editor externo que seja parte do Campsverso. Até lá, vale o Tiled (`.tmj`) | ADR-0050 | antes de um segundo cenário, ou do vilarejo |
| **Renderer 3D** (three.js ou análogo), sobre o mesmo contrato `realtime` do canvas e do Phaser | ADR-0050 | depois do M6 |
| **Visitantes com login.** Separar as visões jogador e operador por credencial, e não só por conexão | ADR-0022, ADR-0050 | antes de abrir para fora de `127.0.0.1` |
| **Playwright.** Testes automáticos da tela num navegador de verdade | ADR-0050 | no M6 |
| **Ações padrão do mundo.** Ações que todo mundo tem (andar, esperar, talvez dormir), declaradas pelo kernel. Hoje, cada cartucho declara o próprio catálogo | ADR-0051 | quando houver um segundo cartucho |
| **Teclado e arrastar.** Atalhos de teclado para as ações e arrastar no mapa. No M5, só o mouse, com os cliques esquerdo e direito | ADR-0051 | depois do M6 |
| **Fila de ações.** Clicar em três canteiros e o avatar fazer um depois do outro, em vez de recusar com `busy` enquanto trabalha. Põe estado novo no kernel (a fila de cada avatar) | ajuste depois do M5 (12/out) | depois do M6, jogando |
| **Despertador.** Acordar numa hora marcada. O sono continua não cancelável pelo controlador; o despertador seria uma regra do mundo que encerra o sono, como a de acordar às 06:00 | ajuste depois do M5 (12/out) | junto com a necessidade "sono" |
| **Cartuchos só de arte.** Pacotes genéricos de arte (terreno, construções, personagens), sem mapa, reaproveitados por vários mundos: a fazenda, o vilarejo, o estúdio. No M6, a arte fica em camadas no gênero e no cenário | ADR-0053 | antes de um segundo gênero |
| **Conferir o `make sessoes` de M2 e M3.** Os números de tempo e tokens desses marcos parecem baixos; parte das conversas pode estar em arquivos que não foram associados ao marco | fechamento da v0.1 (12/out) | antes de publicar os custos |
| **Porta de efeitos externos (a "oficina").** Uma ação longa executada fora do kernel (um agente de código numa worktree isolada), com os resultados voltando como eventos e gravados para reprodução nos testes | ideia do escritório (14/out), ADR-0055 | no plano macro da v0.3 |
| **Vários avatares fora do kernel.** O kernel já itera N avatares e aceita um controlador por avatar; a percepção, o gateway (posse por avatar) e a tela assumem um só | ADR-0055 | antes do segundo agente do escritório |
| **Supervisor de versões.** Quem reinicia a pilha numa versão nova publicada pelo próprio mundo, migrando o snapshot e preservando a memória dos agentes | ADR-0055 | na v0.3 |
| **Duração "até" um evento externo.** Uma ação que dura até a oficina terminar, com o relógio do mundo seguindo normal numa escala baixa; a alternativa é o relógio ancorado ao real | ADR-0055 | na v0.3; pede ADR, porque toca o princípio 7 |
| **Rótulos de eventos pelo cartucho.** A linha do tempo em linguagem natural ("abriu o PR #41"), com o rótulo de cada evento declarado como dado, como as métricas | referências visuais (17/out) | quando a linha do tempo ficar ilegível; o escritório vai precisar |
| **O cliente por chat.** O humano falar com o mundo por um painel de conversa que vira comandos, em vez de só andar com um avatar | referências do estúdio (17/out) | no plano macro da v0.3 |
| **O caderno do avatar.** Um painel com o que o agente anotou e acredita, a partir da memória | segunda proposta da fazenda (17/out) | no M11 |
| **Raio de percepção menor que o mapa, para todos os atores.** Quem joga vê só o raio e o resto fica ofuscado (névoa); script e LLM recebem a foto recortada e precisam se mover para ver. O raio já é dado do cartucho desde o M8, mas vale a propriedade inteira | plano do M8 (17/out) | quando houver um mundo maior que a tela, ou um experimento de exploração |
| **Mapas grandes.** O terreno viaja no `session.started` (1 byte por tile; o NATS aceita 1 MB) e se repete na foto dentro do raio. Até uns 100 × 100 tiles o desenho do M8 serve; acima, o mapa sai da foto (publicado uma vez, guardado pelo controlador) e o raio vira obrigatório | plano do M8 (17/out) | antes de um mundo maior que 100 × 100 |
| **Tick mais curto por mundo.** O kernel já tem `tick_seconds`, mas o cartucho declara durações em ticks (minutos). Se as durações passarem a ser em minutos, convertidas pelo kernel como as taxas das necessidades, um mundo em tempo real (escritório, estúdio) pode rodar com ticks de 10 s e responder a comandos em segundos, sem mudar as regras | revisão do relógio a 1× (17/out) | no plano macro da v0.3 |
