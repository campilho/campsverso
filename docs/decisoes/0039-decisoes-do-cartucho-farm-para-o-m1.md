# ADR-0039 — Decisões do cartucho farm para o M1

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M1
**Esclarece:** `fazenda-camps-biblia-v0.1.md` §4, §6, §7, §10; catálogo §6

Todos os números abaixo ficam na configuração do cartucho, nunca no kernel (ADR-0020).

## Decisão

1. **Estágios da planta:** `semente` → `broto` (≥ 1 ponto) → `crescendo` (≥ 50% dos pontos necessários) → `madura` (100%), ou `murcha` depois de 2 viradas seguidas sem rega.
   - Isso dá 5 imagens por cultura, 15 no total, no renderer do M6. Os pacotes de arte LPC costumam ter de 4 a 6 estágios por cultura.
2. **Ids dos objetos:** `bed`, `table`, `chest`, `sell-box`, `well`, `kiosk`, `door`.
   - O regador é a entidade `watering-can` (tipo `watering_can`), guardada no inventário de `camps`.
   - O avatar começa em (4, 4), ao lado da cama.
3. **Limiares de necessidade, configuráveis no cartucho:**
   - fome **80** subindo e energia **20** descendo pedem decisão ao controlador;
   - energia **0** descendo dispara o desmaio automático (sistema `faint`), sem pedir decisão.
   - Os limiares do fazendeiro-script (fome ≥ 70 para comer, energia < 10 para dormir; bíblia §11) são lógica do próprio script. Ele reavalia tudo a cada pedido de decisão.
4. **Regra oculta genérica no gênero:** `water_proximity_bonus`, desligada por padrão.
   - O gênero não sabe onde há água. A regra mede a distância (Chebyshev, como a vizinhança de 8) até o tile mais próximo marcado com `water` no mapa.
   - O cenário `farm_camps` marca o rio no mapa e declara a instância `river_proximity_bonus`: oculta, ligada, raio 4, multiplicador 1,5.
5. **Chuva:** num dia de chuva, até as plantas plantadas durante o dia já contam como regadas (bíblia §3: "todos os canteiros contam como regados naquele dia").
6. **Venda:**
   - às 22:00 o comprador esvazia a caixa (`item.consumed`, motivo `buyer_collect`);
   - às 06:00 ele paga (`item.created`, motivo `payment`, mais `farm.buyer.paid`);
   - o valor devido fica num atributo oculto da caixa de vendas.

## Consequências

Mudar qualquer número (preço, limiar, raio, estágio) é editar o YAML do cartucho, sem tocar no kernel.
