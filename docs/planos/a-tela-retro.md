# Plano: a tela retrô do escritório

A tela do escritório redesenhada no Claude Design em 21/11/2026. O pedido inteiro, com os números, as cores e o comportamento, está em [`docs/design/briefing-tela.md`](../design/briefing-tela.md), e os prints em [`docs/design/escritorio-tela/`](../design/escritorio-tela/). Este plano só diz em que ordem fazer, o que decidir antes e como conferir.

**O que não muda:**
- a tela desenha o que os eventos dizem e não decide nada;
- nenhum contrato novo;
- a fazenda, a arena e o assistir ficam com a tela de hoje.

## 1. As decisões antes do código

1. **As fontes vêm junto com a UI,** pelos pacotes `@fontsource` (Pixelify Sans, Inter, JetBrains Mono e Patrick Hand), em woff2. São quatro dependências novas, baixadas uma vez pelo `pnpm`. As quatro são OFL e entram nos créditos.
2. **Uma ADR curta** registra:
   - a tela retrô;
   - a troca de visão que navega;
   - as fontes na UI;
   - a prancheta no lugar do painel do pedido.
3. **O que vai ao ar:** o escritório vivo troca de versão a cada push com o CI verde, então cada fase só vai ao `main` inteira e conferida no sandbox. No meio de uma fase, nada vai ao ar.

## 2. As fases

Cada fase é um ou mais commits, com os testes de unidade, a conferência no navegador (no sandbox, na porta 8790) e os prints comparados com os do Claude Design.

1. **A moldura:**
   - os tokens, as fontes e o fundo;
   - a barra de cima: o ícone, o nome, a luz e a troca de visão;
   - o monitor com a sala, a varredura e o rodapé;
   - a barra de baixo: o relógio, os chips das pessoas e os comandos;
   - o Sobre, para onde vão os créditos e o canvas de depuração.
   - Os dois ícones novos de chip entram na folha `icones.png` (`make arte-escritorio`), e a placa da parede passa a ser a de uma linha.
2. **O quadro e a prancheta:**
   - as abas e as fichas na cortiça;
   - a prancheta do novo pedido, com o rascunho e a ficha fantasma;
   - a ficha aberta em leitura, com aceitar, devolver e ver o patch.
   - O cartão "Novo pedido" e os `<details>` de hoje saem.
3. **A conversa:** as falas e as linhas do sistema, as menções com `@` que viram o `to` do `say`, e o aumentar e diminuir. O cartão "Falar" sai.
4. **As mensagens do sistema:**
   - o `kind` no `bannerOf`;
   - o modal que trava a tela na troca e na queda;
   - os avisos de canto.
   - A faixa de hoje sai.
5. **O operador:** a gaveta de vidro com as seções do painel de hoje e a linha do tempo.
6. **Tablet e celular:**
   - os três arranjos;
   - no celular, a câmera que segue o gerente com o minimapa, as abas Quadro, Conversa e Pessoas e a barra de ação.

## 3. Como conferir

- **Os testes de unidade** do §9 do briefing:
  - a menção que vira `to`;
  - a ação curta e o ícone de cada chip;
  - as abas;
  - a ficha fantasma;
  - a cor da luz;
  - o `kind`.
- **O `make ui-e2e`:** o teste do escritório de hoje adaptado à tela nova, e mais os seis passos do §9.
- **Os prints** em 1456 × 816, 820 × 1180 e 402 × 874, comparados com os da pasta.
- **Em cada fase:** o `make check` e o `make ui-e2e`.

## 4. Custo

Nada de API. O trabalho é todo de tela, do tamanho de um marco médio, em várias sessões.
