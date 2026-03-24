"""Feature and prediction drift detection: PSI and KS tests."""
from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl

from libs.contracts.eval_spec import DriftConfig
from libs.quality.distribution_checks import check_distribution


@dataclass
class DriftReport:
    passed: bool
    feature_drift: dict[str, dict] = field(default_factory=dict)  # feature -> {psi, ks, passed}
    score_drift: dict | None = None


def detect_drift(
    reference: pl.DataFrame,
    current: pl.DataFrame,
    feature_cols: list[str],
    score_col: str | None = None,
    config: DriftConfig | None = None,
) -> DriftReport:
    """Compare *current* distributions against *reference* for each feature.

    Args:
        reference: Baseline data (training window or prior period).
        current: Production data window to monitor.
        feature_cols: Feature columns to check for drift.
        score_col: Optional model score column to include in drift checks.
        config: Drift thresholds; defaults to :class:`DriftConfig` defaults.
    """
    cfg = config or DriftConfig()
    feature_drift: dict[str, dict] = {}
    overall_passed = True

    for col in feature_cols:
        if col not in reference.columns or col not in current.columns:
            continue
        result = check_distribution(
            reference[col],
            current[col],
            psi_threshold=cfg.psi_threshold,
            ks_threshold=cfg.ks_threshold,
        )
        feature_drift[col] = {
            "psi": result.psi,
            "ks_statistic": result.ks_statistic,
            "passed": result.passed,
        }
        if not result.passed:
            overall_passed = False

    score_drift = None
    if score_col and score_col in reference.columns and score_col in current.columns:
        result = check_distribution(
            reference[score_col],
            current[score_col],
            psi_threshold=cfg.psi_threshold,
            ks_threshold=cfg.ks_threshold,
        )
        score_drift = {
            "psi": result.psi,
            "ks_statistic": result.ks_statistic,
            "passed": result.passed,
        }
        if not result.passed:
            overall_passed = False

    return DriftReport(passed=overall_passed, feature_drift=feature_drift, score_drift=score_drift)
