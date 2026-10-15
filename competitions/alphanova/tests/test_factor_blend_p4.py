"""Standalone ensemble parity, causality and ticker-equivariance tests."""
from __future__ import annotations

import ast
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "external" / "alphanova-2026-cycle4"
sys.path.insert(0, str(KIT))

from competitions.alphanova.research.feature_screen import (  # noqa: E402
    factor_values,
    feature_panels,
    train_linear_slope,
)
from competitions.alphanova.research.run_feature_screen import (  # noqa: E402
    validation_prediction,
)
from competitions.alphanova.submissions.factor_blend_p4 import (  # noqa: E402
    FactorBlendPredictor,
)


def data(n=305):
    rng = np.random.default_rng(813)
    tickers = [f"ticker.{i}" for i in range(1, 21)]
    cols = pd.MultiIndex.from_product(
        ([f"Feature.{i}" for i in range(1, 7)], tickers)
    )
    x = pd.DataFrame(rng.normal(size=(n, 120)), columns=cols)
    y = x["Feature.1"] + 0.2 * x["Feature.3"] - 0.3 * x["Feature.6"]
    return x, y.sub(y.mean(axis=1), axis=0)


def test_blend_exact_research_parity_and_causality():
    features, labels = data()
    train_features, train_target = features.iloc[:240], labels.iloc[:240]
    candidate = FactorBlendPredictor()
    candidate.train(train_features, train_target)
    raw, tickers = feature_panels(train_features)
    y = train_target.reindex(columns=tickers).to_numpy(dtype=float)
    expected_a = train_linear_slope(factor_values("rank_1", raw), y, 72)
    expected_b = train_linear_slope(factor_values("diff_3_6", raw), y, 72)
    np.testing.assert_allclose(
        [candidate.beta_rank1, candidate.beta_diff36],
        [expected_a, expected_b],
        atol=1e-12,
    )
    validation = features.iloc[240:]
    raw_val, names = feature_panels(validation)
    blend = 0.5 * (
        candidate.beta_rank1 * factor_values("rank_1", raw_val)
        + candidate.beta_diff36 * factor_values("diff_3_6", raw_val)
    )
    expected = validation_prediction(
        blend, 1.0, validation.index, names, 240, 0.02, 0.5
    )
    actual = candidate.predict(validation)
    np.testing.assert_allclose(actual, expected, atol=1e-12)
    np.testing.assert_allclose(actual.iloc[:22], candidate.predict(validation.iloc[:22]))
    np.testing.assert_allclose(actual.mean(axis=1), 0.0, atol=1e-12)
    np.testing.assert_allclose(
        actual, pickle.loads(pickle.dumps(candidate)).predict(validation),
    )

    reversed_tickers = list(reversed(tickers))
    permuted = validation.loc[:, pd.IndexSlice[:, reversed_tickers]]
    np.testing.assert_allclose(
        actual[reversed_tickers],
        candidate.predict(permuted)[reversed_tickers],
        atol=1e-12,
    )


def test_blend_submission_structure():
    source = (ROOT / "competitions/alphanova/submissions/factor_blend_p4.py").read_text()
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    assert len(classes) == 1 and classes[0].name == "FactorBlendPredictor"
    assert all(
        isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef)) or (
            isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
        )
        for n in tree.body
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"bfill", "backfill", "roll"}
