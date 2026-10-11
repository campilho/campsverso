# ADR-0019 — Ordem dos ids dos canteiros

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M1
**Esclarece:** `fazenda-camps-biblia-v0.1.md` §4 (canteiros) e §11 (desempate do script)

## Contexto

A bíblia lista `plot-w-01` … `plot-w-08` em x 8–11, y 9–10 (e o mesmo para o leste), mas não diz qual id fica em qual tile. O fazendeiro-script desempata por menor distância e depois por **menor id**, então a numeração muda o comportamento.

## Decisão

Numeração por linha (y crescente) e, dentro da linha, por x crescente:

| Ids | Tiles |
|---|---|
| `plot-w-01` … `plot-w-04` | (8, 9) … (11, 9) |
| `plot-w-05` … `plot-w-08` | (8, 10) … (11, 10) |
| `plot-e-01` … `plot-e-04` | (24, 9) … (27, 9) |
| `plot-e-05` … `plot-e-08` | (24, 10) … (27, 10) |

## Consequências

- A numeração fica nos dados do mapa do cartucho (Tiled).
- Mudar a numeração muda o comportamento do script e invalida a comparação com execuções anteriores. Se for necessário, registrar nova ADR.
