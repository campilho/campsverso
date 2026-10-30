# ADR-0074 — Decisões do plano do M21 (a terceira arena)

**Status:** aceita · **Data:** 2026-10-27 · **Marco:** M21
**Complementa:** `docs/planos/m21-a-terceira-arena.md`; ADR-0058 (a porta de modelo e o orçamento); ADR-0066 (a v0.3, decisões 12 e 20); ADR-0070 (o mapa d reservado, o juiz e a prova); ADR-0071 (o agricultor treinado); ADR-0073 (o ajudante como teste de julgamento)
**Altera:** ADR-0066, no orçamento da v0.3 (de US$ 150 para 300) e na rodada do humano (sai a da Boa Vista)

## Contexto

O M21 é a medição final da v0.3: quem aprende, e quanto vale aprender. Na Morada do Sol, só o Haiku jogou, e não aprendeu, nem com o playbook. Faltam:
- a régua do meio, para separar planejar de aprender;
- o mapa d, reservado no M19;
- a rodada do humano;
- o Claude nos tamanhos maiores e as outras famílias.

A prova também tem dois defeitos de leitura. Os preços do dia mostraram que o GPT-6 Astra custa umas três vezes o Opus por corrida.

## Decisão

1. **O escopo:** o mapa d, o humano, a régua do meio, o Claude, os dois braços do Haiku, a OpenRouter com dois juízes, a prova corrigida, o relatório final e o custo no painel.
   - Ficam para a v0.4: mudar o teto com o mundo vivo, a guarda caída pausar o mundo, e as medições do prompt em inglês e da foto em prosa.
   - Ficam para a rodada 3: mais seeds e o segundo ano com memória.
   - A rodada do humano na Boa Vista sai.
2. **O mapa d às cegas:** o usuário aprova as promessas da receita (a terra boa num lugar que nenhum mapa usou, quem aprendeu só o lugar erra, alcançável na primeira estação) e vê o print só depois de jogar. O mapa nunca entra nos testes do script 3.
3. **A rodada do humano no mapa d,** antes de qualquer corrida nele ser vista, com a linha ao lado do oráculo, porque o usuário conhece as regras ocultas.
4. **A régua do meio:** o script 3 com a crença presa (`learn: false`) nos quatro mapas. A medida principal do relatório é a fração do valor de saber capturada: (o controlador − o fixo) ÷ (o oráculo − o fixo).
5. **As corridas, no mapa d e na seed da Morada:**
   - o Haiku três vezes;
   - a ferramenta de comparação duas vezes e o conselheiro uma;
   - o Sonnet, o Opus, o Fable, o Gemini e o Astra uma vez cada;
   - os tetos por corrida do plano.
6. **Sem playbook em nenhuma corrida da rodada principal.**
7. **A ferramenta de comparação** como braço do Haiku: lê o caderno do próprio avatar e devolve os plantios que fugiram do esperado, com os parecidos e as colunas em que diferem. Fica em `libs/mind`, ligada por corrida.
8. **O conselheiro** (a ferramenta beta da API) como braço do Haiku, só na reflexão da noite.
9. **O conselheiro é o Opus 4.8,** que devolve o conselho em texto (`advisor_result`). O Opus 5.5 e os mais novos devolvem o conselho criptografado (`advisor_redacted_result`), que o executor lê, mas o nosso código não.
10. **A OpenRouter** num adaptador próprio da porta de modelo, com `httpx`:
    - o custo vem da resposta;
    - o provedor fica fixo em cada modelo;
    - cada chamada grava quem atendeu.

    Os Claude continuam na API da Anthropic.
11. **As outras famílias:** o GPT-6 Astra e o Gemini 4 Argon, conferidos na lista da OpenRouter no dia de cada corrida.
12. **Dois juízes,** o Opus 5.5 e o GPT-6 Astra, em todas as corridas com memória. Na corrida do Opus, vale como referência o veredito do Astra; na do Astra, o do Opus. O Astra é conferido antes contra o gabarito e os controles.
13. **A prova corrigida:**
    - a pergunta dos corvos passa para 40 tiles da porta;
    - o script 3 só diz "aprendeu" com a correção pelos 19 atributos;
    - a leitura nova é refeita nas corridas antigas.

    O comportamento do script não muda.
14. **O custo do dia no painel do operador** e no modo de assistir.
15. **Os créditos:** a Console foi a uns US$ 149, e a OpenRouter tem US$ 50. Mais créditos só com o custo real na mão.
16. **O ano do humano:**
    - 144× com o Camps acordado e 720× dormindo;
    - pausa livre;
    - o sandbox retoma um mundo (`RETOMAR=`);
    - a tela do jogador ganha o relógio quando o gateway aceita os comandos dele.

    A velocidade não muda a medição dos outros: cada corrida é um mundo próprio, as regras andam por ticks, e os modelos jogam com o mundo esperando por eles.
17. **Um passo por vez,** nesta ordem: o humano, o Haiku, os braços do Haiku, o Sonnet, o Opus, o Gemini, o Astra, o Fable e a rodada do playbook. Cada passo pago roda só com o ok do usuário, depois do relatório e do custo real do anterior.
18. **O Astra e o Fable começam por um piloto de dois dias.** Depois do Opus, o usuário escolhe entre um ano e 14 dias, com o custo real. O GPT-6.1 Sol é o plano B do Astra.
19. **Os braços nos outros modelos** se decidem depois dos braços do Haiku, para a rodada do playbook. O conselheiro não vai para os outros modelos: é do servidor da Anthropic, e acima do Haiku o conselho volta criptografado.
20. **A rodada controlada do playbook** no fim do M21:
    - o playbook 3, escrito depois da rodada principal e só com método;
    - os modelos da rodada principal;
    - o mesmo mapa, a mesma seed e a mesma memória;
    - o comprimento pelos custos reais.
21. **O teto da v0.3** sobe de US$ 150 para 300.

## Notas do usuário (27/out)

- **2:** "vamos na surpresa".
- **3:** a estação era pouco; jogar o ano, se a velocidade não atrapalhar a medição dos outros. Daí a decisão 16.
- **5:** "vamos aos poucos": primeiro ele joga, depois o Haiku, depois o Sonnet, passo a passo, mesmo que demore mais.
- **6:** sem playbook em nenhum caso, nem no Opus, nem no Sonnet. Depois, um teste isolado e controlado com o playbook melhorado em todos os modelos, nos mesmos cenários e mapas, para ver se a performance melhora. Ele está intrigado com o playbook não ter mudado o Haiku, porque deveria.
- **7 e 8:** perguntou pelos outros modelos. Daí as decisões 19 e 20.
- **11:** parear com o Opus: o GPT-6 Astra (não o 6.1 Sol) e o Gemini 4 Argon, o 6º e o 7º no índice de inteligência da Artificial Analysis. Antes deles vêm:
  - três Claude, o Opus, o Sonnet e o Fable;
  - o Muse Wonder, que não tem API;
  - o Kimi K3.1 Pro, fora do escopo de longo prazo.

  O Fable não estava no plano e entrou pela decisão 18.
- **12:** o GPT-6 Astra julga o Opus 5.5. Documentar sempre o modelo exato, a versão e o harness, se houver.
- **15:** a Console estava com US$ 49,34 e ganhou US$ 100; a OpenRouter já tem US$ 50.

## Adendo de 28/out: a régua do meio e a decisão 22

O script 3 fixo, medido no passo 2, fez num ano 267 moedas, 72 colheitas e 5 dias de fome. Fez o mesmo nos três mapas, porque planta perto de casa, e o mapa só muda a água e a mata longe dela. Nas moedas, isso derrubou a premissa da decisão 4:
- **planejar vale muito:** o fixo fica 253 moedas acima do script 2;
- **aprender, do jeito do script 3, custa mais do que rende num ano:** ele fica umas 260 moedas abaixo do fixo. Sem as regras ocultas, o mesmo script 3 fez 246 moedas;
- **saber não é um teto em moedas:** o oráculo fica 54 moedas acima do fixo no mapa a, 320 acima no b e 83 abaixo no c. A fração (o controlador − o fixo) ÷ (o oráculo − o fixo) fica com o denominador negativo no c e frágil no a.

22. **O mapa d promete que saber vale** (a opção A, escolhida pelo usuário):
    - num ano, o oráculo passa o script 3 fixo por pelo menos 150 moedas e 15 colheitas, conferido por um teste com um ano de cada (`tests/e2e/test_mapa_d.py`), como já acontece no mapa b;
    - a fração do valor de saber capturada é a medida principal só no d;
    - nos mapas a, b e c, o relatório põe as quatro réguas lado a lado, com a explicação do adendo;
    - os scripts não mudam, e os números do M19 e do M20 continuam valendo.

    Ficaram de fora consertar o planejador para o oráculo nunca ficar abaixo do fixo (B) e tirar a fração (C).

## Adendo de 28/out: a ferramenta de comparação (o passo 5)

A decisão 7 deixou abertos onde a ferramenta entra, o que conta como fugir do esperado e de onde vêm as colunas. Ficou assim:
- **Onde:** só na reflexão da noite, ao lado do `reflect`, com até duas consultas por noite. É ali que a mente escolhe o experimento. Nas decisões, cada ferramenta é uma ação do mundo.
- **O normal vem do próprio caderno:** é a mediana dos dias de três ou mais plantios maduros da cultura na mesma estação. Um plantio fugiu quando se afasta pelo menos um dia e 20% dela. A ferramenta não lê números do cartucho nem do manual.
- **Também as perdas,** que o texto da decisão 7 não citava: as plantas maduras que se perderam antes da colheita, ao lado das colhidas mais parecidas. Entram porque o script 3 também aprende a perda, e uma das perguntas da prova é sobre ela.
- **As colunas são dado do gênero** (`cartridges/farm/mind/.../comparar.yaml`):
  - a quantos tiles o canteiro fica da água, da mata, do caminho e da porta, no terreno visto, e do espantalho, nas coisas vistas;
  - as faixas do script 3 (2, 4, 8 e 16 tiles) decidem se dois plantios diferem;
  - o que havia antes no canteiro, o adubo, a rega e a estação.

  Os parecidos são os que diferem em menos colunas, e a ferramenta lista as colunas em que o plantio difere de todos eles. Ela não diz qual coluna explica nada.
- **A memória guarda o terreno visto** (`MemoryPort.see` e `terrain`), só os tipos que a comparação mede e só com ela ligada. O `Planting` ganha a estação do plantio e a da maturação, sempre, porque são fatos do relógio que nenhum pedido mostra. Uma memória antiga, como a de um sandbox retomado, ganha as colunas ao reabrir.
- **Liga por corrida** (`Spec.compare`), e o resumo conta as consultas (`comparisons`).
- **Os testes:**
  - a descrição, as instruções e os nomes das colunas passam no teste de palavras proibidas da Morada do Sol;
  - desligada, o pedido da reflexão é o de antes, e as fitas passam sem regravar.

## Adendo de 28/out: o conselheiro (o passo 6)

Conferido na documentação e na tabela de preços do dia:
- **O pedido:** a ferramenta `advisor_20260301`, no beta `advisor-tool-2026-03-01`.
- **O uso:** o do conselheiro vem fora do `usage` de quem respondeu, em `usage.iterations` (`advisor_message`, com o modelo).
- **O preço:** o Opus 4.8 custa US$ 5 e 25 por milhão (cache lido a 0,50) e entrou na tabela do ambiente.

Ficou assim:
- **Na porta de modelo:**
  - um pedido com o conselheiro, ou com blocos dele na conversa, vai pela API beta;
  - a `ModelResponse` ganha o `advisor` (o modelo, as consultas e os tokens), e a fita o guarda;
  - o adaptador retoma o `pause_turn` sozinho: a resposta volta como veio, e a continuação se junta a ela.
- **No medidor:** cobra o conselheiro na tarifa dele, soma ao `cost_usd` e publica o campo `advisor` do `llm.call.completed.v1`. Um conselheiro sem preço é recusado antes de gastar.
- **Na mente:** o conselheiro entra só na reflexão (`MemorySettings.advisor`, `Spec.advisor`), com uma consulta por pedido e a saída dele limitada a 4.096 tokens. As instruções pedem uma consulta antes de escolher o experimento, e a mensagem pede ao conselheiro até 150 palavras, em português. O resumo da corrida conta os conselhos (`advised`). O texto do conselho fica na fita da corrida (`llm.jsonl`), de onde o relatório o lê.
- **A fumaça** (`make llm-smoke CONSELHEIRO=claude-opus-4-8`, 28/out) custou US$ 0,017:
  - o Haiku 5.5 consultou o Opus 4.8 (2.593 tokens de entrada e 146 de saída, US$ 0,0166) e seguiu o conselho;
  - o conselho voltou em texto, em português;
  - o evento validou pelo contrato, e a repetição veio da fita sem cobrança;
  - o `disable_parallel_tool_use` convive com a ferramenta do servidor.
- **A conta da corrida:** com a reflexão de uns 15 mil tokens, cada noite custa uns US$ 0,10 a 0,18 de conselheiro. O braço fica nos US$ 3 a 6 do plano.

## Adendo de 28/out: o custo no painel, a ficha e a tabela de preços (o passo 7)

- **O custo das mentes na tela:**
  - a projeção da `libs/world-view` passa a ler, do stream `observer`, os `llm.call.completed` cobrados e os avisos `ops.budget.*`, além do caderno, e o gateway e o modo de assistir usam a mesma lista;
  - o estado da tela ganha o campo opcional `costs` (contrato `realtime/welcome.v1`): por controlador, o gasto do último dia com chamadas, o total, as chamadas e a parte do conselheiro, e o último aviso do orçamento;
  - o painel do operador mostra o cartão "Custo", e a página da arena, o custo de cada corrida até o ponto da reprodução. A visão do jogador não o vê;
  - conferido no modo de assistir: a corrida do Haiku de 25/out soma US$ 0,7104 em 1.030 chamadas, como o resumo dela.
  - **o gateway passa a deduplicar o `observer` e o `internal` pelo id do evento,** com os 4.096 ids recentes no arquivo dele. Antes, deduplicava por `source` e `seq`, e no `observer` isso falhava de dois jeitos:
    - o runner (o caderno) e o medidor (o custo) do mesmo controlador têm o mesmo `source`, com contadores próprios, e o gateway ao vivo jogava fora o evento do contador que estivesse atrás;
    - o `seq` de um controlador volta a zero quando ele reinicia, como no sandbox que retoma.

    O modo de assistir não tinha o defeito, porque lê o arquivo inteiro.
- **A ficha de cada corrida** fica no `summary.json` (`card`):
  - o modelo pedido e os ids que as respostas trouxeram, da fita, com o conselheiro;
  - a data e a rota: o provedor de cada chamada, pelos eventos;
  - o esforço por tipo de chamada;
  - o harness: o commit, se havia mudança fora dele, a versão do SDK, a mente, o hash do prompt de sistema e o das ferramentas, a memória, o playbook e os braços.

  O veredito do juiz ganha o modelo que respondeu, a rota, o hash do pedido e o da rubrica. O relatório da arena tem uma seção com a ficha. O provedor que atendeu na OpenRouter entra no passo 8.
- **A tabela de preços conferida em 28/out:**
  - o cache lido do Sonnet 5.5 é US$ 0,10 por milhão, não 0,20. O M14 contou esse cache em dobro, e os relatórios antigos ficam como estão;
  - o Fable 5.1 entra a US$ 10 e 50 (cache lido a 0,25), para a corrida dele pela API da Anthropic;
  - acima de 100 mil tokens de prompt, o Haiku 5.5 custa cinco vezes mais. Nenhum pedido da fazenda chega lá.

## Adendo de 29/out: o adaptador da OpenRouter (o passo 8, a parte de graça)

- **O `httpx2`, não o `httpx`.** É a biblioteca HTTP deste ambiente: vem com o SDK da Anthropic e já estava na lista de SDKs que só os adaptadores importam. O `OpenRouterModel` fica em `libs/adapters/model_openrouter.py`.
- **A tradução,** que é parte do harness e entra na ficha:
  - o `tool_use` vira `tool_calls`, e cada `tool_result`, uma mensagem `tool` logo depois. O texto do usuário vai numa mensagem depois delas;
  - o `tool_result` com `is_error` ganha a marca `(erro)` no começo, porque o formato de chat não tem o campo;
  - o raciocínio volta num bloco `reasoning`, com os `reasoning_details` como vieram, e a janela o devolve sem mudança, como a OpenRouter pede quando há ferramentas;
  - o `tool_use` guarda os argumentos como o modelo os escreveu (`arguments`), e é esse texto que volta. Argumentos que não são JSON viram uma entrada vazia;
  - as ferramentas estritas continuam estritas (`function.strict`). Os 33 esquemas da Morada (29 ferramentas de decisão, a reflexão, a comparação, a prova e o juiz) cumprem as regras do modo estrito da OpenAI, conferidos de graça;
  - o esforço vai como `reasoning.effort`, e uma ação por vez, como `parallel_tool_calls: false`;
  - os marcadores de cache vão nas partes de texto (o sistema e o texto do usuário). A mensagem `tool` é só texto e não leva marcador.
- **O provedor fixo fica na tabela de preços do ambiente:** a chave `openrouter:` no modelo. A composição escolhe o adaptador pelo modelo (`model_port`), e um modelo sem rota é recusado antes de sair. A lista de 29/out:
  - o GPT-6 Astra (`openai/gpt-6-astra`) pelo provedor `openai`, a US$ 10 e 50 por milhão (cache lido a 1,00 e gravado a 12,50);
  - o Gemini 4 Argon (`google/gemini-4-argon`) pelo `google-ai-studio`, a US$ 2 e 10 (cache lido a 0,10 e gravado a 0,1875);
  - **os dois têm também um provedor `flex` pela metade do preço** (`openai/flex` a 5 e 25; `google-ai-studio/flex` a 1 e 5), mais lento e às vezes indisponível. Como o mundo espera o modelo na arena, o flex pode cortar à metade o custo do Astra e do Gemini. A escolha fica para o usuário antes das corridas pagas.
- **O custo vem da resposta** (`usage.cost`) e vai em `ModelUsage.cost_usd`. O medidor e o juiz o usam no lugar da tabela, e a fita o guarda. A tabela continua sendo a guarda (modelo sem preço é recusado) e a estimativa.
- **O evento `llm.call.completed.v1` ganha dois campos opcionais:**
  - `response_model`, o id que a resposta disse ser, publicado em toda chamada;
  - `served_by`, quem atendeu na OpenRouter, lido do campo `provider` da resposta. A referência da API não documenta esse campo; a fumaça de 29/out o confirmou nos dois modelos.
- **Os erros** são classificados como na Anthropic: o 402 (sem créditos) e o 403 contam como `auth`. Como o SDK de lá, o adaptador repete o 408, o 429, os 5xx e as falhas de rede até duas vezes, com a espera que o servidor pede. Um erro que chega num 200 (no corpo ou na escolha) também é erro. A OpenRouter não conta tokens sem gerar.
- **A ficha:** a rota diz quem atendeu (`openrouter: OpenAI`), e o SDK do harness é o `httpx2`.
- **O segundo juiz:** `make juiz JUIZ=openai/gpt-6-astra` julga com o Astra. A fita é a mesma (o hash do pedido tem o modelo), e o veredito vai para `juiz-gpt-6-astra.json`, ao lado do `juiz.json` do Opus; `CONFERIR=` com o mesmo `JUIZ=` confere esse.
- **A fumaça é `make llm-smoke MODEL=openai/gpt-6-astra`,** em vez do `PROVEDOR=openrouter` do plano, porque a rota sai da tabela. Pela OpenRouter, a fumaça dá também o segundo turno, com o resultado da ferramenta e a resposta inteira de volta, que é a tradução que mais pode falhar. Ela pede `OPENROUTER_API_KEY` no `.env`; o `make secrets` deixa a linha comentada para o usuário preencher.
- **A fumaça de 29/out,** com a chave do usuário (limite de US$ 50 por semana na chave), custou US$ 0,0105 nas quatro chamadas:
  - o GPT-6 Astra, atendido pela OpenAI, propôs nos dois turnos, e o custo que a OpenRouter cobrou bateu com a tabela (US$ 0,0088). No esforço baixo, ele não devolveu raciocínio, então a volta do raciocínio dele fica para o piloto;
  - o Gemini 4 Argon, atendido pelo Google AI Studio, devolveu o raciocínio criptografado (`reasoning.encrypted`), que voltou sem mudança no segundo turno e foi aceito (US$ 0,0017).
- **O Astra conferido como segundo juiz (29/out):** as 17 chamadas do gabarito (12 corridas e 5 controles), pelo provedor normal, custaram US$ 1,70, abaixo da estimativa de 4 a 7:
  - **concordância de 47 em 47 nas corridas e de 28 em 28 nos controles,** como o Opus, e com o mesmo veredito e a mesma crença do Opus em todas as regras. A decisão 12 vale como foi escrita: o Astra julga a corrida do Opus;
  - no esforço alto, ele raciocinou pouco: 3.712 tokens de saída nas 17 chamadas, uns 220 por chamada. A entrada foi de 121 mil tokens, contra 183 mil do Opus no mesmo pedido, pelo tokenizador de cada um;
  - a OpenRouter contou quase todo o pedido como cache gravado, a 1,25× da entrada, por causa do marcador de cache no sistema. Numa chamada só por corrida, como no juiz, isso é um gasto à toa de uns 25%, igual ao do Opus na Anthropic; nas corridas, o cache lido compensa.

## Adendo de 29/out: o que o humano achou na tela, jogando o mapa d

- **A névoa esquecia canteiros.** A tela mede a vista pela posição desenhada do avatar, que anda suave, e o servidor manda as coisas pela posição dele no mundo, que pode estar um pulso atrás. Na borda da vista, a tela achava um canteiro à vista que o servidor já não mandava, apagava a lembrança dele e não a desenhava mais. Agora a lembrança só se apaga a 2 tiles da borda para dentro (`MARGIN`), onde as duas contas concordam.
- **A névoa sobrevive a fechar a tela.** A lembrança fica no navegador, por mundo e avatar (`localStorage`). Uma lembrança de um tick depois do de agora é de outro jogo no mesmo mundo (um sandbox novo começa no tick 0) e é esquecida; o sandbox que retoma continua de onde parou. A ADR-0068 a deixava só na aba aberta.
- **O menu diz o custo, o horário e o preço.** O catálogo de ações (`world.session.started.v1`) ganha campos opcionais: o custo de cada ação pela tabela do cartucho, uma nota com valores dos dados (`aberto das {kiosk.opens} às {kiosk.closes}`) e, nos parâmetros, o preço de tabela de cada escolha, o atributo do alvo com o preço de agora (`preco_`) e o com o estoque do dia (`estoque_hoje`). A tela mostra "8 de energia · 15 min", "aberto agora" ou "fechado agora" pelo atributo `open` do alvo, o preço ao lado de cada escolha e só o que há no estoque. A mente não muda: ela já lia tudo isso no manual e na percepção.
- **A fome aparece como saciedade.** Na tela, a barra mostra 100 menos a fome, cheia quando o avatar comeu, como a da energia. O mundo, o manual e a linha do tempo continuam falando em fome.

## Consequências

- **O orçamento da v0.3 dobra,** e o plano passa a gastar por passos aprovados, não por rodada.
- **O `llm.call.completed.v1` ganha campos opcionais:**
  - o conselheiro;
  - o provedor que atendeu;
  - o id do modelo que a resposta trouxe.
- **A porta de modelo ganha um segundo provedor,** e a `ModelUsage`, um custo opcional dito pelo provedor.
- **O sandbox passa a retomar um mundo,** e a tela do jogador passa a mostrar o relógio quando pode mandar nele.
- **As três fazendas não mudam:** a ferramenta e o conselheiro ficam desligados fora dos braços, e as fitas passam sem regravar.
