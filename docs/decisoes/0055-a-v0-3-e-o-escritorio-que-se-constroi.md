# ADR-0055 — A v0.3 é o escritório que constrói a si mesmo

**Status:** aceita (a direção; as decisões de detalhe ficam para o plano macro da v0.3) · **Data:** 2026-10-17 · **Marco:** entre a v0.1 e a v0.2
**Complementa:** `docs/planos/ideia-escritorio-que-se-constroi.md`; `docs/planos/v0.2-macro.md`; escopo §2; `docs/design/README.md`; ADR-0025, ADR-0031, ADR-0052, ADR-0054

## Contexto

O escopo da v0.1 previa, depois da possessão por LLM (v0.2), o estúdio do podcast como segundo cartucho (v0.3, simulado) e a ligação dele ao pipeline real (v0.4). Em 14/out o usuário trouxe outra ideia: um escritório de programação cujos agentes trabalham para melhorar o próprio Campsverso, recebendo requisitos de nós como clientes, e publicando versões que o mundo passa a rodar. O aprofundamento está no documento da ideia, com o que existe por aí (Smallville e AI Town, ChatDev e MetaGPT, TheAgentCompany, Gas Town, Darwin Gödel Machine, Ouroboros, AgentFactory) e por que a combinação não existe: um mundo persistente, visível e habitável cujos moradores fazem software de verdade sobre o próprio mundo, com tudo registrado como eventos.

O que muda de verdade é uma coisa: na fazenda, uma ação só muda estado dentro do kernel; no escritório, o efeito vive fora (um repositório, um CI, um PR). O escritório é o mesmo tipo de coisa que o estúdio ligado ao pipeline real, só que o pipeline é software e o produto é a própria plataforma.

## Decisão

1. **A v0.3 é o escritório que constrói a si mesmo:** o gênero `office` e o cenário `office_campsverso`, o primeiro cartucho com efeitos externos. O estúdio do podcast passa para depois, sobre a porta de efeitos externos que o escritório constrói; o escritório pode construir o estúdio.
2. **A v0.2 continua como planejada e é pré-requisito:** a `ModelPort` com gravação e reprodução, a guarda de orçamento, o controlador LLM com cartão de identidade e tool use pelo catálogo, e a memória que sobrevive a um reinício. O M9 e o M10 são desenhados sabendo que uma ação longa pode ser delegada a uma porta externa, sem construir nada do escritório. O M12 (a arena) pode encolher para "script × um modelo, 30 dias, custo por dia".
3. **A arquitetura-guia é "a mente no mundo, as mãos na oficina":** o controlador LLM decide em tempo simulado, com chamadas baratas, e o kernel valida e publica os fatos; uma ação longa como `codificar` é executada por um adaptador atrás de uma porta (um agente de código numa worktree isolada), e o resultado volta como eventos. O kernel nunca roda git; o adaptador roda, e o kernel escreve o fato. A ação é `partial` (ADR-0052).
4. **O ciclo fecha por um portão humano:** PR mesclado pelo cliente, tag, e um supervisor fora do mundo que reinicia a pilha na versão nova, migrando o snapshot e preservando a memória. Agentes novos entram como dados (cartão, papel, catálogo, orçamento) propostos por PR; o mundo reinicia com mais um avatar.
5. **Governança desde o início:** CLAUDE.md, contratos, CI, orçamento e a própria governança são a constituição, que os agentes leem e propõem mudar, mas nunca aplicam; o CI é o juiz; o orçamento é por ticket e por dia; as mãos trabalham isoladas, sem segredos e sem tocar `data/archive/`. A autonomia cresce baixando o portão por caminho: documentação, testes, dados do cartucho, código.
6. **O primeiro agente é um dev generalista; o primeiro ajudante, o revisor.** A especialização é conquistada a partir de gargalos medidos.
7. **As referências visuais** em `docs/design/` (o par `escritorio-dia` e `escritorio-noite`) guiam a tela da v0.3, no mesmo renderer e com a mesma arte LPC.

Ficam para o plano macro da v0.3, com decisões numeradas: o tempo (ação que dura "até" o evento externo, com escala baixa, ou relógio ancorado); as mãos (o Claude Agent SDK em vez de um harness próprio); o repositório-alvo (o próprio Campsverso, com risco graduado por caminho); rótulos de eventos declarados pelo cartucho; o cliente por avatar ou por chat; as métricas da fábrica.

## Consequências

- O roteiro muda: v0.2 a possessão (inalterada), v0.3 o escritório, o estúdio depois. O README e o escopo §2 registram a revisão.
- O `futuro.md` ganha a porta de efeitos externos, os vários avatares fora do kernel, o supervisor de versões, a duração "até", os rótulos de eventos, o cliente por chat e o caderno do avatar.
- Nada muda no código agora. Os contratos novos (`office.*`, `ops.budget.*` já previsto no M9) nascem nos planos dos marcos.
- O risco conhecido: as mãos são não determinísticas e custam dólares. A resposta é a mesma do M9: gravar os resultados externos para reproduzir nos testes, e a guarda de orçamento antes de ligar qualquer coisa.
