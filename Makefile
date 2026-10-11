# Campsverso: ponto de entrada (CLAUDE.md, seção "Comandos").
# Compatível com o GNU Make 3.81 do macOS.

SHELL := /bin/bash
export PATH := $(HOME)/.local/bin:$(PATH)

UV ?= uv
PNPM ?= pnpm
PY := $(UV) run --locked
CONTRACTS := $(PY) python -m campsverso_tools.contracts
COMPAT_BASE ?= HEAD

.DEFAULT_GOAL := help
.PHONY: help setup contracts check lint fmt types test arch contracts-check compat \
        up run ui soak replay tools

help: ## lista os alvos
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-16s %s\n", $$1, $$2}'

setup: ## instala dependências Python (uv) e TypeScript (pnpm)
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

up: ## sobe o NATS (marco M2)
	@echo "make up: ainda não implementado (marco M2)"; exit 1

run: ## sobe kernel, percepção, controller-runner, gateway e arquivador (marcos M2 a M4)
	@echo "make run: ainda não implementado (marcos M2 a M4)"; exit 1

ui: ## sobe a UI em modo desenvolvimento (marco M4)
	@echo "make ui: ainda não implementado (marco M4)"; exit 1

soak: ## resistência em modo máximo com o script: make soak DAYS=30 (marco M3)
	@echo "make soak: ainda não implementado (marco M3)"; exit 1

replay: ## reexecuta um dia a partir do arquivo e compara hashes: make replay DAY=N (marco M3)
	@echo "make replay: ainda não implementado (marco M3)"; exit 1

tools: ## baixa ferramentas locais com versão fixa, como o nats-server (marco M2)
	@echo "make tools: ainda não implementado (marco M2)"; exit 1
