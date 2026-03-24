"""Evaluation slicing: compute metrics independently for each data slice."""
from __future__ import annotations

from collections.abc import Callable

import polars as pl

from libs.contracts.eval_spec import SliceSpec


def apply_slices(
    df: pl.DataFrame,
    slices: list[SliceSpec],
    metric_fn: Callable[[pl.DataFrame], dict[str, float]],
) -> dict[str, dict[str, float]]:
    """Run *metric_fn* over the full DataFrame and each named slice.

    Args:
        df: The evaluation DataFrame.
        slices: List of :class:`SliceSpec` defining filter conditions.
        metric_fn: Function that takes a DataFrame and returns a metric dict.

    Returns:
        Mapping of slice name (including "overall") → metric dict.
    """
    results: dict[str, dict[str, float]] = {"overall": metric_fn(df)}

    for spec in slices:
        filtered = _apply_filter(df, spec.filters)
        if filtered.is_empty():
            results[spec.name] = {}
        else:
            results[spec.name] = metric_fn(filtered)

    return results


def _apply_filter(df: pl.DataFrame, filters: dict) -> pl.DataFrame:
    """Apply a simple dict of {column: value_or_list} filters to *df*."""
    expr = pl.lit(True)
    for col, val in filters.items():
        if col not in df.columns:
            continue
        if isinstance(val, list):
            expr = expr & pl.col(col).is_in(val)
        else:
            expr = expr & (pl.col(col) == val)
    return df.filter(expr)
