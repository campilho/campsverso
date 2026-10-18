# ADR-0057 — Tick antecipado no modo contínuo e andar a 30 tiles por minuto

**Status:** aceita · **Data:** 2026-10-17 · **Marco:** M8 (passo zero)
**Altera:** bíblia §8 (`move`); `kernel-gestao-do-tempo.md` §3.3; ADR-0037 (só a cadência real, não a ordem do tick)

## Contexto

Jogando a 1× (um minuto simulado por minuto real), o usuário clicou para andar e o avatar só partiu na virada do minuto. É o desenho da ADR-0037: propostas de ação são aplicadas na etapa `commands` do próximo tick, e um tick é um minuto simulado. A 72× a espera é de 0,8 s e ninguém nota; a 1× chega a um minuto; nos 6× previstos para o escritório seriam 10 s.

O pedido foi deixar a movimentação "mais em tempo real, independente do modo". Atrelar a velocidade de andar à escala do relógio quebraria o determinismo: dois mundos com a mesma seed divergiriam conforme a velocidade em que alguém assistiu, o replay deixaria de bater e a arena da v0.2 não compararia controladores no mesmo mundo. E a tela não consegue fingir sozinha: mostrar o avatar no destino enquanto o kernel ainda o considera andando faz o próximo clique ser recusado.

## Decisão

1. **Tick antecipado.** No modo contínuo, uma proposta de ação que chega no meio de um tick roda o próximo tick na hora, e o marcapasso desconta esse tick do tempo real que ainda vai passar. A sequência de ticks e o diário de entradas não mudam, então o replay é idêntico; só a cadência real desloca em menos de um tick. Só um antecipado por vez: com a dívida em aberto, o comando seguinte espera o ritmo normal, e a quantidade de ticks por minuto real continua a da escala. Não vale na pausa nem no modo máximo.
2. **Andar passa a 30 tiles por minuto simulado** (era 3), dado do gênero `farm`. A 1× é um tile a cada 2 s, e a fazenda se atravessa num minuto; qualquer trajeto da fazenda cabe num tick. Os 3 tiles por minuto eram um número de jogo calibrado para o 72×, que em tempo real virava um passo de tartaruga.
3. **A tela tem um teto de velocidade de desenho,** 12 tiles por segundo real. A 72×, 30 tiles por tick dariam 36 tiles por segundo, um pulo; acima do teto a tela fica para trás do kernel e o alcança em seguida, inclusive depois de o trajeto terminar. A 1× e a 6× o teto nunca é atingido. É só desenho: o kernel não espera nem adianta nada (escopo §9).

## Consequências

- A linha de base muda: andar fica quase de graça em tempo simulado, o script trabalha mais horas por dia, e os soaks do M8 medem o efeito junto com o das regras novas (acordado −1/h, fome em 100).
- O teste de fumaça do navegador passa a pausar o relógio e avançar um tick por vez para ver a caminhada, porque a 72× ela passa em menos de um segundo.
- Mesmo com as duas mudanças, a 1× regar leva 2 minutos reais e um dia leva 24 horas: é o que tempo real significa, e por isso a fazenda se joga a 72×. Para mundos em tempo real (escritório, estúdio), o caminho é o tick mais curto por mundo (`futuro.md`).
- Nenhum contrato muda: `entity.moved.v1` já leva `tiles_per_tick`.
