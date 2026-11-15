# ADR-0079 — O passo de tela e o passo começado

**Status:** aceita · **Data:** 2026-11-15 · **Marco:** M23
**Complementa:** ADR-0078 (o escritório, o andar sem pulo); ADR-0057 (o tick adiantado e o andar); ADR-0072 (a ficha do avatar, o `speed`)

## Contexto

Na primeira partida do usuário no escritório, a 72×, o personagem "flutuava até o destino" e "dava uma enroscada". O dev parecia sumir da sala.

O kernel andava no relógio do mundo: 1,2 tile por segundo simulado, o passo de uma pessoa. A 1× é isso mesmo. A 72× vira 86 tiles por segundo na tela, e o dev cruza a sala num décimo de segundo. Nenhum desenho deixa isso bonito: a ação de andar acaba antes de a animação dar um passo.

A tela do jogador não tinha botões de velocidade no escritório. O escritório vivo anda no relógio de São Paulo, mas o sandbox roda a 72× para ver o dia inteiro.

## Decisão

1. **O passo de tela.**
   - Um cartucho pode declarar o andar em tiles por segundo na tela (`set_screen_tiles_per_second`), em vez de tiles por minuto do mundo.
   - O kernel converte pela escala do momento. O passo por tick é o passo de tela vezes os segundos do tick, dividido pela escala.
   - O escritório anda 4 tiles por segundo na tela. A 1× são 8 tiles num tick de 2 s. A 72× é um tile a cada 9 ticks, e andar até o quadro custa uns 2 minutos do mundo, como nos jogos de fazenda.
   - A fazenda não muda: segue andando no relógio do mundo.
2. **Continua determinístico.**
   - A escala é estado do kernel. Ela muda por comando gravado no diário, vai no snapshot e volta no replay.
   - No modo máximo, vale a última escala, que o relógio guarda.
   - O que muda é que o tempo de andar, no mundo, depende da escala. No escritório isso pesa pouco: os blocos de trabalho são de minutos, e andar é raro.
3. **O passo começado termina.**
   - Antes, um andar trocado no meio de um tile voltava o avatar para o tile de trás. No relógio do mundo isso quase não acontecia. Com o passo de tela, a 72× um tile leva 9 ticks, e a seta segurada troca o destino a cada 7: o avatar não saía do lugar.
   - Agora, quando um andar substitui outro no meio de um passo, o andar novo parte do tile em que o avatar está entrando, no tick em que chega nele.
   - A interrupção marca o avatar nesse tile (`move_interrupted`), para a tela não puxá-lo para trás.
   - Se o destino novo é esse mesmo tile, o kernel aceita e o avatar para ali. Antes, recusava com `already_there`, e o andar antigo seguia.
   - O `depart_tick` do `world.entity.moved.v1` pode vir depois do tick em que a ação foi aceita. O formato do contrato não muda.
4. **A tela.**
   - A animação de andar segue o desenho, e não a ação. Quem se mexe na tela anda, com uma folga de 120 ms entre dois passos do teclado.
   - O sandbox do escritório mostra ao jogador os botões 1×, 6×, 24× e 72×. O escritório vivo (`make escritorio`) não mostra nenhum, porque o gateway dele não aceita o relógio do jogador.
5. **O aviso do almoço.** O dev-script diz "Vou almoçar. Volto à uma." nos dois minutos antes de sair, para o gerente se ele estiver na sala, ou para a sala.

## Consequências

- **O que fica bom:** o andar fica igual a 1×, 6×, 24× e 72×. O sandbox do escritório passa a servir para ver o dia e para mostrar o escritório.
- **O que fica a conferir:** um replay a uma escala diferente da gravada não muda o passo, que vem do trajeto gravado. O replay de um dia num aparelho à parte (o Companion de `docs/design`) vai precisar do mesmo cuidado quando chegar.
- **O que não muda:** os controladores que andam no meio do caminho e trocam de ideia passam a terminar o passo antes de virar. Na fazenda o passo por tick é inteiro, então nada muda lá.
