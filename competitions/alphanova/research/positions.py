"""Causal, market-neutral turnover controls for P2 research.

Policies operate on an already inferred cross-sectional position target.
They do not access targets, future returns, or hidden competition data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def position_policy(
    targets: pd.DataFrame,
    min_trade_l1: float = 0.0,
    rebalance_fraction: float = 1.0,
) -> pd.DataFrame:
    """Causal portfolio controller: hold until L1 gap exceeds no-trade band.

    If trading, apply `rebalance_fraction` of the desired position change.
    Both previous positions and current target must be cross-sectionally
    centered; the update preserves this invariant. No look-ahead or smoothing
    of future observations is performed. Every predict() call starts flat.
    """
    if min_trade_l1 < 0 or not np.isfinite(min_trade_l1):
        raise ValueError("min_trade_l1 must be finite and nonnegative")
    if not np.isfinite(rebalance_fraction) or not (0 < rebalance_fraction <= 1):
        raise ValueError("rebalance_fraction must be in (0, 1]")
    values = targets.to_numpy(dtype=float, copy=True)
    if values.ndim != 2 or not values.shape[1]:
        raise ValueError("Targets must have at least one asset")
    if not np.isfinite(values).all():
        raise ValueError("Targets contain nonfinite values")
    values -= values.mean(axis=1, keepdims=True)
    previous = np.zeros(values.shape[1], dtype=float)
    output = np.empty_like(values)
    for t, desired in enumerate(values):
        delta = desired - previous
        if np.abs(delta).sum() > min_trade_l1:
            previous = previous + rebalance_fraction * delta
        output[t] = previous
    output -= output.mean(axis=1, keepdims=True)
    return pd.DataFrame(output, index=targets.index, columns=targets.columns)


def policy_diagnostics(positions: pd.DataFrame) -> dict[str, float | int]:
    """Rebalance frequency and activity, complementary to PnL diagnostics."""
    x = positions.to_numpy(dtype=float)
    if len(x) < 2:
        return {"rebalance_fraction_observed": 0.0, "rebalance_count": 0}
    gaps = np.abs(np.diff(x, axis=0)).sum(axis=1)
    count = int(np.count_nonzero(gaps > 1e-12))
    return {
        "rebalance_fraction_observed": count / len(gaps),
        "rebalance_count": count,
    }
