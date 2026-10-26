# Plano do M20 — Os ajudantes

*Proposto em 26/out/2026, depois do agricultor treinado (ADR-0071). É o marco dos vários avatares da v0.3 (ADR-0066, decisão 10; o plano macro, §8, decisão 14): cinco personagens contratáveis, cada um com a sua ficha, que trabalham para quem os contrata. A proposta das fichas está no diário de 21/out. Aprovado em 26/out/2026 (ADR-0072), com as notas do usuário no fim da §11.*

**Pronto quando:**
- **Na Morada do Sol há cinco ajudantes,** cada um com uma ficha (nome, especialidade, um ponto bom e um ruim) e uma diária.
- **O Camps contrata, dá ordens e dispensa,** qualquer que seja o controlador: o humano pela tela, o script 3 pela conta do dinheiro, e o LLM pelas ferramentas.
- **O ajudante é um script que obedece às ordens** de quem o contratou: chega de manhã, trabalha, come da comida da fazenda e vai para casa no fim do dia.
- **A plataforma tem vários avatares de ponta a ponta:** o kernel, a percepção, o runner, o NATS, o gateway, a tela e a medição. Cada avatar vê só o que está à volta dele.
- **O critério do plano macro:** um ajudante contratado trabalha um ano, sem conflito e com replay.
- **As fazendas 1 e 2 ficam intactas,** com as mesmas fitas e os mesmos soaks.

## O que o levantamento mostrou

Mapeei o código atrás de tudo o que supõe um avatar só.

- **O kernel já lida com N avatares:**
  - cada avatar tem o seu controlador, as suas necessidades e a sua posse;
  - o lockstep espera qualquer avatar que deve uma decisão;
  - o snapshot guarda os avatares que estão no estado.
- **Em volta do kernel, tudo é do `camps`:**
  - as permissões do NATS (`agent.camps.>` no runner, na mente e no gateway);
  - o gateway (`AVATAR = "camps"`, um humano só, a boas-vindas com um avatar);
  - a tela (a câmera presa no Camps, os textos "Camps", a arte de um avatar só);
  - o runner, com um avatar por processo e os scripts como instâncias únicas do módulo, que não servem a dois avatares;
  - as métricas e o pipeline de testes.
- **Nada adiciona nem remove um avatar no meio da corrida.**
  - `spawn` cria a entidade, mas não o avatar com as necessidades e o controlador.
  - `despawn` recusa avatares.
  - A ADR-0055 já tinha escolhido o caminho: um agente novo entra como dado, e o mundo começa com ele.
- **A velocidade, o ritmo das necessidades e a capacidade valem para o mundo inteiro.** As fichas pedem esses números por avatar.
- **Há dois furos que um segundo avatar abriria:**
  - a percepção mostra o inventário de outro avatar que esteja à vista;
  - a caixa de vendas paga a quem vendeu por último, e não a cada vendedor.
- **A visão do jogador ainda recebe o mundo inteiro** pelo WebSocket. Filtrar no gateway ficou para o M20 (o diário de 24/out). A rodada do humano no M21 precisa disso para ser justa.
- **Os jogos de fazenda mostram dois modelos de ajudante:**
  - em Harvest Moon (Back to Nature), cada ajudante faz uma tarefa só (colher, regar, cuidar dos animais), contratado por 1, 3 ou 7 dias ([wiki](https://harvestmoon.fandom.com/wiki/Harvest_Sprites_(BTN)));
  - em Stardew Valley, os Junimos colhem só em volta da cabana e esbarram em obstáculos ([guia](https://www.bisecthosting.com/zh-cn/blog/stardew-valley-junimo-hut-guide-how-to-get-harvesting-layout)).

  Ordens simples, por tarefa, e um contrato por dias são o que um jogador entende rápido.
- **A economia tem as peças:** a agenda (`Recurring`), as encomendas com quem as pegou, e transferir moedas.

## 1. Os ajudantes como dados do cenário

- **Os cinco são avatares declarados pelo cenário,** fora da fazenda enquanto ninguém os contrata.
  - Não há avatar novo no meio da corrida: a ficha é dado, como a ADR-0055 pediu para os agentes do escritório.
  - O kernel ganha a presença do avatar. Fora da fazenda, o avatar não está no mapa, não recebe pedido de decisão e não segura o relógio. Entrar e sair são operações do mundo, com evento.
  - O snapshot, o replay e as permissões do NATS ficam simples, porque os avatares são sempre os mesmos.
- **O quadro de ajudantes** fica junto ao quadro de encomendas, na entrada da fazenda. Ele mostra quem está livre, a ficha e a diária.
- **As fichas** (a proposta de 21/out, com os números do ruim e do bom; as diárias são calibradas no §4):

| Nome | Especialidade | O bom | O ruim |
|---|---|---|---|
| Dita | a plantadeira | planta e colhe na metade do tempo | anda devagar: cada passo leva o dobro |
| Zé Graúdo | o carregador | carrega o dobro e cava mais rápido | come o dobro: a fome sobe duas vezes mais rápido |
| Nina | a batedora | vê o dobro do raio e enxerga à noite | cansa rápido (50% mais energia) e não carrega ferramenta pesada |
| Seu Bento | o veterano | faz tudo 20% mais rápido e não desmaia | a diária mais cara, e só trabalha das 8h às 16h |
| Tião | o aprendiz | a diária mais barata | faz tudo 50% mais devagar e perde uma semente em cada dez plantios |

- **Os traços são modificadores genéricos do avatar no kernel:** a velocidade, a duração das ações, o gasto de energia, o ritmo das necessidades, a capacidade e o "não desmaia". O kernel não sabe o que é uma plantadeira (princípio 8).
  - O raio e a noite entram na regra de percepção (ADR-0068), como a lanterna.
  - A semente perdida do Tião é uma regra do cenário, com RNG nomeado.

## 2. O contrato e o dia do ajudante

- **Contratar:** no quadro, por 1, 3 ou 7 dias, pago adiantado. O ajudante chega na manhã seguinte.
- **Dispensar:** a qualquer hora. Ele termina a ação, vai embora, e os dias pagos não voltam.
- **O dia:**
  - chega pela entrada às 06:00 (Seu Bento, às 08:00);
  - vai embora às 18:00 (Seu Bento, às 16:00);
  - dorme e janta em casa, então chega com as necessidades zeradas.
- **A comida:** no trabalho, com a fome em 60, ele come do baú da fazenda. Sem comida no baú, vai para casa mais cedo, e o dia está perdido. É o custo que o Zé Graúdo dobra: quem contrata planeja a comida.
- **As ordens** são um conjunto fechado de tarefas, dadas ao lado do ajudante, como qualquer ação: mandar custa tempo, e a corrida mede a gestão.
  - **cuidar** (o padrão): regar os canteiros que precisam e colher o que está maduro, guardando no baú;
  - **regar,** **colher** ou **plantar** (a semente do baú, a cultura escolhida), nos canteiros dados ou em todos;
  - **cavar** n canteiros em volta de um ponto;
  - **vender** o que está no baú, na caixa;
  - **parar.**

  A ordem fica até ser trocada. Ela é um atributo do ajudante que quem está perto vê.
- **O dinheiro:** o que o ajudante vende vai para quem o contratou. Isso conserta a caixa, que passa a pagar a cada vendedor, ou ao patrão de quem vendeu.

## 3. O ajudante é um script

- **O fazendeiro-ajudante** tem a percepção dele, como qualquer avatar, e faz o que a ordem diz.
  - Usa o que o script 2 já sabe: andar, regar, colher, a lembrança e o caminho.
  - Não decide o que plantar nem quando vender.
  - Não sabe nenhuma regra oculta.
- **O runner** passa a servir vários avatares num processo, uma instância do script por avatar. Os scripts deixam de ser instâncias únicas do módulo e passam a ser fábricas.
- **O ajudante LLM** fica para a arena do M21, como variável. A plataforma já permite qualquer controlador por avatar.

## 4. Quem contrata

- **O humano,** pela tela:
  - o quadro de ajudantes no menu do clique direito;
  - o menu do ajudante para dar a ordem ou dispensar;
  - os ajudantes no HUD, com a ordem e o que estão fazendo.
- **O script 3:**
  - contrata pela conta: quando os canteiros que ele não dá conta de cuidar valeriam mais que a diária, com o caixa da diária fora da reserva da comida;
  - escolhe a ficha pelo custo-benefício e dá a ordem "cuidar";
  - o oráculo é o mesmo código.
  - O script 2 nunca contrata: continua a linha de base cega.
- **O LLM:**
  - ferramentas novas: contratar, ordenar e dispensar;
  - o manual da Morada do Sol conta o quadro, as fichas, o contrato e as ordens; as fichas são públicas;
  - a fita da Morada do Sol é regravada.
- **A diária é calibrada pelo oráculo:** com um ajudante, ele só ganha mais do que sozinho a partir de uns 20 canteiros. Contratar por impulso dá prejuízo, como o plano macro pediu. A faixa esperada vai de umas 20 moedas (o Tião) a umas 70 (o Seu Bento).
  - **A medida (ADR-0073):** o Camps trabalha umas 2 das 16 horas, e nem ações mais longas deram valor ao ajudante. As diárias ficam, o ajudante vira um teste de julgamento, e a conta do script 3 não contrata.

## 5. A plataforma com vários avatares

- **O kernel:**
  - a presença do avatar (entrar, sair), com eventos novos no contrato;
  - os traços por avatar;
  - quem é o patrão de cada ajudante: só o controlador do patrão dá ordens, e só o script do ajudante o controla, com o humano e o operador limitados como hoje.
- **A percepção:**
  - uma entrega por avatar presente;
  - o inventário de outro avatar deixa de aparecer, e só os contêineres da fazenda (o baú, a caixa) continuam à vista.
- **O NATS:** um usuário por avatar, gerado da lista de avatares do mundo, para o runner dos ajudantes ver só os ajudantes (princípio 5).
- **O gateway:**
  - recebe os fatos de todos os avatares para o operador;
  - **a visão do jogador passa a ser a percepção do avatar dele:** o que o Camps vê e lembra, e não mais o mundo inteiro;
  - a tela de assistir passa a mostrar todos os avatares.
- **A tela:**
  - a câmera segue o avatar possuído, escolhido depois da boas-vindas;
  - os ajudantes desenhados, com a arte de cada ficha;
  - os textos sem "Camps" fixo;
  - o clique no ajudante abre o menu dele.
- **A arte:** cinco personagens LPC, montados com peças do gerador de personagens LPC, com os créditos. Dita e Nina pedem a base feminina, que não está no repositório: baixar as peças pede a sua permissão. A alternativa são variações de cor do Camps.

## 6. A medição

- **As métricas por avatar:** ações, colheitas, desmaios e fome de cada um.
- **Os ajudantes:** as diárias pagas, a comida que comeram, o que fizeram por ordem, as recusas de conflito (dois avatares no mesmo canteiro).
- **O relatório da arena** ganha "os ajudantes": quanto cada contratação rendeu menos o que custou.
- **A rodada de verificação**, de graça: o script 3 e o oráculo, com e sem ajudante, nos mapas a e b. Mais uma corrida do Haiku com os ajudantes, se você quiser, por uns US$ 0,80.

## 7. Os contratos

- O kernel: a entrada e a saída do avatar na fazenda.
- O cenário: contratar, dispensar e dar a ordem, no domínio do cartucho.
- O `realtime`: a boas-vindas passa a dizer qual é o avatar do jogador e quem são os outros.
- Nada muda de forma incompatível: campos opcionais e tipos novos.

## 8. Testes do marco

- **O kernel:**
  - um avatar fora da fazenda não segura o relógio nem recebe pedido;
  - entrar e sair passam pelo snapshot e pelo replay;
  - os traços mudam a duração, o gasto e o ritmo;
  - dois avatares no mesmo canteiro no mesmo tick: o segundo é recusado pela ordem dos ids, sempre igual.
- **A percepção:** cada avatar vê o próprio inventário e não o do outro; a Nina vê o dobro do raio e de noite.
- **O NATS:** o runner dos ajudantes não lê a percepção do Camps.
- **O cenário:**
  - o contrato, o pagamento e a dispensa;
  - o dia (a chegada, a saída, a comida do baú, a ida mais cedo sem comida);
  - cada ordem;
  - a semente do Tião;
  - a venda que paga ao patrão.
- **O ajudante:** obedece a cada ordem e nunca age sem ordem.
- **O critério do marco:** um ano da Morada do Sol com o script 3 contratando, sem travar, com as recusas esperadas, e o replay de um dia com dois avatares igual ao arquivo.
- **O de sempre:**
  - os soaks das fazendas 1 e 2 (1.175 e 220);
  - as fitas das fazendas 1 e 2 sem regravar;
  - o `make check`, o `make ui-e2e` e o CI.

## 9. Ordem do trabalho

1. **O kernel:** a presença do avatar, os traços e o patrão, com os contratos.
2. **A percepção e o NATS** por avatar, e o pipeline de testes com vários avatares.
3. **O runner com fábricas de script** e o fazendeiro-ajudante.
4. **O cenário:** as fichas, o quadro, o contrato, o dia, as ordens e a caixa que paga a cada um.
5. **O script 3 que contrata,** e o critério do marco, o ano com um ajudante.
6. **O gateway e a tela:** a visão do jogador pela percepção, os menus, o HUD e a câmera. A arte entra aqui, com a sua permissão para baixar as peças.
7. **A mente:** as ferramentas, o manual e a fita.
8. **A medição** e a rodada de verificação.
9. **O fechamento:** a bíblia 3, o diário, as sessões e os custos.

Cada passo vira um ou mais commits, com `make check` antes de cada um e um push por passo com o seu ok.

## 10. Custo

- **API:** centavos. A fita da Morada do Sol custa uns US$ 0,04, e a corrida do Haiku com ajudantes, se você quiser, uns US$ 0,80.
- **Desenvolvimento:** é o marco mais largo da v0.3, porque toca todos os serviços e a tela. Deve levar de três a quatro sessões.

## 11. Decisões

1. **Os ajudantes são avatares declarados pelo cenário,** fora da fazenda até a contratação, e o kernel ganha a presença do avatar (entrar e sair). *Recomendação: sim. Segue a ADR-0055 (agente novo entra como dado), e o snapshot, o replay e o NATS ficam simples. Criar avatares no meio da corrida pediria mais do kernel sem ganho para a fazenda.*
2. **O ajudante é um script que obedece às ordens;** o ajudante LLM fica para o M21, como variável da arena. *Recomendação: sim. É a recomendação de 21/out: a corrida mede a gestão de quem contrata, e o custo fica numa mente só.*
3. **O contrato:** no quadro de ajudantes, por 1, 3 ou 7 dias, pago adiantado, sem devolução ao dispensar. *Recomendação: sim. É o contrato de Harvest Moon; pagar adiantado evita dívida, e quem contrata assume o risco.*
4. **As ordens:** um conjunto fechado de tarefas (cuidar, regar, colher, plantar, cavar, vender, parar), dadas ao lado do ajudante, e a ordem fica até ser trocada. *Recomendação: sim. Mandar de perto custa tempo, como qualquer ação, e é isso que torna a gestão mensurável; ordens livres em texto pediriam um ajudante LLM.*
5. **As fichas de 21/out,** com os traços como modificadores genéricos do avatar no kernel, o raio na regra de percepção e a semente do Tião como regra do cenário; as diárias calibradas pelo oráculo. *Recomendação: sim. O kernel continua sem saber o que é uma fazenda (princípio 8).*
6. **O dia do ajudante:** chega às 06:00 e sai às 18:00 (o Seu Bento, das 08:00 às 16:00), come do baú da fazenda e vai embora mais cedo sem comida, e dorme em casa. *Recomendação: sim. A comida do ajudante é um custo que quem contrata precisa planejar, e é o que dá sentido ao ruim do Zé Graúdo.*
7. **Cada avatar vê só o que está à volta dele:**
   - sem visão compartilhada;
   - o inventário do outro não aparece;
   - um usuário do NATS por avatar.

   *Recomendação: sim. É o princípio 5 com mais de um avatar; o patrão sabe do ajudante o que vê, como um fazendeiro de verdade.*
8. **A visão do jogador vira a percepção do avatar dele, no gateway;** o operador continua vendo tudo. *Recomendação: sim. Foi adiado do M17 para cá, e a rodada do humano no M21 só é justa assim.*
9. **O script 3 contrata pela conta do dinheiro,** o oráculo é o mesmo código, e o script 2 nunca contrata. *Recomendação: sim. O script 2 continua a régua cega das rodadas anteriores.*
10. **A mente ganha as ferramentas e o manual dos ajudantes** só na Morada do Sol, com a fita regravada. *Recomendação: sim. As fichas são públicas; as fazendas 1 e 2 não mudam.*
11. **A arte:** cinco personagens montados com peças do gerador LPC, baixadas com a sua permissão na hora, com os créditos. *Recomendação: sim. Dita e Nina pedem a base feminina; variar a cor do Camps fica como plano B.*
12. **A medição e a verificação:** métricas por avatar, a seção dos ajudantes no relatório, e o script 3 e o oráculo com e sem ajudante nos mapas a e b, de graça. *Recomendação: sim. A corrida do Haiku com ajudantes fica opcional (uns US$ 0,80), à sua escolha.*
13. **O critério do marco:** um ano com o script 3 contratando, sem travar, com as recusas esperadas e o replay de um dia com dois avatares. *Recomendação: sim. É o critério do plano macro em forma de teste.*

**As notas do usuário na aprovação (26/out):**
- **2:** o ajudante é um script por enquanto, porque os scripts vão melhor que os modelos; no futuro, o Haiku, quando os modelos simples forem bem.
- **6:** das 6 às 18, e pode haver exceção (o Seu Bento).
- **7:** são personagens independentes.
- **11:** eu monto a arte, e o usuário ajusta depois, se precisar.
- **13:** testar contratar por 1, 3 e 7 dias, e conferir a calibragem: com o ajudante, o resultado deve ser melhor do que sem.
- **A decisão 10** (a mente) ficou sem resposta e segue a recomendação.
- **Sem push por enquanto:** os commits vão para o GitHub no fim do dia.
