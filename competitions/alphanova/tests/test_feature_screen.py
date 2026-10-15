"""P4: cross-sectional invariants and training-label cutoff."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from competitions.alphanova.research.feature_screen import (
    cross_rank,
    cross_sectional_ic,
    factor_names,
    factor_values,
    feature_panels,
    train_linear_slope,
)
from competitions.alphanova.research.run_feature_screen import (
    validate_config,
    validation_prediction,
)


def panel(seed=7, n=70):
    rng = np.random.default_rng(seed)
    tickers = [f"ticker.{i}" for i in range(1, 21)]
    columns = pd.MultiIndex.from_product(
        ([f"Feature.{j}" for j in range(1, 7)], tickers)
    )
    x = pd.DataFrame(rng.normal(size=(n, 120)), columns=columns)
    return x


def test_all_48_factors_centered_finite_and_causal():
    x = panel()
    x.iloc[3, 0] = np.nan
    x.iloc[4, 20] = np.inf
    raw, _ = feature_panels(x)
    names = factor_names()
    assert len(names) == 48
    for name in names:
        f = factor_values(name, raw)
        assert f.shape == (70, 20)
        assert np.isfinite(f).all(), name
        np.testing.assert_allclose(f.mean(axis=1), 0.0, atol=1e-10)
        assert np.max(np.abs(f)) < 10

    earlier, _ = feature_panels(x.iloc[:41])
    for name in names:
        np.testing.assert_allclose(
            factor_values(name, earlier),
            factor_values(name, raw)[:41],
            atol=1e-12,
            err_msg=name,
        )


def test_cross_rank_identity_and_constant_rows():
    x = np.tile(np.arange(20, dtype=float), (5, 1))
    x[1] = 42
    x[2, :2] = np.nan
    rank = cross_rank(x)
    assert rank.shape == x.shape
    np.testing.assert_allclose(rank.mean(axis=1), 0.0, atol=1e-12)
    np.testing.assert_allclose(rank[1], 0.0)
    assert np.isfinite(rank).all()


def test_ticker_permutation_and_groupwise_feature_alignment():
    x = panel()
    raw, tickers = feature_panels(x)
    inv = list(reversed(tickers))
    reordered = x.loc[:, pd.IndexSlice[:, inv]]
    shuffled_raw, new_tickers = feature_panels(reordered)
    assert new_tickers == inv
    for name in factor_names():
        a = factor_values(name, raw)
        b = factor_values(name, shuffled_raw)
        np.testing.assert_allclose(a[:, ::-1], b, atol=1e-12)


def test_training_labels_after_cutoff_do_not_affect_fitted_slope():
    x = cross_rank(np.random.default_rng(3).normal(size=(90, 20)))
    y = 0.1 * x
    slope = train_linear_slope(x, y, train_end=50, tail_rows=35)
    changed = y.copy()
    changed[50:] *= -1000
    assert slope == pytest.approx(0.1, abs=1e-10)
    assert train_linear_slope(x, changed, 50, 35) == pytest.approx(slope)


def test_cross_sectional_ic_planted_and_undefined():
    rng = np.random.default_rng(2)
    x = cross_rank(rng.normal(size=(17, 20)))
    np.testing.assert_allclose(cross_sectional_ic(x, 5 * x), 1.0, atol=1e-12)
    assert np.isnan(cross_sectional_ic(x, np.zeros_like(x))).all()


def test_policy_prefix_invariance_and_shapes():
    rng = np.random.default_rng(99)
    x = cross_rank(rng.normal(size=(100, 20)))
    tickers = [f"ticker.{i}" for i in range(1, 21)]
    full = validation_prediction(x, 0.05, pd.RangeIndex(100), tickers, 240, 0.02, 0.5)
    part = validation_prediction(
        x[:33], 0.05, pd.RangeIndex(33), tickers, 240, 0.02, 0.5
    )
    np.testing.assert_allclose(full.iloc[:33], part, atol=1e-12)
    np.testing.assert_allclose(full.mean(axis=1), 0.0, atol=1e-12)


def test_selection_periods_are_separated():
    config = {
        "discovery_periods": ["001", "004"],
        "confirmation_periods": ["022", "031"],
        "top_k": 6,
    }
    validate_config(config)
    with pytest.raises(ValueError):
        validate_config({
            **config, "discovery_periods": ["001", "024"],
        })
    with pytest.raises(ValueError):
        validate_config({
            **config, "confirmation_periods": ["020", "020"],
        })
