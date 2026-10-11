# ADR-0028 — Percepção da v0.1 só com instantâneos; deltas na v0.2

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M0 (contrato), M3 (serviço)
**Altera:** `contratos-eventos-v0.md` §14.4

## Contexto

A seção 14.4 prevê que `perception.delivered` leve instantâneos e também deltas.

- **Instantâneo:** a foto completa do que o avatar percebe no momento da decisão. Por exemplo: "são 14:20, sol; você está em (12, 9) com fome 62 e energia 40; no inventário, 3 rabanetes e o regador com 4 cargas; `plot-e-01` maduro, `plot-e-02` em broto e regado hoje, …" (os 16 canteiros, o baú, o quiosque).
- **Delta:** só o que mudou desde a foto anterior. Por exemplo: "desde as 13:50, `plot-e-01` amadureceu, o regador perdeu 2 cargas e o quiosque fechou".

Para quem decide, as duas formas servem a coisas diferentes:

| Controlador | Precisa de |
|---|---|
| Script | do instantâneo: reavalia as prioridades da bíblia (§11) do zero a cada decisão |
| Humano | de nenhum dos dois: vê o mundo na tela, pelos eventos `world` que o gateway repassa |
| LLM (v0.2) | dos dois. A foto inteira a cada decisão custa tokens; o delta é mais barato e é o formato natural de "o que aconteceu enquanto eu fazia outra coisa", que alimenta memória e narrativa |

## Decisão

- Na v0.1, `perception.delivered.v1` leva **só o instantâneo** (`kind: snapshot`), um a cada `avatar.decision_requested`.
- Os deltas são desenhados na v0.2, junto com o controlador LLM, que é o primeiro consumidor real. Lá se decide se viram `kind: delta` no mesmo tipo ou um tipo próprio.

## Consequências

- O serviço de percepção da v0.1 fica simples: uma projeção do mundo e uma foto por pedido de decisão.
- Nada impede acrescentar deltas depois: é um campo ou tipo novo, compatível pelas regras da seção 9.
