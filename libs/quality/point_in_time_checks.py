"""Point-in-time (PIT) correctness checks to prevent look-ahead bias."""
from __future__ import annotations

from datetime import datetime

import polars as pl


def check_no_lookahead(
    df: pl.DataFrame,
    event_time_col: str,
    label_time_col: str,
) -> bool:
    """Verify that every label timestamp is strictly after its event timestamp.

    Args:
        df: DataFrame containing both timestamp columns.
        event_time_col: Column with the feature observation time.
        label_time_col: Column with the label realisation time.

    Returns:
        True if no row has label_time <= event_time.
    """
    violations = df.filter(pl.col(label_time_col) <= pl.col(event_time_col))
    return violations.is_empty()


def filter_as_of(
    df: pl.DataFrame,
    timestamp_col: str,
    as_of: datetime,
) -> pl.DataFrame:
    """Return only rows with *timestamp_col* <= *as_of* (point-in-time slice).

    Args:
        df: Source DataFrame.
        timestamp_col: Column name for the row timestamp.
        as_of: Cut-off datetime (inclusive).

    Returns:
        Filtered DataFrame containing only rows known at *as_of*.
    """
    return df.filter(pl.col(timestamp_col) <= pl.lit(as_of))
