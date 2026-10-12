# Plano do M5 — Controlador humano

**Status:** implementado em 12/out/2026. Falta a partida de meio dia do usuário (o critério de pronto). O que mudou está na seção 8.
**Escopo** (escopo §7): clicar para mover, menu de ações, assumir e devolver a posse.
**Pronto quando:** você joga meio dia e devolve ao script sem quebrar nada.
**Critério de aceite:** A9 (posse) pelo caminho da UI: o humano assume, joga e devolve, e os comandos de quem não tem a posse são recusados.

## 0. Passo zero (já aprovado na revisão do M4)

### 0a. Pulso do kernel

- **O que é:** uma vez por intervalo de tempo real, o kernel publica o tick de verdade, mais o relógio (modo, escala, pausa).
- **Configurável:** `kernel.pulse_seconds` em `config/env/local.yaml`, 1 s no começo. Vou medir o custo; se pesar, mudamos para 5 ou 10.
- **Fora do histórico:**
  - o pulso vai para um assunto `campsverso.<mundo>.live.kernel` que nenhum stream guarda;
  - não entra no arquivo JSONL, no replay nem no hash de determinismo;
  - sai do laço do relógio, e não do núcleo determinístico.
- **Contrato:** `contracts/live/kernel.v1`, uma mensagem leve sem envelope, como as de `realtime`.
  - A porta `EventBus` ganha um `announce` (publicar sem guardar).
  - O NATS deixa o kernel publicar e o gateway assinar `campsverso.*.live.>`.
- **No gateway e na tela:**
  - o estado ganha `pulse` (tick, hora simulada e se o kernel está vivo);
  - depois de 3 pulsos perdidos, o gateway marca o kernel como sem sinal;
  - a tela passa a se ancorar no tick do pulso, para de estimar e mostra "kernel sem sinal".

### 0b. `make sessoes`: tempo e tokens por marco, guardados no git

- **De onde vêm os dados:** o histórico de sessões do Claude Code deste projeto (`~/.claude/projects/<projeto>/*.jsonl`), lido só para tirar números.
- **`docs/custos/sessoes.csv`:**
  - uma linha por turno: sessão, início, fim, minutos ativos, chamadas, tokens de entrada, de saída, de cache lido e escrito, e o marco;
  - nunca o texto da conversa;
  - cada execução atualiza as linhas existentes e acrescenta as novas;
  - o marco das linhas novas vem de `MARCO=M5`;
  - as sessões de M0 a M4 já entram classificadas.
- **`docs/custos/plano.csv`:** o uso do plano Max (janela de 5 horas e semana). Esse número não está no histórico; só o app o mostra. Eu anoto ao fechar cada marco.
- **`docs/custos/README.md`:** gerado, com os totais por marco e a evolução do uso do plano.

## 1. O caminho do clique

```
clique na UI ─► gateway: monta cmd.action.propose com controller human/camps-browser e valida
                   │
                   ▼
                kernel: confere a posse (not_in_control), aceita ou recusa ─► eventos ─► tela
```

O kernel já tem tudo o que o M5 precisa:
- `possess` e `release`;
- a recusa `not_in_control` para quem não tem a posse;
- humano proibido no modo máximo (`mode_not_allowed`);
- uma ação nova do mesmo controlador cancela a que está em andamento, exceto `sleep`.

O trabalho fica no catálogo de ações, no gateway e na UI.

## 2. Catálogo de ações: o que aparece no menu (decisão 1)

Hoje as ações existem só como código do cartucho, e a UI não sabe o que oferecer ao clicar num canteiro. Proposta:

- **O cartucho declara o catálogo como dados** (`affordances` no `farm.yaml`):
  - em quais tipos de entidade a ação aparece (`plot`, `well`, `chest`…, ou `self`, no próprio avatar);
  - um rótulo em português;
  - os parâmetros, com as escolhas possíveis.
- **Exemplos:**
  - **plantar:** em `plot`, escolhendo a cultura;
  - **comer:** em `self`, escolhendo um comestível que esteja no inventário;
  - **comprar:** no `kiosk`, escolhendo a semente e a quantidade.
- **O kernel publica o catálogo no `session.started`,** num campo opcional e compatível. A projeção o guarda, e a UI monta os menus a partir dele.
- **Um teste confere o catálogo:** toda ação do catálogo existe no cartucho, e todo parâmetro é um que a ação lê.
- **O menu só sugere; quem decide continua sendo o kernel.** Um item pode aparecer e ser recusado (`not_adjacent`, `missing_item`…), e a recusa aparece na tela.
- **Serve depois ao LLM (v0.2):** é o "catálogo de afordâncias" da bíblia §8, pelo mesmo contrato.

## 3. Gateway

- **Comandos novos para as duas visões:** `action.propose`, `avatar.possess` e `avatar.release` (decisão 2). O relógio continua só com o operador.
- **O gateway preenche o controlador humano:**
  - `controller: human`, `controllerid: human/camps-browser` e `actor: human/<visão>`;
  - a UI não escolhe quem é.
- **NATS:** o gateway passa a poder publicar esses três comandos, e nada além.

## 4. UI

- **Clique (decisão 4):**
  - **esquerdo anda:** num tile vazio, até lá (`move` para o tile); numa entidade, até perto dela (`move {near}`);
  - **direito abre o menu:** numa entidade, as ações daquele tipo; no próprio Camps, o menu de si (comer, dormir, esperar);
  - escolhas e quantidades aparecem num submenu curto.
- **Posse:** um botão "Assumir" ou "Devolver ao script" nas duas visões. Sem a posse, clicar no mapa só mostra a dica "assuma o controle para jogar".
- **Retorno:**
  - a ação em andamento aparece sobre o Camps, como hoje;
  - uma recusa vira aviso com o motivo legível;
  - o pedido de decisão do kernel aparece discreto ("o mundo espera sua decisão"), e o mundo não espera.
- **Modo máximo (decisão 3):**
  - na visão operador, "Assumir" troca para o contínuo antes;
  - na visão jogador, mostra a recusa do kernel e pede ao operador.

## 5. Testes

| O quê | Como |
|---|---|
| **Catálogo** | unidade no cartucho: ações e parâmetros do catálogo batem com o código; o `session.started` traz o catálogo; a projeção o guarda |
| **Gateway** | em memória: as duas visões podem assumir, propor e devolver; o envelope sai com o controlador humano; comando fora da lista é recusado |
| **A9 pela UI** | NATS e processos de verdade, com um cliente WebSocket: assumir; andar até um canteiro; plantar e regar; um comando do script é recusado com `not_in_control`; devolver; o script volta a decidir |
| **Pulso** | o pulso chega no intervalo configurado e não aparece no arquivo; com o kernel morto, o gateway marca "sem sinal" depois de 3 pulsos; a tela para |
| **`make sessoes`** | um histórico de exemplo: turnos, minutos ativos e tokens; rodar duas vezes não duplica linhas |
| **UI** | Vitest no menu (o que aparece para cada tipo, com o catálogo e o inventário) e na âncora do pulso |
| **Pronto quando** | você joga meio dia no `make sandbox` e devolve ao script; eu antes faço o mesmo roteiro no navegador embutido |

## 6. Decisões

| # | Decisão | Recomendação (todas aprovadas) |
|---|---|---|
| 1 | De onde vem o menu de ações | **Catálogo declarado pelo cartucho (dados) e publicado pelo kernel no `session.started`.** Alternativas: (a) um arquivo do cartucho servido pelo gateway, como o mapa, que não chegaria ao LLM pelo mesmo caminho; (b) menus fixos na UI, que colocariam conhecimento da fazenda dentro da tela |
| 2 | Quem assume e joga | **As duas visões**, como o mesmo humano (`human/camps-browser`): na v0.1 o jogador é você. A alternativa é só o operador assumir e o jogador apenas agir |
| 3 | Assumir com o mundo no modo máximo | **Operador: "Assumir" troca para o contínuo e depois assume. Jogador: mostra a recusa do kernel.** A UI não contorna regra; só junta dois pedidos do operador |
| 4 | Gesto de jogo | **Só o mouse: o clique esquerdo anda, e o direito abre o menu** (da entidade, ou do próprio Camps). Teclado e arrastar ficam para depois |
| 5 | Humano que não responde | **O mundo não espera e nunca devolve sozinho.** O avatar fica parado até você agir ou devolver |
| 6 | Detalhes do pulso | **`kernel.pulse_seconds: 1`; "sem sinal" depois de 3 pulsos perdidos; assunto `live`, fora dos streams; contrato em `contracts/live/`.** Eu meço CPU e mensagens com 1 s e anoto no diário |
| 7 | Onde guardar os custos | **`docs/custos/`, com o CSV por turno, o CSV do uso do plano e um README gerado com os totais por marco.** Só números; o texto das conversas nunca entra |

As decisões viraram a ADR-0051.

**Observações do usuário na aprovação:**
- **Decisão 1:** no futuro, o mundo pode ter ações padrão que sempre existem. Foi para `futuro.md`.
- **Decisão 4:** os cliques esquerdo e direito. O esquerdo anda; o direito abre o menu. Teclado e arrastar foram para `futuro.md`.
- **Decisão 5:** sem devolução automática, por princípio. O mundo segue sem quem não age.
- **Decisão 6:** 1 s, acompanhando o consumo. A máquina é um MacBook Pro M3, acima da média, e os números do diário precisam dizer isso.

## 7. Commits previstos

1. `docs: plano do M5 aprovado (ADR-0051)`
2. `feat: pulso do kernel (contracts/live)`
3. `feat: make sessoes e docs/custos`
4. `feat: catálogo de ações do cartucho no session.started`
5. `feat: gateway aceita os comandos do humano`
6. `feat: UI joga: clique, menu de ações, assumir e devolver`
7. `test: A9 pela UI com NATS`
8. `docs: fechamento do M5`

## 8. Como ficou

| Item | Resultado |
|---|---|
| **Roteiro no navegador embutido** | assumir; plantar longe do canteiro (o kernel recusa: `not_adjacent`, e a tela mostra); clique esquerdo para chegar perto; plantar rabanete; o menu do próprio Camps ("Comer" desabilitado sem comida); devolver, e o script volta regando o canteiro plantado |
| **Modo máximo** | o operador assume e o mundo passa a 72× antes; o jogador recebe "O kernel recusou avatar.possess (mode_not_allowed…)" |
| **A9 com NATS** | um cliente WebSocket assume, anda, planta, vê um comando do script recusado com `not_in_control`, devolve, e o script volta a agir; cerca de 2 s |
| **Pulso** | a cada 1 s, fora do arquivo; com `kill -9` no kernel, o estado vira "sem sinal" em cerca de 3 s. Custo medido em 45 s a 72× num MacBook Pro M3: +0,02 s de CPU no kernel e +0,13 s no gateway |
| **Custos** | `make sessoes` grava os turnos de M0 a M5 em `docs/custos/` |

**O que mudou em relação ao plano:**

- **Cada conexão vê a recusa dos próprios comandos.** `world.command.rejected` é `observer`, e a visão jogador não saberia por que o kernel recusou o seu "Assumir". O gateway guarda os ids dos comandos de cada conexão.
- **No YAML do cartucho, a chave é `kinds`.** No YAML 1.1, `on:` vira booleano. O contrato continua `on`.
- **Clique direito no chão anda,** como o esquerdo. Não há menu de chão.
- **Os avisos da tela vêm direto dos eventos de cada update,** e não da linha do tempo. No modo máximo, a linha do tempo enche (1.000 entradas), e os avisos novos se perdiam.
