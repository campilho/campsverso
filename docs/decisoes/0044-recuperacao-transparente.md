# ADR-0044 — Recuperação transparente: snapshot, diário e outbox

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M2
**Complementa:** plano do M2 §1 (decisões 1 e 3)

## Contexto

O plano do M2 fixou a estratégia de recuperação: snapshot completo de hora em hora, diário de entradas e outbox. Ao implementar, surgiram escolhas de detalhe que mudam o que os eventos mostram.

## Decisão

1. **A queda é invisível para quem consome.**
   - A recuperação não publica `session.started` com `resumed: true`.
   - O fluxo de eventos continua do `seq` seguinte, como se tivesse havido só uma pausa. É o que permite comparar o hash com uma execução sem queda (A7).
   - O reinício aparece na telemetria (`kernel.recovered`). `resumed: true` fica para quando uma sessão nova começar de um snapshot (replay, no M3).
2. **Só se grava o que produziu algo.** Cada comando, e cada tick que gerou fatos, é uma transação. Ticks quietos não gravam nada.
   - Depois de uma queda, o kernel volta à última fronteira gravada e roda de novo os ticks quietos. Eles não geram fatos, então ninguém percebe.
3. **O snapshot é um fato.**
   - O snapshot agendado cai depois do tick que fecha cada bloco de 60. O aviso `world.snapshot.created.v1` tem `seq`, e o estado gravado já o conta.
   - Id: `t<tick>-s<seq>`, único mesmo quando a parada elegante cai no mesmo tick de um agendado.
   - A parada elegante entra no diário como uma entrada do tipo `snapshot`, para que reexecutar o diário (M3) a reproduza.
4. **A versão do código é o sha256 dos arquivos** do kernel, da cartridge-api, dos contratos e da cadeia de cartuchos, mais a cadência de snapshots.
   - A versão de pacote em desenvolvimento quase nunca muda; os arquivos mudam.
   - Incrementais gravados por outra versão são recusados, como no plano. Para trocar de versão: parar com elegância, que grava um snapshot sem incrementais depois.
5. **Retenção:**
   - o snapshot inicial (tick 0) nunca sai, porque é a origem do mundo;
   - dos outros, ficam os `keep_full` mais recentes (168, ou 7 dias simulados);
   - o outbox apaga os fatos já publicados antes do snapshot mais antigo que ficou. O arquivo JSONL é a memória longa.
6. **Ordem do estado preservada:** o snapshot guarda os dicionários na ordem em que estão, para que o mundo restaurado itere igual ao original.
   - Um teste compara o estado completo depois de restaurar. Foi ele que achou a escala gravada como `72` e restaurada como `72.0`.

## Consequências

- O A7 exige o hash idêntico ao de uma execução sem queda, e não só a `seq` contínua.
- Uma mudança de código entre a queda e o reinício exige voltar à versão anterior para recuperar. É o preço da conferência.
