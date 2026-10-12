# Plano do M4 — UI de depuração

**Status:** aprovado em 12/out/2026 (ADR-0049 e ADR-0050), em implementação.
**Escopo** (escopo §7): gateway WebSocket, canvas simples, visões jogador e operador, controles do relógio.
**Pronto quando:** dá para assistir a um dia ao vivo no browser e pausar, acelerar e avançar passo a passo.
**Critérios de aceite tocados:** A6 no gateway (derrubar o gateway não derruba o kernel; ao voltar, ele retoma do ponto certo) e a visão jogador sem nada `internal`. Prepara o M5 (humano joga) e o M7 (métricas no painel).

## 0. Passo zero: dormir a qualquer hora (decisão 0)

Antes da UI, um ajuste pequeno no cartucho, como o passo zero do M2 (ADR-0041).

**Por que existe a recusa hoje.** O sono da v0.1 tem um único horário para acordar, as 06:00. Se o avatar deitasse às 14:00, dormiria 16 horas. Por isso a janela ficou em 20:00–06:00, e a ADR-0041 deixou os cochilos "para o futuro".

**Proposta: o cochilo**
- `sleep` passa a valer a qualquer hora, com ou sem cama, como já é à noite.
- **Começou à noite** (20:00–06:00): nada muda. Dorme até as 06:00.
- **Começou de dia** (06:00–20:00): é um cochilo. Acorda quando a energia chega a 100, na taxa do lugar (cama 12,5/h, chão 5/h), ou às 06:00, o que vier antes. Exemplo: cochilar na cama às 10:00 com energia 30 dá 5 h 36 min e acorda às 15:36.
  - Esse horário de acordar sai de uma conta no começo do sono, então o kernel não precisa de nada novo.
  - O cochilo diurno não pode acordar no meio da noite, senão o avatar desmaiaria às 02:00.
- **De dia com energia 100**, o cochilo duraria zero, e a ação é recusada com `not_tired`. O motivo `too_early_to_sleep` sai de uso.
- **Contrato:** nenhuma mudança. `sleep.started.v2` já traz `wake_at_tick` e `cause: voluntary`.
- **Fazendeiro-script:** a regra 1 da bíblia (energia < 10 → dormir) passa a valer de dia também. Nos soaks a energia nunca caiu abaixo de 30, então os números de 30 dias não mudam.
- **O "marcador de sono" fica para depois.** Um dia anterior que acabou tarde deixaria o avatar com sono. É a necessidade "sono" que a ADR-0041 descreveu para o futuro: ela sobe acordado e só baixa dormindo. Faz mais sentido com o LLM ou com o humano jogando, que podem virar a noite; o script nunca vira.

## 1. O caminho de um evento até a tela

```
kernel ─► NATS (world, agent.camps, internal) ─► gateway ─WebSocket─► UI (canvas)
  ▲                                              (projeção, filtro
  │                                               por visão, lotes)
  └──────────── cmd.clock.* ◄── gateway monta e valida o envelope ◄── botão da UI
```

## 2. Gateway (processo próprio)

- **O que lê:** os streams `world` e `agent` do avatar, e também `internal`, que vai só para o operador (ADR-0022). Usa consumidores duráveis.
- **Projeção do observador** (decisão 2): o estado atual do mundo, com o mesmo código genérico da projeção da percepção.
  - Além do que a percepção já guarda, a projeção ganha o relógio (modo, escala, pausa), a posse do avatar e a sessão (mapa, `tick_seconds`, início).
  - Ela é durável como a da percepção, num arquivo com o último `seq` aplicado e um consumidor durável. Se o gateway cair, volta de onde parou.
- **A conversa com o browser** (decisão 1):
  - Ao conectar, a UI recebe `welcome`, com o estado e as últimas 500 entradas da linha do tempo.
  - Depois recebe `update` a cada 100 ms: um *merge patch* (RFC 7386) do estado, mais os eventos daquele intervalo.
  - A UI não aplica eventos ao mundo: só desenha o estado e lista os eventos. O modo máximo funciona do mesmo jeito; a tela mostra o estado mais recente, sem animar cada passo.
- **Visões** (decisão 4): cada conexão escolhe `jogador` ou `operador`. O filtro é feito no gateway, então o browser na visão jogador nunca recebe nada `internal`.
- **Comandos** (decisão 4):
  - No M4, só a visão operador manda comandos, e só os do relógio: `pause`, `resume`, `step`, `set_scale` e `set_mode`.
  - O gateway monta o envelope completo (id UUIDv7, `source`, `actor: human/operador`), valida contra o contrato e publica.
  - A resposta é o evento do kernel (`clock.paused`, ou `command.rejected` com o motivo), que volta pelo mesmo WebSocket.
- **HTTP:** serve o conteúdo do cartucho (o mapa Tiled, decisão 3) e, fora do modo de desenvolvimento, a UI compilada.
- **Portas:** o FastAPI fica num adaptador (`RealtimeGateway`, escopo §4.1), como manda o princípio 3. Os testes usam um adaptador em memória.
- **Endereço:** só `127.0.0.1`, sem login, na v0.1.

## 3. UI (`apps/ui`, canvas 2D; o Phaser só entra no M6)

- **Mapa:**
  - É a camada `terrain` do `map.tmj`, com uma cor por tipo de tile: grama, caminho, árvore, rio, parede, porta…
  - As entidades são quadrados coloridos por tipo, com rótulo curto. O canteiro muda de cor com o estágio.
  - O avatar é um círculo que anda interpolado pelo trajeto do `entity.moved` e mostra "Zz" quando dorme.
- **HUD (as duas visões):**
  - dia e hora, escala, modo e pausa;
  - moedas e clima;
  - fome e energia, com o último valor exato recebido (`need.changed` sai no máximo uma vez por hora; `decision_requested` traz os valores exatos);
  - inventário.
  - A UI não estima as necessidades entre um evento e outro, porque isso exigiria as taxas do cartucho dentro da UI.
- **Painel do operador:**
  - **Relógio:** Pausar ou Retomar; Avançar 1, 10 ou 60 ticks (só com pausa, ADR-0026); 1×, 72× e 720×; Máximo.
  - **Controlador atual:** só leitura. Assumir e devolver ficam no M5.
  - **Decisão atual:** o último pedido e a proposta que o respondeu.
  - **Linha do tempo:** filtro por visibilidade e tipo, com `internal` destacado.
- **A UI nunca decide.** Desabilitar "Avançar" fora da pausa é só conforto: quem aceita ou recusa é o kernel.
- **Design:** segue o layout de `docs/design/` e corrige os quatro pontos listados lá (a coleta das 22:00, a taxa de sono, a cena dormindo/desmaiado e o passo só com pausa).

## 4. Processos e comandos

- **`Procfile`:** ganha o `gateway`.
- **`make ui`:** sobe o Vite, com proxy de `/ws` e `/content` para o gateway.
- **`make sandbox`** (decisão 6): sobe um mundo descartável em `data/sandbox/<data-hora>`, no modo contínuo, com NATS próprio, os cinco processos e o gateway. Assim dá para testar e mostrar sem criar o mundo oficial.
- **Configuração:** a porta e o endereço do gateway e a pasta de conteúdo do cartucho vão para `config/env/local.yaml`.
- **NATS:** a credencial do `gateway` passa a ler `internal` (hoje é negada, provisoriamente). O acesso à API do JetStream fica restrito aos streams e consumidores dele, como foi feito com a percepção no M3.

## 5. Testes

| O quê | Como |
|---|---|
| **Projeção** | os testes da percepção passam a valer para o código em comum, mais relógio, posse e sessão |
| **Gateway, unidade** | `InMemoryBus` mais o adaptador em memória: o `welcome` traz o estado; o `update` traz o patch e os eventos; a visão jogador nunca recebe `internal`; um comando do operador vira envelope válido no assunto certo; um comando inválido volta como erro e nada é publicado |
| **Gateway com NATS** | processos de verdade e um cliente WebSocket em Python: recebe o `welcome`; `pause` faz chegar `clock.paused`; `step` faz chegar `clock.stepped`; a visão jogador não vê `internal` |
| **A6 no gateway** | `kill -9` no gateway e o kernel segue; ao voltar, a projeção fica igual à de um gateway novo que leu tudo |
| **UI** | Vitest nas partes puras: aplicar o patch, interpolar o trajeto, filtrar a linha do tempo, ler as cores do mapa |
| **Pronto quando** | roteiro manual com `make sandbox` e `make ui`: assistir um dia, pausar, avançar, 1×, 72×, máximo. Eu rodo no navegador embutido e registro no diário; depois você confere |

## 6. Decisões

| # | Decisão | Recomendação (todas aprovadas) |
|---|---|---|
| 0 | Dormir a qualquer hora | **Sim, como cochilo** (§0). Sem marcador de sono por enquanto: ele vira uma necessidade nova, mais adiante |
| 1 | Contrato do WebSocket | **JSON Schema em `contracts/realtime/`**, com codegen para Python e TypeScript e o AsyncAPI ganhando um servidor `ws`. A UI é um módulo como os outros e só conhece o gateway por contrato. A alternativa, tipos escritos à mão dos dois lados, divergiria sem ninguém notar |
| 2 | Como a UI recebe o estado | **Projeção no gateway e merge patch para a UI.** A projeção sai da percepção para uma lib comum, `libs/world-view`, e percepção e gateway passam a usá-la. Alternativas: um redutor de eventos em TypeScript (a mesma lógica em duas linguagens) ou ler o snapshot do kernel (acopla a UI ao formato interno do kernel) |
| 3 | De onde vem o mapa | **O arquivo Tiled do cartucho, servido pelo gateway** em `/content/maps/<id>.tmj`; o id vem do `session.started`. O M6 usa o mesmo arquivo. A alternativa, um evento novo com o terreno, deixaria o arquivo JSONL autossuficiente, mas repetiria em cada sessão um dado estático |
| 4 | Visões, comandos e acesso | **Filtro por conexão no gateway, só `127.0.0.1`, sem login na v0.1.** Só a visão operador manda comandos, e no M4 só os do relógio. Visitantes de fora exigiriam credenciais separadas (ADR-0022) |
| 5 | Métricas no painel | **Ficam para o M7**, como no escopo. O M4 já mostra as recusas na linha do tempo e o `make metrics` cobre o resto |
| 6 | Testar sem criar o mundo oficial | **`make sandbox`**, um mundo descartável com tudo ligado. O `farm-camps-01` continua esperando o seu primeiro `make run` |
| 7 | Teste de navegador automatizado | **Sem Playwright no M4.** Ficam o Vitest nas partes puras, o teste do gateway com cliente WebSocket e o roteiro manual. O Playwright volta a ser avaliado no M6, quando houver sprites e animações para conferir |

As decisões viraram a ADR-0049 (cochilo) e a ADR-0050 (as demais).

**Observações do usuário na aprovação:**
- O contrato e o estado precisam ser genéricos e não depender do kernel, para que um renderer mais sofisticado (three.js ou análogo) use as mesmas mensagens. A ADR-0050 registra isso.
- O equilíbrio da energia, um formato de mapa próprio com editor e os outros itens para depois estão em [futuro.md](futuro.md).

## 7. Commits previstos

1. `docs: plano do M4 aprovado (ADR-0049 e ADR-0050)`
2. `feat: cochilo, dormir a qualquer hora (passo 0)`
3. `refactor: projeção do mundo em libs/world-view`
4. `feat: contratos do WebSocket (contracts/realtime)`
5. `feat: gateway com projeção, visões e comandos do relógio`
6. `feat: UI de depuração em canvas`
7. `feat: make sandbox, make ui e permissões do gateway`
8. `test: gateway com NATS e A6 do gateway`
9. `docs: fechamento do M4`
