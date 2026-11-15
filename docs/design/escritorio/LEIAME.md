# Escritório CampsVerso · protótipo

O escritório de programação na mesma linha do estúdio do CampsCast:

- dois andares em corte, como casa de bonecas, em pixel art;
- a equipe no relógio de São Paulo;
- replay do dia, registro de eventos e fichas.

A diferença é a equipe: um humano (o Camps, dev líder) e robôs retrô, que são os agentes de IA.

Feito no Claude Design em 08/11/2026 e entregue por engano na pasta do CampsCast (`prototipos/escritorio/`); movido para cá em 14/11/2026, sem mudar nada além deste parágrafo e do caminho abaixo. Não vai ao ar com nada: é referência navegável, como as imagens desta pasta. O estúdio do CampsCast não foi tocado.

## Como abrir

Os módulos JS não carregam por `file://`; precisa de um servidor local:

```bash
cd ~/CampsVerso/docs/design/escritorio
python3 -m http.server 8000
# http://localhost:8000/
```

Parâmetros úteis:

- `?sim=10:30`, `?sim=22:00` ou `?sim=folga`: simula o horário.
- `?replay&em=14:47&pausa`: abre o replay parado num momento.
- `?ficha=revisor&aba=revisoes`: abre uma ficha.
- `?ficha=mesa:m3`: abre a ficha de uma mesa vaga.
- `folha.html`: todos os quadros de animação; aceita `?id=camps,revisor&estados=parado&k=4`.

## O que tem

### Planta

**Em cima:**

- **Desenvolvimento.** Seis mesas com divisórias de cubículo. Hoje duas têm dono (Camps e Revisor); as outras ficam cobertas por lençol, com etiqueta VAGA ou RESERVADA. Na parede ficam o quadro de tickets, que se mexe com os dados, o relógio e o pôster RUN. No fundo, a estante com a doca do drone e a estação do tubo pneumático do Mensageiro.
- **Planejamento** (no lugar do arquivo). Sala de reunião com o quadro branco da especificação atual, mesa e cadeiras. É onde acontecem a daily e a retro.

A cabine de locução e as áreas em obras saíram.

**Embaixo:**

- **Portaria**, com o mesmo Vigia do estúdio.
- **Café e jogos**: bancada com espresso, geladeira, mesa alta, pôster HI SCORE, estante de cartuchos e a TV de tubo com o console. Na frente, um sofá de costas para nós. No almoço, o Camps joga e a TV passa um joguinho de plataforma.
- **Servidores** (no lugar da técnica):
  - racks com LEDs, que piscam mais rápido quando o CI roda;
  - unidade de fita com rolos que giram;
  - painel do CI e semáforo (amarelo rodando, verde, vermelho piscando);
  - console de publicação com o botão vermelho, que acende no deploy;
  - nobreak e a chegada do tubo pneumático.

**Escada.** Tem um trilho listrado: o robô de rodas sobe numa plataforma e o drone voa por cima.

### Equipe

Todos em 40 × 56, desenhados em código, com contorno escuro:

| Quem | Corpo | Papel | Animações |
|---|---|---|---|
| Camps | humano, barba e camiseta `>_` | dev líder | digitando, café, andando, de costas jogando no sofá |
| Revisor | aranha de quatro pernas com lupa | revisão e testes | sobe na mesa e passa a lupa no papel |
| Integrador | monociclo com tela de LEDs | CI, build e deploy | LEDs correndo, roda girando, carrega o formulário contínuo |
| Pesquisador | drone com disquete | documentação e dependências | hélices, flutuação, feixe ciano na estante, pousa na doca |
| Mensageiro | cabeça redonda no tubo pneumático | avisos | espia do tubo e sai com o envelope |
| Vigia | o do estúdio | portaria | ronda de lanterna à noite |

**De noite**, os robôs ficam na recarga, com um LED âmbar pulsando.

### Estados pelo relógio de São Paulo

| Chip | Quando | O que aparece |
|---|---|---|
| EXPEDIENTE | horário de trabalho | cada um no seu lugar; quem fez algo há pouco (8 minutos do dia) tem balão |
| ALMOÇO | horário de almoço | Camps no sofá; os robôs seguem com a fila |
| FECHADO | fora do expediente em dia útil | robôs na recarga; o Vigia lê a agenda e os números do dia; de noite, tudo azul menos a portaria, os servidores e o corredor |
| FOLGA | fim de semana ou feriado | placa no café com a volta da equipe |
| REPLAY | replay aberto | o dia evento a evento |

**Replay:**

- quatro velocidades: 1× (9 h 9 min), 6×, 60× (9 min) e Máximo (cerca de 2 min, um evento a cada 0,9 a 2,6 s);
- botão de próximo evento;
- momentos do dia;
- clicar num evento do registro leva a linha do tempo até ele.

### Painel do operador

Fica ao lado da cena no computador e embaixo no celular. Mostra só números contados dos eventos até o momento:

- tickets entregues;
- PRs mesclados;
- CI verde (X de Y);
- rodadas de revisão;
- deploys;
- cafés do Camps, com as xícaras;
- custo de modelo, com a barra contra o limite do JSON.

Embaixo vêm os eventos, com etiqueta de origem, legenda e "Como ler".

### Barra de status

No expediente:

- a pendência mais importante (aguardando o CI do PR #41, CI vermelho, pedido de mudança, esperando revisão);
- o momento do dia;
- o sprint.

Fora do expediente: o próximo expediente e os números do dia.

### Fichas

Abas **Hoje**, a aba própria de cada um e **Perfil**. As abas próprias:

- Camps: **Sprint**, com a especificação e os tickets por coluna;
- Revisor: **Revisões**, por PR, com as rodadas;
- Integrador: **CI e deploys**;
- Pesquisador: **Pesquisas**;
- Mensageiro: **Avisos**;
- Vigia: **Plantão**.

O quadro de tickets e o quadro branco abrem o Sprint; o painel do CI abre o Integrador. Clicar numa mesa coberta mostra para quem ela está reservada.

### Abra um ticket

O formulário diz "Protótipo: nada foi enviado". No expediente, o Mensageiro sai do tubo com o balão de reação (origem "site"); fora dele, quem responde é o Vigia.

### Celular

Mesma câmera e minimapa do estúdio, com paradas extras nas salas largas (mesas, vagas e estante; café, sofá e videogame). O registro fica embaixo da cena e a ficha vira uma folha que sobe de baixo.

## Mantido do estúdio

- O motor separado da cena: `motor.js` devolve o quadro, `cena2d.js` só desenha.
- A regra de fidelidade dos balões e o corte em cerca de 90 caracteres com "…" (o texto inteiro fica no registro).
- O fuso de São Paulo, a acessibilidade (botões nos personagens, `aria-live`, foco devolvido, `prefers-reduced-motion`) e o tema claro/escuro.
- Sem cookies e sem rastreamento.

## Pendências

- **Dados reais.** Tudo é demonstração. A equipe, os modelos ("LLM via OpenRouter (exemplo)") e o dia 06/11 são inventados para desenhar. Falta decidir de onde vêm os eventos de verdade (o CampsVerso, o GitHub ou os dois) e gerar `ultimo.json` no contrato `campsverso.escritorio/1` (veja `CONTRATO.md`).
- **Envio do ticket.** Quando existir envio de verdade, falta uma política de privacidade para o escritório, como a do CampsCast.
- **3D.** Ficou de fora, como no estúdio.
- **Tela entre 1100 e cerca de 1700 px em densidade 1.** A cena usa escala fracionária, como no estúdio.
- **Mesa do recém-chegado.** O lençol sai na hora do evento de chegada, alguns segundos antes de o robô chegar andando.
- **Novos corpos.** Só existem os cinco: humano, pernas, rodas, drone e tubo. Um corpo diferente (esteira, braço mecânico) precisa ser desenhado em `sprites.js`.
