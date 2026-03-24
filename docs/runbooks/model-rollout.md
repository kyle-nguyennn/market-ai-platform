# Runbook: Model Rollout

## Purpose
Roll out a new model version to production.

## Steps

1. Ensure candidate model is registered in the model registry
2. Run eval: `POST /eval-runs` against candidate vs current prod
3. Review promotion gate output: `POST /promotions/check`
4. If gate passes, set canary: `POST /models/canary` with desired percentage
5. Monitor shadow/canary metrics in Grafana for at least one trading day
6. Promote: `POST /models/promote`

## Rollback

Set production model back to previous version via `POST /models/promote` with previous model ID.
