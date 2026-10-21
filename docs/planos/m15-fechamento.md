# Plano do M15 — o fechamento da v0.2

*Proposto em 21/out/2026, depois do M14 e da decisão da v0.3 (ADR-0064). Aprovado em: (pendente). Como no M7, o fechamento da v0.1, este marco não constrói nada novo: confere, documenta e publica.*

## O que a v0.2 prometeu

A pergunta do plano macro: **"Um LLM consegue viver na Fazenda do Camps, sobreviver, prosperar e descobrir sozinho a regra oculta do rio?"**, e como ele se compara ao script, a um humano e a outros modelos. Cada marco tinha um "pronto quando"; o M15 os confere um a um, com a evidência, e responde à pergunta com os números.

## 1. Critérios de aceite

`docs/aceite-v0.2.md`, no formato do `aceite-v0.1.md`: um critério por linha, com a evidência e o resultado.

| # | Critério (o "pronto quando" do plano macro) | Evidência |
|---|---|---|
| B1 | **M8:** um script sobrevive 30 dias com as regras novas; a foto e o delta cabem num orçamento de tokens medido | soak de 30 dias da fazenda 1 no código final; `make percepcao` sobre o arquivo dele |
| B2 | **M9:** uma chamada real e uma gravada passam pelo mesmo contrato; estourar o teto pausa o mundo | `make llm-smoke` (uma chamada, centavos); os testes da fita e da guarda; o teste do M14 que para a corrida no teto |
| B3 | **M10:** o LLM vive 7 dias simulados sem intervenção, dentro do orçamento | a corrida de 7 dias do M10 e as corridas de 30 dias das duas arenas (nenhuma desistiu nem bateu no teto) |
| B4 | **M11:** a memória sobrevive a um reinício; uma reflexão cita fatos do arquivo de eventos | os testes da memória com reinício; as crenças citadas nos relatórios das arenas |
| B5 | **M12:** o relatório compara script, Haiku com e sem memória e o controle em 30 dias, com quem descobriu o leste | `docs/arena/2026-10-19.md` |
| B6 | **M13:** o script 2 vive 30 dias na Boa Vista; a mente joga nela com o manual novo; a fazenda 1 intacta | soak de 30 dias da Boa Vista no código final; a fita da Boa Vista no `make check`; os testes da fazenda 1 |
| B7 | **M14:** o relatório compara os modelos onde as decisões custam | `docs/arena/2026-10-20.md` |
| B8 | **Os princípios continuam valendo:** arquitetura, contratos, determinismo e replay nos dois mundos, regra oculta fora do manual e do catálogo | `make check` verde (local e CI), com o teste de palavras proibidas lendo notas e catálogo; `make ui-e2e` nos dois mundos |

**A resposta à pergunta**, no fim do `aceite-v0.2.md`: o LLM vive e prospera (o Haiku com memória empatou ou passou o script na fazenda 1; o Opus fez cinco vezes as moedas do script 2 na Boa Vista), mas **nenhum controlador descobriu a regra do rio**: na fazenda 1 a crença apareceu e se diluiu; na Boa Vista ninguém explorou. O humano ficou como referência qualitativa. É a pergunta que a v0.3 herda.

## 2. As conferências finais

- **Dois soaks de 30 dias** no código final, um por mundo (minutos, sem custo), com `make metrics`.
- **`make check` com `TZ=UTC`**, o CI verde no último push, e `make ui-e2e` nos dois mundos (`MUNDO=farm-boavista-01`).
- **Uma chamada real** pelo `make llm-smoke`, para provar que o caminho da API continua de pé no fechamento (a chave vence em 31/12, no `futuro.md`).

## 3. A revisão do `futuro.md`

O backlog cresceu a v0.2 inteira. A revisão tira o que foi feito (enxergar o mapa, Playwright, andar gasta energia, o caderno do avatar, a reserva da corrida, conferir o `make sessoes` do M2 e do M3, Sonnet e Opus numa fazenda mais rica) e põe em cada item que fica o destino do plano macro da v0.3: um marco da v0.3, a fazenda 4, a v0.4 ou depois.

## 4. Documentação

- **README:** o estado da v0.2 concluída; como rodar a mente (`make sandbox MENTE=camps`), a corrida, a arena e a Boa Vista; o diagrama de arquitetura com a mente, a guarda de orçamento e a porta de modelo; o caminho para a v0.3.
- **`docs/diario/README.md`:** "a v0.2 em números", como a v0.1 teve: tempo e tokens do Claude Code por marco (`make sessoes`), custo de API por marco, testes, commits e arquivos, e as frases para o LinkedIn de cada marco.
- **`contracts/CHANGELOG.md`:** as seções "Não publicado" do M8 ao M13 viram uma seção `v0.2.0`.
- **`CLAUDE.md`:** a v0.2.0 publicada; a v0.3 como a versão em construção.

## 5. A versão

- **As notas** em `docs/versoes/v0.2.0.md`: o que tem, como experimentar, os critérios, os resultados das duas arenas, os custos, o que ficou conhecido e para depois, as licenças.
- **A tag `v0.2.0`** no commit final, com o CI verde. O push da tag e a Release no GitHub esperam o ok do usuário, como na v0.1.

## 6. Ordem do trabalho

1. Os soaks, as conferências e a chamada real.
2. `docs/aceite-v0.2.md` com as evidências e a resposta.
3. A revisão do `futuro.md`.
4. README, diário consolidado com "a v0.2 em números", CHANGELOG dos contratos, CLAUDE.md, notas da versão.
5. `make sessoes MARCO=M15`, custos, commit, e a tag com o ok do usuário.

Estimativa: uma sessão. Custo de API: uns centavos (a chamada real).

## 7. Decisões

1. **Os critérios B1 a B8** como o aceite da v0.2, com a resposta à pergunta no fim. *Recomendação: sim; são os "pronto quando" que o plano macro já tinha, mais os princípios.*
2. **Os dois soaks finais e a chamada real** como evidência no código que vai virar `v0.2.0`. *Recomendação: sim; custam minutos e centavos e evitam citar números de um código que mudou depois.*
3. **A revisão do `futuro.md`** com o destino de cada item. *Recomendação: sim; a v0.3 começa por ele.*
4. **"A v0.2 em números"** no diário, incluindo o custo de API por marco. *Recomendação: sim; o projeto é público e o custo é parte da história.*
5. **A tag `v0.2.0` e a Release** no GitHub, depois do seu ok. *Recomendação: sim, como na v0.1.*
6. **As vinte decisões do plano macro da v0.3:** a sua resposta "vamos nesta linha" vale como aprovação de todas como recomendado (a ADR-0065 no começo da v0.3), ou prefere passar por elas uma a uma antes? *Recomendação: aprovar a linha agora e confirmar as decisões de cada marco no plano dele, como na v0.2; a ADR-0065 registra a lista no começo do M16.*

## 8. Como ficou

*(a preencher no fechamento)*
