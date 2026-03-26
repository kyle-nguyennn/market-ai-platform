# ADR 005 — CI/CD Pipeline: Per-Service Build, EKS Deploy, Rollback

**Status:** Proposed

**Context:** The current `ci.yml` runs lint, test, and a single `docker compose build` for all services together on every push and pull request. As the platform grows to three independently deployable services, this creates problems:

- A change to `services/dataset_platform/` triggers unnecessary rebuilds of the other two services.
- There is no automated path from a merged commit to a running preprod environment.
- There is no rollback mechanism when a bad deploy reaches preprod.

**Decision:** Split the monolithic `ci.yml` into four focused workflows and add Kubernetes manifests for EKS.

**Consequences:**

- CI runs faster and more efficiently by avoiding unnecessary image builds for unaffected services.
- There is an automated path from merged commits to a running preprod environment on EKS.
- Rollbacks become first-class operations via automated rollback on failed rollouts and a dedicated manual rollback workflow.
- Operational complexity increases slightly due to multiple workflows and Kubernetes manifests that must be maintained.

### 1. `ci.yml` (updated — lint + test on PRs)

Remove the `build` job. Add a lightweight `docker compose build` smoke-check scoped to pull requests only, so PR feedback remains fast without triggering pushes to the registry.

### 2. `build-push.yml` (new — per-service image build on merge to `main`)

- Uses `dorny/paths-filter` to detect which services changed.
- `libs/**`, `environment.yml`, `pyproject.toml` changes trigger all three services (shared dependencies).
- Service-specific paths (`services/dataset_platform/**`, etc.) trigger only the affected service.
- Three parallel build jobs, each gated on the change-detection output.
- Images pushed to **Docker Hub** with two tags:
  - `{user}/{service}:sha-{git-sha}` — immutable, used for deploy and audit trail.
  - `{user}/{service}:preprod` — floating, convenient for manual pulls.
- Layer caching via GitHub Actions cache (`type=gha`).

### 3. `deploy-preprod.yml` (new — deploy to AWS EKS preprod)

- Triggered automatically via `workflow_run` on completion of `build-push.yml`.
- Also triggerable manually via `workflow_dispatch` with a `service` input for targeted re-deploys.
- Per-service steps:
  1. Configure AWS credentials and update kubeconfig for the EKS cluster.
  2. `kubectl set image` with the immutable `sha-{sha}` tag.
  3. `kubectl rollout status --timeout=5m` to confirm successful rollout.
  4. **Auto-rollback** (`if: failure()`): `kubectl rollout undo deployment/{service}`.
  5. Post-rollout health check executed **from within the cluster** (for example, `kubectl run rollout-healthcheck --rm -i --restart=Never --image=curlimages/curl -- curl -f http://{service}-svc/health`). If instead you want to `curl` from the GitHub Actions runner, you must either use a self-hosted runner with VPC access to the cluster or expose the service via an Ingress/LoadBalancer and curl that external URL.

### 4. `rollback.yml` (new — manual rollback via `workflow_dispatch`)

- Inputs: `service` (choice of individual service or `all`) and optional `revision` (K8s revision number; defaults to previous revision).
- Runs `kubectl rollout undo deployment/{service}` (or `--to-revision={n}`).
- Confirms success with `kubectl rollout status` and prints the active image tag post-rollback.

### 5. `infra/k8s/preprod/` (new — Kubernetes manifests)

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
- Image field defaults to `{user}/{service}:preprod`; deploy workflow overrides with the sha tag.
- Namespace: `market-ai-preprod`.

---

## Required GitHub Secrets

| Secret | Used by |
|--------|---------|
| `DOCKERHUB_USERNAME` | `build-push.yml` |
| `DOCKERHUB_TOKEN` | `build-push.yml` |
| `AWS_ACCESS_KEY_ID` | `deploy-preprod.yml`, `rollback.yml` |
| `AWS_SECRET_ACCESS_KEY` | `deploy-preprod.yml`, `rollback.yml` |
| `AWS_REGION` | `deploy-preprod.yml`, `rollback.yml` |
| `EKS_CLUSTER_NAME` | `deploy-preprod.yml`, `rollback.yml` |

---

## Consequences

- Changed services build and deploy independently — unchanged services are never rebuilt on unrelated commits.
- Every merge to `main` that changes service code automatically deploys to preprod within the same pipeline run.
- Failed rollouts self-recover; human intervention is only needed when the auto-rollback itself fails.
- The `sha-{sha}` image tag creates a direct link between a Git commit and a running container for auditability.

---

## Alternatives Considered

- **Single monolithic build job for all services:** Simpler to maintain but wastes CI minutes and couples unrelated services.
- **Helm instead of raw kubectl manifests:** Adds templating and multi-environment promotion support, but introduces tooling overhead not yet justified at this stage.
- **OIDC instead of static AWS keys:** More secure (no long-lived credentials stored as secrets). Rejected only for initial setup simplicity; recommended as a follow-up migration.