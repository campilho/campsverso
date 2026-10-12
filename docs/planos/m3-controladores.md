# Plano do M3 — Controladores headless

**Status:** aprovado em 11/out/2026 (ADR-0047); em implementação.
**Escopo** (escopo §7): percepção, `decision_requested`, controller-runner com script e replay, posse, modo máximo.
**Pronto quando:** 30 dias simulados com o fazendeiro-script, sem intervenção; os testes de determinismo e de replay passam.
**Critérios de aceite cobertos:** A3 (resistência), A4 (determinismo), A5 (replay), A9 (posse), A10 (economia sustentável) e uma prévia do A11 (evidência da regra oculta).

## 1. O ciclo de decisão, ponta a ponta

```
kernel ──decision_requested (agent.camps)──► percepção ──perception.delivered (agent.camps)──► controller-runner
   ▲                                         (projeção do mundo,                                (script ou replay)
   │                                          só eventos world)                                        │
   └───────────────────── cmd.action.propose (mesmo correlationid) ◄───────────────────────────────────┘
```

1. O avatar fica ocioso e o kernel publica `decision_requested`. Isso já existe desde o M1.
2. A **percepção** responde com `perception.delivered`: um instantâneo do que o avatar percebe (ADR-0028), com o mesmo `correlationid`.
3. O **controller-runner** roda o controlador que tem a posse e publica `cmd.action.propose` com esse `correlationid`.
4. **No modo máximo (lockstep)**, o kernel não avança enquanto espera a resposta do controlador.

## 2. Serviço de percepção (processo próprio)

- **Lê só `world`**, mais os pedidos de decisão do avatar. A credencial dele nunca vê `internal`, então nada oculto vaza (princípio 5).
- **Mantém uma projeção do mundo:** entidades e atributos visíveis, itens por contêiner, clima, fase do dia, posição e ação de cada avatar.
  - Necessidades vêm exatas no próprio `decision_requested`.
  - A posição no meio de um trajeto sai da conta do `entity.moved` (D1).
- **Monta o instantâneo** no formato genérico de `perception.delivered.v1` (catálogo §3.7). Nada nele é específico da fazenda.
- **Durabilidade** (decisão 2): a projeção vai para um arquivo junto com o último `seq` aplicado, e a confirmação no JetStream só sai depois de gravar. Se cair, a percepção volta do arquivo e o consumidor durável entrega o que faltou.
- **Ordem:** antes de montar a foto, a percepção esvazia o que ainda está pendente no stream `WORLD`. O kernel publica em ordem de `seq`, então tudo o que aconteceu antes do pedido já está lá.

## 3. Controller-runner e os controladores

- **Processo próprio**, que carrega o controlador pelo nome, por entry point, como o kernel faz com os cartuchos (ADR-0011). Depende só dos contratos.
- **Fazendeiro-script** (bíblia §11), em `cartridges/farm/script`:
  - função pura do instantâneo para uma proposta;
  - prioridades na ordem da bíblia, desempate por menor distância e depois por menor id;
  - prefere a cama; dorme no chão só se não der tempo de chegar (ADR-0041).
- **Para chegar perto de uma coisa**, o script precisa saber onde pisar, e o instantâneo não traz o mapa. Proposta (decisão 1): `move` aceita `{near: entity_id}`, e o kernel acha o tile livre e alcançável mais próximo ao lado da entidade. Serve também ao humano (M5) e ao LLM (v0.2).
- **Controlador replay:**
  - lê os comandos aceitos de uma sessão gravada;
  - a cada pedido de decisão, reenvia o próximo com `at_tick` = o tick em que foi aplicado na sessão original;
  - o kernel passa a aceitar `at_tick`, só do controlador replay e no modo máximo (já previsto no contrato), e aplica a proposta exatamente naquele tick.

## 4. Kernel

- **Lockstep no modo máximo** (decisão 5):
  - o núcleo marca o avatar como "aguardando" quando pede uma decisão a um controlador script ou replay;
  - a marca sai quando chega uma proposta desse controlador;
  - o relógio só avança sem marcas.
  - A espera não é entrada do diário: a proposta sempre chega na mesma fronteira, então a reexecução continua exata.
- **`move` com `near`** (decisão 1) e **`at_tick`** para o replay.
- **Permissões do NATS revistas** para `perception` e `controller` (as do M2 eram provisórias). O controlador lê só os eventos do seu avatar, com um consumidor filtrado.
- **Salto de tempo fica de fora** (decisão 7): tick a tick, 30 dias são 43.200 ticks, poucos segundos.

## 5. Testes e ferramentas

| Critério | Como |
|---|---|
| **A3 + A10** resistência e economia | `make soak DAYS=30`: NATS, kernel em modo máximo, percepção e controller-runner como processos. Registra tempo real, memória, moedas por dia, desmaios e recusas. No `make check` roda uma versão curta (decisão 3) |
| **A4** determinismo | duas execuções com a mesma seed pelos processos de verdade → mesmo hash canônico |
| **A5** replay | `make replay DAY=N` (decisão 4): reexecuta o dia N a partir do snapshot do começo do dia e do diário de entradas, e compara o hash com o arquivo JSONL. O controlador replay ganha um teste próprio: reproduz uma sessão gravada pelo barramento |
| **A9** posse | teste automatizado: o operador assume como humano, o script passa a ser recusado com `not_in_control`, a posse volta e o script retoma |
| **A11** (prévia) | `make metrics`: lê o arquivo JSONL e calcula as métricas da bíblia §13 (decisão 6), inclusive dias até amadurecer por grupo de canteiros |
| **Percepção** | unidade: projeção a partir de eventos; o instantâneo nunca tem atributo oculto nem dado de evento `internal`; volta da queda sem perder nem repetir |
| **Script** | unidade: cada prioridade da bíblia §11 a partir de instantâneos montados à mão |

## 6. Decisões

| # | Decisão | Recomendação (todas aprovadas) |
|---|---|---|
| 1 | Como o script chega perto de canteiros, poço, baú etc., se o instantâneo não traz o mapa | **`move {near: entity_id}`**: o kernel escolhe o tile vizinho livre mais próximo pelo caminho. Alternativas: o script carrega uma tabela de "pontos de acesso" (acopla o script do gênero ao mapa do cenário), ou o instantâneo ganha o mapa (pesado e genérico demais) |
| 2 | Durabilidade da percepção | **Projeção própria em arquivo + consumidor durável.** A alternativa, reconstruir tudo do stream `WORLD` ao subir, para de funcionar quando o mundo ficar mais velho que a retenção (30 dias reais) |
| 3 | Resistência no `make check` | **2 dias simulados com processos no `make check`** (alguns segundos); os 30 dias ficam no `make soak`, rodado à mão, com os números no diário |
| 4 | Como provar o replay (A5) | **`make replay DAY=N` pelo kernel** (snapshot do início do dia + diário), mais um teste do controlador replay pelo barramento. Só o controlador replay também provaria, mas depende de mais peças funcionando juntas |
| 5 | Prazo de espera no lockstep | **Sem prazo no M3:** o modo máximo é de experimento, e esperar é o certo. A telemetria avisa a cada 10 s de espera. O prazo real com ação reflexa (tempo §6.1) chega com o LLM, na v0.2 |
| 6 | Métricas antes do painel (M7) | **`make metrics` lendo o arquivo JSONL**, com as métricas da bíblia §13 por dia. O mesmo código serve aos testes do A10 e do A11 |
| 7 | Salto de tempo no modo máximo | **Fora do M3.** Tick a tick já basta, e o salto exigiria entrar no diário. Volta se o soak mostrar que precisa |

## 7. Commits previstos

- `move` com `near`, `at_tick` e lockstep no kernel;
- serviço de percepção e permissões revistas;
- controller-runner e fazendeiro-script;
- controlador replay e `make replay`;
- `make metrics`;
- `make soak`, A3, A4, A9 e A10;
- `Procfile` com os quatro processos;
- ADRs e diário.
