# ADR-0071 — O agricultor treinado: um playbook de método para qualquer modelo

**Status:** aceita · **Data:** 2026-10-25 · **Marco:** entre o M19 e o M20
**Complementa:** `docs/planos/agricultor-treinado.md`; ADR-0059 (a mente); ADR-0066 (decisão 17, o orçamento); ADR-0070 (decisões 4, 9 e 14)

## Contexto

Na rodada de verificação do M19, o Haiku propôs 27 experimentos da noite, todos sobre o que o manual já explica. Nenhum comparou canteiros em lugares diferentes, nem o mesmo canteiro em plantios seguidos, e a fadiga do solo foi lida como efeito da estação. O caderno de campo já tinha os fatos; faltava o método para lê-los. O script 3 tem esse método escrito em código. A pergunta é se um modelo que recebe o mesmo método, em palavras, também aprende.

## Decisão

1. **Um playbook para qualquer modelo.** O texto é o mesmo para todos os modelos, presentes e futuros, e é ligado por corrida. A corrida sem playbook continua sendo o padrão, para não quebrar as comparações antigas. O texto melhora conforme o desempenho, com cada versão no git.
2. **Duas camadas:**
   - **o método,** em `libs/mind`, para qualquer mundo; um mundo que não liga o playbook não o vê;
   - **o ofício do agricultor,** no gênero `farm`, porque só faz sentido nele.
3. **Só método, nunca regra oculta (princípio 5).**
   - As suspeitas que o playbook sugere são as mesmas do script 3, que a ADR-0070 (decisão 4) julgou justas: atributos que qualquer um vê, misturados com distratores.
   - O teste de palavras proibidas da mente lê o playbook.
   - Contar as regras (o "saber do ofício" da ideia original) mediria outra coisa e fica fora.
4. **O Haiku em três corridas de 28 dias:** com o playbook no mapa a, e sem e com o playbook no mapa b. A corrida sem playbook do mapa a é a do M19. Custam uns US$ 2,10.
5. **O Sonnet só se o Haiku mudar** pelo critério do plano (§2). Nesse caso, uma dupla de 14 dias, sem e com o playbook, no mapa a, com teto de US$ 15 por corrida.
6. **O rascunho do playbook** do plano (§1) foi aprovado como está.

## Notas do usuário (25/out)

- **2:** uma biblioteca é importada só por quem a usa, como a economia e o clima.
- **3:** fica para depois um outro experimento, o agente que joga de novo com o que aprendeu: 30 dias, depois mais 30 com a memória da primeira corrida, N vezes. E outras técnicas de prompt: exemplos (one-shot e few-shot), cadeia de raciocínio e papel. O papel já existe (o cartão do Camps), e o raciocínio adaptativo já está ligado. Os dois experimentos estão no `futuro.md`.
- **4:** por que três corridas? Elas não tiram a aleatoriedade do modelo. Uma corrida por condição não separa o efeito do playbook da variação entre corridas, que o M12 mostrou com quatro seeds. As três medem o playbook num mapa e conferem se o efeito aparece em outro. Se o resultado for ambíguo, repetições do Haiku custam US$ 0,70 cada.
- **5:** o saldo da Console era de US$ 54,25 em 25/out. O pior caso deste passo (uns US$ 27) cabe. A arena do M21 vai pedir créditos novos, como a ADR-0066 já previa.

## Consequências

- **A mente ganha um campo, o ofício do gênero,** e o controlador LLM ganha a opção de ligar o playbook. Com ela desligada, o pedido é o mesmo de antes, e as fitas passam sem regravar.
- **A arena ganha `playbook` em cada corrida,** e o relatório mostra quem jogou com ele.
- **O M21 decide,** com este resultado, se a arena roda com o playbook, sem ele ou com os dois.
