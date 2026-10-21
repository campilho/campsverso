# ADR-0064 — A v0.3 é a fazenda sofisticada; o escritório vai para a v0.4

**Status:** aceita · **Data:** 2026-10-20 · **Marco:** fechamento do M14
**Substitui:** a ordem das versões da ADR-0055 (a direção do escritório continua valendo, uma versão depois)
**Complementa:** `docs/planos/analise-ordem-v0.3-v0.5.md`; `docs/planos/v0.3-macro.md`; ADR-0062, ADR-0063; escopo §2

## Contexto

A segunda rodada da arena (M14, ADR-0063) mostrou que, num mundo em que as escolhas custam, os modelos se separam: o Opus terminou com cinco vezes as moedas do fazendeiro-script 2, o Haiku quebrou. E deixou uma pergunta aberta: ninguém cavou na faixa do rio, porque o mundo não pedia exploração e, com o teto de 32 canteiros e nenhum jeito de desfazer um canteiro, uma descoberta tardia não mudaria nada. O usuário decidiu, no fechamento do M14, que a próxima versão continua na fazenda, mais sofisticada, com melhor jogabilidade e um script mais forte, e pediu a análise da ordem entre a fazenda, o escritório e o estúdio do podcast.

## Decisão

1. **A v0.3 é a fazenda sofisticada** (plano macro em `docs/planos/v0.3-macro.md`).
2. **A v0.4 é o escritório que constrói a si mesmo**, com tudo o que a ADR-0055 decidiu sobre ele (a mente no mundo e as mãos na oficina, o portão humano, a governança, o primeiro agente).
3. **A v0.5 é o estúdio do podcast**, sobre a porta de efeitos externos do escritório; o mundo com memória completa e a camada social anda para a v0.6 em diante.
4. **A fazenda constrói de propósito o que os três mundos pedem**: vários avatares fora do kernel, a primitiva de remover entidade, o replay na tela, pedidos de fora com prazo (as encomendas, o análogo dos tickets), rótulos de eventos e, se a memória pedir, relevância. A v0.4 começa pelo que é só dela: a porta externa, o tempo novo e o supervisor de versões.
5. **A v0.3 tem corte**: um número fechado de marcos, aprovado no plano macro; o que não couber vai para uma "fazenda 4" no `futuro.md`.

## Consequências

- O escopo §2, o README, o plano macro da v0.2 e a ideia do escritório registram a nova ordem; o `futuro.md` marca os itens do escritório como da v0.4.
- O M15 continua sendo o fechamento da v0.2, com a tag `v0.2.0`; a v0.3 começa depois, pelo plano macro com decisões numeradas.
- O escritório chega numa base mais pronta e com uma arena de famílias de modelos já medida; o custo é esperar uma versão pelo mundo que se constrói.
