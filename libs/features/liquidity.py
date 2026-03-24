"""Liquidity features: average daily volume, bid-ask spread proxies, turnover."""
from __future__ import annotations

import polars as pl


def average_daily_volume(
    df: pl.DataFrame,
    window: int = 20,
    volume_col: str = "volume",
) -> pl.DataFrame:
    """Add rolling average daily volume column ``adv_{window}d``."""
    name = f"adv_{window}d"
    return df.with_columns(
        pl.col(volume_col).rolling_mean(window_size=window).alias(name)
    )


def amihud_illiquidity(
    df: pl.DataFrame,
    close_col: str = "close",
    volume_col: str = "volume",
    window: int = 20,
) -> pl.DataFrame:
    """Add the Amihud (2002) illiquidity ratio column ``amihud_{window}d``.

    Defined as the rolling mean of |ret| / (close × volume).
    """
    name = f"amihud_{window}d"
    abs_ret = (pl.col(close_col) / pl.col(close_col).shift(1)).log().abs()
    dollar_vol = pl.col(close_col) * pl.col(volume_col)
    ratio = abs_ret / dollar_vol
    return df.with_columns(ratio.rolling_mean(window_size=window).alias(name))


def turnover_ratio(
    df: pl.DataFrame,
    close_col: str = "close",
    volume_col: str = "volume",
    shares_outstanding_col: str = "shares_outstanding",
) -> pl.DataFrame:
    """Add daily turnover ratio = volume / shares_outstanding."""
    return df.with_columns(
        (pl.col(volume_col) / pl.col(shares_outstanding_col)).alias("turnover_ratio")
    )
