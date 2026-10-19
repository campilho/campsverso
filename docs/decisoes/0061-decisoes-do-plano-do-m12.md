# ADR-0061 — Decisões do plano do M12 (a arena)

**Status:** aceita · **Data:** 2026-10-19 · **Marco:** M12
**Complementa:** `docs/planos/m12-arena.md`; `docs/planos/v0.2-macro.md` (decisão 3, o lockstep com o LLM); tempo §6; pesquisa §13; ADR-0055, ADR-0057, ADR-0058, ADR-0059, ADR-0060
**Altera:** o plano macro no M12 (sem o segundo modelo e sem o humano na tabela; a arena é script × Haiku, com e sem memória) e a tarefa "OpenRouter no M12" do `futuro.md` (vai para a v0.3)

## Decisão

As decisões do plano, aprovadas pelo usuário em 19/out/2026:

1. **A arena roda em processo,** sobre o `make corrida` do M11: kernel, percepção, mente, medidor e guarda no mesmo processo, com o barramento em memória entregando e esperando cada resposta. O mundo espera o modelo por construção, sem tocar no kernel, no modo máximo nem no princípio 7 (a ADR-0057 fica como está). Os 7 dias a 72× do M10 e do M11 ficam como demonstração ao vivo; o experimento é em processo. A decisão 3 do plano macro ("lockstep com o LLM") fica respondida assim.
2. **Mesmo mundo e mesma seed para todos** (`farm-camps-01`, seed 20261010), e três seeds a mais para o Haiku com memória, o controlador principal, para ver a variância entre corridas sem gastar mais que uns dólares.
3. **Quem corre, por 30 dias:** o script da bíblia §11; o Haiku 5.5 sem memória (o M10); o Haiku 5.5 com memória (o M11) em quatro seeds; e o Haiku 5.5 com memória sem a regra R-001, como controle. **O Sonnet fica de fora**, por decisão do usuário: o mundo é simples demais para a diferença entre modelos aparecer, e a comparação entre modelos (Sonnet e Opus, por menos dias) fica para uma segunda rodada, numa fazenda mais rica, proposta para o M13 (ver "Consequências"). O humano entra como referência qualitativa, não na tabela.
4. **A tabela da bíblia §13 lado a lado,** por corrida, nos totais de 30 dias: colheitas por grupo, dias até amadurecer, moedas ao fim, recusas por motivo, murchas, pico de fome, desmaios; mais chamadas por dia, custo por dia e latência mediana; e, para quem tem memória, as crenças ao fim (quantas, e as três mais confiantes).
5. **"Descobriu o leste" pelo dado da memória do agente,** por pedido do usuário: para cada corrida com memória, quando o agente escreveu pela primeira vez sobre o leste (a primeira anotação e a primeira crença, com dia e hora) e como manteve isso ao longo dos dias (a trajetória da confiança de cada crença sobre o leste a cada reflexão: formada, confirmada, enfraquecida ou retirada, com o enunciado e a confiança ao fim). O comportamento (colheitas e plantios no leste a partir do dia 4) fica como sinal secundário, para quem não tem memória, e a corrida sem a regra é o controle: se a crença e o comportamento só aparecem com a regra ligada, o agente descobriu.
6. **`make arena-report`** lê as corridas de `data/arena/<data-hora>/` e escreve `docs/arena/AAAA-MM-DD.md` com as tabelas, as moedas por dia em texto e os caminhos das fitas. É o artefato da v0.2 para o fechamento e para publicar.
7. **Langfuse e OpenTelemetry GenAI adiados** para a versão em nuvem: o que a arena precisa já está nos eventos `llm.call.*`, nas fitas e nos resumos das corridas.
8. **OpenRouter fora do M12,** por decisão do usuário: GPT e Gemini não entram na arena da v0.2; o segundo adaptador fica para o futuro, talvez na v0.3.
9. **A arena e o relatório são ferramentas de desenvolvimento,** testadas com corridas sintéticas (resumos e arquivos pequenos escritos pelo teste) e com o script em processo; o CI nunca chama a API.

## Consequências

- `campsverso_testkit.arena` compõe as corridas sobre o `make corrida` (controlador, memória, regra, seed, dias) e grava cada uma em `data/arena/<data-hora>/<corrida>/`; `campsverso_tools.arena` calcula os sinais do leste a partir do arquivo de cada corrida e escreve o relatório. `make arena` e `make arena-report` entram no `Makefile`; `docs/arena/` guarda os relatórios.
- As métricas ganham os plantios por grupo e por dia (`metrics.py`), para o sinal secundário do leste; a tabela da bíblia não muda.
- Custo estimado da arena inteira: uns US$ 5 no Haiku (seis corridas de 30 dias com modelo, a uns US$ 0,02 a 0,03 por dia), em umas 6 horas de relógio em sequência.
- **Proposta do usuário, a decidir à noite de 19/out:** depois da arena, uma segunda rodada numa fazenda mais rica (mais culturas com custo-benefício bom e ruim, mais canteiros do que o avatar consegue cuidar, ferramentas caras que exigem escolha), para trazer o Sonnet e o Opus por menos dias e ver se decisões mais complexas separam os modelos. Se aprovada, o M13 vira "a fazenda mais rica e a segunda rodada" e o fechamento da v0.2 passa a ser o M14; a proposta está em `docs/planos/ideia-m13-fazenda-mais-rica.md`.
- Fora do M12: Sonnet e Opus (segunda rodada), OpenRouter (v0.3), Langfuse e OpenTelemetry (nuvem), o humano na tabela de 30 dias (quando houver uma tarde de jogo gravada).
