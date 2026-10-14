"""Synthetic and official-evaluator parity tests; no shipped data required."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from competitions.alphanova.research.diagnostics import (
    assert_valid_predictions,
    new_history_slice,
    pnl_components,
    sharpe,
)

KIT = Path(__file__).resolve().parents[3] / "external" / "alphanova-2026-cycle4"
sys.path.insert(0, str(KIT))
from evaluation import backtest  # noqa: E402


def test_pnl_matches_official_local_backtest():
    rng = np.random.default_rng(17)
    cols = [f"ticker.{i}" for i in range(1, 21)]
    positions = pd.DataFrame(rng.normal(size=(80, 20)), columns=cols)
    positions = positions.sub(positions.mean(axis=1), axis=0)
    returns = pd.DataFrame(rng.normal(scale=.01, size=(80, 20)),
                           columns=list(reversed(cols)),
                           index=pd.RangeIndex(100, 180))
    p = pnl_components(positions, returns)
    official = backtest(positions, returns)
    np.testing.assert_allclose(p["net"].to_numpy(), official.to_numpy(), atol=1e-12)
    np.testing.assert_allclose(p["net"], p["gross"] - p["cost"], atol=1e-12)
    assert_valid_predictions(positions, returns)


def test_flip_only_changes_gross_pnl_not_cost():
    rng = np.random.default_rng(12)
    cols = ["a", "b", "c"]
    p = pd.DataFrame(rng.normal(size=(12, 3)), columns=cols)
    p = p.sub(p.mean(axis=1), axis=0)
    r = pd.DataFrame(rng.normal(size=(12, 3)), columns=cols)
    normal = pnl_components(p, r)
    inverted = pnl_components(-p, r)
    np.testing.assert_allclose(normal["gross"], -inverted["gross"])
    np.testing.assert_allclose(normal["cost"], inverted["cost"])


def test_de_mean_guard():
    p = pd.DataFrame([[1.0, -1.0], [2.0, -2.0]], columns=["a", "b"])
    r = p.copy()
    assert_valid_predictions(p, r)
    p.iloc[0, 0] = 3
    with pytest.raises(ValueError, match="NOT_DEMEANED"):
        assert_valid_predictions(p, r)


def test_nonoverlapping_cumulative_slice():
    sample = pd.DataFrame({"net": list(range(800))})
    # Previous cumulative panel had 50,000 rows; this one's train split
    # ends at 49,800, so the first 200 validation rows are repeated history.
    novel = new_history_slice(sample, train_rows=49800, previous_period_rows=50000)
    assert len(novel) == 600
    assert novel.iloc[0, 0] == 200
    assert len(new_history_slice(sample, 49800, None)) == 800


def test_sharpe_zero_variance():
    assert sharpe(pd.Series([0.0, 0.0])) == 0.0
