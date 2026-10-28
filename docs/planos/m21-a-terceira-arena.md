# Plano do M21 — A terceira arena

*Proposto em 26/out/2026, depois do fechamento do M20, e aprovado em 27/out com as notas do usuário (as decisões 1 a 21; ADR-0074). É o marco da medição final da v0.3 (ADR-0066; o plano macro, §2), no mapa reservado no M19 (ADR-0070, decisão 2):*
- *a rodada do humano;*
- *o Claude em quatro tamanhos, o script 3 e o oráculo;*
- *o GPT-6 Astra e o Gemini 4 Argon pela OpenRouter;*
- *no fim, a rodada controlada do playbook.*

*O plano junta os itens do `futuro.md` marcados para o M21 e dá o destino de cada um.*

**Pronto quando:**
- **O mapa d existe, e ninguém o viu antes da rodada:** nem o script 3 nos testes, nem o usuário antes de jogar.
- **A rodada do humano:** o usuário joga um ano no mapa d, em várias noites, e a partida entra na rodada como uma corrida.
- **A rodada do Claude no mapa d:**
  - os scripts e o oráculo nos quatro mapas;
  - o Haiku três vezes, o Sonnet e o Opus, um ano cada;
  - os dois braços do Haiku: a ferramenta de comparação e o conselheiro;
  - o Fable, depois de um piloto de dois dias, por um ano ou por 14 dias (decisão 18).
- **A rodada das famílias:** o Gemini 4 Argon por um ano e o GPT-6 Astra, depois de um piloto, por um ano ou por 14 dias, com o mesmo manual e a mesma memória, e o custo dito pelo provedor.
- **A rodada controlada do playbook:** o playbook 3 nos modelos da rodada principal, no mesmo mapa e na mesma seed (§9).
- **O relatório final da v0.3** põe todos lado a lado, com:
  - quanto do valor de saber cada um capturou;
  - a prova antes e depois;
  - dois juízes de famílias diferentes;
  - os ajudantes;
  - o custo;
  - a ficha de cada corrida e de cada juiz: o modelo exato, a versão, a rota e o harness.
- **O custo do dia aparece no painel do operador.**
- **As três fazendas ficam intactas:** as fitas e os soaks de hoje passam sem regravar.
- **O gasto cabe no teto novo da v0.3,** de US$ 300 (decisão 21), e cada passo pago roda só depois do ok do usuário, com o custo real do anterior.

## O que o levantamento mostrou

- **Na Morada do Sol, só o Haiku jogou.**
  - Foram 8 corridas de um ano, nos mapas a e b, com de 0 a 91 moedas.
  - O juiz não achou descoberta em nenhuma.
  - O Sonnet e o Opus nunca jogaram a Morada. Na Boa Vista, o Opus fez cinco vezes as moedas do script 2.
- **As réguas estão medidas** (M19, repetidas no M20; as moedas no fim do ano):

  | | Mapa a | Mapa b | Mapa c |
  |---|---|---|---|
  | script 2 (não sabe, não planeja) | 14 | 14 | 14 |
  | script 3 (planeja e aprende) | 2 | 8 | 6 |
  | oráculo (planeja e sabe) | 321 | 587 | 184 |

  - Saber vale de 170 a 573 moedas por mapa.
  - O script 3 aprende a fadiga e, nos mapas a e b, a água. Num ano, porém, ele capta pouco disso em moedas; em colheitas, sim.
- **Falta uma régua do meio:** o script 3 sem aprender. Sem ela, não dá para separar o que vem de planejar do que vem de aprender, porque o script 2 é outro código, mais simples.
- **O ajudante virou um teste de julgamento** (ADR-0073): com as diárias, todo contrato forçado perdeu dinheiro. A mente tem as ferramentas de contratar desde o M20, então a arena já mede quem contrata por impulso.
- **O custo de uma corrida de um ano na Morada:**
  - o Haiku custa de US$ 0,66 a 0,71, com umas 950 chamadas, em 53 minutos;
  - uma chamada na Morada lê uns 37% mais cache que na Boa Vista: 30 mil tokens, contra 22 mil, no Haiku;
  - com a mistura de tokens do M14, o Sonnet deve custar de US$ 15 a 25 e o Opus de US$ 30 a 45, de 2 a 3 horas cada.
- **Os preços do dia** (a lista pública da OpenRouter em 27/out; US$ por milhão de tokens):

  | Modelo | Entrada | Saída | Cache lido | Um ano na Morada (estimativa) |
  |---|---|---|---|---|
  | Gemini 4 Argon | 2 | 10 | 0,10 | 12 a 25 |
  | Sonnet 5.5 | 2 | 10 | 0,10 | 15 a 25 |
  | Opus 5.5 | 4 | 20 | 0,20 | 30 a 45 |
  | Fable 5.1 | 10 | 50 | 0,25 | 65 a 95 |
  | GPT-6 Astra | 10 | 50 | 1,00 | 100 a 150 |

  - Cada chamada relê uns 30 mil tokens de cache. No Astra, o cache lido custa cinco vezes o do Opus, e o ano sai por umas três vezes o do Opus.
  - A nossa tabela de preços cobra o cache lido do Sonnet 5.5 a US$ 0,20, e a lista mostra 0,10: confiro no passo 7.
- **O orçamento:**
  - a v0.3 tinha US$ 150 (ADR-0066), e gastamos uns US$ 8 até aqui;
  - em 27/out, o usuário pôs US$ 100 na Console, que foi a uns US$ 149, e já tem US$ 50 na OpenRouter.
- **A porta de modelo e a OpenRouter falam formatos diferentes.**
  - A porta fala o formato da Messages API: os blocos `text`, `tool_use` e `tool_result`.
  - A OpenRouter fala o formato de chat da OpenAI, com `tool_calls`, e devolve na resposta o custo da chamada (`usage.cost`).
  - O evento `llm.call.completed.v1` já tem `provider` e `cost_usd`.
- **O mapa d só existe como promessa:** "desenhado só no M21, com outra receita" (ADR-0070, decisão 2).
- **A rodada do humano tem dois problemas:**
  - **O tempo:** o ano, a 72×, leva 9 horas na tela, e o sandbox sempre cria um mundo novo. Não dá para jogar em várias noites.
  - **O usuário conhece as regras ocultas.** A partida dele não mede o aprender. Ela mede o saber fazer, e se compara com o oráculo, que também sabe.
- **A prova tem dois defeitos de leitura** (rodada do M19):
  - a pergunta dos corvos fala de 30 tiles, e o modelo do script 3 lê uma faixa de 16 a 32, que mistura tiles com e sem corvos;
  - com 19 atributos, o intervalo de 90% deu um falso positivo: a repetição "acelerou" num mundo sem a regra.
- **O que o `futuro.md` marcou para o M21:**
  - a OpenRouter e o custo no painel;
  - mudar o teto com o mundo vivo, e a guarda caída pausar o mundo;
  - as medições do prompt em inglês e da foto em prosa;
  - os dois defeitos da prova;
  - o conselheiro e a ferramenta de comparação;
  - mais seeds para o Sonnet e o Opus, e o playbook como braço deles;
  - talvez, o agente que joga de novo com o que aprendeu.

  A ADR-0070 (nota 13) pediu também um segundo juiz para as corridas do Opus. A §10 diz o que fica e o que sai.

## 1. O mapa d

- **É uma receita como as outras:** a casa, o centro, a estrada e a entrada ficam no lugar; a água e a mata mudam.
- **O que a receita promete,** conferido pelo teste no mapa gravado:
  - a terra boa (até 4 tiles da água) fica num lugar que nenhum dos três mapas usou;
  - quem aprendeu só o lugar erra: o d não tem água nem no leste do mapa a, nem na coluna do córrego do b, nem nas lagoas do c;
  - um explorador alcança a terra boa na primeira estação;
  - **saber vale** (decisão 22): num ano, o oráculo passa o script 3 fixo por pelo menos 150 moedas e 15 colheitas, conferido por um teste com um ano de cada.
- **Este plano não diz onde fica a água,** porque o usuário vai jogar nesse mapa. A receita fica no repositório, e o print vai para a aprovação dele depois da partida (decisão 2).
- **O mundo é o `farm-morada-do-sol-04`,** com a mesma seed dos outros três, então a diferença entre eles é só o mapa. O mapa visual e o modo de assistir funcionam como nas outras variantes.
- **O script 3 vê o d pela primeira vez na rodada.** O mapa nunca entra nos testes do script 3: é o conjunto de teste que ninguém viu.

## 2. A rodada do humano

- **No mapa d, antes de o usuário ver qualquer corrida nele,** no sandbox com o Camps e os ajudantes. As réguas de graça rodam no d antes, mas os números delas só aparecem depois que ele terminar de jogar.
- **Um ano, em várias noites** (decisão 16):
  - 144× com o Camps acordado, uns 7 minutos por dia do jogo;
  - 720× enquanto ele dorme;
  - pausa sempre que o usuário quiser pensar.

  O ano cabe em umas 3 h 30 min de relógio, mais as pausas, em duas ou três noites.
- **A velocidade não mexe na medição dos outros:**
  - cada corrida é um mundo próprio, e as regras andam por ticks, não pelo relógio da parede;
  - os modelos jogam com o mundo esperando por eles, e a pausa livre dá ao humano as mesmas condições;
  - a velocidade só pesa na partida do humano: mais rápido, menos tempo para reagir se ele não pausar.
- **A tela do jogador ganha o relógio:** os botões de pausa e de velocidade (72×, 144× e 720×) e um atalho de pausa, só quando o gateway aceita os comandos do relógio, como no sandbox. O painel do operador ganha o 144×.
- **O sandbox passa a retomar um mundo.** `make sandbox RETOMAR=data/sandbox/<pasta>` continua de onde a partida parou, pelo snapshot e pelo diário de entradas (a recuperação transparente da ADR-0044).
- **A partida entra na rodada** por `make arena-humano`, como a ADR-0066 previu.
- **A comparação:**
  - o humano é comparado no fim do ano, como todos, e o corte do dia 7 continua no relatório;
  - a linha dele fica junto do oráculo, com a nota de que ele sabe as regras.

## 3. As corridas

Todas na seed da Morada (20261022), sem playbook (decisão 6). As corridas dos modelos têm memória, o caderno de campo e o experimento da noite. De uma corrida para outra, só muda o controlador.

**Um passo por vez** (decisão 17). Cada passo pago roda só depois do ok do usuário, com o relatório e o custo real do anterior. A ordem é esta:
1. o humano;
2. o Haiku três vezes;
3. os braços do Haiku;
4. o Sonnet;
5. o Opus;
6. o Gemini;
7. o Astra;
8. o Fable;
9. a rodada do playbook.

**A rodada `terceira`, do Claude** (no mapa d, a menos que a linha diga outro):

| Corrida | Quem | Dias | Teto (US$/dia · total) | Custo estimado (US$) |
|---|---|---|---|---|
| script2, script3 e oraculo, nos mapas a, b, c e d | as réguas | 28 | – | 0 |
| script3-fixo, nos mapas a, b, c e d | o script 3 sem aprender (§4) | 28 | – | 0 |
| haiku, haiku-r2, haiku-r3 | o Haiku 5.5, três vezes | 28 | 0,60 · 10 | 2,10 |
| haiku-comparar, haiku-comparar-r2 | o Haiku com a ferramenta de comparação (§5) | 28 | 0,60 · 10 | 1,50 |
| haiku-conselheiro | o Haiku com o conselheiro na reflexão (§6) | 28 | 1,00 · 12 | 3 a 6 |
| sonnet | o Sonnet 5.5 | 28 | 1,50 · 30 | 15 a 25 |
| opus | o Opus 5.5 | 28 | 2,50 · 55 | 30 a 45 |
| fable-piloto | o Fable 5.1 | 2 | 5,00 · 12 | 5 a 7 |
| fable | o Fable 5.1 | 14 ou 28 | 5,00 · 100 | 33 a 48, ou 65 a 95 |

**A rodada `familias`,** no mapa d, depois do adaptador da OpenRouter (§7):

| Corrida | Quem | Dias | Teto (US$/dia · total) | Custo estimado (US$) |
|---|---|---|---|---|
| gemini | o Gemini 4 Argon | 28 | 1,50 · 30 | 12 a 25 |
| astra-piloto | o GPT-6 Astra | 2 | 8,00 · 15 | 7 a 11 |
| astra | o GPT-6 Astra | 14 ou 28 | 8,00 · 160 | 50 a 75, ou 100 a 150 |

- **O Haiku corre três vezes,** porque as oito corridas da Morada mostraram que ele varia muito: de 0 a 91 moedas no mesmo mundo. A ferramenta de comparação corre duas vezes, e o conselheiro, uma.
- **O Sonnet, o Opus, o Fable, o Gemini e o Astra correm uma vez,** como decidido na ADR-0066 (decisão 12). Mais seeds, só se a rodada pedir, na rodada 3 (§10).
- **Todos jogam um ano,** porque a comparação é com as réguas, que jogam o ano. Se o Opus passar do dobro do custo estimado por dia, a corrida cai para 14 dias, como no M14.
- **O Fable e o Astra começam por um piloto de dois dias** (decisão 18), uma corrida à parte. Depois do Opus, o usuário escolhe entre um ano e 14 dias, com o custo real do piloto:
  - se o Opus mostrar o que aprendeu antes do dia 14, os 14 dias bastam, e o relatório compara todos também no dia 14;
  - se nem os 14 dias do Astra couberem, o GPT-6.1 Sol, com o preço do Sonnet, é o plano B.
- **Cada modelo faz a prova antes,** numa chamada com a memória vazia, **e depois.**
- **As corridas de script nos mapas a, b e c** repetem o M19 número por número, e conferem que nada mudou.

## 4. A régua do meio: o script 3 sem aprender

- **É o mesmo código do script 3,** com a crença presa no ponto de partida (`learn: false` no `farmer3.yaml`).
  - Ele planeja o capital e usa a feira, as encomendas e o tacho, como o script 3.
  - Mas escolhe pela média da crença inicial e não testa.
- **Com ele, o relatório reparte em três o valor de cada controlador:**
  - **planejar:** o script 3 fixo menos o script 2;
  - **aprender:** o controlador menos o script 3 fixo;
  - **saber:** o oráculo menos o script 3 fixo, que é o teto.
- **A fração do valor de saber capturada** é (o controlador − o fixo) ÷ (o oráculo − o fixo), em moedas e em colheitas. Abaixo de zero, o controlador foi pior que não aprender.
- **É de graça,** como as outras réguas.
- **O que a medida mostrou** (28/out, adendo da ADR-0074). Num ano, o fixo fez 267 moedas, 72 colheitas e 5 dias de fome, igual nos três mapas:
  - planejar vale muito: o fixo fica 253 moedas acima do script 2;
  - aprender, do jeito do script 3, custa mais do que rende num ano: ele fica umas 260 moedas abaixo do fixo;
  - o oráculo fica 54 moedas acima do fixo no mapa a, 320 acima no b e 83 abaixo no c.

  Por isso a fração vale como medida principal só no mapa d, que promete que saber vale (decisão 22). Nos mapas a, b e c, o relatório põe as quatro réguas lado a lado.

## 5. A ferramenta de comparação

- **O que faz:** lê o caderno de campo do próprio avatar e devolve os plantios que fugiram do esperado, os que levaram mais ou menos dias que o normal para a cultura e a estação. Cada um vem com os plantios parecidos que não fugiram e com as colunas em que eles diferem:
  - o lugar: a distância à água, à mata, ao caminho e à porta;
  - o que havia antes no canteiro;
  - o adubo, a rega e a estação.
- **O modelo escolhe o teste.** A ferramenta faz a conta que o script 3 faz em código e deixa o raciocínio para o modelo. É a pergunta que a rodada do playbook deixou: o Haiku falha por não saber o método, ou por não conseguir fazer a conta?
- **Só usa fatos do próprio avatar.** As colunas são as suspeitas do script 3, com distratores, que a ADR-0070 julgou justas (princípio 5). A ferramenta não nomeia regra, e o teste de palavras proibidas lê a descrição dela.
- **Fica em `libs/mind`, ao lado do caderno,** e só é ligada no braço (`Spec.comparar`). Desligada, o pedido é o de hoje, e as fitas não mudam.
- **Funciona com qualquer modelo,** até pela OpenRouter. Nos outros modelos, ela só entra depois dos braços do Haiku, decidida para a rodada do playbook (decisão 19).

## 6. O conselheiro

- **O que é:** a ferramenta de conselheiro da API (beta `advisor-tool-2026-03-01`). O Haiku consulta um modelo mais capaz no meio da geração, na mesma chamada; o conselheiro lê a conversa e devolve um plano ou uma correção.
- **Onde entra:** só na reflexão da noite, onde a mente escolhe o experimento do dia seguinte. São umas 28 consultas por corrida.
- **O conselheiro é o Opus 4.8** (decisão 9). O conselho volta dentro da resposta do Haiku, num bloco `advisor_tool_result`:
  - com o Opus 4.8, o bloco traz o texto (`advisor_result`), e o relatório pode mostrar o que ele aconselhou e se o Haiku seguiu;
  - com o Opus 5.5 e os mais novos, o bloco traz um conteúdo criptografado (`advisor_redacted_result`): o Haiku lê, porque a API o decifra quando a conversa volta para ela, mas o nosso código, o arquivo, o relatório e o juiz não.
- **Só no Haiku:**
  - é uma ferramenta do servidor da Anthropic, então o GPT e o Gemini não a têm;
  - o conselheiro precisa ser pelo menos tão capaz quanto quem joga. O Sonnet 5.5 não aceita o Opus 4.8, e todos os conselheiros que ele aceita devolvem o conselho criptografado. Acima do Opus 5.5, só há o Fable, também criptografado.
- **O que pede no código:**
  - o adaptador da Anthropic na API beta, com os blocos do conselheiro devolvidos à janela sem mudança, e o `pause_turn`;
  - o uso do conselheiro (`usage.iterations`, cobrado na tarifa dele) no medidor e na guarda;
  - um campo opcional `advisor` no `llm.call.completed.v1`, com o modelo, os tokens e o custo do conselheiro; o `cost_usd` continua sendo o total.
- **Confiro a documentação na hora,** porque o beta pode ter mudado.

## 7. A OpenRouter

- **É um segundo adaptador da porta de modelo** (`model_openrouter.py`, só em `libs/adapters`), com `httpx`:
  - ele traduz os blocos da Messages API para o formato de chat (as mensagens, as `tool_calls` e a mensagem da ferramenta) e de volta;
  - ele leva as ferramentas estritas, o esforço como `reasoning.effort` e os marcadores de cache onde o provedor aceita;
  - o custo vem da resposta (`usage.cost`): a `ModelUsage` ganha um `cost_usd` opcional, que o medidor usa no lugar da tabela.
- **Não é um padrão oficial, e sim um roteador:** uma conta, uma chave e um formato só para centenas de modelos. O formato de chat da OpenAI virou um padrão de fato. Cada laboratório tem a sua API própria, e as novidades chegam nela primeiro. Por isso:
  - os Claude continuam na API da Anthropic, como em todas as rodadas;
  - o GPT e o Gemini passam pela tradução da OpenRouter, que é parte do harness e entra na ficha;
  - o provedor fica fixo em cada modelo (`provider.order`, sem `allow_fallbacks`), e cada chamada grava quem atendeu, porque a OpenRouter pode mandar o mesmo modelo para provedores diferentes.
- **A conta e a chave são do usuário.**
  - Ele já tem US$ 50 em créditos e põe `OPENROUTER_API_KEY` no `.env` (eu não leio o `.env`).
  - Antes da rodada, `make llm-smoke PROVEDOR=openrouter` faz uma chamada de centavos.
- **Os modelos** (decisão 11), escolhidos pelo usuário em 27/out:
  - o GPT-6 Astra (`openai/gpt-6-astra`) e o Gemini 4 Argon (`google/gemini-4-argon`);
  - são os mais bem colocados no índice de inteligência da Artificial Analysis depois dos três Claude, do Muse Wonder (sem API) e do Kimi K3.1 Pro (fora do escopo de longo prazo);
  - os ids e os preços são conferidos na lista da OpenRouter no dia de cada corrida.
- **No CI,** os testes usam um transporte falso: o CI nunca chama a OpenRouter.

## 8. A medição e o relatório

- **Dois juízes** (decisão 12), em todas as corridas com memória: o Opus 5.5, como no M19, e o GPT-6 Astra.
  - Antes, o Astra é conferido contra o gabarito feito à mão e os controles (47 e 28 vereditos).
  - Na corrida do Opus, vale como referência o veredito do Astra; na do Astra, o do Opus.
  - As discordâncias entre os dois vão para o relatório.
- **A ficha de cada corrida e de cada juiz:**
  - o id exato do modelo que a resposta trouxe e a data;
  - a rota: a API da Anthropic, ou a OpenRouter e o provedor que atendeu;
  - o esforço ou o raciocínio pedido;
  - o harness: a versão da mente (o commit), o hash do prompt, as ferramentas, a memória e o playbook, se houver; no juiz, a versão da rubrica e o hash do prompt.
- **A prova corrigida:**
  - a pergunta dos corvos passa de 30 para 40 tiles da porta, onde o modelo do script 3 lê uma faixa que só tem corvos. A resposta certa não muda, porque as duas distâncias ficam além dos 18 tiles da regra;
  - o script 3 só diz "aprendeu" quando o intervalo exclui "nenhum efeito" com a correção pelos 19 atributos, o que leva o intervalo de 90% para uns 99,5%;
  - a leitura nova é refeita nas corridas do M19 e do playbook, e o relatório diz o que mudou.
- **O relatório final da v0.3** (`docs/arena/<data>.md`) traz:
  - a tabela principal no mapa d, com todos lado a lado e as réguas;
  - a fração do valor de saber capturada (§4), em moedas e em colheitas, no mapa d;
  - os scripts nos quatro mapas, para ver se o script 3 vai tão bem no d quanto nos outros;
  - a prova antes e depois, os dois juízes, as métricas de exploração e os experimentos da noite;
  - os ajudantes: quem contratou, por quantos dias e quanto perdeu;
  - os braços do Haiku: o que a ferramenta e o conselheiro mudaram;
  - o humano, no fim do ano e no dia 7;
  - a rodada do playbook, contra as mesmas corridas sem ele;
  - o custo e a ficha de cada corrida.
- **O custo no painel do operador:**
  - o gasto do dia e o total de cada mente, a partir dos `llm.call.completed` e dos `ops.budget.*`, que o gateway já lê do `observer`;
  - no modo de assistir, o custo de cada corrida.

## 9. A rodada controlada do playbook

- **Quando:** o último passo pago, depois da rodada principal e dos braços (decisão 20).
- **A pergunta:** o playbook não mudou o Haiku em sete corridas (ADR-0071). Ele aprendeu a forma do método, mas não o assunto: em 223 experimentos, nenhum comparou lugares, e quatro de cada cinco foram sobre a rega e a chuva. Há duas hipóteses:
  - **a capacidade:** o difícil é escolher de que suspeitar num caderno de 30 mil tokens, e o playbook ensina o procedimento, não onde prestar atenção;
  - **o próprio playbook:** a regra "não troque de assunto antes de resolver" pode ter prendido o Haiku num assunto ruidoso, que nunca se resolve.

  A rodada sem playbook separa as duas: se os modelos maiores compararem lugares sozinhos, a barreira do Haiku é a capacidade.
- **O playbook 3** é escrito depois da rodada principal, só com método:
  - nada do mapa d, nem das regras ocultas;
  - passa no teste de palavras proibidas;
  - o usuário o lê antes da rodada.
- **Quem:** os modelos da rodada principal e, se a decisão 19 disser, os braços nos outros modelos.
- **As mesmas condições:** o mapa d, a seed, a memória e os dias das corridas sem playbook; só o playbook muda.
- **O comprimento sai dos custos reais.** Com 14 dias, comparados ao dia 14 das corridas sem playbook, a rodada custa a metade.
- **Uma corrida por modelo e por condição:** o relatório diz que a diferença de uma corrida só é indício, não prova.

## 10. O que fica de fora

| Item | Destino | Por quê |
|---|---|---|
| Mudar o teto com o mundo vivo (`cmd.ops.budget.set`), e a guarda caída pausar o mundo | v0.4 | a arena roda em processo, com o teto da corrida; os dois servem à pilha viva, que o escritório vai usar por muito tempo |
| Medir o prompt em inglês e a foto em prosa | v0.4 | mudar o prompt agora quebra a comparação do M19 ao M21; a mente do escritório é nova e pode nascer medida |
| Mais seeds para os modelos grandes e o agente que joga o segundo ano com a memória do primeiro | a rodada 3, decidida com os resultados | só faz sentido se a rodada mostrar aprendizado, e o teto diz quanto cabe |
| O conselheiro nos outros modelos | sai | é do servidor da Anthropic, e acima do Haiku o conselho volta criptografado |
| O ajudante LLM | quando os modelos simples forem bem | a nota do usuário no M20 |
| A estação no modelo do script 3 | `futuro.md` | muda a régua que o M19 e o M20 mediram |
| A rodada do humano na Boa Vista | sai | a da Morada a substitui, e o tempo do usuário é o recurso mais curto |

## 11. Os contratos

- **`llm.call.completed.v1`** ganha campos opcionais:
  - `advisor`, com o modelo, os tokens e o custo do conselheiro (§6);
  - o provedor que atendeu na OpenRouter e o id do modelo que a resposta trouxe, para a ficha (§8).
- **Nada mais muda:** o `provider` e o `cost_usd` já existem, e o `map:` do mundo novo é configuração.

## 12. Testes do marco

- **O mapa d:** a receita cumpre as promessas, e nenhum teste do script 3 usa o mapa.
- **O script 3 fixo:** com `learn: false`, a crença não muda no ano, e ele não planta par de teste.
- **A ferramenta de comparação:**
  - num caderno feito à mão, ela devolve o plantio que fugiu e as colunas certas;
  - a descrição passa no teste de palavras proibidas;
  - desligada, as fitas das três fazendas passam sem regravar.
- **O conselheiro,** no transporte falso:
  - os blocos do conselheiro voltam à janela sem mudança;
  - o `pause_turn` continua a chamada;
  - o medidor soma as duas tarifas;
  - o evento valida com o campo `advisor`.
- **A OpenRouter,** no transporte falso:
  - a tradução de ida e volta: o texto, a ferramenta, o resultado, a ferramenta estrita e o raciocínio;
  - o custo que vem da resposta;
  - o provedor fixo no pedido, e o que atendeu, gravado no evento;
  - os erros classificados como na Anthropic.
- **A prova:** com a leitura nova, o falso positivo some nas corridas antigas, e a pergunta dos corvos cai na faixa certa.
- **O sandbox que retoma:** um mundo de sandbox parado e retomado continua no mesmo tick, com o mesmo estado.
- **O relógio na tela do jogador:** os botões aparecem só quando o gateway aceita os comandos do relógio, e o atalho pausa e retoma.
- **O painel:** o custo do dia a partir de eventos sintéticos, no gateway e na tela.
- **O playbook 3:** passa no teste de palavras proibidas.
- **As três fazendas:** as fitas e os soaks de hoje passam sem regravar.

## 13. Ordem do trabalho

O código vem primeiro e é de graça; as corridas pagas vêm uma por vez, cada uma com o ok do usuário.

1. **O plano e a ADR-0074.**
2. **A prova corrigida e o script 3 fixo,** com a leitura refeita nas corridas antigas, de graça.
3. **O mapa d e o mundo `-04`,** e as réguas nos quatro mapas, com os números do d guardados até o usuário jogar.
4. **O sandbox que retoma e o relógio na tela do jogador.** A partir daqui, o usuário pode jogar quando tiver as noites.
5. **A ferramenta de comparação.**
6. **O conselheiro,** com uma chamada de fumaça, de centavos.
7. **O custo no painel, a ficha e a tabela de preços conferida.**
8. **A OpenRouter:** o adaptador, a fumaça com a chave do usuário e o Astra conferido no gabarito como segundo juiz.
9. **A rodada do humano,** quando o usuário jogar.
10. **As corridas pagas,** na ordem da §3, cada uma com o relatório e o custo real antes do ok para a próxima. Antes do Astra longo, o usuário põe mais créditos na OpenRouter.
11. **O playbook 3 e a rodada controlada.**
12. **O relatório e o fechamento:** a bíblia 3, o diário, o `futuro.md`, os custos, o README e o CLAUDE.md. A decisão da rodada 3 vai para o usuário com os números na mão.

Cada passo vira um ou mais commits, com `make check` antes de cada um. O push fica para quando o usuário disser.

## 14. Custo

| Passo | Onde | US$ |
|---|---|---|
| O Haiku e os braços | Console | 7 a 10 |
| O Sonnet | Console | 15 a 25 |
| O Opus | Console | 30 a 45 |
| O Fable: o piloto e 14 dias (ou um ano) | Console | 38 a 55 (70 a 102) |
| O juiz Opus, as provas e as fumaças | Console | 2 a 4 |
| O Gemini | OpenRouter | 12 a 25 |
| O Astra: o piloto e 14 dias (ou um ano) | OpenRouter | 57 a 86 (107 a 161) |
| O juiz Astra, no gabarito e nas corridas | OpenRouter | uns 5 |
| A rodada do playbook, 14 dias, seis modelos | as duas | 115 a 170 |

- **Com o Fable e o Astra em 14 dias,** a rodada principal fecha a v0.3 entre uns US$ 175 e 265. A rodada do playbook vem por cima, e o teto de US$ 300 decide quantos modelos entram nela.
- **A Console,** com uns US$ 149, paga a parte da Anthropic na rodada principal. A rodada do playbook pede outra reposição.
- **A OpenRouter,** com US$ 50, paga o Gemini, o juiz e o piloto do Astra; antes do Astra longo, pede mais créditos, mais 5,5% na compra.
- **O desenvolvimento:** umas três sessões, mais uma tarde de máquina para cada passo pago e as noites do usuário para jogar.

## 15. Decisões

Aprovadas em 27/out. As notas do usuário estão na ADR-0074.

1. **O escopo:** o mapa d, o humano, a régua do meio, o Claude, os dois braços do Haiku, a OpenRouter com dois juízes, a prova corrigida, o relatório final e o custo no painel. O resto da §10 fica de fora.
2. **O mapa d às cegas:** o usuário aprova as promessas da receita e vê o print só depois de jogar.
3. **A rodada do humano no mapa d,** com a linha ao lado do oráculo. A decisão 16 a estende ao ano inteiro.
4. **A régua do meio:** o script 3 sem aprender nos quatro mapas, e a fração do valor de saber capturada como a medida principal do relatório.
5. **As corridas da §3,** um passo por vez (decisão 17).
6. **Sem playbook em nenhuma corrida da rodada principal,** nem no Sonnet, nem no Opus. Depois dela, a rodada controlada do playbook (decisão 20).
7. **A ferramenta de comparação** como braço do Haiku, ligada por corrida.
8. **O conselheiro** na reflexão da noite, como braço do Haiku.
9. **O Opus 4.8 como conselheiro,** com o conselho em texto.
10. **A OpenRouter com `httpx`,** num adaptador próprio, com o custo vindo da resposta e o provedor fixo.
11. **O par da ponta:** o GPT-6 Astra e o Gemini 4 Argon, em vez do GPT-6.1 Sol.
12. **Dois juízes,** o Opus 5.5 e o GPT-6 Astra, cada um a referência na corrida da família do outro, com a ficha de cada corrida e de cada juiz.
13. **A prova corrigida:** a pergunta dos corvos a 40 tiles e a correção pelos 19 atributos na leitura do script 3, refeita nas corridas antigas.
14. **O custo no painel do operador,** sem mudar o teto com o mundo vivo.
15. **Os créditos:** a Console foi a uns US$ 149, e a OpenRouter tem US$ 50; mais créditos, só com o custo real na mão.
16. **O ano do humano:** 144× com o Camps acordado, 720× dormindo, pausa livre e o sandbox retomando, com o relógio na tela do jogador.
17. **Um passo por vez,** na ordem da §3, com o relatório e o custo real antes do ok para o próximo.
18. **O Astra e o Fable começam por um piloto de dois dias,** e o comprimento (um ano ou 14 dias) é escolhido depois do Opus, com o custo real. O Fable entra assim.
19. **Os braços nos outros modelos** se decidem depois dos braços do Haiku, para a rodada do playbook.
20. **A rodada controlada do playbook** no fim do M21: o playbook 3, os modelos da rodada principal, o mesmo mapa e a mesma seed, e o comprimento pelos custos reais.
21. **O teto da v0.3** sobe de US$ 150 para 300, com cada passo pago aprovado com o custo real.
22. **O mapa d promete que saber vale,** e a fração do valor de saber capturada é a medida principal só nele (28/out, depois da medida da régua do meio).
