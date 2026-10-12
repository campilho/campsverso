# ADR-0045 — NATS local: versão, usuários, permissões e senhas

**Status:** aceita · **Data:** 2026-10-11 · **Marco:** M2
**Complementa:** ADR-0024; plano do M2 §3 (decisões 2 e 6)

## Decisão

1. **nats-server 2.14.8**, a versão mais nova da linha 2.14 aprovada no plano.
   - A 2.15 saiu em setembro e fica para uma revisão futura.
   - Os sha256 do macOS arm64 e do Linux amd64 ficam fixados no Makefile, copiados do `SHA256SUMS` da release. `make tools` recusa um arquivo que não confira.
   - `make setup` chama `make tools`, então o CI também baixa o binário e roda os testes que dependem do NATS. No CI, faltar o binário é erro; na máquina local, os testes são pulados.
2. **Um usuário por processo** em `config/nats/nats.conf`: `kernel`, `archiver`, `perception`, `controller`, `gateway` e `operator`.
   - O controlador só publica `cmd.action.propose.v1` e só assina `agent.>`. `internal`, `world` e `cmd` são negados (A8).
   - Ninguém além do operador apaga ou esvazia streams.
   - Percepção e gateway têm permissões provisórias, revistas nos marcos deles (M3, M4).
   - Cada usuário tem a sua caixa de respostas (`_INBOX_<usuário>.>`), para não ler as respostas dos outros.
3. **Senhas fora do git** (decisão 2): `make secrets` gera em `.env` (permissão 600) as que faltam. O `nats.conf` as lê como variáveis de ambiente, e o `honcho` carrega o `.env` para os processos.
4. **`make up` sobe o NATS em segundo plano** (pid e log em `data/nats/`), com a pasta do JetStream passada na linha de comando. `make stop` o derruba, e `make run` sobe o NATS e depois os processos do `Procfile`.

## Consequências

- O `nats.conf` não tem nada secreto e pode ficar público.
- Um papel novo exige uma linha no `nats.conf` e outra em `NATS_ROLES` no Makefile; `make secrets` completa o `.env` sem trocar as senhas que já existem.
