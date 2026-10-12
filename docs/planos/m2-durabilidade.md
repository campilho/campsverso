# Plano do M2 — Durabilidade

**Status:** todas as decisões aprovadas em 11/out/2026; **aguardando o OK do usuário para começar a implementação.**
**Escopo** (escopo §7): adaptador NATS, outbox, arquivador JSONL, snapshots, retomada após queda.
**Pronto quando:** `kill -9` no kernel no meio de um dia → reinício sem lacunas nem duplicatas de `seq`.

## 0. Primeiro passo: ajuste do sono (ADR-0041)

- Dormir em qualquer lugar: sem alvo, o avatar dorme onde está, com o sono ruim do gênero (5/h). Com alvo, uma cama ou análogo ao lado dá a taxa do móvel (cama 12,5/h).
- A primitiva `start_sleep` do kernel passa a receber as taxas de recuperação daquele sono.
- Atualizar bíblia §7 e §8, dados do gênero e testes.

## 1. Recuperação: snapshot completo + incrementais, como num banco de dados

É a estratégia de backup de um banco: um **snapshot completo** de tempos em tempos e **incrementais** no intervalo. Na falha: último completo + incrementais.

O incremental escolhido é o menor possível: **as entradas, não o estado.** É o equivalente ao *write-ahead log* (WAL) de um banco, ou ao log de comandos do Redis. Isso só funciona porque o kernel é determinístico: o mesmo estado mais os mesmos comandos nos mesmos ticks dão os mesmos fatos. Assim, o tamanho do incremental cresce com o número de comandos (pequeno), e não com o tamanho do estado do mundo, que no futuro pode ser grande e complexo.

| Peça | O que guarda | Onde | Configuração |
|---|---|---|---|
| **Snapshot completo** | todo o estado do mundo: entidades, necessidades, ações em curso, RNG, seq, tick, versão do código e dos cartuchos | disco, `data/<mundo>/snapshots/`, com sha256 | `snapshots.full_every_ticks` (início: 60 = 1 hora simulada) e `snapshots.keep_full` (quantos guardar) |
| **Incremental (diário de entradas)** | cada comando aplicado e o tick em que valeu | SQLite, tabela `inputs` | — |
| **Outbox** | cada fato já envelopado, com `seq`, `id` e a marca de publicado | SQLite, tabela `outbox` | — |

- **Cada tick é uma transação SQLite:** os fatos do tick, as entradas consumidas e o tick corrente gravam juntos.
- **Recuperação:**
  1. carrega o último snapshot completo;
  2. reexecuta os incrementais até o último tick gravado, conferindo que os fatos regenerados são idênticos aos do outbox;
  3. continua do ponto onde parou.
  - Divergência na conferência é erro fatal: denuncia quebra de determinismo.
- **Proteção de versão:** o snapshot guarda a versão do código e dos cartuchos. A recuperação se recusa a reexecutar incrementais gravados por outra versão.
  - Por isso, parar com elegância (para um deploy, por exemplo) sempre grava um snapshot completo antes (tempo §9.2).
- **Se um dia o estado ficar enorme** (centenas de agentes), dá para acrescentar snapshots diferenciais (só as entidades que mudaram) atrás da mesma porta, sem mudar o resto.
- **Publicação no NATS:** um publicador lê o outbox em ordem de `seq` e publica com `Nats-Msg-Id` = id do evento. Republicar depois de uma queda não duplica, porque o JetStream e os consumidores deduplicam por id.
- **Comandos:** chegam pelo stream `COMMANDS` com consumidor durável. O kernel só confirma depois de gravar a entrada; um comando não gravado volta a ser entregue depois do reinício e é deduplicado pelo id (ADR-0017).
- **O mesmo mecanismo prepara o replay do M3** (critério A5): reexecutar um dia a partir de um snapshot e do diário.

## 2. Arquivo histórico e retenção

- **Um JSONL por mundo e por dia simulado** (`data/archive/<mundo>/dia-0001.jsonl`), só acrescentando.
- **Guardar todos os dias?** No começo e nos experimentos, sim. Estimativa: um dia roteirizado da fazenda gera cerca de 112 KB, uns 40 MB por ano por mundo, ou uns 4 MB comprimido.
- **Política proposta:**
  - **Comprimir os dias antigos** (gzip, `archive.compress_after_days`, início: 7). Comprimir não reescreve o conteúdo.
  - **Mover para armazenamento frio** (disco externo ou, na fase AWS, S3 Glacier) quando o volume pedir.
  - **Apagar só por decisão manual do operador**, nunca automaticamente. O CLAUDE.md proíbe apagar ou reescrever `data/archive/`: é o registro histórico dos experimentos e a base do replay público.
- **Testes nunca escrevem em `data/archive/`:** usam pastas temporárias, apagadas ao fim do teste.
- **Retenção dos streams no NATS** é outra coisa: é a janela quente, configurável por stream (D3). Lá os dados vencem sozinhos, porque o arquivo JSONL é a memória longa.

## 3. O que será construído

1. **`make tools`:** baixa o `nats-server` (linha 2.14, versão fixa) para `.tools/`, conferindo o sha256 publicado no GitHub da NATS. Builds para macOS arm64 e Linux amd64 (para o CI).
2. **`config/nats/nats.conf`:**
   - JetStream ligado, só em `127.0.0.1`;
   - um usuário por processo, com as permissões de assunto do contratos §6;
   - o controlador não consegue assinar `internal` (A8);
   - **as senhas são geradas na máquina, num arquivo fora do git** (decisão 2), e lidas via variáveis de ambiente.
3. **`config/env/local.yaml`:**
   - retenção dos streams;
   - caminhos;
   - `snapshots.full_every_ticks`, `snapshots.keep_full` e `archive.compress_after_days`.
   - Mais **`config/worlds/farm-camps-01.yaml`**: mundo, cartucho, seed e data-base (ADR-0038).
4. **Novas portas e adaptadores:**
   - **`WorldStore`** em SQLite: outbox, diário e metadados;
   - **`BlobStore`** em disco: snapshots;
   - **`EventArchive`** em JSONL, com compressão dos dias antigos;
   - **`EventBus`** com NATS JetStream: deduplicação, consumidores duráveis e criação idempotente dos streams;
   - **`TelemetryPort`:** logs JSON estruturados.
5. **Kernel:**
   - snapshot completo (serializar e restaurar) e recuperação com conferência e proteção de versão;
   - **`main.py`:** modos contínuo (acumulador de tempo real), máximo (o mais rápido possível; o lockstep é do M3) e pausado.
6. **Arquivador** (processo próprio): consome todos os streams com consumidores duráveis, deduplica por id e retoma do ponto certo depois de cair.
7. **`make run` e `make stop`:** sobem os processos juntos (decisão 5).
8. **CI:** baixa o `nats-server` e roda também os testes que dependem do NATS.

## 4. Testes (critérios de pronto)

- **A7, recuperação:**
  1. NATS de verdade e kernel como processo, em modo contínuo com escala alta (um dia em cerca de 15 s);
  2. `kill -9` no meio do dia e reinício;
  3. `seq` contínua (sem lacunas nem duplicatas) e **hash canônico igual ao de uma execução sem queda**.
- **A6, parte do arquivador:** derrubar e religar o arquivador no meio do dia; o JSONL fica completo e sem repetições.
- **A8:** a credencial do controlador tenta assinar `campsverso.*.internal.>` e é negada pelo NATS.
- **Unidade:**
  - snapshot de ida e volta;
  - a recuperação detecta um fato adulterado e uma versão diferente;
  - o publicador republica sem duplicar;
  - o arquivador separa os arquivos por dia e comprime os antigos.

## 5. Decisões

| # | Decisão | Situação |
|---|---|---|
| 1 | Recuperação: snapshot completo + incrementais (diário de entradas), configurável | **aprovada** (seção 1) |
| 2 | Credenciais do NATS: nada no repositório | **aprovada** |
| 3 | Snapshot completo a cada hora simulada, configurável | **aprovada** |
| 4 | JSONL por mundo e por dia; retenção: comprimir após 7 dias, armazenamento frio depois, apagar só manualmente | **aprovada**, com a política da seção 2 |
| 5 | Subir os processos juntos com `honcho` + `Procfile` (abaixo) | **aprovada** |
| 6 | Baixar o `nats-server` 2.14.x do GitHub oficial da NATS | **aprovada** (o download acontece só quando o M2 começar) |

### O que é a decisão 5

O sistema é feito de **processos separados**: o kernel e o arquivador agora; a percepção, o controller-runner e o gateway nos próximos marcos; mais o NATS. Para desenvolver, é preciso subir todos juntos, ver os logs num terminal só e derrubar todos de uma vez. As opções:

| Opção | Como é | Prós | Contras |
|---|---|---|---|
| **honcho + Procfile** (escolhida) | O `Procfile` tem uma linha por processo (`kernel: uv run python -m campsverso_kernel.main`). O `honcho`, uma ferramenta pequena em Python (versão do Foreman, do Ruby), sobe todos, mostra os logs com o nome de cada um em cores, e Ctrl+C derruba todos | entra como dependência de desenvolvimento pelo `uv`; nada global para instalar; funciona igual no Mac e no Linux | é mais uma ferramenta |
| Script bash | um script sobe cada processo em segundo plano e derruba todos ao sair | nenhuma dependência | frágil: processos órfãos, logs misturados, código para manter |
| `docker compose` | um container por processo | é o caminho da AWS (ADR-0024) | exige Docker, que não está instalado; fica para antes da AWS |

O `Procfile` tem quase o mesmo formato dos serviços de um `docker-compose.yml`, então a troca, quando os containers chegarem, é direta.

## 6. Commits previstos

- ajuste do sono (ADR-0041);
- configuração do NATS e `make tools`;
- portas e adaptadores (SQLite, disco, JSONL, NATS);
- snapshot e recuperação no kernel;
- outbox e publicador;
- `main.py` do kernel e modos de relógio;
- arquivador;
- `make run` e CI com NATS;
- testes A7, A6 e A8;
- ADRs e diário.
