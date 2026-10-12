# ADR-0048 — O ciclo de decisão do M3: foto com o pedido, lockstep, replay e ids derivados

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M3
**Complementa:** ADR-0021, ADR-0028, ADR-0047 · **Altera:** catálogo §3.7 (`perception.delivered`)

## Contexto

Ao ligar kernel, percepção e controladores, surgiram escolhas que o plano não detalhava, e três defeitos que só apareceram com o ciclo inteiro rodando.

## Decisão

1. **A foto já diz de quem é a vez.** `perception.delivered.v1` ganha o campo opcional `decision` (`reason` e `controller`). Mudança compatível: só um campo opcional novo.
   - Antes, o runner juntava dois eventos: o pedido de decisão e a foto.
   - No barramento em memória, a foto chegava antes do pedido, e o script respondia mesmo com o humano no controle (achado pelo teste do A9).
   - Depois de uma queda, o pedido podia já ter sido confirmado e a foto não. Com tudo na foto, basta um evento.
2. **Lockstep pela dívida de decisão:**
   - o kernel marca o avatar quando pede uma decisão a um controlador script ou replay;
   - a marca sai quando chega uma proposta desse controlador, ou quando a posse muda;
   - no modo máximo, o relógio só anda sem marcas. A marca entra no snapshot.
3. **Replay com agenda.** No primeiro pedido de decisão endereçado a ele, o controlador replay manda todas as propostas gravadas, cada uma com `at_tick` (o tick em que valeu na sessão original). O kernel guarda e aplica cada uma no seu tick, então reproduz até uma sessão humana do modo contínuo.
   - Enquanto houver proposta agendada, o avatar não deve decisão.
   - `at_tick` no passado é recusado com `too_late`; de outro controlador, com `unsupported`.
   - As propostas e os ticks saem do arquivo JSONL: cada comando tem um fato do kernel causado por ele.
4. **Ids derivados para reações** (`IdGenerator.derive`).
   - A foto tem um UUIDv7 derivado do id do pedido, e o comando do script, um derivado do id da foto.
   - Se um serviço cair depois de publicar e antes de confirmar, a reação repetida tem o mesmo id: o JetStream a deduplica, e o kernel a ignora pelo diário.
5. **Ler dois streams em ordem.** O consumidor durável ganha `caught_up()`: espera tudo o que já está no stream ser entregue e confirmado. A percepção alcança `world` antes de montar a foto de um pedido de decisão.
6. **Controlador inicial por mundo.** `config/worlds/*.yaml` aceita `controllers: {camps: {type: replay, id: ...}}` para um mundo novo. O padrão do cartucho continua sendo o destino do `release`.
7. **Hash canônico sem o `sha256` do snapshot** (estende a ADR-0021).
   - O estado guarda os ids dos comandos das ações em curso, que são UUIDv7 com relógio e acaso; o `sha256` muda entre execuções com controlador, mesmo com fatos idênticos.
   - A recuperação e o replay (A5) continuam conferindo o `sha256` exato, porque reexecutam com os ids do diário.
8. **Permissões do NATS explícitas para percepção e controlador.**
   - A percepção só usa a API de consumidores de `WORLD` e `AGENT`. `$JS.API.>` abriria `internal` por outras portas: buscar mensagem por número ou puxar do consumidor do arquivador.
   - O controlador só cria consumidores filtrados em `agent.camps.>`. Com vários agentes (v0.2), um usuário por agente.
9. **Interpretação da bíblia §11 no script:**
   - energia abaixo de 10 só leva a dormir depois das 20:00, porque antes o kernel recusa;
   - depois de 01:30, longe da cama, dorme no chão;
   - se uma proposta foi recusada e o script repetiria a mesma, o runner espera 15 minutos em vez disso.
10. **Métricas** em `campsverso_tools.metrics`: lê só o arquivo JSONL. O dia agrícola vem do tick, o que vale para mundos que começam na hora em que o dia vira.

## Defeitos achados e corrigidos

- **Consumidor ocioso morria em silêncio:** o `fetch` do nats-py às vezes levanta o `TimeoutError` comum, e não o dele. O laço agora sobrevive a qualquer erro de busca; só erro do handler derruba.
- **Teste A7 intermitente:** esperava "algum seq ≥ último", mas um evento anterior podia estar a caminho por outro stream. Agora espera todos os seq até o último. (Não explica os CIs vermelhos do M1: o A7 só existe desde o M2.)
- **Script respondendo fora da vez:** ver o item 1.

## Consequências

- O controlador da v0.2 (LLM) recebe a mesma foto, com o motivo do pedido: não precisa de mais nada para decidir.
- O replay de uma sessão humana fica possível desde já, mesmo que a UI só chegue no M4.
