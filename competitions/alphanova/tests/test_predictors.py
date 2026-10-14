"""Contract tests for standalone P1 candidates on synthetic panels."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

KIT = Path(__file__).resolve().parents[3] / "external" / "alphanova-2026-cycle4"
sys.path.insert(0, str(KIT))
from competitions.alphanova.submissions.ridge_v1 import RidgeCrossSectionalPredictor  # noqa: E402
from competitions.alphanova.submissions.xgb_interactions_v1 import XGBInteractionPredictor  # noqa: E402


def make_panel(n_rows=80):
    rng = np.random.default_rng(23)
    tickers = [f"ticker.{i}" for i in range(1, 21)]
    cols = pd.MultiIndex.from_product(
        ([f"Feature.{i}" for i in range(1, 7)], tickers)
    )
    f = pd.DataFrame(rng.standard_normal((n_rows, len(cols))), columns=cols)
    y = (f["Feature.1"] - f["Feature.2"]).copy()
    y = y.sub(y.mean(axis=1), axis=0)
    return f, y


@pytest.mark.parametrize("predictor_cls", [
    RidgeCrossSectionalPredictor,
    XGBInteractionPredictor,
])
def test_submittable_prediction_contract(predictor_cls):
    features, target = make_panel()
    model = predictor_cls()
    model.train(features.iloc[:60], target.iloc[:60])
    p = model.predict(features.iloc[60:])
    assert p.shape == (20, 20)
    assert set(p.columns) == set(target.columns)
    assert np.isfinite(p.to_numpy()).all()
    assert np.max(np.abs(p.mean(axis=1))) < 1e-7
    # Inference is allowed to overlap training data.
    overlap = model.predict(features.iloc[40:70])
    assert len(overlap) == 30
    # Ticker permutations must not change a cross-sectional predictor.
    reversed_tickers = list(reversed(target.columns))
    permuted = features.iloc[60:].loc[
        :, pd.IndexSlice[:, reversed_tickers]
    ]
    p2 = model.predict(permuted)
    np.testing.assert_allclose(p[reversed_tickers], p2[reversed_tickers], atol=1e-6)


@pytest.mark.parametrize("predictor_cls", [
    RidgeCrossSectionalPredictor,
    XGBInteractionPredictor,
])
def test_retrain_after_row_permutation_does_not_crash(predictor_cls):
    f, y = make_panel(60)
    perm = np.random.default_rng(7).permutation(len(f))
    model = predictor_cls()
    model.train(f.iloc[perm], y.iloc[perm])
    out = model.predict(f.iloc[:8])
    assert np.isfinite(out.to_numpy()).all()
    assert np.max(np.abs(out.mean(axis=1))) < 1e-7
