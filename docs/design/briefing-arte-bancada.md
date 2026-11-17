# Pedido de arte: a bancada e os robôs

A continuação do pedido do escritório ([briefing-arte-escritorio.md](briefing-arte-escritorio.md)), para a parte 4 do M24: o dev cria o primeiro robô, o testador, e ele aparece na bancada. O texto entre as linhas abaixo é o pedido; o usuário o dispara para o Claude Design na mesma sessão que fez a arte do escritório.

---

## O pedido

Continuando a arte do escritório que você já fez (as folhas e o `metadados.json` em `docs/design/escritorio-arte/folhas/`), quero três peças novas. **Todas as regras de antes valem:**
- a grade de 32 × 32;
- a vista de cima em 3/4, com só a face sul e o topo;
- o contorno e as camadas, com a âncora no meio da borda de baixo da pegada;
- pixel art sem antialiasing, sem degradê e sem transparência parcial;
- tudo desenho original seu.

**A paleta continua a mesma.** Use as cores que já existem. Se precisar de uma cor nova (a luz de um robô, por exemplo), acrescente no máximo três, sem passar de 48 no total, e dê a cada uma o par de penumbra e de escuro na tabela da luz (`luz.penumbra` e o escuro), como as outras. As luzes dos robôs são **emissivas** à noite, como `telaTexto` e `telaBrilho`: ficam acesas no escuro.

### 1. A bancada dos robôs

**Onde fica:** no cubículo livre ao lado do dev, na fileira de cima. Ela entra no lugar da mesa vazia, no tile (8, 4), com a pegada de 3 × 1 nas colunas 7 a 9, e a cadeira desse cubículo sai.

**O que é:** uma bancada de oficina, de madeira com o tampo de aço ou de borracha, mais baixa e mais funda que a mesa do dev. Nela ficam:
- um painel perfurado na divisória do fundo, com algumas ferramentas penduradas (chave de fenda, alicate, um rolo de fio);
- um multímetro ou um pequeno osciloscópio de tubo, num canto;
- **o tampo livre**, onde os robôs ficam.

| Peça | Quadro | Pegada | Quadros |
|---|---|---|---|
| a bancada | 96 × 64 | 3 × 1 | 2: vazia, e com o osciloscópio ligado (a onda na tela) |

**Os pontos de apoio:** declare no `metadados.json`, na entrada da bancada, `apoios`: três pontos (x, y) no quadro, um sobre cada tile da pegada, onde a âncora de um robô pousa no tampo (algo como `[[16, 40], [48, 40], [80, 40]]`, com o y da linha do tampo). A tela põe um robô em cada ponto, na ordem, conforme o registro de robôs.

### 2. O robô, de um corpo-base

Os robôs são pequenos, de mesa, como brinquedos de lata: um corpo com uma telinha no peito, a cabeça com um visor e uma antena. Faça como os personagens: **um corpo-base parametrizável**, e cada robô é uma configuração dele:
- a cor do corpo: três, da paleta;
- o formato da cabeça: quadrada ou redonda;
- o acessório do robô: o que diz o ofício dele.

O primeiro é **o testador**: corpo verde-claro, cabeça quadrada, e uma lupa na mão. Deixe prontos mais dois para o futuro, sem uso por enquanto:
- **o revisor:** corpo azul, cabeça redonda, uma prancheta;
- **o publicador:** corpo vermelho, cabeça quadrada, um carimbo.

| Peça | Quadro | Âncora | Altura do robô |
|---|---|---|---|
| cada robô | 32 × 32 | (16, 32) | de 20 a 24 px, de frente para a câmera |

**As animações,** todas de frente, na mesma ordem para todos os robôs, uma linha por animação na folha do robô:

| Linha | Animação | Quadros | O que é |
|---|---|---|---|
| 0 | parado | 2 | a luz da antena pisca devagar; a telinha do peito apagada |
| 1 | trabalhando | 4 | a antena gira ou o braço mexe; linhas correndo na telinha |
| 2 | passou | 2 | a telinha verde, com um sinal de certo; a luz verde |
| 3 | falhou | 2 | a telinha vermelha, com um X; a luz vermelha |

Uma folha por robô: `robo_testador.png`, `robo_revisor.png` e `robo_publicador.png`, cada uma com 4 colunas e 4 linhas. O que uma animação não usa fica transparente.

### 3. O monitor da mesa do dev mostra a oficina

A mesa do dev (`mesa_dev.png`) ganha três quadros na mesma folha, depois dos que existem:
- **lendo:** um arquivo aberto, com o número das linhas na margem;
- **testes verdes:** uma barra verde cheia;
- **testes vermelhos:** uma barra vermelha, com uma linha de erro embaixo.

A tela usa o quadro do último passo do dev na oficina.

### A entrega

- **As folhas novas e a atualizada** vão para `docs/design/escritorio-arte/folhas/`: `bancada.png`, os três `robo_*.png` e `mesa_dev.png`, com os quadros novos no fim.
- **O `metadados.json` ganha as entradas novas** no formato das outras: `arquivo`, `grupo`, `quadro`, `colunas`, `linhas`, `pegada`, `ancora`, `camada` e `quadros`. A bancada leva também os `apoios`. Os robôs levam `animacoes`, como os personagens, e `configuracao` (a cor, a cabeça e o acessório).
- **A prévia** (`escritorio-arte.html`) mostra a bancada no cubículo ao lado do dev, com o testador trabalhando no primeiro apoio, de dia e à noite.
- **A API de exportar folhas** da página passa a exportar as peças novas, sem precisar clicar em nada.
- **Não escreva nomes** na bancada nem nos robôs: a tela escreve.

---

## Para nós

- **Quando a arte chegar:**
  - a bancada entra na sala no lugar da mesa vazia de (8, 4), e a cadeira desse cubículo sai;
  - os robôs do registro (`robos:` no `escritorio.yaml`) aparecem nos apoios;
  - a animação do robô segue o estado: parado; trabalhando enquanto o `chamar_robo` roda; passou ou falhou pelo resultado;
  - o monitor do dev segue o último `workshop.step.v1`.
- **Até lá,** um desenho provisório no estilo da sala (o plano da parte 4 do M24, decisão 3).
