# ADR-0038 — Decisões do kernel para o M1

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M1
**Complementa:** ADR-0025 (modelo de mundo), `kernel-gestao-do-tempo.md`

## Decisão

1. **Necessidades em números inteiros.** 1 ponto = 120 unidades.
   - Uma taxa por hora vira unidades por tick: `taxa × 120 × tick_segundos / 3600`. O resultado precisa ser inteiro; se não for, é erro de carga.
   - Na fazenda: fome +3/h = 6 por tick; +1/h = 2; energia +12,5/h = 25.
   - Os eventos mostram o valor em pontos (unidades / 120).
2. **Modelo de mundo e A\* próprios**, pequenos e determinísticos, sem biblioteca de ECS nem de caminhos.
   - Estudar ECS no futuro. Gatilho: centenas de entidades ativas ou desempenho medido como problema.
3. **Calendário configurável por mundo.**
   - O mundo `farm-camps-01` e os testes começam em **2026-10-10 06:00 −03:00**, o dia em que o projeto começou.
   - O dia agrícola começa no horário que o cartucho define (06:00 na fazenda; ADR-0018).
4. **Aleatoriedade própria e estável.**
   - Cada fluxo nomeado tem um gerador SplitMix64, com semente derivada de (seed do mundo, nome do fluxo) por SHA-256.
   - O `random` do Python é proibido na simulação (princípio 4), e a sequência não muda entre versões do Python.
5. **Núcleo determinístico, serviço em volta.**
   - O núcleo do kernel é síncrono: recebe comandos, avança ticks e produz **fatos** (tipo, payload, tick, seq).
   - Um serviço assíncrono em volta carimba `id` e `time` (relógio de parede, pelas portas), resolve `causationid` e `correlationid` e publica pelo `EventBus`.
6. **`move` e `wait` são ações do kernel** (física do espaço e do tempo), com parâmetros do cartucho, como a velocidade. As demais ações são do cartucho.
7. **Detalhes do ciclo de ação:**
   - toda ação dura pelo menos 1 tick;
   - mover para o próprio tile é recusado (`already_there`);
   - o custo de energia é cobrado na conclusão, então uma ação cancelada não gasta energia;
   - uma proposta recusada não cancela a ação em andamento.
8. **O "1 dia" do M1 roda com comandos roteirizados no teste.** O fazendeiro-script é do M3.

## Consequências

- O núcleo é testável sem barramento, sem relógio de parede e sem rede.
- O mesmo núcleo serve ao modo contínuo, ao máximo e ao passo a passo; só o serviço muda o ritmo.
