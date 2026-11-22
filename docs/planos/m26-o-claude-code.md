# Plano do M26 — O Claude Code

*Proposto em 21/nov/2026, depois do fechamento do M25 (ADR-0083). É o quarto marco da v0.4 (ADR-0077): o dev ganha a segunda ferramenta da escada. Até aqui ele programa pelo nosso harness, com oito ferramentas pequenas. Agora ele também pode sentar e trabalhar numa sessão do Claude Code, pelo Claude Agent SDK, no mesmo espaço da oficina, com o briefing (a criação do M25) abrindo a sessão. O marco mede as duas mãos lado a lado e termina com o dev fazendo, pelo Claude Code, o conector do Codex que o M27 usa.*

***Aprovado em 22/nov/2026 (ADR-0089),*** *com as 12 decisões como recomendado. O usuário perguntou:*
- *por que o SDK, e não o `claude -p` sem interface, como o CampsCast. O SDK é esse mesmo modo por baixo: ele abre o Claude Code em `-p`, conversando em JSON, e dá em Python os ganchos, as ferramentas nossas no mesmo processo, os passos tipados e o Claude Code preso numa versão. A `HandsPort` deixa trocar para o `-p` puro, se o SDK der trabalho;*
- *se o Codex precisa da versão de linha de comando. O app do Codex já traz a CLI (§"O que o levantamento mostrou"); o M26 não a usa, e o M27 a liga.*

**Pronto quando:**
- **As duas mãos:** um pedido pode ser feito pelo nosso harness ou pelo Claude Code, escolhido na prancheta junto com o modelo. Dali em diante o caminho é o mesmo do M25: o patch, a revisão da oficina, o PR, o revisor e você.
- **O isolamento:** a sessão do Claude Code só escreve no espaço do pedido. Ela não lê o `.env`, o `privado/`, o `data/` nem a sua pasta `~/.claude`, e só fala com a rede pela nossa porta. A chave da API nunca entra no processo do dev.
- **O custo à vista:** cada chamada do Claude Code ao modelo passa pela guarda, como as do nosso harness. O teto do pedido e o do dia param a sessão.
- **A gravação:** cada sessão fica registrada, com os passos na tela e na linha do tempo, o fato do fim da sessão e a fita para os testes.
- **A comparação:** três pedidos do mesmo tipo, cada um feito pelas duas mãos com o mesmo modelo, com o custo, o tempo, os passos e as rodadas até o aceite lado a lado, num relatório.
- **A criação:**
  - você pede o conector do Codex no quadro;
  - o dev o faz pelo Claude Code e entrega por PR;
  - você mescla, e o escritório troca de versão;
  - o M27 o usa.
- **O mundo intacto:** as fazendas, o soak do escritório e o replay seguem iguais. O CI continua sem chamar a API.

## O que o levantamento mostrou

- **A oficina** (ADR-0080) já é o lugar certo:
  - um clone do repositório por pedido, em `data/oficina/<mundo>/<pedido>/`, sem o `.env`, o `data/` e o `privado/`;
  - os testes e os robôs rodam sob o `sandbox-exec` do macOS: sem rede, escrita só no espaço e um ambiente sem segredos.
- **O nosso harness** é a `WorkSession` da mente:
  - até 60 passos pela porta de modelo;
  - cada chamada vira um `llm.call.completed` com o pedido, e a guarda soma o gasto por pedido e por dia;
  - o teto para a sessão entre um passo e outro.
- **A entrega não depende de quem programou:** o patch do espaço, a revisão, o depósito e o publicador. Trocar a mão não muda nada daí para a frente.
- **O briefing existe e ninguém o usa:** o robô `tools/robos/briefing.py` entrou pelo PR #2, mas a sessão ainda abre com o pedido cru e o bloco da memória.
- **O modelo por pedido ficou para trás:** a decisão 14 do M25 (o Opus 5.5 escolhido na prancheta quando o pedido mexe na arquitetura) não foi construída. O modelo é um só por mundo (`minds.camps.model`), e o pedido não tem o campo.
- **O Claude Agent SDK** (a documentação de 21/nov):
  - o pacote `claude-agent-sdk` traz o próprio Claude Code dentro. Não usaríamos o seu, de `/usr/local/bin`;
  - as opções que importam aqui:
    - a pasta (`cwd`) e o ambiente (`env`);
    - o modelo e o esforço;
    - as ferramentas permitidas e as proibidas;
    - os ganchos por ferramenta (`hooks`);
    - as ferramentas nossas, no mesmo processo (`mcp_servers`);
    - `max_turns` e `max_budget_usd`;
    - de onde ler as configurações (`setting_sources`);
  - o fim da sessão traz o custo (`total_cost_usd`, uma estimativa do próprio SDK), os tokens, as voltas e o motivo do fim (`error_max_turns`, `error_max_budget_usd`);
  - `ANTHROPIC_BASE_URL` manda as chamadas ao modelo para um endereço nosso;
  - **o sandbox do Claude Code cobre só o Bash.** O `Read`, o `Write` e o `Edit` seguem as regras de permissão. Sem nada que os pare, eles leem qualquer arquivo da máquina.
- **Os termos:** a documentação pede chave de API para produtos feitos com o SDK, e é como já usamos a API. Pelo artigo de suporte (atualizado em 7/out), os planos Max, Ultra e Team passaram a incluir créditos mensais de API, que cobrem o SDK quando ele roda com uma chave da organização da Console ligada ao plano. Vale você conferir se a sua Console tem esses créditos.
- **O Codex:** o app do Codex traz a CLI dentro (`/Applications/Codex.app/Contents/Resources/codex-cli/bin/codex`, a 0.171.0-alpha.13 em 22/nov), fora do `PATH`. O `codex exec --json` imprime os eventos em JSONL, o formato que o conector vai ler. A pasta `~/.codex` é a do app, com o login; não a abri.

## 1. As mãos

- **O dev continua com uma mente só:** a rotina e a conversa, pela porta de modelo, decidem no mundo. É o que escolhe o pedido, senta, fala com você e entrega.
- **As mãos** são quem programa no espaço do pedido. Viram uma porta (`HandsPort`), com dois adaptadores:
  - o nosso harness, que é a `WorkSession` de hoje, só mudando de lugar;
  - o Claude Code, pelo SDK.

  O M27 pluga o Codex e o Antigravity na mesma porta.
- **O que a porta recebe:**
  - o espaço do pedido;
  - o texto que abre a sessão (o briefing);
  - o modelo e o esforço;
  - os tetos;
  - as duas ferramentas do mundo: chamar um robô e anotar na memória.
- **O que ela devolve:** se a sessão chegou ao fim, o resumo do dev, as voltas, os passos, o custo e o motivo do fim.
- **O fim de uma sessão do Claude Code** é a resposta final dele: o texto vira o resumo da entrega, como o `resumo` do nosso `pronto`. Daí o patch segue para a revisão, como hoje.
- **Quem escolhe as mãos é o pedido:**
  - a prancheta ganha "quem programa" (o nosso harness ou o Claude Code) e "o modelo";
  - sem escolha, vale o padrão do mundo (`minds.camps.hands` e `model`);
  - isso entrega também a decisão 14 do M25.
- **Os dois cérebros** (ADR-0077, decisão 8): enquanto trabalha num pedido, o dev conversa com o modelo do pedido. A rotina não chama modelo.

## 2. O Claude Code na oficina

- **As ferramentas dele:**
  - `Read`, `Write`, `Edit`, `Glob`, `Grep` e `TodoWrite`;
  - o `Bash`, com o isolamento da §3;
  - duas nossas, servidas no mesmo processo pelo SDK:
    - `chamar_robo`: a bancada anima, e o `workshop.robot_*` sai como hoje;
    - `anotar`: a memória.
- **Ficam de fora:**
  - a web (`WebFetch`, `WebSearch`). Não há rede além do modelo até o computador do M28;
  - os servidores MCP de fora;
  - os subagentes. Ficam para a ideia dos mini-robôs, no `futuro.md`;
  - as suas configurações. Com `setting_sources` só no projeto, ele lê o `CLAUDE.md` do clone, e o `HOME` aponta para uma pasta dentro do espaço. Assim ele não vê a sua memória, os seus plugins nem o seu login.
- **Ninguém aprova nada no meio:** não há humano na sessão. Um gancho antes de cada ferramenta decide na hora, e uma recusa volta ao modelo com o motivo, como as recusas da oficina.
- **As instruções:**
  - as do próprio Claude Code;
  - o cartão do dev;
  - as regras do escritório:
    - a constituição;
    - não rodar alvos que chamam a API;
    - terminar com um resumo do que fez.

## 3. O isolamento, em três camadas

O nosso harness só faz o que as oito ferramentas deixam. O Claude Code roda comandos, então o cercado precisa ser outro.

1. **O nosso `sandbox-exec` em volta do Claude Code inteiro,** como nos testes de hoje:
   - escrita só no espaço e no temporário dele;
   - leitura negada nos lugares com segredo: o `.env` e o `privado/` do repositório de verdade, o `data/`, o `~/.ssh`, o `~/.claude`, o `~/.codex` e as chaves do sistema;
   - rede só para a nossa porta, em `127.0.0.1`.
2. **A chave fica fora do processo do dev:**
   - o Claude Code recebe `ANTHROPIC_BASE_URL` apontando para a nossa porta (§4) e uma chave falsa, que só vale para aquela sessão;
   - a porta põe a chave de verdade e repassa ao modelo;
   - nem um `env` no Bash mostra a chave.
3. **O gancho de cada ferramenta:**
   - o `Read`, o `Write`, o `Edit`, o `Glob` e o `Grep` só aceitam caminhos dentro do espaço, inclusive por link simbólico, como as nossas oito;
   - o `Bash` recusa o que não cabe na oficina: `git push`, os alvos do `make` que chamam a API, ferramentas de rede.

**Junto disso:**
- o sandbox do próprio Claude Code no `Bash`, se ele funcionar dentro do nosso (é a primeira coisa a conferir, §9);
- a revisão da entrega ganha uma checagem: nenhum formato de chave (`sk-ant-`, `sk-or-`) no patch;
- a telemetria e a atualização automática do Claude Code ficam desligadas, porque ele só alcança a nossa porta.

## 4. A porta das mãos: o modelo passa por nós

**O problema:** a ADR-0058 diz que nenhum modelo é chamado fora da porta de modelo. Com o Claude Code, quem chama o modelo é ele.

**A proposta:** uma porta local, em `libs/adapters`, que fica entre o Claude Code e a API:
- **Ela recebe** cada chamada do Claude Code, põe a chave e a repassa à Anthropic. A resposta volta como veio, em streaming.
- **Ela mede:**
  - no fim de cada resposta, ela lê os tokens e publica o `llm.call.completed`, com o pedido, o modelo, o custo pela nossa tabela de preços e um campo novo, `harness`;
  - a guarda soma por pedido e por dia como hoje, sem mudar.
- **Ela para:** com o teto do pedido ou do dia estourado, ela recusa a chamada seguinte com um erro claro, e a sessão termina.
- **Ela grava:** cada chamada vai para uma fita, o pedido e a resposta. Nos testes, a porta responde da fita, na ordem, sem a API. O CI roda uma sessão inteira do Claude Code sem gastar nada, como já faz com a fita do escritório.

**Os tetos da própria sessão,** além da guarda:
- `max_turns`;
- `max_budget_usd`, que é a estimativa do SDK;
- um limite de tempo de relógio.

No fim de cada sessão, o custo da porta é comparado com a estimativa do SDK. Uma diferença grande vira um aviso, porque quer dizer que a nossa tabela de preços está errada.

**Onde roda:** dentro do controlador do dev, numa porta efêmera por sessão. Não é um serviço novo no Procfile.

**Pede uma ADR,** que complementa a ADR-0058: a porta das mãos é a borda do modelo quando quem chama é um harness de fora.

## 5. Na tela, no diário e na memória

- **Os passos:** cada ferramenta do Claude Code vira um passo na tela e na linha do tempo, com o nome que ele usa (`Bash`, `Edit`). O `workshop.step.v1` só aceita os oito nomes do nosso harness. A proposta é o `workshop.step.v2`, com o nome livre e o campo `harness`. A tela lê os dois, para os dias antigos.
- **O fim da sessão:** um fato novo, `workshop.session_finished.v1`, para as duas mãos:
  - o pedido, as mãos e o modelo;
  - as voltas, os passos e o motivo do fim;
  - o custo e o tempo.

  É a fonte do relatório da comparação.
- **O computador da mesa** mostra qual ferramenta está aberta. O chip do dev diz "programando · Claude Code · Opus 5.5". O painel do elenco continua no M27.
- **A memória:** a linha da sessão diz que mãos ele usou e quanto custou.
- **A conversa completa** da sessão (o que o SDK devolve) fica em `data/oficina/<mundo>/<pedido>/sessao-N.jsonl`, fora do git, para a análise e para o post.

## 6. O briefing abre a sessão

É a criação do M25 em uso, como pede a régua do plano macro.

- **O controlador escreve dois arquivos** em `.oficina/`, a parte do espaço que fica fora do diff:
  - o `pedido.md`, com o título, o que fazer, o aceite e a devolução;
  - o `notas.md`, com o bloco da memória.
- **Ele roda o robô:** `python -m tools.robos.briefing`, pela bancada, que anima "o briefing trabalhando".
- **O texto do robô** é a primeira mensagem da sessão, **nas duas mãos**, para a comparação ser justa.
- **Se o robô falhar,** a sessão abre como hoje, e fica um aviso.

## 7. A comparação

É o critério do marco: o mesmo pedido, nas duas mãos.

- **O mesmo modelo nas duas mãos,** para separar o efeito do harness: o **Opus 5.5** (US$ 4 / 20 por milhão de tokens, entrada / saída), como a decisão 15 do M25 previu para o Claude Code.
- **Três pedidos do mesmo tipo:** robôs pequenos em `tools/robos/`, tamanho P ou M, com teste de aceite. Os textos prontos para colar vêm na parte 4. As propostas:
  - **o contador:** as linhas de código e de teste por pasta;
  - **o briefing com a história:** os últimos commits dos arquivos que o briefing cita;
  - **o testador que aponta:** os arquivos mudados sem nenhum teste que os mencione.
- **Cada pedido roda duas vezes,** uma em cada mão, num sandbox, a partir do mesmo commit e com os mesmos tetos. A ordem alterna, para uma mão não aprender com a outra pela memória: a memória do dev começa limpa em cada corrida.
- **Depois, o Fable 5.2** (US$ 8 / 40) no Claude Code, num dos três: o segundo do índice no Claude Code.
- **As medidas** (ADR-0077, decisão 13):
  - o tempo até a entrega;
  - o custo;
  - as voltas e os passos;
  - as chamadas ao testador;
  - a revisão e o CI verdes na primeira;
  - as rodadas até o seu aceite;
  - o tamanho do patch.
- **O relatório:** `docs/arena/m26-as-maos.md`, por `make maos-relatorio`, lido dos fatos. Ele diz também o que difere além do harness, como o `Bash`.

## 8. A criação: o conector do Codex

É a criação do plano macro (§4), usada no M27.

- **O pedido,** escrito por você no quadro, com o Claude Code e o Opus 5.5 na prancheta. Os textos, prontos para colar:
  - **Título:** `Conector do Codex`
  - **O que fazer:** `As mãos do Codex para a oficina: um adaptador em libs/adapters/hands_codex.py que implementa a HandsPort. Ele roda "codex exec --json" no espaço do pedido, com o briefing como entrada; transforma cada evento JSONL num passo (o nome da ferramenta, o caminho quando houver, ok ou não); soma os tokens de uso e calcula o custo pela tabela de preços; para a sessão no limite de tempo ou de voltas; e devolve o resumo final. O formato dos eventos está no exemplo tests/fixtures/codex/exemplo.jsonl. O processo do Codex recebe um ambiente limpo, sem nenhuma chave.`
  - **Teste de aceite:** `Com um codex falso (um script em tests/fixtures/codex que imprime o exemplo), uma sessão vira os passos na ordem, o custo sai dos tokens pela tabela, uma sessão que passa do limite de tempo é parada, e o ambiente do processo não tem nenhuma variável com KEY ou TOKEN. Os testes ficam em libs/adapters/tests e passam no make check.`
  - **Tamanho:** `M`
- **O que nós fazemos antes:** o `exemplo.jsonl`, montado da documentação da OpenAI do dia, com a fonte. O dev não tem rede nem o Codex. Ele escreve contra o exemplo, e o M27 liga o Codex de verdade, com a prova de conformidade.
- **O caminho inteiro é o teste do marco:**
  - o dev trabalha pelo Claude Code;
  - o testador roda, e o publicador abre o PR;
  - o revisor comenta, e você mescla;
  - o supervisor troca a versão;
  - o dev lembra que fez o conector, e com que mãos.

## 9. Ordem do trabalho, em seis partes

1. **A porta e o cercado, sem API:**
   - instalar o SDK (com o seu ok) e conferir:
     - se o nosso `sandbox-exec` deixa o Claude Code rodar;
     - se o sandbox dele funciona dentro do nosso;
     - se ele vive com a rede só até a nossa porta;
   - a porta das mãos, com um modelo falso que responde respostas roteirizadas;
   - os ganchos;
   - o nosso harness atrás da `HandsPort`, sem mudar o comportamento;
   - o primeiro teste de ponta a ponta: o Claude Code de verdade, contra o modelo falso, num espaço de teste. Custa nada.
2. **A primeira sessão de verdade,** em centavos:
   - a prova de conformidade (ADR-0077, decisão 11) do Claude Code com o Opus 5.5: os dois pedidos curtos no repositório de exemplo, `tests/fixtures/oficina`;
   - a fita gravada.
3. **O pedido escolhe as mãos:**
   - a prancheta e os contratos;
   - os passos na tela e o fato do fim;
   - a memória;
   - o briefing abrindo a sessão;
   - a fita do escritório gravada de novo, uns US$ 0,06.
4. **A comparação,** paga, um passo por vez: os três pedidos nas duas mãos, o Fable 5.2 num deles, e o relatório.
5. **A criação:** o conector do Codex, por PR, até a troca de versão.
6. **O fechamento:** a ADR, a bíblia, o diário, os custos e o README.

## 10. Contratos

- **O pedido com as mãos e o modelo:** os campos opcionais `harness` e `model` no comando de escrever o pedido e no `office.ticket.created.v1`.
- **`workshop.step.v2`:** o nome da ferramenta livre, mais o campo `harness`. A v1 continua para os dias antigos.
- **`workshop.session_finished.v1`,** novo.
- **`llm.call.completed.v1`:** o campo opcional `harness`.
- **As três contagens de tipos** nos testes de contrato.

## 11. Testes do marco

- **Unidade:**
  - os ganchos: um caminho fora do espaço, um link simbólico e um comando proibido são recusados;
  - a porta das mãos com o modelo falso:
    - a chave de verdade só na chamada de fora;
    - o custo pela tabela;
    - o teto que recusa;
    - a fita que grava e responde;
  - as duas mãos atrás da porta: o mesmo patch, a mesma entrega;
  - o briefing na abertura, e a volta ao pedido cru se ele falhar.
- **O cercado, no macOS:** uma sessão do Claude Code, contra o modelo falso, que tenta ler o `.env`, escrever fora do espaço e abrir a rede, e falha nas três.
- **De ponta a ponta, sem API:** a manhã do escritório com um pedido feito pelo Claude Code e o modelo falso, do quadro ao PR do GitHub falso. O CI roda isso no Linux, onde o `sandbox-exec` não existe. Lá vale o gancho e a rede pela nossa porta.
- **No navegador:** a prancheta com as mãos e o modelo, e o chip "Claude Code".
- **O mundo intacto:** os soaks das fazendas e do escritório, e o replay.

## 12. Custo

- **API, em passos pagos, cada um com o seu ok:**
  - a prova de conformidade do Claude Code: US$ 0,50 a 1,50;
  - a comparação, com o Opus 5.5 (três pedidos, duas mãos): US$ 3 a 12. Uma sessão do Claude Code deve custar de US$ 0,50 a 3, porque as instruções e as ferramentas dele são longas, mas vão para o cache;
  - o Fable 5.2 num pedido: US$ 1 a 4;
  - a criação, com o revisor: US$ 2 a 6;
  - as fitas: centavos;
  - **total previsto:** US$ 7 a 25. O plano macro previa US$ 40 a 80.
- **A proposta:** um teto de US$ 30 para o marco. Os tetos do escritório ficam assim: US$ 5 por pedido e US$ 10 por dia, contra US$ 1 e 3 hoje. Os da sessão: 80 voltas, US$ 4 e 45 minutos.
- **O Claude Code** para construir (as horas): um marco do tamanho do M25, sem a tela retrô.
- **O pacote novo:** o `claude-agent-sdk`, com o Claude Code dentro, preso numa versão. A troca de versão do SDK passa pela prova de conformidade.

## 13. Riscos

- **O Claude Code lê ou escreve fora do espaço,** porque as ferramentas de arquivo ficam fora do sandbox dele. *A resposta:* o nosso `sandbox-exec` e o gancho, conferidos por um teste que tenta.
- **A chave vaza.** *A resposta:* ela nunca entra no processo do dev, e a revisão procura o formato de chave no patch.
- **Um sandbox dentro do outro não funciona no macOS.** *A resposta:* a parte 1 confere primeiro. Se não funcionar, fica só o nosso, que já cobre o `Bash` e é mais estrito.
- **A fita não reproduz:** o Claude Code faz chamadas auxiliares, e as instruções dele mudam com a data. *A resposta:* nos testes, a porta responde por ordem e por modelo, sem o hash. O CI usa o modelo falso roteirizado. A fita de verdade é o registro.
- **O Claude Code muda debaixo de nós.** *A resposta:* o SDK preso numa versão, a atualização automática desligada e a prova de conformidade a cada troca.
- **O custo dispara.** *A resposta:* a porta recusa acima do teto, mais o `max_budget_usd`, as voltas e o relógio.
- **A comparação engana,** como o Astra no M21. *A resposta:* o mesmo modelo, o mesmo briefing, o mesmo commit e os mesmos tetos, a leitura das conversas antes de concluir, e o relatório dizendo o que difere.
- **Os termos.** *A resposta:* a chave de API, como a documentação pede. Nenhum login de assinatura.

## 14. Decisões

**As mãos**

1. **As mãos como uma porta** (`HandsPort`), com o nosso harness e o Claude Code como dois adaptadores. Do patch em diante, nada muda. *Recomendação: sim.*
2. **O pacote `claude-agent-sdk`,** preso numa versão, só em `libs/adapters`, com o Claude Code que vem dentro dele, e não o seu. *Recomendação: sim. É uma instalação nova, então espera o seu ok.*
3. **Quem escolhe as mãos e o modelo é o pedido,** na prancheta, com o padrão do mundo. Entra também o modelo por pedido da decisão 14 do M25. *Recomendação: sim. O padrão do escritório vivo fica no nosso harness com o Sonnet 5.5 até o relatório da comparação, e aí você decide.*
4. **O briefing abre toda sessão,** nas duas mãos. *Recomendação: sim.*

**O cercado e o custo**

5. **As ferramentas do Claude Code na oficina:**
   - `Read`, `Write`, `Edit`, `Glob`, `Grep`, `TodoWrite` e `Bash`;
   - as nossas `chamar_robo` e `anotar`;
   - sem a web, os MCPs de fora, os subagentes e as suas configurações.

   *Recomendação: sim. Os subagentes ficam para os mini-robôs.*
6. **O isolamento em três camadas** (§3): o nosso `sandbox-exec` em volta de tudo, a chave fora do processo e o gancho por ferramenta. *Recomendação: sim.*
7. **A porta das mãos** (§4): o Claude Code chama o modelo pela nossa porta, que põe a chave, mede pela guarda, recusa acima do teto e grava a fita. Pede uma ADR que complementa a ADR-0058. *Recomendação: sim.*
8. **Os tetos:**
   - por sessão: 80 voltas, US$ 4 e 45 minutos;
   - no escritório: US$ 5 por pedido e US$ 10 por dia.

   *Recomendação: sim.*

**A gravação e a medida**

9. **Na tela e no diário:**
   - o `workshop.step.v2`, com o nome da ferramenta de cada harness;
   - o fato `workshop.session_finished.v1`;
   - o chip com as mãos e o modelo;
   - a conversa da sessão guardada fora do git.

   *Recomendação: sim.*
10. **A comparação:**
    - três pedidos de robô, nas duas mãos, com o Opus 5.5;
    - o Fable 5.2 no Claude Code num deles;
    - no sandbox, do mesmo commit;
    - o relatório em `docs/arena/`.

    *Recomendação: sim.*

**A criação e o orçamento**

11. **A criação é o conector do Codex,** feito pelo dev com o Claude Code e o Opus 5.5, contra um exemplo do formato que nós pomos antes. Os textos do pedido estão na §8. *Recomendação: sim.*
12. **O orçamento do M26:** US$ 30, cada passo pago com o seu ok. *Recomendação: sim.*

## Fontes

- O Claude Agent SDK: a [referência do Python](https://code.claude.com/docs/en/agent-sdk/python), o [acompanhamento de custo](https://code.claude.com/docs/en/agent-sdk/cost-tracking), a [visão geral](https://code.claude.com/docs/en/agent-sdk/overview) e a [implantação segura](https://code.claude.com/docs/en/agent-sdk/secure-deployment), lidos em 21/nov/2026.
- O sandbox do Claude Code: [Sandboxing](https://code.claude.com/docs/en/sandboxing).
- Os termos: [Use the Claude Agent SDK with your Claude plan](https://support.claude.com/en/articles/15036540) e [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance).
