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

## Consequências

- **O orçamento da v0.3 dobra,** e o plano passa a gastar por passos aprovados, não por rodada.
- **O `llm.call.completed.v1` ganha campos opcionais:**
  - o conselheiro;
  - o provedor que atendeu;
  - o id do modelo que a resposta trouxe.
- **A porta de modelo ganha um segundo provedor,** e a `ModelUsage`, um custo opcional dito pelo provedor.
- **O sandbox passa a retomar um mundo,** e a tela do jogador passa a mostrar o relógio quando pode mandar nele.
- **As três fazendas não mudam:** a ferramenta e o conselheiro ficam desligados fora dos braços, e as fitas passam sem regravar.
