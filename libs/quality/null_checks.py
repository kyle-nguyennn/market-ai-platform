"""Null / missing-value checks for DataFrames."""
from __future__ import annotations

from dataclasses import dataclass, field

import polars as pl


@dataclass
class NullCheckResult:
    passed: bool
    null_rates: dict[str, float] = field(default_factory=dict)
    violations: dict[str, float] = field(default_factory=dict)  # col -> rate


def check_nulls(
    df: pl.DataFrame,
    max_null_rate: float = 0.01,
    columns: list[str] | None = None,
) -> NullCheckResult:
    """Check that each column's null rate does not exceed *max_null_rate*.

    Args:
        df: DataFrame to inspect.
        max_null_rate: Maximum fraction of nulls allowed per column [0, 1].
        columns: Subset of columns to check; defaults to all.

    Returns:
        A :class:`NullCheckResult` with per-column null rates and violations.
    """
    cols = columns or df.columns
    n = len(df)
    null_rates: dict[str, float] = {}
    violations: dict[str, float] = {}

    for col in cols:
        if col not in df.columns:
            continue
        rate = df[col].null_count() / n if n > 0 else 0.0
        null_rates[col] = rate
        if rate > max_null_rate:
            violations[col] = rate

    return NullCheckResult(passed=not violations, null_rates=null_rates, violations=violations)
