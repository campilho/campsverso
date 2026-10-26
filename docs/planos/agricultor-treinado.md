# O agricultor treinado: um playbook de método para qualquer modelo

*Proposto em 25/out/2026, à noite, depois do fechamento do M19. É um passo curto entre o M19 e o M20, a pedido do usuário. A ideia está no `futuro.md`, e a linha de base é a corrida do Haiku da rodada de verificação (`docs/arena/2026-10-25.md`). Aprovado no mesmo dia, com as seis decisões (ADR-0071); as notas do usuário estão no fim.*

## O que a corrida do M19 mostrou

- **O Haiku experimenta, mas no lugar errado.** Foram 27 experimentos da noite, todos sobre o que o manual já explica: o avanço dos estágios, a fome dormindo, a chuva. Nenhum comparou canteiros em lugares diferentes, nem o mesmo canteiro em plantios seguidos.
- **A surpresa passou batida.** Do dia 4 ao 18, as hipóteses sobre como a planta avança falharam seguidas vezes. A causa provável era a fadiga do solo, e ele a leu como efeito da estação.
- **O caderno de campo já tem os fatos.** Cada plantio traz o canteiro e onde fica, o que havia antes nele, o adubo, a rega e os dias até amadurecer. Falta o método para ler esses fatos.

O script 3 tem esse método escrito em código: uma lista de suspeitas para cada plantio (a distância à água, à mata, ao caminho e à porta, o que havia antes, o adubo), com distratores, e o hábito de testar onde sabe menos. A pergunta deste passo é se um modelo que recebe o mesmo método, em palavras, também aprende.

## 1. O playbook

**Para qualquer modelo.** O texto é o mesmo para o Haiku, o Sonnet, o Opus e os modelos das outras famílias que vierem. Ele entra no prompt de sistema, depois do manual, quando a corrida pede, e a corrida sem playbook continua sendo o padrão. Assim as comparações com o M12, o M14 e o M19 continuam valendo.

**Duas camadas, como o resto da mente:**
- **O método,** em `libs/mind`, ao lado das instruções da reflexão e do experimento da noite. Vale para qualquer mundo, o escritório da v0.4 também.
- **O ofício do agricultor,** no gênero (`cartridges/farm/mind`). Diz como o método se aplica numa fazenda e vale para os três cenários.

**Só método, nunca regra oculta (princípio 5).** O teste de palavras proibidas da mente passa a ler o playbook também. As suspeitas que ele sugere são as mesmas do script 3, que a ADR-0070 (decisão 4) já julgou justas por serem atributos que qualquer um vê no mapa, misturados com distratores. O playbook não diz quais suspeitas são verdadeiras, nem quanto, nem até onde.

**O rascunho:**

> **O método.**
> 1. O mais valioso que você vê é a surpresa: o que saiu diferente do manual ou da sua crença. Anote-a no mesmo dia e procure a causa antes de seguir em frente.
> 2. Uma causa se procura comparando: dois casos parecidos que deram resultados diferentes. Liste no que eles diferem; cada diferença é uma suspeita.
> 3. Teste uma suspeita de cada vez, com um controle: dois casos que só diferem nela. Um experimento que muda duas coisas não ensina nenhuma.
> 4. Separe o que você viu do que supõe. Uma crença com uma observação só fica com a confiança baixa; ela sobe quando a comparação se repete.
> 5. Experimente barato: o teste não pode pôr em risco a comida nem o dinheiro dos próximos dias.
> 6. Quando uma crença se confirma, use-a: mude o que você faz, e confira se o resultado mudou.
>
> **O ofício do agricultor.**
> - O caderno de campo anota cada plantio: o canteiro e onde fica, a cultura, o que havia antes nele, o adubo, os dias de rega e quantos dias levou para amadurecer. Compare esses dias com os da tabela e da estação: o plantio que levou menos ou mais é a surpresa a explicar.
> - As suspeitas de um canteiro são o que se vê: perto do que ele fica (a casa, o poço, o caminho, a mata, a água), o que havia nele antes, se foi adubado, como foi regado, a estação e o tempo daquele dia.
> - Para testar um lugar, faça o mesmo plantio, no mesmo dia, em dois canteiros que só diferem no lugar. Para testar o histórico, faça o mesmo plantio num canteiro novo e num já usado.
> - O que some, murcha ou estraga também é surpresa: anote onde, quando e o que havia por perto.
> - Ao planejar, conte a comida e o dinheiro de vários dias, e não só de hoje.

## 2. A medição

- **O Haiku primeiro, porque é barato.** A corrida "sem" do mapa a já existe. Entram três corridas novas de 28 dias:
  - o Haiku com o playbook no mapa a;
  - o Haiku sem e com o playbook no mapa b, para ver se o efeito vale em outro mapa.

  Custam uns US$ 2,10. A prova, o juiz, as métricas de exploração e os experimentos da noite vêm como no M19, e o relatório põe as corridas lado a lado.
- **O Sonnet só se o Haiku mudar.** Mudar quer dizer qualquer um destes:
  - o juiz acha uma descoberta, a causa ou só o lugar, que a corrida sem playbook não teve;
  - a prova sobe com uma crença que sustente a resposta;
  - os plantios vão para a terra boa depois de testá-la.

  Se o Haiku mudar, roda uma dupla do Sonnet, sem e com o playbook, de 14 dias cada, no mapa a, com teto de US$ 15 por corrida: uns US$ 20 a 25 ao todo. Se o Haiku não mudar, o playbook é revisto antes de gastar com o Sonnet.

## 3. O custo e o orçamento

- **O orçamento de API da v0.3 é de US$ 150** (ADR-0066, decisão 17). Até aqui gastamos uns US$ 3. A arena do M21 está estimada em US$ 80 a 120.
- **Uma corrida de 28 dias do Sonnet na Morada do Sol** deve custar de US$ 15 a 22. Na Boa Vista, 30 dias custaram US$ 11,58, e a Morada pede uns 35% mais tokens de entrada por chamada que a Boa Vista.
- **Uma dupla de 28 dias** (US$ 30 a 45) cabe, mas deixaria o M21 no limite de baixo da estimativa. A dupla de 14 dias, só se o Haiku mudar, custa a metade e mede o que importa aqui: a descoberta aparece nas duas primeiras estações.
- **Este passo, no pior caso:** uns US$ 27 (o Haiku e a dupla do Sonnet).
- **As corridas não servem ao M21.** O M20 muda o mundo com os ajudantes, então este passo é um experimento à parte. O M21 decide, com este resultado na mão, se a arena roda com o playbook, sem ele ou com os dois.

## 4. Testes

- O playbook passa no teste de palavras proibidas da mente nos três cenários.
- Com o playbook desligado, o pedido é o mesmo de hoje: as fitas das três fazendas passam sem regravar.
- Com o playbook ligado, ele aparece no prompt de sistema, depois do manual, e a arena aceita `playbook` na corrida.
- O relatório mostra quem jogou com o playbook.

## 5. Ordem do trabalho

1. O playbook nas duas camadas, a opção na mente e na arena, e os testes.
2. As três corridas do Haiku, o juiz e o relatório.
3. A decisão do Sonnet pelo critério da §2: a dupla de 14 dias, ou a revisão do playbook.
4. O registro: a ADR-0071, o diário, o `futuro.md` e a recomendação para o M21.

## 6. Decisões

1. **Um playbook para qualquer modelo,** o mesmo texto para todos, ligado por corrida, com a corrida sem playbook como padrão. *Recomendação: sim. É o que o usuário pediu, e o padrão desligado preserva as comparações antigas.*
2. **Duas camadas:** o método em `libs/mind` e o ofício no gênero `farm`. *Recomendação: sim. O método serve ao escritório da v0.4; o ofício é dado do gênero, como o manual.*
3. **Só método, sem regra oculta:** as suspeitas são as do script 3, com distratores, e o teste de palavras proibidas lê o playbook. *Recomendação: sim. A camada "saber do ofício" do `futuro.md` (a água perto ajuda, repetir cansa a terra) ficaria de fora: ela contraria o princípio 5 e mediria outra coisa, quanto vale contar a regra, e não quanto vale ensinar a procurar. Se um dia quisermos medir isso, é outra ADR.*
4. **O Haiku em três corridas:** com o playbook no mapa a, e sem e com no mapa b, por uns US$ 2,10. *Recomendação: sim. Uma semente por condição é pouco, mas dois mapas mostram se o efeito não é do mapa.*
5. **O Sonnet condicionado ao Haiku:** uma dupla de 14 dias, com teto de US$ 15 por corrida, só se o Haiku mudar pelo critério da §2. *Recomendação: sim. Responde à pergunta do usuário sem gastar um quarto do orçamento num resultado que talvez já se saiba pelo Haiku.*
6. **O rascunho do playbook (§1)** aprovado como está, ou com as suas mudanças. *Recomendação: aprovar, e ajustar depois de ler os experimentos da noite do Haiku com o playbook.*

**As notas do usuário na aprovação (25/out):**
- **1:** o playbook melhora conforme o desempenho.
- **2:** uma biblioteca é importada só por quem a usa, como a economia e o clima.
- **3:** fica para depois o agente que joga de novo com o que aprendeu (30 dias, depois mais 30 com a memória, N vezes) e as técnicas de prompt: exemplos (one-shot, few-shot), cadeia de raciocínio e papel.
- **4:** por que três? Não é para tirar a aleatoriedade do modelo; a resposta está na ADR-0071.
- **5:** o saldo da Console era de US$ 54,25.

## 7. A primeira rodada (25/out, à noite)

As três corridas do Haiku rodaram em paralelo em `data/arena/20261025-playbook`, junto com cópias das corridas de referência do M19, e o relatório está em `docs/arena/2026-10-25-playbook.md`. Custaram US$ 1,81, mais US$ 0,01 da prova e US$ 0,23 do juiz.

| Corrida | Moedas | Colheitas | Dias com a fome em 100 | Canteiros cavados | Repetiu a cultura | O juiz | A prova (depois) |
|---|---|---|---|---|---|---|---|
| sem playbook, mapa a (M19) | 91 | 45 | 5 | 12 | 41 de 44 | só o lugar da fadiga | 2 certas, sem crença que as sustente |
| com playbook, mapa a | 0 | 21 | 17 | 7 | 13 de 15 | nada | fadiga certa, tomate errado, sem crença |
| sem playbook, mapa b | 5 | 34 | 19 | 11 | 19 de 30 | nada | fadiga certa, sem crença |
| com playbook, mapa b | 6 | 17 | 18 | 5 | 14 de 14 | nada | tudo "não sei" |

- **Pelo critério da §2, o Haiku não mudou:** o juiz não achou descoberta nova, a prova não subiu com crença que sustente, e ninguém plantou na terra boa. O Sonnet não roda, e o playbook é revisto antes (decisão 5).
- **O playbook mudou a forma dos experimentos, e não o assunto.** Os testes passaram a ter controle ("o plot-001 regado, o plot-002 sem rega"), mas os 56 experimentos das duas corridas com playbook foram sobre a rega, a chuva, o sono e a estação, como os 55 das duas sem ele. Nenhum comparou lugares, e nenhum fez o teste do canteiro novo contra o usado que o ofício sugere.
- **A fadiga voltou a se disfarçar.** No mapa b, com o playbook, o Haiku repetiu a cultura em 14 de 14 plantios e passou 7 noites testando que "crescendo só vira madura depois de dois dias seguidos de rega", uma causa inventada para a planta que demorava. O método foi seguido à letra (uma suspeita por vez, com previsão), mas a lista de suspeitas que ele mesmo montou não tinha o histórico do canteiro.
- **O playbook custou na economia, numa corrida por condição:** cavou menos canteiros, plantou menos e passou mais fome. Uma corrida por condição não separa isso do acaso: sem playbook, o mesmo Haiku fez 91 moedas no mapa a e 5 no mapa b.

**A revisão proposta** (o playbook 2): trocar o conselho geral por um procedimento, como o script 3 faz em código, e um exemplo (a nota do usuário sobre o few-shot):
- quando um plantio levar mais ou menos dias que a tabela, compará-lo, na tabela do caderno, com outro da mesma cultura que não levou, e escrever no que os dois diferem, coluna por coluna (o lugar, o que havia antes, o adubo, a rega, a estação);
- a cada semana, um par de teste: dois canteiros que só diferem numa dessas colunas;
- um exemplo de experimento bem feito, contado do começo ao fim, sobre uma mecânica visível (a chuva rega?), para mostrar a forma sem tocar em regra oculta.
