"""Unit tests for libs/quality checks."""
from __future__ import annotations

import polars as pl
import pytest

from libs.common.exceptions import SchemaValidationError
from libs.quality.null_checks import check_nulls
from libs.quality.schema_checks import assert_schema, check_schema


def test_check_schema_passes(sample_bars_df):
    expected = {"close": "Float64", "volume": "Float64"}
    result = check_schema(sample_bars_df, expected)
    assert result.passed
    assert not result.missing_cols
    assert not result.type_mismatches


def test_check_schema_missing_column(sample_bars_df):
    expected = {"close": "Float64", "nonexistent": "Int64"}
    result = check_schema(sample_bars_df, expected)
    assert not result.passed
    assert "nonexistent" in result.missing_cols


def test_assert_schema_raises(sample_bars_df):
    with pytest.raises(SchemaValidationError):
        assert_schema(sample_bars_df, {"nonexistent": "Int64"})


def test_check_nulls_passes(sample_bars_df):
    result = check_nulls(sample_bars_df, max_null_rate=0.01)
    assert result.passed


def test_check_nulls_detects_violations():
    df = pl.DataFrame({"a": [1.0, None, None, None, 1.0]})
    result = check_nulls(df, max_null_rate=0.1)
    assert not result.passed
    assert "a" in result.violations
