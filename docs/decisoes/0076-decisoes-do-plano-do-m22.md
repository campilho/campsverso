# ADR-0076 — Decisões do plano do M22 (fechamento da v0.3)

**Status:** aceita · **Data:** 2026-11-14 · **Marco:** M22
**Complementa:** `docs/planos/m22-o-fechamento-da-v0.3.md`; plano macro da v0.3; ADR-0065 (o fechamento da v0.2); ADR-0074 (o M21)

## Contexto

A v0.3 terminou o M21 com a terceira arena rodada e o lacre do mapa d aberto. Faltava conferir os "pronto quando" de cada marco no código que vira `v0.3.0`, responder à pergunta da versão com os números e publicar, como o M7 e o M15 fizeram.

Em 13/nov, o usuário perguntou se o Fable, o melhor do M21, rodou pelo Claude Code e aproveitou o harness de lá, e se o SDK do Claude Code é muito mais efetivo que um modelo pela OpenRouter. A resposta:
- todos rodaram no mesmo harness, a mente do Campsverso, com o mesmo prompt, as mesmas ferramentas e o mesmo esforço;
- os Claude foram pela API da Anthropic, e o Astra e o Gemini pela OpenRouter;
- ninguém rodou pelo Claude Code.

Procurando a resposta, as fitas mostraram um erro de medição nosso. O GPT-6 Astra respondeu vazio em 876 de 1.874 chamadas do ano (47%), sempre logo depois do resultado de uma ação. A mente transforma a resposta sem ação em esperar 15 minutos, então o avatar ficou quase metade do dia parado, e as respostas vazias custaram 43% do gasto dele. Os Claude responderam sem ação de 1 a 55 vezes por corrida. O piloto de 2 dias já mostrava o problema, mas a saúde dos pilotos olhava só o custo.

## Decisão

As decisões do plano, aprovadas pelo usuário em 14/nov como recomendado:

1. **Os critérios C1 a C8 são o aceite da v0.3.** C1 a C6 são os "pronto quando" dos marcos M16 a M21; C7 cobre os princípios, e C8 o custo dentro do teto de US$ 300 (ADR-0074, decisão 21). O documento é o `docs/aceite-v0.3.md`, com a resposta à pergunta da versão no fim.
2. **O conserto do Astra é de graça e vem primeiro:**
   - na rota da OpenRouter, a ferramenta é obrigatória (`tool_choice: required`) nos modelos de fora da Anthropic, porque toda chamada da plataforma espera uma;
   - o Claude com raciocínio não aceita a ferramenta forçada, então fica com `auto`, e as fitas do Claude não mudam;
   - o relatório da arena ganha a linha "respostas sem ação", e o progresso de cada dia a conta, para que a saúde dos pilotos pare acima de 5%.
3. **O Astra consertado roda de novo:** um piloto de 2 dias e depois 14 dias, no mapa d e com a mesma seed, ao lado dos outros no corte do dia 14. Cada passo pago espera o ok do usuário.
4. **O Haiku pela OpenRouter, 2 dias,** contra o Haiku direto, para separar o efeito do cano do efeito da tradução.
5. **A evidência vem do código final:**
   - os soaks nos três mundos;
   - o `make check` com `TZ=UTC` e o `make ui-e2e`;
   - duas chamadas reais, uma pela Anthropic e outra pela OpenRouter.
6. **O print da versão** é a Morada do Sol na tela do jogador, e o modo de assistir entra como segunda imagem nas notas.
7. **"A v0.3 em números"** no índice do diário, com o tempo e os tokens do Claude Code por marco e o custo de API de cada marco.
8. **As 19 ideias da §7 do plano** vão para o `futuro.md` com destino v0.4, sem ser feitas aqui. A rodada 3 (mais seeds e o segundo ano com memória) também vai para a v0.4, como o usuário decidiu em 13/nov.
9. **A tag `v0.3.0` e a Release no GitHub,** com as notas em `docs/versoes/v0.3.0.md`, depois do ok do usuário para o push.

## Consequências

- **O Astra do M21 fica no relatório como rodou,** com a linha nova mostrando as respostas sem ação. O plano do M21 e o diário de 12/nov ganham uma nota: os 3% medem o nosso harness, e não o modelo.
- **A pergunta do usuário fica em duas partes.**
  - Se o cano da OpenRouter, sozinho, muda alguma coisa: o piloto do Haiku (decisão 4) responde.
  - Se o harness de cada laboratório rende mais que o nosso: só a bancada dos harnesses, o primeiro marco da v0.4 (ADR-0074, decisão 30), responde.
- **Um provedor novo passa por uma prova de conformidade** antes de entrar numa rodada: as respostas sem ação, as recusas e os formatos, medidos em dois dias. Fica como ideia para a v0.4, na lista do plano.
