# ADR-0065 — Decisões do plano do M15 (fechamento da v0.2)

**Status:** aceita · **Data:** 2026-10-21 · **Marco:** M15
**Complementa:** `docs/planos/m15-fechamento.md`; plano macro da v0.2; ADR-0054 (o fechamento da v0.1); ADR-0064

## Contexto

A v0.2 terminou o M14 com as duas arenas rodadas e a ordem das próximas versões decidida (ADR-0064). Faltava conferir os "pronto quando" de cada marco no código que vira `v0.2.0`, responder à pergunta da versão com os números e publicar, como o M7 fez com a v0.1.

## Decisão

As decisões do plano, aprovadas pelo usuário:

1. **Os critérios B1 a B8** são o aceite da v0.2. Cada um é o "pronto quando" de um marco (M8 a M14), e o B8 cobre os princípios: arquitetura, contratos, determinismo e replay nos dois mundos, e a regra oculta fora do manual e do catálogo. O documento é o `docs/aceite-v0.2.md`, com a resposta à pergunta da versão no fim.
2. **A evidência vem do código final.** São um soak de 30 dias em cada mundo, o `make check` com `TZ=UTC`, o `make ui-e2e` nos dois mundos e uma chamada real pelo `make llm-smoke`. As arenas não rodam de novo: os relatórios do M12 e do M14 são a evidência delas.
3. **O `futuro.md` revisto:** sai o que a v0.2 fez, e cada item que fica ganha o destino da lista do plano macro da v0.3.
4. **"A v0.2 em números"** no índice do diário, com o tempo e os tokens do Claude Code por marco e o custo de API de cada marco.
5. **A tag `v0.2.0` e a Release no GitHub,** com as notas em `docs/versoes/v0.2.0.md`, depois do ok do usuário para o push.
6. **As vinte decisões da v0.3 não são aprovadas agora.** O usuário aprovou a linha do plano macro da v0.3 e prefere revisar as decisões em detalhe quando a v0.3 começar. Aprovadas, elas viram a ADR-0066.

## Consequências

- O `make llm-smoke` passa a gravar numa fita nova a cada execução. Com a fita padrão, o pedido repetido voltava dela sem chamar a API, e a fumaça deixava de provar o caminho real.
- O CHANGELOG dos contratos ganha as seções `v0.2.0` (M8 a M13) e `v0.1.0` (M2 a M7, mais a primeira versão como M0). As seções do M2 ao M7 tinham ficado como "Não publicado" na tag da v0.1.
- Os números de tempo e tokens de M2 e M3 ficam como estão, com a ressalva no diário. A causa provável é a compactação da sessão, a mesma do M10+M11, que reescreve a transcrição.
