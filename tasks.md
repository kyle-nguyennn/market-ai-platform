# tickets.md

# Market AI Platform — Execution Tickets

This document converts the roadmap into implementation tickets for the monorepo MVP.

## Guiding constraints

- Scope v1 to **20–50 liquid ETFs**
- Use **daily bars** first
- Target use case: **volatility regime classification**
- Stack:
  - Python
  - FastAPI
  - Polars + PyArrow
  - DuckDB
  - Postgres
  - Redis
  - Prometheus + Grafana
  - Streamlit
  - Docker Compose
- Do **not** build these in MVP:
  - filings/news ingestion
  - React frontend
  - Kubernetes/Terraform
  - ONNX/Triton
  - intraday streaming
  - auto rollback
  - multimodal models

---

# Epic 0 — Platform Foundation

## PLAT-1 — Initialize monorepo skeleton
**Goal**  
Create the base repository structure for the Market AI Platform monorepo.

**Scope**
- Create top-level folders:
  - `docs/`
  - `infra/`
  - `configs/`
  - `data/`
  - `schemas/`
  - `libs/`
  - `services/`
  - `ui/`
  - `tests/`
  - `scripts/`
- Add:
  - `README.md`
  - `Makefile`
  - `pyproject.toml`
  - `.env.example`
  - `docker-compose.yml`

**Acceptance criteria**
- Repo structure exists and is committed
- `make help` works
- Python project installs locally
- README contains local setup placeholders

---

## PLAT-2 — Set up Python tooling and CI
**Goal**  
Establish code quality and test tooling early.

**Scope**
- Configure:
  - Ruff
  - MyPy
  - Pytest
- Add GitHub Actions for:
  - lint
  - tests
  - build
- Add PR template

**Acceptance criteria**
- `make lint` runs successfully
- `make test` runs successfully
- CI passes on a clean branch
- At least one sample unit test exists

---

## PLAT-3 — Shared config and settings system
**Goal**  
Create one consistent configuration model across services.

**Scope**
- Add `libs/common/settings.py`
- Support:
  - env var loading
  - service-specific config
  - local dev defaults
- Add config classes for:
  - dataset platform
  - inference gateway
  - eval control plane
  - postgres
  - redis

**Acceptance criteria**
- Each service boots with config loaded from environment
- `.env.example` documents required variables
- Invalid config fails fast with clear error

---

## PLAT-4 — Local runtime stack with Docker Compose
**Goal**  
Make the MVP runnable locally as one stack.

**Scope**
- Add containers for:
  - postgres
  - redis
  - dataset-platform
  - inference-gateway
  - eval-control-plane
  - prometheus
  - grafana
- Add health checks

**Acceptance criteria**
- `docker compose up` boots the stack
- Services respond on health endpoints
- Postgres and Redis are reachable from services
- Prometheus and Grafana UIs are accessible locally

---

## PLAT-5 — Initial database schema migration
**Goal**  
Create the minimal Postgres metadata/control-plane schema.

**Scope**
- Add migration tooling
- Create tables:
  - `datasets`
  - `dataset_sources`
  - `quality_reports`
  - `models`
  - `model_deployments`
  - `eval_runs`
  - `eval_metrics`
  - `drift_alerts`
  - `promotion_decisions`

**Acceptance criteria**
- Migration can be applied from scratch
- Migration can be rerun cleanly in dev
- Table definitions are documented

---

# Epic 1 — Shared Libraries

## LIB-1 — Common utility library
**Goal**  
Create shared utilities used by all services.

**Scope**
- Add:
  - `logging.py`
  - `time.py`
  - `ids.py`
  - `exceptions.py`

**Acceptance criteria**
- Structured logging helper exists
- UTC/time helpers are tested
- ID generation is deterministic where needed
- Common exceptions are reusable across services

---

## LIB-2 — Storage abstraction library
**Goal**  
Centralize storage logic for Parquet, Postgres metadata, and Redis hot state.

**Scope**
- Add:
  - `parquet_store.py`
  - `metadata_store.py`
  - `redis_store.py`
  - `artifact_store.py`
- Support local file-based artifacts for MVP

**Acceptance criteria**
- Can read/write Parquet datasets
- Can persist metadata rows to Postgres
- Can read/write Redis keys
- Unit tests cover each storage adapter

---

## LIB-3 — Quality checks library
**Goal**  
Provide reusable data validation primitives.

**Scope**
- Add:
  - schema checks
  - null checks
  - duplicate key checks
  - staleness checks
  - point-in-time leakage checks

**Acceptance criteria**
- Quality checks return machine-readable results
- Checks can be run in batch from ingestion and dataset build flows
- At least one negative test per check exists

---

## LIB-4 — Contracts and schemas library
**Goal**  
Define cross-service contracts early.

**Scope**
- Add Pydantic/domain contracts for:
  - dataset request/response
  - feature snapshot
  - model metadata
  - score request/response
  - eval run request/response
  - promotion decision
- Align with JSON schemas in `schemas/`

**Acceptance criteria**
- Contracts are versioned
- Services use shared contracts rather than redefining payloads
- Schema validation tests pass

---

# Epic 2 — Market Data Ingestion and Dataset Platform

## DATA-1 — Define v1 canonical schemas
**Goal**  
Define the raw and cleaned schemas for the first dataset slice.

**Scope**
- Add schemas for:
  - `bars_daily`
  - `macro_daily`
  - `symbols`
  - `feature_vector`
  - `online_feature_snapshot`

**Acceptance criteria**
- JSON schemas are written and committed
- Required fields and types are explicit
- Schema examples are included

---

## DATA-2 — Build ETF universe config
**Goal**  
Define a stable v1 ETF universe.

**Scope**
- Create config for 20–50 liquid ETFs
- Include symbol metadata such as category/asset group if available

**Acceptance criteria**
- Universe is stored in config
- Universe hash can be computed for lineage
- Universe is used by ingestion jobs

---

## DATA-3 — Implement daily price ingestion job
**Goal**  
Fetch and store historical daily OHLCV for the ETF universe.

**Scope**
- Add ingestion job for historical daily bars
- Write outputs to `data/raw` or bronze Parquet
- Record source metadata

**Acceptance criteria**
- Job ingests full history for configured universe
- Raw data is persisted to Parquet
- Basic source metadata is recorded
- Job can be rerun idempotently

---

## DATA-4 — Implement silver normalization pipeline
**Goal**  
Clean and normalize raw price data into canonical silver tables.

**Scope**
- Standardize column names and dtypes
- Normalize timestamps
- Deduplicate `(symbol, ts)`
- Enforce sorted time order

**Acceptance criteria**
- Cleaned Parquet output is generated
- Duplicate rows are removed or rejected
- Validation errors are surfaced clearly

---

## DATA-5 — Add macro series ingestion
**Goal**  
Bring in a small macro panel for context features.

**Scope**
- Ingest a small number of daily macro series
- Normalize to canonical schema
- Store in bronze/silver

**Acceptance criteria**
- Macro series data is available in silver format
- Time alignment is consistent with daily bar data
- Source metadata is recorded

---

## DATA-6 — Build quality reporting for ingested data
**Goal**  
Produce persistent quality reports during ingestion.

**Scope**
- Run:
  - schema checks
  - null checks
  - duplicate checks
  - stale timestamp checks
- Store results in `quality_reports`

**Acceptance criteria**
- Every ingestion run emits a quality report
- Failures are queryable in Postgres
- Logs reference quality report IDs

---

## DATA-7 — Implement feature registry v1
**Goal**  
Create reusable feature definitions shared by offline and online paths.

**Scope**
- Add first feature set:
  - `ret_1d`
  - `ret_5d`
  - `ret_20d`
  - `vol_20d`
  - `adv_20d`
  - `range_5d`
  - `market_ret_1d`
- Store feature definitions in YAML plus code implementation

**Acceptance criteria**
- Feature definitions are versioned
- Features can be materialized for a dataset build
- Feature calculations are unit-tested

---

## DATA-8 — Implement point-in-time join engine
**Goal**  
Guarantee no future leakage in dataset builds.

**Scope**
- Join market and macro features using as-of semantics
- Enforce lag rules where needed
- Add leakage tests

**Acceptance criteria**
- Join engine only uses data available at prediction time
- Leakage tests fail when future data is introduced
- Join behavior is documented

---

## DATA-9 — Implement label generation for volatility regime
**Goal**  
Define and build v1 labels for the first ML task.

**Scope**
- Create volatility regime label spec
- Generate label per `(symbol, ts)` using future window logic
- Document exact label definition

**Acceptance criteria**
- Label generation is deterministic
- Labels are aligned to dataset rows correctly
- Label spec version is recorded in dataset metadata

---

## DATA-10 — Build dataset snapshot builder
**Goal**  
Create immutable, reproducible training datasets.

**Scope**
- Build dataset from:
  - universe
  - feature set version
  - label spec version
  - date range
  - as-of date
- Write snapshot to Parquet
- Persist metadata and lineage

**Acceptance criteria**
- Same inputs reproduce the same dataset version/hash
- Dataset version is immutable
- Artifact URI and row count are recorded

---

## DATA-11 — Build dataset service API
**Goal**  
Expose dataset management via FastAPI.

**Scope**
- Add endpoints:
  - `GET /datasets`
  - `POST /datasets/build`
  - `GET /datasets/{name}/versions`
  - `GET /datasets/{name}/versions/{version}`
  - `GET /quality/reports/{dataset_version}`

**Acceptance criteria**
- Endpoints are documented in OpenAPI
- Happy-path integration tests pass
- Validation errors return clean API responses

---

## DATA-12 — Build dataset diff utility
**Goal**  
Compare dataset versions for debugging and reproducibility review.

**Scope**
- Compare:
  - row counts
  - columns
  - min/max timestamp
  - feature coverage
  - label distribution

**Acceptance criteria**
- Version diff can be run from CLI or API
- Output is human-readable and machine-readable
- Useful in debugging rebuild mismatches

---

## DATA-13 — Build dataset quality dashboard page
**Goal**  
Expose data and quality status in Streamlit.

**Scope**
- Show:
  - latest datasets
  - dataset versions
  - null/staleness summary
  - quality violations
  - lineage summary

**Acceptance criteria**
- Dashboard page renders locally
- Latest dataset build status is visible
- Quality reports can be inspected interactively

---

# Epic 3 — Training Worker and Model Registry

## ML-1 — Implement time-based train/val/test split
**Goal**  
Create a leakage-safe training split policy.

**Scope**
- Split by date, not random sampling
- Support configurable cutoffs

**Acceptance criteria**
- Splits are deterministic
- No overlap between train/val/test periods
- Split config is recorded with model metadata

---

## ML-2 — Build baseline training job
**Goal**  
Train the first v1 model.

**Scope**
- Use XGBoost classifier
- Read dataset snapshot version as input
- Train volatility regime model
- Save training metrics

**Acceptance criteria**
- Training job runs from CLI or worker entrypoint
- Model artifact is persisted
- Metrics are saved and reproducible

---

## ML-3 — Implement model artifact export
**Goal**  
Standardize model persistence and loading.

**Scope**
- Save model artifact plus metadata
- Include:
  - model type
  - feature set version
  - training dataset version
  - training timestamp
  - code version

**Acceptance criteria**
- Artifacts can be reloaded for scoring
- Artifact paths are registered in metadata
- Model version IDs are unique

---

## ML-4 — Implement model registry metadata
**Goal**  
Track model versions and deployment state.

**Scope**
- Populate `models` and `model_deployments`
- Support production and candidate slots

**Acceptance criteria**
- A model can be registered after training
- Production/candidate state can be queried
- Registry records training dataset version

---

## ML-5 — Add model registration API/CLI
**Goal**  
Allow promotion candidates to be recorded operationally.

**Scope**
- Add model registration command or endpoint
- Support candidate assignment

**Acceptance criteria**
- Newly trained models can be marked as candidate
- Registry state updates are persisted
- Invalid transitions are rejected

---

# Epic 4 — Real-Time Alpha Inference Gateway

## SERVE-1 — Implement `/health` and `/models` endpoints
**Goal**  
Expose basic operational state for the inference gateway.

**Scope**
- Add:
  - `GET /health`
  - `GET /models`

**Acceptance criteria**
- Health endpoint returns status of service dependencies
- Models endpoint shows prod/candidate versions

---

## SERVE-2 — Implement feature snapshot contract
**Goal**  
Define the exact Redis payload for online features.

**Scope**
- Create online snapshot schema:
  - symbol
  - as_of_ts
  - features
  - feature_set_version

**Acceptance criteria**
- Snapshot schema is versioned
- Redis payloads validate against schema
- Contract is documented

---

## SERVE-3 — Implement online feature retrieval layer
**Goal**  
Serve scoring from hot feature state.

**Scope**
- Read latest feature snapshot from Redis
- Fallback to latest persisted snapshot if cache miss
- Compute freshness metadata

**Acceptance criteria**
- Features can be fetched by symbol
- Freshness is calculated correctly
- Cache miss fallback works

---

## SERVE-4 — Implement `/score` endpoint
**Goal**  
Serve low-latency scoring for one symbol at one timestamp.

**Scope**
- Request:
  - symbol
  - as_of_ts
  - model_name
  - optional feature overrides
- Response:
  - score
  - predicted class
  - model version
  - feature freshness
  - latency
  - fallback status

**Acceptance criteria**
- Endpoint returns valid prediction response
- Latency is measured and returned
- Invalid requests return clean validation errors

---

## SERVE-5 — Implement model loader for inference
**Goal**  
Load production and candidate artifacts at serving time.

**Scope**
- Support loading XGBoost artifacts
- Cache loaded models in-process for MVP

**Acceptance criteria**
- Model loader resolves correct version from registry
- Model reload is possible after registry update
- Load failures are surfaced cleanly

---

## SERVE-6 — Implement replay driver for market days
**Goal**  
Simulate live scoring on historical data.

**Scope**
- Replay historical daily events in timestamp order
- Update Redis feature state
- Invoke `/score` deterministically

**Acceptance criteria**
- Replay can be run from a script
- Replay results are deterministic for same inputs
- Useful for demo and debugging

---

## SERVE-7 — Add Prometheus instrumentation
**Goal**  
Measure operational serving behavior.

**Scope**
- Track:
  - request count
  - error count
  - latency histogram
  - cache hit rate
  - stale feature rate
  - fallback count

**Acceptance criteria**
- Metrics are exported to Prometheus
- Grafana can visualize the metrics
- Metrics labels are documented

---

## SERVE-8 — Implement shadow scoring
**Goal**  
Score candidate models without affecting production decisions.

**Scope**
- Score candidate model alongside production model
- Log score deltas and metadata
- Do not alter prod response decision

**Acceptance criteria**
- Prod output remains authoritative
- Shadow scores are recorded
- Shadow mode can be enabled/disabled via config

---

## SERVE-9 — Implement canary routing
**Goal**  
Allow small controlled traffic splits to candidate models.

**Scope**
- Read canary percent from deployment config
- Route a configurable percentage of requests to candidate

**Acceptance criteria**
- Canary behavior is deterministic enough for testing
- Routed model version is visible in response metadata
- 0% and 100% edge cases are handled

---

## SERVE-10 — Implement fallback policy
**Goal**  
Make scoring resilient under feature or model failures.

**Scope**
- Handle:
  - stale features
  - missing features
  - model unavailable
  - scoring timeout/latency budget breach
- Fallback options:
  - reject request
  - return baseline model score

**Acceptance criteria**
- Fallback path is explicit in response metadata
- Silent degradation is not allowed
- Each fallback case has integration coverage

---

## SERVE-11 — Build inference latency dashboard page
**Goal**  
Expose serving metrics visually.

**Scope**
- Streamlit/Grafana view for:
  - p50/p95/p99 latency
  - cache hit rate
  - fallback rate
  - stale feature rate
  - prod vs shadow count

**Acceptance criteria**
- Metrics are visible end-to-end
- Dashboard useful for demo and ops review

---

# Epic 5 — Eval and Drift Control Plane

## EVAL-1 — Implement eval run model
**Goal**  
Create the control-plane object for evaluation jobs.

**Scope**
- Persist eval runs with:
  - baseline model
  - candidate model
  - dataset version
  - eval spec version
  - status

**Acceptance criteria**
- Eval runs can be created and queried
- State transitions are persisted cleanly

---

## EVAL-2 — Build offline evaluation runner
**Goal**  
Run candidate vs baseline evaluation on a fixed dataset snapshot.

**Scope**
- Load baseline and candidate models
- Score same dataset version
- Persist outputs and metrics

**Acceptance criteria**
- Both models are evaluated on identical rows
- Eval run can be repeated deterministically
- Eval artifacts are stored

---

## EVAL-3 — Implement headline metrics
**Goal**  
Measure basic model quality.

**Scope**
- Compute:
  - AUC
  - log loss
  - calibration summary
  - rank IC
  - decile/bucket spread

**Acceptance criteria**
- Metrics are persisted to `eval_metrics`
- Metric computation is tested
- Reports show baseline, candidate, delta

---

## EVAL-4 — Implement slice engine
**Goal**  
Measure performance under different regimes.

**Scope**
- Slice by:
  - volatility regime
  - ETF category
  - liquidity bucket

**Acceptance criteria**
- Slice definitions are configurable
- Per-slice metrics are generated
- Missing/undersized slices are handled safely

---

## EVAL-5 — Implement drift engine
**Goal**  
Detect changes in data or score distributions.

**Scope**
- Compute:
  - PSI
  - KS statistic
  - JS divergence
  - null-rate drift
  - score distribution drift

**Acceptance criteria**
- Drift values are persisted
- Threshold breaches create drift alerts
- Alert severity can be configured

---

## EVAL-6 — Implement regression detector
**Goal**  
Identify important underperformance masked by aggregate metrics.

**Scope**
- Compare candidate vs baseline by slice
- Flag material regressions

**Acceptance criteria**
- Regressions are included in eval report
- Critical slices can be marked higher priority

---

## EVAL-7 — Implement promotion gate logic
**Goal**  
Make deployment decisions rules-based and reproducible.

**Scope**
- Use config-driven thresholds for:
  - aggregate improvement
  - max acceptable regression by critical slice
  - drift warning/block thresholds

**Acceptance criteria**
- Promotion decision is deterministic
- Decision includes reasons
- Gate can block despite aggregate improvement

---

## EVAL-8 — Build eval and promotion APIs
**Goal**  
Expose eval workflows through the control plane service.

**Scope**
- Add:
  - `POST /eval-runs`
  - `GET /eval-runs/{id}`
  - `GET /reports/{eval_run_id}`
  - `POST /promotions/check`

**Acceptance criteria**
- Endpoints validate correctly
- Reports and decisions can be queried after run completion

---

## EVAL-9 — Build drift and promotion dashboard pages
**Goal**  
Visualize model quality and deployment readiness.

**Scope**
- Show:
  - headline metrics
  - slice regressions
  - drift alerts
  - promotion decision and reasons

**Acceptance criteria**
- Dashboard makes pass/fail easy to understand
- Can be used in final demo

---

# Epic 6 — End-to-End Flows and Integration

## INT-1 — End-to-end dataset-to-training integration test
**Goal**  
Verify that dataset snapshots can drive model training reproducibly.

**Scope**
- Build dataset
- Train model
- Register model

**Acceptance criteria**
- Flow passes in CI on fixture data
- Produced artifacts are valid

---

## INT-2 — End-to-end training-to-serving integration test
**Goal**  
Verify that a trained model can be served through the inference gateway.

**Scope**
- Register model
- Load model in gateway
- Score with feature snapshot

**Acceptance criteria**
- Serving path works from registered artifact
- Returned model version matches registry

---

## INT-3 — Shadow mode integration test
**Goal**  
Verify prod and candidate models are scored correctly in shadow mode.

**Scope**
- Run serving with prod + candidate
- Assert prod output is returned
- Assert shadow output is logged

**Acceptance criteria**
- Shadow never changes prod decision
- Both outputs are observable

---

## INT-4 — Promotion gate integration test
**Goal**  
Verify the candidate can be blocked on slice regression or drift.

**Scope**
- Run eval
- Generate regression/drift
- Run promotion check

**Acceptance criteria**
- Decision output matches expected gate logic
- Failure reasons are explicit

---

## INT-5 — Full replay integration test
**Goal**  
Exercise the full platform on replayed historical data.

**Scope**
- Replay historical period
- Score live through gateway
- Run eval and gate checks

**Acceptance criteria**
- Scripted demo flow works end-to-end
- Outputs are deterministic enough for demo reuse

---

# Epic 7 — Docs, Runbooks, and Interview Packaging

## DOC-1 — Write architecture overview
**Goal**  
Document the system as one coherent platform.

**Scope**
- Create:
  - system overview
  - dataset platform doc
  - inference gateway doc
  - eval control plane doc

**Acceptance criteria**
- Docs explain service boundaries and shared contracts
- Architecture diagrams are included

---

## DOC-2 — Write ADRs
**Goal**  
Document important design choices.

**Scope**
- Add ADRs for:
  - monorepo decision
  - Parquet + DuckDB
  - Postgres metadata
  - Redis online store
  - canary routing

**Acceptance criteria**
- Each ADR states context, decision, consequences

---

## DOC-3 — Write operational runbooks
**Goal**  
Make the repo look operationally mature.

**Scope**
- Add runbooks for:
  - backfill
  - stale data incident
  - model rollout
  - drift alert triage

**Acceptance criteria**
- Runbooks are concrete and executable
- Incident response paths are clear

---

## DOC-4 — Final README rewrite
**Goal**  
Turn the repo into a portfolio-grade artifact.

**Scope**
- Include:
  - problem statement
  - architecture diagram
  - why market data stresses ML infra
  - quickstart
  - API examples
  - screenshots
  - design tradeoffs
  - future work

**Acceptance criteria**
- README can sell the project without extra explanation
- Local quickstart works from README

---

## DOC-5 — Demo script and screenshots
**Goal**  
Prepare the final showcase flow.

**Scope**
- Script the demo:
  1. ingest data
  2. build dataset
  3. train model
  4. register candidate
  5. replay scoring
  6. compare prod vs candidate
  7. block or approve promotion
- Capture screenshots/GIFs

**Acceptance criteria**
- Demo can be run repeatably
- Screenshots cover:
  - dataset quality
  - inference latency
  - shadow vs prod
  - drift report
  - promotion decision

---

# Suggested execution order

Follow this order to minimize rework:

1. PLAT-1 to PLAT-5
2. LIB-1 to LIB-4
3. DATA-1 to DATA-6
4. DATA-7 to DATA-13
5. ML-1 to ML-5
6. SERVE-1 to SERVE-7
7. SERVE-8 to SERVE-11
8. EVAL-1 to EVAL-9
9. INT-1 to INT-5
10. DOC-1 to DOC-5

---

# MVP exit criteria

The MVP is complete when you can demonstrate this end-to-end flow:

1. Ingest daily ETF data
2. Build a versioned point-in-time-correct dataset snapshot
3. Train a volatility regime model
4. Register prod and candidate models
5. Replay a market period and score live through `/score`
6. Show latency, freshness, and fallback metrics
7. Run offline evaluation for candidate vs baseline
8. Detect drift/regressions by slice
9. Produce a promotion decision with explicit reasons

---

# Stretch backlog

Only do these after MVP is fully working:

- Kafka/Redpanda ingestion
- intraday bars
- event-driven online feature updates
- ONNX runtime benchmarks
- Triton serving
- Kubernetes deployment
- multimodal filings/news features
- automatic canary rollback
- React operator console