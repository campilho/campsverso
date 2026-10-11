# ADR-0037 — Ordem de execução do tick configurável

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M1
**Esclarece:** ADR-0018, item 4

## Contexto

A ordem do que acontece dentro de um tick muda o resultado: crescer antes ou depois de zerar a rega, desmaiar antes ou depois de concluir uma ação. A ordem proposta foi aceita com um pedido: que seja fácil de mudar e de enxergar.

## Decisão

1. **Etapas nomeadas, em ordem, na configuração do kernel.** A ordem padrão é:

   | # | Etapa | Quem roda |
   |---|---|---|
   | 1 | `scheduled` | sistemas do cartucho agendados para este horário |
   | 2 | `clock` | kernel: fases do dia |
   | 3 | `needs` | kernel: necessidades avançam pelas taxas e cruzam limiares |
   | 4 | `wake` | kernel: avatares acordam na hora marcada |
   | 5 | `actions` | kernel: ações que terminam neste tick, com os efeitos do cartucho |
   | 6 | `commands` | kernel: ações propostas pelos controladores (aceitar, recusar, cancelar a atual) |
   | 7 | `reactions` | sistemas do cartucho disparados por limiar cruzado neste tick (ex.: desmaio com energia 0) |
   | 8 | `decisions` | kernel: pedidos de decisão para avatares ociosos |

2. **Sistemas do cartucho declaram etapa e prioridade.** Dentro da etapa, roda primeiro a menor prioridade; o empate é decidido pelo nome. Exemplo às 06:00: `crop_growth` (10) → `buyer_pay` (20) → `new_day` (30); depois a fase "amanhecer" e o despertar.
3. **Comandos de controle rodam fora do tick**, na fronteira entre dois ticks: relógio, posse e alternância de regras. Com o relógio pausado nenhum tick roda, e mesmo assim é preciso conseguir retomar ou avançar.
4. **A ordem efetiva fica visível e travada por teste.** Um teste imprime a ordem dos horários-chave (02:00, 05:00, 06:00, 22:00) e a compara com um arquivo de referência. Mudar a ordem é editar a configuração ou as prioridades e atualizar a referência de propósito.
5. **Configuração inválida falha na carga:** etapa desconhecida ou sistema sem etapa é erro.

## Consequências

- Mudar a ordem não exige mexer no código do kernel.
- A ordem vira documentação verificada: quem lê o arquivo de referência sabe exatamente o que acontece às 06:00.
