# Plano do M7 — Fechamento da v0.1

**Status:** aprovado em 12/out/2026 (ADR-0054).
**Escopo** (escopo §7): as métricas da bíblia no painel do operador, o README e o diário de bordo consolidados.
**Pronto quando:** os critérios de aceite da seção 8 do escopo estiverem conferidos.

## 1. Métricas no painel do operador (decisões 1 e 2)

O caminho, sem nada de fazenda no kernel, no gateway ou na tela:

```
farm.yaml (metrics) ─► kernel: confere e publica no session.started
                         │
                         ▼
        projeção comum: conta por dia simulado ─► gateway: ObserverState.metrics ─► painel
```

- **O catálogo, no `farm.yaml`:**

  | Métrica | Tipo | De onde |
  |---|---|---|
  | Colheitas | `count` | `action.completed` com `action: harvest`, agrupado pelo `group` do canteiro (oeste, leste) |
  | Plantas murchas | `count` | `farm.crop.withered` |
  | Ações recusadas | `count` | `action.rejected`, agrupado pelo `reason` |
  | Desmaios | `count` | `avatar.fainted` |
  | Pico de fome | `max_need` | a necessidade `fome` |
  | Moedas no fim do dia | `item` | o item `moeda` com o avatar |

- **Os grupos** vêm de uma propriedade `group` dos canteiros no mapa (`map.tmj`), que vira atributo visível da entidade.
- **A projeção comum** guarda os últimos 8 dias. O gateway já salva a projeção, então as métricas sobrevivem a um reinício.
- **O painel** mostra uma tabela com hoje, ontem e os últimos 7 dias. Somas para contagens, máximo para picos e o último valor para itens. Grupos aparecem lado a lado: "oeste 3 · leste 5".
- **`make metrics`** continua sendo a análise completa do arquivo.

## 2. Critérios de aceite (decisão 3)

`docs/aceite-v0.1.md`, um critério por linha, com a evidência e o resultado:

| # | Evidência |
|---|---|
| A1 | `import-linter` e `dependency-cruiser` no `make check` |
| A2 | validação no publicador e nos testes; exemplos inválidos recusados |
| A3, A10, A11 | soak de 30 dias com a regra e sem a regra; `make metrics` de cada um |
| A4, A5 | testes de determinismo e de replay |
| A6 | teste automático do gateway com `kill -9`, mais um roteiro manual no sandbox (derrubar gateway, arquivador e percepção) |
| A7 | teste de recuperação com `kill -9` no kernel |
| A8 | teste da credencial do controlador tentando assinar `internal` |
| A9 | teste A9 pela tela e as partidas do usuário |

Os dois soaks também medem a velocidade do modo máximo. Isso decide a primeira noite do mundo oficial.

## 3. O mundo oficial (decisão 4)

O usuário cria o `farm-camps-01` com `make run`. Quanto tempo e em que modo ele roda na primeira noite fica para depois de medir: no modo máximo, uma noite pode virar décadas simuladas e gigabytes de arquivo que nunca se apagam (`data/archive/`).

## 4. Documentação (decisão 5)

- **README final:** o que é, como rodar e jogar, um diagrama de arquitetura em Mermaid (o GitHub desenha), o estado dos marcos e as licenças.
- **`docs/diario/README.md`:** o índice das entradas, "a v0.1 em números" (tempo e tokens por marco, testes, commits, arquivos) e as frases para o LinkedIn.

## 5. Versão (decisão 6)

A tag `v0.1.0`, com notas de lançamento em `docs/versoes/v0.1.0.md`. O push da tag espera o ok do usuário.

## 6. Ordem do trabalho

1. Propriedades do mapa como atributos; o `group` dos canteiros.
2. Contratos, cartridge-api e kernel do catálogo de métricas; o catálogo da fazenda.
3. Projeção, gateway e painel.
4. Soaks de 30 dias, roteiro do A6 e `docs/aceite-v0.1.md`.
5. README, diário consolidado, notas da versão, custos e tag.
