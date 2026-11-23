# ADR-0092 — As telas do Claude Design, o gerente Camps e o dev Tiago

**Status:** aceita · **Data:** 2026-11-22 · **Entre o M26 e o M27**
**Complementa:** ADR-0087 (a tela retrô); ADR-0088 (a luz); ADR-0089 (as mãos e a tela da sessão)

## Contexto

Em 22/nov, o Claude Design entregou três pedidos de tela (`docs/design/briefing-tela-2.md`, `-3.md` e `-4.md`):
- o monitor maior, o relógio de 7 segmentos e os retratos;
- o gerente novo e o elenco novo;
- as fichas quadradas e a ficha aberta;
- a tela do dev num terminal de fósforo verde;
- o menu, os comandos e os créditos no padrão da tela;
- o quadro com quatro colunas e o interruptor redesenhado.

No mesmo dia, o usuário pediu mais três coisas:
- **trocar os nomes:** o gerente passa a ser o Camps, e o dev ganha um nome de dev;
- **a devolução maior:** o campo era pequeno, e o comentário era cortado em 280 caracteres sem aviso;
- **a fila da tela:** o passo do quadro esperava o lazer acabar, e um clique limpava a fila sem dizer nada.

O plano está em `docs/planos/as-telas-do-claude-design.md`.

## Decisão

1. **Um bloco sem número entre o M26 e o M27,** com plano e esta ADR, como a tela retrô dentro do M25. O plano macro da v0.4 (ADR-0077) não muda.
2. **O gerente é o Camps,** de blazer (a folha `gerente_blazer`), e o id continua `gerente`: é a cadeira do jogador. O senhor de terno e o Camps de óculos ficam guardados na arte, sem uso no elenco.
3. **O dev é o Tiago,** com a folha `tiago`. A Dandara, a Lívia e o Kenji ficam para os próximos devs e lugares.
4. **O id do dev muda de `camps` para `tiago`.** Com o gerente chamado Camps, o id antigo deixaria a menção e o arquivo do mundo ambíguos.
   - Nenhum contrato muda por isso, e o kernel também não: o elenco é dado do cartucho.
   - O Camps das fazendas é outro avatar, de outro cartucho, e não muda. Ele passa a ser o avatar do humano nos dois mundos.
5. **O escritório vivo vai para um mundo novo,** o `office-campsverso-02`, com o Tiago de memória limpa.
   - O mundo 01 fica inteiro no arquivo.
   - O quadro recomeça no pedido 1, e os ramos ganham o prefixo `dev/tiago/`, para não colidir com os do GitHub. O número vem de um contador do kernel, e continuar no 4 pediria uma opção nova no kernel. O usuário escolheu não mexer nele.
6. **A devolução maior:**
   - fica no papel da ficha aberta, em pauta e tinta vermelha, com um contador;
   - o limite sobe de 280 para 1.000 caracteres, pelo `office.ticket.returned.v2`;
   - o desenho é nosso, no estilo da prancheta.
7. **Seis fases, cada uma inteira no `main`:**
   1. os nomes e o elenco;
   2. o monitor maior;
   3. o quadro;
   4. a tela do dev;
   5. as janelas;
   6. a fila.
8. **A fonte VT323** da tela do dev, pelo `@fontsource/vt323` (OFL 1.1), nos créditos.
9. **O interruptor sem mexer no kernel.**
   - Ele já existe no mundo vivo, e o mundo 02 nasce com ele.
   - Rodar os sistemas do começo da sessão ao retomar um mundo vai para o `futuro.md`: muda o que o replay de um dia retomado vê, e isso merece um plano próprio.
10. **As fitas que levam o nome do dev são regravadas,** por centavos, com o ok do usuário no passo.

## Consequências

- **O kernel e as fazendas não mudam.** O que muda está nos cartuchos do escritório, na tela, na mente do dev e nos testes.
- **Um contrato novo:** o `office.ticket.returned.v2`. A v1 continua para os dias antigos.
- **O comando do escritório vivo muda:** `make escritorio MENTE=tiago_escritorio`, no mundo 02.
- **Os títulos "Pedido 1" a "Pedido 3"** vão se repetir no GitHub, com números de PR e ramos diferentes.

## Adendo: como ficou (22/nov)

As seis fases foram feitas no mesmo dia, cada uma no `main` com o CI verde; o "Como ficou" fase a fase está no plano (§10). O que mudou em relação ao decidido:
- **O kernel e as fazendas seguem sem mudança, com uma exceção no cartucho:** um título de pedido de 65 a 80 caracteres publicava um `entity.spawned.v1` inválido, e o kernel parava. A correção ficou no cartucho do escritório: o nome da ficha sai abreviado até os 64 do contrato, e o título inteiro fica no atributo.
- **As janelas novas (o menu, os comandos e os créditos) valem só com a tela retrô.** As fazendas seguem com as de sempre; o conteúdo dos comandos delas passou a sair da mesma função.
- **O mundo vivo guarda o que nasceu com ele:** no mundo 02, a mesa do dev ainda se chama "Mesa do Camps", porque nasceu antes da correção do nome no mapa.
- **A troca de mundo do escritório vivo** pede guardar o `estado.json` do supervisor com outro nome, para ele instalar o `main` do zero.
