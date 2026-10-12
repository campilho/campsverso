# ADR-0047 — Decisões do plano do M3 (controladores headless)

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M3
**Complementa:** `docs/planos/m3-controladores.md`; escopo §5, §7; bíblia §11, §12

## Decisão

As sete decisões do plano, aprovadas pelo usuário:

1. **`move {near: entity_id}`:** o kernel escolhe o tile livre e alcançável mais próximo, pelo caminho, ao lado da entidade. O instantâneo da percepção não traz o mapa, e o script precisa saber onde pisar. O mesmo atalho serve ao humano (M5) e ao LLM (v0.2).
2. **Percepção durável:** projeção própria em arquivo, com o último `seq` aplicado, mais um consumidor durável que só confirma depois de gravar.
3. **Resistência:** o `make check` roda 2 dias simulados com processos; os 30 dias ficam no `make soak DAYS=30`, rodado à mão, com os números no diário.
4. **Replay (A5):** `make replay DAY=N` reexecuta o dia no kernel, a partir do snapshot do começo do dia e do diário de entradas, e compara o hash com o arquivo JSONL. O controlador replay tem um teste próprio pelo barramento.
5. **Lockstep sem prazo:** no modo máximo, o kernel espera o controlador o quanto for preciso. A telemetria avisa a cada 10 s de espera. Prazo real com ação reflexa chega com o LLM (tempo §6.1).
6. **`make metrics`:** lê o arquivo JSONL e calcula as métricas da bíblia §13 por dia. O mesmo código serve aos testes do A10 e do A11.
7. **Sem salto de tempo no M3:** o modo máximo roda tick a tick. O salto volta se o soak mostrar que faz falta (ele precisaria entrar no diário).

## Para o futuro (não agora)

- **Enxergar o mapa.** Quem joga vê o mapa inteiro na tela; o script e o LLM também precisam vê-lo, para não jogarem em desvantagem.
  - Caminho natural: o instantâneo ganha, como campo opcional e compatível, os tiles ao alcance do avatar (passável, água etc.), num raio N declarado pelo cartucho.
  - É o "raio de percepção configurável" da bíblia §12. Na fazenda, o raio cobriria a propriedade inteira.
  - O `move {near}` continua útil depois disso, como atalho.

## Consequências

- O catálogo §3.4 ganha a forma `{ near: entity_id }` para `move`. `params` é livre no schema, então nenhum contrato muda.
- O M3 entrega quatro processos que conversam só pelo NATS: kernel, percepção, controller-runner e arquivador.
