# ADR-0041 — Dormir em qualquer lugar; a cama turbina a recuperação

**Status:** proposta · **Data:** 2026-10-11 · **Marco:** antes do M2 (ajuste pequeno no M1)
**Altera:** `fazenda-camps-biblia-v0.1.md` §7 e §8 (`sleep`); ADR-0039

## Contexto

Hoje:

- **Dormir exige estar ao lado da cama:** sem ela, a ação é recusada com `not_adjacent`. Dormir onde está só acontece no desmaio.
- **Recuperação:** 12,5 de energia por hora vale para qualquer sono.
- **Desmaio:** acorda às 06:00 com energia 50 fixa.
- **Sono curto já acorda cansado,** porque a recuperação é por hora: quem deita às 03:00 acorda às 06:00 com +37,5.

A revisão do M1 levantou três pontos:

- o avatar (IA ou jogador) deve poder escolher dormir onde está;
- o sono fora da cama deve recuperar o mínimo, algo como o desmaio;
- camas e coisas análogas devem turbinar a recuperação.

## Proposta

1. **`sleep` sem alvo:** dorme onde está (sono ruim). **`sleep` com alvo:** uma entidade de dormir adjacente (cama hoje; rede, sofá ou saco de dormir no futuro) dá sono bom.
2. **A recuperação depende do lugar.**
   - Cada tipo de entidade de dormir declara sua taxa (`sleep_rate_per_hour`; cama = 12,5).
   - Dormir no chão usa a taxa mínima do gênero (`sleep.rough_rate_per_hour`). Proposta: **5/h**, ou seja, 8 h no chão dão +40, parecido com o desmaio. 8 h na cama dão +100.
3. **Kernel:** a primitiva `start_sleep` passa a receber as taxas de recuperação daquele sono, que substituem a taxa "dormindo" da necessidade. O kernel continua genérico e confere que a taxa vira unidade inteira (5/h = 10 unidades por tick).
4. **Janela de sono:** continua 20:00–06:00 para os dois tipos, acordando às 06:00. Cochilos durante o dia ficam para o futuro.
5. **Desmaio:** continua como na bíblia (acorda às 06:00 com 50).

## Para o futuro (não agora)

- **Itens que recuperam energia** (café, comidas), com limite.
- **Uma segunda necessidade, "sono"** (pressão de sono). Ela sobe enquanto se está acordado, só baixa dormindo e, em 100, desmaia.
  - Separa **energia** (fôlego para agir, que um café recupera) de **sono** (cansaço acumulado, que só a cama resolve). Ninguém fica três dias acordado à base de café.
  - Hoje o desmaio das 02:00 já garante isso.

## Consequências

- A bíblia §7 e §8 passa a dizer "dormir em qualquer lugar; a cama recupera mais".
- O fazendeiro-script (M3) prefere a cama e só dorme onde está se não der tempo de chegar.
- Mudança pequena: um parâmetro na primitiva do kernel, a ação `sleep`, dados do gênero e testes.
