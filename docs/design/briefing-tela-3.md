# Pedido de tela, 3: a tela do dev

A continuação do [briefing-tela.md](briefing-tela.md) e do [briefing-tela-2.md](briefing-tela-2.md), aprovada pelo usuário em 22/11.

**O que já existe.** A tela do dev entrou no ramo `m23-bases`, no commit 95383ce (ADR-0089), em `apps/ui/src/retro/devscreen.ts`:
- um modal aberto pelo chip do dev;
- com o pedido, as mãos e o modelo, o tempo, os passos e o custo;
- e os últimos passos, um por linha.

Os dados estão certos. O que este pedido muda é a forma: o modal vira o próprio computador do dev, um terminal antigo de fósforo verde, animado, só para acompanhar.

**O que não muda:** o contrato, a projeção e o `screenView`. A tela continua sem ter onde digitar e não decide nada.

O canvas tem a página 6, "a tela do dev". Os prints estão em `escritorio-tela/`:

| Arquivo | O quê |
|---|---|
| `tela-dev.webp` | ao vivo, no fim da animação: o prompt esperando o próximo passo |
| `tela-dev-fim.webp` | no fim da sessão, com o resumo e o cursor parado |
| `tela-dev-vazia.webp` | sem sessão |
| `tela-dev-celular.webp` | no iPhone 17, em tela cheia |

---

## 1. Como abrir

- **Pelo computador do dev, na sala.** É a mesa com a oficina dele, a que tem `workshop` no manifesto.
  - Ao passar o mouse, um contorno amarelo tracejado de 2 px (`#f2c94c`) e um fundo amarelo a 12% aparecem sobre o monitor, com o `title` "Ver a tela do Camps".
  - O clique abre a tela, com o gerente assumido ou não: o computador não é chão, e andar até ele continua pelo menu.
  - No menu do botão direito, a entrada "Ver a tela" faz o mesmo. Ela é só da tela, não é uma proposta.
- **Pelo chip do dev,** no painel do monitor, como hoje. O chip ganha um botão de 30 × 26 depois do texto: um monitorzinho escuro com a borda verde, com `aria-label` "Ver a tela do Camps".
- **Só os devs** (`papel: dev`) têm tela. Sem sessão, ela abre no estado vazio (§3.5).

## 2. O gabinete

O modal é um monitor bege, como os da sala, por cima de tudo.

**O fundo:** `rgb(23 20 31 / 78%)`, com z 34: acima da prancheta (32) e abaixo das mensagens do sistema (40). O escritório continua andando atrás.

**O gabinete**

| Propriedade | Valor |
|---|---|
| tamanho | 940 × 720 px, no máximo a tela menos 24 px de cada lado |
| `padding` | `26px 28px 0` |
| borda | 3 px `#1b1726` |
| raio | 30 |
| fundo | `#e7d9b4` |
| bisel | `inset 5px 5px 0 #f4ead0`, `inset -6px -7px 0 #ae9b72` |
| sombra | `0 30px 80px rgb(0 0 0 / 70%)` |

**A moldura do vidro:** `padding: 6px`, raio `34px / 28px`, fundo `#26222f`, anel de 3 px `#cdbb8f` e `inset 0 3px 0 #1b1726`.

**O queixo do gabinete:** 72 px de altura, embaixo do vidro. Da esquerda para a direita:
1. **A marca:** "CAMPSVERSO" em Pixelify 15, com 3 px entre as letras, em `#85735a`; embaixo, "OFICINA-1 · 640K" em 10 px; e seis frestas de 3 × 16.
2. **A plaqueta, que diz de quem é a tela.** É uma placa de metal:
   - fundo `#c9ced4`, borda de 2 px e bisel `#f6f2e8` / `#9aa1ab`;
   - o rosto do dev, 32 × 32: o retrato dos `retratos` cortado a partir de (4, 4), sobre a cor de fundo dele;
   - o título "Tela do Camps", um `h2` em Pixelify 16, que é o `aria-labelledby` do diálogo;
   - embaixo, "o dev · LLM · mesa 1" em 11 px. É o papel, o controlador e a mesa.
3. **A luz:** 10 px, com o rótulo ao lado.

   | Estado | Cor | Rótulo |
   |---|---|---|
   | ao vivo | `#3fd17a`, piscando a cada 1,6 s | "ao vivo" |
   | no fim | `#ffab2e`, fixa | "terminou" |
   | sem sessão | `#4a4d57` | "sem sessão" |

4. **"Fechar":** 40 px, o botão creme de sempre.

**Mais de um dev:** a plaqueta vira um seletor, uma plaqueta-botão por dev, lado a lado, com `aria-pressed` na que está aberta. Trocar de dev troca a tela sem fechar o modal. Hoje o elenco tem um dev só.

## 3. O terminal

### 3.1 A letra e as cores

**A letra:** VT323, a de terminal antigo, em 22 px com entrelinha de 25 px (no celular, 19 e 22).
- Ela vem com a UI pelo `@fontsource/vt323` (OFL 1.1), como as outras quatro da ADR-0087, e entra nos créditos.
- O `ch` dela é a largura de uma letra; as contas da animação usam isso.

**As cores**

| Para quê | Cor |
|---|---|
| o fundo do vidro | `#050a06` |
| o texto | `#3fd17a` (`telaTexto`) |
| o prompt, os títulos e o fim | `#a8f5c4` (`telaBrilho`) |
| as horas, os colchetes e a tela de entrada | `#4c9a3f` (`verde`) |
| o que falhou | `#ff4646` (`ledVerm`) |
| o robô e "terminou" | `#ffab2e` (`ledAmbar`) |
| o divisor | `#2f6b30` (`verdeEsc`) |

**O fósforo**
- **O brilho do texto:** `text-shadow: 0 0 3px rgb(63 209 122 / 55%), 0 0 12px rgb(63 209 122 / 18%)`.
- **A varredura:** um `::before` com uma linha preta a 30% a cada 3 px.
- **A vinheta:** um `::after` com um gradiente radial, um verde a 4% no meio e um preto a 62% nas bordas.
- **O tubo:** raio `28px / 24px` e `inset 0 0 60px rgb(0 0 0 / 90%)`.
- **Uma tremida leve:** a opacidade cai a 0,9 e 0,95 por um instante, a cada 7 s.

### 3.2 A tela de entrada

No alto, como se o computador tivesse acabado de ligar:

```
Campsverso OS 0.4 (oficina-1) tty1                          ← apagado
login: camps                                                ← apagado
Bem-vindo, Camps. Mãos: Claude Code · modelo: Opus 5.5      ← texto
Pedido #2 · Conector do Codex · sessão desde 14:32          ← texto
────────────────────────────────────────────────────────    ← divisor
```

- O login é o id do dev.
- As mãos e o modelo vêm do `hands` do `screenView`.
- O pedido e a hora do começo vêm do `title` e do `status`.

### 3.3 Cada passo, como um comando

```
camps@oficina:~/pedido-2$ Edit libs/adapters/hands_codex.py          14:37
  [  OK  ] +24 -6
camps@oficina:~/pedido-2$ Bash uv run pytest tests/test_hands_codex.py 14:38
  [FALHOU] 2 falharam, 9 passaram
camps@oficina:~/pedido-2$ robô testador tools/robos/tests            14:44
  [ ROBÔ ] testes verdes
```

**A linha do comando**
- **O prompt:** `<id do dev>@oficina:~/pedido-<n>$`, em `telaBrilho`.
- **O comando:** a ferramenta e o caminho inteiro, quando o passo tem `path`. Sem `path`, é o `summary`, como no `stepShort`.
  - Ele corta com "…" no que couber na linha: a largura do terminal em `ch`, menos o prompt e a hora.
- **A hora,** à direita, apagada.

**A linha do resultado,** com recuo de 2 `ch`:
- **o selo**, no estilo da inicialização do Linux:

  | Selo | Quando | Cor do selo |
  |---|---|---|
  | `[  OK  ]` | o passo deu certo | verde |
  | `[FALHOU]` | `ok` falso | vermelho |
  | `[ ROBÔ ]` | uma chamada da bancada (`tool` igual a `robô`) | âmbar |

  Os colchetes ficam apagados.
- **depois do selo, o `summary`** quando o comando usou o `path`. O texto fica vermelho quando falhou.

### 3.4 Ao vivo e no fim

**Ao vivo.** Os passos chegam depois de feitos (`ok` já vem no fato), então nunca há um passo "em curso" para mostrar.
- Depois do último passo, fica o prompt esperando o próximo, com o cursor piscando: `camps@oficina:~/pedido-2$ █`.
- **O cursor:** um bloco de 11 × 19 em `telaTexto`, com brilho, piscando a cada 1 s.

**No fim** (`finished`, ou a ficha fora de "fazendo", como no `screenView`):

```

──────── fim da sessão ────────                      ← telaBrilho
pronto · 19 voltas · 24 passos · US$ 0,50 · 15 min   ← telaBrilho
o pedido #2 foi entregue: PR #4 · CI verde          ← texto, se a ficha diz
camps@oficina:~/pedido-2$ █                          ← o cursor parado
```

### 3.5 Sem sessão

```
Campsverso OS 0.4 (oficina-1) tty1
login: camps
Nenhuma sessão na oficina ainda.
A tela acende quando o Camps sentar para trabalhar num pedido.

camps@oficina:~$ █
```

### 3.6 A barra de status

Na base do vidro, em vídeo invertido, como a de um `tmux`:
- **o fundo e o texto:** fundo `telaTexto` e texto `#050a06`, numa linha só, sem brilho;
- **à esquerda:** `[camps]` e `#2 Conector do Codex`, que corta com reticências;
- **à direita:** `Claude Code · Opus 5.5 │ 15 min │ 23 passos │ US$ 0,61`;
- **no fim, o segmento do estado,** em fundo preto:

  | Estado | O segmento | Cor |
  |---|---|---|
  | ao vivo | `● AO VIVO` | verde, com o ● piscando |
  | no fim | `TERMINOU · pronto` | âmbar |
  | sem sessão | `SEM SESSÃO` | apagado |

- **Sem `aria-live`:** o tempo muda o tempo todo e faria barulho no leitor de tela.

## 4. A animação

- **A história aparece de uma vez.** Ao abrir, tudo o que a sessão já tem aparece pronto. Só o que chega depois anima.
- **Um passo novo entra deslizando:** `max-height` de 0 a 90 px e opacidade de 0 a 1, em 300 ms.
- **O comando se digita.** A largura vai de 0 a `N ch` com `steps(N)`, a 32 ms por letra, entre 350 ms e 1,6 s, começando 300 ms depois de o passo entrar. O resultado aparece 400 ms depois do último caractere.
  - O texto inteiro está no DOM desde o começo: o efeito é só um recorte da largura. O leitor de tela recebe a linha inteira, uma vez.
- **Vários passos de uma vez** (a volta de uma queda): eles entram em fila, no máximo 0,8 s cada. Com mais de cinco na fila, entram todos juntos, sem digitar.
- **Só acrescenta.** A lista nunca é redesenhada inteira, senão as animações dos passos antigos recomeçariam. Uma linha nova é um nó novo, e as velhas saem pela ponta de cima, até 50, como na projeção.
- **Segue o fim.** O registro usa `flex-direction: column-reverse` com um embrulho dentro, e fica preso embaixo enquanto ninguém subiu (24 px de folga, como hoje).
  - Se a pessoa subiu para reler, aparece uma pílula "▼ 3 linhas novas" no canto de baixo, acima da barra, em `telaTexto` com o texto preto. O clique desce até o fim.
- **A barra de rolagem:** fina, em `verdeEsc`.
- **Com `prefers-reduced-motion`:** sem a tremida, sem o piscar, sem digitar e sem deslizar. As linhas aparecem prontas.

## 5. Acessibilidade e teclado

- **O diálogo:** `role="dialog"` e `aria-modal`, com o título na plaqueta.
  - Esc e "Fechar" fecham. O foco vai para o "Fechar" ao abrir e volta para quem abriu.
  - O `keydown` para no modal, como hoje: o teclado anda com o avatar.
- **O registro:** `role="log"` e `aria-live="polite"`, que anuncia a linha nova inteira, com o selo por extenso ("ok", "falhou", "robô").
- **O contraste sobre `#050a06`:**

  | Cor | Contraste |
  |---|---|
  | o prompt (`telaBrilho`) | cerca de 15,7:1 |
  | o texto | cerca de 10:1 |
  | o apagado | cerca de 5,7:1 |
  | o vermelho | cerca de 5,9:1 |
  | o âmbar | cerca de 10,6:1 |

## 6. No celular

- **Tela cheia:**
  - o fundo sem margem;
  - o gabinete com raio 18 e `padding: 10px 8px 0`;
  - o queixo com 60 px, só com a plaqueta, a luz e o "Fechar".
- **O terminal:**
  - 19 px com entrelinha de 22;
  - o prompt curto, `$`;
  - o comando quebra a linha (`pre-wrap`, `break-all`), sem o efeito de digitar;
  - a hora vai para o fim da linha do resultado.
- **A barra:** `[camps] #2 … 23 passos  ● AO VIVO`.

## 7. Uma opção para depois: as respostas do modelo

Hoje a tela mostra o que o dev **fez**: a ferramenta, o arquivo e um resumo de até 200 letras. O texto que o modelo escreve entre os passos não chega à projeção.

Se a sessão guardar um trecho desse texto, uma mudança de contrato que pede ADR, o terminal o mostra como um comentário de shell, apagado e sem selo:

```
# vou criar o conector a partir do do Claude Code e trocar só o transporte
camps@oficina:~/pedido-2$ Write libs/adapters/hands_codex.py          14:35
```

Fica para quando o usuário pedir.

## 8. Como conferir

- **Os testes de unidade:**
  - o comando e o resultado de um passo, com e sem `path`, e o do robô;
  - o corte com "…" pela largura em `ch`;
  - as linhas do fim e do vazio;
  - o selo por extenso para o leitor de tela.
- **No navegador:**
  - o clique no computador da sala abre a tela do dev certo;
  - o botão do chip também abre;
  - um passo novo entra e se digita, e os antigos não piscam de novo;
  - subir a lista mostra a pílula, e o clique nela desce;
  - Esc fecha, e o gerente não anda com o teclado enquanto a tela está aberta;
  - os prints ao lado dos do canvas, em 1456 × 816 e 402 × 874.
