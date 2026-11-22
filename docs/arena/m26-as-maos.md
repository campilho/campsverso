# A comparação das mãos (22/nov/2026)

**O que é:** o critério do M26 (ADR-0089, decisão 10; o plano do M26, §7). O mesmo pedido, feito pelas duas mãos com o mesmo modelo, para separar o efeito do harness:
- **o nosso harness:** a `WorkSession` da mente, com as oito ferramentas da oficina;
- **o Claude Code:** pelo SDK, no mesmo espaço, com as ferramentas dele, o cercado e a porta das mãos.

O modelo foi o Opus 5.5 nas duas mãos. Por último, o Fable 5.2 fez no Claude Code um dos três pedidos. Ferramenta: `make maos` (as corridas, pagas) e `make maos-relatorio` (a tabela, lida dos fatos de cada corrida).

**As corridas:**
- Cada uma é o escritório de teste em processo, do quadro à entrega:
  - o gerente-script escreve o pedido às 9:30, com as mãos e o modelo na prancheta;
  - o dev senta, o robô do briefing abre a sessão, e o dev trabalha;
  - a revisão da oficina olha o patch, e a entrega sai.
- **O espaço** é um clone deste repositório:
  - todas no mesmo commit, o `d257b83`, o fim da parte 3;
  - com o ambiente Python do espaço (`uv sync`, sem rede), como no escritório vivo.
- **A memória** começa limpa em cada corrida, e a ordem das mãos alterna de um pedido para o outro.
- **O teto** é o do pedido no escritório, US$ 5 por corrida. Ninguém chegou perto.

**Os três pedidos,** robôs pequenos da bancada, com teste de aceite (os textos estão em `tests/support/src/campsverso_testkit/maos.py`):
- **o contador** (P): um robô novo que conta as linhas de código e de teste por pasta, posto na bancada;
- **a história** (M): o briefing ganha a seção dos últimos commits dos arquivos prováveis;
- **o testador que aponta** (M): o testador diz os arquivos mudados que nenhum teste importa.

**A conferência é por fora,** no espaço, depois da sessão:
- **o CI de perto:** o `ruff` nos arquivos mudados, o `pyright` estrito nos que a configuração do projeto cobre (ela não cobre `tools/robos`), os testes da bancada e as pastas de teste que o patch mudou;
- **o aceite:** um teste escondido por pedido, que o dev nunca viu, conferindo o teste de aceite.

## O resultado

<!-- tabela: make maos-relatorio -->

| # | Pedido | Mãos | Modelo | Entregou | Voltas | Passos | Testador | Custo | Tempo | Patch | CI de perto | Aceite |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| 1 | contador | nosso harness | opus-5-5 | sim | 21 | 21 | 1 | US$ 0,27 | 1,2 min | 5 arq., +94 -2 | sim | sim |
| 2 | contador | Claude Code | opus-5-5 | sim | 17 | 16 | 1 | US$ 0,18 | 2,0 min | 5 arq., +99 -2 | sim | sim |
| 3 | historia | Claude Code | opus-5-5 | sim | 16 | 15 | 0 | US$ 0,23 | 2,4 min | 2 arq., +120 -7 | sim | sim |
| 4 | historia | nosso harness | opus-5-5 | sim | 21 | 21 | 0 | US$ 0,32 | 1,5 min | 2 arq., +115 -6 | sim | sim |
| 5 | aponta | nosso harness | opus-5-5 | sim | 35 | 35 | 9 | US$ 0,39 | 2,1 min | 3 arq., +115 -0 | sim | sim |
| 6 | aponta | Claude Code | opus-5-5 | sim | 13 | 12 | 0 | US$ 0,15 | 1,9 min | 2 arq., +100 -0 | sim | sim |
| 7 | historia | Claude Code | fable-5-2 | sim | 6 | 5 | 0 | US$ 0,24 | 2,0 min | 2 arq., +118 -6 | sim | sim |

**Total:** 7 corridas, US$ 1,79.

**As ferramentas de cada corrida**, pelos passos (`workshop.step.v2`):

- 1 (contador, nosso harness, opus-5-5): buscar 3, editar 3, escrever 2, ler 6, pronto 1, rodar_testes 2, ver_arquivos 1, ver_mudancas 1.
- 2 (contador, Claude Code, opus-5-5): Bash 6, Edit 3, Grep 2, Read 1, Write 2, anotar 1, chamar_robo 1.
- 3 (historia, Claude Code, opus-5-5): Bash 3, Edit 7, Grep 1, Read 3, anotar 1.
- 4 (historia, nosso harness, opus-5-5): buscar 2, editar 10, ler 4, pronto 1, rodar_testes 2, ver_mudancas 1.
- 5 (aponta, nosso harness, opus-5-5): buscar 3, editar 7, escrever 7, ler 5, pronto 1, rodar_testes 1, ver_mudancas 1.
- 6 (aponta, Claude Code, opus-5-5): Bash 7, Edit 2, Read 1, Write 1, anotar 1.
- 7 (historia, Claude Code, fable-5-2): Bash 5.

<!-- /tabela -->

## O que se vê

- **As sete corridas entregaram,** com o CI de perto verde e o aceite escondido passando. Nenhum pedido separou as mãos pelo resultado: os três são pequenos e bem descritos, e os dois patches de cada pedido mexem nos mesmos arquivos (menos o rascunho da corrida 5), com tamanhos parecidos.
- **O Claude Code foi mais barato nos três pedidos:** US$ 0,18 contra 0,27, 0,23 contra 0,32 e 0,15 contra 0,39. Ele faz menos voltas (17, 16 e 13 contra 21, 21 e 35) porque junta trabalho:
  - um `Bash` lê três arquivos e roda os testes numa linha só;
  - vários `Edit` saem na mesma resposta.

  O nosso harness lê um arquivo por vez.
- **O custo do Claude Code veio todo da leitura do cache:** em todas as chamadas, até a primeira de cada sessão, a API relatou a entrada inteira como leitura de cache, sem escrita. A conta do próprio SDK (`total_cost_usd`) diz o mesmo que a porta das mãos, centavo por centavo. Vale conferir na Console se a cobrança bate.
- **O tempo de relógio foi parecido,** de 1 a 2,5 minutos por sessão. O Claude Code demorou mais no contador e na história; o nosso harness, no testador que aponta, com as 35 voltas.
- **O testador foi usado de jeitos diferentes:**
  - o nosso harness o chama para rodar o `ruff`, que ele não tem como rodar de outro jeito;
  - o Claude Code roda o `pytest` e o `ruff` direto no terminal, e chamou o robô só uma vez, no contador.

  No testador que aponta, o nosso harness chamou o robô 9 vezes: quatro delas sobre um arquivo de rascunho.
- **O rascunho entrou na entrega:** na corrida 5, o nosso harness escreveu `tmp_scratch_fmt.py` para ver como o `ruff` formatava um trecho e não tinha como apagá-lo. O arquivo foi no patch, e nem a revisão da oficina nem o CI de perto o pegaram. Num PR de verdade, você o devolveria. O próprio dev percebeu e anotou: "não crie arquivos de rascunho na oficina, porque não dá para apagá-los e eles entram no patch". É o "apagar na oficina" do `futuro.md`, agora com um custo medido.
- **As duas mãos aprenderam o mesmo sobre a oficina,** nas anotações da memória:
  - o `pyright` não roda lá dentro, por falta do node (o pacote do PyPI o baixa na primeira vez, e a oficina não tem rede);
  - o `ruff` tropeça no `.git` de fora do espaço, que o sandbox não deixa ler.

  O nosso harness anotou também a cópia do briefing no repositório de exemplo da fita.
- **O Fable 5.2 no Claude Code fez a história em 6 voltas e 5 passos, todos `Bash`:**
  - ele leu os dois arquivos de uma vez;
  - escreveu a seção nova e os testes com um script Python no terminal, sem o `Write` e o `Edit`;
  - mediu o teto de linhas, corrigiu e formatou.

  Saiu por US$ 0,24, pouco mais que o Opus no mesmo pedido (0,23), apesar do preço o dobro.

## O que difere além do harness

- **As ferramentas:** o Claude Code tem um terminal. Ele roda o `pytest`, o `ruff` e o `git` direto, junta comandos e escreve arquivos por script. O nosso harness tem as oito ferramentas e os robôs da bancada.
- **As instruções:** as do próprio Claude Code, mais o cartão, as notas e as instruções da sessão das mãos de fora (`sessao-maos.md`); no nosso harness, as instruções da sessão de sempre. O briefing e o pedido são os mesmos.
- **O cercado:** o `Bash` escreve por script, e o gancho só vê as ferramentas de arquivo. No Mac, o nosso `sandbox-exec` segura a escrita no espaço; no Linux, sem ele, só o gancho valeria, e ele não vê o que o terminal escreve (está no `futuro.md`).

## O que a comparação não diz

- **Os pedidos são pequenos.** Os três couberam em duas a três dezenas de voltas, e as duas mãos acertaram todos. Um pedido grande, ou mal descrito, pode separar as mãos, e o conector do Codex (a criação do marco) é o primeiro desse tamanho.
- **O aceite é o teste escondido, e não você.** A medida "rodadas até o seu aceite" (ADR-0077, decisão 13) fica para os PRs de verdade; aqui, o rascunho da corrida 5 seria a única devolução.
- **Uma corrida por mão e pedido.** A variação entre duas corridas iguais não foi medida.

## A decisão

A decisão 3 da ADR-0089 deixou o padrão do escritório vivo no nosso harness com o Sonnet 5.5 até este relatório. Pelo que ele mostra, o Claude Code fez o mesmo trabalho por menos, sem perder nada que a conferência meça. A minha recomendação:
- **o Claude Code com o Opus 5.5 vira o padrão** dos pedidos de código;
- **o nosso harness fica** como a reserva e para comparar.

A escolha é sua.

## Onde estão os dados

**Fora do git, em `data/maos/20261122/<corrida>/`:**
- os fatos (`fatos.jsonl`), de que a tabela sai;
- o resultado da conferência (`resultado.json`);
- o patch (`entrega.patch`);
- a fita das duas portas (`nosso.jsonl`, com os pedidos, e `claude-code.jsonl`, magra);
- a conversa inteira do Claude Code (`maos/pedido-001/sessao-*.jsonl`);
- o espaço do pedido, com o teste escondido.

`make maos-relatorio PASTA=data/maos/20261122` refaz a tabela sem a API, e o `--reconferir` do módulo refaz a conferência.
