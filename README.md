# market-ai-platform

Data plane, inference plane, and eval/control plane for market signal research and production serving.

## Architecture

| Layer               | Service                | Port  |
|---------------------|------------------------|-------|
| Data plane          | `dataset-platform`     | 8001  |
| Inference plane     | `inference-gateway`    | 8002  |
| Eval / control      | `eval-control-plane`   | 8003  |
| Observability       | Prometheus / Grafana   | 9090 / 3000 |

Storage: Postgres 16 (metadata), Redis 7 (online feature cache), Parquet + DuckDB (datasets).
ML stack: PyTorch (GPU), XGBoost, LightGBM, ONNX Runtime.

```
libs/           shared libraries (common, contracts, features, models, …)
services/       FastAPI services + CLI workers
configs/        YAML-driven pipeline configuration
schemas/        JSON schemas for data contracts
data/           local data lake (raw → bronze → silver → gold)
notebooks/      research notebooks and demos
infra/          Dockerfiles, Terraform, local dev infra
scripts/        bootstrap, backfill, seeding helpers
tests/          unit, integration, e2e
ui/             Streamlit ops dashboard
```

---

## Prerequisites

- **Docker** and **Docker Compose** (v2)
- **Micromamba** — [install guide](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)
- NVIDIA GPU + driver ≥ 525 (optional; required for GPU-accelerated training/inference)

---

## Dev Environment Setup

### Quick start (recommended)

```bash
git clone <repo-url> && cd market-ai-platform
./scripts/bootstrap.sh
```

`bootstrap.sh` will:
1. Create the `market-ai` mamba environment from `environment.yml`
2. Install the monorepo packages in editable mode (`pip install --no-deps -e .`)
3. Copy `.env.example` → `.env` (if `.env` does not exist)
4. Start Postgres and Redis via Docker Compose
5. Apply the database schema

### Manual setup

```bash
# Create the mamba environment
micromamba env create -f environment.yml --yes

# Activate it
micromamba activate market-ai

# Editable install of libs/*
pip install --no-deps -e .

# Copy env file
cp .env.example .env

# Start infrastructure
docker compose up -d postgres redis
```

---

## Developing

```bash
# Activate the environment (every new terminal)
micromamba activate market-ai

# Start all services (Postgres, Redis, Prometheus, Grafana, 3 FastAPI apps)
make up

# Stop everything
make down

# Run a single service locally (outside Docker, useful for debugging)
uvicorn services.dataset_platform.app.main:app --reload --port 8001
```

### Available Make targets

```
make help     Show available commands
make env      Create / update the mamba environment
make up       Start local docker-compose stack
make down     Stop local docker-compose stack
make test     Run all tests
make lint     Run linter
make build    Build all docker images
```

### Jupyter notebooks

```bash
jupyter lab --notebook-dir=notebooks/
```

Notebooks share the same `market-ai` environment, so PyTorch GPU, all ML libs, and the monorepo packages are available without extra setup.

---

## Testing

```bash
# Run full test suite
make test

# Run specific test directories
micromamba run -n market-ai pytest tests/unit/ -v
micromamba run -n market-ai pytest tests/integration/ -v
micromamba run -n market-ai pytest tests/e2e/ -v

# Run tests for a single module
micromamba run -n market-ai pytest tests/unit/test_features.py -v

# Run with coverage (if pytest-cov is installed)
micromamba run -n market-ai pytest tests/ --cov=libs --cov-report=term-missing
```

### Linting

```bash
make lint
# or
micromamba run -n market-ai ruff check .

# Auto-fix
micromamba run -n market-ai ruff check . --fix
```

---

## CI/CD Pipeline

CI runs on every push to `main` and on every pull request via GitHub Actions (`.github/workflows/ci.yml`).

### Pipeline stages

```
lint ──┐
       ├──► build
test ──┘
```

1. **Lint** — runs `ruff check .` against the full codebase.
2. **Test** — installs the environment, runs `pytest tests/ -v`.
3. **Build** — builds all Docker images via `docker compose build`. Only runs after lint and test pass.

The pipeline uses `mamba-org/setup-micromamba@v2` with `cache-environment: true`, so the mamba environment is cached between runs to speed up CI.

### Branch protection (recommended)

Configure the repo to require the `lint`, `test`, and `build` checks to pass before merging PRs to `main`.

---

## Deploying to Pre-prod

### 1. Build images

```bash
make build
# or
docker compose build
```

This builds three service images using the Dockerfiles in `infra/docker/`:
- `dataset-platform`
- `inference-gateway`
- `eval-control-plane`

All images use `mambaorg/micromamba:1.5-jammy` as the base and install the full environment from `environment.yml`.

### 2. Configure environment

Create a `.env` file on the target host from `.env.example`. Update values for the pre-prod environment:

```bash
POSTGRES_HOST=<pre-prod-db-host>
POSTGRES_PASSWORD=<strong-password>
REDIS_HOST=<pre-prod-redis-host>
```

### 3. Push images to a registry

```bash
# Tag and push (substitute your registry)
docker compose build
docker tag market-ai-platform-dataset-platform:latest <registry>/dataset-platform:<tag>
docker tag market-ai-platform-inference-gateway:latest <registry>/inference-gateway:<tag>
docker tag market-ai-platform-eval-control-plane:latest <registry>/eval-control-plane:<tag>

docker push <registry>/dataset-platform:<tag>
docker push <registry>/inference-gateway:<tag>
docker push <registry>/eval-control-plane:<tag>
```

### 4. Deploy

```bash
# On the pre-prod host
docker compose up -d
```

For GPU-enabled services (training-worker, inference-gateway), ensure the host has the NVIDIA Container Toolkit installed and add `deploy.resources.reservations.devices` to the relevant service in `docker-compose.yml`.

### 5. Verify

```bash
# Health checks
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# Prometheus metrics
curl http://localhost:9090/api/v1/targets
```