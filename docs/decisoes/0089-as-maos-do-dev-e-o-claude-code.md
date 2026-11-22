# ADR-0089 — As mãos do dev e o Claude Code (decisões do plano do M26)

**Status:** aceita · **Data:** 2026-11-22 · **Marco:** M26
**Complementa:** `docs/planos/m26-o-claude-code.md`; ADR-0058 (a porta de modelo); ADR-0077 (o plano macro da v0.4); ADR-0080 (a oficina); ADR-0083 (o ciclo fecha)

## Contexto

Até o M25, o dev programa pelo nosso harness: uma conversa com o modelo pela porta de modelo e oito ferramentas pequenas na oficina. O M26 traz a segunda ferramenta da escada da v0.4: o Claude Code, pelo Claude Agent SDK.

O levantamento achou:
- a entrega não depende de quem programou: o patch do espaço, a revisão, o PR e o revisor seguem iguais;
- o briefing (a criação do M25) existe, mas a sessão ainda abre com o pedido cru;
- o modelo por pedido (ADR-0083, decisão 14) não foi construído;
- o SDK abre o próprio Claude Code em modo sem interface (`-p`, em JSON) e dá em Python os ganchos por ferramenta, as ferramentas no mesmo processo, os tetos de voltas e de custo e o endereço do modelo (`ANTHROPIC_BASE_URL`);
- o sandbox do Claude Code cobre só o `Bash`. As ferramentas de arquivo dele leem qualquer lugar da máquina se nada as parar.

O usuário aprovou as 12 decisões em 22/nov, como recomendado.

## Decisão

1. **As mãos são uma porta (`HandsPort`),** com dois adaptadores: o nosso harness (a `WorkSession`) e o Claude Code. O M27 pluga o Codex e o Antigravity nela. Do patch em diante, nada muda.
2. **O pacote `claude-agent-sdk`,** preso numa versão, só em `libs/adapters` (princípio 3), com o Claude Code que vem dentro dele. A troca de versão passa pela prova de conformidade.
3. **O pedido escolhe as mãos e o modelo,** na prancheta, com o padrão do mundo (`minds.camps.hands` e `model`). Entra assim o modelo por pedido da ADR-0083. O escritório vivo segue no nosso harness com o Sonnet 5.5 até o relatório da comparação.
4. **O briefing abre toda sessão,** nas duas mãos, rodado pela bancada. Se ele falhar, a sessão abre com o pedido, como antes.
5. **As ferramentas do Claude Code na oficina:**
   - `Read`, `Write`, `Edit`, `Glob`, `Grep`, `TodoWrite` e `Bash`;
   - as nossas `chamar_robo` e `anotar`, no mesmo processo;
   - sem a web, os MCPs de fora, os subagentes e as configurações do usuário (`setting_sources` só no projeto, e o `HOME` dentro do espaço).
6. **O isolamento tem três camadas:**
   - o nosso `sandbox-exec` em volta do Claude Code inteiro, com a escrita só no espaço, a leitura negada nos lugares com segredo e a rede só para a nossa porta;
   - a chave fora do processo do dev;
   - um gancho antes de cada ferramenta, que recusa caminhos fora do espaço e comandos que não cabem na oficina.

   A revisão da entrega procura também formatos de chave no patch.
7. **A porta das mãos.** Quando quem chama o modelo é um harness de fora, a borda da ADR-0058 passa a ser uma porta local nossa, em `libs/adapters`, por onde o harness chama o modelo:
   - ela põe a chave e repassa a chamada;
   - mede cada resposta e publica o `llm.call.completed`, com o campo novo `harness`, e a guarda soma como sempre;
   - recusa a chamada acima do teto do pedido ou do dia;
   - grava a fita, de que os testes respondem sem a API.
8. **Os tetos:**
   - por sessão: 80 voltas, US$ 4 (a estimativa do SDK) e 45 minutos de relógio;
   - no escritório: US$ 5 por pedido e US$ 10 por dia.
9. **A gravação:**
   - o `workshop.step.v2`, com o nome da ferramenta de cada harness e o campo `harness` (a v1 fica para os dias antigos);
   - o fato `workshop.session_finished.v1`, das duas mãos: o pedido, as mãos, o modelo, as voltas, os passos, o motivo, o custo e o tempo;
   - o chip com as mãos e o modelo;
   - a conversa da sessão guardada fora do git.
10. **A comparação:**
    - três pedidos de robô, cada um nas duas mãos, com o Opus 5.5, do mesmo commit e com os mesmos tetos;
    - o Fable 5.2 no Claude Code num deles;
    - o relatório em `docs/arena/`.
11. **A criação é o conector do Codex,** feito pelo dev com o Claude Code e o Opus 5.5, contra um exemplo do formato do `codex exec --json` que nós pomos antes. O M27 o liga ao Codex de verdade.
12. **O orçamento de API do M26 é de US$ 30,** cada passo pago com o ok do usuário.

## Consequências

- **A ADR-0058 ganha uma segunda borda.** A porta de modelo continua sendo a única para quem chama o modelo dentro do nosso código. A porta das mãos é a borda quando quem chama é um harness de fora, com a mesma medida e a mesma guarda.
- **A chave da API nunca entra num processo que o modelo controla,** nem no nosso harness nem no Claude Code.
- **O CI roda uma sessão do Claude Code sem a API,** com o modelo falso roteirizado. No Linux do CI não há `sandbox-exec`: lá valem o gancho e a rede só pela porta.
- **Quatro contratos mudam ou nascem:** o pedido com as mãos e o modelo, o `workshop.step.v2`, o `workshop.session_finished.v1` e o campo `harness` no `llm.call.completed.v1`.
- **Os tetos do escritório sobem** (de US$ 1 para 5 por pedido, e de 3 para 10 por dia), porque o Opus no Claude Code custa mais por pedido que o Sonnet no nosso harness.
