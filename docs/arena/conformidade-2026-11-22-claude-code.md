# A prova de conformidade pelo Claude Code (22/nov/2026)

**O que é:** a mesma prova de 16/nov (`conformidade-2026-11-16.md`), os dois pedidos curtos num repositório de exemplo, agora feitos pelas mãos do Claude Code (ADR-0089; o plano do M26, §9, parte 2). Ferramenta: `make conformidade MAOS=claude_code`.

**O caminho é o das mãos de fora:**
- o Claude Code que vem no SDK (`claude-agent-sdk` 0.2.187), sob o nosso `sandbox-exec`, com o ambiente limpo e o gancho de cada ferramenta;
- as ferramentas dele (`Read`, `Write`, `Edit`, `Glob`, `Grep`, `TodoWrite` e `Bash`) e as duas do mundo (`chamar_robo`, com a bancada vazia, e `anotar`);
- as instruções do Claude Code, mais o cartão do dev, as notas do escritório e as instruções da sessão das mãos de fora (`sessao-maos.md`);
- cada chamada ao modelo pela porta das mãos, que põe a chave, mede e grava a fita;
- a memória vazia na abertura, o Opus 5.5 e o esforço `medium`.

**A contagem muda pouco:**
- a resposta final do Claude Code é o `pronto` dele, e não conta como resposta sem ação;
- o formato é conferido contra as ferramentas que o próprio Claude Code ofereceu em cada chamada;
- as chamadas sem ferramentas (as auxiliares do harness) contam só no custo. Não houve nenhuma: o tráfego que não é essencial vai desligado.

A correção por fora, os limites e o teto de US$ 1,50 são os mesmos.

## O resultado

| Mãos | Modelo | Passou | Respostas | Sem ação | Recusas | Formato | Escrever | Consertar | Custo | Tempo |
|---|---|---|---:|---:|---:|---:|---|---|---:|---:|
| Claude Code | Opus 5.5 | sim | 6 | 0 | 0 | 0 | sim | sim | US$ 0,038 | 15 s |
| o nosso harness (16/nov) | Opus 5.5 | sim | 17 | 0 | 0 | 0 | sim | sim | US$ 0,066 | 23 s |

**O que se vê:**
- **Três respostas por pedido.** O Claude Code junta trabalho em cada resposta:
  - no pedido de escrever, os dois `Write` e o `Bash` dos testes saíram na mesma resposta;
  - o `Bash` junta comandos: listar, ler e rodar os testes numa linha só.

  O nosso harness fez uma ferramenta por resposta.
- **Ele leu antes de mudar e conferiu depois:**
  - leu o código e os testes, mudou só os arquivos pedidos e rodou o `pytest` do espaço;
  - olhou o `git status`, e no conserto também o `git diff`;
  - não tocou no teste da média nem anotou nada.
- **O resumo é o de um dev para o gerente:** o que mudou, como conferiu e que a mudança é só aquela.
- **O custo veio quase todo do cache:** em todas as chamadas, uns 11 mil tokens de entrada vieram como leitura do cache, e a entrada nova foi de 2 tokens. A prova é pequena demais para dizer quanto as mãos custam num pedido de verdade; isso é a comparação da parte 4.

## O que a prova achou antes de rodar

- **O here-doc do terminal:** o zsh grava o here-doc em `/tmp`, que o nosso sandbox fecha, e o `cat > arquivo <<'FIM'` falhava. O teste com o modelo falso achou o defeito antes da sessão paga. Agora o temporário do zsh (`TMPPREFIX`) fica no espaço.
- **A fita entre sessões:** cada sessão abria a fita do começo, e o segundo pedido tocaria as respostas do primeiro. Agora as mãos guardam uma fita só, e cada sessão continua de onde a anterior parou.

## Onde estão os dados

- **Fora do git, em `data/conformidade/20261122-120322/`:**
  - o resultado;
  - a fita;
  - a conversa inteira de cada sessão (`maos/<pedido>/sessao-*.jsonl`).
- **A fita no repositório:** em `tests/fixtures/llm/conformidade-claude-code.jsonl`, magra, com o caminho do espaço trocado por `{espaco}`.
- **O CI não chama a API:** `tests/e2e/test_conformidade.py` toca essa fita pelo Claude Code de verdade, com o gancho e a conferência por fora, num espaço novo. Testa também um roteiro do modelo falso.
