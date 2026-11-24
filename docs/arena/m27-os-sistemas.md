# A comparação entre sistemas (23/nov/2026)

**O que é:** a comparação do M27 (ADR-0093, decisão 17, a emenda de 23/nov). Os mesmos três pedidos de robô do M26, agora pelo sistema da OpenAI, o Codex com o GPT-6.2 Astra, ao lado do sistema da Anthropic, o Claude Code com o Opus 5.5, que o M26 já tinha medido. Cada sistema é o harness com o modelo do laboratório dele. O modelo sozinho, pela OpenRouter ou pela API, as arenas já mediram. Ferramenta: `make maos SO=8,9,10 PASTA=data/maos/20261122` (as corridas, pagas) e `make maos-relatorio PASTA=data/maos/20261122 DESTINO=docs/arena/m27-os-sistemas.md` (a tabela, lida dos fatos de cada corrida).

**As corridas são as do M26** (`m26-as-maos.md`), com três diferenças:
- **o sistema do pedido:** o Codex 0.171.0, do pacote fixado pelo `make tools-maos`, no nosso cercado. Ele roda pelo modo código e chama as ferramentas do mundo pelo `/mcp` da porta das mãos;
- **a mente do dev** continua no Opus 5.5, e só o pedido escolhe o Codex com o Astra (o dev e o sistema são independentes; decisão 18). O pedido vai para o Tiago, e o Kenji fica parado;
- **o espaço** é um clone deste repositório no commit `982f61d`, do M27. As do M26 foram no `d257b83`. Os pedidos e os testes de aceite são os mesmos, e mexem só na bancada (`tools/robos`), que pouco mudou entre os dois commits.

A memória começa limpa em cada corrida, e o teto é o mesmo, US$ 5 por corrida. A conferência é por fora, como no M26: o CI de perto e o teste de aceite escondido.

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
| 8 | contador | Codex | gpt-6.2-astra | sim | 20 | 22 | 0 | US$ 0,39 | 0,8 min | 5 arq., +75 -1 | sim | sim |
| 9 | historia | Codex | gpt-6.2-astra | sim | 20 | 19 | 0 | US$ 0,43 | 0,9 min | 2 arq., +76 -6 | sim | sim |
| 10 | aponta | Codex | gpt-6.2-astra | sim | 22 | 20 | 0 | US$ 0,45 | 1,1 min | 2 arq., +73 -1 | sim | sim |

**Total:** 10 corridas, US$ 3,06.

**As ferramentas de cada corrida**, pelos passos (`workshop.step.v2`):

- 1 (contador, nosso harness, opus-5-5): buscar 3, editar 3, escrever 2, ler 6, pronto 1, rodar_testes 2, ver_arquivos 1, ver_mudancas 1.
- 2 (contador, Claude Code, opus-5-5): Bash 6, Edit 3, Grep 2, Read 1, Write 2, anotar 1, chamar_robo 1.
- 3 (historia, Claude Code, opus-5-5): Bash 3, Edit 7, Grep 1, Read 3, anotar 1.
- 4 (historia, nosso harness, opus-5-5): buscar 2, editar 10, ler 4, pronto 1, rodar_testes 2, ver_mudancas 1.
- 5 (aponta, nosso harness, opus-5-5): buscar 3, editar 7, escrever 7, ler 5, pronto 1, rodar_testes 1, ver_mudancas 1.
- 6 (aponta, Claude Code, opus-5-5): Bash 7, Edit 2, Read 1, Write 1, anotar 1.
- 7 (historia, Claude Code, fable-5-2): Bash 5.
- 8 (contador, Codex, gpt-6.2-astra): command_execution 16, file_change 6.
- 9 (historia, Codex, gpt-6.2-astra): command_execution 15, file_change 4.
- 10 (aponta, Codex, gpt-6.2-astra): command_execution 15, file_change 5.

<!-- /tabela -->

## O que se vê

- **Os três sistemas entregaram os três pedidos,** com o CI de perto e o aceite escondido certos.
- **O Codex foi o mais rápido:** de 0,8 a 1,1 minuto por pedido, contra uns 2 minutos do Claude Code.
- **E fez as mudanças menores:** de 73 a 76 linhas novas, contra 99 a 120 dos outros dois, nos mesmos arquivos.
- **Ele trabalha pelo terminal.** No modo código, quase tudo é comando (`command_execution`), e os arquivos mudam por patch (`file_change`). Não chamou o testador nem anotou nada na memória; o Claude Code chamou o testador uma vez e anotou em cada pedido.
- **Custou o dobro do Claude Code,** de US$ 0,39 a 0,45 por pedido, contra 0,15 a 0,23. É o preço do Astra, o dobro do Opus por token. A maior parte vem da primeira chamada de cada sessão, que leva as instruções e as ferramentas do Codex antes de o cache valer (a prova de conformidade, `conformidade-2026-11-23-codex.md`).
- **Três pedidos são poucos para ordenar os sistemas.** A comparação ao vivo é o "Para todos" do escritório, com o Tiago e o Kenji no mesmo pedido.

## O que a comparação achou antes de dar certo

A primeira corrida do Codex acabou em 11 s, sem passo e sem dizer nada. Com o `PASTA=` relativo, o harness rodava com o diretório no espaço e não achava o perfil do cercado, e a casa dele ficava relativa ao espaço. O motor das mãos de fora e o Claude Code passaram a resolver os dois caminhos, e a saída de erro do harness ficou num `.stderr` ao lado da conversa. A corrida falha (US$ 0,01, só a mente) ficou em `data/maos/falhas/`.

## Onde estão os dados

- **Fora do git, em `data/maos/20261122/`:** as corridas 1 a 7 do M26 e as 8 a 10 do M27, cada uma com o resultado, os fatos, o patch, as fitas e a conversa inteira de cada sessão (`maos/pedido-001/codex-*.jsonl`).
- **O custo das corridas do Codex:** US$ 1,30, mais US$ 0,01 da corrida que falhou.
