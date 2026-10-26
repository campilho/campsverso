# ADR-0072 — Decisões do plano do M20 (os ajudantes)

**Status:** aceita · **Data:** 2026-10-26 · **Marco:** M20
**Complementa:** `docs/planos/m20-os-ajudantes.md`; ADR-0055 (agentes novos entram como dados); ADR-0066 (decisões 10 e 14); ADR-0067 (a Morada do Sol); ADR-0068 (o raio); ADR-0069 (a economia); ADR-0070 (o script 3 e o oráculo)

## Contexto

A v0.3 prometeu ajudantes contratáveis, com fichas, e vários avatares na percepção, na posse e na tela. O kernel já lida com N avatares. O resto da plataforma está preso ao `camps`, e nada adiciona um avatar no meio da corrida. As fichas foram propostas no diário de 21/out.

## Decisão

1. **Os cinco ajudantes são avatares declarados pelo cenário,** fora da fazenda até a contratação. O kernel ganha a presença do avatar: entrar e sair são operações do mundo, com evento. Fora da fazenda, o avatar não recebe pedido de decisão nem segura o relógio.
2. **O ajudante é um script que obedece às ordens** de quem o contratou.
3. **O contrato:** no quadro de ajudantes da entrada, por 1, 3 ou 7 dias, pago adiantado, sem devolução ao dispensar.
4. **As ordens** são um conjunto fechado de tarefas: cuidar (o padrão), regar, colher, plantar, cavar, vender e parar. São dadas ao lado do ajudante, e a ordem fica até ser trocada.
5. **As fichas de 21/out:**
   - Dita, a plantadeira;
   - Zé Graúdo, o carregador;
   - Nina, a batedora;
   - Seu Bento, o veterano;
   - Tião, o aprendiz.

   Os traços são modificadores genéricos do avatar no kernel. O raio fica na regra de percepção, e a semente perdida do Tião é uma regra do cenário. As diárias são calibradas pelo oráculo.
6. **O dia do ajudante:** chega às 06:00 e sai às 18:00, com a exceção do Seu Bento (das 08:00 às 16:00). Come do baú da fazenda, vai embora mais cedo sem comida e dorme em casa.
7. **Cada avatar vê só o que está à volta dele.** Não há visão compartilhada, o inventário de outro avatar não aparece, e há um usuário do NATS por avatar.
8. **A visão do jogador vira a percepção do avatar dele, no gateway.** O operador continua vendo tudo.
9. **O script 3 contrata pela conta do dinheiro,** e o oráculo é o mesmo código. O script 2 nunca contrata.
10. **A mente ganha as ferramentas e o manual dos ajudantes** só na Morada do Sol, com a fita regravada. Esta decisão ficou sem resposta na aprovação e segue a recomendação do plano.
11. **A arte:** cinco personagens montados com peças do gerador LPC, com os créditos. As peças que não estão no repositório são baixadas com a permissão do usuário na hora.
12. **A medição e a verificação:**
    - métricas por avatar;
    - a seção dos ajudantes no relatório da arena;
    - o script 3 e o oráculo com e sem ajudante nos mapas a e b, de graça.
13. **O critério do marco:** um ano com o script 3 contratando, sem travar, com as recusas esperadas, e o replay de um dia com dois avatares.

## Notas do usuário (26/out)

- **2:** o ajudante é um script neste momento, porque os scripts vão melhor que os modelos. No futuro, deveria ser o Haiku, mas só quando acharmos uma forma de os modelos simples irem bem.
- **6:** das 6 às 18, e pode haver exceção.
- **7:** são personagens independentes.
- **11:** eu monto a arte, e o usuário ajusta depois, se precisar.
- **13:** testar contratar por 1, 3 e 7 dias, e ver se a diária está bem calibrada: com o ajudante, o resultado deve ser melhor do que sem ele.
- **Sem push por enquanto:** os commits vão para o GitHub no fim do dia.

## Consequências

- **O kernel ganha a presença e os traços do avatar, e o patrão de um ajudante,** sem saber o que é uma fazenda.
- **A percepção, o NATS, o runner, o gateway, a tela e a medição passam a ter vários avatares.** O `camps` deixa de ser o único avatar e passa a ser o avatar do jogador.
- **As fazendas 1 e 2 não mudam.** A Morada do Sol ganha os ajudantes, e a fita dela é regravada.
