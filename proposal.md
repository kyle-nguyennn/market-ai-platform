# Market AI Platform proposal

1. **Market ML Dataset Platform**
2. **Real-Time Alpha Inference Gateway**
3. **Model Evaluation and Drift Platform**

**Market AI Platform = data plane + inference plane + evaluation/control plane**


---

# 1. High-level architecture

## System view

```text
                ┌──────────────────────────┐
                │   External Data Sources  │
                │ OHLCV / filings / macro  │
                │ news / corp actions      │
                └────────────┬─────────────┘
                             │
                             ▼
                 ┌─────────────────────────┐
                 │ Ingestion Pipelines     │
                 │ batch + streaming       │
                 │ schema validation       │
                 └────────────┬────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────────┐
        │            Dataset Platform (Project 1)         │
        │                                                 │
        │ - canonical schemas                             │
        │ - point-in-time joins                           │
        │ - feature definitions                           │
        │ - dataset versioning / snapshots                │
        │ - data quality checks                           │
        │ - offline training datasets                     │
        │ - online feature materialization                │
        └───────────────┬───────────────────┬────────────┘
                        │                   │
                        │                   │
                        ▼                   ▼
         ┌──────────────────────┐   ┌──────────────────────┐
         │ Feature Store / Cache│   │ Training / Backtest  │
         │ Redis / online state │   │ model build pipeline │
         └───────────┬──────────┘   └──────────┬───────────┘
                     │                         │
                     ▼                         ▼
          ┌──────────────────────┐   ┌──────────────────────┐
          │ Inference Gateway    │   │ Eval / Drift Control │
          │ (Project 2)          │   │ Plane (Project 3)    │
          │                      │   │                      │
          │ - /score API         │   │ - offline metrics    │
          │ - online features    │   │ - regime slices      │
          │ - routing            │   │ - drift detection    │
          │ - shadow / canary    │   │ - model comparison   │
          │ - fallback           │   │ - promotion gates    │
          └───────────┬──────────┘   └──────────┬───────────┘
                      │                         │
                      └─────────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Dashboards / Reports │
                         │ Prometheus / Grafana │
                         │ Streamlit / React    │
                         └──────────────────────┘
```

## What each project proves

### Project 1: Dataset Platform

Demonstrates **AI data infrastructure** capability:

* reproducible datasets
* point-in-time correctness
* lineage
* validation
* feature definitions
* offline/online consistency

### Project 2: Inference Gateway

Demonstrates **AI serving infrastructure** capability:

* low-latency scoring
* online features
* model version routing
* shadow/canary deployment
* reliability and fallbacks

### Project 3: Eval/Drift Control Plane

Demonstrates **AI quality/safety infrastructure** capability:

* regression detection
* data drift
* regime-aware evaluation
* model promotion gates

---

# 2. Monorepo structure

This belongs in a single monorepo because the shared contracts matter more than pretending they are independent companies.

```text
market-ai-platform/
├─ README.md
├─ Makefile
├─ pyproject.toml
├─ poetry.lock
├─ .env.example
├─ docker-compose.yml
├─ .github/
│  ├─ workflows/
│  │  ├─ ci.yml
│  │  ├─ tests.yml
│  │  ├─ lint.yml
│  │  └─ build-images.yml
│  └─ pull_request_template.md
│
├─ docs/
│  ├─ architecture/
│  │  ├─ system-overview.md
│  │  ├─ dataset-platform.md
│  │  ├─ inference-gateway.md
│  │  ├─ eval-control-plane.md
│  │  └─ decisions/
│  │     ├─ 001-monorepo.md
│  │     ├─ 002-parquet-duckdb.md
│  │     ├─ 003-redis-online-store.md
│  │     └─ 004-canary-routing.md
│  ├─ api/
│  │  ├─ dataset-api.md
│  │  ├─ inference-api.md
│  │  └─ eval-api.md
│  ├─ runbooks/
│  │  ├─ backfill.md
│  │  ├─ model-rollout.md
│  │  ├─ stale-data-incident.md
│  │  └─ drift-alert-triage.md
│  └─ diagrams/
│
├─ infra/
│  ├─ docker/
│  │  ├─ dataset-platform.Dockerfile
│  │  ├─ inference-gateway.Dockerfile
│  │  ├─ eval-control-plane.Dockerfile
│  │  └─ worker.Dockerfile
│  ├─ k8s/
│  │  ├─ namespace.yaml
│  │  ├─ dataset-platform/
│  │  ├─ inference-gateway/
│  │  ├─ eval-control-plane/
│  │  ├─ redis/
│  │  ├─ postgres/
│  │  └─ monitoring/
│  ├─ terraform/
│  │  ├─ modules/
│  │  └─ envs/dev/
│  └─ local/
│     ├─ init-db.sql
│     └─ seed-data.sh
│
├─ configs/
│  ├─ sources/
│  │  ├─ prices.yaml
│  │  ├─ macro.yaml
│  │  ├─ filings.yaml
│  │  └─ news.yaml
│  ├─ features/
│  │  ├─ returns.yaml
│  │  ├─ volatility.yaml
│  │  ├─ liquidity.yaml
│  │  ├─ event_features.yaml
│  │  └─ microstructure.yaml
│  ├─ datasets/
│  │  ├─ daily_equities_v1.yaml
│  │  ├─ intraday_etf_v1.yaml
│  │  └─ earnings_event_v1.yaml
│  ├─ models/
│  │  ├─ xgb_alpha_v1.yaml
│  │  ├─ vol_regime_v1.yaml
│  │  └─ baseline_rules.yaml
│  └─ eval/
│     ├─ default.yaml
│     ├─ regime_slices.yaml
│     └─ promotion_gates.yaml
│
├─ data/
│  ├─ raw/
│  ├─ bronze/
│  ├─ silver/
│  ├─ gold/
│  └─ sample/
│
├─ schemas/
│  ├─ market_data/
│  │  ├─ bars.json
│  │  ├─ corp_actions.json
│  │  ├─ macro_series.json
│  │  └─ news_events.json
│  ├─ features/
│  │  ├─ feature_vector.json
│  │  └─ online_feature_snapshot.json
│  ├─ inference/
│  │  ├─ score_request.json
│  │  └─ score_response.json
│  └─ eval/
│     ├─ eval_report.json
│     └─ drift_alert.json
│
├─ libs/
│  ├─ common/
│  │  ├─ logging.py
│  │  ├─ settings.py
│  │  ├─ time.py
│  │  ├─ ids.py
│  │  └─ exceptions.py
│  ├─ contracts/
│  │  ├─ dataset.py
│  │  ├─ feature_store.py
│  │  ├─ model_registry.py
│  │  └─ eval_spec.py
│  ├─ quality/
│  │  ├─ schema_checks.py
│  │  ├─ null_checks.py
│  │  ├─ staleness_checks.py
│  │  ├─ distribution_checks.py
│  │  └─ point_in_time_checks.py
│  ├─ storage/
│  │  ├─ parquet_store.py
│  │  ├─ metadata_store.py
│  │  ├─ redis_store.py
│  │  └─ artifact_store.py
│  ├─ features/
│  │  ├─ registry.py
│  │  ├─ rolling.py
│  │  ├─ event.py
│  │  ├─ liquidity.py
│  │  └─ joins.py
│  ├─ serving/
│  │  ├─ router.py
│  │  ├─ cache.py
│  │  ├─ fallbacks.py
│  │  ├─ batching.py
│  │  └─ shadow.py
│  ├─ models/
│  │  ├─ registry.py
│  │  ├─ loader.py
│  │  ├─ xgb_runner.py
│  │  ├─ torch_runner.py
│  │  └─ onnx_runner.py
│  ├─ eval/
│  │  ├─ metrics.py
│  │  ├─ slices.py
│  │  ├─ drift.py
│  │  ├─ regressions.py
│  │  └─ reports.py
│  └─ ui/
│     ├─ charts.py
│     └─ tables.py
│
├─ services/
│  ├─ dataset-platform/
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ api/
│  │  │  │  ├─ datasets.py
│  │  │  │  ├─ features.py
│  │  │  │  ├─ snapshots.py
│  │  │  │  └─ quality.py
│  │  │  ├─ domain/
│  │  │  │  ├─ dataset_builder.py
│  │  │  │  ├─ snapshot_manager.py
│  │  │  │  ├─ pt_join_engine.py
│  │  │  │  └─ feature_materializer.py
│  │  │  └─ repositories/
│  │  └─ tests/
│  │
│  ├─ inference-gateway/
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ api/
│  │  │  │  ├─ score.py
│  │  │  │  ├─ batch_score.py
│  │  │  │  ├─ models.py
│  │  │  │  └─ health.py
│  │  │  ├─ domain/
│  │  │  │  ├─ scorer.py
│  │  │  │  ├─ online_features.py
│  │  │  │  ├─ routing.py
│  │  │  │  ├─ canary.py
│  │  │  │  └─ fallback.py
│  │  │  └─ repositories/
│  │  └─ tests/
│  │
│  ├─ eval-control-plane/
│  │  ├─ app/
│  │  │  ├─ main.py
│  │  │  ├─ api/
│  │  │  │  ├─ eval_runs.py
│  │  │  │  ├─ drift.py
│  │  │  │  ├─ promotions.py
│  │  │  │  └─ reports.py
│  │  │  ├─ domain/
│  │  │  │  ├─ eval_runner.py
│  │  │  │  ├─ slice_engine.py
│  │  │  │  ├─ drift_engine.py
│  │  │  │  ├─ regression_engine.py
│  │  │  │  └─ promotion_gate.py
│  │  │  └─ repositories/
│  │  └─ tests/
│  │
│  ├─ ingestion-worker/
│  │  ├─ app/
│  │  │  ├─ jobs/
│  │  │  │  ├─ ingest_prices.py
│  │  │  │  ├─ ingest_filings.py
│  │  │  │  ├─ ingest_macro.py
│  │  │  │  └─ validate_raw.py
│  │  │  └─ main.py
│  │  └─ tests/
│  │
│  └─ training-worker/
│     ├─ app/
│     │  ├─ jobs/
│     │  │  ├─ build_dataset.py
│     │  │  ├─ train_xgb.py
│     │  │  ├─ export_model.py
│     │  │  └─ register_model.py
│     │  └─ main.py
│     └─ tests/
│
├─ ui/
│  ├─ ops-dashboard/
│  │  ├─ streamlit_app.py
│  │  └─ pages/
│  │     ├─ dataset_quality.py
│  │     ├─ inference_latency.py
│  │     ├─ drift_monitor.py
│  │     └─ promotion_report.py
│  └─ react-console/
│     └─ ...
│
├─ notebooks/
│  ├─ research/
│  │  ├─ alpha_baseline.ipynb
│  │  ├─ feature_exploration.ipynb
│  │  └─ regime_analysis.ipynb
│  └─ demos/
│     ├─ dataset_diff_demo.ipynb
│     ├─ shadow_eval_demo.ipynb
│     └─ drift_alert_demo.ipynb
│
├─ tests/
│  ├─ integration/
│  │  ├─ test_dataset_to_training_flow.py
│  │  ├─ test_training_to_serving_flow.py
│  │  ├─ test_shadow_mode_flow.py
│  │  └─ test_promotion_gate_flow.py
│  ├─ e2e/
│  │  └─ test_full_replay.py
│  └─ fixtures/
│
└─ scripts/
   ├─ bootstrap.sh
   ├─ run_local_stack.sh
   ├─ backfill_daily.sh
   ├─ seed_sample_data.sh
   ├─ benchmark_inference.py
   └─ replay_market_day.py
```

---

# 3. Architecture by project

## Project 1: Market ML Dataset Platform

### Purpose

Build the source of truth for:

* training datasets
* feature definitions
* point-in-time joins
* dataset snapshots
* offline/online feature consistency

### Core components

* **Ingestion worker**: fetches and normalizes raw market data
* **Validation layer**: schema, null, staleness, duplicate, timestamp sanity
* **Canonical storage**: Parquet in bronze/silver/gold layout
* **Metadata catalog**: dataset versions, schemas, feature lineage
* **Point-in-time join engine**: ensures no leakage
* **Feature registry**: reusable feature definitions
* **Dataset API**: fetch dataset snapshot or feature set by version/as-of time

### Key APIs

```text
GET /datasets
POST /datasets/build
GET /datasets/{name}/versions
GET /datasets/{name}/snapshot/{version}
POST /features/materialize
GET /quality/reports/{dataset_version}
```

### Data design

Use medallion-style tiers:

* **bronze**: raw, lightly normalized
* **silver**: cleaned, deduplicated, typed
* **gold**: model-ready, point-in-time-correct tables

> **Note:** Key signal — correct historical data reconstruction without leakage.

---

## Project 2: Real-Time Alpha Inference Gateway

### Purpose

Serve models against live or replayed market events.

### Core components

* **Model registry**: current production model, candidate model
* **Online feature store/cache**: latest rolling features per symbol
* **Inference API**: sync score endpoint and micro-batch endpoint
* **Router**: route by model version, asset group, regime
* **Shadow scoring module**: score candidate in parallel
* **Canary release logic**: send small % of traffic to candidate
* **Fallback logic**:

  * stale features -> reject or fallback
  * model unavailable -> baseline
  * high latency -> degrade gracefully
* **Observability**:

  * stage timing
  * p50/p95/p99
  * cache hit rate
  * stale-feature rate
  * error rate

### Key APIs

```text
POST /score
POST /batch_score
GET /models
POST /models/promote
POST /models/canary
GET /health
```

### Runtime flow

```text
market event -> validate -> fetch/update online features
-> score prod model
-> optionally score shadow model
-> apply guardrails / thresholding
-> emit score + metadata + latency metrics
```

> **Note:** Key signal — operational layer around ML, not just notebooks.

---

## Project 3: Eval and Drift Control Plane

### Purpose

Decide whether a model is actually safe/useful to deploy.

### Core components

* **Eval runner**: run model on historical or replayed data
* **Metric engine**:

  * AUC / log loss / calibration
  * rank IC
  * bucket spread
  * turnover-aware utility proxy
* **Slice engine**:

  * regime
  * sector
  * liquidity bucket
  * earnings days
* **Drift engine**:

  * feature distribution drift
  * null-rate drift
  * score drift
  * label drift if available
* **Regression engine**:

  * compare candidate vs baseline
* **Promotion gate**:

  * pass/fail based on configurable thresholds
* **Report UI**:

  * diff reports
  * charts
  * top regressions

### Key APIs

```text
POST /eval-runs
GET /eval-runs/{id}
GET /drift/{model_version}
POST /promotions/check
GET /reports/{eval_run_id}
```

> **Note:** Key signal — production ML is not "train once, deploy once."

---

# 4. Recommended tech stack

Keep the stack credible and not overly exotic.

## Core

* **Python**
* **FastAPI**
* **Polars + PyArrow**
* **DuckDB** for local analytics and reproducible demos
* **Postgres** for metadata catalog / control plane state
* **Redis** for online feature cache and hot state
* **Parquet** for dataset artifacts
* **Prometheus + Grafana** for metrics
* **Streamlit** first, React later if needed
* **Docker Compose** for MVP
* **Kubernetes** for production deployment on cloud

## Model layer

* **XGBoost / LightGBM** for first model
* Optional:

  * ONNX runtime for serving benchmark
  * small PyTorch sequence model later


---

# 5. Build plan: 12-week execution plan

This is aggressive but realistic for a portfolio-grade MVP.

## Phase 0: week 1

### Goal

Set the monorepo foundation.

### Deliverables

* monorepo skeleton
* shared config system
* local docker-compose stack
* Postgres + Redis + one FastAPI service booting
* CI: lint + unit tests + build

### Exit criteria

The following commands should all succeed:

```bash
make up
make test
make lint
```

---

## Phase 1: weeks 2–4

## Project 1 MVP: Dataset Platform

### Week 2

Build ingestion and storage foundations.

* ingest daily OHLCV for equities/ETFs
* normalize schema
* write bronze and silver Parquet
* create metadata tables in Postgres
* basic data quality checks

### Week 3

Build feature registry and point-in-time join engine.

* rolling return
* rolling vol
* ADV/liquidity
* event lag features
* point-in-time join API
* reproducible dataset snapshot versioning

### Week 4

Expose dataset service and quality UI.

* `/datasets` and `/features/materialize`
* dataset quality report
* dataset diff by version
* null/staleness dashboard
* one end-to-end dataset build flow

### Phase 1 exit demo

“Build `daily_equities_v1` as-of 2025-12-31, reconstruct the exact same snapshot, and show quality checks + feature lineage.”

---

## Phase 2: weeks 5–7

## Project 2 MVP: Inference Gateway

### Week 5

Training pipeline and model registration.

* build training dataset from Project 1
* train baseline XGBoost alpha/regime model
* save artifact
* model registry table
* inference contract schema

### Week 6

Build online scoring path.

* `/score` endpoint
* online feature fetch from Redis / fallback to recent snapshot
* return score + metadata + timing
* Prometheus metrics

### Week 7

Add rollout and resilience logic.

* shadow scoring
* canary routing
* stale-feature detection
* fallback model / degrade mode
* latency dashboard

### Phase 2 exit demo

“Replay a market day, score live, compare prod vs shadow model, show p95 latency and fallback behavior.”

---

## Phase 3: weeks 8–10

## Project 3 MVP: Eval and Drift Plane

### Week 8

Build offline evaluation engine.

* candidate vs baseline comparison
* AUC / calibration / rank IC / bucket spread
* eval run metadata
* report generation

### Week 9

Build slicing and drift detection.

* sector slices
* volatility regime slices
* liquidity bucket slices
* PSI / KS / JS divergence
* score drift and null-rate drift

### Week 10

Build promotion gates and UI.

* configurable thresholds
* pass/fail summary
* top regressions
* promotion recommendation report

### Phase 3 exit demo

“Candidate model improved headline AUC but regressed in high-volatility ETF regime, so promotion was blocked.”

---

## Phase 4: weeks 11–12

## Integration and polish

### Week 11

Productionize the story.

* integration tests across all 3 services
* runbooks
* architecture docs
* benchmark scripts
* replay scripts
* seed datasets
* polished screenshots / demo gifs

### Week 12

Pitch packaging.

* README with architecture diagrams
* case-study writeup
* design tradeoffs
* future directions with Kafka/K8s/Triton
* record short demo video
* convert into selling bullets and talking points

### Final demo

A single scripted demo:

1. ingest market data
2. build snapshot dataset
3. train model
4. serve model live on replayed events
5. compare candidate vs prod
6. detect drift / regression
7. block or approve promotion

> **Note:** Strong demo asset.

---

# 6. Milestones and artifacts

## Milestone 1: dataset credibility

Required:

* versioned snapshot build
* feature registry
* point-in-time correctness
* quality dashboard

## Milestone 2: inference credibility

Required:

* live/replay scoring
* latency metrics
* shadow model
* canary routing
* graceful fallback

## Milestone 3: ML ops credibility

Required:

* offline evaluation reports
* regime-based slices
* drift alerts
* promotion gates

## Milestone 4: portfolio credibility

Required:

* docs
* tests
* screenshots
* repeatable demo
* clean repo

---

# 7. MVP scope vs stretch scope

## Must-have MVP

* daily bars or intraday bars for a manageable universe
* one baseline model
* dataset snapshots
* point-in-time joins
* `/score`
* shadow mode
* drift report
* promotion gate

## Nice stretch goals

* Kafka/Redpanda streaming ingestion
* K8s deployment
* ONNX / Triton benchmark
* event-driven online feature updater
* multimodal text features from filings/news
* feature store abstraction layer
* canary auto-rollback

---

# 8. Goals

## Overall

* Built an end-to-end **Market AI Platform** in a monorepo spanning data infrastructure, online inference, and evaluation control planes for stock-market ML workloads.
* Designed a **versioned dataset platform** with point-in-time-correct joins, reproducible snapshot builds, schema/data-quality validation, and feature lineage for offline training and online serving consistency.
* Implemented a **real-time inference gateway** with online feature retrieval, low-latency model scoring, shadow deployments, canary routing, and fallback paths for stale-data and model-failure scenarios.
* Developed an **evaluation and drift control plane** with regime-aware slicing, candidate-vs-baseline regression analysis, feature/score drift detection, and configurable model promotion gates.
* Added production-style operational controls including structured observability, latency SLO dashboards, integration tests, replay tooling, and incident runbooks for model rollout and stale-data triage.

## Project 1

* Built a market dataset platform that ingests OHLCV, macro, and event data into canonical Parquet datasets with metadata-backed versioning and reproducible rebuilds.
* Implemented point-in-time feature joins and leakage checks to ensure historically correct training datasets for financial ML workflows.
* Created data-quality pipelines covering schema validation, missingness, staleness, duplicate timestamps, and version-to-version dataset diffing.

## Project 2

* Built a low-latency inference gateway for stock/ETF models with model registry integration, online feature caching, shadow scoring, canary rollout, and graceful degradation paths.
* Instrumented the serving path with per-stage latency metrics, cache-hit metrics, stale-feature alerts, and replay tooling for deterministic debugging.

## Project 3

* Developed an evaluation control plane for model validation across market regimes, sectors, and liquidity buckets, with calibration, ranking, and bucket-spread metrics.
* Added drift monitoring and promotion gates to prevent rollout of models that regressed under high-volatility or low-liquidity conditions.

---

# 9. Elevator pitch (30s)

"This is a market AI platform with three layers: a dataset platform for point-in-time-correct training data, a real-time inference gateway for online scoring and shadow/canary rollout, and an evaluation control plane for drift detection and promotion gates. Market data was chosen because it forces rigor around leakage, latency, and regime shifts, which makes the infra problems concrete."

> **Note:** Signals systems thinking, ML infra depth, production tradeoffs, and domain rigor.

---

# 10. GitHub README

## README sections

* problem statement
* system diagram
* why market data is a good stress test for AI infra
* architecture of each service
* local quickstart
* example API flows
* screenshots of dashboards
* design tradeoffs
* future improvements

## Screenshots to include

* dataset quality dashboard
* inference latency dashboard
* shadow vs prod score comparison
* drift report
* promotion gate report

---

# 11. Implementation prioritization

1. `libs/common`, `libs/storage`, `libs/quality`
2. ingestion worker
3. dataset-platform APIs
4. training worker + model registry
5. inference-gateway `/score`
6. shadow/canary/fallback
7. eval engine
8. drift engine
9. dashboards
10. integration tests and docs

> **Note:** This order minimizes rework.

---

# 12. Good first concrete dataset/model choices

Keep the first version simple.

## Dataset

* daily OHLCV bars for S&P 500 or liquid ETFs
* optional macro daily series
* optional earnings calendar events

## First model

Choose one (TBC):

* next-day direction classifier
* volatility regime classifier
* ETF rotation scorer

> **Preferred:** **volatility regime classifier** or **ETF rotation scorer** because the inference/eval story is cleaner than trying to defend alpha claims.

---

## Engineering signals

| Area | What this project demonstrates |
|---|---|
| **Data correctness at scale** | Point-in-time joins, leakage prevention, schema validation, and reproducible dataset snapshots — the hardest part of production ML data pipelines |
| **Heterogeneous storage design** | Deliberate tiering across Parquet (bronze/silver/gold), Postgres (control plane metadata), and Redis (low-latency online state) with explicit tradeoff reasoning |
| **ML serving reliability** | Shadow deployments, canary routing, stale-feature detection, and graceful degradation — not just a `/predict` endpoint |
| **Evaluation discipline** | Regime-aware slicing, candidate-vs-baseline regression analysis, and configurable promotion gates before any model reaches production |
| **Operational maturity** | Structured observability (Prometheus/Grafana), latency SLO tracking, incident runbooks, and replay tooling for deterministic debugging |
| **Systems thinking** | Three planes (data / inference / eval-control) designed as a coherent platform with shared contracts, not three disconnected prototypes |

