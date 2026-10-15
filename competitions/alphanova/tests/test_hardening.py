"""Submission source audit and synthetic model robustness checks."""
import ast
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "external/alphanova-2026-cycle4"
sys.path.insert(0, str(KIT))

from competitions.alphanova.submissions.turnover_xgb_v1 import TurnoverAwareXGBPredictor  # noqa: E402

CANDIDATE = (
    ROOT / "competitions/alphanova/submissions/turnover_xgb_v1.py"
)


def make_panel(n=88):
    rng = np.random.default_rng(333)
    tickers = [f"ticker.{j}" for j in range(1, 21)]
    cols = pd.MultiIndex.from_product(
        ([f"Feature.{k}" for k in range(1, 7)], tickers)
    )
    features = pd.DataFrame(rng.normal(size=(n, 120)), columns=cols)
    target = features["Feature.1"] - features["Feature.2"]
    return features, target.sub(target.mean(axis=1), axis=0)


def test_single_class_no_module_execution_or_forbidden_operations():
    source = CANDIDATE.read_text()
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    assert len(classes) == 1
    assert any(isinstance(base, ast.Name) and base.id == "Predictor"
               for base in classes[0].bases)
    assert all(isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef))
               or (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))
               for n in tree.body)
    forbidden = {"bfill", "backfill", "roll"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden
            if node.func.attr == "rolling":
                assert not any(
                    k.arg == "center" and isinstance(k.value, ast.Constant)
                    and k.value.value is True
                    for k in node.keywords
                )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "shift" and node.args:
                a = node.args[0]
                assert not (isinstance(a, ast.UnaryOp)
                            and isinstance(a.op, ast.USub))


def test_serialization_causality_permutation_and_overlap():
    features, target = make_panel()
    model = TurnoverAwareXGBPredictor()
    model.n_rounds = 5
    model.train(features.iloc[:60], target.iloc[:60])
    full = model.predict(features)
    prefix = model.predict(features.iloc[:35])
    np.testing.assert_allclose(full.iloc[:35], prefix, atol=1e-9)
    assert np.isfinite(full.to_numpy()).all()
    assert np.max(np.abs(full.mean(axis=1))) < 1e-8
    # Model output must remain valid when inference overlaps training.
    assert len(model.predict(features.iloc[:60])) == 60
    restored = pickle.loads(pickle.dumps(model))
    np.testing.assert_allclose(restored.predict(features), full, atol=1e-9)
    reversed_tickers = list(reversed(target.columns))
    reordered = features.loc[:, pd.IndexSlice[:, reversed_tickers]]
    permuted = model.predict(reordered)
    np.testing.assert_allclose(full[reversed_tickers], permuted[reversed_tickers],
                               atol=1e-8)


def test_unexpected_values_do_not_trigger_data_based_assertions():
    f, y = make_panel(70)
    f.iloc[1:3, 0] = np.nan
    f.iloc[4, 17] = np.inf
    model = TurnoverAwareXGBPredictor()
    model.n_rounds = 4
    perm = np.random.default_rng(4).permutation(len(f))
    model.train(f.iloc[perm], y.iloc[perm])
    pred = model.predict(f.iloc[:18])
    assert pred.shape == (18, 20)
    assert np.isfinite(pred.to_numpy()).all()
