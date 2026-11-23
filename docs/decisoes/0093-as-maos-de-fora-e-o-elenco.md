# ADR-0093 — As mãos de fora e o elenco: o Codex, o Antigravity, o Kenji e a Lívia (decisões do plano do M27)

**Status:** aceita · **Data:** 2026-11-22 · **Marco:** M27
**Complementa:** `docs/planos/m27-o-codex-e-o-antigravity.md`; ADR-0058 (a porta de modelo); ADR-0077 (o plano macro da v0.4, decisões 8 e 11); ADR-0089 (as mãos e a porta das mãos); ADR-0092 (o Camps e o Tiago)

## Contexto

O M27 é o terceiro degrau da escada de ferramentas do dev (ADR-0077): depois do nosso harness pela API (M24) e do Claude Code (M26), os harnesses da OpenAI e do Google, cada um com o modelo do próprio laboratório.

O levantamento de 22/nov mostrou como cada um roda sem interface:
- **o Codex:** `codex exec --json`, com um provedor próprio no `config.toml`;
- **o Antigravity CLI:** `agy -p … --output-format stream-json`, com o `GOOGLE_GEMINI_BASE_URL`.

Pelos dois caminhos, o modelo pode passar pela nossa porta. O conector do Codex já existe: foi a criação do M26 (PR #4), escrito contra um exemplo montado à mão.

Ao rever o plano, o usuário pediu três coisas:
- o Kenji e a Lívia entram já, um dev por laboratório;
- a conversa ganha ações: o Tiago topou jogar videogame e disse que ia para casa, e não fez nenhum dos dois;
- o tamanho do pedido sai da tela.

## Decisão

1. **Três devs, um por laboratório.** O dev é o modelo, e o harness é a ferramenta dele (ADR-0077, decisão 8):

   | Dev | A mente | As mãos |
   |---|---|---|
   | o Tiago | o Claude Opus 5.5 | o Claude Code |
   | o Kenji | o GPT-6.2 Astra | o Codex |
   | a Lívia | o Gemini 4 Neon | o Antigravity CLI |

   O marco vai em duas metades: as mãos primeiro, o elenco depois.
2. **As mãos falam com a API do próprio laboratório,** com chaves novas do usuário, cada uma com limite de gasto no painel. Elas não passam pela OpenRouter:
   - pelo cache: o Haiku pela OpenRouter custou o dobro;
   - porque o Antigravity só fala a língua do Gemini.
3. **As mentes do Kenji e da Lívia vão pela OpenRouter, como o revisor:** a porta de modelo já fala com ela, e o saldo de lá as cobre.
4. **A porta das mãos fala três línguas:**
   - a da Anthropic, como no M26;
   - a da OpenAI (Responses);
   - a do Gemini (`streamGenerateContent`).

   Para cada uma, ela troca a chave falsa pela de verdade, lê os tokens e publica o `llm.call.completed` com o `harness`. Ela também para no teto e grava as fitas. Ela é a borda do modelo quando quem chama é um harness de fora, como na ADR-0089.
5. **O nosso `sandbox-exec` é a cerca:**
   - o sandbox de cada harness fica desligado: o Codex com `-s danger-full-access -a never`, o `agy` sem `--sandbox` e com `--dangerously-skip-permissions`;
   - o `HOME` da sessão fica dentro do espaço, com a configuração do provedor apontada para a nossa porta;
   - não há gancho por ferramenta. Seguram o cercado e a revisão da entrega.
6. **A instalação de cada harness fica fixada no `Makefile`,** com a versão, como a do `nats-server`, e com o ok do usuário em cada download.
7. **As duas comparações:**
   - **em processo:** os três pedidos do M26 em quatro combinações (o Astra no Codex e no nosso harness, o Neon no Antigravity e no nosso harness), para separar o efeito do modelo e o do harness;
   - **ao vivo:** o "Para todos", que compara o resultado final dos três devs.
8. **O "Para quem" e o "Para todos":**
   - campos opcionais `assignee` e `group` no `office.ticket.created.v1`;
   - um dev só pega o que é dele ou o que é de quem estiver livre;
   - no "Para todos", o kernel cria uma ficha por dev, com o mesmo texto e o mesmo `group`.
9. **O escritório vivo vai para um mundo novo, o `office-campsverso-03`,** com os três devs. O elenco nasce com o mundo. O mundo 02 fica no arquivo, e o quadro recomeça no pedido 1, com um ramo por dev: `dev/<dev>/pedido-N`.
10. **A conversa tem ações:** uma ferramenta `agir`, com ir para casa quando convocado, uma pausa da rotina e a luz.
    - A dispensa pelo próprio dev usa o `office.staff.dismissed.v1` como está: o motivo `dispensado`, com o dev no `by`.
    - O cartão da conversa passa a dizer que o dev só promete o que vai fazer.
11. **O tamanho do pedido sai da tela.** A prancheta manda "M", e o contrato não muda. A faixa da ficha ganha a cor do dev, ou fica neutra para quem estiver livre.
12. **Os dois itens do `futuro.md` com destino no M27,** em campos opcionais:
    - a devolução que troca quem programa (`harness` e `model` no `office.ticket.returned.v2`);
    - o texto do modelo entre os passos (`note` no `workshop.step.v2`).
13. **A criação do M27 é a receita do computador do dev, com o robô que a confere,** feita num "Para todos". O gerente mescla a melhor das três entregas.
14. **O teto do M27 é US$ 60,** cada etapa paga com o ok do usuário, com o custo da anterior.

## Consequências

- **Nenhum tipo de evento novo:** só campos opcionais nos tipos de hoje. O kernel aprende o quadro com vários devs no cartucho do escritório, como o resto do mundo dele. As fazendas não mudam.
- **O escritório vivo troca de mundo de novo,** com o `estado.json` do supervisor guardado à parte, como na ADR-0092.
- **O usuário cria duas contas de API.** Sem as chaves, a primeira metade avança só até onde o transporte falso e as fitas vão.
- **Três devs custam mais.** Sem pedido no quadro, nenhuma mente é chamada; o teto por dia e por pedido vale para todos; o "Para todos" é escolhido, nunca automático.
