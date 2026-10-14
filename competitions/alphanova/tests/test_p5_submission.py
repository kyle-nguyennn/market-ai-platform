"""P5 standalone model must match research regime coefficients and policy."""
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

from competitions.alphanova.research.regime import (  # noqa: E402
    predict_raw, train_from_panels,
)
from competitions.alphanova.research.run_feature_screen import (  # noqa: E402
    validation_prediction,
)
from competitions.alphanova.submissions.disagreement_regime_p5 import (  # noqa: E402
    DisagreementRegimePredictor,
)


def sample(n=1000):
    rng = np.random.default_rng(872)
    tickers = [f"ticker.{i}" for i in range(1, 21)]
    columns = pd.MultiIndex.from_product(
        ([f"Feature.{i}" for i in range(1, 7)], tickers)
    )
    features = pd.DataFrame(rng.normal(size=(n, 120)), columns=columns)
    y = features["Feature.1"] - .7 * features["Feature.6"]
    y += rng.normal(0, .2, (n, 20))
    return features, y.sub(y.mean(axis=1), axis=0)


def test_submittable_predictor_matches_regime_research():
    f, labels = sample()
    train_features, train_labels = f.iloc[:850], labels.iloc[:850]
    research = train_from_panels(
        train_features, train_labels,
        regime="feature1_6_disagreement",
        tail_rows=20000, embargo_rows=168, shrinkage=.5,
    )
    candidate = DisagreementRegimePredictor()
    candidate.train(train_features, train_labels)
    np.testing.assert_allclose(
        [
            candidate.threshold, candidate.beta_low,
            candidate.beta_high, candidate.beta_global,
        ],
        [
            research.threshold, research.beta_low,
            research.beta_high, research.beta_global,
        ],
        atol=1e-12,
    )
    held = f.iloc[850:]
    raw, tickers = predict_raw(held, research)
    expected = validation_prediction(
        raw, 1.0, held.index, tickers, 240, .02, .5,
    )
    actual = candidate.predict(held)
    np.testing.assert_allclose(actual, expected, atol=1e-10)
    np.testing.assert_allclose(actual.mean(axis=1), 0.0, atol=1e-12)
    np.testing.assert_allclose(
        actual.iloc[:50], candidate.predict(held.iloc[:50]), atol=1e-12,
    )
    np.testing.assert_allclose(
        actual,
        pickle.loads(pickle.dumps(candidate)).predict(held),
        atol=1e-12,
    )
    reverse = list(reversed(tickers))
    reordered = held.loc[:, pd.IndexSlice[:, reverse]]
    np.testing.assert_allclose(
        actual[reverse], candidate.predict(reordered)[reverse], atol=1e-12
    )
    assert len(candidate.predict(train_features.iloc[:20])) == 20


def test_missing_data_and_permuted_training_rows():
    f, labels = sample(500)
    shuffled = np.random.default_rng(4).permutation(480)
    model = DisagreementRegimePredictor()
    model.train(f.iloc[shuffled], labels.iloc[shuffled])
    damaged = f.iloc[480:].copy()
    damaged.iloc[0, 0] = np.inf
    damaged.iloc[1, 101] = np.nan
    p = model.predict(damaged)
    assert np.isfinite(p.to_numpy()).all()


def test_submission_ast_single_class():
    src = (
        ROOT / "competitions/alphanova/submissions/disagreement_regime_p5.py"
    ).read_text()
    tree = ast.parse(src)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    assert len(classes) == 1 and classes[0].name == "DisagreementRegimePredictor"
    assert all(
        isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef))
        or isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
        for n in tree.body
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"bfill", "backfill", "roll"}
