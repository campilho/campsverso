# Referências visuais

Primeira proposta de visual 2D da Fazenda do Camps, feita no Claude Design (11/out/2026). Serve de referência para a UI do M4 (layout do painel do operador) e para o renderer do M6 (tiles, sprites e HUD). Não é especificação: a UI desenha o que os eventos dizem e nunca decide nada (escopo §9).

| Tela | Arquivo |
|---|---|
| Operador, manhã: menu de ações no canteiro, recusa `not_adjacent`, linha do tempo | [v0-operador-dia.webp](v0-operador-dia.webp) |
| Operador, noite: avatar dormindo, controles do relógio, métricas do dia | [v0-operador-noite.webp](v0-operador-noite.webp) |

A visão do jogador é a mesma tela, sem o painel da direita.

## Já de acordo com os contratos

- **Mapa:** segue a bíblia §4 (casa, canteiros oeste e leste, poço, quiosque, rio).
- **Relógio:** pausar, avançar 1 tick, 1×, 72× e máximo, com a pausa como estado (ADR-0026).
- **Linha do tempo:** marcada pela visibilidade (`world`, `agent`, `internal`).
- **Métricas da bíblia §13:** colheitas por grupo, moedas, ações recusadas, plantas murchas.
- **Itens e menu:** regador com cargas (atributo `charges`); menu de ações com o motivo de recusa (`canteiro ocupado` = `plot_occupied`).

## A ajustar quando a UI for construída

1. `farm.buyer.collected` não existe. A coleta das 22:00 é `world.item.consumed` (motivo `buyer_collect`), e o pagamento das 06:00 é `farm.buyer.paid`.
2. A energia no sono sobe 12,5 por hora na cama (bíblia §7), não 6.
3. A tela da noite mostra ao mesmo tempo o avatar dormindo na cama e o detalhe "desmaiado às 02:00". O operador veria um ou outro.
4. "Avançar 1 tick" só vale com o relógio pausado (ADR-0026). O botão fica desabilitado fora da pausa.
