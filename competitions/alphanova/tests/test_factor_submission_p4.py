"""P4 standalone predictors must match the prespecified research harness."""
from __future__ import annotations

import ast
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

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
from competitions.alphanova.submissions.factor_diff36_p4 import (  # noqa: E402
    Feature36DiffPredictor,
)
from competitions.alphanova.submissions.factor_rank1_p4 import (  # noqa: E402
    Feature1RankPredictor,
)


def panel(n=300):
    rng = np.random.default_rng(2026)
    tickers = [f"ticker.{k}" for k in range(1, 21)]
    columns = pd.MultiIndex.from_product(
        ([f"Feature.{i}" for i in range(1, 7)], tickers)
    )
    features = pd.DataFrame(rng.normal(size=(n, 120)), columns=columns)
    labels = (features["Feature.1"] - features["Feature.5"]).copy()
    labels = labels.sub(labels.mean(axis=1), axis=0)
    return features, labels


@pytest.mark.parametrize("model_cls,name,file_name", [
    (Feature1RankPredictor, "rank_1", "factor_rank1_p4.py"),
    (Feature36DiffPredictor, "diff_3_6", "factor_diff36_p4.py"),
])
def test_model_matches_research_and_is_causal(model_cls, name, file_name):
    features, labels = panel()
    train = features.iloc[:240]
    y = labels.iloc[:240]
    valid = features.iloc[240:]
    raw, tickers = feature_panels(train)
    slope = train_linear_slope(
        factor_values(name, raw),
        y.reindex(columns=tickers).to_numpy(dtype=float),
        240 - 168, 20_000,
    )
    valid_raw, val_tickers = feature_panels(valid)
    model = model_cls()
    model.train(train, y)
    assert model.beta == pytest.approx(slope, abs=1e-12)
    expected = validation_prediction(
        factor_values(name, valid_raw), slope, valid.index,
        val_tickers, 240, 0.02, 0.5,
    )
    actual = model.predict(valid)
    np.testing.assert_allclose(actual.to_numpy(), expected.to_numpy(), atol=1e-10)
    np.testing.assert_allclose(actual.mean(axis=1), 0.0, atol=1e-12)
    np.testing.assert_allclose(
        actual.iloc[:35].to_numpy(),
        model.predict(valid.iloc[:35]).to_numpy(),
        atol=1e-12,
    )
    restored = pickle.loads(pickle.dumps(model))
    np.testing.assert_allclose(restored.predict(valid), actual, atol=1e-12)
    assert len(model.predict(train.iloc[170:])) == 70

    # Permuting labels and their corresponding feature columns must
    # permute output labels, not prediction semantics.
    reversed_tickers = list(reversed(tickers))
    permuted = valid.loc[:, pd.IndexSlice[:, reversed_tickers]]
    out = model.predict(permuted)
    np.testing.assert_allclose(
        out[reversed_tickers], actual[reversed_tickers], atol=1e-12
    )

    src = (ROOT / "competitions/alphanova/submissions" / file_name).read_text()
    parsed = ast.parse(src)
    classes = [n for n in parsed.body if isinstance(n, ast.ClassDef)]
    assert len(classes) == 1
    assert classes[0].name == model_cls.__name__
    assert all(
        isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef)) or (
            isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
        )
        for n in parsed.body
    )
    for node in ast.walk(parsed):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"bfill", "backfill", "roll"}


@pytest.mark.parametrize("model_cls", [Feature1RankPredictor, Feature36DiffPredictor])
def test_embargo_and_missing_values(model_cls):
    features, labels = panel(280)
    model = model_cls()
    model.train(features.iloc[:240], labels.iloc[:240])
    beta = model.beta
    changed = labels.copy()
    changed.iloc[72:240] *= 1000
    model.train(features.iloc[:240], changed.iloc[:240])
    assert model.beta == pytest.approx(beta)
    damaged = features.iloc[240:].copy()
    damaged.iloc[3, 0] = np.inf
    damaged.iloc[9, 40] = np.nan
    predictions = model.predict(damaged)
    assert np.isfinite(predictions.to_numpy(dtype=float)).all()
