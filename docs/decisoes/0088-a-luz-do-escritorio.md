# ADR-0088 — A luz do escritório

**Status:** aceita · **Data:** 2026-11-21 · **Marco:** M25
**Complementa:** ADR-0078 (o escritório); ADR-0082 (a arte nova e a luz pela hora); ADR-0086 (a convocação fora do expediente); ADR-0087 (a tela retrô)

## Contexto

A luz da sala era só desenho da tela: o `lights` do `art.json` dizia dia das 6h às 18h, as luminárias das 18h às 21h e escuro depois, com a lanterna do vigia (ADR-0082). Com a convocação (ADR-0086), o gerente e o dev passaram a estar na sala à noite. Em 21/nov, o usuário entrou como o gerente às 22h, a sala estava toda escura, e não havia como acender. Ele pediu ao vigia, que é um script que só faz a ronda e não leu o pedido.

## Decisão

1. **A luz é do mundo.** Um interruptor (`light_switch`) na parede à direita da porta, em (10, 13), com o atributo visível `acesa`. O cenário diz onde ele fica (`light_switch` no `escritorio.yaml`).
2. **O sistema `lights` do gênero** põe o interruptor no mundo quando ele ainda não existe, também num mundo retomado de um snapshot (o escritório vivo volta assim a cada troca), aceso se for a hora do temporizador.
3. **O temporizador do prédio** acende às 18:00 e apaga às 21:00 (`lights` no `office.yaml`, com as chaves `acende` e `apaga`: `on` e `off` o YAML lê como booleanos). Sem ninguém mexer, a sala fica como antes.
4. **As ações `light_on` e `light_off`**, de qualquer papel, ao lado do interruptor. Recusadas longe dele (`not_adjacent`) e quando a luz já está assim. O menu oferece as duas e desabilita a que não faz sentido (`requires` no atributo `acesa`).
5. **O fato novo `campsverso.office.light.switched.v1`**: o interruptor, o estado e quem mexeu. Sem `by`, foi o temporizador.
6. **A tela** desenha a luz pela agenda de dia; à noite, quando o mundo tem um interruptor, ele manda: aceso, as luminárias; apagado, o escuro. Sem interruptor, vale a agenda de antes. O desenho do interruptor (aceso e apagado) é feito em código pelo `make arte-escritorio`.
7. **O vigia atende:**
   - quando falam com ele sobre a luz (a fala dirigida a ele, ou que diz "vigia"), ele responde e vai ao interruptor;
   - na ronda, apaga a sala vazia.
8. **O dev vê o interruptor, mas a mente dele não ganha a ferramenta agora** (o `futuro.md`).

## Consequências

- **O gerente acende a luz à noite** pelo menu do interruptor, ou pedindo ao vigia. A conversa conta quem acendeu.
- **Um tipo de evento a mais** no domínio `office` (86 eventos).
- **O mundo ganha uma entidade e um sistema** que rodam também nos mundos já criados. A foto do dev não mudou, e a fita do escritório continua valendo.
- **O vigia passa a ler o que ouve.** Isso fica restrito à luz e às falas dirigidas a ele, para que o dev, ao falar de "luz" com o gerente, não o mande ao interruptor.
