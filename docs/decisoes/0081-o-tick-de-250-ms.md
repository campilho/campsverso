# ADR-0081 — O tick de 250 ms no escritório

**Status:** aceita · **Data:** 2026-11-15 · **Marco:** M24
**Revê:** ADR-0078, decisão 1 (o tick de 2 s) · **Complementa:** ADR-0079 (o passo de tela); ADR-0057 (o tick adiantado)

## Contexto

O usuário jogou o escritório como o gerente nas quatro velocidades. A 24× e a 72×, o andar ficou bom. A 1× e a 6×, não:
- o clique demorava a fazer o gerente andar;
- com as setas, ele ia e voltava.

**A causa é o tick.** O kernel aplica um comando na virada do tick, e o tick do escritório era de 2 s do mundo:
- a 72×, isso dava 28 ms de tela; a 1×, 2 s inteiros;
- o clique esperava até 2 s, menos o primeiro, que sai na hora pelo tick adiantado;
- ao soltar a seta, a parada chegava ao kernel até 2 s depois, com o avatar já até 8 tiles além do ponto, e ele voltava;
- a tela ainda andava com o teclado a 6 tiles por segundo, contra os 4 do passo de tela, e alcançava o kernel aos trancos.

Foram vistas três saídas:
- o tick menor;
- a previsão na tela, com o andar ancorado no instante do comando;
- um paliativo só na tela.

A previsão é bem mais frágil (acertar a tela quando o kernel recusa ou alguém bloqueia). O paliativo deixa o clique esperando até 2 s. O usuário escolheu o tick menor.

## Decisão

1. **O tick do escritório passa a 250 ms.** A 1×, o kernel aceita comandos 4 vezes por segundo. O clique espera no máximo 250 ms, e o avatar anda um tile por tick.
2. **O kernel conta o tempo em milissegundos inteiros:**
   - o cartucho declara `tick_seconds` em segundos, e uma fração vale (`0.25`);
   - o calendário guarda `tick_ms`, que precisa dividir um minuto;
   - as contas da fazenda dão o mesmo de antes.
3. **O `session.started` ganha uma v2,** com `tick_ms` no lugar de `tick_seconds`:
   - o kernel publica a v2 só quando o tick não cabe em segundos inteiros;
   - as fazendas seguem no v1, byte a byte, e as fitas e os replays delas não mudam;
   - quem lê a sessão aceita as duas versões: a projeção, a guarda, o gateway no modo de assistir e as ferramentas de métricas.
4. **O passo de tela vai na sessão** (`screen_tiles_per_second`, opcional nas duas versões). Com ele, a tela anda com o teclado no ritmo do kernel.
5. **Soltar a seta para onde o kernel vai estar no tick seguinte,** quando a parada chegar a ele, e não onde ele está agora.
6. **A sessão da tela** (`realtime/welcome.v1`) ganha `tick_ms` e o passo de tela, e o `tick_seconds` deixa de ser obrigatório. Essa mensagem vai só do gateway à tela, que saem do mesmo commit.
7. **Quem está andando e pede o tile em que está para ali,** também na virada exata de um tile. Com um tile por tick, a 1× o avatar está sempre na virada, e o kernel recusava a parada (`already_there`), deixando o andar velho seguir.
8. **O desenho não passa da parada que a seta mandou,** até o kernel responder. Quando um trajeto novo começa atrás do desenho, no mesmo caminho, o desenho espera o kernel em vez de voltar.
9. **A fala não interrompe o humano** (revê a decisão 5 da ADR-0080). Ela interrompe só quem decide por pedido de decisão, o script e a mente. O humano lê a fala na tela, e o aviso do dev cancelava o aceite que o gerente acabava de começar.

## Consequências

- **O andar responde a 1×:** o clique anda em menos de 800 ms, e a seta solta para sem voltar. Ele ainda anda uns 2 tiles depois de soltar (a 72×, um): a parada chega ao kernel no tick seguinte, depois da rede.
- **O escritório tem 8 vezes mais ticks:** 345.600 por dia. O custo está nas decisões dos scripts, e não nos ticks (o adendo da ADR-0078), mas os testes do escritório e o soak ficam mais lentos.
- **Os horários de 1 s** (o `simtime` do envelope) se repetem em 4 ticks seguidos. O tick é a ordem; o `simtime` é só para ler.
- **Um mundo com tick quebrado** (700 ms, que não divide o minuto, ou meio milissegundo) é recusado ao subir.
