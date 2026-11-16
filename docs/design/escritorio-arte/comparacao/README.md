# O escritório com a arte nova, na tela de verdade

Capturas dos sandboxes do escritório com a arte do Claude Design (ADR-0082): as folhas do commit 9e923ed, com as animações novas, o quadro em três colunas, a luz da noite, a janela e o relógio que seguem a hora do mundo. Os instantes de cada uma estão em `instante.txt`.

- `sala-dia.png` e `quadro-fichas.png` (09:50): o gerente escreveu três pedidos, um de cada tamanho. O quadro pendura uma ficha por pedido, na coluna do estado dele: as fichas amarela (M) e vermelha (G) em "a fazer" e a verde (P) em "fazendo". O dev digita no cubículo de cima à esquerda.
- `sala-almoco.png` e `copa-almoco.png` (12:10): o dev almoça sentado de lado na cadeira da copa, com a animação de comer, e a marmita aberta na mesinha. No quadro, há uma ficha em cada coluna: o pedido 1 entregue, o 2 sendo feito e o 3 a fazer.
- `sala-luminarias.png` (20:10): das 18:00 às 21:00, as luminárias acesas, com poças de luz de borda em xadrez e penumbra fora delas. O corredor, a face do banheiro e a janela ficam sempre acesos. A janela mostra a cidade de noite, e o relógio marca 8 horas.
- `sala-noite-vigia.png` (21:05): depois das 21:00 a sala fica escura, e só a lanterna do vigia ilumina, em anéis com as bordas em xadrez.
- `sofa-jogando.png`: o gerente de pé no tapete, logo abaixo do sofá, aparece sentado nele com o encosto por cima, e a TV mostra o jogo. **A cena é sintética.** O kernel deste ramo ainda não tem as ações `tv` e `videogame`, então a página da captura recebeu, além das mensagens do gateway, um patch com o gerente jogando.
- `mesa-dev.png` é da captura anterior (10:25), antes das folhas novas.

## Como refazer

Com um sandbox do escritório no ar, rode a partir da raiz do repositório:

    node docs/design/escritorio-arte/ferramentas/capturar-arte-nova.cjs dia http://127.0.0.1:8792 docs/design/escritorio-arte/comparacao

Para a noite, use um mundo que comece perto das 18:00. Pode ser uma cópia do `office-campsverso-demo` com `start` às 17:58, fora do repositório. Depois, troque `dia` por `noite`. Para o sofá, troque por `sofa`.

## O que ainda falta

- As telas acesas, que a prévia deixa claras no escuro.
- O rótulo das ações `tv` e `videogame` no locale: hoje a tela mostra o id.
- O atributo `carregando` no kernel. Com ele, o dev anda com a marmita entre a geladeira e o lixo, e a tela já desenha a animação de carregar.
