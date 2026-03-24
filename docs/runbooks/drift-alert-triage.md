# Runbook: Drift Alert Triage

## Symptoms
- Drift alert in Grafana or eval-control-plane dashboard
- `drift_alerts` table has new unresolved rows

## Steps

1. Identify affected model version and drift type (feature/score/label)
2. Run full eval: `POST /eval-runs` with affected candidate
3. Inspect slice breakdown for regime/liquidity segment regressions
4. If drift is material, block promotion via gate config
5. Escalate to model team if root cause is data distribution shift
