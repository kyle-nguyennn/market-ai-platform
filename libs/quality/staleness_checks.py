"""Staleness checks — verify data freshness relative to a reference time."""
from __future__ import annotations

from datetime import datetime, timedelta

import polars as pl

from libs.common.exceptions import StaleDataError
from libs.common.time import utc_now


def check_staleness(
    df: pl.DataFrame,
    timestamp_col: str,
    max_age: timedelta,
    reference_time: datetime | None = None,
) -> bool:
    """Return True if the most recent row in *timestamp_col* is within *max_age*.

    Args:
        df: DataFrame with a datetime column.
        timestamp_col: Column name containing timestamps.
        max_age: Maximum allowed age of the most recent record.
        reference_time: Compared against this instant (defaults to UTC now).

    Returns:
        True when the data is fresh enough.
    """
    if df.is_empty():
        return False

    now = reference_time or utc_now()
    latest = df[timestamp_col].max()

    if latest is None:
        return False

    # Polars may return a Python datetime or a pl.Datetime scalar; normalise.
    if hasattr(latest, "item"):
        latest = latest.item()

    if latest.tzinfo is None:
        from libs.common.time import as_utc
        latest = as_utc(latest)

    return (now - latest) <= max_age


def assert_fresh(
    df: pl.DataFrame,
    timestamp_col: str,
    max_age: timedelta,
    reference_time: datetime | None = None,
) -> None:
    """Like :func:`check_staleness` but raises :class:`StaleDataError` on failure."""
    if not check_staleness(df, timestamp_col, max_age, reference_time):
        raise StaleDataError(
            f"Column '{timestamp_col}' has stale data — max age {max_age} exceeded."
        )
