"""P3 candidate parity: identical model plus research portfolio controller."""
import ast
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "external/alphanova-2026-cycle4"
sys.path.insert(0, str(KIT))

from demo_engineered import EngineeredXGBoostPredictor  # noqa: E402

from competitions.alphanova.research.positions import position_policy  # noqa: E402
from competitions.alphanova.submissions.candidate_p3 import EngineeredTurnoverPredictor  # noqa: E402


def make_panels(n=88):
    rng = np.random.default_rng(444)
    tickers = [f"ticker.{i}" for i in range(1, 21)]
    columns = pd.MultiIndex.from_product(
        ([f"Feature.{k}" for k in range(1, 7)], tickers)
    )
    features = pd.DataFrame(rng.normal(size=(n, 120)), columns=columns)
    target = features["Feature.1"] - features["Feature.2"]
    target = target.sub(target.mean(axis=1), axis=0)
    return features, target


def test_packaged_candidate_matches_research_policy():
    features, target = make_panels()
    reference = EngineeredXGBoostPredictor()
    candidate = EngineeredTurnoverPredictor()
    reference.n_rounds = 5
    candidate.n_rounds = 5
    reference.span = candidate.span
    reference.train(features.iloc[:62], target.iloc[:62])
    candidate.train(features.iloc[:62], target.iloc[:62])
    held_out = features.iloc[62:]
    expected = position_policy(
        reference.predict(held_out),
        candidate.min_trade_l1,
        candidate.rebalance_fraction,
    )
    observed = candidate.predict(held_out)
    np.testing.assert_allclose(observed.to_numpy(), expected.to_numpy(), atol=1e-7)
    np.testing.assert_allclose(observed.mean(axis=1), 0.0, atol=1e-9)


def test_packaged_candidate_causal_permutation_and_pickle():
    features, target = make_panels()
    candidate = EngineeredTurnoverPredictor()
    candidate.n_rounds = 5
    idx = np.random.default_rng(12).permutation(60)
    candidate.train(features.iloc[idx], target.iloc[idx])
    full = candidate.predict(features)
    prefix = candidate.predict(features.iloc[:40])
    np.testing.assert_allclose(full.iloc[:40], prefix, atol=1e-8)
    assert np.isfinite(full.to_numpy()).all()
    again = pickle.loads(pickle.dumps(candidate)).predict(features)
    np.testing.assert_allclose(full, again, atol=1e-8)
    assert len(candidate.predict(features.iloc[:60])) == 60
    rev = list(reversed(target.columns))
    rearranged = features.loc[:, pd.IndexSlice[:, rev]]
    np.testing.assert_allclose(
        candidate.predict(rearranged)[rev], full[rev], atol=1e-8
    )


def test_packaged_candidate_is_standalone():
    source = (
        ROOT / "competitions/alphanova/submissions/candidate_p3.py"
    ).read_text()
    tree = ast.parse(source)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    assert len(classes) == 1
    assert any(isinstance(n, ast.Name) and n.id == "Predictor"
               for n in classes[0].bases)
    assert all(
        isinstance(n, (ast.Import, ast.ImportFrom, ast.ClassDef)) or (
            isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
        )
        for n in tree.body
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"bfill", "backfill", "roll"}
            if node.func.attr == "shift":
                for arg in node.args:
                    assert not (
                        isinstance(arg, ast.UnaryOp) and
                        isinstance(arg.op, ast.USub)
                    )
