# ADR-0082 — A planta e a arte nova do escritório

**Status:** aceita · **Data:** 2026-11-15 · **Marco:** M24
**Revê:** ADR-0077 (a arte LPC no escritório) e a sala da bíblia do escritório (§3) · **Complementa:** ADR-0078 (o escritório); ADR-0080 (a copa e a rotina); ADR-0081 (o tick de 250 ms)

## Contexto

A arte LPC do M23 ficou com uma cara estranha para o usuário. O teste de arte do Claude Design (o pedido em `docs/design/briefing-arte-escritorio.md`) entregou uma arte desenhada em código, na vista de cima em 3/4, com uma paleta só. O usuário pediu ajustes, aprovou o resultado e mudou a planta da sala junto (a prévia em `docs/design/escritorio-arte/escritorio-arte.html`):
- quatro cubículos à esquerda, em duas fileiras, abertos para o sul. O dev usa o de cima à esquerda;
- uma sala de descompressão em cima à direita, com o tapete, a TV com o videogame, o sofá e os pufes;
- a copa embaixo à direita: a lixeira, a máquina de café, a pia com o micro-ondas, a geladeira, o bebedouro e duas mesinhas com as cadeiras de lado;
- o banheiro colado à parede de baixo, à esquerda, com as portas no corredor: para ir a ele, sai-se da sala;
- o quadro dos pedidos, a janela e o relógio na parede do fundo; o vigia de pé no corredor, ao lado da porta.

## Decisão

1. **O mapa lógico segue a planta da prévia,** tile a tile.
   - Dois tipos de tile novos: a divisória (`partition`, não passa) e o tapete (`rug`, passa).
   - As peças novas são entidades do gênero `office`: a máquina de café, a geladeira, o micro-ondas, a lixeira, a cadeira da copa (com o atributo `virada`), o arquivo, a planta, a TV, o sofá, o pufe (com a `cor`) e o bloco do banheiro. As portas do banheiro levam o `lado`.
2. **O banheiro fica fora da sala.** As portas dão para o corredor, e o único lado livre delas é o do corredor: a rotina sai pela porta da sala, vai até a porta do banheiro e volta.
3. **O almoço vira quatro etapas da rotina:** pegar na geladeira (15 s), esquentar no micro-ondas (90 s), comer sentado na cadeira de lado da mesinha até 12:55, e jogar fora (5 s). Os 5 minutos do fim (`lunch_tail_minutes`) são para jogar fora e voltar à mesa. As etapas são ilustrativas, como as pausas (ADR-0080): nenhum item no mundo.
4. **O café sai da máquina, e a água do bebedouro da copa.**
5. **A arte nova substitui a LPC no escritório,** no gênero `office` e no cenário `office_campsverso`. Os créditos passam a ser só do Campsverso. As fazendas seguem com a LPC (ADR-0053).
6. **A bancada sai da sala por enquanto.** Ela volta com os robôs, na parte 4 do M24, num cubículo livre ou numa peça nova.

## Consequências

- **O que a arte ainda não tem fica parado:** usar, beber, comer e as animações da copa. O desenho delas vem depois, sem mudar o mundo.
- **Os testes que conheciam a sala antiga** (a cadeira do dev em (5,7), o balcão da copa, o posto do vigia) passaram para a planta nova.
- **Um soak de um dia** na planta nova: o almoço nas quatro etapas, duas idas ao banheiro pelo corredor, os 4 pedidos do dia entregues e nenhuma recusa.
