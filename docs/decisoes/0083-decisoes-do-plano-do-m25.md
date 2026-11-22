# ADR-0083 — Decisões do plano do M25 (o ciclo fecha)

**Status:** aceita · **Data:** 2026-11-20 · **Marco:** M25
**Complementa:** `docs/planos/m25-o-ciclo-fecha.md`; ADR-0077 (o plano macro da v0.4); ADR-0080 (a oficina, a entrega e a bancada); ADR-0070 (o juiz fora da mente); ADR-0058 (a porta de modelo)
**Revê:** ADR-0077, nos modelos dos marcos M26 e M27

## Contexto

No M24, a entrega do dev terminava num patch que o humano aplicava à mão. O M25 fecha o ciclo: a entrega vira um PR no GitHub, o humano mescla, e o escritório vivo troca sozinho para a versão nova, sem perder o mundo nem a memória do dev.

O levantamento achou:
- nenhum serviço fala com o GitHub, e a oficina não tem rede;
- o kernel já troca de versão com segurança: a parada elegante grava um snapshot, e a versão nova retoma dele;
- a memória do dev fica fora do snapshot e sobrevive a um reinício;
- o escritório vivo roda da pasta em que nós trabalhamos.

O usuário aprovou as 16 decisões do plano em 20/nov, com notas. Ele trouxe também o índice de agentes de código da Artificial Analysis daquela semana, com o Antigravity e o Gemini 4 Neon em primeiro (59), o Claude Code com o Fable 5.2 e com o Opus 5.5 logo atrás (58), e o Codex com o GPT-6.2 Astra em 53.

## Decisão

1. **A identidade do dev no GitHub é um GitHub App** só deste repositório (`campsverso-dev`): conteúdo e pull requests, sem workflows nem administração. O usuário o cria, e a chave fica em `privado/`.
2. **O `main` tem um ruleset:** só o dono o atualiza, e o App só escreve em ramos `dev/*`.
3. **Quem abre o PR é o publicador,** um script nosso, depois da revisão da entrega. O modelo nunca vê o GitHub nem a chave: ele entende o projeto pelo clone inteiro da oficina. O publicador aparece na bancada, mas não é uma ferramenta do dev.
4. **O aceite é mesclar.** Devolver segue no quadro, e o dev refaz no mesmo ramo. Fechar o PR sem mesclar devolve o pedido a "a fazer".
5. **Os fatos do GitHub entram no mundo como comandos.** O vigia do GitHub manda ao kernel cada mudança de um PR (`cmd.office.pull_request.report.v1`); o kernel confere e publica `office.ticket.pr_*`. O comando fica no diário, e o replay o refaz sem perguntar ao GitHub.
6. **O primeiro PR de verdade é do dev-script,** sem API, e é fechado sem mesclar: o primeiro PR de todos. O primeiro mesclado é a criação do marco.
7. **O revisor de outra família fica fora do mundo,** como o juiz da arena (ADR-0070): comenta no PR, aconselha o humano e não dá ordens ao dev. Depois ele vira um personagem.
8. **O revisor é o Gemini 4 Neon,** calibrado antes contra o GPT-6.2 Astra em três diffs com defeitos plantados. O GPT-6.2 Astra é a reserva. A API direta do Google ou da OpenAI e o Bedrock são adaptadores da porta de modelo, para quando forem precisos.
9. **O CI confere a constituição** no diff de cada PR de um ramo `dev/*`: a segunda conferência, depois da revisão da oficina.
10. **O escritório vivo roda de uma worktree própria,** presa na versão publicada, sob o supervisor (`make escritorio`).
11. **A troca de versão, o auto-update:** a versão candidata é preparada ao lado e passa por uma fumaça numa cópia dos dados (uma hora simulada). O supervisor espera o dev sair de uma sessão, por até 30 minutos, copia os dados, para com elegância, troca e confere a saúde. Se falhar, volta sozinho para a versão e os dados de antes. Ficam as três últimas cópias, e cada passo vai para o diário da troca.
12. **A versão fica à vista:** uma placa na parede e no HUD (o campo opcional `build` na sessão da tela), o fato do kernel `world.version.changed.v1` e um episódio na memória do dev. A arte vai num pedido ao Claude Design.
13. **A criação é o briefing:** um robô que monta o que uma sessão do Claude Code vai ler, usado no M26. A bancada fica com o testador, o briefing e o publicador.
14. **O dev segue com o Sonnet 5.5;** o Opus 5.5 entra quando o pedido mexe na arquitetura do mundo, escolhido no quadro.
15. **O médio prazo** (revê a ADR-0077):
    - o Gemini 4 Neon passa pela prova de conformidade do nosso harness já no M25;
    - o M26 traz o Claude Code com o Opus 5.5 e o Fable 5.2;
    - o M27 traz o Antigravity com o Gemini 4 Neon e o Codex com o GPT-6.2 Astra, conferindo o índice da hora;
    - o plano do M27 desenha o painel do elenco: que modelo é cada personagem, e quem está ligado numa rodada.
16. **O orçamento de API do M25 é de US$ 20,** cada passo pago com o ok do usuário.

## Consequências

- **O escritório passa a ter efeitos fora do mundo,** no GitHub. O mundo segue reproduzível, porque o que vem de fora entra como comando no diário.
- **Uma credencial nova existe:** a chave do App, fora do git e fora do espaço do dev, com o mínimo de permissões.
- **O escritório vivo deixa a nossa pasta,** e a versão que ele roda passa a ser só a publicada.
- **Os contratos ganham** os fatos do PR, o comando do vigia, a troca de versão e o campo da placa.
- **O CI ganha um passo** que só olha os ramos do dev.
- **A troca de versão pode derrubar o mundo.** A fumaça numa cópia e a volta automática são a resposta.

## Adendo: a parte 1, sem API (20/nov)

O ciclo fecha em memória e o código fala com o GitHub de verdade; falta só o primeiro PR, que espera o ok do usuário. O que a implementação decidiu além do plano:

1. **A porta do repositório de fora** (`CodeHostPort`, em `libs/ports`) tem quatro operações: publicar um ramo, abrir o PR, ler o estado de um PR e comentar. Abrir o PR de um ramo que já tem um PR aberto devolve esse mesmo PR: depois de uma queda, o publicador refaz a entrega sem abrir outro.
2. **O GitHub, sem biblioteca nova e sem `git push`:**
   - o JWT do App é assinado pelo `openssl`, que é o único a ler a chave em `privado/`;
   - o token da instalação, de uma hora, é renovado cinco minutos antes de vencer;
   - o commit vai pela API de dados do git: os arquivos viram blobs, os blobs uma árvore sobre a da base, e a árvore um commit sobre a base (ou sobre o topo do ramo, num pedido refeito);
   - o GitHub falso, em memória, serve aos testes.
3. **O publicador manda o texto inteiro de cada arquivo, e não o patch.**
   - O patch se aplica sobre a base num clone compartilhado deste repositório, e o próprio git diz quais arquivos mudaram.
   - Um arquivo renomeado vira um apagado e um criado.
   - Um arquivo que não é texto em UTF-8, ou um link simbólico, não sai.
4. **O serviço `services/codehost`** tem o usuário NATS `codehost`. Ele lê os pedidos do escritório em `world` e só publica o comando do vigia.
   - O estado fica em `data/codehost/<mundo>/codehost.json`: os títulos dos pedidos, os PRs abertos que o mundo conhece e o último relato de cada um.
   - O mesmo relato não sai duas vezes seguidas.
   - Com o GitHub fora do ar, o vigia avisa e tenta de novo na volta seguinte, a cada 60 segundos.
5. **Antes de sair, a entrega é conferida de novo,** e o título e a descrição do PR também, contra a lista de palavras proibidas, porque o PR é público.
   - Com o GitHub, a lista é obrigatória.
   - Sem a chave ou sem a lista, o processo avisa e só espera, e a entrega fica no depósito, como no M24. O `honcho` derrubaria o escritório inteiro se um processo saísse.
6. **A causa de um comando do cartucho nos fatos genéricos é um nome curto** (`pull_request_report`), tirado do tipo, porque o `cause` de `entity.state_changed` é um token. Isso detalha a decisão 3 da ADR-0084.
7. **O gerente-script dos testes não decide um pedido com PR aberto:** quem decide é quem mescla.
8. **A constituição cresce** com o caminho até o GitHub: `services/codehost/`, os adaptadores `codehost_*` e a própria regra (`workshop_review.py`).
   - O passo novo do CI roda só nos PRs de `dev/*` e usa a regra tirada do `main`, e não a do PR: o dev não muda a regra no mesmo PR que ela confere.
   - A lista de palavras fica fora do git, e o publicador já a conferiu.
   - As notas da mente (`escritorio.md`) ainda listam a constituição de antes. Elas mudam na parte 2, com a fita regravada: mudar o texto que o modelo lê muda o hash de cada pedido da fita.
9. **O sandbox do escritório publica no GitHub só com `GITHUB=1`.** Ele copia o `codehost` do escritório vivo, e `CHAVE=` aponta a chave fora de `privado/`. Sem isso, o sandbox fica como no M24: com o GitHub falso, ninguém mescla, e nenhum pedido seria aceito.

## Adendo: a parte 2, o supervisor (21/nov)

O supervisor está pronto e foi ensaiado de verdade, com um repositório local no papel do GitHub. O que a implementação decidiu além do plano:

1. **Duas worktrees que trocam de papel,** `a` e `b`, em vez de uma viva e uma candidata.
   - A candidata é preparada ao lado (`uv sync`, `pnpm install`, a tela compilada) e vira a viva na troca. A de antes fica intacta, presa no commit dela.
   - Assim, a troca e a volta são só parar, apontar para a outra e subir, sem compilar nada no meio. No ensaio, o escritório ficou 6,2 s fora do ar.
2. **Tudo do escritório vivo fica numa pasta só dele,** `../campsverso-vivo`, com as duas worktrees, os dados, o arquivo, o NATS, as cópias para a volta, os logs e o estado. O git e a pasta de trabalho não a tocam.
   - A pasta `privado/` (a chave do App e a lista de palavras) chega a cada worktree por um link.
   - O `.env` chega pelo ambiente.
   - As senhas do NATS são geradas a cada subida.
3. **A fumaça fecha a cópia com a versão de antes.** O kernel só retoma um mundo com entradas depois do snapshot na mesma versão do código. Na fumaça, o kernel de antes sobe na cópia e para com elegância, e o snapshot a fecha.
   - A versão nova sobe nessa cópia inteira, sem o publicador (nada vai ao GitHub) e sem a mente (nenhuma chamada paga), na escala 72 (o kernel aceita `--scale` num mundo retomado, pelo comando de sempre).
   - Ela passa se nada cai, o gateway responde e o pulso anda.
   - Os invariantes do escritório ficaram de fora da fumaça: eles moram no testkit, que o sistema não importa.
4. **O arquivador só liga depois da saúde.** O arquivo nunca se reescreve, e o que a versão nova publicou numa troca que voltou fica fora dele. O que ela publicou na janela da saúde fica no JetStream, e o arquivador o alcança ao ligar.
5. **A volta devolve os dados e o NATS** guardados logo depois da parada elegante. A oficina (os clones do dev) não entra na cópia nem na volta.
6. **A saúde é lida no `/health` do gateway,** que passa a dizer o tick do pulso do kernel, se o pulso chega, se um dev está numa sessão na oficina (um passo há menos de 5 minutos simulados que não foi a entrega, ou um robô rodando) e a versão.
   - O tick usado é o do pulso. O tick do último fato fica parado de madrugada, e uma troca à noite voltaria à toa; foi o ensaio que mostrou.
7. **Um processo que cai sem troca derruba e sobe a pilha inteira,** na mesma versão. Depois de três reinícios em dez minutos, o supervisor espera, mas segue olhando o `origin/main`, porque o commit novo pode trazer o conserto.
8. **O supervisor não se atualiza sozinho.** Ele roda da pasta de trabalho, e atualizá-lo é reiniciar o `make escritorio` depois de um `git pull`. O `make escritorio-aqui` sobe o escritório desta pasta, sem supervisor, para ver uma mudança antes de publicá-la.
9. **A troca de versão entra no mundo como um comando,** `cmd.world.version.record.v1`, mandado pela raiz de composição do kernel quando o supervisor diz o commit (`CAMPSVERSO_COMMIT`, a data e os PRs).
   - O kernel guarda a versão no estado e publica `world.version.changed.v1`.
   - O gateway manda a versão na sessão da tela, e o HUD a mostra em texto. A placa desenhada da arte do M25 vem depois.
   - A memória do dev guarda a troca com peso 8.

## Adendo: a mesclagem e o revisor (21/nov)

**O ruleset do `main` muda (decisão 2).** Com o escritório vivo ligado, o PR do dev precisa ser mesclável sem a caixa de contornar. A pedido do usuário, a regra "só o dono atualiza" virou:

- o `main` só muda por PR, com os três passos do CI verdes (`make check`, `make ui-e2e` e a constituição do PR do dev) e com uma aprovação;
- a aprovação cai quando o ramo recebe um commit novo, e a mesclagem é por merge ou squash, que são as duas formas em que o supervisor acha o número do PR;
- o contorno de dono continua para os nossos pushes diretos;
- o App não consegue mesclar sozinho, porque não aprova o próprio PR. A garantia vem da permissão, e não do código do publicador, que de todo modo não tem o verbo.

O que o gerente faz num PR do dev: lê o PR, aprova e mescla. O ruleset anterior está guardado fora do git, para voltar se for preciso.

**O revisor de outra família (decisões 7 e 8), como ficou:**

1. **Uma chamada só, sem ferramentas.** O modelo responde em Markdown, e a primeira linha é o veredito: mesclar, conferir ou devolver. Sem ferramentas, a tradução da OpenRouter não tem onde tropeçar, e foi numa chamada com ferramentas que o Gemini desistiu no M21.
2. **O que ele lê:**
   - o pedido do quadro, com o aceite;
   - as seções do `CLAUDE.md` que valem para um diff (os princípios, as convenções e o "nunca faça");
   - a lista da constituição;
   - o diff da entrega, até 150 mil caracteres.
   - A lista de palavras proibidas nunca vai ao modelo, porque é privada. O comentário passa por ela antes de sair.
3. **O publicador chama o revisor, fora do consumidor.** Cada entrega publicada, aberta ou atualizada, entra numa fila no estado do publicador. O laço do serviço a esvazia numa tarefa à parte, porque uma revisão leva minutos e o lote do barramento não pode esperar tanto.
   - A revisão vira um comentário no PR, que diz quem revisou, quem falhou antes e o custo.
   - Uma revisão que falha nos dois modelos sai da fila com um aviso, e `make revisar PR=N` a roda de novo à mão.
4. **A fita do revisor** fica nos dados do mundo (`codehost/<mundo>/revisor.jsonl`). Uma revisão paga e interrompida antes do comentário responde de graça na volta.
5. **O custo do revisor não entra no orçamento do mundo:** ele está fora do mundo, como o juiz. O custo fica na telemetria (`codehost.reviewed`) e no comentário.
6. **A calibração** (`make revisor-calibrar`) usa quatro entregas do escritório. Três têm um defeito plantado: um teste afrouxado, um caminho da constituição e um erro de lógica, em que a sexta caiu na quinta e o teste usa uma quinta. A quarta é o gêmeo limpo do erro de lógica, a mesma mudança feita certa, para medir se o revisor inventa defeito.
   - Os testes e o pyright passam nas quatro: o CI não pega nenhum dos defeitos.
   - As respostas ficam em `tests/fixtures/revisor/calibracao.json` e o relatório em `docs/arena/revisor-calibracao.md`.
7. **A calibração inverteu a ordem da decisão 8.** Na rodada de 21/nov (US$ 0,35, as quatro entregas nos dois modelos):
   - **os dois acharam os três defeitos plantados,** todos como graves, sem nenhum achado a mais nos casos com defeito;
   - **no gêmeo limpo, o GPT-6.2 Astra disse "mesclar",** sem achados;
   - **o Gemini 4 Neon disse "conferir",** com dois achados médios. Um deles lê o princípio 8, que é sobre o código do kernel, como se valesse para os testes; o outro é uma sugestão justa de cobertura, que não impede a mesclagem;
   - **pela regra do plano** (fica o que acha os defeitos sem inventar outros), o Astra passa a ser o plano A, e o Gemini, a reserva;
   - **o Astra também saiu mais barato,** US$ 0,153 contra US$ 0,194 nos quatro casos, porque escreve menos raciocínio, apesar do preço por token maior;
   - **com quatro casos, a diferença é de um caso só.** Voltar à ordem do plano é trocar uma linha do arquivo do mundo, e a próxima calibração, com mais casos, pode mudar isso.

## Adendo: o fechamento (21/nov)

O M25 fecha com as cinco partes do plano, a tela retrô (ADR-0087) e a luz (ADR-0088).
- **Os dois consertos do fechamento,** sem API:
  - **o publicador tenta de novo** a entrega que o GitHub não recebeu, a cada volta do vigia (60 s), até uma hora. Na queda de rede da tarde, a entrega ficava recusada para sempre. Uma entrega nova do mesmo pedido toma o lugar da que esperava, e a fila vai para o estado em arquivo;
  - **o dev convocado não faz as pausas do dia que ficaram para trás.** No primeiro pedido do dev convocado, ele chegou à noite e foi jogar videogame antes de olhar o quadro. Num dia normal, a pausa com mais de uma hora de atraso fica para outro dia. A mente usa a mesma rotina do script.
- **Ficam para o `futuro.md`:**
  - o revisor julgando pela entrega contra o teste de aceite (hoje ele é rigoroso demais), com uma calibração paga nova;
  - o apagar da oficina;
  - a conferência de que a sessão do dev retoma depois de uma falha do modelo.
