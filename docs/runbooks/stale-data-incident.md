# Runbook: Stale Data Incident

## Symptoms
- Stale-feature rate alert firing in Grafana
- Inference gateway returning `fallback: stale_features` in score responses

## Steps

1. Check ingestion worker logs for last successful run
2. Verify Redis key freshness for affected symbols
3. Manually trigger ingestion: `scripts/backfill_daily.sh <date> <date>`
4. Confirm Redis keys updated and stale-feature rate drops
