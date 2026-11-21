# Plano do M25 — O ciclo fecha

*Proposto em 20/nov/2026, depois do fechamento do M24 (ADR-0080). É o terceiro marco da v0.4 (ADR-0077): a entrega do dev deixa de ser um patch que o humano aplica à mão e vira um PR no GitHub, que só o humano mescla. Quando ele mescla, o escritório reinicia sozinho na versão nova, e o dev lembra o que fez. Entra também o que o usuário perguntou em 20/nov: uma revisão por um modelo de outra família e o Gemini 4 Neon no médio prazo.*

***Aprovado em 20/nov/2026 (ADR-0083),*** *com as 16 decisões como recomendado e as notas do usuário:*
- *o primeiro PR, o do dev-script, é o primeiro de todos: um marco;*
- *o revisor começa fora do mundo, como o juiz, e depois vira um personagem;*
- *o revisor tem o GPT-6.2 Astra de reserva, e os adaptadores diretos do Google, da OpenAI e do Bedrock ficam para quando forem precisos;*
- *a troca de versão, o "auto-update", ganha o detalhe que um post pede (§3);*
- *a placa da versão vai num pedido de arte ao Claude Design (§4);*
- *o Opus 5.5 entra quando o pedido mexe na arquitetura do mundo (§6);*
- *o painel do elenco (que modelo é cada personagem, e quem está ligado) vai para o plano do M27 (§6);*
- *o orçamento do M25 é de US$ 20.*

**Pronto quando:**
- **O PR:** a entrega do dev vira um PR no GitHub, aberto por uma identidade só dele, que não mescla nem toca no `main`. O modelo nunca vê o GitHub nem a credencial.
- **A revisão antes de você:**
  - o PR chega com o resultado do testador, a revisão de sempre (a constituição, os testes apagados, as palavras proibidas) e o CI;
  - um revisor de outra família (o Gemini 4 Neon) comenta no PR;
  - você mescla, ou devolve no quadro.
- **O supervisor:** quando você mescla, o escritório vivo testa a versão nova numa cópia do mundo e só então troca. Se ela falhar, volta para a anterior sozinho.
- **A versão à vista:** o escritório mostra a versão que roda, e o dev lembra que ela mudou e por quê.
- **A criação:**
  - você pede o briefing no quadro;
  - o dev o entrega por PR, e você mescla;
  - o escritório reinicia na versão nova;
  - o briefing aparece na bancada, e o dev lembra que o fez.
- **O mundo intacto:**
  - as fazendas e o soak do escritório seguem iguais;
  - o replay reproduz os dias com PR.

## O que o levantamento mostrou

- **A entrega do M24 termina num patch:**
  - o patch fica no depósito de entregas;
  - o `make aplicar` o põe num ramo local;
  - o aceite é um botão do gerente no quadro.
- **Nenhum serviço fala com o GitHub,** e a oficina não tem rede. Não há `gh` na máquina. A API pública basta para ler o estado de um PR e do CI; abrir um PR pede uma credencial.
- **O kernel já troca de versão com segurança:**
  - a parada elegante grava um snapshot, e a versão nova retoma dele;
  - o kernel recusa subir se sobraram incrementais gravados por outra versão. É a base do supervisor.
- **A memória do dev** fica fora do snapshot (`data/<mundo>/memory/camps.sqlite`) e sobrevive a um reinício.
- **O CI** roda em todo PR, em dois jobs, e nunca chama a API.
- **O escritório vivo** (`make escritorio`) roda da pasta principal, a mesma em que nós trabalhamos. Trocar a versão dele hoje seria trocar o código debaixo de nós.
- **A bancada** tem três apoios, e só o testador está nela. A arte do revisor e do publicador já existe (ADR-0080, adendo de 16/nov).

## 1. O caminho do PR

- **A identidade do dev no GitHub:** um GitHub App só deste repositório (`campsverso-dev`), criado por você.
  - **Pode:** ler e escrever conteúdo e pull requests.
  - **Não pode:** mexer em workflows nem na administração.
  - **A chave privada** fica fora do git, em `privado/`, e nunca entra no espaço do dev.
  - **No GitHub,** o PR aparece como `campsverso-dev[bot]`, e não no seu nome.
- **O `main` protegido** por um ruleset:
  - só você atualiza o `main`; os meus pushes seguem com a sua credencial, como hoje;
  - o App só escreve em ramos `dev/*`.
- **Quem abre o PR é o publicador,** um script nosso, e não o modelo. Depois que a revisão da oficina aprova a entrega, ele:
  - aplica o patch num ramo `dev/pedido-N`, sobre o `main` de agora;
  - empurra o ramo e abre o PR;
  - no PR vão o título do pedido, o resumo do dev, o teste de aceite, o resultado do testador e o custo da sessão.
- **O publicador na bancada:** ele aparece como robô e trabalha enquanto abre o PR, pelos mesmos fatos da oficina (`workshop.robot_started` e `robot_called`). Não é uma ferramenta do dev: o `chamar_robo` não o oferece.
- **O que volta para o mundo:**
  - um vigia do GitHub, processo nosso, lê o estado de cada PR aberto a cada minuto: o CI, a revisão, mesclado ou fechado;
  - ele manda cada mudança ao kernel como comando;
  - o kernel publica os fatos `office.ticket.pr_*`, que ficam no diário, e o replay os refaz;
  - sem o GitHub, o vigia tenta de novo, e o mundo segue.
- **No quadro,** o pedido entregue mostra o número do PR, o CI e o link.
- **O aceite é mesclar:**
  - quando você mescla, o pedido vai para "aceito";
  - devolver segue no quadro, com o comentário, e o dev refaz no mesmo ramo, num commit novo;
  - fechar o PR sem mesclar devolve o pedido a "a fazer".
- **Nos testes e no soak:** um GitHub falso, em memória, atrás de uma porta (`CodeHostPort`, princípio 3). O real fica só no escritório vivo.

**O que o dev vê, sem o GitHub** (a pergunta do usuário em 20/nov). O dev não precisa do GitHub para entender o projeto:
- **ele trabalha numa cópia inteira do repositório,** o clone da oficina: todo o código, os testes, os documentos e o `CLAUDE.md`. Só ficam de fora o `.env`, o `data/` e o `privado/`;
- **ele não lê tudo de uma vez,** e nem precisa. Como o Claude Code aqui, ele procura (`buscar`), lista (`ver_arquivos`) e lê (`ler`) os arquivos que importam para o pedido, a partir do `CLAUDE.md` e dos documentos que ele indica;
- **o GitHub é só a vitrine:** onde o código vai para a revisão e onde você mescla. Os comentários do revisor e os seus no PR não chegam ao dev sozinhos. Se você devolve o pedido no quadro, o seu comentário chega, como hoje;
- **no M26, o briefing** (a criação deste marco) monta o começo de cada sessão: o pedido, o aceite e as regras que importam.

**Por que os fatos do GitHub entram como comandos** (a pergunta do usuário em 20/nov):
- **O mundo tem um dono só da verdade, o kernel** (princípio 2). Tudo o que acontece nele vira um fato no diário: o pedido escrito, o dev sentado, a entrega. É isso que deixa reproduzir um dia inteiro depois (o replay).
- **Mas o merge acontece fora do mundo,** no GitHub. Para o quadro mostrar "aceito", alguém tem de levar a notícia para dentro.
- **Quem leva é o vigia do GitHub:** um processo nosso que, a cada minuto, pergunta ao GitHub como está cada PR. Quando algo muda, ele manda ao kernel um recado (um comando): "o PR #12, do pedido 3, foi mesclado".
- **O kernel confere e registra:** o pedido existe? Ele foi entregue com aquele PR? Se sim, publica o fato `office.ticket.pr_merged`, e o pedido vai para "aceito".
- **No replay,** o recado já está no diário, no tick em que chegou. O kernel o refaz sem perguntar de novo ao GitHub, e o dia sai igual.
- **É como o gerente apertando "aceitar" na tela:** o vigia é uma segunda mão, que aperta o botão quando o GitHub diz que mesclou.

## 2. A revisão antes de você

São cinco camadas, da mais barata para a mais cara:
1. **O testador,** um robô sem modelo: o dev o chama antes de entregar, e o resultado vai no PR.
2. **A revisão da oficina,** como no M24: a constituição, os testes apagados e as palavras proibidas.
3. **O CI do GitHub,** com um passo novo que confere no diff do PR que a constituição não mudou. É a segunda conferência que a §6 do plano macro pede:
   - **a constituição** são os caminhos que o dev nunca muda: o `CLAUDE.md`, `contracts/`, `.github/`, o `Makefile`, os tetos em `config/`, as ADRs aceitas e `data/archive/`;
   - **a primeira conferência é nossa,** na revisão da oficina: uma entrega que toca nesses caminhos nem vira PR;
   - **a segunda é do GitHub:** num PR de um ramo `dev/*`, o CI lista os arquivos mudados e fica vermelho se algum estiver na constituição. Se a nossa revisão tiver um defeito, ou se alguém empurrar algo para o ramo do dev por outro caminho, você vê o vermelho antes de mesclar;
   - **a terceira é o próprio App,** que não tem permissão de mexer em workflows;
   - **os nossos PRs e pushes** seguem mudando a constituição quando precisam: o passo só olha os ramos `dev/*`.
4. **O revisor de outra família:** um modelo que não é Claude lê o diff, o pedido e o `CLAUDE.md`, e comenta no PR.
   - Fica fora do mundo, como o juiz da arena (ADR-0070): não é robô nem avatar, e não dá ordens ao dev.
   - Ele aconselha você, e você decide se devolve. A regra 3 do escritório (LLMs são sempre avatares humanos) vale para quem está no mundo.
   - Roda aqui, chamado pelo publicador, nunca no CI. `make revisar PR=N` o roda de novo à mão.
5. **Você mescla.** Quando quiser uma segunda leitura, eu reviso o PR aqui na conversa, como revisei o testador.

**O modelo do revisor:**
- **A proposta:** o Gemini 4 Neon, pela OpenRouter, a US$ 3 / 15 por milhão de tokens (entrada / saída) em 20/nov. Com o Antigravity, ele lidera o índice de agentes de código da Artificial Analysis desta semana (59).
- **A calibração antes do primeiro PR,** como os controles do juiz:
  - três diffs com defeitos plantados: um teste afrouxado, um caminho da constituição e um erro de lógica;
  - lidos pelo Gemini 4 Neon e pelo GPT-6.2 Astra (US$ 8 / 40);
  - fica o que achar os defeitos sem inventar outros.
- **O risco do Gemini:** no M21, ele desistiu no primeiro dia pela OpenRouter (`INVALID_ARGUMENT` do Google). O revisor é uma chamada só, sem ferramentas, então o risco é menor.
- **A reserva, em camadas:**
  - **o plano A** é o Gemini 4 Neon pela OpenRouter;
  - **o plano B:** se ele falhar, o mesmo pedido vai ao GPT-6.2 Astra pela OpenRouter, e o comentário diz quem revisou;
  - **o plano C,** quando for preciso: a API direta do Google ou da OpenAI, sem a OpenRouter.
- **A arquitetura já deixa isso desacoplado:**
  - a mente e o revisor só falam com a porta de modelo (`ModelPort`, ADR-0058);
  - quem escolhe o adaptador é uma tabela de rotas no ambiente: hoje a API da Anthropic ou a OpenRouter;
  - um adaptador novo (o Google, a OpenAI direta, o Bedrock da AWS) é uma classe em `libs/adapters` e uma linha na tabela, sem mexer na mente;
  - o M27 precisa das chaves diretas do Google e da OpenAI para o Antigravity e o Codex, e os adaptadores diretos entram ali.

## 3. O supervisor: o auto-update do escritório

O escritório passa a se atualizar sozinho: o dev escreve o código, você mescla, e o escritório vivo testa a versão nova e troca para ela, sem ninguém parar nada. Se ela quebrar, ele volta sozinho para a de antes. Por isso cada passo é desenhado para falhar sem estrago.

**Onde cada coisa roda:**
- **A pasta de trabalho** (a nossa, onde o Claude Code e você mexem) não roda mais o escritório vivo.
- **O escritório vivo** roda de uma worktree só dele, `../campsverso-vivo/`, presa no commit publicado. O git garante que ninguém edita ali por engano.
- **A pasta de dados do mundo** (`data/office-campsverso-01/`, com o snapshot, o diário e a memória do dev) fica fora das duas worktrees, e as versões a usam uma de cada vez.
- **`make escritorio` sobe o supervisor,** e o supervisor sobe a pilha da worktree viva: o NATS, o kernel, a percepção, o controlador, o arquivador, o gateway e a guarda.

**O ciclo, passo a passo**, a cada minuto:
1. **Olhar:** o supervisor busca o `origin/main`. Se o commit é o mesmo que roda, nada a fazer.
2. **Preparar, ao lado:** num commit novo, ele monta a versão candidata numa segunda worktree, `../campsverso-candidata/`: as dependências (`uv sync`, `pnpm install`) e a tela compilada. O escritório vivo segue rodando, sem perceber.
3. **A fumaça, numa cópia:**
   - copia a pasta de dados para uma pasta temporária;
   - sobe a versão candidata sobre a cópia, com o NATS próprio, numa porta própria;
   - anda uma hora simulada a 72×, uns 50 s;
   - confere: o kernel subiu do snapshot sem recusar, nenhum serviço caiu, os invariantes do escritório valem, e o gateway responde.

   O mundo de verdade não é tocado. Se a fumaça falha, a candidata é descartada, e o escritório mostra "a versão X não passou na fumaça".
4. **Esperar a hora:** se o dev está no meio de uma sessão na oficina, o supervisor espera ela acabar, por até 30 minutos. Passou disso, troca assim mesmo, e a sessão volta no próximo bloco de trabalho.
5. **Guardar a volta:** antes de trocar, copia a pasta de dados de verdade para `data/versoes/<commit-antigo>/`. Ficam as três últimas cópias.
6. **A troca:**
   - para a pilha com elegância: o kernel grava o snapshot ao parar, e a memória do dev já está no disco;
   - move a worktree viva para o commit novo (`git checkout`, já preparado no passo 2);
   - sobe a pilha da versão nova sobre os mesmos dados.
7. **A saúde, por 2 minutos:** o gateway responde, o pulso do kernel anda, o dev volta a decidir, e nenhum serviço cai.
8. **Deu certo:** o kernel publica `world.version.changed.v1`, a placa mostra a versão nova, e o dev guarda o episódio na memória.
9. **Deu errado** (a saúde falhou): para a versão nova, devolve a pasta de dados copiada no passo 5, volta a worktree ao commit antigo e sobe de novo. O escritório mostra "a versão X caiu e voltamos para a Y", e o supervisor não tenta aquele commit de novo até chegar outro.

**O diário da troca:** cada passo vai para `data/versoes/supervisor.jsonl`, com a hora, o commit, o resultado e o tempo. É de onde sai o post: quanto tempo o escritório ficou fora do ar em cada troca (a meta: menos de um minuto), quantas trocas deram certo e quantas voltaram.

**O que pode dar errado, e o que acontece:**
- **o código novo não compila ou não sobe:** a fumaça pega, nada muda;
- **o código novo não lê o snapshot de antes** (o formato do estado mudou): a fumaça pega, porque sobe da cópia do snapshot de verdade;
- **cai depois de subir, com o mundo de verdade:** a saúde pega, e a volta devolve os dados de antes da troca;
- **o supervisor cai no meio da troca:** ao subir de novo, ele lê o diário da troca e termina a volta;
- **duas mesclas seguidas:** ele troca para a mais nova e registra as duas.

**O que não é automático:**
- uma mudança que quebra o formato dos dados de propósito (uma migração) não passa pela fumaça. Ela vem de nós, com ADR, e não do dev, que não toca nos contratos;
- o supervisor nunca mescla nada nem empurra para o GitHub: ele só lê o `origin/main`.

## 4. A versão à vista e a memória

- **A placa:** o escritório mostra a versão que roda, o commit curto e a data, numa placa na parede e no HUD. Vai num campo opcional novo da sessão da tela (`realtime/welcome.v1`).
- **O fato da troca:** ao subir numa versão diferente da que gravou o snapshot, o kernel publica `world.version.changed.v1`, com a versão de antes, a de agora e os PRs que entraram.
- **A memória:** a troca vira um episódio de peso alto: "o escritório reiniciou na versão X, com o PR do pedido N". A revisão da manhã seguinte o vê.
- **A arte é nova** e vai num pedido ao Claude Design (`docs/design/briefing-arte-m25.md`), como os do M23 e do M24:
  - a placa da versão na parede, com espaço para o commit e a data;
  - o robô do briefing, para a bancada;
  - um selo de PR nas fichas do quadro: aberto, CI verde ou vermelho, mesclado;
  - o publicador trabalhando: a arte dele existe, mas sem a animação de enviar.

  Até a arte chegar, a placa e o selo saem em texto, na tela.

## 5. A criação: o briefing

A criação do plano macro (§4), usada no M26: o texto que uma sessão do Claude Code vai ler.

- **O pedido,** escrito por você no quadro. Os textos, prontos para colar:
  - **Título:** `Briefing`
  - **O que fazer:** `Um robô para a bancada que monta o briefing de uma sessão do Claude Code. Ele recebe dois arquivos do espaço de trabalho: o pedido (título, o que fazer e o teste de aceite) e as notas da memória do dev. Devolve um texto em Markdown com: o pedido e o aceite como vieram; as regras do CLAUDE.md que valem para ele (os princípios e as convenções, sem o resto); os arquivos do repositório que o pedido provavelmente toca, achados pelas palavras do pedido; e as notas da memória que falam do assunto. Uso: python -m tools.robos.briefing <pedido.md> <notas.md>.`
  - **Teste de aceite:** `Com um pedido de exemplo, o briefing tem no máximo 150 linhas, traz o teste de aceite sem mudar uma palavra, cita pelo menos um arquivo que existe no repositório e não traz nada do .env, de data/ nem de privado/. Vem com o teste do próprio briefing em tools/robos/tests e a linha dele no registro de robôs.`
  - **Tamanho:** `M`
- **Onde mora:** `tools/robos/briefing.py`, com o teste, e uma linha no registro de robôs do cenário.
- **O caminho inteiro é o teste do marco:**
  - o dev (o Sonnet 5.5) faz o briefing e chama o testador;
  - o publicador abre o PR, e o revisor comenta;
  - você mescla;
  - o supervisor testa e troca;
  - o briefing aparece na bancada, e o dev lembra que o fez.
- **A bancada fica com três robôs:** o testador, o briefing e o publicador.

## 6. Os modelos

- **O dev:** o Sonnet 5.5, que fez a criação do M24 por uns US$ 0,05 por pedido, para os pedidos pequenos e os que não mexem na arquitetura do mundo. Um pedido que mexe no kernel ou no desenho de um cartucho vai para o Opus 5.5: o modelo vem no pedido, escolhido por você no quadro, e o custo previsto aparece antes.
- **O revisor:** o Gemini 4 Neon, com o GPT-6.2 Astra na calibração e de reserva (§2).
- **O médio prazo,** uma revisão da ADR-0077 com o índice da Artificial Analysis de 20/nov:
  - **o Gemini 4 Neon na prova de conformidade** do nosso harness ainda no M25 (centavos), para poder ser o dev num pedido de comparação;
  - **o M26, o Claude Code,** com o Opus 5.5 e o Fable 5.2 (58 no índice, no Claude Code);
  - **o M27, o Antigravity com o Gemini 4 Neon** (59, o primeiro) **e o Codex com o GPT-6.2 Astra** (53). Os laboratórios trocam de modelo todo mês, então o plano do M27 confere o índice da hora.
- **Um segundo dev,** outro avatar que também revise, continua no escritório 2 (plano macro, §10). O revisor de fora deste marco é o primeiro passo dele.
- **O painel do elenco, para o plano do M27:** com vários modelos e harnesses ligados, o escritório precisa dizer, na própria tela, que modelo é cada personagem e quem está ligado ou desligado numa rodada. Por exemplo, o Camps no Sonnet pelo nosso harness, um segundo dev no Gemini 4 Neon pelo Antigravity, e o revisor no GPT-6.2 Astra. O plano do M27 desenha isso por inteiro: o painel do operador, o arquivo do mundo e o que o gerente vê.

## 7. Contratos

- **Os fatos do PR** (do domínio `office`): `office.ticket.pr_opened.v1`, `pr_updated.v1` (o CI e a revisão), `pr_merged.v1` e `pr_closed.v1`.
- **O comando do vigia do GitHub:** `cmd.office.pull_request.report.v1`. O kernel o valida e publica o fato, e o comando fica no diário.
- **A troca de versão:** `world.version.changed.v1`, do kernel.
- **A placa:** o campo opcional `build` em `realtime/welcome.v1`.
- **O publicador** usa os fatos da oficina que já existem.

## 8. Testes do marco

- **Unidade:**
  - o publicador com o GitHub falso: o ramo, o corpo do PR e nenhuma credencial no espaço do dev;
  - o vigia do GitHub: cada mudança de um PR vira um comando, uma vez só;
  - os estados do pedido com o PR: entregue, devolvido, mesclado e fechado;
  - o revisor com a fita: o pedido e o comentário;
  - o fato da troca de versão e o episódio na memória.
- **O supervisor,** com um repositório local no papel do GitHub:
  - um commit bom troca a versão e mantém a memória;
  - um commit que quebra a fumaça não troca;
  - um que passa na fumaça e cai depois volta atrás, com a pasta de dados de antes.
- **De ponta a ponta, com a fita e o GitHub falso:** a manhã do escritório de novo, agora com o PR aberto e mesclado, e o pedido aceito. A fita é gravada de novo (centavos).
- **No navegador:** o quadro com o PR, o CI e o link, e a placa da versão.
- **O mundo intacto:** os soaks das fazendas, o soak do escritório e o replay de um dia com PR.

## 9. Ordem do trabalho, em quatro partes

1. **O caminho do PR, sem API:**
   - a porta e o GitHub falso;
   - o publicador e o vigia do GitHub;
   - os contratos;
   - o quadro;
   - o passo da constituição no CI;
   - depois que você criar o App, o primeiro PR de verdade, aberto pelo dev-script e fechado sem mesclar.
2. **O supervisor, sem API:**
   - a worktree do escritório vivo;
   - a fumaça, a troca e a volta;
   - a placa e o fato da troca.
3. **O revisor,** em centavos: a calibração e o comentário no PR.
4. **A criação,** em centavos: o briefing por PR, do pedido ao reinício, e o fechamento.

## 10. Custo

- **API, em passos pagos, cada um com o seu ok:**
  - a prova de conformidade do Gemini 4 Neon: US$ 0,10 a 0,30;
  - a calibração do revisor (três diffs, dois modelos): uns US$ 0,30;
  - as sessões do dev na criação e nos testes de PR: US$ 0,05 a 0,15 por pedido;
  - o revisor: US$ 0,02 a 0,10 por PR;
  - a fita de novo: uns US$ 0,06;
  - **total previsto:** US$ 1 a 3. O teto do marco é de US$ 20, como o usuário pediu, com uns US$ 99 de saldo na Console em 20/nov. O plano macro previa US$ 10 a 20.
- **GitHub:** nada. O repositório é público, e o Actions é grátis.
- **O Claude Code:** um marco do tamanho do M24.

## 11. Riscos

- **A credencial vaza.**
  - A chave do App fica em `privado/` e nunca entra no espaço do dev.
  - O App não mexe em workflows nem no `main`.
  - O ruleset segura o resto.
- **A versão nova quebra o mundo.** A fumaça numa cópia, a cópia da pasta de dados e a volta automática.
- **Um PR público leva o que não pode sair.** A revisão com as palavras proibidas, o passo da constituição no CI, o revisor e você antes de mesclar.
- **O revisor erra ou inventa.** A calibração com defeitos plantados. Ele só aconselha.
- **O Gemini falha pela OpenRouter,** como no M21. Uma chamada só, sem ferramentas, e o GPT-6.2 Astra de reserva.
- **A troca no meio de uma sessão do dev.** O supervisor espera o dev sair da oficina.
- **O GitHub fora do ar.** O vigia tenta de novo, e o pedido fica em "entregue" até o PR responder.

## 12. Decisões

Respondidas pelo usuário em 20/nov/2026 (ADR-0083).

**O PR**

1. **A identidade do dev:** um GitHub App só deste repositório, criado por você, sem workflows nem administração, com a chave em `privado/`. *Sim, o App.*
2. **O `main` protegido por um ruleset:** só você atualiza o `main`, e o App só escreve em `dev/*`. *Sim.*
3. **Quem abre o PR é o publicador,** um script nosso, depois da revisão da entrega. O modelo nunca vê o GitHub, e o publicador aparece na bancada. *Sim. O dev entende o projeto pelo clone inteiro da oficina, como o Claude Code aqui (§1).*
4. **O aceite é mesclar:**
   - devolver segue no quadro, e o dev refaz no mesmo ramo;
   - fechar sem mesclar devolve o pedido a "a fazer".

   *Sim.*
5. **Os fatos do GitHub entram no mundo como comandos** do vigia do GitHub, gravados no diário, com os contratos `office.ticket.pr_*`. *Sim. A explicação está na §1.*
6. **O primeiro PR de verdade** é do dev-script, sem API, e fechado sem mesclar. O primeiro mesclado é a criação. *Sim: o primeiro PR de todos, um marco do projeto.*

**A revisão**

7. **O revisor de outra família,** fora do mundo, como o juiz da arena: ele comenta no PR e não dá ordens ao dev. *Sim. Depois ele vira um personagem.*
8. **O modelo do revisor:** o Gemini 4 Neon, calibrado contra o GPT-6.2 Astra em três diffs com defeitos plantados. *Sim, com o GPT-6.2 Astra de reserva. O plano C, a API direta do Google ou da OpenAI, e o Bedrock são adaptadores para quando forem precisos (§2).*
9. **O passo da constituição no CI,** sobre o diff de cada PR de um ramo `dev/*`. *Sim. A explicação está na §2.*

**O supervisor**

10. **O escritório vivo numa worktree própria,** presa na versão publicada, sob o supervisor (`make escritorio`). *Sim.*
11. **A troca de versão, o auto-update:**
    - a fumaça numa cópia, uma hora simulada;
    - a espera pelo fim da sessão do dev, até 30 minutos;
    - a parada elegante, a troca e a saúde;
    - a volta automática se falhar;
    - as três últimas cópias da pasta de dados;
    - o diário da troca.

    *Sim, com o detalhe da §3, que serve também ao post.*
12. **A versão à vista:** a placa na parede e no HUD, o fato `world.version.changed.v1` e o episódio na memória do dev. *Sim, com a arte num pedido ao Claude Design (§4).*

**A criação e os modelos**

13. **A criação é o briefing,** com os textos do pedido na §5. A bancada fica com o testador, o briefing e o publicador. *Sim.*
14. **O dev segue com o Sonnet 5.5;** o Opus 5.5 quando o pedido mexe na arquitetura do mundo. *Sim.*
15. **O médio prazo** (revisão da ADR-0077):
    - o Gemini 4 Neon na prova de conformidade do nosso harness já no M25;
    - no M26, o Claude Code com o Opus 5.5 e o Fable 5.2;
    - no M27, o Antigravity com o Gemini 4 Neon e o Codex com o GPT-6.2 Astra, conferindo o índice da hora no plano dele.

    *Sim: conectar todos. O painel do elenco, com o modelo de cada personagem e quem está ligado numa rodada, entra no plano do M27 (§6).*
16. **O orçamento do M25:** cada passo pago com o seu ok. *US$ 20.*

## 13. A parte 5: a convocação e a troca segura (21/nov)

**Por quê:** o usuário trabalha no projeto nos fins de semana e feriados, justamente quando o dev não está. E as primeiras trocas de verdade, em 21/nov, mostraram duas falhas:
- o supervisor segue qualquer commit novo do `origin/main`, até com o CI vermelho (o `49fb87e` foi ao ar assim);
- a tela não diz nada enquanto o escritório troca de versão.

### A convocação

- **Ao entrar:** quando o gerente entra fora do expediente e dentro da janela da convocação, o dev é convocado sozinho.
  - Ele chega pela porta depois do deslocamento e diz que veio pelo chamado.
  - O vigia sai na troca, como no fim do expediente.
- **O botão:** com a convocação ao entrar, ele serve para o resto.
  - "Dispensar o Camps", enquanto o dev está convocado.
  - "Convocar o Camps" para chamá-lo de novo depois de dispensá-lo, num cenário com a convocação ao entrar desligada, ou para um segundo dev, que não vem sozinho.
- **Até quando:** até o gerente dispensar ou sair do escritório, com um teto de horas. O que o dev estiver fazendo termina como no fim do expediente.
- **Os números ficam nos dados do cenário** (`schedule.on_call`):
  - se a convocação está ligada, e se ela vem ao entrar;
  - a janela do dia em que vale (padrão 08:00 às 23:00), em qualquer hora fora do expediente: as noites, os fins de semana e os feriados;
  - o deslocamento (padrão 2 minutos);
  - o teto de uma convocação (padrão 6 horas);
  - cada dev do elenco pode ter o próprio acordo, por cima do padrão do cenário.
- **No mundo:**
  - a convocação e a dispensa são ações do gerente, que o kernel confere e publica como fatos do escritório (`office.staff.summoned.v1` e `office.staff.dismissed.v1`);
  - o dev entra e sai com o motivo `convocacao`;
  - o replay refaz tudo, e a tela só propõe.
- **O dev sabe:** a percepção mostra a convocação, e a memória a guarda (quem chamou e quando).
- **O custo:** os tetos do orçamento de hoje, por dia e por pedido, seguem valendo.

### A troca segura

- **Só com o CI verde:** o supervisor só troca para um commit do `origin/main` cujos passos do CI no GitHub terminaram verdes.
  - Ele lê o CI pelo App, que já tem Checks: Read.
  - Um commit vermelho é recusado, como uma fumaça que falha; um que ainda roda espera.
- **Nunca um commit local:** o supervisor só olha o `origin/main`. Hoje o `main` muda por um PR mesclado (o CI verde e a sua aprovação) ou por um push nosso. Com o portão do CI, os dois só vão ao ar verdes.
- **Seguir só as versões publicadas** (as tags `v*`) fica como opção do supervisor para depois, se o escritório um dia precisar de mais calma.

### A troca avisada

- **Antes de parar a pilha,** o supervisor avisa o gateway vivo, e o gateway avisa as telas: "o escritório vai trocar para a versão abc1234 (PR #N)". A mensagem é nova no contrato da tela (`realtime`).
- **Com a conexão caída,** a tela mostra uma faixa "trocando de versão…", e não só os botões apagados. Uma queda sem aviso mostra "conexão perdida; tentando de novo".
- **Na volta,** a faixa diz "versão nova: abc1234 · PR #N" por alguns segundos, e a placa muda como hoje.
- **Uma troca que espera o dev terminar uma sessão** avisa também: "troca pendente: esperando o dev terminar".
- **Uma volta** avisa: "a versão nova falhou; voltamos para a abc1234".

### O primeiro pedido do dev convocado

O PR #2 caiu no lint, que a revisão da oficina não roda. O testador passa a rodar o `ruff` e o `pyright` nos arquivos mudados. É uma melhoria do robô do próprio dev, em `tools/robos/`, fora da constituição: um bom primeiro pedido para o dev convocado.

### Ordem, testes e custo

1. **A troca segura,** primeiro, porque é segurança.
2. **A convocação:** os dados, as ações, os fatos, o sistema, o painel e a memória.
3. **O aviso da troca:** o gateway e a tela.

- **Os testes:**
  - o sistema do escritório:
    - convocar fora do expediente;
    - chegar depois do deslocamento, e o vigia sai;
    - dispensar, o teto, e o gerente que sai;
    - fora da janela, nada;
  - o replay de um sábado com convocação;
  - o supervisor com o CI falso: o vermelho é recusado, o que roda espera e o verde troca;
  - no navegador, o botão e a faixa.
- **Uma ADR nova,** a 0086, com as decisões.
- **O custo:** nada de API para construir. A convocação gasta o que o dev gastaria no expediente.

## Apêndice: como criar o GitHub App

Os passos que o usuário faz, uma vez só. A chave privada nunca entra na conversa nem no git.

1. **Criar o App:** no GitHub, a sua foto → **Settings** → **Developer settings** → **GitHub Apps** → **New GitHub App**.
   - **GitHub App name:** `campsverso-dev`. Se o nome estiver tomado, `campsverso-dev-campilho`.
   - **Homepage URL:** `https://github.com/campilho/campsverso`.
   - **Webhook:** desmarcar **Active**. O vigia do GitHub pergunta; ninguém precisa avisar.
   - **Repository permissions:**
     - **Contents:** Read and write;
     - **Pull requests:** Read and write;
     - **Checks:** Read-only;
     - **Commit statuses:** Read-only;
     - **Metadata:** Read-only (vem sozinho);
     - todas as outras, inclusive **Workflows** e **Administration:** No access.
   - **Where can this GitHub App be installed?** **Only on this account.**
   - **Create GitHub App.**
2. **Anotar o App ID,** que aparece no topo da página do App. Não é segredo.
3. **Gerar a chave privada:** na mesma página, **Private keys** → **Generate a private key**. O navegador baixa um arquivo `.pem`. Mova-o para `privado/github-app-campsverso-dev.pem`, na raiz do repositório. A pasta `privado/` fica fora do git.
4. **Instalar o App no repositório:** no menu do App, **Install App** → **Install** na sua conta → **Only select repositories** → `campsverso` → **Install**. A página que abre termina em `/installations/<número>`: anotar o número, o ID da instalação. Também não é segredo.
5. **Proteger o `main`:** no repositório, **Settings** → **Rules** → **Rulesets** → **New ruleset** → **New branch ruleset**.
   - **Ruleset name:** `main protegido`;
   - **Enforcement status:** Active;
   - **Bypass list:** **Add bypass** → **Repository admin** (você);
   - **Target branches:** **Add target** → **Include default branch**;
   - **Rules:** marcar **Restrict updates**, **Restrict deletions** e **Block force pushes**;
   - **Create.**
6. **Passar para a conversa** só o App ID e o ID da instalação. Eu confiro o resto com uma chamada que só lê, sem abrir a chave.
