# ADR-0077 — Decisões do plano macro da v0.4 (o escritório que constrói a si mesmo)

**Status:** aceita · **Data:** 2026-11-14 · **Marco:** antes do M23
**Complementa:** `docs/planos/v0.4-macro.md`; `docs/planos/ideia-escritorio-que-se-constroi.md`; ADR-0055; ADR-0064
**Revê:** ADR-0074, decisão 30 (a bancada dos harnesses como primeiro marco); ADR-0055, decisão 6 (o revisor como primeiro ajudante); a decisão do usuário de 13/nov que mandou a rodada 3 para a v0.4 (ADR-0076)

## Contexto

A v0.3 fechou em 14/nov com a tag `v0.3.0` (ADR-0076). O plano macro da v0.4 foi proposto no mesmo dia, começando por dois marcos na fazenda: a bancada dos harnesses e a mente que planeja, lembra e calcula, com a rodada 3. Só depois vinha o escritório, com a tela em corte do protótipo do Claude Design (`docs/design/escritorio/`).

O usuário mudou o rumo:
- a fazenda já provou o que tinha a provar, e a v0.4 começa direto no escritório;
- a vista é a de cima, com arte LPC, no mesmo renderer da fazenda, com o visual caprichado e o movimento sem pulos;
- o escritório roda em tempo real;
- o dev é sempre um LLM, e o humano entra como o gerente;
- os robôs do protótipo eram só uma exploração de imagens;
- não há corridas: o teste de cada marco é o dev criar alguma coisa do próprio escritório;
- o site fica para depois, como o replay de um dia, igual ao do CampsCast.

O plano foi reescrito nessa linha e aprovado como recomendado.

## Decisão

**As regras do escritório,** definidas pelo usuário:

1. O dev é sempre um LLM, com um script de reserva. Nenhum humano assume o dev.
2. O humano entra como o gerente. Como no filme Matrix, para entrar no mundo é preciso assumir alguém lá dentro: o gerente fala com o dev e escreve os pedidos no quadro.
3. LLMs são sempre avatares humanos. Os robôs são ferramentas (scripts, código), nunca um LLM.
4. O elenco começa com o Camps, líder técnico e único dev, o gerente e o vigia, que só aparece à noite.
5. Não há corridas. O teste de cada marco é uma criação do dev, usada no marco seguinte.
6. Os pedidos vêm só do gerente, por enquanto. Depois o dev ganha um telefone para falar com o usuário.
7. O escritório roda em tempo real, e acelerar é raro.
8. A vista é a de cima, com arte LPC (a ADR-0055, decisão 7, fica como estava).
9. O site é o replay de um dia, para depois. O protótipo do Claude Design é a referência dele.

**As decisões do plano,** aprovadas como recomendado:

1. **Oito marcos, do M23 ao M30:**
   - M23, o escritório;
   - M24, o dev pensa e cria;
   - M25, o ciclo fecha;
   - M26, o Claude Code;
   - M27, o Codex e o Antigravity;
   - M28, o computador do dev;
   - M29, o telefone;
   - M30, o fechamento.

   O que não couber vai para um "escritório 2".
2. **A fazenda sai da v0.4.** A bancada na fazenda, a rodada 3 e as ideias de planejar e lembrar vão para a fazenda 4. As que servem ao dev entram nele.
3. **O orçamento de API é de US$ 300,** com teto por dia e por pedido, e cada etapa paga com o ok do usuário.
4. **O tempo real:**
   - o relógio de São Paulo a 1×;
   - as durações em minutos, convertidas pelo kernel;
   - um tick entre 1 e 5 s, escolhido pela medida no M23;
   - o relógio salta até agora quando a pilha sobe de novo.

   A ADR é escrita no M23, porque toca o princípio 7.
5. **O movimento:** reproduzir o pulo na fazenda, com teste, e redesenhar o andar para o tempo real na tela que as duas usam.
6. **A arte:**
   - "LPC Revised: The Office";
   - a mobília LPC;
   - o gerador de personagens (roupa formal, óculos);
   - o que faltar, desenhado no estilo.
7. **Um gerente-script nos testes,** com pedidos roteirizados.
8. **Os dois cérebros:** o mesmo modelo na mente e no harness, e cada dev com o harness do próprio laboratório.
9. **A escada das ferramentas** começa pelo nosso harness pela API, com ferramentas nossas e pequenas, para todos os modelos já testados. O Claude Code vem no M26.
10. **Os robôs são as criações do dev** e ficam na bancada. As ferramentas de software ficam no computador da mesa.
11. **A prova de conformidade** antes de cada modelo e de cada harness novo.
12. **O teste de cada marco é uma criação do dev,** com o teste de aceite do gerente. Se o dev não conseguir, nós fazemos, e a tentativa fica como dado. As criações propostas se confirmam no plano de cada marco: o testador, o briefing, o conector do Codex, a receita do computador e o telefone.
13. **As medidas são por pedido,** no lugar das corridas. Comparar é repetir um pedido com outro dev, só quando valer a pena.
14. **Onde vive o trabalho:** no M24, um espaço de trabalho isolado e um patch que o humano aplica; do M25 em diante, PRs no GitHub, mesclados só pelo humano.
15. **A constituição e o isolamento,** como na §6 do plano.
16. **O computador do dev:** uma máquina por dev, isolada e persistente. Primeiro local, depois a nuvem quando precisar. O Claude Code dentro dela usa uma chave de API. A ADR é escrita no M28.
17. **O telefone:** o dev fala só com o usuário, e o que chega por ele é dado. O canal fica para o plano do M29.

## Consequências

- **A bancada dos harnesses** (ADR-0074, decisão 30) deixa de ser um marco na fazenda e vira a escada de ferramentas do dev, medida no escritório (M24, M26 e M27).
- **O primeiro ajudante não é mais um revisor LLM** (ADR-0055, decisão 6). Um segundo LLM, um dia, é outro dev, um avatar humano. Os subagentes como mini-robôs e o escritório espelho, que punham um LLM num robô e um humano no dev, ficam para revisão no `futuro.md`.
- **A tela em corte do protótipo** não vira cartucho. Fica como referência do site.
- **O `futuro.md`** ganha os destinos novos: fazenda 4, escritório 2 e os marcos da v0.4.
- **O CLAUDE.md e o README** contam a v0.4 nessa linha.
- **O M23 começa pelo plano,** antes do código.
