"""Event-based features: earnings flags, macro release proximity, index rebalance."""
from __future__ import annotations

from datetime import date

import polars as pl


def days_to_next_event(
    df: pl.DataFrame,
    date_col: str,
    event_dates: list[date],
) -> pl.DataFrame:
    """Add a ``days_to_next_event`` column with the number of calendar days
    until the nearest upcoming event for each row date.

    Args:
        df: Source DataFrame with a date column.
        event_dates: Sorted list of known event dates.
        date_col: Name of the date column in *df*.
    """
    if not event_dates:
        return df.with_columns(pl.lit(None).cast(pl.Int32).alias("days_to_next_event"))

    events_df = pl.DataFrame({"event_date": pl.Series(event_dates).cast(pl.Date)})

    result = (
        df.join(events_df, how="cross")
        .filter(pl.col("event_date") >= pl.col(date_col))
        .group_by(date_col)
        .agg(
            (pl.col("event_date") - pl.col(date_col))
            .dt.total_days()
            .min()
            .alias("days_to_next_event")
        )
    )
    return df.join(result, on=date_col, how="left")


def is_event_window(
    df: pl.DataFrame,
    date_col: str,
    event_dates: list[date],
    window_days: int = 1,
) -> pl.DataFrame:
    """Add a boolean ``in_event_window`` flag for rows within ±*window_days* of an event."""
    event_set = {d for d in event_dates}

    def _flag(d: date) -> bool:
        from datetime import timedelta
        for offset in range(-window_days, window_days + 1):
            check = d + timedelta(days=offset)
            if check in event_set:
                return True
        return False

    dates = df[date_col].to_list()
    flags = [_flag(d) for d in dates]
    return df.with_columns(pl.Series("in_event_window", flags))
