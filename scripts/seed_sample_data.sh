#!/usr/bin/env bash
# seed_sample_data.sh — write a small sample dataset to data/sample/ for local dev
set -euo pipefail

echo "==> Generating sample data..."
mamba run -n market-ai python - <<'EOF'
import polars as pl
import numpy as np
from datetime import date, timedelta

n = 252  # ~1 year of daily bars
base = date(2023, 1, 2)
dates = [base + timedelta(days=i) for i in range(n)]
close = 100.0 * np.cumprod(1 + np.random.normal(0, 0.01, n))

df = pl.DataFrame({
    "date":   pl.Series(dates).cast(pl.Date),
    "ticker": ["SPY"] * n,
    "open":   pl.Series(close * 0.999),
    "high":   pl.Series(close * 1.002),
    "low":    pl.Series(close * 0.997),
    "close":  pl.Series(close),
    "volume": pl.Series(np.random.randint(50_000_000, 150_000_000, n).astype(float)),
})

import os
os.makedirs("data/sample", exist_ok=True)
df.write_parquet("data/sample/daily_bars.parquet")
print(f"Written {len(df)} rows to data/sample/daily_bars.parquet")
EOF

echo "==> Sample data seeded."
