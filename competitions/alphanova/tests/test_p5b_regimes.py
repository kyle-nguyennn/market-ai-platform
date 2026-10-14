"""P5-B causal regime and training-only cutoff invariants."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from competitions.alphanova.research.feature_screen import feature_panels
from competitions.alphanova.research.regime import (
    REGIMES, conditional_factor, fit_regime, predict_raw,
    regime_score, train_from_panels,
)


def panels(n=480):
    rng = np.random.default_rng(90)
    tickers = [f"ticker.{i}" for i in range(1, 21)]
    cols = pd.MultiIndex.from_product(
        ([f"Feature.{i}" for i in range(1, 7)], tickers)
    )
    features = pd.DataFrame(rng.standard_normal((n, 120)), columns=cols)
    labels = features["Feature.1"] + rng.normal(0, .2, (n, 20))
    return features, labels.sub(labels.mean(axis=1), axis=0)


@pytest.mark.parametrize("regime", REGIMES)
def test_fitted_parameters_ignore_embargo_labels(regime):
    features, labels = panels()
    base = train_from_panels(
        features.iloc[:420], labels.iloc[:420], regime=regime,
        tail_rows=300, embargo_rows=24,
    )
    changed = labels.copy()
    changed.iloc[396:420] *= -1000
    again = train_from_panels(
        features.iloc[:420], changed.iloc[:420], regime=regime,
        tail_rows=300, embargo_rows=24,
    )
    assert again == base
    out, tickers = predict_raw(features.iloc[420:], base)
    assert out.shape == (60, 20)
    assert len(tickers) == 20
    assert np.isfinite(out).all()
    np.testing.assert_allclose(
        predict_raw(features.iloc[420:440], base)[0], out[:20]
    )


def test_planted_regime_has_distinct_coefficients():
    rng = np.random.default_rng(31)
    f = rng.standard_normal((1000, 20))
    scores = np.linspace(-1, 1, 1000)
    y = f * np.where(scores[:, None] > 0, .4, -.25)
    m = fit_regime(
        f, y, scores, "feature1_dispersion", shrinkage=1., min_rows=10
    )
    assert m.beta_high == pytest.approx(.4, abs=.02)
    assert m.beta_low == pytest.approx(-.25, abs=.02)
    np.testing.assert_allclose(conditional_factor(f, scores, m), y, atol=.02)


def test_regime_scores_are_ticker_invariant():
    features, _ = panels(25)
    raw, tickers = feature_panels(features)
    perm, _ = feature_panels(
        features.loc[:, pd.IndexSlice[:, tickers[::-1]]]
    )
    for name in REGIMES:
        np.testing.assert_allclose(regime_score(name, raw), regime_score(name, perm))
