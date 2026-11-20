# Pedido de arte: o M25, o ciclo fecha

A continuação dos pedidos do escritório ([briefing-arte-escritorio.md](briefing-arte-escritorio.md), [briefing-arte-bancada.md](briefing-arte-bancada.md) e [briefing-arte-baloes.md](briefing-arte-baloes.md)), para o M25 (ADR-0083). A entrega do dev vira um PR no GitHub, o escritório troca sozinho para a versão nova quando o usuário mescla, e o dev cria o segundo robô, o briefing. O texto entre as linhas abaixo é o pedido; o usuário o dispara para o Claude Design na mesma sessão que fez a arte do escritório.

---

## O pedido

Continuando a arte do escritório que você já fez (as folhas e o `metadados.json` em `docs/design/escritorio-arte/folhas/`), quero quatro peças para a próxima fase. **Todas as regras de antes valem:**
- a grade de 32 × 32;
- a vista de cima em 3/4, com só a face sul e o topo;
- o contorno e as camadas, com a âncora no meio da borda de baixo da pegada;
- pixel art sem antialiasing, sem degradê e sem transparência parcial;
- tudo desenho original seu.

**A paleta continua a mesma** (47 cores). Use as que existem; se faltar uma, acrescente no máximo uma, sem passar de 48, com o par de penumbra e de escuro na tabela da luz. As luzes novas são **emissivas** à noite, como as dos robôs: ficam acesas no escuro.

### O que muda no escritório

Até agora, o dev entregava o trabalho e o gerente aceitava no quadro. Agora:
1. o dev entrega;
2. **o publicador**, um robô da bancada, carimba a entrega e a envia para o GitHub como um PR;
3. o usuário revisa e mescla lá fora;
4. **o escritório se atualiza sozinho** para a versão nova, e uma placa na parede mostra a versão que roda.

A criação do dev nesta fase é **o briefing**: um robô que junta numa pasta o que uma sessão de trabalho vai ler.

### 1. O robô do briefing

Mais uma configuração do corpo-base dos robôs, como o testador, o revisor e o publicador:
- **a cor do corpo:** amarelo ou âmbar, da paleta, para não confundir com os outros três;
- **a cabeça:** redonda;
- **o acessório:** uma pasta de documentos, com folhas aparecendo.

As mesmas quatro animações dos outros robôs, de frente, uma linha por animação:

| Linha | Animação | Quadros | O que é |
|---|---|---|---|
| 0 | parado | 2 | a luz da antena pisca devagar; a telinha do peito apagada |
| 1 | trabalhando | 4 | ele folheia a pasta, e uma folha entra nela; linhas correndo na telinha |
| 2 | passou | 2 | a pasta fechada, a telinha verde com um sinal de certo, a luz verde |
| 3 | falhou | 2 | as folhas espalhadas, a telinha vermelha com um X, a luz vermelha |

A folha: `robo_briefing.png`, com 4 colunas e 4 linhas de 32 × 32, âncora em (16, 32).

### 2. O publicador trabalhando de verdade

A folha do publicador (`robo_publicador.png`) já existe, com o trabalho de todos os robôs: a antena girando. Ele ganha o trabalho dele, na mesma folha e nas mesmas linhas:

| Linha | Animação | Quadros | O que é |
|---|---|---|---|
| 1 | trabalhando | 4 | ele carimba um envelope, e o envelope sobe e some para cima |
| 2 | passou | 2 | um envelope pequeno com um selo verde, acima da cabeça |
| 3 | falhou | 2 | o envelope com um X vermelho, caído na bancada |

A linha 0 (parado) continua como está.

### 3. A placa da versão

**O que é:** uma placa de metal pequena na parede, como a de um elevador ou de uma máquina, onde a tela escreve a versão que roda: o código curto do commit (7 caracteres, como `7c6b8ac`) e a data (`20/11`), em duas linhas, na fonte pixel que você já fez (8 × 12).

**Onde fica:** na parede de cima da sala, num trecho livre perto do relógio ou da porta. Escolha o lugar que fique bem e marque na prévia; declare o tile no `metadados.json`, em `posicao`.

| Peça | Quadro | Pegada | Camada |
|---|---|---|---|
| a placa | 64 × 64 | 2 tiles de parede | `parede` |

**Os quadros**, numa linha, com uma luz pequena num canto da placa:

| Quadro | O que é |
|---|---|
| `rodando` | a luz verde, acesa |
| `atualizando` | a luz âmbar acesa |
| `atualizando2` | a luz âmbar apagada (a tela alterna os dois enquanto o escritório se atualiza) |
| `voltou` | a luz vermelha: a versão nova falhou, e o escritório voltou para a de antes |

**O texto:** declare na entrada da placa `texto: { x, y, largura, altura, cor }`, o retângulo onde as duas linhas cabem, com a cor do texto como nome da paleta. A placa vem sem texto; a tela escreve.

A folha: `placa_versao.png`, com 4 colunas e 1 linha.

### 4. O PR nas fichas do quadro e nos ícones

As fichas do quadro de cortiça (`fichas.png`, 10 × 10) mostram os pedidos. Uma ficha com PR ganha um **selo** pequeno no canto de baixo à direita:

| Selo | O que mostra |
|---|---|
| `pr` | o PR aberto: duas bolinhas ligadas por uma linha, como um ramo |
| `ci_verde` | o PR com os testes verdes: o ramo com um ponto verde |
| `ci_vermelho` | o PR com os testes vermelhos: o ramo com um ponto vermelho |
| `mesclado` | o PR mesclado: as duas linhas juntas numa só, com um ponto roxo ou azul |

A folha: `selos.png`, 4 colunas de 6 × 6. Declare `selos: { nome: [coluna, linha] }` e, na entrada das fichas, `selo: [x, y]`, onde o selo pousa na ficha.

**Os mesmos quatro, em 16 × 16, na folha dos ícones** (`icones.png`), para o painel ao lado do mapa e para o balão de ação. Mais um:

| Nome | O que mostra | Onde |
|---|---|---|
| `atualizando` | duas setas em círculo | no HUD, enquanto o escritório se atualiza |

Os ícones novos entram no fim de `icones.png`, na ordem das tabelas, e no `icones` do `metadados.json`.

### A entrega

- **As folhas novas e as atualizadas** vão para `docs/design/escritorio-arte/folhas/`: `robo_briefing.png`, `robo_publicador.png` com o trabalho novo, `placa_versao.png`, `selos.png` e `icones.png` com os ícones no fim.
- **O `metadados.json` ganha as entradas novas** no formato das outras: `arquivo`, `grupo`, `quadro`, `colunas`, `linhas`, `pegada`, `ancora`, `camada` e `quadros`, e mais:
  - o robô leva `animacoes` e `configuracao`;
  - a placa leva `posicao` e `texto`;
  - os selos levam `selos`, e as fichas, `selo`.
- **A prévia** (`escritorio-arte.html`) mostra:
  - a bancada com três robôs nos apoios: o testador, o briefing e o publicador, este carimbando;
  - a placa na parede, rodando e atualizando, com o texto de exemplo `7c6b8ac` e `20/11`;
  - o quadro com três fichas: uma com o selo `pr`, uma com `ci_verde` e uma com `mesclado`;
  - de dia e à noite.
- **A API de exportar folhas** da página passa a exportar as peças novas, sem precisar clicar em nada.
- **Não escreva nomes** nos robôs nem na placa: a tela escreve.

---

## Para nós

- **Quando a arte chegar** (`make arte-escritorio` copia as folhas para os cartuchos e monta o tileset):
  - o briefing entra na bancada quando o PR dele for mesclado e o escritório se atualizar;
  - o publicador trabalha enquanto o publicador de verdade abre o PR (os fatos `workshop.robot_started` e `robot_called` que ele publica);
  - a placa segue o estado do supervisor: rodando, atualizando ou voltou; o texto vem do campo `build` da sessão da tela;
  - os selos seguem os fatos `office.ticket.pr_*`, nas fichas e no painel;
  - o ícone `atualizando` aparece no HUD durante a troca de versão.
- **Até lá,** a placa e o selo saem em texto na tela, e o publicador usa o trabalho de todos os robôs.
- **O revisor** (`robo_revisor.png`) continua sem uso: a revisão do M25 é feita por um modelo fora do mundo (ADR-0083, decisão 7). A folha fica pronta para quando ele virar um personagem.
