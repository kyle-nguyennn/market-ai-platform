.PHONY: help env up down test lint build

RUN = micromamba run -n market-ai

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

env: ## Create / update the mamba environment
	micromamba env create -f environment.yml --yes || micromamba update -f environment.yml --yes
	$(RUN) pip install --no-deps -e .

up: ## Start local docker-compose stack
	docker compose up -d

down: ## Stop local docker-compose stack
	docker compose down

test: ## Run all tests
	$(RUN) pytest tests/ services/ -v

lint: ## Run linter
	$(RUN) ruff check .

build: ## Build all docker images
docker compose build
