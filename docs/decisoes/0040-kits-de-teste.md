# ADR-0040 — Kits de teste: laboratório no kernel, fazenda num pacote à parte

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M1
**Complementa:** ADR-0011 (fronteiras entre pacotes), ADR-0025

## Contexto

O pytest roda no modo `importlib`, em que um arquivo de teste não consegue importar outro, nem o `conftest`. Os testes precisavam compartilhar mundos montados e controladores roteirizados. O primeiro impulso, colocar um kit dentro do pacote do cenário, quebraria a regra "cartuchos mudam o mundo só pela cartridge-api", porque o kit importa o kernel.

## Decisão

1. **`campsverso_kernel.testing`:** um cartucho de **laboratório**, mínimo e sem nada de fazenda (mapa de 7×4, uma caixa, água, duas necessidades). Prova que o kernel é genérico (ADR-0025) e serve aos testes de percepção e controladores nos próximos marcos.
2. **`campsverso_testkit`** (`tests/support/`): pacote do workspace **só para testes**.
   - Monta a Fazenda do Camps pela cadeia real (entry points), sem importar código de cartucho.
   - Oferece um controlador roteirizado (direto no núcleo ou pelo barramento validador) e o hash canônico da ADR-0021.
   - O import-linter proíbe qualquer pacote do sistema de importá-lo.
3. **Onde fica cada teste:**
   - kernel → `services/kernel/tests`, com o laboratório;
   - ações e sistemas do gênero `farm` → `cartridges/farm_camps/sim/tests`, porque é no cenário que a fazenda inteira se monta;
   - fluxo completo → `tests/e2e`.

## Consequências

- Nenhuma exceção às regras de arquitetura para acomodar testes.
- O roteiro dos testes não é o fazendeiro-script: só propõe a próxima ação de uma lista. O script com as prioridades da bíblia (§11) é do M3.
