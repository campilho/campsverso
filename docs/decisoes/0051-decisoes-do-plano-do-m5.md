# ADR-0051 — Decisões do plano do M5 (controlador humano)

**Status:** aceita · **Data:** 2026-10-12 · **Marco:** M5
**Complementa:** `docs/planos/m5-controlador-humano.md`; escopo §5 e §7; bíblia §8; ADR-0022, ADR-0050

## Decisão

As decisões do plano, aprovadas pelo usuário:

1. **Catálogo de ações declarado pelo cartucho.**
   - O cartucho declara como dados, no próprio cartucho, quais ações aparecem em cada tipo de entidade, com rótulo e parâmetros.
   - O kernel publica o catálogo no `session.started`, num campo opcional. A UI monta os menus a partir dele.
   - O menu só sugere: quem aceita ou recusa continua sendo o kernel.
   - Para o futuro: ações padrão que todo mundo tem, declaradas pelo kernel.
2. **As duas visões assumem e jogam** como o mesmo humano, `human/camps-browser`. O usuário pode ser jogador num teste e operador noutro.
3. **Modo máximo.** O kernel não deixa um humano assumir com o mundo no modo máximo, que é exclusivo de script e replay (princípio 7). Por isso:
   - na visão operador, "Assumir" passa o mundo para o contínuo antes;
   - na visão jogador, que não mexe no relógio, aparece a recusa do kernel.
4. **Só o mouse.**
   - **Clique esquerdo anda:** num tile, até ele; numa entidade, até perto dela.
   - **Clique direito abre o menu de ações** da entidade, ou o do próprio avatar.
   - Teclado e arrastar ficam para depois.
5. **Sem devolução automática, por princípio.** Se o humano não age, o avatar fica parado e o mundo segue sem ele. É o que vai acontecer com qualquer agente quando houver vários.
6. **Pulso do kernel a cada 1 s.** É configurável (`kernel.pulse_seconds`) e fica fora do histórico. O consumo é medido e anotado; se pesar, passa a 5 ou 10 s.
7. **Custos em `docs/custos/`,** só com números: tempo, chamadas e tokens por turno e por marco, mais o uso do plano anotado ao fechar cada marco. O texto das conversas nunca entra.

## Consequências

- `session.started.v1` ganha o campo opcional `affordances`, e o estado da UI o carrega na sessão.
- O gateway aceita `action.propose`, `avatar.possess` e `avatar.release` das duas visões e preenche o controlador humano; a UI não escolhe quem é.
- Um novo tipo de mensagem, `contracts/live`, para avisos que não ficam no histórico (o pulso).
