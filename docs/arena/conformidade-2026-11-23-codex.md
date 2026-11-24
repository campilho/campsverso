# A prova de conformidade pelo Codex (23/nov/2026)

**O que é:** a mesma prova de 16/nov (`conformidade-2026-11-16.md`), os dois pedidos curtos num repositório de exemplo, agora feitos pelo Codex com o GPT-6.2 Astra (ADR-0093; o plano do M27). É a primeira prova de um sistema de fora da Anthropic: o harness da OpenAI com o modelo dela. Ferramenta: `make conformidade MAOS=codex`.

**O caminho é o das mãos de fora:**
- o Codex 0.171.0, do pacote completo do release (`make tools-maos`), sob o nosso `sandbox-exec`, com o sandbox e as aprovações dele desligados;
- o modo código do Codex: o modelo escreve um JavaScript que chama `tools.exec_command` e `tools.apply_patch`;
- as duas ferramentas do mundo (`chamar_robo`, com a bancada vazia, e `anotar`), no `/mcp` da porta das mãos;
- as instruções do Codex, mais o cartão do dev, as notas do escritório e as instruções da sessão das mãos de fora (`sessao-maos.md`);
- cada chamada ao modelo pela porta das mãos, na língua da Responses API, que põe a chave da OpenAI, mede e grava a fita;
- a memória vazia na abertura, o Astra e o esforço `medium`.

**A contagem é a do Claude Code:**
- a resposta final é o `pronto` do harness;
- o formato é conferido contra as ferramentas que o próprio Codex ofereceu em cada chamada;
- a chamada livre (o `exec`, cuja entrada é código e não JSON) conta como ferramenta usada.

A correção por fora, os limites e o teto de US$ 1,50 são os mesmos.

## O resultado

| Mãos | Modelo | Passou | Respostas | Sem ação | Recusas | Formato | Escrever | Consertar | Custo | Tempo |
|---|---|---|---:|---:|---:|---:|---|---|---:|---:|
| Codex | GPT-6.2 Astra | sim | 12 | 0 | 0 | 0 | sim | sim | US$ 0,340 | 42 s |
| Claude Code (22/nov) | Opus 5.5 | sim | 6 | 0 | 0 | 0 | sim | sim | US$ 0,038 | 15 s |
| o nosso harness (16/nov) | Opus 5.5 | sim | 17 | 0 | 0 | 0 | sim | sim | US$ 0,066 | 23 s |

As 12 respostas e o formato foram contados de novo pela reprodução da fita, sem a API. Na corrida paga, a porta ainda não lia as ferramentas do Codex (a seção abaixo) e contou 0. O custo e o tempo são os da corrida paga.

**O que se vê:**
- **Ele começa pelas convenções do repositório.** Leu o `CLAUDE.md` do exemplo, olhou o `git status` e listou os arquivos com o `rg` antes de abrir o código.
- **Ele confere mais e por mais caminhos:**
  - rodou o `pytest` de `tests/`;
  - tentou o `pyright` de três jeitos;
  - viu o diff de cada arquivo novo.

  Foram 27 passos nos dois pedidos, contra 9 do Claude Code.
- **Ele diz o que não conseguiu conferir.** O repositório de exemplo não traz o `pyright` no ambiente. Os dois resumos dizem isso ao gerente ("a verificação de tipos ficou pendente porque o `pyright` está indisponível na oficina"), em vez de dar a conferência por feita.
- **O custo veio da primeira chamada de cada sessão.** Nas 12 chamadas entraram 172 mil tokens:
  - 141 mil vieram do cache;
  - 31 mil foram entrada nova, a maior parte nas primeiras chamadas, que levam as instruções e as ferramentas do Codex antes de o cache valer;
  - saíram só 933 tokens.

  Por token, o Astra custa o dobro do Opus. A prova é pequena demais para dizer quanto um sistema custa num pedido de verdade; isso é a comparação em processo.

## O que a prova achou

- **As ferramentas do Codex não vêm no campo `tools`.** O Codex 0.171 as manda num item `additional_tools` da entrada, com espaços de nomes. A porta via toda chamada como auxiliar, e a contagem saiu zerada; o custo, não, porque a porta o mede de qualquer jeito. Agora o dialeto da OpenAI lê os dois lugares, e a chamada livre do `exec` vai num objeto.
- **A fita tinha 1,3 MB, quase tudo eco.** A OpenAI repete a lista inteira das ferramentas em três eventos de cada resposta, e o Codex não a lê. A porta grava a fita sem esse eco, e a desta prova passou pela mesma limpeza: ficou com 333 KB.

O ensaio sem custo do mesmo dia, com o Codex de verdade diante de uma OpenAI falsa, já tinha achado o resto: o modo código precisa do `codex-code-mode-host` (o pacote completo), os comandos rodam num terminal novo, e as ferramentas do mundo chegam pelo `/mcp` da porta (`tests/fixtures/codex/README.md`).

## Onde estão os dados

- **Fora do git, em `data/conformidade/20261124-005659/`:**
  - o resultado;
  - a fita como veio;
  - a conversa inteira de cada sessão (`maos/<pedido>/codex-*.jsonl`).
- **A fita no repositório:** em `tests/fixtures/llm/conformidade-codex.jsonl`, sem o eco das ferramentas, com o caminho do espaço trocado por `{espaco}`.
- **A reprodução:** `tests/e2e/test_conformidade.py` toca essa fita pelo Codex de verdade, com o cercado e a conferência por fora, num espaço novo. O CI não tem o Codex (ele fica fora do `make setup`), e lá o teste é pulado; no Mac, o `make check` o roda.
