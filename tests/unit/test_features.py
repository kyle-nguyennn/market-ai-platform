"""Unit tests for libs/features rolling computations."""
from __future__ import annotations

import polars as pl  # noqa: F401  # TODO: use for inline DataFrame construction in tests

from libs.features.rolling import momentum, ret_1d, rolling_volatility


def test_ret_1d_column_added(sample_bars_df):
    df = ret_1d(sample_bars_df)
    assert "ret_1d" in df.columns


def test_ret_1d_first_value_null(sample_bars_df):
    df = ret_1d(sample_bars_df)
    assert df["ret_1d"][0] is None or (df["ret_1d"][0] != df["ret_1d"][0])  # NaN check


def test_rolling_volatility_column_added(sample_bars_df):
    df = rolling_volatility(sample_bars_df, window=5)
    assert "vol_5d" in df.columns


def test_momentum_column_added(sample_bars_df):
    df = momentum(sample_bars_df, window=5)
    assert "mom_5d" in df.columns


def test_rolling_volatility_non_negative(sample_bars_df):
    df = rolling_volatility(sample_bars_df, window=5)
    valid = df["vol_5d"].drop_nulls()
    assert (valid >= 0).all()
