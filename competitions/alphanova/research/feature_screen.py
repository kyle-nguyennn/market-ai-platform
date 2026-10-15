"""Causal, ticker-equivariant cross-sectional factor library for AlphaNova P4.

Factors are functions only of the six contemporaneous input panels. Names
identify hypotheses, not trained models. No use of the forward target or
returns is made when constructing factors.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd


def factor_names() -> list[str]:
    """48 predeclared hypotheses; freeze before reading validation labels."""
    names = [f"rank_{i}" for i in range(1, 7)]
    names += [f"z_{i}" for i in range(1, 7)]
    names += [f"diff_{a}_{b}" for a, b in combinations(range(1, 7), 2)]
    names += [f"product_{a}_{b}" for a, b in combinations(range(1, 7), 2)]
    names += [f"tail_{i}" for i in range(1, 7)]
    return names


def center_cross_section(values: np.ndarray) -> np.ndarray:
    """Finite row-wise de-mean. Missing observations take neutral value zero."""
    arr = np.asarray(values, dtype=float)
    arr = np.where(np.isfinite(arr), arr, np.nan)
    count = np.sum(np.isfinite(arr), axis=1, keepdims=True)
    mean = np.nansum(arr, axis=1, keepdims=True) / np.maximum(count, 1)
    arr = np.where(np.isfinite(arr), arr - mean, 0.0)
    # Re-center after replacing missing values, since neutral missing weights
    # must not create residual market exposure among the 20 output positions.
    return arr - arr.mean(axis=1, keepdims=True)


def cross_rank(values: np.ndarray) -> np.ndarray:
    """NaN-aware row rank in [-1,1], centered over all ticker positions."""
    raw = np.asarray(values, dtype=float)
    clean = np.where(np.isfinite(raw), raw, np.nan)
    ranked = pd.DataFrame(clean).rank(axis=1).to_numpy(dtype=float)
    n = np.isfinite(clean).sum(axis=1, keepdims=True)
    scaled = (ranked - 0.5 * (n + 1)) / (
        0.5 * np.maximum(n - 1, 1)
    )
    return center_cross_section(scaled)


def cross_zscore(values: np.ndarray, clip: float = 3.0) -> np.ndarray:
    """Causal row normalization with clipping; no fitted global statistics."""
    raw = np.asarray(values, dtype=float)
    clean = np.where(np.isfinite(raw), raw, np.nan)
    count = np.isfinite(clean).sum(axis=1, keepdims=True)
    mean = np.nansum(clean, axis=1, keepdims=True) / np.maximum(count, 1)
    centered = np.where(np.isfinite(clean), clean - mean, 0.0)
    variance = np.sum(centered * centered, axis=1, keepdims=True) / np.maximum(count, 1)
    z = centered / np.sqrt(np.maximum(variance, 1e-12))
    return center_cross_section(np.clip(z, -clip, clip))


def feature_panels(features: pd.DataFrame) -> tuple[list[np.ndarray], list[str]]:
    """Align all six feature panels by ticker *label* before any operations."""
    tickers = list(features["Feature.1"].columns)
    raw = []
    for i in range(1, 7):
        part = features[f"Feature.{i}"].reindex(columns=tickers)
        raw.append(part.to_numpy(dtype=float, copy=False))
    return raw, tickers


def factor_values(
    name: str,
    raw: list[np.ndarray],
    ranked: list[np.ndarray] | None = None,
) -> np.ndarray:
    """Generate one hypothesis without materializing a 48-factor 3D cube."""
    if len(raw) != 6:
        raise ValueError("Expected precisely six anonymous feature panels")
    if name not in factor_names():
        raise ValueError(f"Unrecognized factor: {name}")
    if ranked is None:
        ranked = [cross_rank(x) for x in raw]
    pieces = name.split("_")
    typ = pieces[0]
    a = int(pieces[1]) - 1
    if typ == "rank":
        return ranked[a]
    if typ == "z":
        return cross_zscore(raw[a])
    if typ == "tail":
        return center_cross_section(ranked[a] ** 3)
    b = int(pieces[2]) - 1
    if typ == "diff":
        return cross_rank(raw[a] - raw[b])
    if typ == "product":
        return center_cross_section(ranked[a] * ranked[b])
    raise ValueError(f"Unsupported factor family: {typ}")


def cross_sectional_ic(signal: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Pearson cross-sectional IC for each timestamp; undefined rows are NaN.

    Correlation is computed only on finite *paired* asset observations,
    not flattened over all timestamps. The sign of the supplied signal is
    preserved, allowing out-of-sample direction assessment.
    """
    x = np.asarray(signal, dtype=float)
    y = np.asarray(target, dtype=float)
    if x.shape != y.shape or x.ndim != 2:
        raise ValueError("Expected matching 2-D signal and target panels")
    good = np.isfinite(x) & np.isfinite(y)
    n = good.sum(axis=1, keepdims=True)
    xa = np.where(good, x, 0.0)
    ya = np.where(good, y, 0.0)
    xa -= xa.sum(axis=1, keepdims=True) / np.maximum(n, 1)
    ya -= ya.sum(axis=1, keepdims=True) / np.maximum(n, 1)
    num = np.sum(xa * ya, axis=1)
    denom = np.sqrt(np.sum(xa * xa, axis=1) * np.sum(ya * ya, axis=1))
    return np.divide(
        num, denom, out=np.full(len(x), np.nan),
        where=(denom > 1e-12) & (n[:, 0] >= 3),
    )


def train_linear_slope(
    signal: np.ndarray,
    target: np.ndarray,
    train_end: int,
    tail_rows: int = 20_000,
) -> float:
    """Fit univariate direction/magnitude to strictly earlier labels only.

    This is a pure one-variable OLS coefficient on demeaned cross-sectional
    observations, not a hyperparameter optimization against validation.
    """
    if not 0 < train_end <= len(signal):
        raise ValueError("Invalid train end")
    if tail_rows <= 0:
        raise ValueError("tail_rows must be positive")
    start = max(0, train_end - tail_rows)
    x = signal[start:train_end]
    y = target[start:train_end]
    valid = np.isfinite(x) & np.isfinite(y)
    xx = np.where(valid, x, 0.0)
    yy = np.where(valid, y, 0.0)
    denom = np.sum(xx * xx)
    if denom < 1e-12:
        return 0.0
    slope = np.sum(xx * yy) / denom
    return float(np.clip(slope, -5.0, 5.0))
