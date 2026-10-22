# Tarefas futuras

Ideias e pendências que ainda não têm marco. Cada uma vira plano, ou ADR, quando chegar a hora. As mais novas ficam no fim.

**Revisto no fechamento da v0.2 (M15, 21/out/2026).** Saíram os itens que a v0.2 fez:
- enxergar o mapa (M8);
- andar gasta energia (M13, na Boa Vista);
- o Playwright (M6);
- o caderno do avatar (M11);
- Sonnet e Opus numa fazenda mais rica (M13 e M14);
- a reserva da corrida (M14);
- a ordem das versões (ADR-0064).

Saiu também a conferência do `make sessoes` de M2 e M3. A causa provável é a mesma do M10+M11: compactar a sessão reescreve a transcrição e apaga as chamadas antigas. Desde o commit e14e230 um turno gravado não encolhe, mas o que se perdeu antes não volta, e a ressalva fica no diário.

A coluna "Destino" segue a lista do plano macro da v0.3 (`v0.3-macro.md` §1). Ela ainda passa pelas decisões no começo da v0.3. "Fazenda 4" é o que fica para depois da v0.3.

| Tarefa | Origem | Destino |
|---|---|---|
| **Salto de tempo no modo máximo.** Hoje ele anda tick a tick; o salto exigiria entrar no diário de entradas | ADR-0047 | se algum soak ficar lento (30 dias levam uns 33 s nos dois mundos) |
| **A necessidade "sono".** Pressão de sono que sobe acordado e só baixa dormindo. Uma noite que acabou tarde deixa o avatar com sono no dia seguinte | ADR-0041, ADR-0049 | decisão 9 da v0.3 (recomendação: fazenda 4) |
| **Correr.** Movimento mais rápido que gasta mais energia que andar (andar já gasta na Boa Vista) | revisão do M3 (12/out) | fazenda 4 |
| **Formato de mapa próprio e editor.** Um arquivo JSON ou binário com todos os detalhes do mapa (terreno, camadas, objetos, propriedades), feito num editor externo que seja parte do Campsverso. Até lá, vale o Tiled (`.tmj`), que serviu à Boa Vista | ADR-0050 | depois da v0.3 |
| **Renderer 3D** (three.js ou análogo), sobre o mesmo contrato `realtime` do canvas e do Phaser | ADR-0050 | com o estúdio, na v0.5 |
| **Visitantes com login.** Separar as visões jogador e operador por credencial, e não só por conexão | ADR-0022, ADR-0050 | antes de abrir para fora de `127.0.0.1` |
| **Ações padrão do mundo.** Ações que todo mundo tem (andar, esperar, talvez dormir), declaradas pelo kernel. Hoje, cada cartucho declara o próprio catálogo | ADR-0051 | com um segundo gênero (o escritório, v0.4); a Boa Vista é cenário do mesmo gênero |
| **Teclado e arrastar.** Atalhos de teclado para as ações e arrastar no mapa. No M5, só o mouse, com os cliques esquerdo e direito | ADR-0051 | M21 (os menus do humano) |
| **Fila de ações.** Clicar em três canteiros e o avatar fazer um depois do outro, em vez de recusar com `busy` enquanto trabalha. Põe estado novo no kernel (a fila de cada avatar) | ajuste depois do M5 (12/out) | M21 (os menus do humano) |
| **Despertador.** Acordar numa hora marcada. O sono continua não cancelável pelo controlador; o despertador seria uma regra do mundo que encerra o sono, como a de acordar às 06:00 | ajuste depois do M5 (12/out) | junto com a necessidade "sono" |
| **Cartuchos só de arte.** Pacotes genéricos de arte (terreno, construções, personagens), sem mapa, reaproveitados por vários mundos: a fazenda, o vilarejo, o estúdio. Hoje a arte fica em camadas no gênero e nos cenários | ADR-0053 | antes de um segundo gênero (v0.4) |
| **Porta de efeitos externos (a "oficina").** Uma ação longa executada fora do kernel (um agente de código numa worktree isolada), com os resultados voltando como eventos e gravados para reprodução nos testes | ideia do escritório (14/out), ADR-0055 | v0.4 (ADR-0064) |
| **Vários avatares fora do kernel.** O kernel já itera N avatares e aceita um controlador por avatar; a percepção, o gateway (posse por avatar) e a tela assumem um só | ADR-0055 | M20 |
| **Supervisor de versões.** Quem reinicia a pilha numa versão nova publicada pelo próprio mundo, migrando o snapshot e preservando a memória dos agentes | ADR-0055 | v0.4 (ADR-0064) |
| **Duração "até" um evento externo.** Uma ação que dura até a oficina terminar, com o relógio do mundo seguindo normal numa escala baixa; a alternativa é o relógio ancorado ao real | ADR-0055 | v0.4 (ADR-0064); pede ADR, porque toca o princípio 7 |
| **Rótulos de eventos pelo cartucho.** A linha do tempo em linguagem natural ("colheu 3 abóboras", "abriu o PR #41"), com o rótulo de cada evento declarado como dado, como as métricas | referências visuais (17/out) | M17 |
| **O cliente por chat.** O humano falar com o mundo por um painel de conversa que vira comandos, em vez de só andar com um avatar | referências do estúdio (17/out) | v0.4 (ADR-0064); a fazenda pode testar com as encomendas |
| **Raio de percepção menor que o mapa, para todos os atores.** Quem joga vê só o raio e o resto fica ofuscado (névoa); script e LLM recebem a foto recortada e precisam se mover para ver. O raio já é dado do cartucho desde o M8, mas vale a propriedade inteira | plano do M8 (17/out) | M18 |
| **Mapas grandes.** O terreno viaja no `session.started` (1 byte por tile; o NATS aceita 1 MB) e se repete na foto dentro do raio. Até uns 100 × 100 tiles o desenho do M8 serve; acima, o mapa sai da foto (publicado uma vez, guardado pelo controlador) e o raio vira obrigatório | plano do M8 (17/out) | M18 (o mapa maior), se passar de 100 × 100 |
| **Tick mais curto por mundo.** O kernel já tem `tick_seconds`, mas o cartucho declara durações em ticks (minutos). Se as durações passarem a ser em minutos, convertidas pelo kernel como as taxas das necessidades, um mundo em tempo real (escritório, estúdio) pode rodar com ticks de 10 s e responder a comandos em segundos, sem mudar as regras | revisão do relógio a 1× (17/out) | v0.4 (ADR-0064) |
| **Lote na porta de modelo.** `submit_batch` e `collect_batch` no adaptador da Anthropic (metade do preço, assíncrono), para a reflexão da noite quando houver muitos avatares refletindo ao mesmo tempo | plano do M9 (18/out); decisão 7 do M11 | com os vários avatares (M20), se pesar |
| **`cmd.ops.budget.set`.** Subir ou baixar o teto com o mundo vivo, pelo operador; hoje é editar o arquivo do mundo e reiniciar a guarda | plano do M9 (18/out) | M21 |
| **Guarda caída pausa o mundo.** O `ops.heartbeat` dos contratos: sem sinal da guarda, o kernel pausa por segurança | plano do M9 (18/out) | M21 |
| **OpenRouter como segundo adaptador.** Uma chave para Claude, GPT, Gemini e os demais, com `usage.cost` em toda resposta | ADR-0058; fora do M12 por decisão do usuário (19/out) | M21 (a arena de famílias) |
| **A chave `chave-campsverso` expira em 31/12/2026.** Se o projeto ainda chamar a API, renovar a validade ou criar outra na Console e trocar no `.env` | criação da chave (18/out) | no fim de dezembro de 2026 |
| **Prompt de sistema em inglês.** Medir uma vez a diferença de tokens e, se valer, manter a parte fixa (notas e descrições das ferramentas) em inglês com o cartão e as intenções em português | decisão 6 do M10 (18/out) | M21, como medição |
| **Lockstep com o controlador `llm`.** O modo máximo esperando o modelo, para comparações justas e gravações determinísticas fora do pipeline em memória; toca o princípio 7 e pede ADR. Em processo (`make corrida`, `make arena`) o mundo já espera o modelo por construção; isto só vale para a pilha com NATS | decisão 8 do M10 (18/out); ADR-0061 | fazenda 4, se a arena precisar rodar na pilha de verdade |
| **A mente retomar a posse sozinha.** Depois de devolver o avatar ao script por falhas seguidas do modelo, voltar a assumir quando a porta responder de novo (uma sondagem custa uma chamada) | decisão 9 do M10 (18/out) | fazenda 4 (o fallback não aconteceu nas arenas) |
| **Tradutor da foto para prosa.** O JSON da percepção tokeniza a 2 caracteres por token; uma narração em português pode custar menos tokens e ler melhor, ao preço de uma segunda fonte de verdade | calibração do M9 (18/out) | M21, como medição |
| **Custo do dia no painel do operador,** a partir dos `llm.call.*` e dos `ops.budget.*` | decisão 12 do M10 (18/out) | M21 |
| **Relevância na memória: vetores e a `EmbeddingPort`.** Quando as crenças e os episódios não couberem no bloco de abertura, buscar por semelhança (sqlite-vec local, pgvector na nuvem), com o memory stream inteiro: recência × importância × relevância | decisão 2 do M11 (18/out) | decisão 10 da v0.3: medir o bloco no M18 |
| **Importância pontuada por modelo.** Hoje a importância de um episódio vem de uma tabela; o Generative Agents pede ao modelo | decisão 4 do M11 (18/out) | fazenda 4 |
| **Serviço de memória com request-reply.** `cmd.memory.recall` pelo NATS, como o documento de contratos desenhou, quando houver um segundo consumidor (o supervisor migrando memória, dois agentes que compartilham o que ouviram) | decisão 3 do M11 (18/out) | com os vários avatares (M20) ou o supervisor (v0.4) |
| **Origem `told` nas crenças.** Quem me contou, com a confiança reduzida; o schema já aceita | decisão 9 do M11 (18/out) | na camada social (v0.6 em diante, ADR-0064) |
| **Reflexão proporcional ao sono.** Dormir bem reflete melhor; dormir pouco, pior, como num humano; hoje é uma reflexão por dia, ao dormir | ressalva do usuário na decisão 7 do M11 (18/out) | junto com a necessidade "sono" |
| **Adaptador Hindsight pela `MemoryPort`.** O belief store da Vectorize (fatos, experiências, observações consolidadas, opiniões com confiança), sobre PostgreSQL e com reflexão própria, como alternativa à memória baseline | decisão 12 do M11 (18/out) | na memória completa (v0.6 em diante, ADR-0064) |
| **Langfuse e OpenTelemetry GenAI.** Rastros das chamadas de modelo fora dos nossos eventos: self-host em containers ou nuvem; o que a arena precisa já está nos `llm.call.*`, nas fitas e nos resumos | decisão 7 do M12 (19/out) | na versão em nuvem |
| **O humano na tabela de 30 dias.** Hoje é referência qualitativa; entra na arena quando houver uma tarde de jogo gravada (a 72×, 30 dias são 10 horas na tela) | decisão 3 do M12 (19/out) | M21 |
| **Assistir na tela uma corrida da arena.** A arena roda em processo, sem barramento nem tela; o controlador de replay reaplicaria as propostas gravadas num sandbox, mas o kernel só aceita propostas agendadas (`at_tick`) do replay no modo máximo, que não dá para assistir, e com o avatar possuído pelo replay. Pede uma ADR: aceitar `at_tick` no modo contínuo para o replay (o mundo segue determinístico, as propostas já vêm com o tick) e o sandbox com `--replay` passando a posse | pergunta do usuário durante a rodada do M14 (20/out) | M16 |
| **Guardar e pegar ferramentas pelo menu do baú.** O humano guarda itens pelo menu, mas as ferramentas são entidades com id (`plow-1`, `watering-can-large-1`) e não estão nas escolhas, que são listas fixas; a ação já aceita o id, como a mente e o script usam | conferência da tela do M14 (20/out) | M21 (os menus do humano) |
| **Cavar pelo clique direito na grama.** Hoje o menu do humano só cava onde o Camps está (afordância de si, sem alvo); a ação já aceita `target: {x, y}` ao lado, como regar, e a tela poderia abrir um menu num tile de grama vazio | conferência da tela do M13 (20/out) | M21 (os menus do humano) |
| **Espantalho e corvos (R-002).** Sem espantalho, um corvo come uma colheita madura por dia nos canteiros longe da casa; só o efeito é visível, como na R-001 | conversa do M13 (19/out) | M18 |
| **Estações, cesta, ferramentas que quebram, pragas.** Mais atrito e mais decisões, quando a Fazenda Boa Vista já tiver medido o que mede | conversa do M13 (19/out) | as estações no M16; a cesta, as ferramentas que quebram e as pragas na fazenda 4 |
| **Canteiros sem teto, e aterrar o canteiro vazio.** Na Boa Vista ninguém cavou na faixa do rio, e com o teto de 32 e sem desfazer canteiro uma descoberta tardia não muda a fazenda; como no Stardew, cavar em qualquer grama, com a energia, as sementes e a rega como freios, e o canteiro vazio voltando a ser grama depois de alguns dias (pede uma primitiva de remover entidade no kernel e um evento novo) | rodada do M14 (20/out), conversa com o usuário | M16 |
| **Um fazendeiro-script que planeja e experimenta.** O script 2 perdeu para o Opus por cinco vezes em moedas: falta planejar o capital (contar o pagamento antes de comprar), diversificar, usar o arado e o regador grande, cozinhar, guardar o que vence, e fazer experimentos (canteiros de teste em lugares diferentes, medir o tempo de amadurecer e mudar a fazenda para onde rende), sem regra oculta embutida | rodada do M14 (20/out) | M19 (o fazendeiro-script 3 e o oráculo) |
