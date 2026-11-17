# A prova de conformidade do escritório (16/nov/2026)

**O que é:** antes de um modelo trabalhar como o dev do escritório, ele faz dois pedidos curtos num repositório de exemplo, pelo mesmo caminho do escritório (ADR-0077, decisão 11; o plano do M24, §2.4; o adendo de 16/nov da ADR-0080). Ferramenta: `make conformidade` (`tests/support/src/campsverso_testkit/conformidade.py`).

**O caminho é o do escritório:**
- a sessão da oficina (`WorkSession`), com as instruções e o cartão do dev (`camps_escritorio`);
- as oito ferramentas da oficina e a de anotar;
- a memória vazia na abertura e o esforço `medium`.

**Os dois pedidos,** cada um num repositório de exemplo próprio, criado na hora:
- **Escrever:** criar `calc/saudacao.py` com `saudar(nome)` e o teste;
- **Consertar:** um teste falha por um defeito no código (a média dividia por um a mais); o conserto é no código, sem mudar o teste.

**A correção é por fora,** depois do `pronto`:
- os testes rodam de novo, sob o mesmo `sandbox-exec`;
- um teste escondido, que o modelo nunca viu, confere o resultado;
- a revisão da oficina olha o patch, e o arquivo do teste da média não pode mudar.

**Os limites:** nenhuma recusa, no máximo 5% de respostas sem ação e no máximo dois erros de formato (uma ferramenta que não existe, um argumento que falta ou de tipo errado, uma resposta cortada). Passa quem respeita os limites e faz os dois pedidos certos. O teto é de US$ 1,50 por modelo.

## O resultado

| Modelo | Passou | Respostas | Sem ação | Recusas | Formato | Escrever | Consertar | Custo | Tempo |
|---|---|---:|---:|---:|---:|---|---|---:|---:|
| Haiku 5.5 | sim | 18 | 0 | 0 | 0 | sim | sim | US$ 0,002 | 15 s |
| Sonnet 5.5 | sim | 14 | 0 | 0 | 0 | sim | sim | US$ 0,028 | 15 s |
| Opus 5.5 | sim | 17 | 0 | 0 | 0 | sim | sim | US$ 0,066 | 23 s |
| Fable 5.2 | sim | 18 | 0 | 0 | 0 | sim | sim | US$ 0,129 | 21 s |
| Astra (OpenRouter) | sim | 19 | 0 | 0 | 0 | sim | sim | US$ 0,133 | 49 s |

**Total:** 86 respostas e US$ 0,36. Nenhuma chamada à API falhou.

**O que se vê:**
- **Os cinco mudaram só os arquivos pedidos:** os dois do pedido de escrever e só `calc/media.py` no de consertar. Ninguém tocou no teste da média nem saiu do escopo.
- **O Opus e o Fable usaram `anotar`** uma vez cada, no pedido de escrever. Os outros não anotaram.
- **O Sonnet foi o mais enxuto:** 14 respostas, contra 17 a 19 dos outros. O Astra, pela OpenRouter, foi o mais lento.
- **O Fable é o 5.2,** o atual e mais barato que o 5.1 da arena do M21. O preço dele entrou na tabela (`config/env/local.yaml`).

## O que a prova não diz

A prova é de conformidade, e não de qualidade: os dois pedidos são pequenos de propósito, para ver se o caminho funciona com cada modelo (o harness pode enganar, como mostrou o Astra do M21). Passar nela não ordena os modelos. A decisão 14 da ADR-0080 dá a criação ao melhor da prova entre o Sonnet e o Opus: os dois acertaram tudo, e o Sonnet fez em menos passos, mais rápido e pela metade do custo.

## Onde estão os dados

- **Fora do git, em `data/conformidade/2026-11-16/`:** as fitas de cada modelo (`<modelo>.jsonl`, magras), o resultado por modelo e o `resultado.json` com os cinco.
- **O CI não chama a API:** os testes da prova (`tests/e2e/test_conformidade.py`) usam um modelo de mentira.
