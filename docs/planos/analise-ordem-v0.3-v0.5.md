# Análise: a ordem da fazenda sofisticada, do escritório e do estúdio

*Escrita em 20/out/2026, no fechamento do M14, a pedido do usuário, que já decidiu trocar a v0.3 do escritório para uma fazenda mais sofisticada e pediu a confirmação da melhor ordem entre os três mundos. A decisão fica na ADR-0064.*

## Os três mundos

| | A fazenda sofisticada | O escritório que constrói a si mesmo | O estúdio do podcast |
|---|---|---|---|
| **O que é** | a Boa Vista com mais decisões: canteiros sem teto, estações, encomendas, processamento, exploração, vários avatares e um script que planeja e experimenta | um ou dois agentes que recebem tickets, abrem PRs no próprio Campsverso, esperam o CI e fazem o mundo reiniciar na versão que escreveram (ADR-0055) | papéis (pauta, pesquisa, roteiro, gravação, edição, publicação) produzindo episódios, primeiro simulados e depois ligados ao pipeline real |
| **Onde vive o efeito de uma ação** | dentro do kernel (estado do mundo) | fora: git, CI, PR | fora: textos, áudio, publicação |
| **Determinismo** | total: o mundo é função da seed e das propostas | o mundo sim; o trabalho das "mãos" não (gravado como fita) | o mundo sim; a produção não (gravada) |
| **Como se mede** | números objetivos: moedas, colheitas, descobertas, custo | semiobjetivos: tickets entregues, CI verde na primeira, rodadas de revisão, intervenções humanas, custo por ticket | subjetivos em boa parte: qualidade do episódio, aderência à pauta; objetivos só o prazo e o custo |
| **Custo de um experimento** | centavos a dezenas de dólares por rodada, com teto por corrida | dólares e dezenas de minutos por ticket | dólares por episódio, mais as ferramentas de mídia |
| **Risco** | baixo: nada sai do processo | alto: agentes mexendo no repositório, governança, segredo, CI | médio a alto: conteúdo público, direitos, voz |
| **O que a tela mostra** | o trabalho é visível (cavar, plantar, colher) | o trabalho é invisível (um dev digitando); precisa de lousa, quadro, balões | idem, com a cabine "no ar" e a pauta |

## O que os três têm em comum

O núcleo já serve aos três e não muda: o kernel com relógio, entidades, ações, necessidades e regras; cartuchos em camadas (gênero e cenário); a percepção; a mente com cartão, catálogo e memória; a porta de modelo com fita e medidor; a guarda de orçamento; a arena e as métricas declaradas pelo cartucho; a tela com a arte LPC; e o arquivo de eventos.

E todos os três pedem coisas que ainda não existem:

| Pendência | Fazenda | Escritório | Estúdio |
|---|---|---|---|
| **Vários avatares fora do kernel** (percepção, posse no gateway, tela) | dois fazendeiros, ou um ajudante contratado | dev e revisor | três a cinco papéis |
| **Remover uma entidade** (primitiva e evento) | o canteiro que volta a ser grama, o animal vendido | o ticket fechado, o ajudante dispensado | a pauta descartada |
| **Assistir na tela o que rodou em processo** (replay em modo contínuo) | as corridas da arena | uma noite de tickets | um episódio |
| **Pedidos de fora com prazo e preço** | encomendas de clientes | tickets | pautas |
| **Rótulos de eventos legíveis** na linha do tempo | "colheu 3 abóboras" | "abriu o PR #41" | "gravou o bloco 2" |
| **Memória com relevância** quando o bloco crescer | 30 dias e muitas regras | um repositório inteiro | um arquivo de episódios |
| **Um baseline não LLM** para comparar | o script que planeja e experimenta | um "dev-script" que só roda lint e testes | um pipeline fixo |
| **A porta de efeitos externos** (a "oficina") | não | sim, é o centro | sim, a mesma |
| **Outro modelo de tempo** (duração "até", tick mais curto, relógio ancorado) | não | sim | sim |
| **O cliente por chat** | opcional (o dono pede uma encomenda) | sim | sim |
| **Supervisor de versões** | não | sim | não |

A tabela mostra uma escada: a fazenda pede o que é comum aos três e roda inteira dentro do mundo; o escritório pede, além disso, a porta externa, o tempo novo e o supervisor; o estúdio reaproveita a porta e o tempo do escritório e acrescenta mídia e conteúdo público.

## As três ordens

### A. Fazenda (v0.3) → escritório (v0.4) → estúdio (v0.5)

**Prós**
- Aproveita o embalo e o achado ainda fresco: a arena, as métricas e a pergunta que a Boa Vista deixou aberta (ninguém explorou o rio).
- Constrói as pendências comuns (vários avatares, remover entidade, replay na tela, encomendas como "tickets", memória com relevância) num mundo determinístico, barato de testar e sem risco. O escritório já nasce sobre elas.
- Gradiente de risco e de medição: do objetivo e reproduzível para o externo e subjetivo.
- Gera resultados publicáveis cedo (LLM contra script, famílias de modelos, descoberta de regras), bom material para o projeto em público.

**Contras**
- Adia o mais original dos três, o mundo que se constrói.
- A fazenda tende a crescer sem fim; precisa de um corte claro.
- Não constrói a porta externa, que é o que o escritório e o estúdio mais precisam.

### B. Escritório (v0.3) → fazenda (v0.4) → estúdio (v0.5)

**Prós**
- O ciclo mais ambicioso primeiro; a porta externa sai cedo e o estúdio se apoia nela.
- *Dogfooding*: os primeiros tickets do escritório poderiam ser as tarefas da fazenda sofisticada.

**Contras**
- Começa pelo mais caro e arriscado (dólares por ticket, governança, agentes no repositório), sem as pendências comuns prontas: vários avatares, replay na tela e memória com relevância teriam de ser feitos no meio do caminho, sob mais pressão.
- Agentes de código ainda completam uma fração das tarefas em ambientes como o TheAgentCompany; tickets reais da fazenda seriam lentos e caros no começo.
- Perde o embalo da arena; o achado da Boa Vista fica parado uma versão.

### C. Estúdio primeiro

**Prós**
- É o mundo mais ligado a um uso pessoal concreto (o podcast).

**Contras**
- Depende da porta externa, que ninguém construiu ainda; mistura num só passo a porta, o tempo novo, a mídia e o conteúdo público.
- É o mais difícil de avaliar com números; sem baseline claro.
- O menor reaproveitamento do que acabou de ser feito.

## Recomendação

**A ordem A**: a fazenda sofisticada na v0.3, o escritório na v0.4 e o estúdio na v0.5; o mundo com memória completa e camada social anda para a v0.6 em diante. Ela confirma a decisão do usuário e acrescenta dois cuidados:

1. **A fazenda constrói de propósito as pendências comuns**: vários avatares, a primitiva de remover entidade, o replay na tela, encomendas com prazo (o análogo dos tickets), rótulos de eventos e, se o bloco pedir, memória com relevância. Assim a v0.4 começa pelo que é dela (a porta externa, o tempo e o supervisor).
2. **A fazenda tem corte**: um número fechado de marcos (o plano propõe sete, M16 a M22, com o fechamento), com o que ficar de fora indo para uma fazenda 4 no `futuro.md`, e não para dentro da v0.3.

A ordem B só valeria se o objetivo principal fosse ver o ciclo de autoconstrução o quanto antes, aceitando custo e risco maiores; a C, se o podcast tivesse prazo.
