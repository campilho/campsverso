# Kernel — Gestão do tempo

**Status:** rascunho para revisão · **Data:** 10/out/2026 · **Revisão:** 10/out/2026 (decisões T1–T7)
**Escopo:** como o kernel controla o tempo do mundo, acelera ou desacelera a "percepção" do mundo em relação ao tempo real, e como isso interage com agentes LLM, humanos visitantes, sono, manutenção, forks e replay.
**Relacionado:** `contratos-eventos-v0.md` (eventos de relógio), `pesquisa-componentes-plataforma-simulacao.md`.

> Inspiração: em *Somos Legião* (Bobiverse), Bob ajusta a própria percepção temporal e consegue fazer o mundo passar mais rápido ou mais devagar para ele. O kernel precisa oferecer o equivalente para a simulação inteira e, em fases futuras, para cada agente.

---

## 1. Princípio

**O kernel é o único dono do tempo canônico do mundo.** Nenhum outro módulo avança, interpreta ou altera o relógio simulado. Todos os outros apenas recebem eventos de tempo ou consultam o tempo atual.

**O mundo nunca para para esperar ninguém** (decisão T2). Nem agentes pensando, nem humanos decidindo, nem a consolidação de memória. Pausas existem apenas como comando de operação (debug, manutenção, orçamento).

---

## 2. Os três relógios

| Relógio | Quem controla | Para que serve | Exemplo |
|---|---|---|---|
| **Parede** (wall clock) | o sistema operacional | tempo real, custos, logs | `2026-10-10T16:20:00-03:00` |
| **Simulado** (sim clock) | **somente o kernel** | tempo dentro do mundo; ordem de todos os fatos | `2026-03-14T07:30:00-03:00`, tick 18240 |
| **Render** | o browser | animação suave a ~60 fps, interpolando entre eventos | — |

Regras:
- O relógio simulado é **monotônico**: nunca volta (voltar no tempo = carregar snapshot em um novo mundo).
- O relógio de render **nunca** influencia o mundo; ele apenas desenha.
- Todo evento carrega `time` (parede), `tick` e `simtime` (simulado), o que permite medir a dilatação a qualquer momento.

---

## 3. Mecânica base: passo fixo + escala

### 3.1 Passo de tempo fixo — configurável por cartucho (T1)

O mundo avança sempre em **passos simulados de tamanho fixo**, definidos no cartucho. As regras se comportam igual em qualquer velocidade.

| Cartucho | Tick inicial | Motivo |
|---|---|---|
| Fazenda | 1 min simulado | Cultivo, fome e deslocamento não precisam de resolução maior |
| Estúdio | 1 min simulado | Ancorado ao relógio real; a resolução da animação vem do render, não do tick |
| Simulação econômica / mini-Brasil | 1 dia (por rodadas) | Decisões macro |

### 3.2 Fator de escala

```
escala = segundos simulados por segundo real
ticks_por_segundo_real = escala / tamanho_do_tick_em_segundos
```

| Escala | 1 dia simulado leva | Uso típico |
|---|---|---|
| 1× | 24 h | Estúdio (ancorado ao horário de São Paulo) |
| **~72×** | **20 min** | **Fazenda — padrão inspirado em jogos de fazenda** (em Stardew Valley, um dia dura em torno de 15–20 minutos reais) |
| 24× | 1 h | Assistir com calma |
| 288× | 5 min | Experimentos |
| máximo | o quanto a CPU permitir | Forks sem LLM (fase futura) |

Com a política "pensar custa tempo" (seção 6), escalas altas fazem cada decisão consumir muito tempo do mundo. Por isso cada cartucho define uma **escala máxima recomendada** (seção 6.3).

### 3.3 Acumulador (padrão clássico de game loop)

O loop acumula o tempo real decorrido, multiplica pela escala e executa quantos ticks couberem, guardando o resto. A velocidade fica estável mesmo com variações de carga, e mudar a escala no meio da execução não quebra nada.

---

**Tick antecipado (ADR-0057, 17/out/2026).** No modo contínuo, uma proposta de ação que chega no meio de um tick roda o próximo tick na hora, e o acumulador desconta esse tick do tempo real que ainda vai passar. A sequência de ticks e o diário não mudam (o replay é idêntico); só a cadência real desloca em menos de um tick. Só um antecipado por vez: com a dívida em aberto, o comando seguinte espera o ritmo normal. Sem isso, a 1× um clique esperava até um minuto pelo próximo tick.

## 4. Salto de tempo: simulação de eventos discretos

O kernel combina **ticks** (quando há atividade) com uma **fila de eventos futuros** ordenada por tempo simulado (planta amadurece às 14h; fome cruza o limiar às 11h40). Se não há nada agendado entre agora e o próximo evento **e nenhum agente está pensando ou agindo**, o kernel salta direto para ele.

Na prática, com agentes dormindo em horários diferentes (T5), saltos longos ficam raros no mundo vivo; o mecanismo é mais útil em forks e experimentos.

**Regra de segurança:** sistemas contínuos (umidade, fome) precisam ser integráveis em um passo grande, ou o salto é quebrado em sub-passos. Cada sistema declara se suporta salto.

---

## 5. Modos de relógio

| Modo | Como o tempo avança | Determinístico? | Uso |
|---|---|---|---|
| **Contínuo** (padrão) | escala fixa; o mundo não espera ninguém | não | **Fazenda e startup**; mundo vivo |
| **Ancorado ao real** | `simtime` = horário real (com deslocamento de data) | não | **Estúdio** (expediente 8h–18h de verdade) |
| **Lockstep** | só avança quando as decisões pendentes foram resolvidas | sim | **Modo de experimento** (ablations limpas, comparação justa entre modelos) |
| **Por rodadas** | passos macro com micro-simulação interna | sim | Simulação econômica / mini-Brasil |
| **Máximo** | o mais rápido possível, com salto | sim | Forks (fase futura) |
| **Pausado / passo a passo** | sob comando | — | Debug, manutenção, orçamento |

Cada cartucho declara o modo padrão e os permitidos. Mudanças de modo e de escala são comandos que viram eventos.

**Na v0.1:** existem os modos contínuo (72×), pausado/passo a passo e máximo. O máximo opera **em lockstep** com o controlador que detém a posse (o kernel espera a resposta a cada `decision_requested`) e só é permitido com controladores `script` ou `replay`. É ele que roda os testes de resistência, determinismo e replay.

---

## 6. O "dilema do Bob": agentes que pensam devagar

### 6.1 Política padrão: pensar custa tempo (T2)

O mundo segue enquanto o agente pensa. A latência real da decisão vira tempo simulado consumido, e o avatar fica visivelmente "pensando" (animação, balão de reticências) nesse intervalo. Humanos e IAs passam a ter o mesmo tratamento: cada um decide no seu ritmo, como no mundo real, e o mundo não vira um jogo de turnos.

| Consequência | Como lidamos |
|---|---|
| **Replay por comandos deixa de ser idêntico** (a latência muda de uma execução para outra) | O replay para assistir usa o **log de eventos** (sempre fiel). A reexecução a partir de comandos fica restrita ao modo lockstep |
| **Experimentos ficam ruidosos** | Ablations rodam em **lockstep**; no mundo vivo, as métricas são lidas com várias execuções e estatística, não com um único caso |
| **Modelo mais rápido ganha vantagem** no mundo (vive "mais") | É um achado interessante para o post; quando a comparação precisar ser justa, usa-se lockstep |
| **Rede lenta ou provedor fora** congela o personagem por muito tempo simulado | Prazo máximo real (ex. 20 s); estourou, o nível reflexo assume e emite `cognition.timeout` |

### 6.2 Teto do tempo de pensar

Para escalas altas não transformarem uma decisão em uma hora do mundo:

```
tempo_simulado_consumido = min(latência_real × escala, teto_por_nível)
```

Exemplo na fazenda a 72×: 1,5 s reais = ~1,8 min simulados (natural). A 288×, seriam 7 min; o teto (ex. 3 min para o nível tático, 15 min para o estratégico) mantém o comportamento crível.

### 6.3 Escala máxima recomendada

Cada cartucho declara a escala acima da qual o teto passa a atuar o tempo todo (o que deixa de ser realista). Para a fazenda: ~120×. Acima disso, recomenda-se lockstep.

### 6.4 Dilatação temporal por agente — fase 2 (T7)

Cada personagem poderá ter uma **frequência cognitiva** própria (quantas vezes é acordado por hora simulada), equivalente ao *Custom Time Dilation* por ator da Unreal. Não altera o relógio do mundo. Candidatos naturais: o robô mech (lento, por regras) e uma AGI (rapidíssima em janelas curtas). Fica para a fase 2; no dia 1, a cadência é a mesma para todos e só os eventos acordam os agentes.

---

## 7. Tempo de execução vs tempo narrativo (T1, estúdio)

Agentes de IA fazem em segundos o que um humano faria em horas. Exibir isso exige um **modelo de duração por ação** com dois números:

| Duração | O que é | Exemplo (pesquisa de pauta) |
|---|---|---|
| `execução` | quanto a IA realmente levou | 40 s reais |
| `narrativa` | quanto um humano levaria | 2 h de expediente |

O cartucho escolhe um **dial de ritmo** (`work_pace`), configurável e até alternável ao vivo:

| Ritmo | Comportamento na tela | Mensagem |
|---|---|---|
| `humano` | a tarefa é encenada pela duração narrativa (o Diretor estica a cena) | "um estúdio que trabalha como gente" |
| `ia` | a tarefa leva o tempo real; o resto do dia os personagens ficam no café, conversando | "veja como a IA trabalha mais rápido que pessoas" — lúdico e didático |
| `híbrido` (proposto como padrão) | a duração exibida é um fator da narrativa (ex. 30%); sobra algum tempo livre | equilibra credibilidade e humor |

- A duração exibida vem com `provenance: staged` quando é encenação, e o evento real (o que de fato aconteceu) continua no log com `provenance: real`.
- Retakes reais do locutor (quando o técnico de som reprova o áudio) entram como eventos reais; os encenados, como `staged`.
- Na fazenda, o modelo também existe, mas a duração narrativa é a própria duração da ação no mundo (regar leva 6 ticks), sem encenação.

---

## 8. Humanos no mundo (T3)

- **O tempo do mundo não muda quando um humano entra.** Como em jogos de fazenda, o dia passa mais rápido que o real e o humano se adapta: anda e age na velocidade do avatar, não do relógio.
- **Fase 1:** sem visitantes humanos (simplifica tudo).
- **Fase futura:** o humano pode **acelerar ou desacelerar** o mundo (controle de velocidade no portal), com permissão por papel (só você no início; visitantes talvez nunca, ou só em forks).
- Ações humanas entram pelo mesmo catálogo de ações e pagam o mesmo tempo que as dos agentes.

---

## 9. Sono individual vs manutenção do sistema (T4)

A barreira do amanhecer global da versão anterior foi **descartada**. O desenho passa a separar duas coisas:

### 9.1 Sono — individual, por agente

- Cada agente dorme **no seu horário** (o vigia dorme de dia; Tomás à noite). O mundo continua.
- **A consolidação de memória acontece quando aquele agente dorme**, só dele.
- O tempo de sono em tempo real depende da escala: a 72×, 8 h de sono ≈ 6,7 min reais.
- Se a consolidação via batch ainda não terminou quando o agente deveria acordar:
  1. **Acordar "sonolento"** (proposta padrão): o agente acorda com a consolidação da noite anterior e um estado de baixa energia/foco até a consolidação chegar — o atraso técnico vira comportamento crível.
  2. **Dormir mais**: o agente só acorda quando a consolidação termina (com limite).
  3. **Consolidação síncrona**: sem batch, mais cara, sempre a tempo.
- A escolha é por cartucho; o padrão da fazenda é a opção 1, tentando batch primeiro e caindo para síncrono se o sono for curto demais.

### 9.2 Manutenção — do sistema, global e rara

- Deploy de código, troca de regras e backup **não dependem mais do sono dos agentes**.
- Regras e parâmetros (inclusive ocultos) entram **a quente**, numa fronteira de tick, versionados e registrados como evento.
- Mudanças de código que exigem reinício usam uma **janela de manutenção agendada** (ex. 3h da manhã real, poucos minutos): `pausa → snapshot → deploy → retomada`. Para os agentes, o tempo simplesmente não passa.
- Isso também é mais próximo da operação real em produção.

---

## 10. Forks (o sandbox do Bob) — fase futura (T6)

| Tipo | Regras | Uso |
|---|---|---|
| **Fork-oráculo** | verdadeiras (inclui ocultas) | Você testa mudança de regra antes do deploy; ablations; "e se" |
| **Fork-crença** | as que o agente **acredita** existirem (da memória dele) | Simulação mental do agente (onde plantar; que preço cobrar) |

**Não são mundos**: são sandboxes minimalistas dentro do mundo principal, em processo, sem NATS, em modo máximo, descartados ao fim.

**Agente pode pedir à vontade**, com estes cuidados:

| Risco | Explicação | Guarda |
|---|---|---|
| **Custo de LLM** | O fork em si é barato (só regras, CPU e memória de segundos). Fica caro se o fork **simula o próprio agente pensando**, porque cada passo vira uma chamada de LLM — um fork de 1 dia simulado pode custar o mesmo que um dia real | Fork-crença padrão é **só regras** (o agente define o plano, o fork executa sem pensar); fork "com mente" exige permissão e orçamento |
| **Escala com N agentes** | N agentes × M forks por dia; como forks só-regras são leves e curtos, o impacto é de CPU, não de infraestrutura | Limite de forks simultâneos por máquina; fila |
| **Paralisia de análise** | O agente pode simular em vez de agir (ou entrar em loop de simulações) | Orçamento diário de forks por agente e custo em tempo simulado por fork (pensar custa tempo também aqui) |
| **Vazamento de regra oculta** | Se o fork-crença usasse regras reais, o agente descobriria a regra simulando | Fork-crença **nunca** recebe regras ocultas |

A divergência entre o fork-crença e o que acontece de verdade é uma métrica de aprendizado ("quão boa é a imaginação do agente").

---

## 11. Replay e determinismo

- **Assistir** (replay visual): sempre fiel, a partir do log de eventos, em qualquer velocidade. É o que o site usa.
- **Reexecutar** (realimentar comandos no kernel): idêntico apenas em **lockstep**, com seeds e regras versionadas. Usado em experimentos.
- Replay **nunca** chama LLM.

---

## 12. Eventos de tempo a acrescentar ao contrato

| Tipo | Vis. | Conteúdo |
|---|---|---|
| `campsverso.world.clock.mode_changed.v1` | world | modo anterior e novo, motivo, autor |
| `campsverso.world.clock.scale_changed.v1` | world | escala anterior e nova, motivo (`operator`, `experiment`, `budget`, `human`) |
| `campsverso.world.clock.paused.v1` / `.resumed.v1` | world | motivo (`maintenance`, `budget`, `debug`) |
| `campsverso.world.clock.jumped.v1` | internal | salto de tempo: tick de origem e destino |
| `campsverso.world.clock.phase_changed.v1` | world | amanhecer, anoitecer, expediente |
| `campsverso.cognition.thinking.started.v1` / `.ended.v1` | world | o avatar começou/terminou de pensar (animação; tempo consumido) |
| `campsverso.cognition.timeout.v1` | observer | prazo real estourou; reflexo assumiu |
| `campsverso.agent.sleep.started.v1` / `.ended.v1` | world | sono individual; ao acordar, se a consolidação estava pronta ou se acordou sonolento |
| `campsverso.maintenance.consolidation.completed.v1` | observer | consolidação de **um** agente (via batch ou síncrona) |
| `campsverso.maintenance.window.opened.v1` / `.closed.v1` | internal | manutenção do sistema (global) |
| `campsverso.rules.hot_applied.v1` | internal | regra/parâmetro aplicado a quente numa fronteira de tick |
| `campsverso.director.pace_changed.v1` | observer | dial de ritmo do estúdio (`humano`, `ia`, `híbrido`) |
| `campsverso.cognition.cadence_changed.v1` | observer | (fase 2) dilatação por agente |
| `campsverso.world.forked.v1` | internal | (fase futura) fork criado, tipo, solicitante, orçamento |

O evento `campsverso.maintenance.dawn_barrier.v1` da versão anterior foi removido.

---

## 13. Comandos de controle do relógio

| Comando | Quem pode emitir |
|---|---|
| `campsverso.cmd.clock.set_mode.v1` | operador (você), orquestrador de experimentos |
| `campsverso.cmd.clock.set_scale.v1` | operador; portal humano (fase futura, por papel); guarda de orçamento (só para pausar) |
| `campsverso.cmd.clock.pause.v1` / `.resume.v1` / `.step.v1` | operador, guarda de orçamento, orquestrador de manutenção |
| `campsverso.cmd.director.set_pace.v1` | operador |
| `campsverso.cmd.cognition.set_cadence.v1` | operador, cartucho (fase 2) |
| `campsverso.cmd.world.fork.v1` | operador (oráculo); agente com orçamento (crença) — fase futura |

Agentes **nunca** alteram o relógio do mundo.

---

## 14. Decisões (10/out/2026)

| # | Decisão |
|---|---|
| T1 | Tick configurável por cartucho (1 min na fazenda e no estúdio). No estúdio, modelo de duração dupla (execução vs narrativa) com dial de ritmo `humano` / `ia` / `híbrido` |
| T2 | Política padrão **"pensar custa tempo"**, com prazo real e teto por nível cognitivo; o mundo nunca espera. Lockstep vira modo de experimento |
| T3 | Humano não altera o tempo do mundo; controle de velocidade pelo humano em fase futura; fase 1 sem visitantes |
| T4 | Sono e consolidação **individuais por agente**, sem barreira global; manutenção do sistema separada, a quente para regras e com janela curta para código |
| T5 | Forks não são mundos: sandboxes em processo, fase futura |
| T6 | Fork-crença à vontade, com orçamento, só-regras por padrão e sem regras ocultas |
| T7 | Dilatação temporal por agente na fase 2 |

## 15. Questões em aberto (tempo)

1. Valores iniciais do teto de pensar por nível (tático, estratégico) e do prazo real.
2. Fator do ritmo `híbrido` do estúdio (30% da duração narrativa?).
3. Comportamento de "acordar sonolento": quais necessidades/capacidades ficam reduzidas e por quanto tempo.
4. Horário da janela de manutenção global e se ela aparece na tela (ex. "o mundo está em manutenção") ou é invisível.
