# Bíblia do cartucho — Fazenda do Camps (v0.1)

**Status:** proposta · **Data:** 10/out/2026
**Cartucho:** `farm` · **Mundo:** `farm-camps-01`
**Relacionado:** `escopo-v0.1.md`, `contratos-eventos-v0.md`, `kernel-gestao-do-tempo.md`

> Este documento define **o mundo**, não o código. Tudo aqui vira configuração do cartucho (YAML/JSON + mapa Tiled), nunca regra fixa no kernel. Números são ponto de partida e devem ser ajustados com dados dos testes de resistência.

---

## 1. Conceito

Uma pequena fazenda genérica, sem lore, onde um único avatar planta, rega, colhe, vende, come e dorme. O objetivo da v0.1 é **validar a plataforma**, não contar uma história. Por isso:

- Não há LLM. O avatar é controlado por **humano** (você, pela UI), **script** (fazendeiro determinístico) ou **replay**.
- Há uma **regra oculta** ativa desde o primeiro dia, mesmo sem ninguém capaz de aprendê-la. O script vira a **linha de base** dos experimentos futuros.
- A fazenda do vilarejo remoto na Patagônia, num futuro alternativo (Tomás e outros moradores), será, no futuro, este mesmo cartucho com outro mapa, outros personagens e outro cartão de identidade.

---

## 2. O avatar

| Campo | Valor |
|---|---|
| `id` | `camps` |
| Nome exibido | Camps |
| Papel | fazendeiro |
| Controlador inicial | `script` |
| Aparência (para o sprite LPC) | homem adulto; cabelo escuro curto, barba curta grisalha; camisa social azul com mangas dobradas; calça cáqui; sapato marrom; relógio de pulso |
| Retrato (HUD/diálogos) | ilustração em pixel art já existente (gerada no Gemini) |
| Personalidade | **nenhuma na v0.1** (cartão de identidade fica para a v0.2) |

---

## 3. Calendário, tempo e clima

| Item | Valor |
|---|---|
| Tick | 1 minuto simulado |
| Escala padrão | 72× (1 dia simulado ≈ 20 min reais) |
| Início | Dia 1, 06:00 |
| Estações | **nenhuma na v0.1** (primavera fixa) |
| Virada do dia agrícola | 06:00 (crescimento das plantas, pagamento das vendas) |
| Sorteio do clima | 05:00, fluxo de RNG `weather` (seed registrada) |
| Probabilidade de chuva | 20% |
| Efeito da chuva | todos os canteiros contam como regados naquele dia |

Fases do dia (eventos `world.clock.phase_changed`): `amanhecer` 06:00, `meio_dia` 12:00, `entardecer` 18:00, `noite` 20:00, `madrugada` 00:00.

---

## 4. Mapa

Grade de **32 × 18 tiles** (tiles de 32 px no renderer). Esboço:

```
        0         1         2         3
        01234567890123456789012345678901
y00     TTTTTTTTTTTTTTTTTTTTTTTTTTTTRRRR
y01     T...........................RRRR
y02     T.CCCCC.....................RRRR
y03     T.Cb.mC.....................RRRR
y04     T.C...CB....................RRRR
y05     T.CCPCC.....................RRRR
y06     T...=...V...................RRRR
y07     T...=.......................RRRR
y08     T...=.......................RRRR
y09     T...=...HHHH............HHHHRRRR
y10     T...=...HHHH.....W......HHHHRRRR
y11     T...=.......................RRRR
y12     T...=.......................RRRR
y13     T...========================RRRR
y14     T..............=............RRRR
y15     T..............=S...........RRRR
y16     T..............=............RRRR
y17     TTTTTTTTTTTTTTTEETTTTTTTTTTTRRRR
```

| Símbolo | Elemento | Coordenadas | Passável |
|---|---|---|---|
| `T` | árvores / cerca | bordas | não |
| `R` | rio | x 28–31 | não |
| `C` | parede da casa | x 2–6, y 2–5 | não |
| `P` | porta da casa | (4, 5) | sim |
| `b` | cama | (3, 3) | não (interagir adjacente) |
| `m` | mesa | (5, 3) | não |
| `B` | baú | (7, 4) | não |
| `V` | caixa de vendas | (8, 6) | não |
| `W` | poço | (17, 10) | não |
| `S` | quiosque de sementes | (16, 15) | não |
| `E` | entrada da propriedade | (15–16, 17) | sim (decorativa na v0.1) |
| `=` | caminho | — | sim |
| `H` | canteiro | ver abaixo | sim |
| `.` | grama | — | sim |

**Canteiros (16):**

| Grupo | IDs | Coordenadas | Distância ao rio |
|---|---|---|---|
| Oeste | `plot-w-01` … `plot-w-08` | x 8–11, y 9–10 | 17 a 20 tiles |
| Leste | `plot-e-01` … `plot-e-08` | x 24–27, y 9–10 | 1 a 4 tiles |

O desenho é proposital para o experimento da regra oculta: dois grupos iguais em tamanho, um colado ao rio e outro longe, e o **poço aproximadamente equidistante** dos dois (6 tiles do grupo oeste, 7 do leste). Na v0.1 o regador **só enche no poço**, não no rio, para não criar uma vantagem de logística que confundiria o efeito da regra.

**Interação:** uma ação sobre um objeto exige estar a até 1 tile dele (vizinhança de 8). Movimento em 4 direções, com pathfinding pelo kernel.

---

## 5. Itens

Moedas também são um item (`moeda`). Isso mantém a economia dentro da mesma primitiva de itens e contêineres.

| Item | Tipo | Empilha | Comestível |
|---|---|---|---|
| `moeda` | moeda | sim | não |
| `semente_rabanete`, `semente_batata`, `semente_abobora` | semente | sim | não |
| `rabanete`, `batata`, `abobora` | colheita | sim | sim |
| `regador` | ferramenta (capacidade 10 cargas) | não | não |

**Contêineres:** inventário do avatar (sem limite na v0.1), baú (sem limite), caixa de vendas (esvaziada pelo comprador).

**Estado inicial:** 100 moedas, 10 sementes de rabanete e o regador cheio no inventário; baú com 5 rabanetes (comida para atravessar os primeiros dias sem colheita).

---

## 6. Culturas

| Cultura | Semente | Dias para amadurecer | Venda | Reduz fome |
|---|---|---|---|---|
| Rabanete | 10 | 3 | 25 | 25 |
| Batata | 20 | 5 | 50 | 35 |
| Abóbora | 40 | 8 | 120 | 50 |

**Ciclo da planta:** `semente` → `broto` → `crescendo` → `madura`; se abandonada, `murcha`.

- Crescimento por **pontos**: às 06:00, cada planta que foi regada no dia anterior ganha 1,0 ponto. Amadurece ao atingir o número de dias da tabela.
- Uma planta **não regada por 2 viradas seguidas murcha** e precisa ser removida.
- A colheita rende **1 unidade** por canteiro.
- A percepção expõe apenas o **estágio** (não os pontos). Quem quiser descobrir a regra oculta precisa observar quantos dias cada canteiro levou.

**Espaço para melhorar (regra visível):** por canteiro-dia, a abóbora rende mais que a batata, que rende mais que o rabanete (≈ 10, 6 e 5 moedas por dia). O fazendeiro-script planta só rabanete, deliberadamente ingênuo. Um agente LLM poderá descobrir que vale a pena mudar de cultura, desde que tenha capital e comida para atravessar os dias sem colheita.

---

## 7. Necessidades

| Necessidade | Escala | Dinâmica | Efeito |
|---|---|---|---|
| Fome | 0 (saciado) → 100 | +3 por hora acordado, +1 por hora dormindo | a partir de 80, as ações gastam o **dobro** de energia |
| Energia | 0 → 100 | gasta por ação (tabela 8); dormir recupera 12,5 por hora na cama e 5 por hora no chão | em 0, o avatar **desmaia** |

**Sono** (ADR-0041, ADR-0049):
- Dorme-se em qualquer lugar e a qualquer hora.
- **À noite** (das 20:00 às 06:00), dorme-se até as 06:00.
- **De dia**, é um cochilo: acorda quando a energia chega a 100, ou às 06:00, o que vier antes. Com a energia já em 100, não há cochilo (`not_tired`).
- **Na cama** (ou análogo, ao lado): energia = mínimo(100, energia + 12,5 × horas dormidas).
- **No chão**, onde estiver: o sono ruim recupera 5 por hora (8 h dão +40).
- Se ainda estiver acordado às 02:00, ou se a energia chegar a 0, desmaia onde estiver e acorda às 06:00 **com energia 50**.

**Ordem de grandeza diária:** a fome sobe cerca de 56 pontos por dia, o equivalente a pouco mais de 2 rabanetes.

---

## 8. Catálogo de ações v0.1 (afordâncias)

Todas as ações são propostas por **qualquer controlador** via `campsverso.cmd.action.propose.v1`, com o mesmo catálogo para humano, script e replay. O menu de quem joga vem do catálogo de afordâncias do gênero (`affordances` no `farm.yaml`), publicado no `session.started` (ADR-0051).

| Ação | Alvo | Pré-condições | Duração (ticks) | Energia | Efeito |
|---|---|---|---|---|---|
| `move` | tile | destino passável e alcançável | distância ÷ 3 tiles/min (arredondado para cima) | 0 | trajeto calculado pelo kernel |
| `plant` | canteiro | canteiro vazio; semente da cultura no inventário | 5 | 2 | semente consumida; planta em `semente` |
| `water` | canteiro | regador com carga; canteiro com planta | 2 | 2 | regador −1; canteiro regado hoje |
| `refill` | poço | adjacente | 3 | 1 | regador = 10 |
| `harvest` | canteiro | planta `madura` | 3 | 1 | +1 colheita no inventário; canteiro vazio |
| `clear` | canteiro | planta `murcha` | 3 | 2 | canteiro vazio |
| `eat` | item | item comestível no inventário | 10 | 0 | item consumido; fome reduzida |
| `deposit` / `withdraw` | baú | adjacente; quantidade disponível | 1 | 0 | transfere itens |
| `sell` | caixa de vendas | adjacente; colheita no inventário | 1 | 0 | itens vão para a caixa |
| `buy` | quiosque | aberto (08:00–18:00); moedas suficientes | 2 | 0 | moedas −; sementes + |
| `sleep` | cama (opcional) | com alvo, ao lado da cama; de dia, energia abaixo de 100 | à noite, até 06:00; de dia, até a energia encher (no máximo até 06:00) | — | recupera energia: 12,5/h na cama, 5/h sem alvo |
| `wait` | — | — | n (1–60) | 0 | nada |

**Regras gerais:**
- Uma ação por vez; uma ação em andamento pode ser **cancelada** por novo comando do mesmo controlador (exceto `sleep`).
- Comando de controlador que não detém a posse → `action.rejected` com motivo `not_in_control`.
- Toda rejeição traz motivo legível por máquina (`not_adjacent`, `missing_item`, `closed`, `not_ripe`, `insufficient_funds`, `not_tired`…). Isso será sinal de aprendizado para o LLM na v0.2.

---

## 9. Sistemas do mundo (rodam sem ninguém agir)

| Sistema | Quando | O que faz |
|---|---|---|
| `clock_phases` | horários fixos | emite fases do dia |
| `weather` | 05:00 | sorteia sol ou chuva |
| `crop_growth` | 06:00 | soma pontos de crescimento; amadurece; murcha |
| `needs` | cada tick (integrável em saltos) | fome sobe, energia de sono |
| `buyer` | 22:00 recolhe; 06:00 paga | esvazia a caixa de vendas e credita moedas no inventário do avatar |
| `kiosk_hours` | 08:00 e 18:00 | abre e fecha o quiosque |
| `faint` | 02:00 e quando energia = 0 | desmaio |

Todos os sistemas são funções puras do estado + tick + RNG nomeado. Nenhum lê o relógio de parede.

---

## 10. Regra oculta R-001 — Bônus do rio

| Campo | Valor |
|---|---|
| `id` | `river_proximity_bonus` |
| Versão | 1.0.0 |
| Visibilidade | `internal` (nunca chega a nenhum controlador) |
| Efeito | canteiros a **até 4 tiles** do rio ganham **1,5 ponto** de crescimento por dia regado, em vez de 1,0 |
| Estado inicial | **ligada** |

Efeito prático (dias até amadurecer):

| Cultura | Longe do rio | Perto do rio |
|---|---|---|
| Rabanete | 3 | 2 |
| Batata | 5 | 4 |
| Abóbora | 8 | 6 |

- Na virada do dia, o kernel emite `campsverso.rules.effect_applied.v1` (internal) para cada canteiro afetado, e `campsverso.action.effects_explained.v1` quando uma colheita teve contribuição da regra.
- Na UI, a regra só aparece no **modo operador** (você), nunca no modo jogador.
- A regra é alternável a quente (`campsverso.rules.toggled.v1`), já preparando os experimentos de "tempo até desaprender".

---

## 11. Fazendeiro-script (controlador determinístico)

Prioridades avaliadas a cada decisão, na ordem. A primeira aplicável vence. Empates são decididos por **menor distância** e depois **menor id**, para garantir determinismo.

1. **Dormir:** se energia < 10 (a qualquer hora; de dia, é um cochilo) ou horário ≥ 21:30 → ir até a cama e dormir.
2. **Comer:** se fome ≥ 70 e há comestível no inventário → comer o de menor valor de venda; se não houver no inventário, mas houver no baú → retirar e comer.
3. **Colher:** se existe planta madura → colher a mais próxima.
4. **Limpar:** se existe planta murcha → limpar.
5. **Encher:** se o regador está vazio e algum canteiro precisa de água → encher no poço.
6. **Regar:** se não choveu hoje e existe planta não regada hoje → regar a mais próxima.
7. **Plantar:** se há canteiro vazio e semente no inventário → plantar no mais próximo.
8. **Vender:** se há colheita além de uma reserva de 3 unidades de comida → vender o excedente.
9. **Comprar:** se o quiosque está aberto, há canteiros vazios sem semente correspondente e moedas suficientes → comprar sementes de rabanete.
10. **Esperar:** 15 minutos.

O script **só usa a percepção**, como qualquer controlador. Ele não conhece a regra oculta e não prefere nenhum grupo de canteiros: é a linha de base contra a qual o agente LLM será medido.

**Observação para os testes:** uma simulação aproximada (sem deslocamento nem horários) indica que, com esses números, o script sobrevive indefinidamente e acumula moedas devagar: cerca de **+15 por dia com a regra oculta desligada** e **+30 por dia com ela ligada**. Ou seja, a regra dobra o rendimento mesmo de quem não sabe que ela existe, o que dá um sinal forte para o agente da v0.2 perceber. Se o teste de resistência mostrar outra coisa, ajustar primeiro os números desta bíblia, não o kernel.

---

## 12. Percepção na v0.1

- O controlador recebe o estado de **toda a propriedade** (raio de percepção configurável, mas a fazenda inteira na v0.1), filtrado para eventos `world` e `agent`.
- Expõe: posições, estágios das plantas, se cada canteiro foi regado hoje, clima do dia, inventário, conteúdo do baú, fome, energia, horário e se o quiosque está aberto.
- **Não expõe:** pontos de crescimento, regras ocultas, eventos `internal`.

---

## 13. Métricas que a v0.1 já deve registrar

| Métrica | Por quê |
|---|---|
| Colheitas por dia, por grupo (oeste/leste) | evidência observável da regra oculta |
| Dias até amadurecer por canteiro | idem |
| Moedas ao fim de cada dia | eficiência econômica |
| Ações rejeitadas por motivo | qualidade do controlador |
| Plantas murchas | desperdício |
| Picos de fome e desmaios | sobrevivência |
| Tempo real por dia simulado | desempenho do kernel |

Essas mesmas métricas, com o script como linha de base, alimentam a arena humano × script × LLM da v0.2.
