# ADR-0086 — A convocação do dev e a troca segura e avisada

**Status:** aceita · **Data:** 2026-11-21 · **Marco:** M25 (a parte 5)
**Complementa:** ADR-0078 (o escritório, o expediente); ADR-0083 (o escritório vivo sob o supervisor)

## Contexto

O usuário trabalha no projeto nos fins de semana e feriados, justamente quando o dev não está: no escritório vivo, em tempo real, o expediente vai de segunda a sexta, das 9h às 18h.

As primeiras trocas de versão de verdade, em 21/nov, mostraram duas falhas no supervisor:
- ele seguia qualquer commit novo do `origin/main`, e o `49fb87e` foi ao ar com o CI vermelho;
- enquanto o escritório trocava, a tela só apagava os botões e reconectava, sem dizer nada.

O plano da parte 5 está no §13 do plano do M25, aprovado pelo usuário com os padrões.

## Decisão

**A convocação:**
1. **Fora do expediente, o gerente convoca o dev.** O dev chega pela porta depois do deslocamento e fica até:
   - o gerente o dispensar;
   - o gerente sair do escritório;
   - o teto de horas;
   - o fim da janela do dia;
   - ou o expediente começar, que o assume.
   - Enquanto um dev está lá, o vigia sai.
2. **Ao entrar, o dev vem sozinho,** se o acordo dele diz isso. Vale no momento em que o gerente entra, uma vez por visita: dispensado, no teto ou no fim da janela, o dev só volta pelo botão.
   - Quem já estava lá quando o mundo começou, como o gerente-script dos testes, não conta como entrada.
3. **Os números ficam nos dados** (`schedule.on_call`):
   - **o gênero a deixa desligada;**
   - **o cenário do Campsverso a liga,** com a convocação ao entrar;
   - **os padrões:** a janela das 08:00 às 23:00, em qualquer hora fora do expediente; o deslocamento de 2 minutos; o teto de 6 horas;
   - **cada dev do elenco pode ter o próprio acordo** (`on_call` na linha dele), por cima do padrão.
4. **No mundo:**
   - **a convocação e a dispensa** são ações do gerente (`summon` e `dismiss`), de qualquer lugar da sala;
   - **os fatos novos** são `office.staff.summoned.v1` e `office.staff.dismissed.v1`;
   - **o motivo** de o dev entrar e sair é `convocacao`, e o replay refaz tudo;
   - **a convocação fica nos atributos do dev** (quem chamou, de onde, quando chega e o teto), e a visita, num atributo do gerente.
5. **O kernel ganha um gatilho genérico, `EveryMinutes`:** um sistema que roda a cada N minutos do dia.
   - O sistema do expediente roda a cada minuto, para os prazos da convocação.
   - O salto do relógio para em cada vencimento, como nos horários fixos.
   - É física de tempo, e não do escritório, e por isso fica no kernel (princípio 8).
6. **A tela não sabe do dev ausente:** a visão do jogador só traz quem está na sala.
   - O bloco "Convocação" do gerente lê a convocação dos atributos do dev presente e, do ausente, dos fatos da convocação na linha do tempo.
   - Antes de qualquer convocação, o botão vai sem alvo, e o kernel escolhe o único dev do elenco.
7. **A memória do dev guarda** a convocação (peso 7) e o fim dela (peso 4).

**A troca segura:**

8. **O supervisor só troca para um commit com o CI verde no GitHub.**
   - Ele lê o CI pelo App do dev (`commit_ci`, na porta do repositório de fora).
   - Um commit que ainda roda espera a próxima volta.
   - Um vermelho também espera, sem ser recusado de vez, porque o CI pode rodar de novo; um commit novo toma o lugar dele.
   - Sem a chave do App, o supervisor não sobe; `--sem-ci` desliga o portão, para o ensaio com um repositório local.
   - Seguir só as tags de versão fica como opção para depois.

**A troca avisada:**

9. **Antes de parar a pilha, o supervisor avisa as telas** pelo gateway vivo:
   - o `POST /aviso` aceita só a própria máquina;
   - a mensagem nova da tela é `realtime/notice.v1`.
10. **Os avisos são três:**
    - a troca que vem;
    - a troca que espera o dev terminar uma sessão;
    - a volta, quando a versão nova falha. Esta é contada pela pilha de antes, de pé de novo.
11. **Na tela,** uma faixa no topo diz:
    - o aviso;
    - "Trocando de versão…" quando a conexão cai logo depois de um aviso de troca;
    - "Conexão perdida" numa queda sem aviso;
    - e "Versão nova no ar: abc1234 (PR #N)" por alguns segundos depois de reconectar.
12. **O gateway guarda o último aviso por dois minutos** e o manda no welcome (`notice`, opcional), para a tela que reconecta no meio da troca.

## Consequências

- **O escritório vivo serve ao fim de semana:**
  - entrar como o gerente traz o Camps em 2 minutos, e sair o manda embora;
  - o custo da mente fica sob os tetos do orçamento de hoje.
- **O que vai ao ar sempre passou pelo CI:** os nossos pushes diretos e os PRs mesclados. Uma troca leva o tempo do CI do push no `main`, uns 12 minutos, mais a fumaça.
- **O dev ainda não roda o `ruff`:** a oficina não tem um formatador para ele, e o PR do briefing caiu no lint e no formato. É o primeiro pedido do dev convocado: o testador passa a rodar o `ruff` e o `pyright` nos arquivos mudados.
- **O supervisor roda da pasta de trabalho** (ADR-0083, adendo da parte 2): o portão e os avisos só valem depois de reiniciar o `make escritorio` sobre o código novo.
