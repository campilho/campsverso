# Campsverso: ponto de entrada (CLAUDE.md, seção "Comandos").
# Compatível com o GNU Make 3.81 do macOS.

SHELL := /bin/bash
export PATH := $(HOME)/.local/bin:$(PATH)

UV ?= uv
PNPM ?= pnpm
PY := $(UV) run --locked
CONTRACTS := $(PY) python -m campsverso_tools.contracts
COMPAT_BASE ?= HEAD

# nats-server com versão e sha256 fixados (ADR-0024). Os hashes vêm do SHA256SUMS da release.
NATS_VERSION := 2.14.8
NATS_SHA256_darwin-arm64 := e54a183a09ffca0e0d9ae1631ebabfbf466dea0945362ad7ad71dbe8c860d45f
NATS_SHA256_linux-amd64 := c60504071c86bced5fc1d89410cee2b319a07e01ee64cb14f5934a2238022021
NATS_DIR := .tools/nats-server-v$(NATS_VERSION)
NATS_BIN := .tools/bin/nats-server
NATS_PID := data/nats/nats-server.pid
NATS_LOG := data/nats/nats-server.log
NATS_ROLES := KERNEL ARCHIVER PERCEPTION CONTROLLER GATEWAY OPERATOR BUDGET MIND

.DEFAULT_GOAL := help
.PHONY: help setup contracts check lint fmt types test arch contracts-check compat \
        up stop run ui ui-build sandbox soak replay metrics ui-e2e mapa-visual sessoes tools secrets fita corrida \
        arena arena-report

help: ## lista os alvos
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-16s %s\n", $$1, $$2}'

setup: tools ## instala dependências Python (uv), TypeScript (pnpm) e o nats-server
	$(UV) sync --locked
	$(PNPM) install --frozen-lockfile

contracts: ## valida os schemas e regenera packages/contracts-* e contracts/asyncapi.yaml
	$(CONTRACTS) check
	$(CONTRACTS) codegen
	$(PNPM) -s contracts:codegen
	$(PNPM) -s contracts:validate

check: lint types test arch contracts-check compat ## lint + tipos + testes + arquitetura + contratos
	@echo "make check: tudo verde."

lint: ## ruff e eslint
	$(PY) ruff check .
	$(PY) ruff format --check .
	$(PNPM) -s lint

fmt: ## formata o código Python
	$(PY) ruff check --fix .
	$(PY) ruff format .

types: ## pyright (estrito) e tsc
	$(PY) pyright
	$(PNPM) -s typecheck

test: ## pytest e vitest
	$(PY) pytest
	$(PNPM) -s test

arch: ## teste de arquitetura: import-linter e dependency-cruiser
	$(PY) lint-imports
	$(PNPM) -s arch

contracts-check: ## valida contratos e exemplos sem escrever nada; falha se o codegen mudar algum arquivo
	$(CONTRACTS) check
	$(CONTRACTS) codegen --check
	$(PNPM) -s contracts:validate
	$(PNPM) -s contracts:codegen -- --check

compat: ## mesma versão maior só ganha campos opcionais (compara com COMPAT_BASE, padrão HEAD)
	$(CONTRACTS) compat --base $(COMPAT_BASE)

up: tools secrets ## sobe o NATS em segundo plano (log em data/nats/nats-server.log)
	@mkdir -p data/nats
	@if [ -f $(NATS_PID) ] && kill -0 "$$(cat $(NATS_PID))" 2>/dev/null; then \
	  echo "NATS já está no ar (pid $$(cat $(NATS_PID)))"; \
	else \
	  set -a; . ./.env; set +a; \
	  nohup $(NATS_BIN) -c config/nats/nats.conf -sd data/nats/jetstream \
	    -P $(NATS_PID) -l $(NATS_LOG) >/dev/null 2>&1 & \
	  for _ in $$(seq 50); do grep -q "Server is ready" $(NATS_LOG) 2>/dev/null && break; sleep 0.1; done; \
	  grep -q "Server is ready" $(NATS_LOG) || { echo "o NATS não subiu; veja $(NATS_LOG)"; exit 1; }; \
	  echo "NATS no ar em 127.0.0.1:4222 (pid $$(cat $(NATS_PID)))"; \
	fi

stop: ## derruba o NATS que o make up subiu
	@if [ -f $(NATS_PID) ] && kill -0 "$$(cat $(NATS_PID))" 2>/dev/null; then \
	  $(NATS_BIN) --signal stop=$(NATS_PID) && echo "NATS parado"; \
	else \
	  echo "NATS não está no ar"; \
	fi

run: up ui-build ## sobe os cinco processos com o honcho (Procfile); UI em http://127.0.0.1:8765/?view=operator
	$(PY) honcho start -f Procfile

ui-build: ## compila a UI em apps/ui/dist, que o gateway serve
	$(PNPM) -s --filter @campsverso/ui build

ui: ## UI em modo desenvolvimento (Vite em http://127.0.0.1:5173), ligada ao gateway de make run ou sandbox
	$(PNPM) --filter @campsverso/ui dev

sandbox: tools ui-build ## mundo descartável com tudo ligado, em data/sandbox/<data-hora>; MENTE=camps põe o LLM no Camps (ADR-0059); Ctrl+C para parar
	$(if $(MENTE),uv run --locked --env-file .env,$(PY)) python -m campsverso_testkit.sandbox --world config/worlds/$(MUNDO).yaml --out data/sandbox/$$(date +%Y%m%d-%H%M%S) $(if $(MENTE),--mind $(MENTE),)

DIAS ?= 1

# farm_boavista grava a fita da fazenda 2 (ADR-0062). O comentário fica na linha de cima: o make
# guarda os espaços antes de um `#` no valor da variável (o CI de 20/out subiu `config/worlds/.yaml`).
CARTUCHO ?= farm_camps

fita: ## grava em processo a fita de teste do controlador LLM, chamando a API (ADR-0059): make fita DIAS=1 [CARTUCHO=farm_boavista]
	uv run --locked --env-file .env python -m campsverso_testkit.fita --days $(DIAS) --cartridge $(CARTUCHO)

corrida: ## N dias em processo com a mente sobre a API, com ou sem memória (ADR-0060): make corrida DIAS=7 [SEM_MEMORIA=1]
	uv run --locked --env-file .env python -m campsverso_testkit.corrida --days $(DIAS) $(if $(SEM_MEMORIA),--sem-memoria,)

ARENA_DIAS ?= 30
# No macOS, o caffeinate segura o Mac acordado enquanto a arena roda (horas de chamadas à API);
# sem ele, o Mac dorme quando ninguém mexe e as corridas param junto (19/out).
CAFFEINATE := $(shell command -v caffeinate >/dev/null 2>&1 && echo "caffeinate -i")

arena: ## as corridas da arena em sequência, em data/arena/<data-hora> (ADR-0061): make arena [RODADA=boavista] [ARENA_DIAS=30] [SO=haiku-memoria] [PASTA=data/arena/x]
	$(CAFFEINATE) uv run --locked --env-file .env python -m campsverso_testkit.arena --days $(ARENA_DIAS) $(if $(RODADA),--rodada $(RODADA),) $(foreach s,$(SO),--only $(s)) $(if $(PASTA),--out $(PASTA),)

arena-report: ## o relatório da arena em docs/arena/AAAA-MM-DD.md, da arena mais recente ou de PASTA=data/arena/x
	$(PY) python -m campsverso_tools.arena $(PASTA)

DAYS ?= 30
# O arquivo do mundo em config/worlds/; farm-boavista-01 é a fazenda 2 (M13). Comentário na linha de cima, como acima.
MUNDO ?= farm-camps-01
ARCHIVE ?= data/archive/$(MUNDO)
EVERY ?= 20
export MUNDO

soak: tools ## resistência com processos e NATS próprios: make soak DAYS=30 (SEM_REGRA=1 desliga a R-001)
	$(PY) python -m campsverso_testkit.soak --days $(DAYS) --world config/worlds/$(MUNDO).yaml \
	  --out data/soak/$$(date +%Y%m%d-%H%M%S) $(if $(SEM_REGRA),--sem-regra,)

replay: ## reexecuta um dia gravado do mundo e compara com o arquivo: make replay DAY=N [MUNDO=farm-boavista-01]
	@test -n "$(DAY)" || { echo "uso: make replay DAY=N [MUNDO=farm-boavista-01]"; exit 1; }
	$(PY) python -m campsverso_kernel.main --replay-day $(DAY) --world config/worlds/$(MUNDO).yaml

metrics: ## métricas da bíblia §13 a partir do arquivo: make metrics [ARCHIVE=pasta do mundo]
	$(PY) python -m campsverso_tools.metrics $(ARCHIVE)

percepcao: ## tokens da percepção por dia a partir do arquivo (ADR-0056): make percepcao [ARCHIVE=pasta] [EVERY=20] [CONTAR=20]
	$(if $(CONTAR),uv run --locked --env-file .env,$(PY)) python -m campsverso_tools.perception_budget $(ARCHIVE) --every $(EVERY) $(if $(CONTAR),--contar $(CONTAR),)

llm-smoke: ## uma chamada real pela porta de modelo, medida e publicada pelo contrato (ADR-0058): make llm-smoke [MODEL=claude-haiku-5-5]
	uv run --locked --env-file .env python -m campsverso_tools.llm_smoke --model $(or $(MODEL),claude-haiku-5-5)

ui-e2e: tools ui-build ## fumaça da tela no navegador (Playwright), com um sandbox próprio na porta 8799 [MUNDO=farm-boavista-01]
	pnpm --filter @campsverso/ui exec playwright test

mapa-visual: ## regrava o mapa visual da fazenda a partir do mapa lógico (ADR-0053)
	$(PY) python -m campsverso_tools.visual_map

sessoes: ## tempo e tokens por turno e por marco em docs/custos (MARCO=M5 marca os turnos novos)
	$(PY) python -m campsverso_tools.sessions $(if $(MARCO),--marco $(MARCO),)

secrets: ## gera em .env (fora do git) as senhas do NATS que ainda faltam
	@touch .env && chmod 600 .env
	@for role in $(NATS_ROLES); do \
	  grep -q "^NATS_$${role}_PASSWORD=" .env || echo "NATS_$${role}_PASSWORD=$$(openssl rand -hex 24)" >> .env; \
	done
	@grep -q "ANTHROPIC_API_KEY=" .env || { echo "# ANTHROPIC_API_KEY=cole-aqui-a-chave-da-console (ADR-0058; o make llm-smoke, o CONTAR=20, o make fita e o sandbox com MENTE usam)" >> .env; echo "aviso: ANTHROPIC_API_KEY ausente em .env; o make llm-smoke precisa dela"; }

tools: $(NATS_DIR)/nats-server ## baixa ferramentas locais com versão fixa (nats-server), conferindo o sha256

$(NATS_DIR)/nats-server:
	@set -euo pipefail; \
	case "$$(uname -s)-$$(uname -m)" in \
	  Darwin-arm64) platform=darwin-arm64; expected=$(NATS_SHA256_darwin-arm64) ;; \
	  Linux-x86_64) platform=linux-amd64; expected=$(NATS_SHA256_linux-amd64) ;; \
	  *) echo "sem nats-server fixado para $$(uname -s)-$$(uname -m)"; exit 1 ;; \
	esac; \
	name=nats-server-v$(NATS_VERSION)-$$platform; \
	mkdir -p .tools/download .tools/bin; \
	echo "baixando $$name.tar.gz do GitHub da NATS"; \
	curl -fsSL -o .tools/download/$$name.tar.gz \
	  https://github.com/nats-io/nats-server/releases/download/v$(NATS_VERSION)/$$name.tar.gz; \
	actual=$$( (command -v sha256sum >/dev/null && sha256sum .tools/download/$$name.tar.gz \
	  || shasum -a 256 .tools/download/$$name.tar.gz) | cut -d' ' -f1); \
	if [ "$$actual" != "$$expected" ]; then \
	  echo "sha256 não confere: $$actual (esperado $$expected)"; rm -f .tools/download/$$name.tar.gz; exit 1; \
	fi; \
	rm -rf $(NATS_DIR) && mkdir -p $(NATS_DIR); \
	tar -xzf .tools/download/$$name.tar.gz -C $(NATS_DIR) --strip-components=1; \
	ln -sf ../nats-server-v$(NATS_VERSION)/nats-server $(NATS_BIN); \
	echo "nats-server $(NATS_VERSION) em $(NATS_BIN)"
