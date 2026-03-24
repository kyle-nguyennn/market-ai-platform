# Runbook: Backfill

## Purpose
Backfill historical bar data for the configured ETF universe.

## Steps

1. Ensure Docker stack is running: `make up`
2. Run: `scripts/backfill_daily.sh <start_date> <end_date>`
3. Verify quality reports in the dataset-platform service
4. Check for null/staleness failures in Grafana
