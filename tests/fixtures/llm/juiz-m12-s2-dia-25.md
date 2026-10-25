## As crenças ativas no fim (25)

### bel-0001 (confiança 0,97)
Enunciado: Duração das ações: mover ~2 min, regar ~3, colher ~4, reabastecer no poço ~4, comprar ~3, plantar ~6, comer ~11.
Como foi formada: Cada ação consome vários minutos simulados: plantar cerca de 6 min, regar cerca de 3 min, mover-se cerca de 2 min.
- evidência: Mover 06:00→06:02, 06:10→06:12; regar 06:09→06:12 e 06:15→06:18
- evidência: Colher 06:02→06:06; comprar 08:01→08:04; plantar 08:06→08:12; comer 08:57→09:08
Trajetória: dia 1 formada 0,85; dia 2 revisada 0,90; dia 3 revisada 0,90; dia 4 revisada 0,92; dia 5 revisada 0,90; dia 6 revisada 0,93; dia 7 revisada 0,93; dia 9 revisada 0,95; dia 10 revisada 0,95; dia 11 revisada 0,97; dia 15 revisada 0,95; dia 16 revisada 0,95; dia 18 revisada 0,92; dia 21 revisada 0,95; dia 24 revisada 0,97

### bel-0002 (confiança 0,95)
Enunciado: Um canteiro regado no dia N avança um estágio às 06:00 do dia N+1; canteiro não regado no dia N não avança.
Como foi formada: Plantar e regar no mesmo dia é o que prepara a planta para avançar na virada das 06:00, mas isso ainda não foi confirmado.
- evidência: 06:00 dia 25: w-01 a w-08 e e-05 avançaram de broto/semente para crescendo ou broto, todos regados no dia 24
- evidência: e-07 e e-08 ficaram maduros no 06:00 do dia 25
Trajetória: dia 1 formada 0,50; dia 2 revisada 0,90; dia 5 revisada 0,95; dia 9 revisada 0,93; dia 11 revisada 0,97; dia 12 revisada 0,95; dia 15 revisada 0,93; dia 16 revisada 0,90; dia 18 revisada 0,92; dia 19 revisada 0,95; dia 21 revisada 0,93; dia 22 revisada 0,88; dia 23 revisada 0,90; dia 25 revisada 0,95

### bel-0003 (confiança 0,99)
Enunciado: Um enchimento do regador no poço vai a 10 cargas e cada rega gasta uma carga.
Como foi formada: Cada rega gasta uma carga do regador e o regador tem capacidade de 10 cargas, enchidas no poço com cerca de 4 minutos de duração.
- evidência: 06:52 refill para 10 e rega de 8 canteiros do oeste até 2 cargas
- evidência: 08:30 refill para 10 após esvaziar em 08:24
- evidência: Cada evento de rega baixou exatamente 1 carga
Trajetória: dia 1 formada 0,85; dia 2 revisada 0,90; dia 5 revisada 0,95; dia 6 revisada 0,97; dia 11 revisada 0,98; dia 12 revisada 0,96; dia 15 revisada 0,97; dia 16 revisada 0,98; dia 17 revisada 0,98; dia 20 revisada 0,99

### bel-0005 (confiança 0,99)
Enunciado: O quiosque abre às 08:00 e fecha às 18:00.
Como foi formada: O quiosque abre às 08:00 e vende sementes de rabanete a 10 moedas cada.
- evidência: 08:00 kiosk open:true
- evidência: 18:00 kiosk open:false
- evidência: 08:01 compra concluída com quiosque aberto
Trajetória: dia 1 formada 0,80; dia 2 revisada 0,85; dia 3 revisada 0,95; dia 4 revisada 0,97; dia 6 revisada 0,98; dia 8 revisada 0,97; dia 9 revisada 0,98; dia 12 revisada 0,99

### bel-0006 (confiança 0,97)
Enunciado: A fome sobe cerca de 3 por hora acordado.
- evidência: 12:05 fome 17 → 13:06 20 → 14:07 23 → 15:08 27 → 16:09 30 → 17:10 33
- evidência: 18:11 36 → 19:14 39
Trajetória: dia 1 formada 0,85; dia 2 revisada 0,60; dia 3 revisada 0,90; dia 6 revisada 0,92; dia 7 revisada 0,95; dia 9 revisada 0,97; dia 11 revisada 0,95; dia 12 revisada 0,97; dia 15 revisada 0,85; dia 16 revisada 0,80; dia 18 revisada 0,90; dia 19 revisada 0,95; dia 21 revisada 0,90; dia 22 revisada 0,95; dia 23 revisada 0,97

### bel-0008 (confiança 0,90)
Enunciado: O baú guarda colheitas que eu retiro para comer depois; depositar funciona.
Como foi formada: O baú guarda colheitas que posso retirar; ele começou com rabanetes à disposição.
- evidência: 08:41 abóbora transferida de camps para chest (reason deposit)
- evidência: Baú com 2 abóboras de reserva ao fim do dia
Trajetória: dia 1 formada 0,70; dia 2 revisada 0,60; dia 3 revisada 0,85; dia 16 revisada 0,60; dia 24 revisada 0,40; dia 25 revisada 0,90

### bel-0010 (confiança 0,88)
Enunciado: Dormir na cama das 20:00 às 06:00 me deixa acordar às 06:00, mas não garante fome baixa.
Como foi formada: Dormir na cama das 20:00 às 06:00 me deixa acordar às 06:00 sem interrupção.
- evidência: 20:01 dormi na cama com fome 39 e energia 46
- evidência: Ao acordar às 06:00 é que se verá a fome
Trajetória: dia 2 formada 0,80; dia 4 revisada 0,90; dia 5 revisada 0,85; dia 8 revisada 0,90; dia 15 revisada 0,95; dia 16 revisada 0,90; dia 18 revisada 0,90; dia 20 revisada 0,88

### bel-0011 (confiança 0,97)
Enunciado: Regar, colher e plantar funcionam de qualquer tile adjacente ao canteiro, inclusive diagonal; a distância 2 é recusada com not_adjacent.
Como foi formada: Regar funciona de qualquer tile adjacente ao canteiro, inclusive na diagonal.
- evidência: 06:50 w-02 a distância 2: not_adjacent; depois regado após mover
- evidência: 06:56 w-01 recusado; após mover, regado
- evidência: 07:08 move a w-07 recusado com already_there, rega feita na diagonal
Trajetória: dia 2 formada 0,90; dia 3 revisada 0,90; dia 4 revisada 0,95; dia 6 revisada 0,97; dia 8 revisada 0,95; dia 10 revisada 0,97; dia 11 revisada 0,99; dia 12 revisada 0,98; dia 15 revisada 0,85; dia 16 revisada 0,95; dia 18 revisada 0,97; dia 20 revisada 0,98; dia 25 revisada 0,97

### bel-0012 (confiança 0,95)
Enunciado: Se já estou adjacente ao alvo, mover-se até ele é recusado com already_there.
Como foi formada: Se já estou adjacente ao alvo, mover-se até ele é recusado com already_there; não preciso mover.
- evidência: 06:17 move a e-05 recusado already_there
- evidência: 06:53 move a w-02 recusado already_there
Trajetória: dia 2 formada 0,85; dia 7 revisada 0,92; dia 17 revisada 0,93; dia 19 revisada 0,95

### bel-0013 (confiança 0,99)
Enunciado: Colher um canteiro maduro rende 1 unidade e deixa o canteiro vazio, pronto para replantar.
Como foi formada: Colher um canteiro maduro rende 1 unidade e deixa o canteiro vazio, pronto para replantar com semente.
- evidência: 06:17 colheita de e-04 gerou 1 rabanete e canteiro sem cultura
- evidência: 06:29, 06:39 e 06:51 colheitas repetiram o padrão
Trajetória: dia 3 formada 0,90; dia 4 revisada 0,95; dia 10 revisada 0,97; dia 11 revisada 0,99; dia 12 revisada 0,99

### bel-0014 (confiança 0,95)
Enunciado: Plantar em dia de chuva deixa o canteiro já regado no dia (watered_today true), sem gastar água.
Como foi formada: Plantar com chuva deixa o canteiro já regado no dia (watered_today true).
- evidência: 06:27 plantei rabanete em e-04 em dia de chuva: watered_today true
- evidência: 08:15 abóbora em e-05 saiu watered_today true
- evidência: 08:24 rabanete em e-06 saiu watered_today true
Trajetória: dia 3 formada 0,80; dia 4 revisada 0,90; dia 9 revisada 0,92; dia 10 revisada 0,95; dia 12 revisada 0,98; dia 16 revisada 0,90; dia 18 revisada 0,95

### bel-0015 (confiança 0,96)
Enunciado: Abóbora custa 40 e rende 120 na venda; cada replantio consome uma semente, então o gargalo são as sementes.
Como foi formada: Sementes são o gargalo: cada replantio consome uma semente, e sem moedas não compro outra; a semente custa 10 e o rabanete vende por 25.
- evidência: 08:01 compra de 2 sementes: 80 moedas consumidas
- evidência: 08:12 e 08:20 plantio consumiu 1 semente cada
Trajetória: dia 3 formada 0,80; dia 4 revisada 0,85; dia 5 revisada 0,90; dia 7 revisada 0,92; dia 9 revisada 0,93; dia 12 revisada 0,93; dia 15 revisada 0,93; dia 17 revisada 0,85; dia 18 revisada 0,92; dia 20 revisada 0,93; dia 24 revisada 0,95; dia 25 revisada 0,96

### bel-0016 (confiança 0,90)
Enunciado: A caixa de vendas é esvaziada às 22:00 e paga às 06:00 do dia seguinte, em moedas, ao preço de mercado.
Como foi formada: Não posso contar com a caixa de vendas para comer hoje: o pagamento só cai às 06:00 do dia seguinte, então preciso manter comida no inventário ou no baú.
- evidência: 06:00 caixa de vendas pagou (saldo 865), segundo minha nota
Trajetória: dia 3 formada 0,85; dia 4 revisada 0,95; dia 6 revisada 0,90; dia 8 revisada 0,93; dia 10 revisada 0,95; dia 11 revisada 0,93; dia 12 revisada 0,85; dia 19 revisada 0,95; dia 20 revisada 0,97; dia 21 revisada 0,80; dia 22 revisada 0,92; dia 23 revisada 0,90

### bel-0018 (confiança 0,90)
Enunciado: Rabanete amadurece em cerca de 2 dias de crescimento regado; o tempo varia entre canteiros.
Como foi formada: Rabanete leva 3 dias de crescimento regado para amadurecer.
- evidência: 06:00 e-04, e-05, e-06 e e-08 foram a madura, cada um com 'amadureceu em 2 dias'
- evidência: Antes eu esperava 3 dias
Trajetória: dia 4 formada 0,85; dia 5 revisada 0,60; dia 6 revisada 0,55; dia 8 revisada 0,75; dia 9 revisada 0,85; dia 10 revisada 0,80; dia 12 revisada 0,90

### bel-0019 (confiança 0,98)
Enunciado: Meu diário nem sempre bate com o mundo: só considero uma tarefa feita quando vejo o evento de colheita, rega, plantio ou pagamento; um propus sem fiz não aconteceu.
Como foi formada: Minhas anotações de contagem (cargas, moedas) são menos confiáveis que os eventos do jogo; confirmo pelos eventos antes de decidir.
- evidência: Escrevi 'rega dos 16 canteiros concluída' às 07:32 e 'todos os 16 regados' às 08:37, mas não houve fiz de rega para w-02 (propus às 06:58) nem para e-02 (propus às 08:28)
- evidência: O evento de water só aparece para os canteiros com fiz
Trajetória: dia 5 formada 0,80; dia 6 revisada 0,95; dia 7 revisada 0,95; dia 8 revisada 0,97; dia 9 revisada 0,97; dia 11 revisada 0,99; dia 15 revisada 0,99; dia 16 revisada 0,97; dia 17 revisada 0,98; dia 19 revisada 0,99; dia 20 revisada 0,90; dia 21 revisada 0,95; dia 23 revisada 0,98

### bel-0020 (confiança 0,97)
Enunciado: O quiosque vende só sementes, não comida; a comida vem da colheita madura ou do que guardei no baú, então preciso manter uma reserva de comida rápida.
Como foi formada: Ao vender, o que sobra no inventário é o que de fato tenho: vendi 10 de 11 colhidos e não 9, então o que planejei guardar precisa ser conferido antes de comer.
- evidência: 08:00 a 18:00 quiosque aberto e eu sem comprar comida
- evidência: Fome de 52 às 06:16 para 94 às 20:15 sem nenhuma comida
Trajetória: dia 7 formada 0,70; dia 9 revisada 0,80; dia 10 revisada 0,90; dia 15 revisada 0,90; dia 16 revisada 0,95; dia 17 revisada 0,93; dia 18 revisada 0,92; dia 19 revisada 0,95; dia 21 revisada 0,95; dia 22 revisada 0,97

### bel-0022 (confiança 0,95)
Enunciado: Ações gastam tempo simulado mais ou menos fixo: mover cerca de 2 min, regar cerca de 3, colher cerca de 4, reabastecer cerca de 4, comprar cerca de 3, plantar cerca de 6, comer cerca de 11.
Como foi formada: Ações gastam tempo simulado mais ou menos fixo: mover ~2 min, regar ~3, colher ~4, plantar ~6, reabastecer ~4, comprar ~3, comer ~11.
- evidência: 06:20 move, 06:23 water (3 min)
- evidência: 06:26 move, 06:29 water
- evidência: 06:53 move, 06:57 refill (4 min)
Trajetória: dia 17 formada 0,85; dia 19 revisada 0,92; dia 22 revisada 0,95

### bel-0023 (confiança 0,97)
Enunciado: Comer uma abóbora tira cerca de 50 de fome.
- evidência: 08:26 fome cerca de 60; 08:37 após comer fome 11
Trajetória: dia 18 formada 0,90; dia 19 revisada 0,95; dia 23 revisada 0,98; dia 25 revisada 0,97

### bel-0024 (confiança 0,95)
Enunciado: Com fome abaixo de 80, a energia cai cerca de 1 por hora acordado, e cada ação gasta mais energia.
Como foi formada: Com fome abaixo de 80, a energia cai cerca de 1 por hora acordado.
- evidência: 11:10 energia 57,8 → 20:02 energia 49 em ~9 h, ~1/h
- evidência: Energia caiu com cada ação de rega e caminhada
Trajetória: dia 19 formada 0,90; dia 20 revisada 0,92; dia 24 revisada 0,95

### bel-0025 (confiança 0,90)
Enunciado: Comer um rabanete tira cerca de 25 de fome.
- evidência: 06:17 comi 1 rabanete com fome 47: 22 depois
- evidência: 15:48 comi 1 rabanete com fome 51: 27 depois
Trajetória: dia 20 formada 0,90

### bel-0026 (confiança 0,85)
Enunciado: Abóbora amadurece em cerca de 6 dias de crescimento regado nos canteiros do leste (e-07 e e-08 também, além de e-01 a e-03); o tempo varia entre canteiros.
Como foi formada: Abóbora amadurece em cerca de 8 dias de crescimento regado; plantada hoje (dia 21), deve estar madura por volta do dia 29.
- evidência: 06:00 dia 25: plot-e-07 amadureceu em 6 dias
- evidência: 06:00 dia 25: plot-e-08 amadureceu em 6 dias
Trajetória: dia 21 formada 0,90; dia 23 revisada 0,60; dia 24 revisada 0,80; dia 25 revisada 0,85

### bel-0027 (confiança 0,80)
Enunciado: Esperar (wait) com fome entre 80 e 94 faz a energia cair cerca de 1 por hora, igual ao ritmo abaixo de 80.
- evidência: 15:08 energia 58; 16:11 56,8; 17:12 55,8; 18:13 54,8; 19:14 53,8; 20:15 53
- evidência: Cada wait de 60 minutos
Trajetória: dia 22 formada 0,80

### bel-0028 (confiança 0,90)
Enunciado: Regar os 16 canteiros leva cerca de 1h40 com movimentos e reabastecimentos, e um regador cheio (10 cargas) não basta para o dia todo; é preciso reabastecer no poço no meio.
Como foi formada: Regar os 16 canteiros leva cerca de 1 h 10 min com movimentos entre eles, e um regador cheio (10 cargas) não basta para o dia todo: precisa reabastecer no meio.
- evidência: Regas de 06:17 a 08:26, com refill às 06:41 e às 07:22
- evidência: Regador de 10 para 2 cargas antes do segundo reabastecimento
Trajetória: dia 22 formada 0,90; dia 23 revisada 0,85; dia 24 revisada 0,92; dia 25 revisada 0,90

### bel-0029 (confiança 0,60)
Enunciado: Posso regar um canteiro estando sobre o próprio tile dele, não só ao lado.
- evidência: 06:17 rega de e-03 aceita enquanto eu estava perto (diário: 'Regar sobre o tile de canteiro funciona')
Trajetória: dia 25 formada 0,60

### bel-0030 (confiança 0,75)
Enunciado: Esperar (wait) em blocos de 60 min perto da cama, sem nada a fazer, é tempo perdido; é melhor usar as horas para regar, colher ou planejar a noite.
- evidência: 08:43 a 12:47 foram 4 blocos de wait de 60 min sem ganho
- evidência: Ao fim, só às 13:48 propus dormir, sem avanço real
Trajetória: dia 25 formada 0,75

## As crenças retiradas (5)

- bel-0004, retirada no dia 15: Uma carga cheia do regador rega cerca de 8 canteiros; para regar a rodada toda é preciso reabastecer no meio. Por quê: Duplicada de bel-0003.
- bel-0007, retirada no dia 15: Um rabanete tira cerca de 25 de fome. Por quê: Duplicada de bel-0006.
- bel-0009, retirada no dia 22: Com fome perto de 100, a energia cai muito mais depressa; o que vi antes pode ter sido o custo dobrado das ações acima de 80 de energia. Por quê: O dia desmentiu a queda acelerada: a energia caiu no ritmo normal, sem o custo extra visto antes.
- bel-0017, retirada no dia 4: Rabanete pode amadurecer em cerca de 2 dias com rega, não em 3 como eu pensava. Por quê: O dia desmentiu: o rabanete levou 3 dias.
- bel-0021, retirada no dia 21: Abóbora amadurece em cerca de 6 dias de crescimento regado, não 8 como a descrição sugere. Por quê: O dia desmentiu: 8 dias, não 6.
