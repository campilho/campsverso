# ADR-0053 — Decisões do plano do M6 (renderer Phaser)

**Status:** aceita · **Data:** 2026-10-12 · **Marco:** M6
**Complementa:** `docs/planos/m6-renderer-phaser.md`; escopo §6 e §7; ADR-0031, ADR-0032, ADR-0050, ADR-0051

## Decisão

As decisões do plano, aprovadas pelo usuário:

1. **Phaser 4, na 4.2.1,** a versão estável atual, como pede o CLAUDE.md. A pesquisa de componentes falava do Phaser 3 porque o 4 ainda não existia. O 4.0 saiu em abril de 2026, e a série 3 terminou na 3.90, de maio de 2025.
2. **A arte mora no cartucho, em camadas, como os dados (ADR-0031).**
   - O gênero `farm` traz o que serve a qualquer fazenda; o cenário `farm_camps` traz o Camps e o mapa visual.
   - Um manifesto por camada diz como desenhar cada tipo de tile, cada `kind` (com variações por atributo) e as animações do avatar. O gateway serve a arte; a tela junta as camadas e não sabe o que é uma fazenda.
   - Para explorar reuso no futuro: cartuchos só de arte, genéricos e sem mapa.
3. **Arte LPC, em 32 px.**
   - O usuário monta o Camps no gerador de personagens LPC.
   - Terreno, construções e culturas vêm de pacotes LPC do OpenGameArt; cada download é aprovado antes, com arquivo, origem, tamanho e licença.
   - Cada pasta de arte tem o seu `CREDITS.csv`, e a tela tem um link "Créditos". O código continua MIT; o "compartilha igual" vale só para a arte.
4. **Mapa visual num arquivo à parte.**
   - O mapa lógico continua a verdade do kernel.
   - O visual é feito a partir dele e ajustado a pedido do usuário. O kernel nunca o lê, e um teste confere a coerência entre os dois.
   - Sem editor por enquanto.
5. **Dia, noite e chuva simples:** uma camada escura pela fase do dia e gotas na chuva.
6. **O canvas de depuração continua,** em `?render=debug`. O Phaser é o padrão.
7. **Retrato:** a cabeça recortada do sprite, com um selo de estado. É uma entrada do manifesto, para depois virar um retrato próprio de fazendeiro.
8. **Playwright:**
   - um teste de fumaça (`make ui-e2e`), principalmente para o CI, que baixa o Chromium;
   - na máquina local, ele usa o Chrome instalado;
   - no dia a dia, a tela é conferida no navegador embutido do app.

## Consequências

- O gateway ganha a rota `/content/art/...` e a configuração das pastas de arte, na ordem das camadas.
- O CI ganha um passo com navegador. O `make check` local não muda.
- A arte entra no git com os créditos. Um pacote sem licença clara não entra.
- A ADR-0050 dizia "sem Playwright" no M4; no M6, ele entra só como teste de fumaça.
