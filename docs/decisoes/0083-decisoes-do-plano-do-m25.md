# ADR-0083 — Decisões do plano do M25 (o ciclo fecha)

**Status:** aceita · **Data:** 2026-11-20 · **Marco:** M25
**Complementa:** `docs/planos/m25-o-ciclo-fecha.md`; ADR-0077 (o plano macro da v0.4); ADR-0080 (a oficina, a entrega e a bancada); ADR-0070 (o juiz fora da mente); ADR-0058 (a porta de modelo)
**Revê:** ADR-0077, nos modelos dos marcos M26 e M27

## Contexto

No M24, a entrega do dev terminava num patch que o humano aplicava à mão. O M25 fecha o ciclo: a entrega vira um PR no GitHub, o humano mescla, e o escritório vivo troca sozinho para a versão nova, sem perder o mundo nem a memória do dev.

O levantamento achou:
- nenhum serviço fala com o GitHub, e a oficina não tem rede;
- o kernel já troca de versão com segurança: a parada elegante grava um snapshot, e a versão nova retoma dele;
- a memória do dev fica fora do snapshot e sobrevive a um reinício;
- o escritório vivo roda da pasta em que nós trabalhamos.

O usuário aprovou as 16 decisões do plano em 20/nov, com notas. Ele trouxe também o índice de agentes de código da Artificial Analysis daquela semana, com o Antigravity e o Gemini 4 Neon em primeiro (59), o Claude Code com o Fable 5.2 e com o Opus 5.5 logo atrás (58), e o Codex com o GPT-6.2 Astra em 53.

## Decisão

1. **A identidade do dev no GitHub é um GitHub App** só deste repositório (`campsverso-dev`): conteúdo e pull requests, sem workflows nem administração. O usuário o cria, e a chave fica em `privado/`.
2. **O `main` tem um ruleset:** só o dono o atualiza, e o App só escreve em ramos `dev/*`.
3. **Quem abre o PR é o publicador,** um script nosso, depois da revisão da entrega. O modelo nunca vê o GitHub nem a chave: ele entende o projeto pelo clone inteiro da oficina. O publicador aparece na bancada, mas não é uma ferramenta do dev.
4. **O aceite é mesclar.** Devolver segue no quadro, e o dev refaz no mesmo ramo. Fechar o PR sem mesclar devolve o pedido a "a fazer".
5. **Os fatos do GitHub entram no mundo como comandos.** O vigia do GitHub manda ao kernel cada mudança de um PR (`cmd.office.pull_request.report.v1`); o kernel confere e publica `office.ticket.pr_*`. O comando fica no diário, e o replay o refaz sem perguntar ao GitHub.
6. **O primeiro PR de verdade é do dev-script,** sem API, e é fechado sem mesclar: o primeiro PR de todos. O primeiro mesclado é a criação do marco.
7. **O revisor de outra família fica fora do mundo,** como o juiz da arena (ADR-0070): comenta no PR, aconselha o humano e não dá ordens ao dev. Depois ele vira um personagem.
8. **O revisor é o Gemini 4 Neon,** calibrado antes contra o GPT-6.2 Astra em três diffs com defeitos plantados. O GPT-6.2 Astra é a reserva. A API direta do Google ou da OpenAI e o Bedrock são adaptadores da porta de modelo, para quando forem precisos.
9. **O CI confere a constituição** no diff de cada PR de um ramo `dev/*`: a segunda conferência, depois da revisão da oficina.
10. **O escritório vivo roda de uma worktree própria,** presa na versão publicada, sob o supervisor (`make escritorio`).
11. **A troca de versão, o auto-update:** a versão candidata é preparada ao lado e passa por uma fumaça numa cópia dos dados (uma hora simulada). O supervisor espera o dev sair de uma sessão, por até 30 minutos, copia os dados, para com elegância, troca e confere a saúde. Se falhar, volta sozinho para a versão e os dados de antes. Ficam as três últimas cópias, e cada passo vai para o diário da troca.
12. **A versão fica à vista:** uma placa na parede e no HUD (o campo opcional `build` na sessão da tela), o fato do kernel `world.version.changed.v1` e um episódio na memória do dev. A arte vai num pedido ao Claude Design.
13. **A criação é o briefing:** um robô que monta o que uma sessão do Claude Code vai ler, usado no M26. A bancada fica com o testador, o briefing e o publicador.
14. **O dev segue com o Sonnet 5.5;** o Opus 5.5 entra quando o pedido mexe na arquitetura do mundo, escolhido no quadro.
15. **O médio prazo** (revê a ADR-0077):
    - o Gemini 4 Neon passa pela prova de conformidade do nosso harness já no M25;
    - o M26 traz o Claude Code com o Opus 5.5 e o Fable 5.2;
    - o M27 traz o Antigravity com o Gemini 4 Neon e o Codex com o GPT-6.2 Astra, conferindo o índice da hora;
    - o plano do M27 desenha o painel do elenco: que modelo é cada personagem, e quem está ligado numa rodada.
16. **O orçamento de API do M25 é de US$ 20,** cada passo pago com o ok do usuário.

## Consequências

- **O escritório passa a ter efeitos fora do mundo,** no GitHub. O mundo segue reproduzível, porque o que vem de fora entra como comando no diário.
- **Uma credencial nova existe:** a chave do App, fora do git e fora do espaço do dev, com o mínimo de permissões.
- **O escritório vivo deixa a nossa pasta,** e a versão que ele roda passa a ser só a publicada.
- **Os contratos ganham** os fatos do PR, o comando do vigia, a troca de versão e o campo da placa.
- **O CI ganha um passo** que só olha os ramos do dev.
- **A troca de versão pode derrubar o mundo.** A fumaça numa cópia e a volta automática são a resposta.
