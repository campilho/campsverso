# ADR-0093 — As mãos de fora e o elenco: o Codex, o Antigravity, o Kenji e a Lívia (decisões do plano do M27)

**Status:** aceita, com a emenda de 23/nov · **Data:** 2026-11-22 · **Marco:** M27
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

## Emenda de 23/nov: o Kenji só, os sistemas trocáveis e a Lívia no M28

**O contexto.** O `make tools-maos` rodou, e um ensaio sem custo pôs o Codex e o `agy` de verdade no cercado, diante de modelos falsos locais. Ele mostrou duas coisas:
- **O Codex 0.171 cabe no cercado.** Ele roda comandos pelo modo código, que precisa do `codex-code-mode-host`: o binário avulso do release não o traz, e o pacote completo (`codex-package`) traz.
- **O `agy` não cabe.** Ele roda um servidor de linguagem numa porta local que ele mesmo sorteia. O `sandbox-exec` não aceita uma faixa de portas, nem um cercado dentro de outro. Liberar todas as portas locais deixaria os comandos do modelo alcançarem o que roda no Mac: o editor Antigravity do usuário, o app do Claude, e o NATS e o gateway do escritório vivo.

Ao ver o resultado, o usuário pediu três coisas:
- a Lívia entra no M28, com o Antigravity dentro do computador dela;
- a comparação é entre sistemas (o harness com o modelo dele), não entre modelos. O modelo sozinho, pela OpenRouter ou pela API, as arenas já mediram;
- qualquer dev pode usar qualquer sistema: o Tiago com o Codex, a Lívia com o Claude Code, o Kenji com o Antigravity.

**A decisão:**

15. **O M27 tem dois devs: o Tiago e o Kenji.** A Lívia entra no M28, com o Antigravity dentro do computador dela (o plano macro, §5), onde o localhost é só dela. O conector do Antigravity, a porta na língua do Gemini e os testes ficam prontos para ela. A chave do Google sai do M27. Muda as decisões 1, 3 e 5.
16. **O Codex vem do pacote completo do release,** fixado no `Makefile` (decisão 6). As mãos chamam cada programa fixado pelo endereço real, onde ele acha o que veio ao lado dele.
17. **A comparação é entre sistemas.**
    - **Em processo:** os três pedidos de robô do M26 pelo Codex com o Astra, ao lado do Claude Code com o Opus que o M26 já mediu (`docs/arena/m26-as-maos.md`), na mesma base. O nosso harness sai dessa comparação.
    - **Ao vivo:** o "Para todos" com o Tiago e o Kenji.

    Muda a decisão 7.
18. **O dev e o sistema são independentes.** O dev é a identidade: o cartão, a memória e a mente, que é o modelo da conversa e do plano. O sistema é quem programa: o harness, com o modelo e o esforço dele.
    - **O catálogo dos sistemas** fica no gênero do escritório (`office.yaml`). Cada harness lista os modelos da língua dele:
      - o Claude Code, os da Anthropic;
      - o Codex, os da OpenAI;
      - o Antigravity, os do Google, a partir do M28;
      - o nosso harness, os da porta de modelo.
    - **Cada dev tem, no mundo, a mente e o sistema padrão em campos separados.** Hoje um campo só (`model`) serve à conversa e à sessão das mãos.
    - **A prancheta escolhe o sistema do pedido entre todos,** com os modelos do harness escolhido. O kernel confere o par harness–modelo, nunca o par dev–harness.
    - **A entrega registra o sistema** (o `harness` e o `model` no `office.ticket.returned.v2`, decisão 12).
    - **Um teste roda cada dev com cada sistema,** com os harnesses e os provedores falsos, e prova a troca.

    Trocar o sistema de um dev é mudar o padrão dele no mundo ou escolher na prancheta, sem código. Um harness com o modelo de outro laboratório, como o Codex com o Claude, pediria traduzir uma língua na outra dentro da porta, e fica fora.

    Muda a decisão 1: a tabela passa a ser o padrão de cada dev. O dev continua sendo o modelo da mente (ADR-0077, decisão 8), e o sistema é a ferramenta dele.
19. **O mundo 03 nasce com o Tiago e o Kenji.** No M28, a Lívia e os computadores vêm com um mundo novo, como em cada troca de elenco. Muda a decisão 9.
20. **A criação do M27 é a receita do computador, num "Para todos" com dois devs.** A receita já diz o que o `agy` pede: portas locais só dele. Muda a decisão 13.

