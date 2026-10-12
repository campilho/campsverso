# ADR-0050 — Decisões do plano do M4 (UI de depuração)

**Status:** aceita · **Data:** 2026-10-12 · **Marco:** M4
**Complementa:** `docs/planos/m4-ui-de-depuracao.md`; escopo §4.1, §6 e §7; ADR-0022, ADR-0025, ADR-0026

## Decisão

As decisões do plano, aprovadas pelo usuário. A decisão 0, o cochilo, está na ADR-0049.

1. **O contrato do WebSocket fica em `contracts/realtime/`.**
   - As mensagens são `welcome`, `update`, `command` e `reply`, versionadas como os eventos: `campsverso.realtime.<nome>.vN`.
   - Os tipos são gerados para Python e para TypeScript.
   - O AsyncAPI ganha um servidor `ws` para o gateway.
   - A UI é um módulo como os outros e só conhece o gateway por contrato.
2. **O estado vem de uma projeção no gateway.**
   - Ao conectar, a UI recebe o estado inteiro. Depois, a cada 100 ms, recebe um *merge patch* (RFC 7386) com o que mudou, mais os eventos do intervalo.
   - A UI não aplica eventos ao mundo. O código da projeção sai da percepção para `libs/world-view`, e percepção e gateway passam a usá-lo.
   - **O estado é genérico e não depende de como se desenha.** Ele contém o modelo de mundo do kernel (ADR-0025):
     - entidades com tipo, posição em tiles e atributos;
     - itens por contêiner;
     - trajetos com os ticks de partida e a velocidade;
     - necessidades, relógio e posse.
   - Pixels, cores, sprites e câmera ficam de fora. O canvas do M4, o Phaser do M6 ou um renderer 3D (three.js ou análogo) consomem as mesmas mensagens; cada um decide como desenhar cada `kind`.
   - **Também não depende do kernel:** só entram eventos publicados, nunca o snapshot interno do kernel.
3. **O mapa vem do cartucho.**
   - Hoje é o arquivo Tiled (`.tmj`), servido pelo gateway em `/content/maps/<id>.tmj`. O `id` vem do `session.started`.
   - O M6 usa o mesmo arquivo.
4. **Visões e acesso.**
   - Cada conexão escolhe a visão `player` ou `operator`, e o filtro acontece no gateway: a visão jogador nunca recebe nada `internal`.
   - O gateway só escuta em `127.0.0.1`, sem login, na v0.1.
   - Só a visão operador manda comandos. No M4, só os do relógio.
5. **As métricas no painel ficam para o M7**, junto com o visual mais elaborado da tela.
6. **`make sandbox`:** sobe um mundo descartável em `data/sandbox/<data-hora>`, com tudo ligado, para testar sem criar o mundo oficial `farm-camps-01`.
7. **Sem Playwright no M4.**
   - O Playwright abre um navegador de verdade, controlado por código, e confere a tela automaticamente.
   - Por enquanto, os testes são:
     - Vitest nas partes puras da UI;
     - o teste do gateway com um cliente WebSocket;
     - um roteiro manual, conferido no navegador embutido do Claude Code e pelo usuário.
   - O Playwright volta a ser avaliado no M6.

## Para o futuro (não agora)

Os itens estão em `docs/planos/futuro.md`:

- Um formato de mapa próprio, em JSON ou binário, com todos os detalhes, feito num editor que seja parte do projeto.
- Um renderer 3D sobre o mesmo contrato.
- Visitantes com login, que exigem credenciais separadas por visão (ADR-0022).

## Consequências

- **O M4 entrega um quinto processo, o gateway**, e a primeira tela.
- **A credencial NATS do gateway** passa a ler `internal`, com a API do JetStream restrita aos streams dele.
- **Quem implementar outro renderer** só precisa do pacote de contratos e do endereço do gateway.
