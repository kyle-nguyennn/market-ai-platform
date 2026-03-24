"""Statistical distribution checks: PSI, KS test, and simple range guards."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from scipy import stats


@dataclass
class DistributionCheckResult:
    passed: bool
    psi: float | None = None
    ks_statistic: float | None = None
    ks_pvalue: float | None = None


def compute_psi(
    reference: np.ndarray,
    current: np.ndarray,
    buckets: int = 10,
) -> float:
    """Compute the Population Stability Index (PSI) between two distributions.

    PSI < 0.1  → stable
    0.1–0.2    → moderate shift
    > 0.2      → significant shift
    """
    eps = 1e-6
    ref_counts, bin_edges = np.histogram(reference, bins=buckets)
    cur_counts, _ = np.histogram(current, bins=bin_edges)

    ref_pct = ref_counts / (len(reference) + eps) + eps
    cur_pct = cur_counts / (len(current) + eps) + eps

    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def check_distribution(
    reference: pl.Series,
    current: pl.Series,
    psi_threshold: float = 0.2,
    ks_threshold: float = 0.1,
) -> DistributionCheckResult:
    """Run PSI and KS tests comparing *reference* to *current* distributions."""
    ref = reference.drop_nulls().to_numpy().astype(float)
    cur = current.drop_nulls().to_numpy().astype(float)

    if len(ref) < 10 or len(cur) < 10:
        return DistributionCheckResult(passed=True)

    psi = compute_psi(ref, cur)
    ks_stat, ks_p = stats.ks_2samp(ref, cur)

    passed = psi < psi_threshold and ks_stat < ks_threshold
    return DistributionCheckResult(
        passed=passed, psi=psi, ks_statistic=float(ks_stat), ks_pvalue=float(ks_p)
    )
