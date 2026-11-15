# Bíblia do escritório do Campsverso

*A v0.4 (ADR-0077), o M23 (ADR-0078). As regras e os números do escritório: o gênero `office` e o cenário `office_campsverso`. Os dados ficam em `cartridges/office/sim/.../data/office.yaml` (o gênero) e `cartridges/office_campsverso/sim/.../data/escritorio.yaml` (o cenário); se este texto e os dados discordarem, valem os dados, e o texto se corrige.*

## 1. O que é

Um escritório de programação em tempo real. Um dev de IA, o Camps, mora nele; um humano entra como o gerente, escreve os pedidos no quadro, conversa com o dev e aceita ou devolve o que ele entrega. Não há regra oculta: a medida é o pedido (ADR-0077).

## 2. O tempo

| | |
|---|---|
| Tick | 2 s (a medida do M23; ADR-0078, adendo) |
| Relógio | o de São Paulo, a 1×; ao subir, o mundo salta até agora (`clock.anchor: wall`) |
| Dia | começa às 00:00 (o dia do calendário) |
| Fases | madrugada 00:00, manhã 06:00, tarde 12:00, noite 18:00 |
| Expediente | de segunda a sexta, das 09:00 às 18:00 |
| Almoço | das 12:00 às 13:00, fora do escritório |
| Feriados | os nacionais, na lista do cenário |

O escritório vivo é o mundo `office-campsverso-01` (`make escritorio`). O `office-campsverso-teste` (modo máximo, com o gerente-script) serve aos testes e ao soak, e o `office-campsverso-demo` começa numa segunda às 08:59, para ver o dev em qualquer dia.

## 3. A sala

Uma sala de 20 × 14 tiles com as paredes, e o corredor embaixo.

| Coisa | Tile | Tipo |
|---|---|---|
| Quadro dos pedidos | (9, 2) | `board`, bloqueia |
| Mesa do Camps | (5, 6) | `desk`, bloqueia; `dono: camps` |
| Cadeira | (5, 7) | `chair` |
| Bancada | (14 a 16, 5) | `bench`, bloqueia; os robôs vão ficar nela (M24 em diante) |
| Porta | (9, 13) | `door` |
| Cadeira do vigia | (11, 12) | `chair` |
| Entrada | (9, 15) | o tile do corredor por onde todos entram e saem |

Andar: 4 tiles por segundo na tela, em qualquer escala; o kernel converte pela escala do momento (ADR-0079). A 1× são 8 tiles num tick de 2 s; a 72×, andar até o quadro custa uns 2 minutos do mundo. A percepção vê a sala inteira.

## 4. O elenco

| Quem | Papel | Controlador padrão | Aceita | Quando está |
|---|---|---|---|---|
| Camps | `dev` | `script/dev` | `llm`, `script`, `replay`: nunca um humano | no expediente |
| Gerente | `gerente` | `script/gerente-fora` (fora do escritório) | `human`, `script`, `replay` | enquanto alguém o assume; entra pela porta e sai quando é devolvido |
| Vigia | `vigia` | `script/vigia` | `script`, `replay` | sempre que o dev não está: à noite, no fim de semana e nos feriados (não no almoço) |

A cadeira do jogador é o gerente (`player: gerente`): a tela do jogador o assume, e o gateway recusa qualquer outro avatar.

## 5. O pedido

Uma entidade `ticket` guardada no quadro, com os atributos:

| Atributo | O que é |
|---|---|
| `numero` | a ordem em que foi escrito |
| `titulo` | até 80 caracteres |
| `descricao` | até 1.000 |
| `aceite` | o teste de aceite, o "pronto quando": até 500 |
| `tamanho` | P, M ou G: 15, 60 ou 180 minutos de trabalho simulado (no M23, só o dev-script) |
| `estado` | `a_fazer`, `fazendo`, `entregue` ou `aceito` |
| `autor`, `dono` | quem escreveu e quem está fazendo |
| `trabalho` | os segundos de trabalho já feitos |
| `comentario` | o que o gerente disse ao devolver |

## 6. As ações

| Ação | Quem | Onde | Duração | O que faz |
|---|---|---|---|---|
| `say` (do kernel) | todos | qualquer lugar | 2 a 12 s, pelo tamanho | fala até 280 caracteres, para alguém (`to`) ou para quem estiver perto |
| `write_ticket` | gerente | ao lado do quadro | 20 s | escreve um pedido |
| `take_ticket` | dev | ao lado do quadro | 4 s | pega o pedido mais antigo a fazer, ou o escolhido; um de cada vez |
| `work` | dev | ao lado da mesa | o que falta, ou um bloco (`seconds`) | trabalha; `partial`: parar guarda o feito |
| `deliver` | dev | ao lado da mesa | 6 s | entrega o pedido terminado |
| `accept_ticket` | gerente | ao lado do quadro | 6 s | aceita o entregue |
| `return_ticket` | gerente | ao lado do quadro | 10 s | devolve com o comentário; o pedido volta a "a fazer" e o trabalho recomeça |

Fora do papel, a ação é recusada (`not_allowed`); longe do lugar, `not_adjacent`.

## 7. Os eventos

`campsverso.office.ticket.created.v1`, `taken`, `delivered`, `accepted` e `returned`, mais a fala (`campsverso.avatar.spoke.v1`) e a entrada e a saída de cada um (`avatar.entered` e `avatar.left`, com os motivos `expediente`, `almoco`, `plantao`, `possessed` e `released`).

## 8. Os scripts

- **O dev-script**, a linha de base:
  - responde a quem falou com ele ("Bom dia!" na primeira vez do dia, "Anotado." depois);
  - cumprimenta o gerente quando ele chega;
  - pega o pedido mais antigo e avisa;
  - trabalha em blocos de um minuto, entrega e avisa;
  - sem pedido, espera na cadeira.
- **O vigia:** faz a ronda nos 10 primeiros minutos de cada hora e passa o resto na cadeira da porta.
- **O gerente-script** (só nos testes e no soak):
  - escreve três pedidos por dia, às 09:30, 10:30 e 14:00;
  - cumprimenta o dev;
  - aceita os entregues e devolve um de cada três, na primeira entrega.

## 9. As métricas do dia

Os pedidos escritos, entregues, aceitos e devolvidos; os segundos de trabalho entregues; as falas.
