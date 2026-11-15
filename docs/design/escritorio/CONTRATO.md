# Contrato `campsverso.escritorio/1`

O escritório lê dois arquivos JSON em `dados/` e não inventa nada além deles. A regra é a mesma do estúdio do CampsCast: **leia, não invente**.

- **Balões.** Todo balão do expediente é um evento do JSON e mostra a origem dele.
- **Fora do expediente.** O Vigia só lê a agenda e os números do dia, e o balão diz que é isso.
- **Movimento.** Andar, piscar e girar a roda são só animação. Não afirmam nada sobre o trabalho.

| Arquivo | O que tem | Muda quando |
|---|---|---|
| `equipe.json` | o escritório, a equipe, a aparência de cada um e as mesas vagas | alguém entra na equipe |
| `dia-demo.json` (depois, `ultimo.json`) | um dia de trabalho: tickets, PRs, eventos | todo dia útil |

## `equipe.json`

```jsonc
{
  "contrato": "campsverso.escritorio/1",
  "demonstracao": true,                 // a página mostra o selo "Demonstração"
  "escritorio": {
    "nome": "Escritório CampsVerso", "sigla": ">CV", "fuso": "America/Sao_Paulo",
    "expediente": { "abre": "08:40", "fecha": "18:00", "almoco": ["12:30", "13:30"] },
    "dias_uteis": [1, 2, 3, 4, 5],      // 0 = domingo
    "folgas": { "2026-11-15": "Proclamação da República" }
  },
  "equipe": [{
    "id": "revisor", "nome": "Revisor", "tipo": "robo",        // "robo" | "humano"
    "papel": "Revisão e testes", "faz": "…", "por_tras": "…",
    "posto": "m2",                       // m1..m6 (mesas), "deploy", "doca", "tubo", "portaria"
    "desde": "2026-11-06", "situacao": "ativo",
    "modelo": "…", "ferramentas": ["…"],
    "visual": { "corpo": "pernas", "cor": "#c04fa8" }
  }],
  "vagas": [{ "mesa": "m3", "para": "Designer de interface", "previsto": "dezembro de 2026" }]
}
```

**Corpos que já têm desenho:**

- `humano`: aceita `pele`, `cabelo`, `estilo` (`curto`, `raspado`, `bagunca`, `longo`), `barba`, `calca`, `sapato` e `acessorio` (`bone`).
- `pernas`: aranha com lupa.
- `rodas`: monociclo com formulário contínuo.
- `drone`: quadricóptero com disquete.
- `tubo`: mora no tubo pneumático.

**Um robô novo entra sem código.** Basta um item novo em `equipe` com um desses corpos, uma `cor` e um `posto` numa mesa livre. A mesa perde o lençol e o desenho sai na cor dele. Se o dia tiver um evento `chegada` dele, ele entra pela porta da rua nessa hora.

**Mesas vagas.** Ficam cobertas por um lençol.

- `vagas[].para` preenchido: a etiqueta diz RESERVADA.
- `vagas[].para` vazio: a etiqueta diz VAGA.
- Mesa cujo dono só chega mais tarde no dia: também aparece RESERVADA.

## `dia-demo.json`

```jsonc
{
  "contrato": "campsverso.escritorio/1",
  "demonstracao": true,
  "data": "2026-11-06", "dia_numero": 3,
  "sprint": { "nome": "Sprint 1", "objetivo": "…", "spec": { "titulo": "…", "itens": ["…"] } },
  "limites": { "custo_usd": 5.0, "cafes": 5 },      // a barra de custo só existe porque o limite está aqui
  "tickets": [{ "id": 11, "titulo": "Validação de CPF", "estado": "a fazer" }],   // estado no começo do dia
  "prs": [{ "numero": 40, "titulo": "…", "ticket": 10, "estado": "aberto" }],      // null = ainda não aberto
  "capitulos": [{ "t": "2026-11-06T09:15:00-03:00", "titulo": "Daily" }],
  "eventos": [ /* veja abaixo */ ]
}
```

### Evento

| Campo | Obrigatório | Para quê |
|---|---|---|
| `t` | sim | horário ISO com fuso |
| `quem` | sim | `id` de alguém da equipe |
| `origem` | sim | `humano`, `agente`, `ferramenta`, `ci`, `mundo`, `interno`, `agenda` (veja abaixo) |
| `texto` | sim | o que aparece no balão e no registro, sem reescrever |
| `tipo` | não | muda o estado do escritório (tabela abaixo) |
| `onde` | não | `m1`..`m6`, `cafe`, `sofa`, `planejamento`, `estante`, `deploy`, `racks`, `portaria` |
| `ate` | não | até quando fica em `onde`; sem `ate`, fica até o próximo evento dele |
| `com` | não | ids que vão junto para `onde` (uma reunião, por exemplo) |
| `custo_usd` | não | soma no custo do dia |
| `ticket`, `estado`, `titulo` | não | mudam o quadro de tickets; ticket novo aparece com alfinete vermelho |
| `pr`, `estado_ticket` | não | abrem ou mesclam um PR e movem o ticket ligado |
| `ci` | não | `rodando`, `verde` ou `vermelho`; acende o semáforo e o painel dos servidores |
| `rodada`, `resultado` | não | revisão: `mudancas` ou `aprovado` |
| `versao`, `tickets` | não | deploy: os tickets listados vão para "no ar" |

**Origens:**

| Origem | O que é | Como aparece |
|---|---|---|
| `humano` | o que o Camps escreveu | entre aspas |
| `agente` | frase literal do agente | entre aspas, em itálico |
| `ferramenta` | o que alguém fez com uma ferramenta: commit, PR, busca | texto simples |
| `ci` | mensagem da esteira de CI e deploy | fonte de terminal |
| `mundo` | algo que chegou de fora | texto simples |
| `interno` | estado do escritório | texto simples |
| `agenda` | o Vigia lendo a agenda | texto simples |

`numeros` (frase montada com os números do dia) e `visitante` (reação ao formulário) não vêm no JSON. A página monta essas falas e as marca com a origem.

**Tipos com efeito:**

| Tipo | Efeito |
|---|---|
| `abertura`, `fechamento` | os robôs saem da recarga ou entram nela |
| `chegada`, `saida` | a pessoa entra pela porta ou vai embora |
| `recarga`, `acorda` | um robô entra na recarga ou sai dela |
| `cafe` | conta um café |
| `almoco` | com `onde: "sofa"`, liga o videogame |
| `reuniao` | com `onde` e `com`, leva o grupo junto |
| `ticket`, `pr`, `ci`, `revisao`, `deploy` | mudam o quadro, as métricas e o painel |
| `entrega` | o robô vai até a mesa; o de rodas leva o papel impresso |
| `busca` | o drone acende o feixe na estante |
| `aviso`, `pedido` | o Mensageiro sai do tubo com o envelope |

**Tudo que o painel mostra é contado dos eventos até o momento:**

- tickets entregues;
- PRs mesclados;
- CI verde (verdes sobre execuções terminadas);
- rodadas de revisão;
- deploys;
- cafés;
- custo.

## Demonstração no relógio de hoje

Com `"demonstracao": true`, o dia de exemplo toca no relógio de hoje: às 10:30 de qualquer dia útil, a cena mostra as 10:30 do exemplo. Fim de semana e feriado são folga. O replay usa os horários do próprio dia de exemplo.

Quando chegar o dado real, tire `demonstracao`. A página então só mostra o expediente no dia de `data`; num dia útil sem registro, o chip fica em SEM DADOS.
