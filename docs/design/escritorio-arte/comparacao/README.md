# O escritório com a arte nova, na tela de verdade

Capturas do sandbox do escritório (`office-campsverso-demo`), com a arte do Claude Design no lugar da LPC (ADR-0082) e o mapa lógico na planta nova. O mesmo mundo, numa segunda-feira, em dois momentos (`instante.txt`):

- `sala-dia.png` e `mesa-dev.png` (10:25): o gerente escreveu um pedido no quadro; o dev digita sentado no cubículo de cima à esquerda, de costas, com o encosto da cadeira na frente dele e o código rolando na tela do monitor.
- `sala-almoco.png` e `copa-almoco.png` (12:11): o dev pegou o almoço na geladeira, esquentou no micro-ondas e almoça sentado de lado na cadeira da copa, virado para a mesinha.

Como refazer, com um sandbox do escritório no ar:

    NODE_PATH=apps/ui/node_modules node docs/design/escritorio-arte/ferramentas/capturar-escritorio.cjs \
      http://127.0.0.1:8765 docs/design/escritorio-arte/comparacao

O que a arte ainda não tem: usar, beber e comer (o dev fica parado nessas ações); o sentado do gerente e do vigia (na cadeira, ficam de pé); as fichas no quadro dos pedidos, pelo estado de cada pedido; a janela de noite no mapa visual.
