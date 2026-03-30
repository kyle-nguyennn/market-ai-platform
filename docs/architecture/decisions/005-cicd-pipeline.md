# ADR 005 — CI/CD Pipeline: Per-Service Build, EKS Deploy, Rollback

**Status:** Accepted

**Context:** The original `ci.yml` ran lint, test, and a single `docker compose build` for all services together on every push and pull request. As the platform grows to three independently deployable HTTP services (`dataset-platform`, `inference-gateway`, `eval-control-plane`)—with additional worker services (`ingestion_worker`, `training_worker`) that have distinct deployment patterns—this creates problems:

- A change to `services/dataset_platform/` triggers unnecessary rebuilds of the other two services.
- There is no automated path from a merged commit to a running preprod environment.
- There is no rollback mechanism when a bad deploy reaches preprod.

**Decision:** Split the monolithic `ci.yml` into focused workflows and add Kubernetes manifests for EKS. The build pipeline is **implemented** (PR #19); the deploy, rollback, and K8s manifests are **planned**.

**Consequences:**

- CI runs faster and more efficiently — changed services build independently, unchanged services are never rebuilt on unrelated commits.
- There will be an automated path from merged commits to a running preprod environment on EKS (planned).
- Rollbacks will become first-class operations via automated rollback on failed rollouts and a dedicated manual rollback workflow (planned).
- Operational complexity increases slightly due to multiple workflows and Kubernetes manifests that must be maintained.
- The `{sha}` image tag creates a direct link between a Git commit and a running container for auditability.

---

## Implemented: Build Pipeline (PR #19)

The monolithic `ci.yml` was deleted and replaced with a sequential chain of focused workflows:

**Workflow chain:** `lint.yml` → `test.yml` → `build-{service}.yml` × 3 (main only)

### `lint.yml` (entry point — on push/PR)

- Triggers on `push` to `main` and `pull_request`; pipeline entry point.
- Runs `ruff check` in the `market-ai` micromamba environment.
- `concurrency: cancel-in-progress` prevents stale runs.

### `test.yml` (runs after Lint succeeds)

- Triggers via `workflow_run` on `Lint` completion; only runs if Lint succeeded.
- Runs `pytest -n auto` (parallelism via `pytest-xdist`) with coverage (`pytest-cov`).
- Uploads JUnit XML, coverage XML, and HTML artifacts with `if: always()` so artifacts are preserved on test failure.
- CI-only test extras (`pytest-xdist`, `pytest-cov`) are declared in `pyproject.toml [project.optional-dependencies] test` and installed with `pip install -e ".[test]"`.

### `_build-service.yml` (reusable template)

- `workflow_call` template shared by all three service build workflows.
- `dorny/paths-filter@v3` detects whether watched files changed; skips build when nothing relevant changed.
- Accepts `service-name`, `dockerfile`, `watch-paths`, and `force-build` inputs.
- Pushes to Docker Hub when `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets are set; otherwise builds locally only.
- Tags: `quantpiece/{service-name}:{sha}` (immutable, for deploy and audit trail) and `quantpiece/{service-name}:latest` (floating).
- Layer caching via GitHub Actions cache (`type=gha`).

### `build-{service}.yml` × 3 (per-service callers)

`build-dataset-platform.yml`, `build-eval-control-plane.yml`, `build-inference-gateway.yml`:

- Trigger via `workflow_run` on `Test` completion, scoped to `main` branch only.
- `workflow_dispatch` available for on-demand builds (bypasses path filter, always builds).
- Each watches: `environment.yml`, `pyproject.toml`, `libs/**`, `services/{service}/**`, `infra/docker/{service}.Dockerfile`.

---

## Planned: Deploy and Rollback

### `deploy-preprod.yml` (planned — deploy to AWS EKS preprod)

- Triggered automatically via `workflow_run` on completion of any `build-{service}.yml`.
- Also triggerable manually via `workflow_dispatch` with a `service` input for targeted re-deploys.
- Per-service steps:
  1. Configure AWS credentials and update kubeconfig for the EKS cluster.
  2. `kubectl set image` with the immutable `{sha}` tag.
  3. `kubectl rollout status --timeout=5m` to confirm successful rollout.
  4. **Auto-rollback** (`if: failure()`): `kubectl rollout undo deployment/{service}`.
  5. Post-rollout health check executed **from within the cluster** (for example, `kubectl run rollout-healthcheck --rm -i --restart=Never --image=curlimages/curl -- curl -f http://{service}-svc/health`). If instead you want to `curl` from the GitHub Actions runner, you must either use a self-hosted runner with VPC access to the cluster or expose the service via an Ingress/LoadBalancer and curl that external URL.

### `rollback.yml` (planned — manual rollback via `workflow_dispatch`)

- Inputs: `service` (choice of `dataset-platform`, `inference-gateway`, `eval-control-plane`, or `all`) and optional `revision` (K8s revision number; defaults to the previous revision for each deployment).
- For a single `service`, runs `kubectl rollout undo deployment/{service}` (optionally with `--to-revision={n}`); for `service = all`, iterates over the known deployments and runs the same command for each service, applying `--to-revision={n}` (or the default previous revision) independently per deployment.
- Confirms success with `kubectl rollout status` for each affected deployment and prints the active image tag(s) post-rollback.

### `infra/k8s/preprod/` (planned — Kubernetes manifests)

One `Deployment` + `Service` YAML per service:

| File | Service | Port |
|------|---------|------|
| `dataset-platform.yaml` | dataset-platform | 8001 |
| `inference-gateway.yaml` | inference-gateway | 8002 |
| `eval-control-plane.yaml` | eval-control-plane | 8003 |

Common manifest properties:
- `replicas: 2` for preprod availability.
- `strategy: RollingUpdate` (maxUnavailable: 1, maxSurge: 1).
- Liveness + readiness probes on `/health`.
- Image field defaults to `quantpiece/{service}:latest`; deploy workflow overrides with the sha tag.
- Namespace: `market-ai-preprod`.

---

## Worker Services (`ingestion_worker`, `training_worker`)

Workers are not long-running HTTP services and have distinct build and deployment patterns from the three main services above.

**Build:** Workers can use the same `_build-service.yml` reusable template. Add thin caller files `build-ingestion-worker.yml` and `build-training-worker.yml` following the same pattern as the service callers, watching `services/ingestion_worker/**` and `services/training_worker/**` respectively.

**Deploy:** Workers should not use Kubernetes `Deployment` + `Service` manifests. Recommended patterns:
- **`ingestion_worker`** (event-driven or continuous): Deploy as a Kubernetes `Deployment` if it runs continuously polling a queue, or as a `Job`/`CronJob` for scheduled ingestion runs. KEDA can be used to auto-scale based on queue depth.
- **`training_worker`** (on-demand, long-running compute): Deploy as a Kubernetes `Job` (single run triggered by pipeline events or `workflow_dispatch`) or `CronJob` (scheduled). For GPU workloads, consider a dedicated node pool with appropriate taints/tolerations or AWS Batch.

A dedicated `deploy-workers.yml` workflow (or an extension of `deploy-preprod.yml`) with `kubectl apply -f` / `kubectl create job` commands can cover both patterns.

---

## Required GitHub Secrets

| Secret | Used by |
|--------|---------|
| `DOCKERHUB_USERNAME` | `_build-service.yml` |
| `DOCKERHUB_TOKEN` | `_build-service.yml` |
| `AWS_ACCESS_KEY_ID` | `deploy-preprod.yml`, `rollback.yml` (planned) |
| `AWS_SECRET_ACCESS_KEY` | `deploy-preprod.yml`, `rollback.yml` (planned) |
| `AWS_REGION` | `deploy-preprod.yml`, `rollback.yml` (planned) |
| `EKS_CLUSTER_NAME` | `deploy-preprod.yml`, `rollback.yml` (planned) |

---

## Alternatives Considered

- **Single monolithic build job for all services:** Simpler to maintain but wastes CI minutes and couples unrelated services.
- **Helm instead of raw kubectl manifests:** Adds templating and multi-environment promotion support, but introduces tooling overhead not yet justified at this stage.
- **OIDC instead of static AWS keys:** More secure (no long-lived credentials stored as secrets). Rejected only for initial setup simplicity; recommended as a follow-up migration.