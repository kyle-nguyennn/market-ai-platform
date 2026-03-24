"""Shared pytest fixtures."""
from __future__ import annotations

import polars as pl
import pytest


@pytest.fixture
def sample_bars_df() -> pl.DataFrame:
    """A minimal daily OHLCV DataFrame for unit tests."""
    from datetime import date, timedelta

    import numpy as np

    n = 30
    base = date(2023, 1, 2)
    dates = [base + timedelta(days=i) for i in range(n)]
    close = 100.0 * np.cumprod(1 + np.random.normal(0, 0.01, n))

    return pl.DataFrame(
        {
            "date": pl.Series(dates).cast(pl.Date),
            "open":   pl.Series(close * 0.999),
            "high":   pl.Series(close * 1.002),
            "low":    pl.Series(close * 0.997),
            "close":  pl.Series(close),
            "volume": pl.Series(np.random.randint(1_000_000, 10_000_000, n).astype(float)),
        }
    )


@pytest.fixture
def feature_dict() -> dict:
    return {
        "ret_1d": 0.012,
        "vol_20d": 0.18,
        "mom_20d": 0.05,
        "adv_20d": 85_000_000.0,
    }
