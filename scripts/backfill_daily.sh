#!/usr/bin/env bash
# backfill_daily.sh — backfill daily OHLCV bars for a date range
# Usage: ./scripts/backfill_daily.sh --start 2020-01-01 --end 2023-12-31
set -euo pipefail

START=${1:-"2020-01-01"}
END=${2:-$(date +%Y-%m-%d)}

echo "==> Backfilling daily bars from $START to $END..."
mamba run -n market-ai python -m services.ingestion_worker.main \
  --start "$START" \
  --end   "$END"   \
  --universe SPY QQQ IWM GLD TLT EFA EEM XLF XLE XLV XLK XLI XLP XLU

echo "==> Backfill complete."
