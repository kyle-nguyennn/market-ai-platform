#!/usr/bin/env bash
# bootstrap.sh — first-time dev environment setup
set -euo pipefail

echo "==> Checking prerequisites..."
command -v docker     >/dev/null || { echo "Docker is required."; exit 1; }
command -v mamba >/dev/null || { echo "Mamba is required. Install via Miniforge: https://github.com/conda-forge/miniforge#mambaforge"; exit 1; }

echo "==> Creating mamba environment..."
mamba env create -f environment.yml --yes || mamba env update -f environment.yml --yes

echo "==> Installing project in editable mode..."
mamba run -n market-ai pip install --no-deps -e .

echo "==> Copying .env.example to .env (if not already present)..."
[ -f .env ] || cp .env.example .env

echo "==> Starting infrastructure services (postgres, redis)..."
docker compose up -d postgres redis

echo "==> Waiting for Postgres to be ready..."
until docker compose exec -T postgres pg_isready -U market_ai -q; do
  sleep 1
done

echo "==> Applying database schema..."
docker compose exec -T postgres psql -U market_ai -d market_ai -f /docker-entrypoint-initdb.d/init-db.sql 2>/dev/null || true

echo "==> Bootstrap complete. Run 'make up' to start all services."
