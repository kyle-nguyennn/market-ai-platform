"""Rolling window features: returns, volatility, momentum, z-scores."""
from __future__ import annotations

import polars as pl


def ret_1d(df: pl.DataFrame, close_col: str = "close") -> pl.DataFrame:
    """Add 1-day log return column ``ret_1d``."""
    return df.with_columns(
        (pl.col(close_col) / pl.col(close_col).shift(1)).log().alias("ret_1d")
    )


def rolling_volatility(
    df: pl.DataFrame,
    window: int = 20,
    close_col: str = "close",
    col_name: str | None = None,
) -> pl.DataFrame:
    """Add rolling annualised volatility (std of log returns × √252)."""
    name = col_name or f"vol_{window}d"
    log_ret = (pl.col(close_col) / pl.col(close_col).shift(1)).log()
    return df.with_columns(
        (log_ret.rolling_std(window_size=window) * (252 ** 0.5)).alias(name)
    )


def rolling_zscore(
    df: pl.DataFrame,
    col: str,
    window: int = 20,
) -> pl.DataFrame:
    """Add a rolling z-score column ``{col}_zscore_{window}d``."""
    name = f"{col}_zscore_{window}d"
    return df.with_columns(
        (
            (pl.col(col) - pl.col(col).rolling_mean(window_size=window))
            / pl.col(col).rolling_std(window_size=window)
        ).alias(name)
    )


def momentum(
    df: pl.DataFrame,
    window: int = 20,
    close_col: str = "close",
) -> pl.DataFrame:
    """Add a price momentum column ``mom_{window}d`` (return over *window* days)."""
    name = f"mom_{window}d"
    return df.with_columns(
        (pl.col(close_col) / pl.col(close_col).shift(window) - 1).alias(name)
    )
