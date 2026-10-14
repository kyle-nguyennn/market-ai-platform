"""P5-B: predeclared contemporaneous observable regimes, no validation fit.

Regimes:
  feature1_dispersion: cross-sectional raw Feature.1 standard deviation
  feature1_6_disagreement: mean absolute difference of cross-sectional ranks

Thresholds are medians from the past labeled training slice only.
Each regime fits a separate simple OLS beta, shrunk halfway to the
global beta; no trees, model selection, label leakage, or ticker IDs.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from competitions.alphanova.research.feature_screen import (
    cross_rank,
    factor_values,
    feature_panels,
    train_linear_slope,
)

REGIMES = (
    "constant",
    "feature1_dispersion",
    "feature1_6_disagreement",
)


def regime_score(name: str, raw: list[np.ndarray]) -> np.ndarray:
    """Ticker-invariant score available at the signal timestamp."""
    if name == "feature1_dispersion":
        x = np.where(np.isfinite(raw[0]), raw[0], np.nan)
        counts = np.isfinite(x).sum(axis=1)
        means = np.nansum(x, axis=1) / np.maximum(counts, 1)
        dev = np.where(np.isfinite(x), x - means[:, None], 0.0)
        variance = np.sum(dev * dev, axis=1) / np.maximum(counts, 1)
        return np.sqrt(variance)
    if name == "feature1_6_disagreement":
        a, b = cross_rank(raw[0]), cross_rank(raw[5])
        return np.mean(np.abs(a - b), axis=1)
    if name == "constant":
        return np.zeros(len(raw[0]), dtype=float)
    raise ValueError(f"Unrecognized regime: {name}")


@dataclass(frozen=True)
class RegimeModel:
    regime: str
    threshold: float
    beta_global: float
    beta_low: float
    beta_high: float
    train_low_fraction: float


def fit_regime(
    factor: np.ndarray,
    labels: np.ndarray,
    scores: np.ndarray,
    regime: str,
    *,
    shrinkage: float = 0.5,
    min_rows: int = 200,
) -> RegimeModel:
    """Estimate conditional slopes only from the caller's training slice."""
    if factor.shape != labels.shape or factor.shape[0] != len(scores):
        raise ValueError("Regime fit dimensions differ")
    if regime not in REGIMES:
        raise ValueError("Unknown regime")
    if not 0 <= shrinkage <= 1:
        raise ValueError("Shrinkage must be between 0 and 1")
    global_beta = train_linear_slope(factor, labels, len(factor), len(factor))
    if regime == "constant":
        return RegimeModel(regime, 0.0, global_beta, global_beta, global_beta, 1.0)
    valid = scores[np.isfinite(scores)]
    if len(valid) < 2:
        return RegimeModel(regime, 0.0, global_beta, global_beta, global_beta, 1.0)
    threshold = float(np.median(valid))
    high = np.isfinite(scores) & (scores > threshold)
    low = ~high
    if min(high.sum(), low.sum()) < min_rows:
        return RegimeModel(
            regime, threshold, global_beta, global_beta, global_beta,
            float(low.mean()),
        )
    beta_low_raw = train_linear_slope(factor[low], labels[low], int(low.sum()), int(low.sum()))
    beta_high_raw = train_linear_slope(
        factor[high], labels[high], int(high.sum()), int(high.sum())
    )
    beta_low = (1 - shrinkage) * global_beta + shrinkage * beta_low_raw
    beta_high = (1 - shrinkage) * global_beta + shrinkage * beta_high_raw
    return RegimeModel(
        regime, threshold, global_beta, float(beta_low), float(beta_high),
        float(low.mean()),
    )


def conditional_factor(factor: np.ndarray, scores: np.ndarray, model: RegimeModel) -> np.ndarray:
    """Use the current timestamp's regime, never a future observation."""
    high = np.isfinite(scores) & (scores > model.threshold)
    betas = np.where(high, model.beta_high, model.beta_low)
    return np.nan_to_num(factor * betas[:, None], nan=0.0, posinf=0.0, neginf=0.0)


def train_from_panels(
    features: pd.DataFrame,
    target: pd.DataFrame,
    *,
    regime: str,
    tail_rows: int = 20_000,
    embargo_rows: int = 168,
    shrinkage: float = 0.5,
) -> RegimeModel:
    """Trains on pre-embargo data; independent of evaluation target/returns."""
    if tail_rows <= 0 or embargo_rows < 0:
        raise ValueError("Invalid training window")
    cutoff = len(features) - embargo_rows
    if cutoff <= 0:
        raise ValueError("Insufficient training rows")
    start = max(0, cutoff - tail_rows)
    slice_ = features.iloc[start:cutoff]
    raw, tickers = feature_panels(slice_)
    factor = factor_values("rank_1", raw)
    labels = target.iloc[start:cutoff].reindex(columns=tickers).to_numpy(dtype=float)
    scores = regime_score(regime, raw)
    return fit_regime(factor, labels, scores, regime, shrinkage=shrinkage)


def predict_raw(features: pd.DataFrame, model: RegimeModel) -> tuple[np.ndarray, list[str]]:
    raw, tickers = feature_panels(features)
    factor = factor_values("rank_1", raw)
    score = regime_score(model.regime, raw)
    return conditional_factor(factor, score, model), tickers
