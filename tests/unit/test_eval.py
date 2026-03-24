"""Unit tests for libs/eval components."""
from __future__ import annotations

import polars as pl  # noqa: F401  # TODO: use for DataFrame-based eval assertions

from libs.contracts.eval_spec import DriftConfig  # noqa: F401  # TODO: add drift config tests
from libs.eval.metrics import accuracy, precision_recall_f1
from libs.eval.regressions import check_regression_guards


def test_accuracy_perfect():
    assert accuracy([0, 1, 1, 0], [0, 1, 1, 0]) == 1.0


def test_accuracy_half():
    assert accuracy([0, 1, 0, 1], [1, 0, 1, 0]) == 0.0


def test_precision_recall_f1():
    p, r, f1 = precision_recall_f1([1, 1, 0, 0], [1, 0, 0, 0])
    assert p == 1.0
    assert r == 0.5
    assert abs(f1 - 2 / 3) < 1e-6


def test_regression_guards_pass():
    result = check_regression_guards(
        metrics={"roc_auc": 0.70, "f1": 0.55},
        guards={"roc_auc": 0.60, "f1": 0.50},
    )
    assert result.passed
    assert not result.violations


def test_regression_guards_fail():
    result = check_regression_guards(
        metrics={"roc_auc": 0.55},
        guards={"roc_auc": 0.60},
    )
    assert not result.passed
    assert "roc_auc" in result.violations
