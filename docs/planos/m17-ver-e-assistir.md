# Plano do M17 — Ver e assistir

*Proposto em 23/out/2026, depois do fechamento do M16. Aprovado em 23/out/2026 (ADR-0068), com as notas do usuário na §7. É o segundo marco de visual da v0.3 (ADR-0066): o que o avatar vê na tela passa a ser o que ele vê no mundo, e as corridas da arena passam a poder ser assistidas.*

**Pronto quando:**
- **A névoa:** na visão do jogador, a tela mostra só o que o Camps enxerga (o raio, os marcos e o terreno que ele já viu, mais escuro). O operador vê tudo e pode trocar para "ver como o Camps".
- **A noite e a lanterna:** à noite o raio diminui, e a lanterna o aumenta. Vale para o script, para o LLM e para a tela, porque a regra é da percepção.
- **A visão arena:** uma página mostra as corridas de uma rodada lado a lado, pequenas e aceleradas. Um clique entra numa delas na visão do operador. Dá para assistir ao vivo uma corrida que está rodando e rever uma gravada, com controle de velocidade.
- **Os menus do humano:** cavar e fincar o espantalho pelo clique direito na grama; pegar e guardar ferramentas pelo baú; uma fila de ações; atalhos de teclado.
- **A linha do tempo legível:** a linha do tempo fala português ("colheu 1 milho no plot-007"), com os rótulos declarados pelo cartucho.
- **As fazendas 1 e 2 intactas:** os mesmos números de sempre, e a fumaça da tela nos três mundos.

## O que o levantamento mostrou

- **A percepção já corta pelo raio,** e o raio vem da configuração que o cartucho declara (`perception_config`), igual para o dia todo. Ela não sabe de fase nem de luz.
- **A tela recebe o estado do operador inteiro** (`ObserverState`): todas as entidades, sem recorte. A névoa precisa saber o raio e o que o avatar já viu. O estado já traz o raio (`session.perception`).
- **A arena grava o `archive.jsonl` de cada corrida só no fim** (`campsverso_testkit.arena`). Para assistir ao vivo, ela precisa ir gravando por partes, a cada dia simulado. O resumo e as métricas continuam saindo no fim.
- **O gateway monta o estado da tela a partir dos eventos,** pela projeção comum (`libs/world-view`). Hoje os eventos vêm do NATS; ler os mesmos eventos de um arquivo é só outra fonte para a mesma projeção.
- **A tela tem uma conexão e um Phaser por página.** Várias fazendas na mesma página pedem várias conexões. O navegador aceita uns 16 contextos WebGL; o canvas de depuração, em 2D, não tem esse limite.
- **A linha do tempo mostra o tipo e os campos do evento** (`action.accepted`, `avatar_id=camps · action=dig…`). As métricas já são declaradas pelo cartucho e viajam no `session.started`; os rótulos podem seguir o mesmo caminho.

## 1. A névoa, a noite e a lanterna

- **A regra da percepção ganha a noite e a luz,** declaradas pelo cartucho junto do raio (campos opcionais em `perception_config`):
  - `by_phase`: o raio por fase do dia. Na Morada do Sol, 12 de dia, 7 no entardecer e 5 na noite e na madrugada.
  - `lights`: um item que, no inventário, garante um raio mínimo. Na Morada do Sol, a lanterna (`lanterna`, 40 moedas no quiosque, peso 1) dá 10.

  Quem aplica é o serviço de percepção, então valem para o script, o LLM e o humano. As fazendas 1 e 2 não declaram nada e não mudam. A noite e a lanterna entram no manual, porque são regras visíveis.
- **A tela, na visão do jogador:**
  - o que está fora do raio fica coberto;
  - o terreno já visto aparece escurecido;
  - o que nunca foi visto fica preto;
  - as entidades fora do raio somem, menos os marcos.

  O que o avatar já viu fica guardado na própria tela, pelos `tiles` vistos enquanto ela está aberta. O operador ganha o botão "ver como o Camps".
- **A noite na tela:** além da sombra de hoje, um círculo de luz em volta do Camps com o raio da hora, maior com a lanterna.

## 2. A visão arena

- **A corrida grava enquanto roda:** o `archive.jsonl` passa a ser escrito por partes (a cada dia simulado) e um `estado.json` pequeno diz se ela terminou. A tabela e o relatório não mudam.
- **O gateway ganha o modo de assistir** (`make assistir PASTA=data/arena/<rodada>`):
  - em vez do NATS, ele lê os arquivos de eventos das corridas da pasta e monta o estado de cada uma pela mesma projeção;
  - serve a lista das corridas e um WebSocket por corrida (`/ws?run=<nome>`), com o mesmo contrato `realtime`;
  - uma corrida rodando é seguida enquanto o arquivo cresce; uma terminada é tocada desde o começo, num relógio de reprodução com velocidade (pausar, 1 dia por minuto, 1 dia a cada 10 segundos, o máximo).

  Nada passa pelo kernel: assistir é ler fatos, determinístico por construção. Isso substitui a ideia do `at_tick` no modo contínuo, que pedia mexer no princípio 7.
- **A página da arena** (`/?view=arena`):
  - uma grade de cartões, um por corrida, cada um com uma fazenda pequena no canvas 2D, o nome, o dia, as moedas e o custo;
  - um clique abre a corrida na visão do operador, com o Phaser, a câmera e o painel.

  A grade usa o canvas de depuração porque ele é leve e não tem limite de contextos.
- **Assistir o sandbox ao vivo** já é a visão do operador de hoje. A visão arena serve às corridas em processo e às rodadas gravadas.

## 3. Os menus do humano

- **O clique direito na grama vazia** abre um menu com "Cavar aqui" e "Fincar o espantalho aqui" (se ele tiver um). O Camps anda até o lado do tile e faz a ação. A tela só propõe; o kernel valida.
- **O baú:** guardar e pegar ferramentas pelo id, com as escolhas montadas a partir das entidades que estão no inventário ou no baú, e não de uma lista fixa.
- **A fila de ações, na tela:**
  - a tela guarda a fila e manda a próxima proposta quando a anterior termina;
  - o kernel não muda, e uma recusa limpa a fila e avisa;
  - quem enfileira é o shift com o clique;
  - a fila aparece no painel, e o Esc a esvazia.
- **O teclado:**
  - as setas e o WASD andam um tile;
  - o espaço volta a seguir o Camps;
  - E abre o menu do próprio Camps.

## 4. A linha do tempo legível

- **O cartucho declara os rótulos de eventos como dado**, como as métricas: um texto por tipo de evento, com campos entre chaves, por exemplo `campsverso.world.item.created.v1` com `reason: harvest` vira "colheu {qty} {item}". O `session.started` leva os rótulos, num campo opcional.
- **A linha do tempo mostra o rótulo** quando existe e o tipo cru quando não. Os eventos ocultos continuam só na visão do operador.

## 5. Testes do marco

- **Percepção:**
  - o raio pela fase e pela lanterna;
  - as fazendas 1 e 2 com o raio de sempre;
  - o determinismo nos três mundos.
- **Gateway no modo de assistir:**
  - o estado montado a partir de um arquivo é igual ao montado pelo barramento;
  - seguir um arquivo que cresce;
  - a velocidade de reprodução.
- **Tela, no Vitest:** a névoa (o que cobre, o que escurece), a fila de ações e os rótulos.
- **Tela, no Playwright:**
  - a visão do jogador com névoa na Morada do Sol;
  - o clique direito na grama cava;
  - a visão arena com duas corridas sintéticas, e o clique que entra numa.
- **Soaks:** um ano na Morada do Sol com a noite mais curta de visão, e os soaks das fazendas 1 e 2 com os números de sempre.

## 6. Ordem do trabalho

1. A percepção: a noite, a lanterna, os contratos e o manual.
2. A névoa e a luz na tela.
3. A arena gravando por partes, e o gateway no modo de assistir.
4. A página da arena.
5. Os menus do humano e a fila.
6. Os rótulos de eventos.
7. Fechamento: a §9, o diário, os custos e um print.

**Estimativa:** duas a três sessões, como o M16. **Custo de API:** nenhum, a não ser que a mudança no manual peça regravar a fita da Morada do Sol (uns US$ 0,03).

## 7. Decisões

1. **O raio pela fase e a lanterna, na percepção** (`by_phase` e `lights`), com os números da §1, declarados só pela Morada do Sol. *Recomendação: sim. É a mesma regra para quem joga, para o script e para o LLM, e dá um motivo para planejar o dia.*
2. **A névoa na visão do jogador,** com o terreno visto escurecido e o resto preto, e "ver como o Camps" para o operador. *Recomendação: sim.*
3. **A lembrança da névoa fica na tela** (o que foi visto enquanto ela está aberta), e não no servidor. *Recomendação: sim, por agora. Lembrar entre recargas da página pede o gateway guardar o que cada avatar viu, e isso fica para quando houver vários jogadores (M20).*
4. **Assistir lendo os fatos,** com o gateway no modo de assistir, e não reexecutando o kernel com `at_tick`. Essa decisão substitui a ideia antiga e precisa de ADR. *Recomendação: sim. É determinístico, não toca no princípio 7 e serve também ao vivo.*
5. **A arena grava o arquivo por partes,** a cada dia simulado, com um `estado.json` que diz se a corrida terminou. *Recomendação: sim. É o que permite assistir ao vivo.*
6. **A grade da arena no canvas 2D,** e a corrida aberta no Phaser. *Recomendação: sim. Dez ou vinte fazendas pequenas não cabem em contextos WebGL.*
7. **A velocidade da reprodução:** pausar, 1 dia por minuto, 1 dia a cada 10 segundos e o máximo. *Recomendação: sim.*
8. **Os menus do humano da §3,** com a fila na tela e não no kernel. *Recomendação: sim. A fila no kernel mudaria o modelo de ações para todos os controladores sem ganho para o script e o LLM, que já decidem a próxima ação.*
9. **O teclado:** as setas e o WASD andam, o espaço segue, o E abre o menu do Camps. *Recomendação: sim.*
10. **Os rótulos de eventos declarados pelo cartucho,** no `session.started`. *Recomendação: sim. O escritório vai precisar disso ("abriu o PR #41").*
11. **A lanterna desenhada no estilo LPC,** se o pacote não tiver uma (download autorizado se precisar). Ela aparece no inventário e na luz em volta do Camps, não no mapa. *Recomendação: sim.*
12. **O manual da Morada do Sol** ganha a noite e a lanterna, e a fita é regravada se o pedido mudar (uns US$ 0,03). *Recomendação: sim.*

**As notas do usuário na aprovação (23/out):**
- **1:** a mesma regra para todos, configurável, maior de dia e menor de noite.
- **2:** a névoa é névoa mesmo, uma nuvem, e não preto. Onde o avatar passa, ela abre e mostra o chão. Quando ele se afasta, o desenho fica, coberto por um cinza semitransparente, e o que está ali fica congelado como foi visto até ele voltar ao raio.
- **3:** o humano vê o desenho congelado na névoa, mas não sabe se algo mudou. O script e o LLM não veem, então lembram de fato, sabendo que pode ter mudado.
- **5:** ficar de olho no tamanho dos arquivos; uma limpeza pode vir depois.
- **6:** de 4 a 6 corridas por tela, por agora.
- **9:** uma explicação dos comandos na tela, pelo menos na primeira vez.
- **10:** o escritório vai precisar porque o trabalho dele acontece fora do mapa, e a linha do tempo é a janela para isso.

## 8. Como ficou

*(a preencher no fechamento)*
