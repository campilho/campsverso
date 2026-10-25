# Plano do M19 — Os controladores e a medição

*Proposto em 25/out/2026, depois do fechamento do M18. É o marco da medição da v0.3 (ADR-0066): o fazendeiro-script 3 e o oráculo, o caderno de campo da mente, a prova do mundo e o juiz, as métricas de exploração e as variantes do mapa, cujo desenho a ADR-0066 (decisão 18) deixou para este plano. Aprovado em 25/out/2026 (ADR-0070), com as notas do usuário no fim da §14 e a composteira incluída no script 3.*

**Pronto quando:**
- **As variantes do mapa:** a Morada do Sol existe em três mapas, o de hoje e dois com a água em outro lugar. A casa, o centro e a entrada da fazenda ficam onde estão. O arquivo do mundo escolhe o mapa, e a tela desenha o certo. Uma quarta variante fica reservada para a arena final.
- **O fazendeiro-script 3:**
  - planeja o capital e usa a feira, as encomendas e o tacho;
  - **descobre por experimento** a várzea, os corvos e a fadiga do solo nos três mapas, sem nenhuma regra oculta no código ou nos dados;
  - com a R-001 desligada, não "descobre" uma várzea que não existe;
  - ganha mais moedas que o script 2 nos três mapas.
- **O oráculo,** o mesmo script sabendo as regras, dá o teto em cada mapa.
- **A mente:**
  - **o caderno de campo** mostra numa tabela curta o que aconteceu em cada canteiro;
  - **a reflexão pode propor um experimento** para o dia seguinte e conferir a previsão na noite depois;
  - **o resumo da reflexão** não vaza mais marcação de ferramenta.
- **A medição:**
  - as **métricas de exploração**;
  - a **prova do mundo,** feita antes e depois da corrida;
  - o **juiz** que lê as crenças, conferido contra um gabarito feito à mão das arenas do M12 e do M14.
- **As fazendas 1 e 2 intactas,** com as mesmas fitas e os mesmos soaks.

## O que o levantamento mostrou

- **O script 2 é cego, e quem perde é ele.** No ano da Morada do Sol com a economia: 48 plantios, 38 colheitas e 17 moedas no fim.
  - Ele repete o rabanete, e a fadiga do solo leva a planta de 3 para uns 5,5 dias.
  - Vende tudo na caixa, que agora lembra, e não usa a feira nem o tacho.
  - Explorar, ele explora: vê o mapa inteiro entre os dias 2 e 3. O que falta é tirar proveito do que vê.
- **A distância até um bom jogador é grande:** no M14, na Boa Vista, o Opus fez 1.143 moedas, e o script 2, 220.
- **O mapa de hoje junta duas regras.** A R-001 vale a até 4 tiles de qualquer água, e a água é:
  - o rio na borda leste, a uns 50 tiles da porta;
  - a lagoa do morro, entre 15 e 26 tiles da porta, bem na linha dos corvos (R-002: mais de 18 tiles da porta).

  A terra boa fica onde o corvo come. Isso vale para um mapa só: noutro, a mesma regra pede outra estratégia.
- **O mapa não tem gerador no repositório.** O do M16 nasceu de um script descartável e depois foi editado à mão: o fogão, o quadro, a barraca e a composteira entraram assim.
- **O manual não fala de geografia,** só das construções, e elas ficam no mesmo lugar em todas as variantes. Uma variante não pede manual novo.
- **O mundo já sabe trocar uma peça, e a tela já sabe qual mapa desenhar.**
  - O arquivo do mundo tem `rules_file`, que troca o arquivo de regras do cartucho.
  - O `session.started` já leva o id do mapa.
  - O gateway já serve mapas por id.
- **A percepção está no arquivo** (`perception.delivered` e `perception.updated`). Os tiles vistos se contam depois, sem mexer no kernel.
- **O vazamento da reflexão continua.** Na corrida do M18, 4 de 7 noites do Haiku na Morada; nas arenas, de 9 a 19 noites em 30.
  - O resumo termina em `</summary> <parameter name="plan">`, com o plano repetido.
  - A ferramenta da reflexão já é estrita: a gramática garante o formato do pedido, mas não o que vai dentro de um texto.
- **As heurísticas de descoberta erram.** No M14, a "margem" de lucro foi lida como margem do rio, e regar todo dia como o tomate que murcha. Falta uma prova com gabarito e um juiz que leia as crenças.
- **A mente que passou fome por uma encomenda** (M18): o Haiku guardou os rabanetes de um pedido em vez de comer e desmaiou no dia 5. O M19 não muda o manual por isso: o caderno e o experimento da noite são a resposta, e a métrica de desmaios mostra se funcionou.
- **Rodar um script é barato.** Dez dias da Morada do Sol em processo levam 4,2 s (5.165 eventos), e um ano, uns 12 s. O CI pode rodar o script 3 o ano inteiro em cada mapa.

## 1. As variantes do mapa

**Uma receita sobre o mapa de hoje.**
- **Fica onde está:** a casa e o centro (o poço, a caixa, o baú, a composteira), a estrada principal, o ramal do sul e a entrada com o quiosque, o quadro e a barraca.
- **Muda:** a água (o rio, um córrego, lagoas) e as matas em volta dela.

Cada variante é uma receita curta num arquivo do cartucho: onde passa a água, que matas entram ou saem. Um script do repositório aplica a receita sobre o mapa de hoje e confere o resultado (§11). O mapa de hoje é a variante `a`, e o arquivo dele não muda.

| Variante | A água | O que ela pergunta |
|---|---|---|
| **a — o rio** | a de hoje: a lagoa no morro, na linha dos corvos, e o rio na borda leste | a terra boa fica longe e no caminho dos corvos: rende com espantalho |
| **b — o córrego** | um córrego de norte a sul a uns 14 tiles da porta; a estrada passa por cima dele, numa ponte. Sem rio e sem lagoa | a terra boa fica perto e a salvo dos corvos, e começa a 2 tiles do poço, onde o script 2 cava: quem não testa passa raspando |
| **c — as lagoas** | três lagoas pequenas, no morro, na clareira e a leste, todas a mais de 22 tiles da porta; sem rio | a terra boa só existe longe: sem espantalho, metade das maduras vira comida de corvo |
| **d — reservada** | desenhada só no M21, com outra receita | nunca entra nos testes do script 3: prova que ele não decorou os três mapas |

As três juntas cobrem o encontro da R-001 com a R-002: perto e seguro (b), longe e protegido (c), e o meio do caminho (a). As variantes vão como print para a sua aprovação antes do commit.

**Como o mundo escolhe:**
- o arquivo do mundo ganha `map:` (o nome da variante), como já tem `rules_file`;
- o cartucho lista os seus mapas, e o kernel carrega o escolhido depois do cartucho;
- o id do mapa (`morada-b`) vai no `session.started`;
- um mundo que já existe recusa trocar de mapa, como recusa trocar de seed;
- mundos novos `farm-morada-do-sol-02` (b) e `farm-morada-do-sol-03` (c), com a mesma seed do `-01`, para que a diferença entre eles seja só o mapa.

**Na tela:**
- `make mapa-visual` regrava o mapa visual de cada variante;
- o `art.json` da Morada lista os mapas visuais por id, e a tela escolhe pelo id do `session.started`;
- no modo de assistir, cada corrida aparece com o seu mapa.

## 2. O fazendeiro-script 3

**A linha de base honesta.** Ele sabe o manual e não sabe nenhuma regra oculta, mas planeja e experimenta. Vê o que o LLM vê: a mesma percepção e o mesmo catálogo de ações.

**O que ele herda do script 2:** a lembrança e o terreno, a exploração da fronteira, o calendário de plantio, comer, dormir e a sopa. O código é reaproveitado, não copiado.

**O plano do dia, de manhã:**
- **A projeção do caixa:** as moedas, o que a caixa paga às 06:00 e o que vence.
- **O retorno por moeda por dia** de cada cultura da estação em cada lugar candidato:
  - o ganho é o preço que se vê, vezes a chance de a planta não se perder, menos a semente;
  - a conta divide pelos dias esperados e desconta a energia de andar até o lugar.
- **A escolha gulosa:** o que o caixa, a energia e as cargas do regador pagam, do melhor retorno para baixo.
- **Os investimentos:**
  - o regador grande e o arado, quando o retorno paga;
  - o espantalho, quando a perda esperada num grupo de canteiros passa do preço dele (60);
  - o tacho, quando sobra caixa e há na estação a cultura de uma receita.

**O modelo do mundo, o que ele aprende:**
- **O ritmo.** Ele compara os dias que cada planta levou com os que o manual e a estação prometem, e procura o que explica a diferença. Os candidatos são atributos visíveis:
  - do tile: a distância à água, à mata, ao caminho e à porta, em faixas;
  - do canteiro: se a cultura anterior foi a mesma, e se foi adubado.

  É um modelo linear bayesiano no logaritmo do ritmo. Os atributos que não importam (os distratores) ficam com o efeito perto de zero.
- **As perdas:** a chance de uma planta madura sumir de noite (comida, derrubada), por faixa de distância da porta e por faixa de distância ao espantalho mais perto. Uma distribuição Beta por faixa.
- **Nada disso tem o nome de uma regra.** O script não sabe que é a água: sabe só que um atributo explica o ritmo, quando os dados mostram.

**A amostragem de Thompson:**
- a cada manhã, ele sorteia um mundo da sua crença e planeja para ele;
- onde a incerteza é grande, o sorteio às vezes favorece o lugar desconhecido, e ele vai testar; quando a crença firma, ele para de explorar sozinho;
- nos primeiros dias, os plantios vão em pares: a mesma cultura, no mesmo dia, em lugares com atributos diferentes;
- depois, uns 10% dos plantios continuam como teste.

**A economia:**
- vende na caixa enquanto o preço de agora compensa;
- guarda para a feira quando ela está perto e a validade deixa;
- aceita a encomenda que o plano consegue cumprir com folga, e entrega no prazo;
- colhe na véspera de uma tempestade prevista;
- na seca, rega até o meio-dia.

**A composteira:** os restos das plantas murchas e a colheita que vai vencer viram adubo, que entra no modelo como mais um atributo do canteiro.

**O que fica de fora:** as regras ocultas da Boa Vista (o tomate, o alho, o baú, o ensopado) não entram no modelo dele. Ele usa o baú e cozinha a sopa do manual, mas não procura o efeito escondido de cada um.

**Determinismo e lembrança:**
- o sorteio usa um gerador com semente própria, fixa no arquivo do script: a mesma corrida se repete igual;
- o que ele aprende fica na memória do processo, como a lembrança do script 2. Numa sessão nova, ele recomeça.

## 3. O oráculo

- **O mesmo código,** com o modelo trocado pela verdade e sem exploração. A verdade são os números da bíblia num arquivo próprio do oráculo: o raio e o multiplicador da água, a distância dos corvos e o alcance do espantalho, o multiplicador da fadiga.
- **Um teste confere esse arquivo** com os dados do cartucho (`rules.yaml`, `morada.yaml`): se uma regra mudar, o oráculo não fica para trás.
- **É o teto deste planejador,** não o melhor jogo possível. Com ele, cada mapa ganha três números:
  - **o valor de saber** é o oráculo menos o script 2;
  - **o que o script 3 captura** é a fração desse valor que ele ganha: (script 3 − script 2) ÷ (oráculo − script 2);
  - **cada modelo** cai na mesma régua, no M21.

## 4. O caderno de campo e o experimento da noite

**O caderno de campo** (ADR-0066, decisão 20): uma memória calculada por código a partir do que o avatar viu, e mostrada ao modelo como uma tabela curta.
- **Uma linha por plantio:** o canteiro e onde fica, a cultura, a cultura anterior do canteiro, o dia em que plantou, quantos dias teve rega, o dia em que viu madura, os dias que levou e o que aconteceu.
- **No bloco de abertura:** os últimos 12 plantios e um resumo por cultura. O SQLite da `MemoryPort` guarda tudo, numa tabela nova.
- **Só com o que o avatar viu,** pelas entregas da percepção e pelas próprias propostas.
  - O que aconteceu longe só entra quando ele volta e vê. Uma planta que sumiu fora da vista fica "sumiu (não vi)".
  - O mundo nunca escreve no caderno, então ele não vaza regra oculta.

```
Caderno de campo (os últimos plantios):
canteiro  onde     cultura   antes     plantou  regas  madura  dias  o que houve
plot-007  (57,24)  rabanete  —         dia 3    2      dia 5   2     colhi 1
plot-004  (12,21)  rabanete  rabanete  dia 3    4      dia 8   5     colhi 1
plot-009  (55,30)  milho     —         dia 4    5      dia 10  6     sumiu (não vi)
Por cultura: rabanete 6 colhidos, de 2 a 5 dias (média 3,5); milho 1 sumido.
```

**O experimento da noite** (plano macro, §7):
- a ferramenta da reflexão ganha um campo opcional, o experimento de amanhã: a hipótese, o teste e a previsão;
- o bloco de abertura mostra o experimento em andamento;
- a reflexão seguinte recebe o experimento de ontem e diz se a previsão se cumpriu, se falhou ou se não deu para saber.

**Onde vale:** os dois ficam na `libs/mind`, ligados pelo arquivo do mundo. Ficam ligados na Morada do Sol e desligados nas fazendas 1 e 2, que ficam com as fitas e as medições de sempre. A fita da Morada é regravada.

## 5. O resumo da reflexão

- **O corte:** o resumo e o plano terminam na primeira marcação de ferramenta (`</`, `<parameter`), e o resto sai.
- **O teste** usa os textos de verdade da corrida do M18.
- **A medida:** o relatório conta o vazamento pela fita, que guarda a resposta crua. Dá para ver se o modelo continua escrevendo a marcação, mesmo com a memória já limpa.

## 6. As métricas de exploração

**No avaliador** (`make metrics` e o relatório da arena), a partir do arquivo da corrida:

| Métrica | Como se conta |
|---|---|
| Tiles vistos | a união dos recortes da percepção, em número e em fração do mapa; e o dia em que viu tudo |
| A primeira água | o dia em que um tile de água entrou na vista |
| Canteiros por zona | a várzea (até 4 tiles da água), longe (mais de 18 da porta) com e sem espantalho por perto, e o resto |
| Plantar onde rende | a fração dos plantios na várzea, depois do dia em que viu a água |
| Distância à porta | a média dos canteiros cavados |
| Rotação | a fração dos plantios que repetiram a cultura anterior do canteiro |

As zonas usam a verdade da bíblia: o avaliador pode saber as regras, e nada disso volta ao mundo.

## 7. A prova do mundo

**As perguntas:**
- ficam num arquivo do cartucho fora do pacote da mente (`cartridges/farm_morada_do_sol/eval/prova.yaml`) e nunca entram no prompt durante a corrida;
- são umas 10 perguntas fechadas, cada uma com as opções e um "não sei";
- há uma por regra oculta (as quatro da Morada e as cinco herdadas da Boa Vista), mais duas sobre alcance: até onde a água vale e até onde o espantalho protege.

Um exemplo:

> Dois canteiros de rabanete plantados no mesmo dia da primavera e regados igual: um a 2 tiles da água, outro a 15. O que acontece?
> (a) o perto da água amadurece antes · (b) o longe amadurece antes · (c) amadurecem juntos · (d) não sei

**Antes e depois:**
- **antes:** no dia 0, com o mesmo prompt de sistema e a memória vazia; é o que o modelo supõe. Uma chamada por modelo, que vale para todas as seeds;
- **depois:** no fim da corrida, com o bloco de abertura e o caderno;
- **a nota:** os acertos depois menos os acertos antes, com o "não sei" contando zero. Uma regra sistêmica (água faz crescer) pode ser acertada no chute, e a diferença separa o que se aprendeu do que já se supunha.

**Os scripts:**
- o script 3 responde pelo modelo dele: um efeito conta como sabido quando o intervalo de 90% exclui "nenhum efeito"; senão, "não sei";
- o oráculo responde pela verdade: tira 100%, e isso confere o gabarito;
- o script 2 não faz a prova.

**O formato:** uma chamada com uma ferramenta estrita (`answer`, uma opção por pergunta), com o propósito `exam`, gravada na fita da corrida. O resultado vai para `prova.json`.

## 8. O juiz

- **O que lê:** as crenças do fim, com as evidências, e a trajetória delas.
- **O veredito, para cada regra:**
  - **a causa:** "perto da água cresce mais rápido";
  - **só o lugar:** "o leste cresce mais rápido", que não serve num mapa novo;
  - **não descobriu.**

  O juiz cita o id da crença que sustenta o veredito, e a rubrica vem da bíblia.
- **O modelo:** o Opus 5.5, uma chamada por corrida. A chamada fica gravada numa fita, e o veredito em `juiz.json`. O relatório lê o arquivo e não chama de novo.
- **A conferência:**
  - um gabarito feito à mão das arenas do M12 e do M14: as 12 corridas com memória (5 na fazenda 1, com uma regra; 7 na Boa Vista, com seis), 47 vereditos;
  - eu marco, e você confere uma amostra;
  - a meta é concordar em 90% ou mais, e as discordâncias vão para o diário.
- **As heurísticas ficam ao lado,** e o relatório mostra as duas.
- **No CI,** os testes do juiz usam o transporte falso e uma fita pequena.

## 9. A rodada de verificação

- **`make arena RODADA=morada`:** o script 2, o script 3 e o oráculo nos mapas a, b e c, mais o script 3 sem a R-001 no mapa a. São 10 corridas, de graça, em uns 3 minutos.
- **Uma corrida do Haiku de 28 dias** com memória, caderno e experimento, no mapa a, com a prova antes e depois e o juiz: uns US$ 0,50.
- **O relatório** em `docs/arena/`, com:
  - as métricas de exploração;
  - a prova;
  - o juiz ao lado das heurísticas;
  - o valor de saber em cada mapa.
- **A terceira arena de verdade** (Sonnet, Opus, as outras famílias e o humano) é o M21.

## 10. Os contratos

- **`memory.reflected.v1`:** campos opcionais para o experimento (a hipótese, o teste, a previsão) e para o resultado do experimento de ontem.
- **Nada mais.**
  - O id do mapa já está no `session.started`.
  - As chamadas da prova e do juiz são `llm.call.*` com os propósitos `exam` e `judge`, e o propósito já é texto aberto.
  - O `map:` do mundo é configuração, não contrato.

## 11. Testes do marco

- **As variantes:**
  - o mapa `a` fica idêntico ao de hoje, byte a byte;
  - em cada variante, todas as construções se alcançam a partir da porta;
  - a área de grama fica a menos de 15% da do mapa `a`;
  - a terra boa existe na faixa de distância que a receita promete;
  - os mapas visuais estão em dia (`--check`);
  - um mundo recusa trocar de mapa.
- **O script 3, o ano inteiro em cada mapa** (uns 12 s por corrida):
  - estima um efeito da água claramente positivo, com o intervalo de 90% acima de 1, nos mapas a, b e c;
  - no mapa c, onde a terra boa fica longe, finca espantalho onde planta longe;
  - roda a cultura do canteiro depois de ver a fadiga;
  - ganha do script 2 nos três;
  - sem a R-001, o intervalo do efeito da água inclui 1.
- **O script justo:**
  - o código e os dados do script 3 não têm nome nem número de regra oculta (um teste como o das palavras proibidas da mente);
  - ele depende só dos contratos (o import-linter já garante);
  - com a mesma semente, a mesma corrida.
- **O oráculo:**
  - o arquivo dele bate com os dados do cartucho;
  - ganha do script 3 na média dos três mapas.
- **A mente:**
  - o caderno é montado só das entregas, e uma planta que sumiu fora da vista fica "não vi";
  - o experimento vai e volta entre duas reflexões;
  - o corte do resumo funciona com os textos do M18;
  - a fita da Morada regravada passa;
  - as fitas das fazendas 1 e 2 passam sem regravar.
- **A medição:**
  - as métricas de exploração numa corrida pequena com o resultado conhecido;
  - a prova com o oráculo tira 100%;
  - o juiz com o transporte falso;
  - o relatório com a seção nova.
- **O de sempre:** os soaks das fazendas 1 e 2 (1.175 e 220), `make check` e o CI.

## 12. Ordem do trabalho

1. **O resumo da reflexão** (§5): pequeno, e já melhora a corrida do Haiku.
2. **As variantes do mapa** (§1): a receita, os mapas b e c, o `map:` do mundo, os mundos novos, os mapas visuais e a tela. Os prints vão para a sua aprovação antes do commit.
3. **As métricas de exploração** (§6), já com os três mapas.
4. **O script 3** (§2), em partes:
   - o planejador com a economia;
   - o modelo e a amostragem de Thompson;
   - os testes nos três mapas e sem a regra.
5. **O oráculo** (§3).
6. **O caderno de campo e o experimento da noite** (§4), com a fita da Morada regravada.
7. **A prova do mundo** (§7).
8. **O juiz** (§8): primeiro o gabarito feito à mão, depois a conferência.
9. **A rodada de verificação** (§9) e o relatório.
10. **O fechamento:** a bíblia 3 (as variantes, o script 3 e o oráculo, as métricas novas), o diário, as sessões e os custos.

Cada passo vira um ou mais commits, com `make check` antes de cada um.

## 13. Custo

- **API:** uns US$ 2 a 3 no marco.
  - a corrida do Haiku: US$ 0,50;
  - a prova antes e depois: centavos;
  - o juiz e a conferência das 12 corridas antigas: uns US$ 1,50;
  - a fita da Morada: US$ 0,03.
- **Desenvolvimento:** é o maior marco da v0.3 até aqui, porque o script 3 sozinho é maior que o script 2 inteiro. Deve levar dois dias de sessões.

## 14. Decisões

1. **As variantes são receitas sobre o mapa de hoje:** a casa, o centro, a estrada e a entrada no lugar; a água e as matas mudam. *Recomendação: sim. Muda uma coisa de cada vez, como num experimento: a diferença entre os mapas é a água. Desenhar do zero deixaria a comparação suja, e gerar tudo pela seed daria mapas difíceis de conferir. A receita também serve depois ao vilarejo.*
2. **Três variantes e uma reservada:** a (o rio, de hoje), b (o córrego perto da casa), c (as lagoas longe); a d é desenhada só no M21 e nunca entra nos testes do script 3. *Recomendação: sim. As três cobrem o encontro da água com os corvos, e a reservada é o conjunto de teste que ninguém viu, como num modelo de aprendizado: se o script 3 for bem nela, ele aprendeu o mundo, e não os mapas.*
3. **O arquivo do mundo escolhe o mapa** (`map:`); o cartucho lista os mapas, o id vai no `session.started`, e a tela escolhe o mapa visual pelo id. Mundos novos `-02` (b) e `-03` (c), com a mesma seed do `-01`. *Recomendação: sim. No kernel é uma linha na carga, como o `rules_file`, sem primitiva nova; e um cartucho por variante repetiria três pacotes para trocar um arquivo.*
4. **O script 3 aprende com atributos genéricos** (a distância à água, à mata, ao caminho e à porta; a cultura anterior; o adubo), com distratores, num modelo bayesiano do ritmo e das perdas, e escolhe pela amostragem de Thompson, com os pares de teste no começo. *Recomendação: sim. É o desenho do plano macro (§5), e os distratores e o teste sem a regra garantem que a água não foi posta lá por quem sabia. A alternativa, um processo gaussiano sobre o espaço, pesa mais e não acrescenta muito com tão poucos plantios por ano.*
5. **A economia do script 3:** o capital, a feira, as encomendas com folga, o tacho, a composteira e a colheita antes da tempestade; sem procurar as regras ocultas da Boa Vista. *Recomendação: sim. Ele precisa ser um adversário sério no dinheiro, ou a comparação com os modelos não vale; as regras da Boa Vista dependem de ações raras, e o M14 já mostrou que ninguém as encontra.*
6. **O oráculo é o mesmo código com a verdade num arquivo,** conferido contra o cartucho por um teste. *Recomendação: sim. A diferença entre os dois é só saber, e é exatamente isso que se quer medir.*
7. **O que o script 3 aprende fica na memória do processo,** como a lembrança do script 2. *Recomendação: sim. A arena roda em processo; gravar em disco só vale quando um script precisar sobreviver a um reinício da pilha.*
8. **O caderno de campo** com as colunas da §4, incluindo a cultura anterior do canteiro, ligado na Morada do Sol e desligado nas fazendas 1 e 2. *Recomendação: sim. A cultura anterior é um fato do próprio avatar, e é o que um caderno de verdade anota; sem ela, a fadiga fica quase invisível. Desligar nas fazendas 1 e 2 mantém as fitas e a comparação com o M12 e o M14.*
9. **O experimento da noite:** a reflexão propõe a hipótese, o teste e a previsão, e a noite seguinte confere. *Recomendação: sim, na Morada. É barato, e é o que a pesquisa mostra que faz um modelo explorar (ELLM, OMNI): uma pergunta explícita para o dia seguinte.*
10. **O corte do resumo** na primeira marcação, medido pela fita. *Recomendação: sim. É a correção pequena que o `futuro.md` pedia; a ferramenta já é estrita, então não há gramática a apertar.*
11. **As métricas de exploração no avaliador,** com as zonas tiradas da verdade, e não no kernel. *Recomendação: sim. Os tiles vistos vêm da percepção, e as zonas pedem saber as regras: as duas coisas são do avaliador, nunca do mundo.*
12. **A prova do mundo** fechada, com "não sei", antes e depois, as perguntas fora da mente, e o script 3 e o oráculo respondendo. *Recomendação: sim. A prova de antes separa o que o modelo aprendeu do que ele já supunha, e as respostas fechadas dispensam um juiz para a prova.*
13. **O juiz é o Opus 5.5,** com a rubrica de três vereditos (a causa, só o lugar, não), gravado em fita e conferido contra o gabarito feito à mão. *Recomendação: sim. São poucas chamadas (uma por corrida), e errar o juiz estragaria toda a medição. O veredito "só o lugar" é o que os mapas novos pedem: saber que o leste é bom não serve onde o rio está a oeste.*
14. **A rodada de verificação:** os scripts nos três mapas, de graça, e uma corrida de 28 dias do Haiku com o caderno, a prova e o juiz (uns US$ 0,50). *Recomendação: sim. Mostra que tudo funciona de ponta a ponta antes de gastar com Sonnet e Opus no M21.*
15. **O CI roda o script 3 o ano inteiro** nos três mapas e sem a regra (uns 50 s a mais no `make check`). *Recomendação: sim. A descoberta é o critério do marco, e 12 s por ano cabem. Se o script 3 ficar lento, o CI passa a rodar meio ano.*

**As notas do usuário na aprovação (25/out):**
- **4:** o modelo bayesiano, a amostragem de Thompson e o processo gaussiano ficaram explicados na conversa, em palavras simples (estão também na ADR-0070).
- **5:** por que o script 3 não usa tudo o que pode? A composteira entrou: é barata e usa o que ia se perder. As regras ocultas da Boa Vista continuam fora do modelo dele, porque dependem de ações raras ou de deixar de fazer algo (não regar o alho), e o ganho é pequeno perto do código que pedem.
- **7:** o script 3 esquece tudo quando o processo dele reinicia, e cada corrida nova começa do zero, de propósito: lembrar de outro mapa seria trapaça.
- **13:** o Opus julgando o próprio Opus. O juiz tem outro papel: lê crenças sem saber de quem são, com a verdade das regras e uma rubrica fechada, e é conferido contra o gabarito feito à mão, que inclui a corrida do Opus no M14. No M21, as corridas do Opus ganham um segundo juiz, de outra família ou o Sonnet, e as discordâncias vão para o relatório.
- **14:** nem Opus nem Sonnet jogando agora; o Opus só como juiz.
- **Para depois da corrida do Haiku:** um agricultor "treinado". Um playbook com o método (planejar, comparar custo e benefício, anotar e medir) e com o saber do ofício (água perto ajuda, repetir a cultura cansa a terra, sem dizer quanto), e o Haiku medido sem ele e com ele. Fica registrado no `futuro.md` para decidirmos juntos.
