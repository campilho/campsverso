# ADR-0087 — A tela retrô do escritório

**Status:** aceita · **Data:** 2026-11-21 · **Marco:** M25
**Complementa:** ADR-0053 (a tela em Phaser); ADR-0068 (ver e assistir); ADR-0078 (o escritório); ADR-0083 (o escritório vivo e a placa da versão); ADR-0086 (a convocação e os avisos da troca)

## Contexto

A tela do escritório cresceu marco a marco: o quadro dos pedidos, a conversa, o patch, o PR, a convocação e a faixa dos avisos foram entrando na coluna da direita como painéis do mesmo jeito que os da fazenda. Em 21/nov, o Claude Design redesenhou a tela inteira do escritório como um computador retrô, com o monitor da sala, uma barra de pessoas e um quadro de cortiça. O pedido, com os números, as cores e o comportamento, está em `docs/design/briefing-tela.md`; os prints, em `docs/design/escritorio-tela/`; a ordem do trabalho, em `docs/planos/a-tela-retro.md`.

## Decisão

1. **A tela retrô vale só no escritório.** A página monta as peças de sempre (o mapa, a fila, o painel do quadro, o do operador); quando o estado diz que é o escritório, a moldura (`apps/ui/src/retro/`) põe o mapa dentro do monitor e os painéis na coluna da direita, com `body.retro` e o CSS só sob essa classe. A fazenda, a arena e o assistir ficam com a tela de hoje.
2. **A moldura não decide nada.** O que ela mostra sai de funções puras (`retro/model.ts`: a luz, o relógio, os chips), e cada botão chama a ação que a tela já tinha, que vira proposta como antes. Nenhum contrato muda.
3. **A luz da barra de cima nunca é só cor:** verde "online", âmbar "atualizando" (a troca ou a espera do aviso do supervisor) e vermelha "sem conexão" (a conexão fechada ou o mundo sem pulso), sempre com o rótulo no `aria-label` e no `title`.
4. **A troca entre jogador e operador navega** (`?view=`), em vez de trocar a visão na mesma página: as duas assinaturas do gateway são diferentes, e recarregar é o caminho que já existe.
5. **As fontes vêm com a UI,** pelos pacotes `@fontsource` (Pixelify Sans, Inter, JetBrains Mono e Patrick Hand, todas OFL 1.1), em woff2 no build. Elas entram nos créditos da tela. Nenhuma fonte vem de fora em tempo de uso.
6. **Os créditos e o canvas de depuração saem da barra de cima** e vão para o Sobre, aberto pelo ícone.
7. **A arte da parede e dos chips passa pelo `make arte-escritorio`:**
   - a placa da versão numa linha (`placa_versao_linha`, `<commit> <dd/mm>`) substitui a de duas linhas, que sai do cartucho;
   - os dois ícones novos dos chips (`fora` e `vigiar`), que vieram soltos em `escritorio-arte/tela/`, são colados nas casas livres `[6,3]` e `[7,3]` da folha `icones`. Se a folha do Claude Design ocupar essas casas, o pipeline para com erro, e a escolha volta para cá.
8. **A prancheta substitui o painel do pedido** (a fase 2): o novo pedido, a ficha aberta e o aceitar e devolver passam para a cortiça.
9. **Cada fase vai ao `main` inteira e conferida no sandbox.** O escritório vivo troca de versão a cada push com o CI verde; no meio de uma fase, nada vai ao ar. Até a fase 4, a faixa dos avisos vira uma pílula fixa no meio da barra de cima, e os painéis antigos sobre o mapa (a ajuda, a fila, o menu) guardam o fundo escuro de hoje.

## Consequências

- **O escritório tem uma cara própria,** e a fazenda segue igual: os testes da fazenda e da arena no navegador não mudam.
- **São quatro dependências novas na UI**, só de fontes. O build ganha cerca de 1,1 MB de arquivos de fonte (0,5 MB em woff2 e o resto em woff, de reserva), servidos pelo gateway; o navegador só baixa os woff2 dos pesos e alfabetos que a tela usa.
- **A tela passa por um período misto:** a moldura nova com os painéis da direita de hoje, até as fases 2 a 5.
- **A troca de visão recarrega a página.** Ela perde o rascunho que não foi enviado; a fase 2 guarda o rascunho da prancheta no navegador.
- **A folha `icones` do cartucho deixa de ser uma cópia byte a byte da do Claude Design.** O `--check` do pipeline confere que ela continua em dia.
