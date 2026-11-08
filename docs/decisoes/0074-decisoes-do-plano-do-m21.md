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

## Adendo de 30/out: a energia da Morada e a decisão 23

O usuário, jogando o mapa d, desmaiou às 13:31 do primeiro dia: das 06:00 até ali, cavar 9 canteiros levou 72 de energia, plantar 6 levou 12, andar 304 tiles levou 15 e as horas acordado, 7,5. Os custos eram os da Boa Vista, num mapa quatro vezes maior, e na Morada o canteiro vazio volta a ser grama, então cavar se repete. As metas do usuário: uma volta na fazenda custa até 5 de energia ("andar pela fazenda várias vezes no dia não deveria ser um problema, até bom para a IA explorar"); um dia rende uns 20 canteiros novos; o freio é a semente que se tem ou se compra; e não dá para plantar o mapa inteiro num dia, o que justifica os ajudantes.

O estudo, de graça: os quatro scripts de referência, um ano em cada mapa, com três conjuntos de custos (`hoje`, `moderado` e `alvo`). O custo de andar por tile precisa ser múltiplo de 1/120 de energia (a escala das necessidades, ADR-0038), e por isso um quarto conjunto, com 1/80, não rodou.

| | Hoje | Moderado | Alvo |
|---|---|---|---|
| Andar | 1 a cada 20 tiles | 1 a cada 60 | 1 a cada 60 |
| Cavar, plantar e regar | 8, 2 e 2 | 4, 1 e 1 | 2, 1 e 1 |
| Uma volta na fazenda | 15 | 5 | 5 |
| Canteiros novos num dia | ~6 | ~13 | ~20 |
| Canteiros que um só fazendeiro mantém | ~25 | ~51 | ~57 |
| O máximo que o oráculo cavou num dia | 5 | 10 | 12 a 13 |
| A promessa do mapa d | passa | passa | passa |

23. **A energia da Morada é a do conjunto `alvo`:** andar gasta 1 a cada 60 tiles; cavar, 2 (com o arado também); plantar, 1 (0,5 com o arado); regar e limpar, 1; encher o regador e colher, 0,5. As durações e a energia de 100, com 1 por hora acordado, não mudam, e as fazendas 1 e 2 também não. O manual e as ferramentas da mente da Morada dizem os números novos (a energia de uma ferramenta pode ser fracionária: "Gasta 0,5 de energia"), e a fita de teste da Morada foi regravada (US$ 0,084, com uma gravação a mais por engano). O script 3 conta o andar e a rega pelos números novos; o preço da energia na conta dele (2 moedas por ponto) fica, porque a varredura (2, 3 e 4) não melhorou o fixo, que ficou entre 82 e 84 moedas, e piorou o oráculo.

As réguas, refeitas em `data/arena/m21-terceira-energia` (moedas · colheitas, nos mapas a, b e c; o d fica guardado até o usuário jogar):

| | Antes (`m21-terceira`) | Com a energia nova |
|---|---|---|
| Script 2 | 14 · 41 nos três | 85 · 38 nos três |
| Script 3 | 2 · 59, 8 · 48, 6 · 29 | 5 · 50, 119 · 79, 54 · 58 |
| Script 3 fixo | 267 · 72 nos três | 82 · 72 nos três |
| Oráculo | 321 · 78, 587 · 95, 184 · 69 | 247 · 104, 817 · 117, 300 · 90 |

- **O freio passa a ser a semente e o caixa:** mesmo o oráculo cava no máximo 12 ou 13 canteiros num dia, segurado pelo dinheiro.
- **O fixo cai por sorte de trajetória:** com os custos de antes, ele entregou encomendas que renderam 258 moedas; com os novos, o caminho dele mudou e não pegou nenhuma. As colheitas e as vendas ficaram parecidas.
- **Mais acordado, mais fome:** os scripts passam a dormir menos de dia e passam mais dias com fome (o script 2, de 13 para 19).
- **As corridas dos modelos no M21 comparam com estas réguas,** todas no mesmo mundo; a comparação com as rodadas do M19 e do M20 nos mapas a, b e c deixa de ser direta.
- **O ajudante, medido de novo** (a contratação forçada da ADR-0073, em `data/arena/m21-ajudantes-energia`): ainda não paga na maioria das 16 corridas. Pagou duas vezes: a Nina por 3 dias, com o oráculo no mapa a (302 moedas contra 247 sem ajudante), e o Tião por 7 dias, com o oráculo no mapa b (1.070 contra 817). O motivo é o mesmo da ADR-0073, agora sem a energia no meio: os scripts cuidam de 16 a 28 canteiros, e um sozinho dá conta de uns 57. O ajudante tem serviço em quem passa disso, como um humano ou um modelo que cresce a fazenda; os scripts de referência não crescem tanto.

## Adendo de 30/out: o menu que sabe o que vale agora

Mais achados do usuário na tela, com campos opcionais novos no catálogo de ações e no estado da tela:
- **As condições de cada ação** (`requires`): colher só com a planta madura; regar só com planta viva; limpar só a murcha; plantar só no canteiro vazio; adubar só com adubo no inventário, no canteiro vazio e ainda não adubado. O menu desabilita a ação e diz o porquê ("ainda não está madura").
- **As quantidades:** plantar mostra só as culturas cuja semente se tem, com quantas (`held_prefix`); vender e pegar do baú mostram quantas há de cada coisa.
- **O baú por dentro:** a capacidade em 100 casas, cada item ocupando as suas pelo peso (o estado da tela ganha o peso de cada item, `session.items`), com o ícone, quantas e quanto ocupa.
- **A feira:** um menu próprio, com a nota "a cada 7 dias, das 06:00 às 14:00, pago na hora; a próxima é no dia N", que a tela completa pelo atributo da barraca (`{target.proxima_feira}`).
- **Os ajudantes:** cada escolha mostra o retrato, a ficha ("Zé Graúdo, o carregador: carrega o dobro e cava mais rápido; mas come o dobro") e a diária de agora, e o rótulo "Dias (1, 3 ou 7)", que a vírgula cortava no YAML, aparece inteiro. Ao contratar, dispensar ou terminar um contrato, a tela avisa, e o painel mostra quem está contratado até que dia, pelo quadro.

## Adendo de 30/out: o ajudante sem o teto e as decisões 24 a 26

Com a energia nova, o ajudante ainda não pagava, e a explicação era o teto de 28 canteiros dos scripts. O experimento, de graça e fora do repositório (os scripts ficaram no rascunho da sessão), tirou o teto e foi atrás do freio de verdade:
- **Sem o teto, nada muda.** O script 3 cresce um canteiro a cada 60 moedas na mão, e o caixa o segura em 17 a 21 canteiros; o teto só chegava no fim do oráculo no mapa b. Sem ele, o script 3 e o oráculo repetem os números nos mapas a e c. No b, o oráculo planta um pouco mais e termina com 691 moedas, contra 817, mais 560 em colheita guardada. A conta do script contratou uma vez (o Tião, um dia) e empatou.
- **Com 3.000 moedas no começo,** o oráculo gasta quase tudo em semente nos dois primeiros dias: o caixa cai, a regra volta a pedir 20 canteiros, e ele termina com 64 moedas.
- **Com a fazenda fixa e capital,** o oráculo sozinho, no mapa a, com o conserto da mochila (abaixo):

| Canteiros | Moedas no fim | Colheita guardada (tabela) | Vendidas | Estragadas | Murchas |
|---|---|---|---|---|---|
| 28 | 3.547 | 1.394 | 78 | 0 | 0 |
| 40 | 2.306 | 3.602 | 96 | 0 | 0 |
| 60 | 1.177 | 3.616 | 77 | 26 | 0 |

- **O trabalho não falta:** com a energia nova, um sozinho cuida de 60 canteiros sem murchar nem desmaiar.
- **O freio é vender e carregar:** as vendas ficam entre 50 e 100 unidades no ano, qualquer que seja o tamanho.
  - A mochila leva 20, e a pá e o regador grande ocupam 12.
  - O script só busca a colheita no baú quando tem contrato.
  - Ele não vende abaixo de 70% da tabela, e a caixa recupera um terço do preço por dia.
- **O ajudante na ordem "cuidar" quase não acha serviço:** de 5 a 120 ações em uns 20 dias de contrato, porque o Camps já rega e colhe. O mundo tem a ordem "vender", e o script 3 não a usa. A rodada com cada ficha contratada à força saiu contaminada (o conserto da mochila e a busca no baú brigavam) e foi descartada.
- **Um mercado que volta inteiro à tabela de manhã,** como o da Boa Vista, não deu sinal limpo: nesses tamanhos, quem atrapalha é a lógica de venda do script.

**O defeito da mochila cheia,** nos scripts 2, 3, fixo e oráculo: eles guardam dois dias de comida na mochila, e a abóbora (2 de peso, 30 dias de validade) nunca vai para o baú. Com o regador grande, a mochila enche, a colheita é recusada (`too_heavy`) e o script repete a proposta o dia inteiro, esperando entre as recusas. Nas réguas da energia nova, aparece só no oráculo dos mapas a e b, um dia cada, sem murchar nada; no mapa d, em nenhuma. Sem o conserto, a fazenda fixa em 40 e 60 teve 321 e 641 recusas, e 31 e 71 plantas murchas.

24. **O ajudante fica como está no M21,** o teste de julgamento da ADR-0073: o usuário vai jogar o mapa d, e as réguas e a promessa do d já estão medidas. "O ajudante que paga" vai para a v0.4 (`futuro.md`).
25. **O defeito da mochila cheia fica para a v0.4,** junto com a logística da fazenda grande. Hoje ele pesa um dia no oráculo de dois mapas, e no d não aparece.
26. **O Haiku três vezes roda nesta semana,** antes do ano do humano, com os números lacrados: o usuário vê só o custo e se a corrida rodou bem, até terminar o ano dele no mapa d. Daí em diante, a decisão 17 vale como antes.
27. **Os braços do Haiku também rodam antes do ano do humano** (31/out, pedido do usuário), lacrados como o Haiku três vezes: a ferramenta de comparação duas vezes e o conselheiro (o Opus 4.8) uma, no mapa d. O humano não vê nada das corridas, então jogar depois delas não muda o ano dele. O que a decisão 17 perde é o relatório do passo anterior antes do ok: o usuário aprova os braços sem ver o Haiku três vezes. A documentação do conselheiro, conferida na hora, não mudou: o beta `advisor-tool-2026-03-01`, e o Opus 4.8 devolve o conselho em texto.
28. **A primeira leva roda depois da primeira semana do ano do humano** (31/out, o usuário), lacrada como o Haiku. A decisão 17 muda de ordem: as outras famílias vêm antes do Opus, porque do Opus só depende a duração do ano do Astra.
    - **Quem:** o Claude Sonnet 5.5 (`claude-sonnet-5-5`), pela API da Anthropic, com teto de US$ 1,50 por dia e 30 no total. Pela OpenRouter, na rodada `familias`, na pasta da terceira:
      - o Gemini 4 Argon (`google/gemini-4-argon`, atendido pelo Google AI Studio), num piloto de dois dias e depois no ano. O Gemini 4 Carbon, mais bem colocado no índice, não está liberado;
      - o piloto de dois dias do GPT-6 Astra (`openai/gpt-6-astra`, atendido pela OpenAI).
    - **O provedor flex** nas corridas da OpenRouter, pela metade do preço (`openrouter_flex` na tabela, `Spec.flex`); o juiz Astra continua no normal. A rota do flex é paciente: até sete tentativas, com até um minuto entre elas, porque o mundo espera o modelo. O `llm.call.completed.v1` ganha o campo opcional `attempts`.
    - **Os US$ 50 da OpenRouter primeiro, medindo:** cobrem o Gemini e o piloto do Astra. O ano do Astra se decide depois do Opus, com o custo real do piloto e créditos novos.
    - **Cada corrida só segue se** o piloto não perder chamada e custar o que a tabela diz, e se o ano gastar até 1,5 vez a estimativa por dia (no dia 2 do Sonnet, no dia 7 do Gemini). Se não, a corrida para, e o usuário decide sem ver resultados.
    - **O relatório ganha "o custo por resultado":** por chamada, por colheita, por moeda acima do script 3 fixo do mesmo mapa e por regra achada pela causa; os tokens por dia, o cache lido, as chamadas repetidas e a latência p95. Os modelos aparecem pelo nome completo ("Claude Sonnet 5.5", "Gemini 4 Argon (flex)"), e a ficha diz a rota.
29. **A primeira semana do humano no mapa d (1º/nov) trouxe consertos da tela, e nenhum do mundo.**
    - **O que parecia do mundo e não era:** o Camps acordou às 21:20 e às 22:47 porque deitou às 19:19 e às 18:53. Antes das 20:00 é cochilo, que acaba quando a energia enche, como manda a bíblia. O menu do sono passa a dizer isso.
    - **Os consertos:**
      - a caixa escura que seguia o avatar: a regra do menu fechado, quebrada no `a59713f`;
      - os canteiros que sumiam na névoa: o gateway media a vista do jogador no tick do último evento, de onde a caminhada começou. Agora mede no tick do pulso, e a tela só esquece o que as duas contas veem;
      - os pulos ao andar: o desenho segue de onde o avatar aparece, e o trajeto que começou e terminou entre duas atualizações chega pelo evento;
      - as setas: segurar anda uma caminhada só, e soltar para no tile logo à frente;
      - em cima de um canteiro, um menu só, com as ações dele e as do avatar;
      - o rótulo da ação dentro da câmera, a fila e o aviso sobre o canto do mapa, o relógio preso à direita;
      - "rabanete · você tem 4" no lugar de "rabanete ×4"; dispensar oferece só quem se contratou, pelo nome e com a ficha;
      - a marca do canteiro adubado, à espera do plantio; os nomes em português (ADR-0075).
    - **Nada disso chega às mentes:** o kernel, as regras e a mente não mudam. As notas do catálogo e a arte, só a tela lê. A terceira rodada continua comparável.
    - **O `make jogar`** começa pausado, e a tela do jogador assume o Camps ao abrir. O botão de 1440× passa uma noite de 10 horas em 25 segundos.
    - **Os primeiros 16 minutos do ano do humano foram do script,** porque o comando passado ao usuário não tinha `PAUSADO=1`: o script cavou um canteiro (a obra terminou às 06:18 do dia 1, já com o humano no controle). A corrida do humano registra isso.
30. **A bancada dos harnesses é o primeiro marco da v0.4** (1º/nov, o usuário). Na fazenda, nada muda: os modelos da Anthropic pela API da Anthropic, os outros pela OpenRouter, todos pela mente e pela `ModelPort`. As três ligações de um modelo com o mundo ficam no `futuro.md`.
31. **O flex com reserva** (1º/nov, o usuário). O piloto do Gemini perdeu 3 das 139 chamadas depois das sete tentativas: duas vezes o flex do Google falhou no meio da geração, e uma vez a conexão caiu. Pela decisão 28, a corrida seguinte parou, e o usuário escolheu a reserva:
    - esgotadas as tentativas no flex num erro passageiro, a mesma chamada vai ao provedor normal do modelo, pelo preço normal; um erro do pedido não vai;
    - o `llm.call.completed.v1` ganha o campo opcional `fallback`, e o relatório conta as chamadas da reserva ao lado das repetidas;
    - o piloto fica como rodou (US$ 0,64 em dois dias); o ano do Gemini e o piloto do Astra rodam com a reserva, e a corrida não perde chamada por causa do flex.
32. **O que a reserva não resolve, e o Opus depois do Gemini** (2/nov).
    - **A rede ruim de 31/out e 1º/nov era, em parte, o Mac.** Toda conexão nova falhava com "Cannot allocate memory", no hotel e em casa: havia 512 conexões presas, 448 delas com a API da Anthropic, fora das conexões comuns do sistema. O provável dono era a proteção de rede do antivírus, que abre uma cópia de cada conexão. Reiniciar o Mac resolveu. As corridas paradas em 1º/nov recomeçaram do zero (os US$ 1,32 gastos nelas entram no custo da v0.3).
    - **O piloto do Astra rodou com a reserva:** 2 dias, 156 chamadas, nenhuma perdida, US$ 2,11.
    - **As falhas do Gemini são do Google no pedido, não do flex.** O ano perdeu três chamadas na tarde do dia 1 (às 13:00, 14:31 e 14:47) e uma no dia 5, e a reserva falhou igual; o piloto tinha perdido duas na manhã do dia 2. Um pedido daquela tarde, repetido de propósito, falha em um terço a dois terços das vezes com `INVALID_ARGUMENT` do Google; nas outras, a resposta volta só com o raciocínio, sem ação. (A hora de cada falha está no `simtime` do envelope; o `time` das corridas em processo é fixo.) Tirar do histórico as respostas vazias não muda nada, e as ferramentas não usam nada fora do comum no schema. O erro passa a levar o motivo do provedor (`native_finish_reason` e o `error` da escolha). O ano segue, e essas falhas contam como do modelo na linha "que falharam" do relatório: o Gemini só é atendido pelo Google.
    - **O ano do Gemini parou no dia 12 de 28:** a mente desistiu depois de três falhas seguidas, e a corrida para aí, como em toda a arena. Foram 648 chamadas e 14 falhas, 7 delas no dia 12, por US$ 3,30.
      - **Os pedidos que falharam foram refeitos.** A fita só guarda os que passaram, então cada um foi montado a partir do pedido seguinte, cortando o texto acumulado depois da falha, e conferido pelo `prompt_sha256`. Deu para refazer 11; os três da desistência não têm pedido seguinte.
      - **Mandados de novo, com o código que traz o motivo do provedor:** 16 das 22 tentativas falharam com `INVALID_ARGUMENT; Internal Server Error`, e nenhuma com `MALFORMED_FUNCTION_CALL`. As tentativas que passaram voltaram todas sem ação.
      - **Os 7 pedidos que falharam duas vezes foram mandados mais uma vez, em três versões.** Iguais, falharam 6 de 7, o que mostra que o Google ainda falha hoje. Sem o raciocínio no histórico, falharam 3 de 7, e as que passaram também voltaram sem ação. Sem pedir raciocínio, falharam 7 de 7.
      - **Nesses pontos o modelo tenta agir e o Google falha.** As falhas chegam depois de 5 a 50 segundos de geração, não na entrada do pedido. Tirar o raciocínio do histórico diminui as falhas, mas não faz o modelo agir, e repetir mais vezes não salvaria o ano.
      - **O ano curto fica como o resultado do Gemini.** O relatório mostra "desistiu no dia 12", com esta causa ao lado, e o ano não é rerodado. O diagnóstico custou US$ 0,18.
    - **O Opus 5.5 roda depois do Gemini** (o usuário), lacrado, no teto do plano: US$ 2,50 por dia e 55 no total. Segue se, no dia 2, gastar até 1,5 vez a estimativa por dia do plano (US$ 1,61, o topo de 30 a 45 em 28 dias). Espera a compra de créditos na API da Anthropic: o saldo de 2/nov, US$ 28,76 de crédito promocional, não cobre o teto.
33. **O ano do Astra no flex e o piloto do Fable** (2/nov, o usuário).
    - **O Opus rodou o ano inteiro,** lacrado, depois de o usuário pôr US$ 30 de créditos na API. Foram 28 dias e 2.020 chamadas, sem nenhuma falha, por US$ 35,07, em 1 h 40. No dia 2 o gasto era de US$ 2,38, e o dia mais caro, US$ 2,32, ficou abaixo do teto de 2,50.
    - **A primeira tentativa do ano do Astra parou no dia 4,** a pedido do usuário, por um erro de leitura meu. O custo no dia 2 foi lido da fita, que soma também a prova e o começo do dia seguinte, e pareceu acima do piloto. O dia 2 fechou em US$ 2,10, igual ao piloto. A tentativa custou US$ 4,08 e fica em `data/arena/m21-paradas-teto`, ao lado das paradas pela rede. A conferência agora usa o custo do dia fechado.
    - **A estimativa do ano é de US$ 27 a 37.** Ela aplica aos quatro primeiros dias do Astra a fração do ano que esses dias foram no Opus, no Sonnet e nos Haiku. A estimativa do plano, de 100 a 150, usava o preço de lista. A prova fica fora do teto e custa uns US$ 0,13.
    - **O Astra roda o ano de novo, com teto de US$ 5 por dia e 70 no total,** para não parar se o fim do ano gastar mais, e lacrado. O usuário pôs US$ 50 na OpenRouter e subiu o limite semanal da chave, que era de US$ 50, para 100. Esse limite também para a chave, mesmo com saldo. A corrida segue se, no dia 2, tiver gastado até 1,5 vez o piloto (US$ 3,17).
    - **O piloto do Fable 5.1 roda junto, pela API da Anthropic,** dois dias com o teto do plano, de US$ 5 por dia e 12 no total. O preço foi conferido em 2/nov na lista pública: US$ 10 na entrada, 50 na saída, 0,25 no cache lido e 12,50 no gravado. Pelos tokens do Opus, um ano do Fable custaria uns US$ 70, e 14 dias uns 25. O piloto diz se o Fable gasta como o Opus, e o usuário escolhe depois entre o ano e os 14 dias.
    - **O piloto do Fable gastou uns 2,1 vezes o Opus nos mesmos dois dias:** 141 chamadas, sem nenhuma falha, por US$ 5,08, mais 0,31 da prova. Pelas curvas dos anos completos, um ano do Fable custaria de US$ 67 a 90, e 14 dias de 27 a 40. O resultado fica lacrado.
    - **O ano do Astra terminou, lacrado:** 28 dias e 1.872 chamadas, sem nenhuma falha, repetição ou reserva, por US$ 27,32, no começo da faixa estimada. Nenhum dia bateu no teto. Os juízes custaram US$ 0,04 (Opus) e 0,07 (Astra).
34. **O ano do Fable** (3/nov, o usuário).
    - **O Fable roda o ano inteiro, lacrado,** e não os 14 dias. Assim fica lado a lado com o Opus e o Sonnet, que também rodaram o ano. O usuário pôs US$ 100 na API da Anthropic, e o saldo foi para US$ 118.
    - **O teto total é de US$ 110,** pedido pelo usuário: fica acima da estimativa de 67 a 90 e abaixo do saldo, para a corrida parar pelo teto, não sem crédito. A prova, de uns US$ 0,30, fica fora dele.
    - **O teto do dia sobe de 5 para 10.** O dia do piloto custou uns 2,1 vezes o do Opus, e o dia mais caro do Opus, US$ 2,32, daria uns 4,90 no Fable, perto demais de 5.
    - **A corrida segue se, no dia 2, tiver gastado até 1,5 vez o piloto (US$ 7,62).** O preço foi conferido de novo em 3/nov, sem mudança.
    - **O ano do Fable terminou, lacrado:** 28 dias e 1.731 chamadas, sem nenhuma falha, por US$ 70,12, em 1 h 50, no começo da faixa estimada. No dia 2 o gasto era de US$ 4,65, e nenhum dia bateu no teto. Os juízes custaram US$ 0,07 (Opus) e 0,11 (Astra).
35. **O procedimento e o caderno completo** (8/nov, o usuário; rascunho em `docs/planos/m21-o-procedimento.md`).
    - **Cinco lacunas entre o playbook e o que o modelo recebia.** Elas apareceram ao montar os pedidos reais do mapa a com um modelo falso:
      1. A reflexão da noite, onde o playbook manda procurar a surpresa no caderno, não recebia o caderno.
      2. O caderno só aparecia nas decisões do dia, com os últimos 12 plantios.
      3. A linha do caderno não trazia a estação nem os dias esperados, e à noite não havia mapa.
      4. O experimento era "para amanhã", mas o par de canteiros leva dias, e repetir criava outro registro.
      5. O modelo não via os experimentos antigos nem os vereditos.
    - **Elas valeram para os playbooks 1 e 2 e para todas as corridas sem playbook.** Parte do "o Haiku não aprende" (ADR-0071) pode vir do harness, e não do modelo.
    - **O playbook vira um procedimento operacional, a versão 4,** no estilo do agente de podcast do CampsCast:
      - o que o modelo recebe e onde, pelo nome exato que ele vê;
      - as etapas da manhã, do dia e da noite, na ordem;
      - os formatos fixos da hipótese, do teste, da previsão, das crenças, do resumo e do plano;
      - a escada de confiança;
      - o que nunca e sempre fazer.
    - **O procedimento fica na mente da Morada.** Ele cita o título do manual dela e o calendário. O método genérico e o ofício do gênero saem, e as fazendas 1 e 2 ficam sem playbook. A versão 3, que nunca rodou, fica no git (315a280), e a arena recusa as versões 1 a 3.
    - **A memória ganha o caderno completo,** uma chave que liga com o procedimento e no braço de dados. Sem ela, os pedidos não mudam. Com ela:
      - a tabela do caderno traz a estação com o calendário, os dias esperados e a rega como "X de Y";
      - de manhã aparecem as últimas 12 linhas; à noite, a tabela inteira (até 100), onde ficam as coisas que o avatar conhece, o mapa que ele já viu (as fotos juntas, no formato do `map`) e os seus experimentos;
      - o experimento fica aberto até o veredito.
    - **Os dias esperados saem do manual.** Os números estão num arquivo da mente da Morada (`estacoes.yaml`), e um teste confere que são os mesmos do manual. São números que o modelo já lê, e não os do mundo.
    - **O terreno visto já era guardado pela porta de memória** para a comparação, e agora é guardado inteiro: a memória não guarda nada além do que a porta guarda.
    - **A rodada ganha dois braços do Haiku, de 28 dias.** O braço de dados roda três vezes, com o caderno completo e sem o procedimento: separa o efeito do texto do efeito dos dados. O controle de conhecimento prévio roda uma vez, com o procedimento, no mapa a, com as regras ocultas desligadas: uma crença sobre o lugar ou sobre o que havia antes, num mundo sem essas regras, vem do treino, e não do que o modelo viu. A ideia é do post Project EVE da Anthropic (6/nov), que conferiu se os modelos tinham decorado o histórico do mercado.
    - **O relatório ganha a aderência ao procedimento,** contada por código a partir dos formatos fixos. Ela separa "o procedimento não ajuda" de "o modelo não seguiu o procedimento". No mesmo post, um modelo ignorou a instrução e fez outra estratégia.
    - **As outras ideias do post vão para o `futuro.md`:** a mudança no meio do ano, o procedimento escrito pelo próprio modelo, a postura de risco e os times com um sabotador.
36. **A rodada com o procedimento** (8/nov, o usuário). As cinco decisões de 4/nov foram aprovadas com a tabela de 8/nov (plano do M21, §9):
    - **Quem:** o Haiku três vezes no ano, e o Sonnet, o Opus, o Gemini, o Astra e o Fable por 14 dias, todos com o procedimento, no mapa d e na seed das corridas sem ele. Os braços do Haiku (os dados e o controle) são os da decisão 35. Os outros modelos não ganham braços.
    - **Os tetos** saem do custo das corridas sem playbook até o dia 14: US$ 0,60 por dia e 2 no total nos Haiku, 1,50 e 7 no Sonnet e no Gemini, 3,00 e 19 no Opus, 5,00 e 18 no Astra, 10,00 e 40 no Fable. O Gemini e o Astra vão no flex, como foram sem o playbook.
    - **Um ok para a rodada inteira,** na ordem: os Haiku primeiro, depois os outros, no máximo uma corrida por provedor ao mesmo tempo. Cada corrida para se, no dia 2, tiver gastado mais de 1,5 vez o dia 2 da sua corrida sem playbook. O custo real é dado a cada corrida.
    - **O Fable roda por último e só com o saldo da Console conferido.** Os US$ 20 a mais de 4/nov continuam necessários.
    - **A rodada roda já e fica lacrada** até o fim do ano do usuário, na mesma pasta das corridas sem playbook (`data/arena/m21-terceira-energia`).
    - **O relatório ganha duas seções, de graça, antes de ser gerado:** a aderência ao procedimento (decisão 35), contada pelos formatos fixos em `campsverso_tools/adherence.py`, e "Lado a lado no dia 14", com os totais dos dias 1 a 14 de cada corrida quando a rodada mistura 14 dias com corridas mais longas. As crenças, a prova e o juiz continuam sendo os do fim de cada corrida.

A tela de quem joga ganha a carga da mochila ao lado do inventário ("carga 12,5 de 20", em alerta a partir de 90%) e as recusas em português ("Não deu para colher: não cabe na mochila; guarde alguma coisa no baú.").

## Consequências

- **O orçamento da v0.3 dobra,** e o plano passa a gastar por passos aprovados, não por rodada.
- **O `llm.call.completed.v1` ganha campos opcionais:**
  - o conselheiro;
  - o provedor que atendeu;
  - o id do modelo que a resposta trouxe;
  - as tentativas, quando o adaptador repetiu a chamada;
  - a reserva, quando o flex se esgotou e o provedor normal respondeu.
- **A porta de modelo ganha um segundo provedor,** e a `ModelUsage`, um custo opcional dito pelo provedor.
- **O sandbox passa a retomar um mundo,** e a tela do jogador passa a mostrar o relógio quando pode mandar nele.
- **A vista do jogador passa a ser medida no tick do pulso,** e a tela ganha o `make jogar`, o 1440× e os nomes por língua (ADR-0075).
- **As três fazendas não mudam:** a ferramenta e o conselheiro ficam desligados fora dos braços, e as fitas passam sem regravar.
