# Plano do M22 — o fechamento da v0.3

*Proposto em 13/nov/2026, depois do fechamento do M21 e da decisão do usuário de deixar a rodada 3 para a v0.4. Como no M7 e no M15, este marco confere, documenta e publica. A exceção é o Astra (§3): preparando este plano, achei um erro de medição nosso, e o fechamento é a hora de consertá-lo. A §7 traz, a pedido do usuário, uma lista de ideias para a v0.4 que não serão feitas aqui. **Aprovado em 14/nov/2026, com as nove decisões como recomendado (ADR-0076).***

## O que a v0.3 prometeu

A pergunta do [plano macro](v0.3-macro.md): **num mundo maior, com estações, encomendas e regras escondidas em lugares que pedem exploração, quem aprende o mundo e lucra com o que aprendeu: um modelo, um script que faz experimentos, ou um humano? E quanto vale aprender**, comparando com um oráculo que já sabe as regras?

Cada marco tinha um "pronto quando". O M22 os confere um a um, com a evidência no código final, e responde à pergunta com os números.

## 1. Critérios de aceite

`docs/aceite-v0.3.md`, no formato do `aceite-v0.2.md`: um critério por linha, com a evidência e o resultado.

| # | Critério (o "pronto quando" do plano macro) | Evidência |
|---|---|---|
| C1 | **M16:** a fazenda 1 e a Boa Vista intactas; o script 2 adaptado vive um ano na Morada do Sol | os soaks de 30 dias das fazendas 1 e 2 (1.175 e 220 moedas); um ano (28 dias) da Morada do Sol no código final |
| C2 | **M17:** uma corrida assistida ao vivo e outra gravada, na visão arena | `make ui-e2e` (a rodada sintética no modo de assistir, na porta 8797); `make assistir` sobre a rodada do M21 |
| C3 | **M18:** o script 2 adaptado vive um ano com a economia; a mente entende as encomendas pela fita | o ano de C1, com as encomendas, a feira e o clima; a fita da Morada (`morada-dia-2`) no `make check` |
| C4 | **M19:** o script 3 descobre as regras por experimento em mapas diferentes; o oráculo dá o teto | as réguas nos quatro mapas (bíblia 3, §19) e "O que o script 3 aprendeu" no relatório do M21 |
| C5 | **M20:** um ajudante contratado trabalha um ano, como o critério ficou no M20: a contratação forçada, sem travar, com as recusas esperadas, e o replay de um dia com dois avatares igual ao arquivo | a rodada `ajudantes` ([2026-10-26](../arena/2026-10-26.md), ADR-0073) e o teste do replay com dois avatares |
| C6 | **M21:** o relatório compara todos, com o valor de aprender | [docs/arena/m21-terceira-energia.md](../arena/m21-terceira-energia.md), com o adendo do Astra (§3) |
| C7 | **Os princípios continuam valendo:** arquitetura, contratos, determinismo e replay nos três mundos; a regra oculta fora do manual, do catálogo e do procedimento | `make check` verde (local e CI), com o teste de palavras proibidas; `make ui-e2e` |
| C8 | **O custo:** a v0.3 dentro do teto de US$ 300 (ADR-0074, decisão 21) | `docs/custos/creditos.csv` e o custo de API por marco |

**A resposta à pergunta**, no fim do `aceite-v0.3.md` (rascunho, a conferir com os números finais):
- **Quanto vale aprender:** no mapa d, 1.028 moedas e 19 dias sem fome no ano (o oráculo contra o script 2).
- **O script que faz experimentos aprende:** o script 3 achou as duas regras do mapa d, a água e a fadiga, com o intervalo de confiança. Mesmo assim não lucrou com elas: 84 moedas, com 22 dos 94 plantios na faixa da lagoa.
- **Os modelos grandes lucram sem aprender:**
  - nenhum achou a água pela causa;
  - o tamanho do adubo saiu pela causa três vezes, e a fadiga uma;
  - jogando a economia visível, capturaram até metade do valor de saber: o Fable 54%, o Opus 49% e o Sonnet 31%.
- **O humano, que sabia as regras,** plantou tudo no lugar certo desde o primeiro dia e terminou 15 dias com 2 moedas.
- **Em uma frase:** aprender e lucrar são habilidades separadas. O script aprende sem lucrar, os modelos grandes lucram sem aprender, e só o oráculo, que sabe, faz os dois.

## 2. As conferências finais

- **Os soaks no código final,** em minutos e sem custo:
  - a fazenda 1 e a Boa Vista em 30 dias;
  - a Morada do Sol em um ano, no mapa a (`farm-morada-do-sol-01`) e no mapa d (`-04`);
  - `make metrics` sobre cada um.
- **`make check` com `TZ=UTC`,** o CI verde no último push, e `make ui-e2e` nos três servidores.
- **Duas chamadas reais,** em centavos:
  - `make llm-smoke` pela Anthropic, para provar que o caminho segue de pé (a chave vence em 31/12);
  - `make llm-smoke MODEL=openai/gpt-6-astra` pela OpenRouter, que também confere o conserto da §3.

## 3. O Astra: um erro de medição nosso

Achado em 13/nov, respondendo à pergunta do usuário sobre o Fable e o Astra.

**Todos rodaram no mesmo harness.** A mente do Campsverso (`libs/mind`) rodou no processo da arena:
- com o mesmo prompt (`9d37ac02`), as mesmas 29 ferramentas e o mesmo esforço (baixo na decisão, médio na reflexão);
- os Claude pela API da Anthropic, e o Astra e o Gemini pela OpenRouter, que traduz o pedido para o formato de chat da OpenAI;
- ninguém rodou pelo Claude Code nem pelo Claude Agent SDK.

**O Astra respondeu vazio em 47% das chamadas:**

| Corrida | Chamadas | Sem ação | Custo das vazias |
|---|---|---|---|
| astra (o ano) | 1.874 | 876, todas vazias | US$ 11,75 de 27,41 (43%) |
| astra-piloto (2 dias) | 158 | 73 | US$ 0,87 de 2,17 |
| astra-procedimento (14 dias) | 764 | 326 | US$ 4,49 de 11,88 |
| Claude (Haiku, Sonnet, Opus, Fable) | de 1.090 a 2.020 | de 1 a 55 | — |
| gemini | 650 | 62, com texto e sem ação | — |

- **O padrão é sempre o mesmo:** ação, vazio, ação, vazio. A resposta vazia vem logo depois do resultado de uma ação.
- **O custo no mundo:** a mente transforma a resposta sem ação em "esperar 15 minutos" (`controller.py`). O avatar ficou parado umas 219 horas simuladas no ano, perto de 8 das 16 horas acordado de cada dia.
- **A causa provável:** no formato da OpenAI, com `tool_choice: "auto"`, o modelo pode encerrar a vez depois do resultado de uma ferramenta. O Claude, treinado no formato da Messages API, segue chamando.
- **O piloto de 2 dias já mostrava o problema** (73 de 156 chamadas), mas a saúde dos pilotos olhava só o custo.

**O que isso muda:** os 3% do Astra no M21 medem o modelo com metade do dia parado, e não o modelo. O relatório, o plano do M21 e o diário de 12/nov ganham uma nota.

**O que fazer:**
1. **O conserto, de graça:**
   - na rota da OpenRouter, `tool_choice: "required"` para os modelos de fora da Anthropic, porque a mente sempre quer uma ação;
   - o Claude com raciocínio não aceita a ferramenta forçada, então o caminho da Anthropic não muda, e as fitas do Claude também não;
   - com os testes do adaptador.
2. **A medida, de graça:**
   - uma linha "respostas sem ação" no custo por resultado do relatório, tirada do `summary.json`;
   - a saúde dos pilotos para acima de 5% de respostas sem ação.
3. **O piloto consertado,** 2 dias do Astra (uns US$ 2), para ver as vazias sumirem.
4. **O Astra consertado em 14 dias** (uns US$ 12 a 16), no mapa d e com a mesma seed. Ele fica ao lado dos outros na seção "Lado a lado no dia 14", que já existe. O ano inteiro custaria uns US$ 25 a 30 e deixaria pouca folga no teto.
5. **O Haiku pela OpenRouter,** 2 dias (uns US$ 0,10): o mesmo modelo pelos dois caminhos, para separar o efeito do cano do efeito da tradução.

**O que isto não responde:** se o harness de cada laboratório (o Claude Agent SDK, o Codex) rende mais que o nosso. É a pergunta da bancada dos harnesses, o primeiro marco da v0.4 (ADR-0074, decisão 30). A §3 só garante que o nosso harness fale direito com cada família, antes de compará-las.

## 4. A revisão do `futuro.md`

- **Saem os itens feitos na v0.3.**
- **Os que ficam ganham destino:** a v0.4 (a bancada, o escritório), depois dela, ou a fazenda 4.
- **A rodada 3** (mais seeds e o segundo ano com memória) passa para a v0.4, como o usuário decidiu em 13/nov.
- **Entram as ideias da §7,** com destino v0.4.

## 5. Documentação

- **README:**
  - a v0.3 concluída;
  - como jogar a Morada do Sol (`make jogar`), rodar a arena, assistir (`make assistir`) e chamar o juiz;
  - o diagrama com as bibliotecas `economy` e `climate` e os vários avatares;
  - o caminho para a v0.4.
- **`docs/diario/README.md`:** "a v0.3 em números", como as versões anteriores tiveram:
  - o tempo e os tokens do Claude Code por marco (`make sessoes`);
  - o custo de API por marco;
  - os testes, os commits e os arquivos;
  - as frases para o LinkedIn de cada marco.
- **`contracts/CHANGELOG.md`:** as seções do M16 ao M21 viram uma seção `v0.3.0`.
- **`CLAUDE.md`, plano macro e escopo:** a v0.3.0 publicada, e a v0.4 como a próxima.
- **A ADR-0076,** com as decisões deste plano.

## 6. A versão

- **As notas** em `docs/versoes/v0.3.0.md`:
  - o que tem e como experimentar;
  - os critérios e os resultados das arenas;
  - os custos;
  - o que ficou conhecido e para depois;
  - as licenças da arte.
- **O print** em `docs/imagens/v0.3.0-fazenda-morada-do-sol.png`: a Morada do Sol na tela do jogador, de dia, tirado no navegador do app. Uma segunda imagem do modo de assistir vai só nas notas.
- **A tag `v0.3.0`** no commit final, com o CI verde. O push da tag e a Release no GitHub esperam o ok do usuário, como nas outras versões.

## 7. Ideias para a v0.4: agentes que planejam, lembram e calculam

A pedido do usuário, uma lista de ideias. Nenhuma será feita no M22: elas vão para o `futuro.md` e para o plano da v0.4. Cada uma parte de algo que o M21 mostrou e diz como seria medida. As mais baratas de medir são as do Haiku, a US$ 0,03 por dia.

### Planejar mais

1. **O plano do dia e da estação, escrito na reflexão.**
   - Hoje a reflexão da noite escreve crenças e um resumo, e o dia seguinte decide ação por ação, com esforço baixo.
   - A ideia: a reflexão escreve um plano com forma fixa (o que plantar e onde, o caixa da comida, as encomendas aceitas, os experimentos abertos). Cada decisão lê o plano e só se desvia dele com o motivo escrito.
   - O Opus e o Fable foram bem porque planejaram o capital; o Haiku decide no varejo.
   - *Medir:* o Haiku com e sem o plano.
2. **O planejador caro e o executor barato.**
   - O Opus ou o Fable só na reflexão da noite, umas 28 chamadas por ano, e o Haiku de dia, seguindo o plano.
   - É o conselheiro do M21 levado ao fim: em vez de um conselho que o Haiku pode ignorar, um plano escrito.
   - *Custo:* a reflexão foi uns 6% do custo do ano do Opus (uns US$ 2) e uns 9% do Fable (uns US$ 6), estimados pelos tokens das fitas. Com o Haiku no dia, seriam uns US$ 3 por ano com o Opus planejando, ou uns US$ 7 com o Fable, contra US$ 35 e 70 dos dois sozinhos.
   - *Medir:* a fração capturada contra a do Opus inteiro.
3. **A fila de ações numa proposta só.**
   - A mente gasta de 40 a 70 chamadas por dia (do Haiku ao Opus), a maioria em andar, regar e colher.
   - A ideia: uma ferramenta propõe uma sequência (regar os canteiros 3 a 9, colher o que estiver maduro no caminho, voltar ao baú).
   - O mundo executa passo a passo e interrompe quando algo muda (a fome, uma recusa, a noite). O kernel continua decidindo cada passo (princípio 2), e o humano já tem a fila (M17).
   - *Medir:* chamadas, custo e moedas por dia. Com menos chamadas, sobra orçamento para pensar mais nas que ficam.
4. **O esforço de pensar onde a decisão pesa.**
   - Hoje o esforço é baixo em toda decisão.
   - A ideia: esforço alto só nas decisões que custam (plantar onde, comprar, aceitar uma encomenda, abrir um experimento), e baixo em andar e regar.
   - *Medir:* o custo por moeda acima do script 3 fixo.
5. **Vários experimentos ao mesmo tempo, com um desenho fixo.**
   - O procedimento do M21 abria um par por vez e esperava o veredito. Os grandes fizeram de 1 a 5 experimentos em 14 dias, quase todos inconclusivos.
   - A ideia: uma bancada de teste no começo de cada estação, com três perguntas em paralelo (o lugar, o histórico do canteiro, o adubo), cada uma com repetições, e o veredito no fim da estação.
   - *Medir:* os experimentos concluídos e as regras achadas pela causa.

### Lembrar mais

6. **O segundo ano em outro mapa.**
   - A rodada 3 que foi para a v0.4, com uma mudança: o segundo ano num mapa diferente do primeiro.
   - Uma crença de causa ("a água perto faz crescer") vale no mapa novo; uma de lugar ("o sudoeste rende") não vale.
   - Mede, sem juiz, se o modelo aprendeu a causa ou decorou o lugar. O Opus acertou o lugar pelo motivo errado, e num mapa novo isso aparece nas moedas.
7. **O livro de cada canteiro, montado pelo harness e não pelo modelo.**
   - Uma tabela por canteiro: o que foi plantado, quando, as regas, o adubo, quantos dias levou e a colheita.
   - O harness a monta a partir do que o avatar viu, e o modelo a consulta por uma ferramenta, sem precisar lembrar nem anotar.
   - A fadiga depende do histórico do canteiro, e só um Haiku a achou. O caderno de campo de hoje depende de o modelo anotar.
   - *Cuidado:* só o que o avatar viu (princípio 5). Os dias até amadurecer contam até ele ver o canteiro maduro.
8. **Crenças com prova e contraprova.**
   - Cada crença guarda a evidência a favor, a evidência contra e uma explicação alternativa.
   - A reflexão pergunta "o que mais explicaria isso?" antes de subir a confiança.
   - O Opus creu que a faixa da lagoa rendia por ficar perto do poço e do quiosque, e nunca testou outra explicação.
9. **A busca por semelhança,** quando o bloco de abertura crescer: a `EmbeddingPort`, que já está no `futuro.md`. Com o segundo ano (ideia 6), as crenças dobram, e a medida do bloco decide.

### Calcular fora do modelo

Ferramentas que fazem a conta fora do modelo:
- a mente paga a pergunta e a resposta curta, e não o raciocínio da conta;
- todas rodam aqui, de graça;
- só leem o que o avatar viu, então não ferem o princípio 5;
- se a crença do modelo estiver errada, a conta também sai errada, porque nenhuma delas sabe as regras ocultas.

10. **A calculadora e a planilha:** uma expressão ou uma tabela pequena, como o lucro de cada cultura com o preço de hoje, os dias e a semente. Conta de cabeça erra, e a conta certa é barata.
11. **A consulta ao caderno.**
    - A ferramenta de comparação do M21, generalizada: filtrar e agrupar o próprio caderno e o livro dos canteiros, como "a média de dias até amadurecer por zona e por cultura".
    - A tabela volta pronta.
12. **O teste estatístico.**
    - Dados dois grupos do caderno, a ferramenta diz se a diferença é real, com o intervalo, como o script 3 faz.
    - O script 3 achou as duas regras do mapa d assim. Os modelos, que leem os mesmos números, deixaram os vereditos inconclusivos.
13. **O planejador da estação.**
    - Um otimizador local que, a partir das crenças do próprio modelo (preços, dias, rendimento por lugar), monta o plano de plantio e o fluxo de caixa dos próximos dias.
    - Ele aponta o dia em que falta dinheiro para a comida.
    - O modelo dá as hipóteses, e a conta é do otimizador.
14. **O mapa e as rotas:** a distância e a energia até um lugar, sobre o terreno que o avatar já viu.
15. **Um sandbox de código.**
    - A versão geral das anteriores: o modelo escreve um script curto sobre os próprios dados e o roda num sandbox local.
    - O sandbox fica sem rede e sem o repositório, porque as regras ocultas estão nele.
    - Custa a saída para escrever o código, e não a conta.
    - Pede ADR, como a `WorkshopPort`.
16. **As ferramentas da mente num servidor MCP.** As de 10 a 15 servem também à bancada dos harnesses: o mesmo conjunto chega ao nosso harness e ao de cada laboratório.

### O harness e cada família de modelos

17. **A prova de conformidade de um provedor novo.**
    - Antes de qualquer rodada, dois dias medindo as respostas sem ação, as recusas e os formatos, com um limite para seguir.
    - É a lição da §3.
18. **O prompt de cada família.**
    - O cartão, o manual e as descrições das ferramentas foram escritos e afinados com o Claude, e testados nas fitas do Claude.
    - A ideia: medir cada família com o mesmo prompt e com uma revisão feita para ela, antes de concluir que um modelo é pior.
19. **A bancada dos harnesses,** o primeiro marco da v0.4, já decidido:
    - o mesmo modelo no nosso harness e no do laboratório (o Claude Agent SDK, o Codex);
    - as mesmas ferramentas da fazenda num servidor MCP;
    - é ela que diz se o SDK de um laboratório rende muito mais.

**Por onde começar, na v0.4:** pela 17 e pela 18 (baratas, e garantem que a comparação seja justa); pela 3 e pela 7 com a 12 (de graça no harness, medidas no Haiku); e pela 2, que testa o caso de uso do mundo real, um executor barato com um planejador caro.

## 8. Ordem do trabalho

1. O conserto do Astra e a linha nova do relatório, de graça, com testes.
2. Os passos pagos, um por vez e com o ok do usuário:
   - o Haiku pela OpenRouter;
   - o piloto do Astra;
   - os 14 dias do Astra.
3. Os soaks, as conferências e as chamadas reais.
4. O `aceite-v0.3.md`, com as evidências e a resposta.
5. A revisão do `futuro.md`, com as ideias da §7.
6. README, diário com "a v0.3 em números", CHANGELOG, CLAUDE.md, a ADR-0076, as notas e o print.
7. `make sessoes MARCO=M22`, os custos, o commit, o push e a tag, com o ok do usuário.

**Estimativa:** uma ou duas sessões.

**Custo de API:** uns US$ 15 a 19:
- o piloto e os 14 dias do Astra, uns US$ 14 a 18;
- o Haiku, os juízes e as chamadas reais, centavos.

A v0.3 fecharia em uns US$ 275, dentro do teto de 300.

## 9. Decisões

1. **Os critérios C1 a C8** como o aceite da v0.3, com a resposta à pergunta no fim. *Recomendação: sim. São os "pronto quando" do plano macro, mais os princípios e o custo.*
2. **O conserto do Astra, a linha "respostas sem ação" e a saúde dos pilotos,** de graça. *Recomendação: sim. Sem isso, a comparação entre famílias do M21 não vale.*
3. **Os passos pagos do Astra:**
   - (a) só o piloto, uns US$ 2;
   - (b) o piloto e 14 dias, uns US$ 14 a 18;
   - (c) o piloto e o ano, uns US$ 27 a 32.

   *Recomendação: (b). Os 14 dias põem o Astra ao lado dos outros no corte do dia 14, e o teto fica com folga.*
4. **O Haiku pela OpenRouter, 2 dias,** uns US$ 0,10. *Recomendação: sim. É o jeito mais barato de saber se o cano, sozinho, muda alguma coisa.*
5. **Os soaks finais nos três mundos e as duas chamadas reais** como evidência no código que vai virar `v0.3.0`. *Recomendação: sim. Custam minutos e centavos.*
6. **O print:** a Morada do Sol na tela do jogador, com o modo de assistir como segunda imagem nas notas. *Recomendação: sim. As versões anteriores mostraram a fazenda delas.*
7. **"A v0.3 em números"** no diário, com o custo de API por marco. *Recomendação: sim, como na v0.2.*
8. **As ideias da §7** no `futuro.md`, com destino v0.4, e a rodada 3 registrada como sua decisão de 13/nov. *Recomendação: sim.*
9. **A tag `v0.3.0` e a Release** no GitHub, depois do seu ok. *Recomendação: sim, como nas outras versões.*

## 10. Como ficou

Feito em 13 e 14/nov, com as nove decisões como recomendado (ADR-0076).

- **O conserto** (`cf837ac`): na OpenRouter, a ferramenta obrigatória fora da Anthropic; a linha "respostas sem ação" no relatório e no progresso de cada dia. O relatório do M21 regravado mostra o Astra do ano com 878 de 1.872 (47%), o do procedimento com 43%, o Gemini com 10% e os Claude perto de 0%.
- **A rodada "conserto"** (`41964f6`), na pasta da terceira arena, um passo pago por vez:
  - **o Haiku pela OpenRouter, 2 dias (US$ 0,11):** nenhuma resposta vazia e a mesma latência do direto, mas umas duas vezes o custo do Haiku direto (US$ 0,045 a 0,050 no dia 2). A tradução só marca o cache no sistema e no texto do usuário, e a conversa cresce fora do cache;
  - **o piloto do Astra consertado (US$ 1,50):** nenhuma resposta sem ação em 88 chamadas, contra US$ 2,11 do piloto antigo;
  - **o Astra consertado, 14 dias (US$ 10,42):** nenhuma resposta sem ação em 586 chamadas. No dia 14, 187 moedas e 31 colheitas, contra 8 moedas e 23 colheitas do Astra do M21 no mesmo dia; nas colheitas, entre o Sonnet (21) e o Fable (38), abaixo do Opus (50). Nenhuma regra achada pelos dois juízes, nenhum plantio na faixa da lagoa, e a cultura repetida em todos os 31 plantios.
- **As conferências:**
  - os soaks repetem a fazenda 1 (1.175), a Boa Vista (220) e a Morada do Sol nos mapas a e d (85);
  - o `make check` com `TZ=UTC` deu verde, com 655 testes em Python, 90 da tela e 3 dos contratos, e 14 contratos de arquitetura;
  - o `make ui-e2e` passou 6 de 6;
  - as duas chamadas reais funcionaram, e a da OpenRouter, que chama de novo depois do resultado de uma ferramenta, mostrou o conserto direto.
- **A documentação:** o aceite, as notas da v0.3.0, o README com o diagrama novo, o CHANGELOG dos contratos com a seção `v0.3.0`, o `CLAUDE.md`, o escopo, o plano macro, o `futuro.md` revisto com as ideias da §7, "a v0.3 em números" e o diário.
- **O print:** o ano do Opus no dia 10, no verão, no modo de assistir, com a crença de que os canteiros valem por ficar perto do poço e do quiosque; a segunda imagem é a página da arena, com o Astra consertado ao vivo.
- **O que mudou em relação ao plano:**
  - o print é a visão do operador, e não a do jogador: como nas versões anteriores, ele mostra o caderno e as crenças da mente;
  - para chegar ao dia 10 no modo de assistir, uma escala maior foi mandada pelo comando de relógio, por um WebSocket aberto na página: o "Máximo" vai direto ao fim, e a velocidade padrão andou uns 6 dias simulados a cada 30 minutos;
  - o Astra consertado custou US$ 10,42, abaixo dos 12 a 16 previstos.
- **O que se achou no caminho:**
  - pela OpenRouter, o Claude não usa o cache no fim da conversa (nas notas da versão, em "conhecido");
  - a tampa do Mac fechada na bateria pausou a corrida por 26 minutos, sem perda;
  - nomes do livro em documentos antigos da fundação, achados pela busca de palavras proibidas; ficou como tarefa à parte, para o usuário decidir.
- **O custo:** uns US$ 12,40 de API (as três corridas, as provas, os dois juízes e as chamadas reais). A v0.3 fecha em uns US$ 266, dentro do teto de 300. O Claude Code levou 40 minutos ativos em 17 turnos.
- **A tag `v0.3.0`** espera o ok do usuário para o push.
