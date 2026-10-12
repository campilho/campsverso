# Plano do M2 — Durabilidade

**Status:** proposta para aprovação · **Data:** 2026-10-11
**Escopo** (escopo §7): adaptador NATS, outbox, arquivador JSONL, snapshots, retomada após queda.
**Pronto quando:** `kill -9` no kernel no meio de um dia → reinício sem lacunas nem duplicatas de `seq`.

## 1. Ideia central: o determinismo faz a recuperação

O kernel do M1 é determinístico: mesmo estado, mesmos comandos nos mesmos ticks, mesmos fatos. O M2 usa isso para recuperar sem gravar o estado inteiro a cada tick:

| Peça | O que guarda | Onde |
|---|---|---|
| **Diário de entradas** | cada comando aplicado e o tick em que valeu (propostas e comandos de controle) | SQLite, tabela `inputs` |
| **Outbox** | cada fato já envelopado, com `seq` e `id`, e a marca de publicado | SQLite, tabela `outbox` |
| **Snapshot** | o estado completo do mundo (entidades, necessidades, ações em curso, estado do RNG, seq, tick) | disco, `data/<mundo>/snapshots/`, com sha256 |

- **Cada tick é uma transação SQLite:** os fatos do tick, as entradas consumidas e o tick corrente gravam juntos. Uma queda no meio do tick perde só o que não foi gravado.
- **Recuperação:**
  1. carrega o último snapshot;
  2. reexecuta o diário até o último tick gravado, conferindo que os fatos regenerados são idênticos aos do outbox;
  3. continua do ponto onde parou.
  - Uma divergência na conferência é erro fatal, porque denuncia uma quebra de determinismo. Assim o próprio reinício vira um teste de determinismo contínuo.
- **Publicação:** um publicador lê o outbox em ordem de `seq` e publica no JetStream com `Nats-Msg-Id` = id do evento. Se cair entre publicar e marcar, republica com o mesmo id, e o JetStream descarta a duplicata. Os consumidores também deduplicam por id (princípio 5 dos contratos).
- **Comandos:** chegam pelo stream `COMMANDS` com consumidor durável. O kernel só confirma (*ack*) depois de gravar a entrada no diário, então um comando recebido e não gravado volta a ser entregue depois do reinício. O kernel deduplica pelo id do comando (ADR-0017).

Isso também prepara o **replay do M3** (critério A5): reexecutar um dia a partir do snapshot e do diário é exatamente o que a recuperação faz.

## 2. O que será construído

1. **`make tools`:** baixa o `nats-server` (linha 2.14, versão fixa) para `.tools/`, conferindo o sha256 publicado no GitHub da NATS. Builds para macOS arm64 e Linux amd64 (para o CI).
2. **`config/nats/nats.conf`:**
   - JetStream ligado, só em `127.0.0.1`;
   - um usuário por processo (kernel, percepção, controlador, gateway, arquivador, operador), com as permissões de assunto do contratos §6;
   - o controlador **não** consegue assinar `internal` (critério A8, testado já aqui).
3. **`config/env/local.yaml`:**
   - retenção por stream (D3: `WORLD` e `OBSERVER` 30 dias, `AGENT` 14, `INTERNAL` 90, `COMMANDS` 30, ADR-0017);
   - caminhos e frequência de snapshot.
   - Mais **`config/worlds/farm-camps-01.yaml`**: mundo, cartucho, seed e data-base (ADR-0038).
4. **Novas portas e adaptadores:**
   - **`WorldStore`** em SQLite: outbox, diário e metadados;
   - **`BlobStore`** em disco: snapshots;
   - **`EventArchive`** em JSONL;
   - **`EventBus`** com NATS JetStream: publicação com deduplicação, consumidores duráveis e criação idempotente dos streams;
   - **`TelemetryPort`:** logs JSON estruturados.
5. **Kernel:**
   - serialização do estado (snapshot) e restauração;
   - recuperação com conferência;
   - **`main.py`** (raiz de composição): lê a configuração e roda nos modos contínuo (acumulador de tempo real), máximo (o mais rápido possível, sem lockstep, que é do M3) e pausado.
6. **Arquivador** (processo próprio):
   - consome todos os streams com consumidores duráveis;
   - grava **um JSONL por mundo e por dia simulado**, só acrescentando;
   - deduplica por id e retoma do ponto certo depois de cair (parte do A6).
7. **`make run` e `make stop`:** sobem o kernel e o arquivador num `Procfile`, com o `honcho`; os outros processos chegam nos marcos seguintes.
8. **CI:** baixa o `nats-server` e roda também os testes que dependem do NATS.

## 3. Testes (critérios de pronto)

- **A7, recuperação:**
  1. NATS de verdade e kernel como processo, em modo contínuo com escala alta (um dia em cerca de 15 s);
  2. `kill -9` no meio do dia e reinício;
  3. no fim, o stream e o arquivo têm `seq` contínua (sem lacunas, sem duplicatas) e o **hash canônico é igual ao de uma execução sem queda**.
- **A6, parte do arquivador:** derrubar o arquivador no meio do dia e religar; o JSONL fica completo e sem repetições.
- **A8:** a credencial do controlador tenta assinar `campsverso.*.internal.>` e é negada pelo NATS.
- **Unidade:**
  - snapshot de ida e volta, com o estado restaurado igual ao original;
  - a conferência da recuperação detecta um fato adulterado;
  - o publicador republica sem duplicar;
  - o arquivador separa os arquivos por dia.

## 4. Decisões para aprovar

| # | Decisão | Recomendação |
|---|---|---|
| 1 | Estratégia de recuperação | snapshot + diário de entradas + reexecução determinística com conferência (seção 1). A alternativa, gravar o estado inteiro a cada tick, é mais simples de explicar, mas mais lenta e não ajuda o replay. |
| 2 | Credenciais do NATS local | geradas na máquina por `make tools`, num arquivo fora do git, e lidas pelo `nats.conf` via variáveis de ambiente. Nada de senha no repositório público. |
| 3 | Frequência de snapshot | a cada hora simulada e ao parar com elegância. A recuperação reexecuta no máximo 60 ticks. |
| 4 | Arquivo histórico | um JSONL por mundo e por dia simulado (`data/archive/<mundo>/dia-0001.jsonl`), só acrescentando. |
| 5 | Subir os processos | `honcho` com um `Procfile` (Python, multiplataforma). |
| 6 | Download | `nats-server` 2.14.x do GitHub oficial da NATS (`nats-io/nats-server`), cerca de 20 MB, com checksum conferido. Preciso do seu ok. |

## 5. Commits previstos

- configuração do NATS e `make tools`;
- portas e adaptadores (SQLite, disco, JSONL, NATS);
- snapshot e recuperação no kernel;
- outbox e publicador;
- `main.py` do kernel e modos de relógio;
- arquivador;
- `make run` e CI com NATS;
- teste de `kill -9` (A7), teste do arquivador (A6) e teste de permissão (A8);
- ADRs e diário.
