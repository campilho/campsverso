# ADR-0070 — Decisões do plano do M19 (os controladores e a medição)

**Status:** aceita · **Data:** 2026-10-25 · **Marco:** M19
**Complementa:** `docs/planos/m19-os-controladores-e-a-medicao.md`; ADR-0060 (a memória da mente); ADR-0061 (a arena); ADR-0066 (decisões 11, 13, 18 e 20); ADR-0067 (a Morada do Sol); ADR-0069 (a economia)

## Contexto

A v0.2 não conseguiu medir o que mais interessava, aprender o mundo. As heurísticas de "descobriu" erraram no M14, e a linha de base sem modelo (o script 2) é cega. A ADR-0066 decidiu que as regras ocultas são verdades fixas do mundo e que o que muda de uma corrida para outra é o mapa. O desenho das variantes do mapa ficou para este plano. O mapa de hoje junta duas regras: a terra boa perto da água fica onde os corvos comem.

## Decisão

1. **As variantes do mapa são receitas sobre o mapa de hoje.**
   - Ficam no lugar: a casa, o centro, a estrada e a entrada com o quiosque, o quadro e a barraca.
   - Mudam: a água e as matas em volta dela.
   - Um script do repositório aplica cada receita e confere o resultado. O mapa de hoje é a variante `a` e não muda.
2. **Três variantes e uma reservada:**
   - **a, o rio:** a de hoje;
   - **b, o córrego:** um córrego perto da casa, com a terra boa a salvo dos corvos;
   - **c, as lagoas:** só lagoas longe, com a terra boa além da linha dos corvos;
   - **d:** desenhada só no M21 e nunca usada nos testes do script 3.
3. **O arquivo do mundo escolhe o mapa** (`map:`), como já escolhe o arquivo de regras.
   - O cartucho lista os seus mapas, e o kernel carrega o escolhido.
   - O id do mapa vai no `session.started`, e a tela escolhe o mapa visual pelo id.
   - Um mundo que já existe recusa trocar de mapa.
   - Mundos novos `farm-morada-do-sol-02` (b) e `-03` (c), com a mesma seed do `-01`.
4. **O fazendeiro-script 3 aprende sem saber as regras.**
   - **Os atributos que ele observa:** do tile, a distância à água, à mata, ao caminho e à porta, em faixas; do canteiro, a cultura anterior e o adubo. Há distratores de propósito, atributos que não importam.
   - **O modelo bayesiano:** ele começa com uma crença larga sobre o efeito de cada atributo (pode não ser nada, pode ajudar ou atrapalhar), e cada colheita estreita a crença. É o mesmo para as perdas de noite, por faixa de distância da porta e do espantalho.
   - **A amostragem de Thompson:** para planejar, ele sorteia um mundo plausível da crença e age como se fosse o verdadeiro. Enquanto a crença é larga, os sorteios às vezes favorecem o lugar desconhecido, e ele vai testar. Quando ela estreita, os sorteios concordam, e ele para de testar. Ele explora na medida da própria dúvida.
   - **Os pares de teste:** nos primeiros dias, a mesma cultura vai a dois lugares diferentes no mesmo dia; depois, uns 10% dos plantios continuam como teste.
   - **A alternativa descartada, o processo gaussiano:** um mapa de calor do rendimento sobre as coordenadas, supondo que vizinhos rendem parecido. Ele pede mais plantios do que um ano dá, e aprende lugares, não causas: num mapa novo não serviria.
5. **O script 3 joga a economia inteira:** o capital, a feira, as encomendas com folga, o tacho, a composteira e a colheita antes da tempestade. Ele usa o baú e cozinha, mas não procura as regras ocultas da Boa Vista, que dependem de ações raras. *(Pergunta do usuário: por que não usar tudo? A composteira entrou.)*
6. **O oráculo é o mesmo código com a verdade num arquivo,** sem exploração. Um teste confere o arquivo com os dados do cartucho. O valor de saber é o oráculo menos o script 2, e o que o script 3 captura é a fração desse valor que ele ganha.
7. **O que o script 3 aprende fica na memória do processo,** como a lembrança do script 2. Ele esquece quando o processo reinicia, e cada corrida começa do zero, de propósito: lembrar de outro mapa seria trapaça. *(Pergunta do usuário.)*
8. **O caderno de campo na mente:**
   - uma linha por plantio (onde, a cultura, a cultura anterior, as regas, os dias, o que houve), calculada só do que o avatar viu;
   - os últimos plantios e um resumo por cultura no bloco de abertura, e tudo numa tabela nova da `MemoryPort`;
   - ligado na Morada do Sol e desligado nas fazendas 1 e 2.
9. **O experimento da noite:** a reflexão propõe a hipótese, o teste e a previsão para o dia seguinte, e a noite seguinte diz se a previsão se cumpriu. Só na Morada do Sol.
10. **O resumo da reflexão é cortado na primeira marcação de ferramenta,** com o plano também. O relatório mede o vazamento pela fita.
11. **As métricas de exploração ficam no avaliador,** e não no kernel. As zonas são tiradas da verdade da bíblia, e nada volta ao mundo.
12. **A prova do mundo:**
    - perguntas fechadas com "não sei", fora do pacote da mente;
    - feita antes (no dia 0, sem memória) e depois da corrida, e a nota é a diferença;
    - o script 3 responde pelo modelo dele, o oráculo pela verdade, e o script 2 não faz.
13. **O juiz é o Opus 5.5:** uma chamada por corrida, com a rubrica de três vereditos por regra (a causa, só o lugar, não), gravada em fita. Ele é conferido contra um gabarito feito à mão das 12 corridas com memória do M12 e do M14 (47 vereditos), com meta de 90% de concordância. *(Pergunta do usuário: o Opus julgando o Opus.)*
    - O juiz lê as crenças sem saber de quem são, com a verdade das regras e uma rubrica fechada. Classificar contra um gabarito é menos sujeito à preferência pelo próprio texto do que dar nota de qualidade.
    - O gabarito inclui a corrida do Opus no M14, e a concordância é medida por controlador.
    - No M21, as corridas do Opus ganham um segundo juiz (o Sonnet ou outra família), e as discordâncias vão para o relatório.
14. **A rodada de verificação:** os scripts nos três mapas, de graça, e uma corrida de 28 dias do Haiku com o caderno, a prova e o juiz. Nem Opus nem Sonnet jogam neste marco: o Opus aparece só como juiz. *(Nota do usuário.)*
15. **O CI roda o script 3 o ano inteiro** nos três mapas e sem a regra.

## Durante a implementação (25/out)

O script 3 mostrou que, na Morada do Sol com a economia do M18, ninguém comia direito: o script 2 passava 16 dos 28 dias com a fome em 100; com 400 moedas a mais no começo, perdia 327; e o oráculo, sabendo as regras, também passava fome nos mapas a e c. O freio é a comida: a fome comia quase metade do que 16 canteiros produziam, e a semente custa uns 40% da venda. Decisões do usuário:

16. **A fome da Morada do Sol calibrada em 2 por hora acordado** (era 3), nos dados do cenário (`needs`), sem mudar as fazendas 1 e 2. Com 2, o oráculo atravessa o ano sem fome nos três mapas, e quem ainda aprende passa fome: a diferença é o valor de aprender (a tabela está na bíblia 3, §15).
17. **As regras de sobrevivência são explícitas para todos:** comer cedo, separar os canteiros da comida (M) dos de vender (N), guardar comida para dois dias e não investir o dinheiro da semente da comida. Estão no manual da mente da Morada do Sol e na configuração do script 3 e do oráculo; o script 2 fica como era, a linha de base cega. Com moedas sobrando, o fazendeiro compara o custo das comidas e anota o que descobre dos pratos no caderno.

O gabarito feito à mão do juiz (decisão 13), marcado antes de o juiz rodar, saiu com os 47 vereditos em "não": nenhuma das 12 corridas com memória do M12 e do M14 terminou com uma crença ativa que diga uma regra oculta. Assim a conferência só mediria se o juiz inventa descobertas, e não se ele reconhece uma. Decisão do usuário:

18. **O juiz é conferido também contra controles,** marcados no gabarito antes de ele rodar (`docs/arena/juiz-gabarito.yaml`). São dois tipos:
    - **Um controle real:** a s2 do M12 lida até o dia 25, quando uma crença dizia, a 0,85, que a abóbora amadurece em 6 dias "nos canteiros do leste" (só o lugar).
    - **Quatro dossiês de corridas reais com crenças acrescentadas à mão:** uma causa por regra da Boa Vista; as armadilhas (repetir o manual, contradizer a regra, só o lugar); a confiança baixa e a crença retirada; e as regras novas da Morada do Sol.

    Ao todo, 28 vereditos, 15 deles positivos. A concordância conta à parte nas corridas e nos controles, e os dois números vão para o relatório.

## Consequências

- **O kernel ganha só a escolha do mapa pelo arquivo do mundo,** sem primitiva nova.
- **A `libs/mind` ganha:**
  - o caderno de campo e o experimento, opcionais por mundo;
  - o corte do resumo, para todos.
- **O contrato `memory.reflected.v1`** ganha campos opcionais para o experimento.
- **As fazendas 1 e 2 ficam com as fitas e as medições de sempre,** e a Morada do Sol ganha a fita regravada.
- **A arena passa a ter três réguas:** o script 2 (cego), o script 3 (aprende) e o oráculo (sabe). O relatório ganha a exploração, a prova e o juiz ao lado das heurísticas.
- **Fica para depois da corrida do Haiku:** o agricultor "treinado", um playbook com o método e o saber do ofício, medido sem e com (`futuro.md`).
