# O procedimento do agricultor (M21)

**Aprovado em 8/nov** (ADR-0074, decisão 35), com os quatro pontos: o mapa à noite, um par de
teste sempre em andamento, o fim do exemplo do padeiro e o texto todo na mente do cenário. O
texto que o modelo lê está em
`cartridges/farm_morada_do_sol/mind/src/campsverso_farm_morada_do_sol_mind/data/procedimento.md`.

Foi o rascunho lido antes do código. É o caminho (b) de 8/nov: o playbook vira um
procedimento operacional, no estilo do agente de podcast do CampsCast, e a memória passa a mostrar
os dados que o procedimento manda usar. Foi escrito sem ler as corridas do mapa d, que continua
sendo o teste.

## 1. Por que mudar

Montando os pedidos reais do mapa a (`data/prompt-exemplo/morada-mapa-a.md`), apareceram três
lacunas entre o que o playbook manda fazer e o que o modelo recebe:

1. A reflexão da noite, onde o playbook manda procurar a surpresa no caderno e propor o
   experimento, não recebe o caderno: só os acontecimentos do dia, as anotações e as crenças.
2. O caderno aparece só nas decisões do dia, e só os últimos 12 plantios.
3. A linha do caderno não traz a estação nem os dias esperados, e o lugar é só a coordenada; à
   noite não há mapa nenhum para saber do que o canteiro fica perto.

E duas coisas que o rascunho também precisou resolver:

4. O experimento é "para amanhã", mas um par de canteiros leva de 3 a 10 dias para dar
   resultado. Hoje, repetir o experimento cria outro registro, e o de antes fica aberto para
   sempre.
5. O modelo não vê os experimentos antigos nem os vereditos deles. Sem isso, "cada suspeita tem
   duas tentativas" não tem como ser contado.

O playbook 3 (método e ofício, em 315a280) nunca rodou. O procedimento o substitui como a
**versão 4**, porque a versão sobe a cada mudança de texto.

## 2. O texto que o modelo vai ler

Entra no prompt de sistema logo depois do manual, no lugar do "## O playbook". Vale nas decisões
e na reflexão. O exemplo do padeiro sai, porque os formatos fixos cumprem o papel dele.

````markdown
## O procedimento

Este é o seu procedimento de trabalho nesta fazenda. Siga as etapas na ordem, sem pular nenhuma. Ele serve para descobrir, gastando pouco, o que o manual não conta, e para usar o que você descobriu.

### O que você recebe, e onde

- **O manual** é a seção "A Fazenda Morada do Sol, para quem acabou de chegar", acima. Duas tabelas dele contam aqui: a das culturas (a coluna "Dias, mais ou menos" é o tempo na estação boa) e a do calendário de plantio (boa, fraca, parada).
- **A tabela do caderno** ("Caderno de campo") tem uma linha por plantio, escrita pelo caderno com o que você fez e viu. De manhã, no bloco "O que você lembra", vêm as últimas linhas; à noite, na reflexão, vem a tabela inteira. As colunas:
  - `canteiro` e `x,y`: qual e onde;
  - `semente` e `plantou`: o que e em que dia;
  - `estação`: a do dia do plantio e como a semente vai nela (boa, fraca ou parada); `primavera→verão` quando amadureceu já na estação seguinte;
  - `esperado`: os dias que o manual dá para essa semente nessa estação;
  - `antes`: a semente que havia antes no canteiro, ou `novo`;
  - `adubo`: `sim` ou `não`;
  - `rega`: em quantos dias o canteiro foi regado, de quantos dias ele cresceu (a chuva conta como rega);
  - `levou`: os dias do plantio até amadurecer (vazio se ainda não amadureceu);
  - `fim`: `colhida`, `comida`, `derrubada`, `murcha`, `sumiu` ou `crescendo`.
- **À noite, na reflexão**, vêm também: "Onde ficam as coisas" (as construções e o que você já viu, com as coordenadas), "O mapa que você já viu" (no mesmo formato do `map` da foto; `?` é o que você nunca viu) e "Os seus experimentos" (todos, com o veredito de cada um).
- **As suas anotações** são o campo `note` das ferramentas. O que você anota hoje volta à noite, em "O que você anotou".
- **As crenças e o experimento aberto** voltam toda manhã, em "O que você lembra", e toda noite, na reflexão.

### Etapa 1. Ao acordar, no primeiro pedido do dia

1. Leia o "Plano" e o "Experimento em teste" em "O que você lembra": eles são o roteiro do dia.
2. Confira a comida: se não houver comida para hoje e amanhã, no inventário ou no baú, o dia começa por ela.
3. Na primeira ação do dia, escreva em `note`: `HOJE: <o que plantar e onde>. PAR: <os dois canteiros do teste, ou "nenhum">.`

### Etapa 2. Durante o dia

1. Faça o trabalho do plano: comer, regar, colher, vender, plantar.
2. Se o experimento aberto pede um par de teste e ele ainda não foi plantado, plante-o hoje, junto com os plantios do dia. O par: dois canteiros que só diferem na suspeita testada, com a mesma semente, plantados no mesmo dia. Regue os dois em todos os dias, até amadurecerem.
3. Quando algo surpreender (uma recusa, uma planta que sumiu, uma colheita perdida, um preço, uma refeição), escreva em `note` na ação seguinte: `VI: <o fato, com o canteiro, o dia e o número>.`

### Etapa 3. À noite, na reflexão, nesta ordem

1. **As surpresas.** Na tabela do caderno, olhe as linhas com `levou` preenchido, `rega` completa (por exemplo, `6 de 6`) e uma só estação. É surpresa a linha em que `levou` difere de `esperado` em 2 dias ou mais, e toda linha com `fim` igual a `comida`, `derrubada` ou `sumiu`. O que o manual já explica não é surpresa: a rega incompleta, a estação fraca ou parada, a tempestade que derruba o maduro, o maduro que murcha sem colheita.
2. **As suspeitas.** Para a surpresa que mais aparece, a lista de suspeitas é sempre a mesma: o lugar do canteiro (do que ele fica perto: a casa, o poço, o caminho, a mata, a água; veja pelo mapa e pelas coordenadas), `antes`, `adubo` e `estação`. Todas entram, sem descartar nenhuma.
3. **Os grupos.** Para cada suspeita, separe as linhas da mesma semente e da mesma estação em dois grupos, com ela e sem ela, e compare: o `levou` médio, e quantas linhas de cada grupo tiveram surpresa.
4. **O veredito.** Se há experimento aberto e os dois canteiros do par já amadureceram (ou um deles se perdeu), compare com a previsão e responda em `experiment_result`: `cumpriu`, `falhou` ou `inconclusivo` (inconclusivo quando um dos dois deixou de ser regado, mudou de estação ou se perdeu). Se o par ainda está crescendo, deixe `experiment_result` vazio e copie em `experiment` o mesmo experimento, sem mudar nada.
5. **As crenças.** Revise todas, com a escada de confiança abaixo. Cada evidência é uma linha da tabela ou uma anotação, com o canteiro e os números.
6. **O próximo experimento.** Se não há experimento aberto, escolha a suspeita: a que separou os grupos no passo 3; se nenhuma separou, a primeira da lista que ainda não foi testada em "Os seus experimentos". Cada suspeita tem duas tentativas: depois de duas sem decidir, passe para a próxima, e volte a ela só depois de testar todas. Monte o par com a semente mais barata e mais rápida da estação boa, entre os plantios que você já ia fazer.
7. **O plano e o resumo.** Escreva `plan` e `summary` nos formatos abaixo. O plano usa toda crença com confiança 0,7 ou mais: diga qual.

### Os formatos

- `experiment.hypothesis`: `[<suspeita>] <semente> leva <mais ou menos> dias quando <condição>.`
- `experiment.test`: `Par: <canteiro A> (<com>) e <canteiro B> (<sem>), <semente>, plantio no dia <N>, os dois regados todos os dias. Veredito quando os dois amadurecerem.`
- `experiment.prediction`: `<canteiro A> amadurece pelo menos 2 dias <antes ou depois> de <canteiro B>.`
- Uma crença (`statement`): `<semente ou coisa>: <o que acontece> quando <condição>.` Cada `evidence`: `<canteiro> (<x,y>): levou <n>, esperado <n>`, ou `dia <n> <hora>: <o fato>`.
- `summary`: `Comida: <...>. Dinheiro: <...>. Surpresas: <canteiros, ou "nenhuma">. Par: <situação>.`
- `plan`: `Comida: <...>. Plantar: <...>. Par: <plantar, regar ou "nenhum">. Crença em uso: <id, ou "nenhuma">.`

**A escada de confiança.** 0,3 com uma surpresa só; 0,5 quando os grupos do passo 3 concordam; 0,7 quando um par cumpriu; 0,9 quando dois pares cumpriram, ou um par e os grupos. Um par que falhou desce a crença para 0,3; dois pares que falharam a abandonam (`retracted`).

### Nunca

- Nunca gaste um experimento com o que o manual já diz.
- Nunca teste duas suspeitas no mesmo par.
- Nunca chame de surpresa uma linha com a rega incompleta ou que mudou de estação.
- Nunca forme nem suba uma crença sem citar linhas da tabela ou anotações.
- Nunca arrisque a comida, o sono ou a semente da próxima leva por causa de um teste.

### Sempre

- Sempre comida para dois dias antes de qualquer teste.
- Sempre um par de teste em andamento, e só um.
- Sempre a suspeita entre colchetes no começo de `hypothesis`.
- Sempre o mesmo cuidado com os dois canteiros do par: a mesma semente, o mesmo dia, a mesma rega.
- Sempre use no plano a crença de 0,7 ou mais: o que se confirmou muda o que você faz.
````

Até a versão 3, o playbook tinha duas camadas: o método, que valia em qualquer mundo
(`libs/mind`), e o ofício do gênero fazenda (`cartridges/farm/mind`). O procedimento fala de
canteiros do começo ao fim e cita o título do manual e o calendário da Morada. Por isso o texto
todo ficou na mente da Morada (`Mind.craft`); o método e o ofício saíram, e as fazendas 1 e 2
ficaram sem playbook. Um mundo futuro, como o escritório, escreve o próprio procedimento.

## 3. O que o modelo passa a ver

Os exemplos abaixo são inventados e servem só para mostrar a forma.

**De manhã**, no bloco "O que você lembra", as últimas 12 linhas, já em tabela:

```
Caderno de campo (as últimas 12 de 31 linhas):
| canteiro | x,y | semente | plantou | estação | esperado | antes | adubo | rega | levou | fim |
|---|---|---|---|---|---|---|---|---|---|---|
| plot-001 | 12,9 | rabanete | dia 1 | primavera, boa | 3 | novo | não | 3 de 3 | 3 | colhida |
| plot-002 | 13,9 | rabanete | dia 1 | primavera, boa | 3 | novo | não | 3 de 4 | 4 | colhida |
| plot-003 | 14,9 | milho | dia 2 | primavera, boa | 6 | novo | sim | 5 de 5 | 5 | colhida |
| plot-004 | 12,10 | batata | dia 3 | primavera, fraca | 10 | novo | não | 4 de 4 | | crescendo |
```

**À noite**, a mensagem da reflexão ganha quatro seções depois de "As crenças que você já tinha":

1. "Caderno de campo": a tabela inteira, até 100 linhas. As mais antigas que isso só entram no
   resumo da seção, por semente e estação: `rabanete, primavera (boa, esperado 3): 9 maduras, de
   3 a 4 dias (média 3,2); 1 sumiu`.
2. "Onde ficam as coisas": as construções e as coisas que você já viu, com as coordenadas. Os
   canteiros ficam de fora, porque já estão na tabela.
3. "O mapa que você já viu": o terreno que você já viu, montado com os recortes das fotos, no
   formato de `map` (`rows`, `legend`, `origin`), com `?` no que você nunca viu.
4. "Os seus experimentos": um por linha, com o dia, a hipótese, o teste, a previsão e o veredito.

O tamanho fica em uns 5 mil tokens a mais por noite. Uma corrida de 14 dias do Fable custa por
isso uns US$ 0,80 a mais, uma do Opus uns US$ 0,30 e um ano do Haiku menos de 2 centavos.

## 4. O que muda no código

Tudo fica atrás de uma chave nova da memória, o **caderno completo**. Ela liga sozinha nas corridas
com playbook e liga também no braço de dados. Sem a chave, os pedidos ficam idênticos aos de hoje,
e as fitas não mudam.

| Lacuna | O que muda |
|---|---|
| 1 e 2 | A reflexão recebe a tabela inteira do caderno, e o bloco da manhã mostra as últimas 12 linhas no mesmo formato. |
| 3 | A linha ganha a estação com o calendário, os dias esperados e a rega como "X de Y". O esperado sai de um arquivo da mente da Morada com as duas tabelas do manual, e um teste garante que os números são os mesmos do manual. A reflexão recebe o mapa visto e "Onde ficam as coisas". O terreno visto já é guardado pela porta de memória (ADR-0074), então a memória não guarda nada além do que a porta guarda. |
| 4 | O experimento fica aberto até ter veredito: o mesmo texto não cria outro registro. A instrução da reflexão e a descrição de `experiment` deixam de dizer "para amanhã". |
| 5 | A reflexão recebe "Os seus experimentos". |

Junto com isso:
- `PLAYBOOK_VERSION = 4`, e a arena recusa as versões 1 a 3.
- A ficha da corrida grava a chave.
- O teste de palavras proibidas lê o procedimento e os títulos das seções novas. O texto da seção
  2 já passa pela lista da Morada.

## 5. A aderência ao procedimento

Os formatos fixos permitem medir por código se o modelo seguiu o procedimento. Isso separa "o
procedimento não ajuda" de "o modelo não seguiu o procedimento". O relatório da arena ganha, por
corrida:
- quantas hipóteses começam com `[suspeita]`;
- quantos pares foram plantados no mesmo dia, com a mesma semente, e regados igual;
- quantos vereditos foram dados;
- quantas suspeitas da lista foram testadas;
- quantas anotações `HOJE:` e `VI:` houve.

## 6. A rodada

Fica a proposta de 4/nov (§9 do plano do M21), agora com o procedimento e o caderno completo,
mais o braço de dados:

| Corrida | Dias | Custo estimado (US$) |
|---|---|---|
| Haiku ×3, procedimento e caderno completo | 28 | ~2,20 no total |
| **Haiku ×3, só o caderno completo (o braço de dados)** | 28 | ~2,20 no total |
| **Haiku, procedimento, no mapa a sem as regras ocultas (o controle de conhecimento prévio)** | 28 | ~0,75 |
| Sonnet, Opus, Gemini, Astra e Fable, como na proposta | 14 | ~60, mais ~2 do caderno completo |

O braço de dados separa o que vem do texto do que vem dos dados. As corridas sem playbook que já
estão lacradas continuam sendo a base sem os dois.

## 7. O que não muda

- Só método: nenhuma regra oculta nem dica dela. As suspeitas são as mesmas colunas do ofício 3,
  com os distratores.
- O mapa d continua lacrado até o fim do ano do usuário, e nada deste rascunho veio dele.
- Nenhuma chamada paga antes do ok da rodada.
