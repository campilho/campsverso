# Prompts das telas do escritório (v0.3)

Os prompts usados em 14 a 17/out/2026 para pedir referências visuais do escritório a ferramentas de desenho (Claude Design, Image2, Nano Banana, MidJourney). Os resultados e a análise estão no [README](README.md) da pasta. Dica que funcionou: anexar o print atual da fazenda para a ferramenta manter o layout da tela, e pedir 1920×1080.

## A1 — Cubículo dos anos 80, tela do operador, dia

```
Quero uma imagem de referência (não é código) para a tela de um simulador 2D de agentes de IA. Estilo: pixel art 16 bits como os jogos do Mega Drive dos anos 90 (paleta limitada, cerca de 60 cores na tela, sem anti-aliasing, dithering discreto), vista de cima em 3/4 como nos RPGs clássicos, montada numa grade de tiles de 32 px. Imagem em paisagem 16:9, sem logotipos nem marcas; todo texto da interface em português.

A cena: um escritório de programação dos anos 80 com um único programador. Um cubículo de divisórias bege, carpete cinza, luz fluorescente no teto, uma janela com a cidade ao fundo (é manhã). Na mesa: um computador bege com monitor CRT de fósforo verde, teclado grande, impressora matricial ao lado, telefone de teclas, caneca de café, pilha de papéis. Na parede do cubículo, um quadro de cortiça com fichas presas por alfinetes, em quatro colunas: "a fazer" (2 fichas), "fazendo" (1), "revisão" (0), "publicado" (5). Uma lousa branca com o título da especificação atual. Num canto, uma cafeteira de jarra e um arquivo de aço. Em outro canto, um rack de servidor pequeno com um botão vermelho escrito "publicar". Uma porta por onde o cliente entra. Há espaço vazio para mais dois cubículos, ainda sem móveis.

O programador é o único avatar: homem de cabelo castanho-claro com topete, barba castanho-clara, sobrancelhas grossas, camisa vermelha de manga comprida, calça azul, sentado digitando. Sobre a cabeça dele, uma barra de progresso fina com o texto "codificando · ticket 12 · 40%". Na porta, o cliente (outro personagem, de pé) com um balão de fala: "novo ticket".

A interface ao redor do mapa tem posições fixas. No alto à esquerda: o retrato do avatar, "dia 3 · 10:30" e o clima (ensolarado). Abaixo, barras de necessidades: energia 70, foco 55, café 2/5. À direita, o painel do operador em texto pequeno: métricas do dia (tickets entregues 1, PRs mesclados 5, CI verde 4 de 5, rodadas de revisão 2, custo de hoje US$ 2,10 de 5,00), uma linha do tempo dos eventos recentes com três cores por visibilidade (mundo, agente, interno) e os controles do relógio: pausar, avançar 1 tick, 1×, 6×, máximo. Sobre a borda de baixo do mapa, uma faixa de aviso: "aguardando o CI do PR #41".

Se puder, uma segunda imagem com a mesma cena às 23:00: luz da luminária só sobre a mesa, janela escura, o programador ainda digitando e a faixa "hora extra · foco 20".
```

## A2 — Anos 80, a planta crescendo (tríptico)

```
Mesmo estilo da imagem anterior (pixel art 16 bits, Mega Drive, vista de cima em 3/4, tiles de 32 px, sem logotipos). Desta vez sem a interface: só o mapa do escritório, em três quadros lado a lado, mostrando a mesma planta crescendo, como um escritório de software atravessando os anos 80 e 90.

Quadro 1, "um dev": um cubículo com CRT de fósforo verde, o quadro de cortiça, a cafeteira, o rack com o botão "publicar" e a porta do cliente; o resto do piso vazio.

Quadro 2, "dev e revisor": um segundo cubículo encostado no primeiro, com dois monitores CRT e uma pilha de listagens impressas; o quadro de cortiça agora com a coluna "revisão" cheia; uma segunda pessoa de camisa listrada sentada lendo.

Quadro 3, "o squad": quatro cubículos (dev, revisor, pesquisador com uma estante de livros e manuais, testador com um segundo computador só para testes), uma mesa redonda de reunião com cadeiras, o quadro de cortiça virou uma parede inteira de fichas e o rack de servidor cresceu. Mantenha a porta, a janela e a cafeteira nos mesmos lugares nos três quadros.
```

## B1 — Co-work preto e vidro, tela do operador, dia

```
Quero uma imagem de referência (não é código) para a tela de um simulador 2D de agentes de IA. Estilo: pixel art 16 bits como os jogos do Mega Drive dos anos 90 (paleta limitada, sem anti-aliasing, dithering discreto), vista de cima em 3/4 como nos RPGs clássicos, montada numa grade de tiles de 32 px. Imagem em paisagem 16:9, sem logotipos nem marcas; todo texto da interface em português.
[Alternativa, se quiser comparar sem pixel: "Estilo: ilustração flat e limpa, vista de cima em 3/4, numa grade visível de 32 px."]

A cena: o espaço aberto de uma startup, moderno e futurista, todo preto e vidro. Piso de concreto escuro, paredes de vidro do chão ao teto com a cidade ao fundo (é manhã), fitas de LED no teto, acentos em ciano e magenta. Uma bancada longa compartilhada com seis lugares; só um ocupado: notebook num suporte, dois monitores, cadeira ergonômica, fones de ouvido, caneca. Os outros cinco lugares vazios, com as cadeiras encostadas e levemente esmaecidos, como lugares reservados para o futuro. Uma sala de reunião de vidro, uma tela grande na parede com o quadro digital em quatro colunas: "a fazer" (2 cartões), "fazendo" (1), "revisão" (0), "publicado" (5). Um balcão de café com máquina de espresso, plantas, um rack de servidor com LEDs e um console escrito "publicar". Uma porta de vidro por onde o cliente entra.

O programador é o único avatar: homem de cabelo castanho-claro com topete, barba castanho-clara, sobrancelhas grossas, camiseta vermelha, calça azul, sentado digitando. Sobre a cabeça dele, uma barra de progresso fina com "codificando · ticket 12 · 40%". Na porta, o cliente (outro personagem, de pé) com um balão de fala: "novo ticket".

A interface ao redor do mapa tem posições fixas. No alto à esquerda: o retrato do avatar, "dia 3 · 10:30" e o clima (ensolarado). Abaixo, barras de necessidades: energia 70, foco 55, café 2/5. À direita, o painel do operador em texto pequeno: métricas do dia (tickets entregues 1, PRs mesclados 5, CI verde 4 de 5, rodadas de revisão 2, custo de hoje US$ 2,10 de 5,00), uma linha do tempo dos eventos recentes com três cores por visibilidade (mundo, agente, interno) e os controles do relógio: pausar, avançar 1 tick, 1×, 6×, máximo. Sobre a borda de baixo do mapa, uma faixa de aviso: "aguardando o CI do PR #41".

Se puder, uma segunda imagem com a mesma cena às 23:00: a cidade acesa atrás do vidro, só os LEDs e os monitores iluminando, o programador ainda na mesa e a faixa "hora extra · foco 20".
```

## B2 — Co-work, a planta crescendo (tríptico)

```
Mesmo estilo da imagem anterior (pixel art 16 bits, preto e vidro, vista de cima em 3/4, tiles de 32 px, sem logotipos). Sem a interface: só o mapa, em três quadros lado a lado, a mesma planta crescendo.

Quadro 1, "um dev": a bancada de seis lugares com um ocupado (notebook e dois monitores), a tela grande do quadro, o balcão de café, o rack com o console "publicar" e a porta de vidro.

Quadro 2, "dev e revisor": o lugar ao lado ocupado por uma segunda pessoa com um monitor ultrawide, lendo um diff; a tela grande com a coluna "revisão" cheia; a sala de reunião de vidro com a luz acesa.

Quadro 3, "o squad": quatro lugares ocupados (dev, revisor, pesquisador com uma segunda tela cheia de artigos, testador com um painel de CI verde e vermelho), uma segunda bancada ainda vazia, um canto de reunião em pé com um sofá, e a tela grande virou uma parede de telas. Mantenha a porta, o balcão de café e o rack nos mesmos lugares nos três quadros.
```
