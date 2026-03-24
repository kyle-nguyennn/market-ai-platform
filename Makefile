.PHONY: help env up down test lint lint-fix build

RUN = mamba run -n market-ai

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

env: ## Create / update the mamba environment
	mamba env create -f environment.yml --yes || mamba env update -f environment.yml --yes
	$(RUN) pip install --no-deps -e .

up: ## Start local docker-compose stack
	docker compose up -d

down: ## Stop local docker-compose stack
	docker compose down

test: ## Run all tests
	$(RUN) pytest tests/ services/ -v

lint: ## Run linter
	$(RUN) ruff check .

lint-fix: ## Run linter with auto-fix
	$(RUN) ruff check . --fix

build: ## Build all docker images
	docker compose build
