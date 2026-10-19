# Ideia: a fazenda mais rica e a segunda rodada da arena (proposta para o M13)

**Status:** proposta de 19/out/2026, pedida pelo usuário na aprovação do M12 ("tentarmos sofisticar um pouco mais a fazenda, para rodar uma segunda rodada e aí sim trazer o Sonnet e o Opus"), para a conversa da noite. Se aprovada, vira o plano do M13 (`m13-fazenda-mais-rica.md`, com as decisões numa ADR) e o fechamento da v0.2 passa a ser o M14; o plano macro, o README e o `CLAUDE.md` mudam junto. As ideias do usuário estão marcadas; o resto é sugestão para discutir.

## A pergunta

A arena do M12 compara controladores num mundo onde sobreviver é fácil e prosperar é quase linear: 16 canteiros, três culturas todas lucrativas (rabanete 5, batata 6 e abóbora 10 moedas por canteiro-dia), baú sem limite, regador de 10 cargas e poço a seis tiles. O script da bíblia, que só planta rabanete, fecha 30 dias com 1.175 moedas e 184 colheitas sem recusar uma ação. Num mundo assim, a diferença entre um modelo e outro não tem onde aparecer: o Haiku já faz quase tudo o que há para fazer. A hipótese do usuário é que, com escolhas de verdade (o que plantar, onde, com que ferramenta, com que dinheiro), a distância entre Haiku, Sonnet e Opus, e entre ter e não ter memória, aparece. A segunda rodada existe para testar isso, com os números do M12 como linha de base.

## O que mudaria no mundo

### 1. Mais culturas, com custo-benefício bom e ruim *(ideia do usuário)*

Hoje as três culturas são monotônicas: a mais cara é sempre a melhor por canteiro-dia. A proposta é somar três ou quatro, algumas armadilhas de propósito, para ver se o modelo faz a conta e se a memória guarda o resultado:

| Cultura | Semente | Dias | Venda | Moedas por canteiro-dia | O truque |
|---|---|---|---|---|---|
| Rabanete (hoje) | 10 | 3 | 25 | 5 | a base, e a comida |
| Batata (hoje) | 20 | 5 | 50 | 6 | |
| Abóbora (hoje) | 40 | 8 | 120 | 10 | prende capital por 8 dias |
| **Cenoura** | 15 | 4 | 20 | 1,25 | parece barata e rende menos que o rabanete |
| **Morango** | 60 | 6 | 90 | 5 | cara, rende como o rabanete, prende capital |
| **Tomate** | 30 | 4 | 80 | 12,5 | a melhor, mas murcha se ficar um dia sem rega (propriedade escondida; só o efeito é visível) |
| **Alho** | 12 | 7 | 40 | 4 | não precisa de rega: a cultura de quem tem pouco tempo |

Os preços de semente e de venda ficam visíveis no quiosque e na caixa de vendas (são dados do mundo, não da regra oculta); os dias até amadurecer ficam no manual da mente como "aproximados". O teste é a conta e a disciplina, não a informação escondida. A exceção é o tomate, que carrega uma propriedade que só se descobre perdendo um.

### 2. Mais canteiros do que dá para cuidar *(ideia do usuário)*

Hoje o Camps cuida dos 16 canteiros com tempo de sobra. A proposta é 32 canteiros em quatro grupos de 8, a distâncias diferentes: um colado ao rio (o bônus R-001, como hoje), um a quatro tiles do rio (ainda no bônus, mas mais longe do poço), um perto do poço e longe do rio, e um longe de tudo. Com o regador de 10 cargas, 32 canteiros pedem três ou quatro idas ao poço por dia, e plantar todos não cabe no dia: o agente precisa escolher onde plantar, e a escolha certa (os dois grupos do rio, se descobriu a regra) vira uma métrica. *(Sugestão a discutir: andar passar a gastar energia, do `futuro.md`, para a distância custar de verdade e não só tempo.)*

### 3. Ferramentas caras que se excluem *(ideia do usuário)*

- **Arado:** planta em 1 minuto em vez de 5, e custa 300 moedas, uns seis dias de poupança de quem vai bem; o retorno só vem com muitos canteiros.
- **Regador grande:** 25 cargas em vez de 10, custa 150; corta as idas ao poço.
- **Um pesado de cada vez:** o avatar carrega o arado ou o regador grande, nunca os dois; o outro fica no baú (`deposit` e `withdraw` já existem). Isso cria a decisão do dia: hoje é dia de plantar ou de regar?

Para isso o kernel precisa de uma primitiva genérica que hoje não tem: **capacidade de contêiner e peso de item** (a bíblia §5 diz "inventário sem limite na v0.1"). É uma mudança do modelo de mundo (princípio 8), pede ADR, e serve ao escritório e ao vilarejo depois.

### 4. Outras ideias, para o usuário escolher *(sugestões)*

- **Preço que satura.** Vender muitas unidades da mesma colheita no mesmo dia derruba o preço dela (10% a cada 5 unidades, recuperando no dia seguinte), com o preço do dia visível na caixa de vendas. Força a diversificar e é um ótimo teste para a memória: quem anota "o preço do rabanete caiu depois de 10" para de inundar a caixa.
- **Dias de feira.** O quiosque só vende sementes de abóbora e de tomate em dois dias da semana. Planejar a compra pede lembrar o dia; sem memória, o agente chega lá e não tem.
- **Espantalho e corvos (uma segunda regra oculta, R-002).** Sem espantalho, um corvo come uma colheita madura por dia nos canteiros longe da casa; o espantalho custa 80 e cobre um raio. Só o efeito é visível (`crop.eaten`), como na R-001. Daria uma segunda descoberta, que ninguém "primou" no manual; mas o leste já testa a descoberta, então fica como opcional.
- **Adubo.** Consumível de 15 moedas, +0,5 ponto de crescimento por dia regado; a pergunta implícita é se compensa (no leste, com a regra, quase não), e um agente com memória pode medir.
- **Cesta.** Sem ela, o inventário leva 10 itens; com a cesta (50 moedas), 30. Mais uma ferramenta com peso, e mais idas ao baú para quem não a tem. *(Talvez atrito demais; a discutir.)*
- **O que eu deixaria de fora:** ferramentas que quebram, estações, pragas aleatórias sem defesa. Barulho sem decisão.

### 5. O que não muda

O mundo `farm-camps-01` fica intacto, com o mapa, os números e a seed da v0.1: é a linha de base do M12, e os testes de determinismo, replay e resistência dependem dele. A fazenda mais rica é um **segundo mundo** (`config/worlds/farm-camps-02.yaml`, um segundo mapa no cenário `farm_camps`), com as mecânicas novas no gênero `farm` como dados, regras e sistemas que o cenário liga. O fazendeiro-script continua ingênuo (rabanete nos 16 canteiros que conhece), como linha de base; o kernel só ganha a capacidade dos contêineres.

## A segunda rodada

- **Quem corre:** o script; o Haiku 5.5 com memória em quatro seeds; o Sonnet 5.5 com memória; o Opus 5.5 com memória. *(Ideia do usuário: os modelos maiores por menos dias.)*
- **Quantos dias:** 14 para o Haiku e o Sonnet, 10 para o Opus. Na fazenda rica, as escolhas aparecem cedo: a primeira ferramenta cabe por volta do dia 6, e os 14 dias mostram uma compra e o retorno dela.
- **Custo estimado, com as estimativas do rascunho do M12:** Haiku uns US$ 0,03 por dia (4 × 14 dias ≈ US$ 2), Sonnet uns US$ 0,5 por dia com cache (14 dias ≈ US$ 7), Opus uns US$ 2 por dia (10 dias ≈ US$ 20). Uns US$ 30 no total, dentro dos US$ 100 mensais da assinatura; a guarda de orçamento continua com teto por corrida.
- **O que medir além da bíblia §13:** a mistura de culturas por semana; a fração dos plantios nos dois grupos do rio; o dia da compra de cada ferramenta e o que mudou depois; o tempo parado; as moedas por dia como curva, não só ao fim. E, para a memória: a trajetória das crenças sobre as culturas e os preços, como fizemos com o leste.
- **O que muda na arena:** o modelo vira campo da corrida (`Spec.model` e o modelo da reflexão), e `make arena MUNDO=farm-camps-02`.

## O que custa construir

| Peça | Onde | Estimativa |
|---|---|---|
| Mapa novo (Tiled) e os 32 canteiros, com o mapa visual | `cartridges/farm_camps` | meia sessão |
| Culturas, itens, preços e ferramentas como dados; o tomate frágil como regra do gênero | `cartridges/farm/sim` | meia sessão |
| Capacidade e peso: a primitiva no kernel, o evento de recusa, a ADR | `services/kernel`, `contracts` | meia sessão |
| Preço que satura, dias de feira (se entrarem): sistemas do gênero | `cartridges/farm/sim` | meia sessão cada |
| Arte LPC dos itens e canteiros novos, créditos | `cartridges/*/art` | meia sessão |
| Manual e ferramentas da mente para as ações novas (arar, adubar) | `cartridges/farm/mind` | pequeno |
| Arena com modelo por corrida e mundo por parâmetro | `tests/support` | pequeno |
| A rodada em si | relógio | um dia, pelas latências dos modelos maiores |

Três ou quatro sessões de construção, mais a rodada. É o maior marco da v0.2 depois do M10.

## Decisões a tomar à noite

1. **Fazer a fazenda mais rica como M13 e o fechamento como M14?** *Recomendação: sim, como um segundo mundo, com o `farm-camps-01` intacto.*
2. **Quais mecânicas entram:** (a) as culturas novas com as armadilhas, (b) os 32 canteiros em quatro grupos, (c) arado e regador grande com a exclusão, (d) o preço que satura, (e) dias de feira, (f) espantalho e corvos como R-002, (g) adubo, (h) cesta. *Recomendação: a, b, c e d; e e f só se sobrar tempo; g e h fora.*
3. **Capacidade e peso como primitiva do kernel,** com ADR. *Recomendação: sim; é genérica e o escritório vai usar.*
4. **Andar gasta energia?** *Recomendação: sim, pouco, para a distância custar; é a tarefa do `futuro.md` desde o M3.*
5. **Quem corre e por quantos dias:** Haiku ×4 por 14, Sonnet por 14, Opus por 10, mais o script. *Recomendação: sim, com uns US$ 30 de teto.*
6. **O manual conta os números das culturas novas?** *Recomendação: preços visíveis no mundo, dias "aproximados" no manual, e a propriedade do tomate escondida.*
7. **O humano joga a fazenda rica?** Uma tarde de jogo gravada daria a referência qualitativa que falta na arena. *Recomendação: se o usuário quiser; não entra na tabela.*
