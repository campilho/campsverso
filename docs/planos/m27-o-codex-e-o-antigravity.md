# Plano do M27 — o Codex, o Antigravity, o Kenji e a Lívia

*Proposto em 22/nov/2026, depois do bloco das telas do Claude Design (ADR-0092), e revisto no mesmo dia com o rumo do usuário: o Kenji e a Lívia entram já, um dev por laboratório; a conversa passa a ter ações; o tamanho do pedido sai da tela. **Aprovado em 22/nov/2026 (ADR-0093).** É o terceiro degrau da escada de ferramentas do dev (o plano macro da v0.4, §4; ADR-0077): o nosso harness pela API (M24), o Claude Code (M26) e agora os harnesses da OpenAI e do Google, cada um com o modelo do próprio laboratório.*

> **Revisão de 23/nov (a emenda da ADR-0093, decisões 15 a 20).** Onde este bloco e o texto abaixo divergirem, vale o bloco.
> - **O M27 tem dois devs, o Tiago e o Kenji.** A Lívia entra no M28, com o Antigravity dentro do computador dela. O `agy` sorteia uma porta local para o servidor de linguagem dele, e o `sandbox-exec` não a isola (o ensaio de 23/nov). O conector e os testes do Antigravity ficam prontos.
> - **A comparação é entre sistemas, o harness com o modelo dele.** Em processo, os três pedidos do M26 pelo Codex com o Astra, ao lado do Claude Code com o Opus do M26. Ao vivo, o "Para todos" com o Tiago e o Kenji. O nosso harness sai da comparação em processo (o §6 abaixo).
> - **O dev e o sistema são independentes** (o §9 abaixo muda):
>   - o catálogo dos sistemas fica no `office.yaml`, cada harness com os modelos da língua dele;
>   - cada dev tem a mente e o sistema padrão em campos separados no mundo;
>   - a prancheta escolhe qualquer sistema;
>   - um teste roda cada dev com cada sistema.
>
>   O Tiago com o Codex, ou o Kenji com o Claude Code, é uma escolha, sem código.
> - **O mundo 03 nasce com o Tiago e o Kenji.** A receita do computador sai de um "Para todos" com os dois.
> - **O Codex vem do pacote completo** (`codex-package`), com o modo código.

**Pronto quando:**
- **Três devs, um por laboratório,** e "o dev é o modelo" (ADR-0077, decisão 8):

  | Dev | A mente | As mãos |
  |---|---|---|
  | o Tiago | o Claude Opus 5.5 | o Claude Code |
  | o Kenji | o GPT-6.2 Astra | o Codex |
  | a Lívia | o Gemini 4 Neon | o Antigravity CLI (`agy`) |
- **As mãos novas passam na prova de conformidade antes de entrar** (ADR-0077, decisão 11).
- **O modelo de cada mão passa pela nossa porta,** que aprende a falar a API da OpenAI e a do Google: ela mede cada chamada e põe a chave de verdade só do lado de fora.
- **A prancheta:**
  - o "Para quem" é opcional: sem ele, pega quem estiver livre;
  - o "Para todos" põe o mesmo pedido para os três, numa comparação;
  - o tamanho do pedido sai da tela, e a faixa da ficha ganha a cor do dev.
- **Os relatórios:**
  - o "Para todos" compara o resultado final dos três;
  - a comparação em processo separa o efeito do modelo e o do harness.
- **A conversa tem ações:** convocado, o dev vai para casa quando o gerente diz que pode ir; pode fazer uma pausa quando o gerente o chama.
- **A criação:** a receita do computador do dev, que o M28 usa para montar a máquina dele.
- **O que o M26 deixou para o M27 está resolvido:**
  - os pontos do revisor no conector do Codex;
  - o DNS no sandbox;
  - o `ruff` no espaço;
  - o texto do modelo entre os passos;
  - a devolução que troca quem programa.
- **O mundo intacto:**
  - o kernel e as fazendas não mudam;
  - o `make check` e o `make ui-e2e` verdes;
  - o escritório vivo vai para o mundo 03, com os três devs.

## O que o levantamento mostrou

**O Codex** (a página do modo não interativo e o repositório `openai/codex`, lidos em 22/nov):
- **O formato:** `codex exec --json` roda um pedido e imprime um evento por linha. O conector do M26 já lê esse formato (`hands_codex.py`), escrito contra um exemplo montado à mão.
- **A chave:** a variável `CODEX_API_KEY` para uma execução só, ou o `codex login --with-api-key`.
- **O modelo:** um provedor próprio no `config.toml` (`model_provider`, `base_url`, `env_key`) aponta o Codex para qualquer endpoint compatível com a API da OpenAI. É assim que ele chega à nossa porta.
- **O sandbox e as aprovações:** `-s` (`read-only`, `workspace-write`, `danger-full-access`) e `-a never`. No Mac, o sandbox dele é o Seatbelt, o mesmo `sandbox-exec` que usamos em volta das mãos.
- **A OpenRouter:** há um relato de erro no `exec --json` por ela (a issue 12114 do `openai/codex`).

**O Antigravity CLI** (a documentação oficial do modo sem interface e da autenticação, lida em 22/nov):
- **O formato:** `agy -p "<pedido>"` roda e sai. O `--output-format stream-json` imprime um evento por linha:
  - `init`: a pasta, as ferramentas e o modo de permissão;
  - `step_update`: cada passo, com o `step_type`, e em `tool_info` o nome, os parâmetros, a saída e o erro;
  - `result`: a resposta, o estado e os tokens, sem o custo.
- **O tempo e o modelo:** o `--print-timeout` limita o tempo; o `--model` e o `--effort` escolhem o modelo; o `agy models` lista os slugs, como `gemini-4-neon-high`.
- **A chave:** o `GEMINI_API_KEY`, junto com `"modelProvider": "gemini"` no `settings.json` dele.
- **O modelo:** o `GOOGLE_GEMINI_BASE_URL` aponta para um endpoint compatível com o Gemini. É assim que ele chega à nossa porta.
- **As permissões:** sem interface, o que pediria aprovação é negado em silêncio. Um relato diz que as regras de `permissions.allow` não valem nesse modo (a issue 548 do `antigravity-cli`). O `--dangerously-skip-permissions` aprova tudo.
- **A instalação:** por um script (`curl … /cli/install.sh | bash`), sem pacote npm. O binário fica em `~/.local/bin/agy`.

**O escritório hoje:**
- o elenco tem um dev só, e várias regras contam com isso. A convocação, por exemplo, usa "o único dev do elenco" quando o gerente não diz qual;
- a prancheta oferece `hands: [api, claude_code]`;
- o codehost tem um prefixo de ramo por mundo (`dev/tiago/`);
- a tabela de preços já tem o GPT-6.2 Astra e o Gemini 4 Neon, pela OpenRouter, e o revisor de outra família usa os dois por ali;
- a arte do Kenji e da Lívia já está no repositório, com os bustos;
- **na conversa, a mente do dev só tem palavras.** Em 22/nov, o Tiago topou jogar videogame e disse que ia para casa, e não fez nenhum dos dois.

**Os saldos em 22/nov:** US$ 69,67 na OpenRouter e US$ 72,97 na Claude Platform (`docs/custos/creditos.csv`).

## Primeira metade: as mãos

### 1. As mãos novas

| Mãos | Harness | Modelo | Como chega ao modelo |
|---|---|---|---|
| `codex` | o Codex (`codex exec --json`) | o GPT-6.2 Astra | um provedor próprio no `config.toml`, com o `base_url` na nossa porta |
| `antigravity` | o Antigravity CLI (`agy -p … --output-format stream-json`) | o Gemini 4 Neon, no esforço `high` | o `GOOGLE_GEMINI_BASE_URL` na nossa porta |

**As mãos falam com a API do próprio laboratório, e não com a OpenRouter.** A tradução custa: o Haiku pela OpenRouter custou o dobro, porque perdeu o cache. O Antigravity, além disso, só fala a língua do Gemini. As chaves das mãos são novas e do usuário, uma da OpenAI e uma do Google AI Studio, no `.env` e com o limite de gasto no painel de cada uma. Eu não crio conta nem chave.

**As mentes do Kenji e da Lívia vão pela OpenRouter,** como o revisor: a porta de modelo já fala com ela, e o saldo de lá cobre as mentes.

### 2. A porta das mãos fala três línguas

A porta das mãos do M26 recebe as chamadas do Claude Code, põe a chave e repassa à Anthropic. Ela passa a falar também:
- **a API da OpenAI (Responses),** que o Codex usa: o `POST /v1/responses` em streaming. Os tokens vêm no evento final, com os do cache e os do raciocínio;
- **a API do Gemini,** que o Antigravity usa: o `streamGenerateContent`. Os tokens vêm no `usageMetadata`, com os do cache e os do pensamento.

O resto é como já é:
- **ela mede:** o `llm.call.completed` com o `harness`, o custo pela nossa tabela, e a guarda soma por pedido e por dia;
- **ela para:** com o teto estourado, ela recusa a chamada seguinte;
- **ela grava:** as fitas do CI, que nunca chama a API;
- **a chave de verdade fica só nela:** o harness recebe uma chave falsa, que só vale para a sessão.

São os adaptadores diretos da OpenAI e do Google que o `futuro.md` guardava para o M27, na borda das mãos. **Pede uma ADR** que complementa a ADR-0089.

### 3. O isolamento

É o mesmo cercado do Claude Code (ADR-0089), com o que muda para os de fora:
1. **O nosso `sandbox-exec` em volta do processo inteiro:**
   - a escrita só no espaço do pedido;
   - a leitura negada nos lugares com segredo;
   - a rede só para a nossa porta.

   **O sandbox de cada harness fica desligado:**
   - o Codex roda com `-s danger-full-access` e `-a never`;
   - o `agy` roda sem `--sandbox` e com `--dangerously-skip-permissions`.

   No Mac, um Seatbelt dentro do outro não funciona; é a primeira conferência da §11. O nosso é a cerca.
2. **O `HOME` de cada sessão fica dentro do espaço,** com o `~/.codex/config.toml` e o `~/.gemini/antigravity-cli/settings.json` da sessão, o provedor na nossa porta. Eles não veem as suas configurações nem os seus logins.
3. **Não há gancho por ferramenta, como no Claude Code.** Seguram o cercado e a revisão da entrega:
   - a constituição;
   - os formatos de chave (`sk-`, `AIza`) fora do patch.

   No Linux, onde o `sandbox-exec` não existe, os dois ficam desligados, como o Claude Code hoje.
4. **O que o M26 deixou:**
   - o DNS no sandbox: fechar o `/var/run/mDNSResponder`, se nenhuma das mãos precisar dele;
   - o `ruff` no espaço: as mãos recebem a configuração dele, como o testador.

### 4. O Codex de verdade

- **A fita:** a de uma sessão de verdade, gravada na prova de conformidade, no lugar do exemplo montado à mão.
- **Os pontos do revisor no PR #4:**
  - um `PATH` confiável, à parte, para lançar o Codex;
  - o limite de voltas conferido também numa mensagem intermediária;
  - o teto em dólares conferido pela porta, a cada chamada.

### 5. O Antigravity

Um conector novo, `hands_antigravity.py`, como o do Codex:
- **o processo:** o `agy -p` na pasta do espaço, com o briefing, o modelo, o esforço e o `--print-timeout`;
- **os passos:** cada `step_update` de ferramenta concluída vira um passo na tela, com o caminho quando os parâmetros trouxerem um. Os nomes dos parâmetros das ferramentas de arquivo saem da primeira sessão de verdade;
- **o resumo da entrega:** a `response` do `result`;
- **as paradas:** o limite de tempo, o de passos, o teto da sessão e o pedido do mundo, como nos outros.

### 6. A comparação em processo: o modelo ou o harness

Os mesmos três pedidos de robô da comparação do M26 (`make maos`), em quatro combinações novas:

| | O harness do laboratório | O nosso harness |
|---|---|---|
| **GPT-6.2 Astra** | Codex | `api` |
| **Gemini 4 Neon** | Antigravity | `api` |

As duas combinações do Claude são as do M26, já medidas. A coluna da esquerda contra a da direita é o efeito do harness; uma linha contra a outra, o do modelo. O relatório vai para `docs/arena/m27-as-maos-de-fora.md`.

## Segunda metade: o elenco

### 7. O Kenji e a Lívia

- **O elenco** (`escritorio.yaml`): o Kenji e a Lívia, com o papel de dev, as duas mesas de baixo (`dono`), o mesmo expediente e a convocação de cada um.
- **A arte:** as folhas do Kenji e da Lívia, com as mesmas animações, e as colunas deles nos retratos.
- **A mente de cada um:**
  - um cartão próprio ("Você é o Kenji", "Você é a Lívia"), com as mesmas regras do escritório;
  - a memória de cada um.

  Antes de entrar, a mente passa na prova de conformidade com o modelo dela. A da Lívia é a primeira com o Gemini 4 Neon no escritório.
- **Um mundo novo, o 03.** O elenco nasce com o mundo, e o kernel não acrescenta avatares num mundo retomado (o `futuro.md`, "os sistemas do começo da sessão"). O quadro recomeça no pedido 1, e o mundo 02 fica no arquivo.
- **O que conta com um dev só passa a ter o dev dito:**
  - a convocação e a dispensa pelo chip de cada um;
  - o vigia e as falas;
  - o codehost, com um ramo por dev: `dev/<dev>/pedido-N`;
  - as permissões do NATS de cada avatar.

### 8. O quadro com três devs

- **"Para quem" na prancheta,** opcional: o Tiago, o Kenji, a Lívia ou quem estiver livre. Vai num campo opcional `assignee` no `office.ticket.created.v1`. Um dev só pega o que é dele ou o que é de quem estiver livre.
- **"Para todos":** o gerente escreve uma vez, e o kernel cria uma ficha por dev, com o mesmo texto e um campo opcional `group` que as liga. O quadro mostra as três juntas.
- **O relatório do "Para todos"** (`make comparacao GRUPO=…`): as três entregas lado a lado, lidas dos fatos:
  - o PR;
  - o CI;
  - o teste de aceite;
  - o custo da mente e o das mãos;
  - o tempo;
  - os passos;
  - as devoluções.

  É a comparação do resultado final, com o modelo e o harness juntos. A §6 separa os dois.

### 9. A prancheta e as fichas

- **O tamanho sai da tela.** A prancheta não pergunta mais, e manda "M": o campo é obrigatório no contrato, e o script de reserva usa a duração dele. A ficha quadrada e a ficha aberta perdem o quadradinho do tamanho.
- **A faixa da ficha é a cor do dev:** uma cor para cada um, e neutra para quem estiver livre.
- **As mãos e o modelo seguem o dev:** no Kenji, o Codex ou o nosso harness com os modelos da OpenAI; na Lívia, o Antigravity ou o nosso harness com os do Google; no Tiago, como hoje. O kernel confere o par.
- **A devolução troca quem programa:** campos opcionais `harness` e `model` no `office.ticket.returned.v2`.
- **O texto do modelo entre os passos:** um campo opcional `note` no `workshop.step.v2`, até 200 letras do que o modelo escreveu antes do passo. A tela do dev o mostra como um comentário de shell, apagado (`briefing-tela-3.md`, §7).
- **A tela:**
  - os chips dos três devs, cada um com o monitorzinho;
  - a plaqueta da tela do dev vira um seletor entre os três, como o `briefing-tela-3.md` já previa;
  - o "Ver a tela" em cada mesa.

### 10. A conversa com ações

Na conversa, a mente do dev responde e, quando cabe, faz. Ganha uma ferramenta, `agir`, com poucas ações da rotina:
- **ir para casa:** só quando está convocado, fora do expediente. Encerra a própria convocação, como o "Dispensar" do chip. O kernel ganha a variante da dispensa feita pelo próprio dev;
- **fazer uma pausa:** o café, a TV ou o videogame, que a rotina dele já conhece. Só quando não há pedido em andamento;
- **acender ou apagar a luz:** é o item "o dev e a luz" do `futuro.md`.

O cartão da conversa passa a dizer que ele só promete o que vai fazer. Muda o que vai ao modelo, então as fitas do escritório são regravadas (centavos, com o seu ok).

## 11. Ordem do trabalho, em oito partes

**Primeira metade, as mãos:**
1. **As chaves e as ferramentas.**
   - **O usuário cria as duas chaves,** com o limite de gasto, e as põe no `.env`.
   - **Eu fixo e instalo o Codex e o `agy`,** com o seu ok em cada download. A versão fica no `Makefile`, como a do `nats-server`.
   - **As primeiras conferências:**
     - cada um roda dentro do nosso `sandbox-exec`;
     - o DNS fecha;
     - cada um chega à nossa porta com a chave falsa.
2. **A porta em três línguas,** com os testes contra o transporte falso e uma chamada real curta de cada (centavos).
3. **O Codex e o Antigravity:** os conectores, as provas de conformidade (`make conformidade MAOS=codex` e `MAOS=antigravity`) e as fitas.
4. **A comparação em processo** e o relatório.

**Segunda metade, o elenco:**
5. **O Kenji e a Lívia:** o elenco, a arte, as mentes, as provas de conformidade das mentes e o mundo 03 num sandbox.
6. **O quadro com três devs e a prancheta:**
   - o "Para quem" e o "Para todos";
   - o tamanho fora da tela;
   - a devolução que troca quem programa;
   - o texto entre os passos;
   - a tela.
7. **A conversa com ações,** com as fitas regravadas.
8. **O escritório vivo no mundo 03, a criação e o fechamento.**
   - **A criação:** o primeiro "Para todos" de verdade é o pedido da receita do computador, e o gerente aceita a melhor das três entregas.
   - **O fechamento:** o diário e os documentos.

## 12. A criação: a receita do computador

O pedido, escrito pelo gerente no escritório vivo, "Para todos":
- **o que fazer:** a receita da máquina do dev no M28, num arquivo do repositório (`tools/computador/receita.yaml`):
  - o que instalar, com a versão: o Python, o `uv`, o Node, o `pnpm`, o `nats-server`, o Claude Code, o Codex e o `agy`;
  - o que fica de fora: o `.env`, o `privado/`, o `data/`, o `~/.ssh` e o login do usuário;
- **um robô que confere a receita contra o repositório:** as versões são as fixadas no projeto (o `Makefile`, o `pyproject.toml`, o `package.json`), e nenhum caminho com segredo entra;
- **o teste de aceite:** o robô passa na receita, e falha quando uma versão diverge ou um segredo entra.

As três entregas vão para o relatório do "Para todos". O gerente mescla uma, e as outras ficam como dado. Se nenhum dos três conseguir, nós fazemos, e as tentativas ficam registradas.

## 13. Contratos

**Campos opcionais, dentro da versão maior:**
- o `office.ticket.created.v1` ganha `assignee` e `group`;
- o `office.ticket.returned.v2` ganha `harness` e `model`;
- o `workshop.step.v2` ganha `note`, até 200 caracteres;
- a dispensa feita pelo próprio dev cabe no `office.staff.dismissed.v1` como está: o motivo `dispensado`, com o próprio dev no `by`. O motivo é uma lista fechada, e um valor novo pediria o `staff.dismissed.v2`.

**Sem mudança de contrato:**
- os valores `codex` e `antigravity` do `harness`: o campo já é um token livre no `ticket.created.v1`, no `workshop.step.v2` e no `llm.call.completed.v1`, e quem confere os valores é o `office.yaml`;
- o tamanho fora da tela: a prancheta manda "M", e o contrato segue igual.

## 14. Testes do marco

- **Unidade:**
  - a porta nas duas línguas novas, contra o transporte falso: a chave trocada, os tokens lidos, o custo, a parada no teto e a fita;
  - o conector do Antigravity, contra uma fita de `stream-json`;
  - o do Codex, contra a fita de verdade;
  - no kernel:
    - quem pega qual pedido;
    - o "Para todos" criando uma ficha por dev;
    - a convocação e a dispensa de cada dev;
    - a dispensa pelo próprio dev;
  - o par dev, mãos e modelo na ação de escrever e na de devolver;
  - o `note` do passo;
  - a ferramenta `agir` da conversa.
- **De ponta a ponta:**
  - as provas de conformidade das mãos e das mentes, pela fita, sem rede;
  - um dia do mundo 03 com os três devs e o dev-script de reserva;
  - o "Para todos" até as três entregas.
- **No navegador:**
  - o "Para quem" e o "Para todos";
  - as fichas sem o tamanho e com a cor do dev;
  - os três chips e o seletor da tela do dev;
  - o comentário entre os passos.
- **O mundo intacto:** os soaks das fazendas e do escritório (agora com três devs) e o replay.

## 15. Custo

- **API, estimada:**
  - as chamadas curtas e as provas de conformidade, das mãos e das mentes: uns US$ 3;
  - a comparação em processo: uns US$ 10 a 25;
  - o "Para todos" da criação, as mentes e o escritório vivo: uns US$ 15 a 25;
  - as fitas: centavos.
- **O teto proposto do marco é US$ 60,** cada etapa paga com o seu ok, com o custo da anterior. **De onde sai o dinheiro:**
  - as mentes do Kenji e da Lívia pela OpenRouter, com o saldo de lá;
  - as mãos pelas chaves novas;
  - o Tiago pela Claude Platform.
- **O Claude Code:** um marco maior que o M26, com as duas metades.

## 16. Riscos

- **Um Seatbelt dentro do outro.** Se o Codex ou o `agy` exigirem o próprio sandbox, a cerca vira o deles, e o nosso fica só na rede. *A resposta:* é a primeira conferência da parte 1, e se der errado, uma decisão nova antes de seguir.
- **O `agy` é novo e muda rápido.** A versão 1.5.7 mudou o modo padrão sem interface. *A resposta:* a versão fixada e a fita, e a prova de conformidade de novo a cada versão.
- **A porta na língua do Gemini.** O que o `agy` manda pelo `GOOGLE_GEMINI_BASE_URL` ainda não foi visto. *A resposta:* a primeira sessão de verdade grava o tráfego, e a porta é escrita contra ela.
- **As mentes da OpenAI e do Google no escritório:**
  - o Astra já passou pela fazenda, consertado (ADR-0076);
  - o Neon ainda não teve uma mente no mundo.

  *A resposta:* a prova de conformidade de cada mente antes do mundo 03. Uma mente que não passar fica com o dev-script de reserva, e o dev entra mesmo assim.
- **Três devs custam três vezes mais.** *A resposta:* sem pedido no quadro, nenhuma mente é chamada; o teto por dia e por pedido vale para todos; o "Para todos" é escolhido, nunca automático.
- **O mundo novo perde a continuidade do quadro de novo.** *A resposta:* o mundo 02 fica no arquivo, como o 01.

## 17. Decisões

As onze da primeira versão, aprovadas em 22/nov, com o que mudou:
1. ~~Um dev só~~ → **três devs, um por laboratório:** o Kenji (o Astra e o Codex) e a Lívia (o Neon e o Antigravity) entram no M27, em duas metades. *Aprovado pelo usuário em 22/nov.*
2. **Os modelos das mãos:** o GPT-6.2 Astra no Codex, e o Gemini 4 Neon no Antigravity, no esforço `high`. São os equivalentes do Opus. *Aprovado.*
3. **As chaves diretas da OpenAI e do Google para as mãos;** as mentes do Kenji e da Lívia, e o revisor, pela OpenRouter. *Ajustada com os saldos de 22/nov.*
4. **A porta das mãos em três línguas,** com uma ADR que complementa a ADR-0089. *Aprovado.*
5. **O nosso `sandbox-exec` como a cerca,** com o sandbox de cada harness desligado e o `HOME` no espaço. *Aprovado, a conferir na parte 1.*
6. **A instalação fixada pelo `Makefile`,** com o seu ok em cada download. *Aprovado.*
7. **As duas comparações:**
   - a em processo, nas quatro combinações dos três pedidos do M26, para separar o modelo do harness;
   - a do "Para todos", ao vivo, para comparar o resultado final.

   *Ajustada.*
8. **A criação é a receita do computador, com o robô que a confere,** feita num "Para todos". *Ajustada.*
9. **A devolução troca quem programa, e o texto do modelo entre os passos aparece na tela do dev.** *Aprovado.*
10. ~~O escritório vivo segue no mundo 02~~ → **o escritório vivo vai para o mundo 03,** com os três devs. O padrão do Tiago continua o Claude Code com o Opus 5.5. *Ajustada.*
11. **O teto do M27: US$ 60** (era US$ 40, para um dev só), cada etapa paga com o seu ok. *Aprovado pelo usuário em 22/nov.*

**As decisões novas:**

12. **A conversa com ações:** ir para casa quando convocado, uma pausa da rotina e a luz, pela ferramenta `agir`, com as fitas regravadas. *Aprovado pelo usuário em 22/nov.*
13. **O tamanho do pedido sai da tela:** a prancheta manda "M", e a faixa da ficha ganha a cor do dev. *Aprovado pelo usuário em 22/nov.*
14. **O "Para quem" e o "Para todos"** nos campos opcionais `assignee` e `group` do `ticket.created.v1`, com o kernel criando uma ficha por dev no "Para todos". *Aprovado pelo usuário em 22/nov.*

## Fontes

- [O modo não interativo do Codex](https://learn.chatgpt.com/docs/non-interactive-mode.md) e o repositório [openai/codex](https://github.com/openai/codex), lidos no M26 (`tests/fixtures/codex/README.md`).
- [O login do Codex com chave de API](https://www.simplified.guide/codex/api-key-login) e [o `CODEX_API_KEY` no `exec`](https://continuumcode.ai/guides/codex-cli-login/).
- [O Codex pela OpenRouter](https://openrouter.ai/docs/cookbook/coding-agents/codex-cli) e [a issue 12114](https://github.com/openai/codex/issues/12114).
- [O modo sem interface do Antigravity CLI](https://antigravity.google/docs/cli/headless/) e [a autenticação](https://antigravity.google/docs/install/).
- [A issue 548 do `antigravity-cli`](https://github.com/google-antigravity/antigravity-cli/issues/548), sobre as permissões sem interface.
- O plano macro da v0.4 (§1, §4 e §7), a ADR-0077, a ADR-0089 e o `futuro.md`.
