# Plano do M18 — A economia

*Proposto em 24/out/2026, depois do fechamento do M17. É o marco da economia da v0.3 (ADR-0066, decisão 7): um módulo reaproveitável pelo escritório e pelo vilarejo, e a Fazenda Morada do Sol como o primeiro mundo que o usa.*

**Pronto quando:**
- **O módulo de economia** existe à parte da fazenda, com testes próprios: mercados com preço que reage à oferta e à demanda, encomendas com prazo e uma agenda de eventos (a feira).
- **O mercado nos dois sentidos,** na Morada do Sol: vender muito do mesmo item derruba o preço, e ele só se recupera aos poucos nos dias seguintes; comprar muito da mesma semente sobe o preço no dia; o preço muda com a estação e oscila um pouco a cada dia.
- **As encomendas:** um quadro perto do quiosque com pedidos de clientes (quem pede, o quê, quanto, até quando e quanto paga). O avatar aceita, entrega e recebe na hora; o pedido aceito que vence tem consequência.
- **A feira:** a cada 7 dias, uma barraca na entrada da fazenda compra colheitas e produtos com prêmio e paga na hora.
- **O processamento:** o tacho transforma colheita em produto que vale mais e dura mais (geleia, molho, farinha), trabalhando sozinho por horas.
- **O clima com previsão:** o tempo de amanhã sai às 18:00, com dois eventos novos, a tempestade e a seca.
- **A mente entende** as encomendas, a feira e o tacho pelo manual, com a fita regravada; **o script 2 adaptado vive um ano** na Morada do Sol.
- **As fazendas 1 e 2 intactas:** os mesmos números de sempre.

## O que o levantamento mostrou

- **A economia de hoje é código do gênero farm,** ligado por dados de cada cenário:
  - a caixa de vendas tem um preço do dia que cai 10% a cada 5 unidades vendidas da mesma colheita, até 50%, e volta à tabela na virada do dia (`market`, ADR-0062);
  - o comprador recolhe às 22:00 e paga às 06:00;
  - o quiosque vende sementes com preço fixo e um estoque do dia por um ciclo de 6 dias (`kiosk_cycle`); a semente parada na estação some do estoque (ADR-0067);
  - as ferramentas (o regador grande, o arado) nascem como entidades na compra.
- **Nada disso serve a outro mundo:** o escritório vai ter tickets com prazo e pagamento (o análogo das encomendas), e o vilarejo, uma feira. Hoje teriam de copiar o código do gênero.
- **O estado do mercado mora em atributos das entidades,** visíveis (`preco_rabanete`, `estoque_hoje`) e ocultos (`sold_rabanete`, o que cada venda valeu). Toda mudança já vira evento genérico (`world.entity.state_changed`). O módulo pode seguir esse caminho, sem primitiva nova no kernel.
- **O clima é sorteado pelo cartucho** às 05:00 (`draw_weather`, pelo `set_weather` do kernel), só sol ou chuva. Uma previsão é sortear o dia seguinte na véspera; o kernel já guarda o tempo por dia.
- **A mente lê os preços na foto** (os atributos da caixa e do quiosque). As encomendas e a feira entram do mesmo jeito: atributos do quadro e da barraca, mais as ferramentas de aceitar, entregar e processar.
- **O script 2 vende tudo na caixa** e repete o rabanete. Com o preço que não volta de manhã, ele vai ganhar menos; é a linha de base cega, e o script 3 (M19) é quem vai planejar.

## 1. O módulo de economia

Uma biblioteca nova, **`libs/economy`**: Python puro, determinística, sem I/O e sem saber o que é uma fazenda. O cartucho chama as funções dela nos seus sistemas e ações, guarda o estado nos atributos das entidades e muda o mundo só pelas primitivas, como hoje. O kernel não muda.

Três peças:
- **Mercado:** um preço por item, que parte de uma **referência** (a tabela, vezes o fator da estação, vezes a oscilação do dia) e se afasta dela com a **pressão** do dia: vender empurra para baixo, comprar empurra para cima. Na virada do dia a pressão se desfaz aos poucos (a recuperação), e cada mercado diz a sua velocidade.
- **Encomendas:** pedidos com cliente, itens, quantidade, prazo e pagamento. O módulo sorteia os pedidos novos (pelo RNG nomeado que o cartucho passa), aceita, confere a entrega, vence os atrasados e mantém a **reputação** de quem aceitou.
- **Agenda:** eventos que se repetem pelo calendário (a feira a cada 7 dias). Serve também ao escritório (a reunião de toda segunda) e ao vilarejo.

Os nomes do módulo são genéricos (mercado, item, pedido, cliente), e os do cartucho, da fazenda (a caixa de vendas, o quiosque, o quadro, a barraca). O escritório vai usar o mesmo pedido para os tickets.

## 2. O mercado nos dois sentidos

Na Morada do Sol; a Boa Vista e a fazenda 1 continuam com o mercado de hoje.

- **Vender:** cada unidade vendida na caixa derruba o preço daquela colheita em 2%, até o piso de 40% da referência. Na virada do dia, o preço recupera um terço da distância até a referência: quem despeja 30 rabanetes num dia encontra o preço baixo por uns três ou quatro dias. O que se põe na caixa vale o preço do momento, como hoje.
- **Comprar:** cada unidade comprada da mesma semente sobe o preço dela em 3% no dia. Na virada do dia, ele volta à tabela.
- **A referência muda com a estação:** uma colheita fora da estação boa vale mais, porque é rara. Na estação boa vale a tabela, na fraca 25% a mais, na parada 60% a mais (só quem guardou tem o que vender: o alho, a mandioca, a abóbora, ou a farinha).
- **A oscilação do dia:** a referência de cada colheita anda até 4% por dia, para cima ou para baixo, sem passar de 15% da tabela da estação. Vem de um RNG nomeado (`market`), então é determinística pela seed.
- **Na foto e na tela:** a caixa mostra o preço de agora de cada colheita (`preco_milho`), e o quiosque, o de cada semente.

## 3. As encomendas

- **O quadro de encomendas,** ao lado do quiosque, é um marco: todo avatar sabe onde fica.
- **Os pedidos:**
  - às 06:00 aparecem de 0 a 2 pedidos novos, até 4 abertos;
  - cada um tem um cliente (uma lista de nomes da cidade nos dados do cenário), uma colheita da estação ou um produto do tacho, de 2 a 6 unidades e um prazo de 3 a 7 dias;
  - paga 50% acima da referência do dia em que apareceu.
- **Aceitar** (`accept_order`, ao lado do quadro): até 2 aceitos por vez. Quem não aceita vê o pedido sumir no prazo.
- **Entregar** (`deliver_order`, ao lado do quadro): tira os itens do inventário e paga na hora, ao contrário da caixa, que paga no dia seguinte.
- **A reputação:** entregar no prazo faz aparecerem mais pedidos e com prêmio maior. Deixar vencer um pedido aceito faz o contrário. É a regra oculta nova do marco (decisão 7): o manual diz que os clientes lembram, e os números ficam escondidos.
- **Eventos:** o pedido aparece, é aceito, é entregue ou vence (§9).

## 4. A feira

- **Quando:** a cada 7 dias (os dias 7, 14, 21 e 28 de cada ano: o último dia de cada estação), das 06:00 às 14:00.
- **Onde:** uma barraca na estrada, na entrada da fazenda, a uns 45 tiles da casa. Ela é um marco e aparece fechada nos outros dias.
- **O que compra:** colheitas e produtos do tacho, a 30% acima da referência. Tem pressão própria, e paga na hora.
- **Por quê:** é uma decisão de logística, porque a caminhada é longa e a feira acaba às 14:00. Também dá destino aos produtos do tacho, que duram até o próximo dia de feira.

## 5. O processamento

- **O tacho,** comprado no quiosque (200 moedas, peso 6) e fincado na grama como o espantalho. Pode haver mais de um.
- **As receitas,** uma por vez em cada tacho:

  | Produto | Entra | Horas | Vale | Dura (dias) |
  |---|---|---|---|---|
  | geleia | 3 morangos | 12 | 330 (os morangos, 270) | 30 (o morango, 2) |
  | molho de tomate | 3 tomates | 8 | 280 (210) | 30 (3) |
  | farinha | 4 mandiocas | 8 | 450 (320) | 90 (20) |

- **Como funciona:**
  - carregar (`process`) leva 5 minutos e põe os ingredientes no tacho;
  - o tacho trabalha sozinho, e o avatar segue a vida;
  - o produto espera no tacho até ser pego (`withdraw`, como no baú).
- **Os produtos** são itens de categoria nova (`produto`): não se comem, vendem-se na caixa, na feira e nas encomendas, e têm a sua oscilação de preço.
- **A composteira** (decisão 10): ao lado da casa, transforma o que estragou e as plantas murchas em adubo, em 3 dias. Fecha o ciclo do que hoje se perde.

## 6. O clima com previsão

- **A previsão:** às 18:00 sai o tempo de amanhã, visível na foto e no HUD ("amanhã: tempestade"). Às 05:00 ele vale, como hoje.
- **A tempestade:**
  - chove, e a chuva conta como rega;
  - cada planta madura tem 30% de chance de ser derrubada e perdida;
  - quem viu a previsão colhe na véspera.
  - Chance de 8% no verão e de 4% nas outras estações.
- **A seca:**
  - não chove;
  - toda planta precisa de rega até o meio-dia, ou não cresce naquele dia;
  - o regador gasta 2 cargas por canteiro.
  - Chance de 10% no inverno seco e de 3% nas outras estações.
- **O mercado reage ao clima:** depois de uma tempestade ou de uma seca, a referência de cada colheita sobe 15% por 3 dias. Quem guardou colheita, ou tem farinha e geleia, ganha.
- **O resto do clima:** a chuva continua em um dia a cada cinco. As fazendas 1 e 2 não têm previsão nem eventos.

## 7. A mente e o script

- **O manual da Morada do Sol** ganha:
  - o mercado que lembra: vender muito derruba o preço por alguns dias, e comprar muito sobe o da semente;
  - a estação no preço;
  - o quadro de encomendas, com "os clientes lembram de quem cumpre";
  - a feira e o tacho com as receitas;
  - a composteira e a previsão.

  Os números da recuperação e da reputação ficam fora, como regra oculta.
- **As ferramentas:** aceitar e entregar encomenda, carregar o tacho; vender na feira usa a ferramenta de vender, com a barraca como alvo; pegar o produto usa a de pegar, com o tacho como alvo.
- **A fita de dois dias,** regravada (uns US$ 0,05).
- **Uma corrida curta de verificação** com o Haiku, de 7 dias, para ver se ele aceita e entrega encomendas e lê a previsão (uns US$ 0,15).
- **O script 2 adaptado:**
  - aceita encomendas da cultura que já planta quando tem como cumprir, e as entrega;
  - colhe na véspera da tempestade;
  - não usa a feira nem o tacho, que são do script 3 (M19).
  - Ele precisa viver um ano: é a linha de base.

## 8. A tela

- **O quadro:** o clique direito mostra os pedidos (cliente, itens, prazo e pagamento) e o menu de aceitar e entregar. A escolha do pedido vem dos atributos do quadro, e não de uma lista fixa.
- **O HUD** mostra a previsão de amanhã; o tacho mostra o que faz e quanto falta, como o canteiro mostra o estágio.
- **A arte:**
  - o quadro, a barraca da feira, o tacho e a composteira;
  - os ícones dos produtos (geleia, molho, farinha, adubo) no inventário, como a lanterna;
  - a tempestade como um efeito, como a chuva.

  Desenho próprio no estilo LPC, ou download com o seu ok se eu achar um pacote que sirva.
- **Os rótulos e as métricas:**
  - "camps entregou a encomenda da Dona Cida: 4 milhos, 270 moedas";
  - as métricas do dia ganham as encomendas entregues e vencidas, as vendas na feira, o que o tacho fez e as moedas por canal (a caixa, a feira e as encomendas).

## 9. Os contratos

- **Um domínio novo, `economy`,** da plataforma, como `memory` e `llm`. É do módulo e não da fazenda, para o escritório usar os mesmos eventos:
  - `economy.order.posted.v1`, `economy.order.accepted.v1`, `economy.order.delivered.v1` e `economy.order.expired.v1`.
- **O tempo de amanhã:** `world.weather.changed.v1` ganha um campo opcional `forecast` (verdadeiro quando é a previsão). A condição já é um texto aberto (`token`), então `storm` e `drought` entram sem tipo novo (decisão 12).
- **O resto** é o que já existe: itens criados e consumidos, atributos, entidades. A planta derrubada pela tempestade é um evento do cartucho (`farm.crop.knocked_down.v1`), como o corvo do M16.

## 10. Testes do marco

- **O módulo, sozinho:**
  - o preço que cai e recupera;
  - o que sobe na compra e volta;
  - a estação;
  - a oscilação limitada;
  - os pedidos sorteados, aceitos, entregues e vencidos;
  - a reputação;
  - a agenda;
  - tudo determinístico pela seed.
- **A fazenda:**
  - cada ação nova com as suas recusas;
  - o tacho que termina sozinho;
  - a composteira;
  - a tempestade e a seca;
  - a feira aberta e fechada;
  - o determinismo e o replay na Morada do Sol.
- **A mente:** a fita de dois dias e o teste de palavras proibidas, para que a recuperação e a reputação não vazem no manual.
- **A tela:**
  - o menu do quadro e a previsão no Vitest;
  - no Playwright, aceitar e entregar uma encomenda na Morada do Sol pausada.
- **Soaks:**
  - um ano na Morada do Sol com o script 2 adaptado;
  - as fazendas 1 e 2 com os números de sempre.

## 11. Ordem do trabalho

1. O módulo `libs/economy` e a ADR, com os testes dele.
2. O mercado nos dois sentidos na Morada do Sol: a caixa, o quiosque, a estação e a oscilação.
3. As encomendas, os contratos do domínio `economy` e a reputação.
4. A feira.
5. O tacho, as receitas e a composteira.
6. O clima com previsão, a tempestade, a seca e a reação do mercado.
7. A mente (o manual, as ferramentas e a fita) e o script 2 adaptado.
8. A tela: o quadro, a previsão, a arte, os rótulos e as métricas.
9. Fechamento: a §13, a bíblia 3 atualizada, o diário, os custos e um print.

**Estimativa:** três a quatro sessões, o maior marco da v0.3 até aqui. **Custo de API:** a fita (uns US$ 0,05) e a corrida de verificação (uns US$ 0,15).

## 12. Decisões

1. **O módulo mora numa biblioteca, `libs/economy`,** usada pelos cartuchos, e não em primitivas do kernel. Com ADR. *Recomendação: sim. O kernel continua sabendo só a física (princípio 8): mercado, encomenda e feira são regras de um mundo. Com a biblioteca, o escritório usa o mesmo código sem que o kernel aprenda economia. Se um dia vários mundos precisarem do mercado no mesmo lugar, ele pode descer para o kernel.*
2. **O domínio `economy` nos contratos,** da plataforma, para os eventos das encomendas. *Recomendação: sim. O escritório vai publicar os mesmos eventos para os tickets, e a linha do tempo e as métricas já os leem.*
3. **O preço de venda com memória,** só na Morada do Sol: −2% por unidade vendida, piso de 40%, recuperação de um terço da distância por dia. *Recomendação: sim. É a oferta e a demanda de verdade: despejar uma colheita estraga o preço por dias, e diversificar passa a valer.*
4. **O preço de compra que sobe:** +3% por unidade da mesma semente no dia, de volta à tabela de manhã. *Recomendação: sim. Foi o pedido do outro sentido, e um dia basta: o quiosque se reabastece à noite.*
5. **A referência pela estação** (boa 1,0; fraca 1,25; parada 1,6) **e a oscilação do dia** (até 4% por dia, limitada a 15%). *Recomendação: sim. Guardar o que dura para vender fora da estação vira estratégia, e a oscilação faz valer olhar o preço antes de vender.*
6. **As encomendas** com os números da §3: até 4 abertas, até 2 aceitas, prazo de 3 a 7 dias, prêmio de 50%, pagamento na entrega. *Recomendação: sim. É o análogo dos tickets do escritório, e o pagamento na hora é o atrativo frente à caixa.*
7. **A reputação como regra oculta nova (R-004):** cumprir traz mais pedidos e prêmios maiores; falhar, menos. O manual só diz que os clientes lembram. *Recomendação: sim. Ela vale para todo mundo e é frequente (a v0.3 pede regras que não dependam de uma ação rara), e o efeito é visível no quadro. É uma regra fixa: só o mapa varia (ADR-0066).*
8. **A feira a cada 7 dias,** das 06:00 às 14:00, numa barraca na entrada da fazenda, a 30% acima da referência, pagando na hora. *Recomendação: sim. A caminhada e o horário fazem dela uma decisão, e ela dá destino aos produtos.*
9. **O tacho com as três receitas da §5,** comprado e fincado, trabalhando sozinho. *Recomendação: sim. É diferente do fogão: o fogão ocupa o avatar e faz comida, e o tacho trabalha sozinho e faz o que se vende.*
10. **A composteira:** o que estraga e as plantas murchas viram adubo em 3 dias. *Recomendação: sim, pequena. Usa a mesma mecânica do tacho e cumpre os "adubos" do plano macro sem um adubo novo.*
11. **O clima com previsão,** a tempestade e a seca com os números da §6, e o mercado reagindo por 3 dias. *Recomendação: sim. A previsão é a informação que um bom jogador usa (colher antes da tempestade), e a reação do mercado liga o clima à economia.*
12. **O tempo de amanhã no contrato:** um campo opcional `forecast` no `weather.changed.v1`, e as condições novas `storm` e `drought` no campo que já é texto aberto. *Recomendação: sim. É a mudança compatível que os contratos permitem (§6 dos princípios), sem tipo `v2`.*
13. **A mente:** o manual, as ferramentas novas, a fita regravada e uma corrida de verificação de 7 dias com o Haiku (uns US$ 0,20 no total). *Recomendação: sim. A fita prova que o pedido funciona; a corrida curta mostra se ele entende as encomendas antes da arena do M21.*
14. **O script 2 adaptado só no essencial:** encomendas da cultura que já planta e a colheita antes da tempestade; sem feira nem tacho. *Recomendação: sim. A linha de base continua cega, e o script 3 do M19 é quem planeja a economia.*
15. **A tela:** o menu do quadro com os pedidos vindos dos atributos, a previsão no HUD, o progresso do tacho, a arte própria (ou download com ok) e as métricas por canal. *Recomendação: sim.*

## 13. Como ficou

*(a preencher no fechamento)*
